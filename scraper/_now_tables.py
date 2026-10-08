"""List all tables in catalog.db."""
import sqlite3
import os

c = sqlite3.connect(os.path.join(os.path.dirname(__file__), "catalog.db"))
cur = c.cursor()
print("=== ALL TABLES IN LIVE catalog.db ===")
for row in cur.execute(
    "SELECT name FROM sqlite_master WHERE type='table' "
    "AND name NOT LIKE 'sqlite_%' ORDER BY name"
):
    print(" ", row[0])
c.close()
