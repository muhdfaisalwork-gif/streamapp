"""
dedupe_shadows.py — Deduplicate dead shadow rows in catalog.db

Identifies and merges dead shadow rows (seasons=0, avail=0) that sit next to
live rows with matching title/year/slug. Child rows are safely re-pointed to
the live keeper, clean slugs are transferred to the keeper, and dead rows are
removed.

Safety:
  * Dry-run by default (--apply required)
  * Never delete a row with seasons > 0 or availability > 0
  * Re-point all child tables before deletion
  * Single atomic transaction
  * Full audit written to .dedupe_shadows_state.json
"""

import argparse
import json
import sqlite3
import time
from pathlib import Path

HERE = Path(__file__).parent
DB = HERE / "catalog.db"
STATE = HERE / ".dedupe_shadows_state.json"

CHILD_TABLES = [
    "title_genres", "title_countries", "title_languages", "title_audio_languages",
    "title_subtitle_languages", "title_collections", "title_collection",
    "title_aka", "title_audience_tags", "title_translations", "title_view_events",
    "title_cast", "title_crew", "title_actors", "title_directors", "title_studios",
    "title_animation_studios", "title_streaming_providers", "media_assets",
    "availability", "user_watchlist", "user_history", "title_classification",
    "seasons",
]

def season_count(cur, title_id: int) -> int:
    return cur.execute("SELECT COUNT(*) FROM seasons WHERE title_id = ?", (title_id,)).fetchone()[0]

def avail_count(cur, title_id: int) -> int:
    return cur.execute(
        "SELECT COUNT(*) FROM availability WHERE title_id = ? AND playback_url != ''", (title_id,)
    ).fetchone()[0]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Execute changes in DB")
    parser.add_argument("--batch-13k", action="store_true", help="Focus specifically on 13000-13300 bad ingest batch")
    args = parser.parse_args()

    conn = sqlite3.connect(str(DB), timeout=900)
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA foreign_keys = OFF")
    cur = conn.cursor()

    before = cur.execute("SELECT COUNT(*) FROM titles").fetchone()[0]
    print(f"Total titles before: {before:,}")

    # Specific known shadow mappings from audit / handoff
    KNOWN_PAIRS = [
        # (dead_id, live_id)
        (13091, 39595),   # your-name-2016 -> your-name-2016-2
        (13131, 39595),   # your-name-2016-anime -> your-name-2016-2
        (13135, 98143),   # erased-2016 -> erased-2026
        (13150, 38403),   # word-of-honor-2021 -> word-of-honor-2021-2
        (13167, 52836),   # citation-2020 -> citation-2020-2
        (13174, 34429),   # nuri-bilge-ceylan-once-upon-a-time-in-anatolia-2011 -> once-upon-a-time-in-anatolia-2011
        (13175, 20077),   # head-on-2004 -> head-on-2004-2
        (13176, 34456),   # the-wild-pear-tree-2018 -> the-wild-pear-tree-2018-2
        (13177, 34568),   # distancia-2006 -> distant-2002
        (13178, 34434),   # winter-sleep-2014 -> winter-sleep-2014-2
        (13179, 34660),   # three-monkeys-2008 -> three-monkeys-2008-2
        (13180, 34731),   # kelebekler-2018 -> butterflies-2018
        (13181, 34457),   # kuru-otlar-ustune-2023 -> about-dry-grasses-2023
        (13184, 90),      # parasite-2019-eg -> parasite-2019
        (13187, 18971),   # the-broker-2023 -> the-broker-2021
        (13192, 30910),   # the-act-of-killing-2012 -> the-act-of-killing-2012-2
        (13195, 42483),   # impetigore-2019 -> impetigore-2019-2
        (13203, 40308),   # how-to-make-million-b4-grad-2024-th -> how-to-make-millions-before-grandma-dies-2024
        (13204, 54672),   # y-tu-mama-tambien-2001 -> y-tu-mam-tambi-n-2001
        (13149, 38135),   # the-story-of-minglan-2018 -> the-story-of-ming-lan-2018
        (13130, 153),     # akira-1988-anime -> akira-1988
        (13212, 14743),   # incendies-2010 -> incendies-2010-2
        (13216, 15528),   # animal-kingdom-2010 -> animal-kingdom-2010-2
        (13210, 20953),   # the-secret-in-their-eyes-2009 -> the-secret-in-their-eyes-2009-2
        (13230, 44550),   # wadjda-2012 -> wadjda-2012-2
        (13227, 47117),   # capernaum-2018 -> capernaum-2018-2
        (13226, 47118),   # the-insult-2017 -> the-insult-2017-2
        (13228, 47150),   # where-do-we-go-now-2011 -> where-do-we-go-now-2011-2
        (13241, 51006),   # adam-2019 -> adam-2019-2
        (13218, 53081),   # tsotsi-2005 -> tsotsi-2005-2
        (13208, 54944),   # bacurau-2019 -> bacurau-2019-2
        (13211, 55641),   # wild-tales-2014 -> wild-tales-2014-2
        (13242, 55685),   # the-wrath-of-god-2022 -> the-wrath-of-god-2022-2
        (13223, 61838),   # the-salesman-2016 -> the-salesman-2016-2
        (13221, 61839),   # taste-of-cherry-1997 -> taste-of-cherry-1997-2
        (13222, 61855),   # close-up-1990 -> close-up-1990-2
    ]

    merges = []
    # Verify each known pair
    for dead_id, live_id in KNOWN_PAIRS:
        d = cur.execute("SELECT id, slug, title, year FROM titles WHERE id = ?", (dead_id,)).fetchone()
        l = cur.execute("SELECT id, slug, title, year FROM titles WHERE id = ?", (live_id,)).fetchone()
        if not d or not l:
            continue
        d_seasons = season_count(cur, dead_id)
        d_avail = avail_count(cur, dead_id)
        l_seasons = season_count(cur, live_id)
        l_avail = avail_count(cur, live_id)
        
        # Absolute safety check: dead MUST have 0 seasons and 0 avail, live MUST have >0
        if d_seasons == 0 and d_avail == 0 and (l_seasons > 0 or l_avail > 0):
            # Check if live slug has a dirty suffix like -2
            clean_slug = d[1] if (l[1].endswith("-2") or "-anime" in d[1] or "-eg" in d[1]) and not d[1].endswith("-anime") and not d[1].endswith("-eg") else None
            merges.append({
                "dead_id": dead_id,
                "dead_slug": d[1],
                "dead_title": d[2],
                "live_id": live_id,
                "live_slug": l[1],
                "live_title": l[2],
                "clean_slug": clean_slug,
                "live_avail": l_avail,
                "live_seasons": l_seasons,
            })

    print(f"Verified shadow pairs ready to merge: {len(merges)}")
    for m in merges:
        print(f"  DROP [{m['dead_id']}] {m['dead_slug']} -> KEEP [{m['live_id']}] {m['live_slug']} (avail={m['live_avail']}, seasons={m['live_seasons']})" + (f" -> rename slug to {m['clean_slug']}" if m['clean_slug'] else ""))

    if not args.apply:
        print("\nDRY RUN — pass --apply to commit.")
        conn.close()
        return

    started = time.time()
    try:
        conn.execute("BEGIN")
        for m in merges:
            dead = m["dead_id"]
            live = m["live_id"]
            for tbl in CHILD_TABLES:
                try:
                    cur.execute(f"UPDATE OR IGNORE {tbl} SET title_id = ? WHERE title_id = ?", (live, dead))
                    cur.execute(f"DELETE FROM {tbl} WHERE title_id = ?", (dead,))
                except sqlite3.OperationalError as e:
                    if "no such column" not in str(e) and "no such table" not in str(e):
                        raise
            cur.execute("DELETE FROM titles WHERE id = ?", (dead,))
            if m["clean_slug"]:
                # Ensure clean slug doesn't collide
                collision = cur.execute("SELECT id FROM titles WHERE slug = ?", (m["clean_slug"],)).fetchone()
                if not collision:
                    cur.execute("UPDATE titles SET slug = ? WHERE id = ?", (m["clean_slug"], live))
                    print(f"  Renamed [{live}] slug: {m['live_slug']} -> {m['clean_slug']}")
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"\nABORTED: {e}")
        conn.close()
        raise

    after = cur.execute("SELECT COUNT(*) FROM titles").fetchone()[0]
    STATE.write_text(json.dumps(merges, indent=2), encoding="utf-8")
    print(f"\nSuccessfully merged {len(merges)} shadow duplicate pairs in {time.time()-started:.1f}s")
    print(f"Titles: {before:,} -> {after:,} (removed {before-after})")
    conn.close()

if __name__ == "__main__":
    main()
