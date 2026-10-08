"""
backfill_languages.py — Fills in missing title_languages rows for titles
that already have a tmdb_id but were inserted (by an earlier version of
tmdb_discovery.py) without any language tag.

Generated with qwen2.5-coder:7b via Ollama MCP, assembled and bug-fixed
by Claude (conn.fetchone() doesn't exist on Connection objects, only on
the Cursor that .execute() returns).
"""
from __future__ import annotations
import argparse
import json
import logging
import sqlite3
import sys
import time

from tmdb_client import TmdbClient, TmdbError

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("backfill_languages")


def get_language_id(conn: sqlite3.Connection, iso_code: str) -> int | None:
    row = conn.execute("SELECT id FROM languages WHERE code=?", (iso_code.lower(),)).fetchone()
    return row[0] if row else None


def backfill(db_path: str = "catalog.db", limit: int | None = None) -> dict:
    counts = {"tagged": 0, "no_language": 0, "not_found": 0, "errors": 0}
    conn = sqlite3.connect(db_path)
    client = TmdbClient()
    client.configure()
    rows = conn.execute(
        "SELECT id, type, tmdb_id FROM titles WHERE tmdb_id IS NOT NULL AND id NOT IN (SELECT title_id FROM title_languages)"
    ).fetchall()
    if limit is not None:
        rows = rows[:limit]

    for title_id, ttype, tmdb_id in rows:
        try:
            detail = client.tv(tmdb_id) if ttype == "tv" else client.movie(tmdb_id)
            if not detail:
                counts["not_found"] += 1
                continue
            lang_code = detail.get("original_language")
            if not lang_code:
                counts["no_language"] += 1
                continue
            lang_id = get_language_id(conn, lang_code)
            if not lang_id:
                counts["no_language"] += 1
                continue
            conn.execute(
                "INSERT OR IGNORE INTO title_languages (title_id, language_id, is_original) VALUES (?,?,1)",
                (title_id, lang_id),
            )
            conn.commit()
            counts["tagged"] += 1
        except Exception as e:
            log.exception("Error backfilling title_id=%s: %s", title_id, e)
            counts["errors"] += 1
        time.sleep(0.05)

    conn.close()
    return counts


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backfill missing title languages")
    parser.add_argument("--db", default="catalog.db")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    try:
        result = backfill(db_path=args.db, limit=args.limit)
    except TmdbError as e:
        print(f"FATAL: {e}", file=sys.stderr)
        sys.exit(2)
    print(json.dumps(result, indent=2))
