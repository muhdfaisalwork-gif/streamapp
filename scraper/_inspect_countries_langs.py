import sqlite3

conn = sqlite3.connect('scraper/catalog.db')
c = conn.cursor()

print("--- South Asian Languages ---")
for r in c.execute("""
    SELECT l.code, l.name, COUNT(tl.title_id) 
    FROM languages l 
    LEFT JOIN title_languages tl ON l.id = tl.language_id 
    WHERE l.code IN ('hi', 'ur', 'pa', 'bn', 'ta', 'te') 
    GROUP BY l.id
""").fetchall():
    print(r)

print("--- Pakistan Titles Sample ---")
for r in c.execute("""
    SELECT t.id, t.title, t.year, t.type, t.popularity, t.poster 
    FROM titles t
    JOIN title_countries tc ON t.id = tc.title_id
    JOIN countries c ON tc.country_id = c.id
    WHERE c.code = 'PK'
    ORDER BY t.popularity DESC
    LIMIT 5
""").fetchall():
    print(r)

print("--- Short Dramas Sample ---")
for r in c.execute("""
    SELECT t.id, t.title, t.poster 
    FROM titles t 
    WHERE t.type = 'short_drama' OR t.is_short_drama = 1 
    LIMIT 10
""").fetchall():
    print(r)
