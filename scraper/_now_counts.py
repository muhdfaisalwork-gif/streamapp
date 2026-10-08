import sqlite3, os, sys, traceback
c = sqlite3.connect(os.path.join(os.path.dirname(__file__), "catalog.db"))
cur = c.cursor()
print("=== LIVE catalog.db row counts ===")
for row in cur.execute(
    "SELECT name FROM sqlite_master WHERE type='table' "
    "AND name NOT LIKE 'sqlite_%' ORDER BY name"
):
    t = row[0]
    try:
        cur.execute("SELECT COUNT(*) FROM " + t)
        n = cur.fetchone()[0]
        print("  " + t.ljust(30) + " " + str(n))
    except Exception as e:
        print("  " + t.ljust(30) + " ERROR: " + str(e))
c.close()
