"""
purge_dead_titles.py — Purge unplayable dead titles (seasons=0, avail=0) from catalog.db

Safety rules:
1. Dry-run by default; require --apply to commit.
2. NEVER delete a title that has seasons > 0 or availability > 0.
3. NEVER delete discovery stubs (metadata_state = 'stub').
4. For dead titles that shadow a live title, re-point child tables to the live keeper first.
5. All operations inside a single atomic transaction.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import time
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent
DB = HERE / "catalog.db"
STATE = HERE / ".purge_dead_state.json"

CHILD_TABLES = [
    "title_genres", "title_countries", "title_languages", "title_audio_languages",
    "title_subtitle_languages", "title_collections", "title_collection",
    "title_aka", "title_audience_tags", "title_translations", "title_view_events",
    "title_cast", "title_crew", "title_actors", "title_directors", "title_studios",
    "title_animation_studios", "title_streaming_providers", "media_assets",
    "availability", "user_watchlist", "user_history", "title_classification",
    "seasons",
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Commit changes to database")
    args = parser.parse_args()

    conn = sqlite3.connect(str(DB), timeout=900)
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA foreign_keys = OFF")
    cur = conn.cursor()

    before_total = cur.execute("SELECT COUNT(*) FROM titles").fetchone()[0]
    print(f"Total titles before: {before_total:,}")

    # 1. Identify all dead unplayable titles (seasons=0 AND avail=0 AND metadata_state != 'stub')
    print("Scanning for dead unplayable titles...")
    dead_rows = cur.execute("""
        SELECT id, slug, title, year, type
        FROM titles t
        WHERE (SELECT COUNT(*) FROM seasons s WHERE s.title_id=t.id) = 0
          AND (SELECT COUNT(*) FROM availability a WHERE a.title_id=t.id) = 0
          AND metadata_state != 'stub'
    """).fetchall()

    dead_count = len(dead_rows)
    print(f"Dead unplayable titles found: {dead_count:,}")

    # Also check how many discovery stubs are safely preserved
    stub_count = cur.execute("SELECT COUNT(*) FROM titles WHERE metadata_state = 'stub'").fetchone()[0]
    print(f"Discovery stubs preserved: {stub_count:,}")

    # 2. Find live counterparts for shadow duplicates to re-point child tables
    print("Finding live counterparts for shadow duplicates...")
    live_rows = cur.execute("""
        SELECT id, slug, title, year
        FROM titles t
        WHERE (SELECT COUNT(*) FROM seasons s WHERE s.title_id=t.id) > 0
           OR (SELECT COUNT(*) FROM availability a WHERE a.title_id=t.id) > 0
    """).fetchall()

    by_title = defaultdict(list)
    for r in live_rows:
        t = (r[2] or "").strip().lower()
        if t:
            by_title[t].append(r)

    repoint_pairs = []
    pure_dead_ids = []

    for d in dead_rows:
        d_id, d_slug, d_title, d_year, d_type = d
        t_key = (d_title or "").strip().lower()
        candidates = by_title.get(t_key, [])
        if candidates:
            # Pick best match: match year if possible, otherwise first candidate
            match = next((c for c in candidates if c[3] == d_year), candidates[0])
            repoint_pairs.append((d_id, match[0]))
        else:
            pure_dead_ids.append(d_id)

    print(f"Shadow duplicates to re-point to live keepers: {len(repoint_pairs):,}")
    print(f"Pure dead titles to remove cleanly: {len(pure_dead_ids):,}")

    if not args.apply:
        print("\nDRY RUN ONLY — nothing written. Pass --apply to execute.")
        conn.close()
        return

    print("\nExecuting purge inside a single transaction...")
    started = time.time()
    try:
        conn.execute("BEGIN")

        # Step 2a: Re-point child rows for shadow duplicates
        for dead_id, live_id in repoint_pairs:
            for tbl in CHILD_TABLES:
                try:
                    cur.execute(f"UPDATE OR IGNORE {tbl} SET title_id = ? WHERE title_id = ?", (live_id, dead_id))
                    cur.execute(f"DELETE FROM {tbl} WHERE title_id = ?", (dead_id,))
                except sqlite3.OperationalError as e:
                    if "no such column" not in str(e) and "no such table" not in str(e):
                        raise

        # Step 2b: Delete child rows for pure dead titles in chunks of 500
        chunk_size = 500
        for i in range(0, len(pure_dead_ids), chunk_size):
            chunk = pure_dead_ids[i:i + chunk_size]
            placeholders = ",".join("?" for _ in chunk)
            for tbl in CHILD_TABLES:
                try:
                    cur.execute(f"DELETE FROM {tbl} WHERE title_id IN ({placeholders})", chunk)
                except sqlite3.OperationalError as e:
                    if "no such column" not in str(e) and "no such table" not in str(e):
                        raise

        # Step 2c: Delete all dead titles from titles table
        all_dead_ids = [d[0] for d in dead_rows]
        for i in range(0, len(all_dead_ids), chunk_size):
            chunk = all_dead_ids[i:i + chunk_size]
            placeholders = ",".join("?" for _ in chunk)
            cur.execute(f"DELETE FROM titles WHERE id IN ({placeholders})", chunk)

        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"\nABORTED: {e}")
        conn.close()
        raise

    after_total = cur.execute("SELECT COUNT(*) FROM titles").fetchone()[0]
    elapsed = time.time() - started
    print(f"Purge completed in {elapsed:.1f}s")
    print(f"Titles before: {before_total:,}")
    print(f"Titles after : {after_total:,} (removed {before_total - after_total:,})")

    audit_summary = {
        "timestamp": time.time(),
        "before": before_total,
        "after": after_total,
        "removed": before_total - after_total,
        "repointed_pairs": len(repoint_pairs),
        "preserved_stubs": stub_count,
    }
    STATE.write_text(json.dumps(audit_summary, indent=2), encoding="utf-8")
    print(f"Audit log written to {STATE.name}")

    conn.close()


if __name__ == "__main__":
    main()
