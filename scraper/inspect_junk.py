import sqlite3

conn = sqlite3.connect('scraper/cache.db')
c = conn.cursor()

c.execute("SELECT id, source, title, poster, imdb_id, tmdb_id, source_url FROM titles WHERE source IN ('MovieBoxHD', 'HDOBox', 'BeeTV', 'YTS') LIMIT 10")
for r in c.fetchall():
    print(r)
