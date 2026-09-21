import sqlite3

conn = sqlite3.connect('scraper/cache.db')
c = conn.cursor()
c.execute("SELECT source, COUNT(*) FROM titles GROUP BY source")
print("Counts by source:")
for s, count in c.fetchall():
    print(f"  {s}: {count}")

c.execute("SELECT id, source, title, poster, imdb_id, tmdb_id FROM titles WHERE poster LIKE '%sang_e_mah%'")
print("sang_e_mah row:", c.fetchall())

c.execute("SELECT DISTINCT source FROM titles WHERE poster LIKE '%_pk.jpg%' OR poster LIKE '%_tr.jpg%'")
print("Sources with _pk.jpg:", c.fetchall())
