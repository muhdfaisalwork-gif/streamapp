"""More inspection of live catalog.db."""
import sqlite3
import os

c = sqlite3.connect(os.path.join(os.path.dirname(__file__), "catalog.db"))
cur = c.cursor()

print("=== media_assets distinct kinds ===")
for r in cur.execute(
    "SELECT COALESCE(kind, '<null>') AS k, COUNT(*) FROM media_assets GROUP BY kind ORDER BY 2 DESC"
):
    print(f"  {r[0]:30s} {r[1]}")

print()
print("=== media_assets sample (5 with omni in url) ===")
for r in cur.execute(
    "SELECT * FROM media_assets WHERE url LIKE '%omni%' OR url LIKE '%DuckKota%' LIMIT 5"
):
    print(" ", tuple(r))

print()
print("=== collections columns ===")
for row in cur.execute("PRAGMA table_info(collections)"):
    print(f"  {row[1]:25s} {row[2]}")

print()
print("=== genres columns ===")
for row in cur.execute("PRAGMA table_info(genres)"):
    print(f"  {row[1]:25s} {row[2]}")

print()
print("=== people count ===")
print("  people:", cur.execute("SELECT COUNT(*) FROM people").fetchone()[0])

print()
print("=== sources count ===")
print("  sources:", cur.execute("SELECT COUNT(*) FROM sources").fetchone()[0])

print()
print("=== Any tables with poster/logo/image/asset in name? ===")
for (t,) in cur.execute(
    "SELECT name FROM sqlite_master WHERE type='table' "
    "AND (name LIKE '%poster%' OR name LIKE '%logo%' "
    "     OR name LIKE '%image%' OR name LIKE '%asset%') "
    "AND name NOT LIKE 'sqlite_%'"
):
    print(f"  {t}")

print()
print("=== Any tables with streaming/facet/decade/actor/director/studio/animation in name? ===")
for (t,) in cur.execute(
    "SELECT name FROM sqlite_master WHERE type='table' "
    "AND (name LIKE '%stream%' OR name LIKE '%facet%' OR name LIKE '%decade%' "
    "     OR name LIKE '%actor%' OR name LIKE '%director%' OR name LIKE '%studio%' "
    "     OR name LIKE '%animation%') "
    "AND name NOT LIKE 'sqlite_%'"
):
    print(f"  {t}")

c.close()
