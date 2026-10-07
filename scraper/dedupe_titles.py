"""
dedupe_titles.py — merge duplicate title rows that share a tmdb_id.

Why this is urgent
------------------
The original ingest slugified as `name-year`; the scale-up ingest slugified as
`name-<tmdbid>`. The same show therefore got two rows, and the second one was
inserted later so it won every lookup:

    game-of-thrones-2011         id=395     seasons=9
    game-of-thrones-2011-1399    id=109969  seasons=0   <- what the app served

    friends-1994                 id=410     seasons=11
    friends-1994-1668            id=108974  seasons=0   <- what the app served

Game of Thrones has had its 9 seasons the whole time. Last of Us has had its 2.
Users were landing on empty clones, which is why season and episode selection
looked broken, and why the scripted filter had nothing to match on.

Safety rules, because this deletes rows
---------------------------------------
  * dry-run by default; --apply is required to write
  * never delete a row that holds season data while the sibling has none
  * child rows are re-pointed to the keeper BEFORE any delete
  * a keeper is chosen for data, never for recency
  * one transaction; aborts entirely on any error
  * a written state file records every merge so it can be inspected

Run:
    python dedupe_titles.py                    # report only
    python dedupe_titles.py --apply            # do it
    python dedupe_titles.py --apply --limit 50 # small batch first
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import time
from pathlib import Path

HERE = Path(__file__).parent
DB = HERE / "catalog.db"
STATE = HERE / ".dedupe_state.json"

# Every table that points at titles.id. Ordered so seasons moves before
# episodes, which hang off seasons.
CHILD_TABLES = [
    "title_genres", "title_countries", "title_languages", "title_audio_languages",
    "title_subtitle_languages", "title_collections", "title_collection",
    "title_aka", "title_audience_tags", "title_translations", "title_view_events",
    "title_cast", "title_crew", "title_actors", "title_directors", "title_studios",
    "title_animation_studios", "title_streaming_providers", "media_assets",
    "availability", "user_watchlist", "user_history", "title_classification",
    "seasons",
]


def season_count(conn, title_id: int) -> int:
    return conn.execute("SELECT COUNT(*) FROM seasons WHERE title_id = ?", (title_id,)).fetchone()[0]


def data_score(conn, title_id: int) -> tuple:
    """Ranking used to pick the keeper: richer row wins, never newer."""
    seasons = season_count(conn, title_id)
    av = conn.execute(
        "SELECT COUNT(*) FROM availability WHERE title_id = ? AND playback_url != ''", (title_id,)
    ).fetchone()[0]
    g = conn.execute("SELECT COUNT(*) FROM title_genres WHERE title_id = ?", (title_id,)).fetchone()[0]
    pop = conn.execute("SELECT COALESCE(popularity, 0) FROM titles WHERE id = ?", (title_id,)).fetchone()[0] or 0
    rating = conn.execute("SELECT COALESCE(rating, 0) FROM titles WHERE id = ?", (title_id,)).fetchone()[0] or 0
    ov = conn.execute("SELECT LENGTH(COALESCE(overview,'')) FROM titles WHERE id = ?", (title_id,)).fetchone()[0] or 0
    return (seasons, av, g, pop, rating, ov)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="actually write (default is report-only)")
    ap.add_argument("--limit", type=int, default=0, help="max duplicate groups to process")
    args = ap.parse_args()

    conn = sqlite3.connect(str(DB), timeout=300)
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA foreign_keys=OFF")   # re-point manually; constraints are not enforced here
    cur = conn.cursor()

    before = cur.execute("SELECT COUNT(*) FROM titles").fetchone()[0]

    groups = cur.execute("""
        SELECT tmdb_id, COUNT(*) c
        FROM titles WHERE tmdb_id IS NOT NULL AND tmdb_id > 0
        GROUP BY tmdb_id HAVING c > 1
        ORDER BY c DESC
    """).fetchall()
    if args.limit:
        groups = groups[: args.limit]

    print(f"titles before        : {before:,}")
    print(f"duplicate tmdb groups: {len(groups):,}")
    print(f"  (of {cur.execute('''SELECT SUM(c-1) FROM (SELECT COUNT(*) c FROM titles WHERE tmdb_id IS NOT NULL AND tmdb_id>0 GROUP BY tmdb_id HAVING c>1)''').fetchone()[0] or 0:,} redundant rows total)")
    print()

    report = []
    kept_total = 0
    removed_total = 0
    rescued = 0

    for tmdb_id, _c in groups:
        ids = [r[0] for r in cur.execute("SELECT id FROM titles WHERE tmdb_id = ?", (tmdb_id,))]
        if len(ids) < 2:
            continue
        scored = sorted(((data_score(conn, i), i) for i in ids), reverse=True)
        keeper = scored[0][1]
        clones = [i for i in ids if i != keeper]

        k_seasons = season_count(conn, keeper)
        clone_seasons = sum(season_count(conn, i) for i in clones)

        # Safety: never drop a row that has season data when the keeper has none.
        if k_seasons == 0 and clone_seasons > 0:
            alt = max(clones, key=lambda i: data_score(conn, i))
            keeper, clones = alt, [i for i in ids if i != alt]
            rescued += 1

        report.append({
            "tmdb_id": tmdb_id, "keeper": keeper, "removed": clones,
            "keeper_seasons": season_count(conn, keeper),
        })
        kept_total += 1
        removed_total += len(clones)

    print(f"groups to merge      : {kept_total:,}")
    print(f"rows to remove       : {removed_total:,}")
    print(f"keeper swapped       : {rescued} (keeper had no seasons, a clone did)")
    print()

    for r in report[:8]:
        print(f"  tmdb {r['tmdb_id']:<8} keep id={r['keeper']:<8} drop {r['removed']}  "
              f"keeper seasons={r['keeper_seasons']}")

    if not args.apply:
        print("\nDRY RUN — nothing written. Re-run with --apply to execute.")
        conn.close()
        return

    started = time.time()
    try:
        conn.execute("BEGIN")
        for r in report:
            keeper = r["keeper"]
            for clone in r["removed"]:
                for tbl in CHILD_TABLES:
                    try:
                        cur.execute(f"UPDATE OR IGNORE {tbl} SET title_id = ? WHERE title_id = ?",
                                    (keeper, clone))
                        # rows that already exist on the keeper stay; drop the leftovers
                        cur.execute(f"DELETE FROM {tbl} WHERE title_id = ?", (clone,))
                    except sqlite3.OperationalError as e:
                        if "no such column" not in str(e):
                            raise
                k_row = cur.execute("SELECT slug, title FROM titles WHERE id = ?", (keeper,)).fetchone()
                c_row = cur.execute("SELECT slug, title FROM titles WHERE id = ?", (clone,)).fetchone()
                cur.execute("DELETE FROM titles WHERE id = ?", (clone,))
                if k_row and c_row:
                    k_slug = k_row[0]
                    c_slug = c_row[0]
                    if (k_slug.endswith("-2") and not c_slug.endswith("-2")) or ("the-grand-tour" in k_slug and "re-zero" in c_slug):
                        collision = cur.execute("SELECT id FROM titles WHERE slug = ?", (c_slug,)).fetchone()
                        if not collision:
                            cur.execute("UPDATE titles SET slug = ? WHERE id = ?", (c_slug, keeper))
                            print(f"  Adopted cleaner slug for [{keeper}]: {k_slug} -> {c_slug}")
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"\nABORTED, nothing committed: {e}")
        conn.close()
        raise

    after = cur.execute("SELECT COUNT(*) FROM titles").fetchone()[0]
    STATE.write_text(json.dumps(report, indent=1), encoding="utf-8")
    print(f"\nmerged {kept_total:,} groups in {time.time()-started:.0f}s")
    print(f"titles: {before:,} -> {after:,}  (removed {before-after:,})")
    print(f"audit written to {STATE.name}")
    conn.close()


if __name__ == "__main__":
    main()
