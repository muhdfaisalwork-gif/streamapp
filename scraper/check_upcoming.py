import sqlite3

conn = sqlite3.connect("scraper/catalog.db")
cur = conn.cursor()
rows = cur.execute(
    "SELECT t.id, t.title, t.year, t.status, COUNT(a.id) "
    "FROM titles t LEFT JOIN availability a ON a.title_id=t.id "
    "WHERE t.status='upcoming' OR t.year >= 2026 "
    "GROUP BY t.id ORDER BY t.popularity DESC LIMIT 10"
).fetchall()

print("Upcoming / Coming Soon titles and their mirror counts:")
for r in rows:
    print(f"  {r[1]} ({r[2]}) [{r[3]}]: {r[4]} mirror/availability sources")

total_upcoming = cur.execute("SELECT COUNT(*) FROM titles WHERE status='upcoming' OR year >= 2026").fetchone()[0]
print(f"\nTotal upcoming/2026+ titles in catalog: {total_upcoming:,}")
