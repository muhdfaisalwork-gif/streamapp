"""
tmdb_watch_providers.py — Enriches titles with legal "Watch on Netflix"-style
badges from TMDB's /watch/providers endpoint (JustWatch data). This is pure
metadata: it never hosts or embeds content, only records which real, licensed
service (if any) already carries a title, plus TMDB's own referral link to it.

Only providers in PROVIDER_NAME_TO_SLUG (matching the rows seeded by
migrate_watch_providers.py) are recorded; everything else is skipped and
reported under unmapped_providers so the mapping can be extended deliberately
rather than silently growing.

Generated with qwen2.5-coder:7b via Ollama MCP, assembled and bug-fixed by
Claude (the draft never actually slept between TMDB requests despite the spec
requiring it, and it counted every checked title as "has providers" even when
zero were found/inserted for it).

Locked and checkpointed via job_control.py: after three separate run-losses in
one night (two power outages and a zombie-process collision), this now
resumes from its last saved index into the candidate list instead of
restarting from title zero, and refuses to run a second instance against the
same catalog.db while one is already active.
"""
from __future__ import annotations
import argparse
import json
import os
import sqlite3
import sys
import time

import requests

from job_control import LockedJob

TMDB_BASE = "https://api.themoviedb.org/3"
JOB_NAME = "tmdb_watch_providers"

PROVIDER_NAME_TO_SLUG = {
    "netflix": "netflix",
    "amazon prime video": "prime-video",
    "disney plus": "disney-plus",
    "hulu": "hulu",
    "max": "max",
    "hbo max": "max",
    "apple tv": "apple-tv-plus",
    "apple tv plus": "apple-tv-plus",
    "paramount plus": "paramount-plus",
    "peacock": "peacock",
    "peacock premium": "peacock",
    "crunchyroll": "crunchyroll",
}

AVAILABILITY_TYPE_MAP = {
    "flatrate": "subscription",
    "rent": "rent",
    "buy": "buy",
    "free": "free",
    "ads": "ads_supported",
}


def fetch_watch_providers(api_key: str, tmdb_id: int, media_type: str) -> dict | None:
    url = f"{TMDB_BASE}/{media_type}/{tmdb_id}/watch/providers"
    try:
        resp = requests.get(url, params={"api_key": api_key}, timeout=10)
    except requests.RequestException:
        return None
    if resp.status_code != 200:
        return None
    return resp.json()


def main() -> None:
    parser = argparse.ArgumentParser(description="Enrich titles with legal TMDB watch-provider data")
    parser.add_argument("--db", default="catalog.db")
    parser.add_argument("--limit", type=int, default=3000)
    args = parser.parse_args()

    api_key = os.environ.get("TMDB_API_KEY")
    if not api_key:
        sys.exit("FATAL: TMDB_API_KEY not set")

    conn = sqlite3.connect(args.db)
    conn.execute("PRAGMA busy_timeout = 10000")
    conn.row_factory = sqlite3.Row

    with LockedJob(conn, JOB_NAME, stale_after_seconds=300) as job:
        if not job.acquired:
            sys.exit(f"Another {JOB_NAME} run is already in progress against this database — exiting.")

        cursor = conn.cursor()

        provider_id_cache: dict[str, int] = {}
        for row in cursor.execute("SELECT id, slug FROM streaming_providers"):
            provider_id_cache[row["slug"]] = row["id"]

        titles = cursor.execute(
            "SELECT id, tmdb_id, type FROM titles "
            "WHERE tmdb_id IS NOT NULL AND tmdb_id != '' AND type IN ('movie','tv') "
            "ORDER BY popularity DESC LIMIT ?",
            (args.limit,),
        ).fetchall()

        checkpoint = job.load_checkpoint() or {"index": 0}
        start_index = checkpoint.get("index", 0)
        if start_index:
            print(f"Resuming from checkpoint: skipping {start_index} already-processed titles", file=sys.stderr)

        titles_checked = 0
        titles_with_providers = 0
        links_inserted = 0
        api_errors = 0
        unmapped_providers: set[str] = set()

        for i in range(start_index, len(titles)):
            row = titles[i]
            titles_checked += 1
            data = fetch_watch_providers(api_key, row["tmdb_id"], row["type"])
            time.sleep(0.05)

            if data is None:
                api_errors += 1
            else:
                us_result = data.get("results", {}).get("US")
                if us_result:
                    deep_link = us_result.get("link")
                    inserted_for_title = 0

                    for tmdb_kind, our_kind in AVAILABILITY_TYPE_MAP.items():
                        for provider in us_result.get(tmdb_kind, []):
                            name = (provider.get("provider_name") or "").strip().lower()
                            slug = PROVIDER_NAME_TO_SLUG.get(name)
                            if not slug:
                                unmapped_providers.add(name)
                                continue
                            provider_id = provider_id_cache.get(slug)
                            if not provider_id:
                                continue
                            cursor.execute(
                                "INSERT OR REPLACE INTO title_streaming_providers "
                                "(title_id, provider_id, availability_type, region, deep_link, last_checked_at) "
                                "VALUES (?, ?, ?, 'US', ?, strftime('%s','now'))",
                                (row["id"], provider_id, our_kind, deep_link),
                            )
                            inserted_for_title += 1

                    links_inserted += inserted_for_title
                    if inserted_for_title:
                        titles_with_providers += 1

            if titles_checked % 100 == 0:
                conn.commit()
                job.save_checkpoint({"index": i + 1})
                job.heartbeat()

        conn.commit()
        # Full pass complete: reset so the next scheduled run re-verifies from the
        # top (provider availability changes over time) instead of being "done" forever.
        job.save_checkpoint({"index": 0})

    conn.close()

    print(json.dumps({
        "titles_checked": titles_checked,
        "titles_with_providers": titles_with_providers,
        "links_inserted": links_inserted,
        "api_errors": api_errors,
        "unmapped_providers": sorted(unmapped_providers),
    }, indent=2))


if __name__ == "__main__":
    main()
