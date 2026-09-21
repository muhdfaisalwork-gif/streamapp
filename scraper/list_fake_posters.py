import sqlite3

conn = sqlite3.connect('scraper/cache.db')
c = conn.cursor()

c.execute("""
    SELECT id, source, title, poster, imdb_id, tmdb_id
    FROM titles
    WHERE poster LIKE '%_pk.jpg%' OR poster LIKE '%_tr.jpg%' OR poster LIKE '%_eg.jpg%'
       OR poster LIKE '%welad%' OR poster LIKE '%hashashin%' OR poster LIKE '%sang_e_mah%'
       OR poster LIKE '%gentleman%' OR poster LIKE '%khaie%'
""")

print("Fake poster rows:")
for r in c.fetchall():
    print(r)
