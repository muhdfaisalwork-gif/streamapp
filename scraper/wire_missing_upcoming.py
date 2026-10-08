import sqlite3

conn = sqlite3.connect('scraper/catalog.db')
c = conn.cursor()
src = c.execute("SELECT id, slug, name FROM sources WHERE slug='vidsrc_icu' OR is_legal=1 LIMIT 1").fetchone()
print("Using source:", src)
c.execute("""
    INSERT OR IGNORE INTO availability (title_id, source_id, kind, status, external_url, playback_url)
    VALUES (?, ?, 'playback', 'available', 'https://vidsrc.icu/embed/movie/13411', 'https://vidsrc.icu/embed/movie/13411')
""", (13411, src[0]))
conn.commit()

missing_count = c.execute("""
    SELECT COUNT(*) FROM titles t 
    WHERE (t.status = 'upcoming' OR t.year >= 2026) 
    AND t.id NOT IN (SELECT title_id FROM availability WHERE status = 'available')
""").fetchone()[0]
print(f"Remaining upcoming titles missing availability: {missing_count}")
conn.close()
