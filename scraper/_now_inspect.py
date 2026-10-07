"""Inspect live catalog.db schema to plan additions."""
import sqlite3
import os

c = sqlite3.connect(os.path.join(os.path.dirname(__file__), "catalog.db"))
cur = c.cursor()

print("=== ALL TABLES + COLUMNS (live catalog.db) ===")
for (tname,) in cur.execute(
    "SELECT name FROM sqlite_master WHERE type='table' "
    "AND name NOT LIKE 'sqlite_%' ORDER BY name"
):
    print(f"\n--- {tname} ---")
    for row in cur.execute(f"PRAGMA table_info({tname})"):
        cid, name, ctype, notnull, default, pk = row
        flags = []
        if pk: flags.append("PK")
        if notnull: flags.append("NOT NULL")
        if default is not None: flags.append(f"DEFAULT={default!r}")
        print(f"  {name:30s} {ctype:20s} {' '.join(flags)}")

print("\n\n=== ROW COUNTS ===")
for (tname,) in cur.execute(
    "SELECT name FROM sqlite_master WHERE type='table' "
    "AND name NOT LIKE 'sqlite_%' ORDER BY name"
):
    cur.execute(f"SELECT COUNT(*) FROM {tname}")
    print(f"  {tname:30s} {cur.fetchone()[0]}")

print("\n\n=== EXISTING SOURCES (live catalog.db) ===")
for r in cur.execute("SELECT slug, name, type, is_legal FROM sources ORDER BY id"):
    print(f"  {r[0]:25s} {r[1]:30s} type={r[2]:10s} legal={r[3]}")

print("\n\n=== EXISTING COLLECTIONS (live, top 20) ===")
for r in cur.execute("SELECT slug, name, type FROM collections ORDER BY id LIMIT 20"):
    print(f"  {r[0]:35s} {r[1]:35s} type={r[2]}")

print("\n\n=== EXISTING STUDIOS (live, if table exists) ===")
try:
    for r in cur.execute("SELECT slug, name FROM studios ORDER BY id"):
        print(f"  {r[0]:30s} {r[1]}")
except sqlite3.OperationalError as e:
    print(f"  <no studios table: {e}>")

print("\n\n=== EXISTING GENRES (live) ===")
for r in cur.execute("SELECT slug, name FROM genres ORDER BY id"):
    print(f"  {r[0]:30s} {r[1]}")

print("\n\n=== PEOPLE SAMPLE (live, first 10) ===")
try:
    for r in cur.execute("SELECT * FROM people LIMIT 10"):
        print(f"  {tuple(r)}")
    print("\n  --- people columns ---")
    for row in cur.execute("PRAGMA table_info(people)"):
        print(f"  {row[1]:25s} {row[2]}")
except sqlite3.OperationalError as e:
    print(f"  <no people table: {e}>")

print("\n\n=== MEDIA_ASSETS SAMPLE (live) ===")
try:
    for r in cur.execute("SELECT * FROM media_assets LIMIT 5"):
        print(f"  {tuple(r)}")
    print("\n  --- media_assets columns ---")
    for row in cur.execute("PRAGMA table_info(media_assets)"):
        print(f"  {row[1]:25s} {row[2]}")
except sqlite3.OperationalError as e:
    print(f"  <no media_assets table: {e}>")

print("\n\n=== COLLECTION IMAGES SAMPLE (live, if exists) ===")
try:
    for r in cur.execute("SELECT * FROM collection_images LIMIT 5"):
        print(f"  {tuple(r)}")
except sqlite3.OperationalError as e:
    print(f"  <no collection_images table: {e}>")

c.close()
