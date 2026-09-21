import sqlite3

conn = sqlite3.connect('scraper/cache.db')
c = conn.cursor()

c.execute("""
    SELECT source,
           COUNT(*) as total,
           SUM(CASE WHEN poster IS NULL OR poster = '' THEN 1 ELSE 0 END) as empty_poster,
           SUM(CASE WHEN poster LIKE '%_pk.jpg%' OR poster LIKE '%_tr.jpg%' OR poster LIKE '%_eg.jpg%' OR poster LIKE '%welad%' OR poster LIKE '%hashashin%' THEN 1 ELSE 0 END) as fake_poster,
           SUM(CASE WHEN poster LIKE '/%' THEN 1 ELSE 0 END) as relative_poster,
           SUM(CASE WHEN (imdb_id IS NULL OR imdb_id = '') AND (tmdb_id IS NULL OR tmdb_id = '') THEN 1 ELSE 0 END) as no_ids
    FROM titles
    GROUP BY source
""")

print(f"{'Source':<15} | {'Total':<6} | {'Empty Poster':<12} | {'Fake Poster':<12} | {'Rel Poster':<10} | {'No IDs':<8}")
print("-" * 75)
for row in c.fetchall():
    s, tot, emp, fkp, rel, noid = row
    print(f"{s:<15} | {tot:<6} | {emp:<12} | {fkp:<12} | {rel:<10} | {noid:<8}")
