import re
import sqlite3

def audit_moviebox():
    with open('backend/src/scrapers/MovieBoxScraper.js', 'r', encoding='utf-8') as f:
        content = f.read()
    pattern = re.compile(r"(m|v)\(\s*'([^']+)'\s*,\s*'([^']+)'\s*,\s*(\d+)\s*,\s*'([^']*)'\s*,\s*'([^']*)'\s*,\s*\[([^\]]*)\]\s*,\s*([0-9.]+)\s*,\s*(\d+)\s*,\s*'((?:[^'\\]|\\.)*)'\s*,\s*'([^']*)'")
    matches = pattern.findall(content)
    print(f"=== MovieBoxScraper.js ===")
    print(f"Total entries: {len(matches)}")
    no_ids = [m for m in matches if not m[4] and not m[5]]
    print(f"No IDs: {len(no_ids)}")
    bad_posters = [m for m in matches if not m[10]]
    print(f"Bad posters: {len(bad_posters)}")
    tv = [m for m in matches if m[0] == 'v']
    movies = [m for m in matches if m[0] == 'm']
    print(f"Movies: {len(movies)} | TV: {len(tv)}")

def audit_cache():
    conn = sqlite3.connect('scraper/cache.db')
    c = conn.cursor()
    total = c.execute("SELECT COUNT(*) FROM titles").fetchone()[0]
    no_ids = c.execute("SELECT COUNT(*) FROM titles WHERE (tmdb_id IS NULL OR tmdb_id = '') AND (imdb_id IS NULL OR imdb_id = '')").fetchone()[0]
    has_tmdb = c.execute("SELECT COUNT(*) FROM titles WHERE tmdb_id IS NOT NULL AND tmdb_id != ''").fetchone()[0]
    has_imdb = c.execute("SELECT COUNT(*) FROM titles WHERE imdb_id IS NOT NULL AND imdb_id != ''").fetchone()[0]
    bad_poster = c.execute("SELECT COUNT(*) FROM titles WHERE poster IS NULL OR poster = '' OR NOT (poster LIKE 'http%')").fetchone()[0]
    movies = c.execute("SELECT COUNT(*) FROM titles WHERE type = 'movie'").fetchone()[0]
    tv = c.execute("SELECT COUNT(*) FROM titles WHERE type = 'tv'").fetchone()[0]

    print(f"\n=== scraper/cache.db ===")
    print(f"Total titles: {total}")
    print(f"No IDs: {no_ids}")
    print(f"Has TMDb: {has_tmdb}")
    print(f"Has IMDb: {has_imdb}")
    print(f"Bad posters: {bad_poster}")
    print(f"Movies: {movies} | TV: {tv}")
    conn.close()

if __name__ == '__main__':
    audit_moviebox()
    audit_cache()
