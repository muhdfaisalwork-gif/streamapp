import sqlite3

conn = sqlite3.connect('scraper/catalog.db')
c = conn.cursor()

print("--- ALL SHORT DRAMAS ---")
for r in c.execute("SELECT id, slug, title, poster, backdrop FROM titles WHERE type='short_drama' OR is_short_drama=1").fetchall():
    print(r)
