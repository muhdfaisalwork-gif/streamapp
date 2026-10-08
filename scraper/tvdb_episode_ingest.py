"""
tvdb_episode_ingest.py — Adds season/episode data for TV titles already in
catalog.db that have no episodes yet, using TheTVDB as the source.

Matching is confidence-gated (normalized title/alias match + year within
±1), never a blind first-result guess — the Return of the King tmdb_id
mismatch and the earlier archive.org wrong-match incident are exactly the
failure mode this guards against.

Generated with qwen2.5-coder:7b via Ollama MCP, assembled and bug-fixed
by Claude (typo: normalized_title -> normalize_title; defensive .get()
access on episode fields that TVDB sometimes omits).
"""
from __future__ import annotations
import argparse
import os
from pathlib import Path as _P
try:
    from dotenv import dotenv_values as _dv
    for _k, _v in _dv(_P(__file__).parent / '.env').items():
        if _v:
            os.environ.setdefault(_k, _v)
except Exception:
    pass
import json
import logging
import re
import sqlite3
import sys
import time

from tvdb_client import TvdbClient, TvdbError
from job_control import LockedJob

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("tvdb_episode_ingest")
JOB_NAME = "tvdb_episode_ingest"


def normalize_title(s: str) -> str:
    return re.sub(r"\W+", " ", s.lower()).strip()


def find_confident_match(client: TvdbClient, title: str, year: int | None) -> int | None:
    target_norm = normalize_title(title)
    matches = client.search_series(title, year=year)
    for result in matches:
        normalized_name = normalize_title(result.get("name", ""))
        normalized_aliases = [normalize_title(a) for a in result.get("aliases", [])]
        if normalized_name != target_norm and target_norm not in normalized_aliases:
            continue

        if year is not None:
            try:
                year_from_result = int(result.get("first_air_time", "")[:4])
            except (ValueError, TypeError):
                continue
            if not (year - 1 <= year_from_result <= year + 1):
                continue

        raw_id = result.get("id", "")
        if raw_id.startswith("series-"):
            raw_id = raw_id[len("series-"):]
        try:
            return int(raw_id)
        except ValueError:
            continue
    return None


def ingest_episodes_for_title(conn: sqlite3.Connection, client: TvdbClient, title_id: int, series_id: int) -> int:
    """Paginates through TVDB's episode list instead of only fetching page 0.
    TVDB returns episodes oldest-first in pages of ~500; a long-running show
    (Law & Order: SVU, 25+ seasons) has far more than one page, so fetching
    only page 0 silently caps the catalog at whatever aired first — exactly
    the "seasons stop at 2021" staleness bug this fixes."""
    cursor = conn.cursor()
    inserted_count = 0
    page = 0
    MAX_PAGES = 30  # safety cap against an API quirk returning the same page forever

    while page <= MAX_PAGES:
        episodes_data = client.series_episodes(series_id, season_type="default", page=page)
        if not episodes_data or not episodes_data.get("episodes"):
            break

        for ep in episodes_data["episodes"]:
            season_number = ep.get("seasonNumber")
            if season_number is None:
                continue

            cursor.execute(
                "INSERT OR IGNORE INTO seasons (title_id, season_number, name, poster) VALUES (?, ?, ?, ?)",
                (title_id, season_number, "Specials" if season_number == 0 else f"Season {season_number}", None),
            )
            cursor.execute("SELECT id FROM seasons WHERE title_id=? AND season_number=?", (title_id, season_number))
            season_row = cursor.fetchone()
            if not season_row:
                continue
            season_id = season_row[0]

            episode_number = ep.get("number")
            if episode_number is None:
                continue

            cursor.execute(
                "INSERT OR IGNORE INTO episodes (season_id, episode_number, title, overview, thumbnail, air_date, runtime) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (season_id, episode_number, ep.get("name"), ep.get("overview"), ep.get("image"), ep.get("aired"), ep.get("runtime")),
            )
            inserted_count += 1 if cursor.rowcount > 0 else 0

        conn.commit()
        time.sleep(0.1)
        page += 1

    conn.execute(
        "UPDATE seasons SET episode_count = (SELECT COUNT(*) FROM episodes WHERE season_id = seasons.id) WHERE title_id = ?",
        (title_id,),
    )
    conn.commit()
    return inserted_count


def run(db_path: str = "catalog.db", limit: int | None = None, refresh_existing: bool = False) -> dict:
    """Without --refresh-existing: only backfills TV titles that have zero
    seasons yet (the original behavior). With it: re-checks titles that
    already have seasons too, ordered by popularity, so an ongoing show never
    ingested past its first TVDB page (or never refreshed since) can catch up
    on new seasons/episodes. INSERT OR IGNORE elsewhere makes re-processing
    an already-seasoned show safe — it only adds what's actually new."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA busy_timeout = 15000")
    client = TvdbClient()
    if refresh_existing:
        rows = conn.execute(
            "SELECT id, title, year FROM titles WHERE type='tv' "
            "AND id IN (SELECT DISTINCT title_id FROM seasons) ORDER BY popularity DESC"
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id, title, year FROM titles WHERE type='tv' AND id NOT IN (SELECT DISTINCT title_id FROM seasons)"
        ).fetchall()
    if limit:
        rows = rows[:limit]

    counts = {"matched": 0, "unmatched": 0, "episodes_added": 0, "errors": 0}
    lock_name = f"{JOB_NAME}_refresh" if refresh_existing else JOB_NAME

    with LockedJob(conn, lock_name, stale_after_seconds=300) as job:
        if not job.acquired:
            conn.close()
            sys.exit(f"Another {lock_name} run is already in progress against this database — exiting.")

        checkpoint = job.load_checkpoint() or {"index": 0}
        start_index = checkpoint.get("index", 0)
        if start_index:
            log.info("Resuming from checkpoint: skipping %d already-processed titles", start_index)

        for i in range(start_index, len(rows)):
            title_id, title, year = rows[i]
            try:
                series_id = find_confident_match(client, title, year)
                if series_id is None:
                    counts["unmatched"] += 1
                    log.info("No confident TVDB match for %s (%s)", title, year)
                else:
                    n = ingest_episodes_for_title(conn, client, title_id, series_id)
                    counts["matched"] += 1
                    counts["episodes_added"] += n
                    log.info("Matched %s -> tvdb:%s, added %d episodes", title, series_id, n)
            except Exception as e:
                log.exception("Error processing title_id=%s (%s): %s", title_id, title, e)
                counts["errors"] += 1
            time.sleep(0.1)

            if (i + 1) % 50 == 0:
                job.save_checkpoint({"index": i + 1})
                job.heartbeat()

        job.save_checkpoint({"index": 0})  # full pass complete: let the next run start fresh

    conn.close()
    return counts


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TVDB Episode Ingestor")
    parser.add_argument("--db", default="catalog.db")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--refresh-existing", action="store_true",
                         help="Re-check TV titles that already have seasons (ordered by popularity) "
                              "instead of only backfilling titles with zero seasons.")
    args = parser.parse_args()

    try:
        TvdbClient()
    except TvdbError as e:
        print(f"FATAL: {e}", file=sys.stderr)
        sys.exit(2)

    result = run(db_path=args.db, limit=args.limit, refresh_existing=args.refresh_existing)
    print(json.dumps(result, indent=2))
