"""
tmdb_people_studios_ingest.py — Populates the actor/director/studio filmography
junction tables (title_actors, title_directors, title_studios,
title_animation_studios) using TMDB's own credits/discover data, for the
people and studios already seeded by migrate_people_studios.py and wired
into the frontend's categoryAssets.js manifest.

Reuses tmdb_discovery.py's upsert_discovered_title so any credit not yet in
the catalog gets added the same metadata-only way as every other discovery
path this session (no fake availability).

Generated with qwen2.5-coder:7b via Ollama MCP, assembled and bug-fixed by
Claude (the draft hardcoded role='production' for BOTH title_studios and
title_animation_studios inserts — animation studio links need role='animation'
— and it assumed a fetch_json() helper that didn't actually exist anywhere in
the codebase).

Locked and checkpointed via job_control.py.
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
JOB_NAME = "tmdb_people_studios_ingest"


def fetch_json(api_key: str, path: str, params: dict | None = None) -> dict | None:
    try:
        resp = requests.get(f"{TMDB_BASE}{path}", params={**(params or {}), "api_key": api_key}, timeout=10)
    except requests.RequestException:
        return None
    if resp.status_code != 200:
        return None
    return resp.json()


def link_person_credits(conn: sqlite3.Connection, api_key: str, genre_map: dict,
                         person_row_id: int, tmdb_person_id: int, role: str) -> int:
    data = fetch_json(api_key, f"/person/{tmdb_person_id}/combined_credits")
    if data is None:
        return 0

    cursor = conn.cursor()
    links_inserted = 0

    if role == "actor":
        for item in data.get("cast", []):
            title_id, _ = upsert_discovered_title(conn, item, item["media_type"], genre_map, None)
            if title_id is None:
                continue
            cursor.execute(
                "INSERT OR IGNORE INTO title_actors (title_id, actor_id, character_name, billing_order, role_type) "
                "VALUES (?, ?, ?, ?, 'cast')",
                (title_id, person_row_id, item.get("character"), item.get("order", 100)),
            )
            links_inserted += cursor.rowcount

    elif role == "director":
        for item in data.get("crew", []):
            if item.get("job") != "Director":
                continue
            title_id, _ = upsert_discovered_title(conn, item, item["media_type"], genre_map, None)
            if title_id is None:
                continue
            cursor.execute(
                "INSERT OR IGNORE INTO title_directors (title_id, director_id, role) VALUES (?, ?, 'director')",
                (title_id, person_row_id),
            )
            links_inserted += cursor.rowcount

    conn.commit()
    return links_inserted


def link_studio_titles(conn: sqlite3.Connection, api_key: str, genre_map: dict,
                        studio_row_id: int, tmdb_company_id: int, table: str, id_col: str,
                        max_pages: int = 5) -> int:
    role = "animation" if table == "title_animation_studios" else "production"
    cursor = conn.cursor()
    links_inserted = 0

    for page in range(1, max_pages + 1):
        response = fetch_json(api_key, "/discover/movie",
                               {"with_companies": tmdb_company_id, "page": page, "sort_by": "popularity.desc"})
        if not response or not response.get("results"):
            break

        for item in response["results"]:
            title_id, _ = upsert_discovered_title(conn, item, "movie", genre_map, None)
            if title_id is None:
                continue
            cursor.execute(
                f"INSERT OR IGNORE INTO {table} ({id_col}, title_id, role) VALUES (?, ?, ?)",
                (studio_row_id, title_id, role),
            )
            links_inserted += cursor.rowcount

        if page >= response.get("total_pages", page):
            break
        time.sleep(0.1)

    conn.commit()
    return links_inserted


def main() -> None:
    parser = argparse.ArgumentParser(description="Link actor/director/studio filmographies from TMDB")
    parser.add_argument("--db", default="catalog.db")
    parser.add_argument("--studio-pages", type=int, default=5)
    args = parser.parse_args()

    api_key = os.environ.get("TMDB_API_KEY")
    if not api_key:
        sys.exit("FATAL: TMDB_API_KEY not set")

    conn = sqlite3.connect(args.db)
    conn.execute("PRAGMA busy_timeout = 15000")
    conn.row_factory = sqlite3.Row

    with LockedJob(conn, JOB_NAME, stale_after_seconds=600) as job:
        if not job.acquired:
            conn.close()
            sys.exit(f"Another {JOB_NAME} run is already in progress against this database — exiting.")

        client = TmdbClient(api_key=api_key)
        client.configure()
        genre_map = build_genre_map(client)

        summary = {"actors": {}, "directors": {}, "studios": {}, "animation_studios": {}}

        for row in conn.execute("SELECT id, slug, name, tmdb_person_id FROM actors WHERE tmdb_person_id IS NOT NULL"):
            n = link_person_credits(conn, api_key, genre_map, row["id"], row["tmdb_person_id"], "actor")
            summary["actors"][row["slug"]] = n
            time.sleep(0.1)
            job.heartbeat()

        for row in conn.execute("SELECT id, slug, name, tmdb_person_id FROM directors WHERE tmdb_person_id IS NOT NULL"):
            n = link_person_credits(conn, api_key, genre_map, row["id"], row["tmdb_person_id"], "director")
            summary["directors"][row["slug"]] = n
            time.sleep(0.1)
            job.heartbeat()

        for row in conn.execute("SELECT id, slug, name, tmdb_company_id FROM studios WHERE tmdb_company_id IS NOT NULL"):
            n = link_studio_titles(conn, api_key, genre_map, row["id"], row["tmdb_company_id"],
                                    "title_studios", "studio_id", args.studio_pages)
            summary["studios"][row["slug"]] = n
            job.heartbeat()

        for row in conn.execute("SELECT id, slug, name, tmdb_company_id FROM animation_studios WHERE tmdb_company_id IS NOT NULL"):
            n = link_studio_titles(conn, api_key, genre_map, row["id"], row["tmdb_company_id"],
                                    "title_animation_studios", "animation_studio_id", args.studio_pages)
            summary["animation_studios"][row["slug"]] = n
            job.heartbeat()

    conn.close()
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
