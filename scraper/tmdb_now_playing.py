"""
tmdb_now_playing.py — Keeps the catalog's "trending now" metadata current by
pulling TMDB's own now_playing/upcoming/on_the_air/airing_today lists. Reuses
tmdb_discovery.py's upsert_discovered_title so new rows follow the exact same
metadata-only rule: no fake availability, metadata_state stays 'stub' until a
lawful source actually verifies playback.

Generated with qwen2.5-coder:7b via Ollama MCP, assembled and bug-fixed by
Claude (the draft referenced an undeclared global `args` inside a helper
function, never imported `sys` despite calling sys.exit, tried to unpack three
values out of a two-item dict, and overwrote api_errors per endpoint instead
of summing across all four).

Locked and checkpointed via job_control.py so a second concurrent run (or one
left over from a crash) can't collide with this one on catalog.db.
"""
from __future__ import annotations
import argparse
import json
import os
import sqlite3
import sys
import time

import requests

from tmdb_client import TmdbClient
from tmdb_discovery import upsert_discovered_title, build_genre_map
from job_control import LockedJob

TMDB_BASE = "https://api.themoviedb.org/3"
JOB_NAME = "tmdb_now_playing"

# (summary_key, path, media_type, status)
ENDPOINTS = [
    ("now_playing_movies", "/movie/now_playing", "movie", "released"),
    ("upcoming_movies", "/movie/upcoming", "movie", "upcoming"),
    ("on_the_air_tv", "/tv/on_the_air", "tv", "released"),
    ("airing_today_tv", "/tv/airing_today", "tv", "released"),
]


def fetch_page(api_key: str, path: str, page: int) -> dict | None:
    try:
        resp = requests.get(f"{TMDB_BASE}{path}", params={"api_key": api_key, "page": page}, timeout=10)
    except requests.RequestException:
        return None
    if resp.status_code != 200:
        return None
    return resp.json()


def main() -> None:
    parser = argparse.ArgumentParser(description="Pull TMDB now-playing/upcoming/on-the-air lists")
    parser.add_argument("--db", default="catalog.db")
    parser.add_argument("--pages", type=int, default=5, help="max pages to fetch per endpoint")
    args = parser.parse_args()

    api_key = os.environ.get("TMDB_API_KEY")
    if not api_key:
        sys.exit("FATAL: TMDB_API_KEY not set")

    conn = sqlite3.connect(args.db)
    conn.execute("PRAGMA busy_timeout = 10000")

    with LockedJob(conn, JOB_NAME, stale_after_seconds=300) as job:
        if not job.acquired:
            sys.exit(f"Another {JOB_NAME} run is already in progress against this database — exiting.")

        client = TmdbClient(api_key=api_key)
        client.configure()
        genre_map = build_genre_map(client)

        checkpoint = job.load_checkpoint() or {"completed_endpoints": []}
        done = set(checkpoint.get("completed_endpoints", []))

        summary: dict = {}
        api_errors = 0

        for key, path, media_type, status in ENDPOINTS:
            if key in done:
                summary[key] = {"new": 0, "existing": 0, "skipped_resumed": True}
                continue

            counts = {"new": 0, "existing": 0}
            for page in range(1, args.pages + 1):
                data = fetch_page(api_key, path, page)
                time.sleep(0.05)

                if data is None:
                    api_errors += 1
                    continue

                results = data.get("results") or []
                if not results:
                    break

                for item in results:
                    title_id, was_new = upsert_discovered_title(conn, item, media_type, genre_map, None, status=status)
                    if title_id is None:
                        continue
                    counts["new" if was_new else "existing"] += 1

                if data.get("page", page) >= data.get("total_pages", page):
                    break

            summary[key] = counts
            done.add(key)
            job.save_checkpoint({"completed_endpoints": sorted(done)})
            job.heartbeat()

        # Full pass complete: reset so the next scheduled run covers all endpoints again.
        job.save_checkpoint({"completed_endpoints": []})

    conn.close()
    summary["api_errors"] = api_errors
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
