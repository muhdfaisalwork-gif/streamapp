"""Inspect live catalog.db current state."""
import sqlite3, os

c = sqlite3.connect(os.path.join(os.path.dirname(__file__), "catalog.db"))
cur = c.cursor()

print("=== current state ===")
print("total titles:", cur.execute("SELECT COUNT(*) FROM titles").fetchone()[0])
print()

print("=== by source (top 25) ===")
for r in cur.execute(
    "SELECT s.slug, s.name, s.type, COUNT(a.id) AS rows "
    "FROM sources s LEFT JOIN availability a ON a.source_id = s.id "
    "GROUP BY s.id ORDER BY rows DESC NULLS LAST LIMIT 25"
):
    print("  " + str(r[0]).ljust(25) + " " + str(r[1]).ljust(30) +
          " type=" + str(r[2]).ljust(20) + " rows=" + str(r[3] or 0))

print()
print("=== titles by tmdb_id coverage ===")
cur.execute("SELECT COUNT(*) FROM titles WHERE tmdb_id IS NOT NULL AND tmdb_id > 0")
print("  with tmdb_id:", cur.fetchone()[0])
cur.execute("SELECT COUNT(*) FROM titles WHERE tmdb_id IS NULL OR tmdb_id = 0")
print("  without tmdb_id:", cur.fetchone()[0])

print()
print("=== availability status ===")
for r in cur.execute("SELECT status, COUNT(*) FROM availability GROUP BY status"):
    print("  " + str(r[0]).ljust(15) + " " + str(r[1]))

print()
print("=== titles by type ===")
for r in cur.execute("SELECT type, COUNT(*) FROM titles GROUP BY type ORDER BY 2 DESC"):
    print("  " + str(r[0]).ljust(15) + " " + str(r[1]))

print()
print("=== titles with poster ===")
cur.execute(
    "SELECT COUNT(*) FROM titles WHERE poster IS NOT NULL "
    "AND poster != ''"
)
print("  with poster:", cur.fetchone()[0])

print()
print("=== availability rows by source_id ===")
cur.execute(
    "SELECT source_id, COUNT(*) FROM availability GROUP BY source_id ORDER BY 2 DESC"
)
for r in cur.execute(
    "SELECT s.slug, s.name, COUNT(a.id) "
    "FROM availability a JOIN sources s ON a.source_id = s.id "
    "GROUP BY a.source_id ORDER BY 3 DESC LIMIT 25"
):
    print("  src_id=" + str(r[0]) + " " + str(r[1]).ljust(25) + " " + str(r[2]))

print()
print("=== existing tmdb_ids sample (10 random) ===")
for r in cur.execute(
    "SELECT id, title, year, tmdb_id FROM titles "
    "WHERE tmdb_id IS NOT NULL AND tmdb_id > 0 ORDER BY RANDOM() LIMIT 10"
):
    print("  id=" + str(r[0]) + " " + str(r[1]) + " (" + str(r[2]) + ") tmdb=" + str(r[3]))

print()
print("=== titles table schema ===")
for row in cur.execute("PRAGMA table_info(titles)"):
    print("  " + str(row[1]).ljust(20) + " " + str(row[2]))

c.close()
