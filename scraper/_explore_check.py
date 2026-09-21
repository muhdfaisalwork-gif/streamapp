import sqlite3
import sys
sys.stdout.reconfigure(encoding='utf-8')
conn = sqlite3.connect(r'G:\streaming app\scraper\cache.db')

print("--- SELECT COUNT(*) FROM titles ---")
cur = conn.execute("SELECT COUNT(*) FROM titles")
print(cur.fetchone())

print()
print("--- All 'sher' IDs ---")
cur = conn.execute("SELECT id FROM titles WHERE id LIKE '%sher%'")
for r in cur.fetchall():
    print(r)

print()
print("--- Check 854 should be the count of curated ---")
cur = conn.execute("SELECT COUNT(*) FROM titles WHERE source='curated'")
print(cur.fetchone())

print()
print("--- What's the FIRST record ---")
cur = conn.execute("SELECT id, title, year, country, genres, source FROM titles WHERE source='curated' ORDER BY id LIMIT 5")
for r in cur.fetchall():
    print(r)

print()
print("--- Does cache.db have any titles with id like sherlock-XXXX ---")
cur = conn.execute("SELECT id FROM titles WHERE id GLOB 'sherlock*'")
for r in cur.fetchall():
    print(r)

print()
print("--- Curated titles: 677 only? ---")
cur = conn.execute("SELECT source, COUNT(*) FROM titles GROUP BY source")
for r in cur.fetchall():
    print(r)
