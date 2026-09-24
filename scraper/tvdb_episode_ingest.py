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
import json
import logging
import re
import sqlite3
import sys
import time

from tvdb_client import TvdbClient, TvdbError

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("tvdb_episode_ingest")


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
    cursor = conn.cursor()
    episodes_data = client.series_episodes(series_id, season_type="default")
    if not episodes_data or "episodes" not in episodes_data:
        return 0

    inserted_count = 0
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

    conn.execute(
        "UPDATE seasons SET episode_count = (SELECT COUNT(*) FROM episodes WHERE season_id = seasons.id) WHERE title_id = ?",
        (title_id,),
    )
    conn.commit()
    return inserted_count


def run(db_path: str = "catalog.db", limit: int | None = None) -> dict:
    conn = sqlite3.connect(db_path)
    client = TvdbClient()
    rows = conn.execute(
        "SELECT id, title, year FROM titles WHERE type='tv' AND id NOT IN (SELECT DISTINCT title_id FROM seasons)"
    ).fetchall()
    if limit:
        rows = rows[:limit]

    counts = {"matched": 0, "unmatched": 0, "episodes_added": 0, "errors": 0}
    for title_id, title, year in rows:
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

    conn.close()
    return counts


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TVDB Episode Ingestor")
    parser.add_argument("--db", default="catalog.db")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    try:
        TvdbClient()
    except TvdbError as e:
        print(f"FATAL: {e}", file=sys.stderr)
        sys.exit(2)

    result = run(db_path=args.db, limit=args.limit)
    print(json.dumps(result, indent=2))
