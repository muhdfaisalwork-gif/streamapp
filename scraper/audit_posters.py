import re
import sqlite3

def audit_moviebox():
    with open('backend/src/scrapers/MovieBoxScraper.js', 'r', encoding='utf-8') as f:
        content = f.read()

    # match m('id', 'Title', year, 'imdb', 'tmdb', ['Genre'], 'rating', runtime, 'desc', 'poster')
    pattern = re.compile(r"(?:m|v)\(\s*'([^']+)'\s*,\s*'([^']+)'\s*,\s*\d+\s*,\s*'([^']*)'\s*,\s*'([^']*)'\s*,\s*\[[^\]]*\]\s*,\s*[0-9.]+\s*,\s*\d+\s*,\s*'(?:[^'\\]|\\.)*'\s*,\s*'([^']*)'")
    matches = pattern.findall(content)
    print(f"MovieBoxScraper entries: {len(matches)}")
    bad_mb = []
    for item_id, title, imdb, tmdb, poster in matches:
        if not poster:
            bad_mb.append((item_id, title, "empty"))
        elif not (poster.startswith('/') or poster.startswith('http')):
            bad_mb.append((item_id, title, poster))
    print(f"MovieBoxScraper bad posters: {len(bad_mb)}")
    for b in bad_mb:
        print(" ", b)

def audit_db():
    conn = sqlite3.connect('scraper/cache.db')
    c = conn.cursor()
    rows = c.execute('SELECT id, title, poster, type FROM titles').fetchall()
    print(f"\nSQLite cache.db entries: {len(rows)}")
    bad_db = []
    for item_id, title, poster, mtype in rows:
        p = poster or ''
        if not p:
            bad_db.append((item_id, title, "empty"))
        elif not p.startswith('http'):
            bad_db.append((item_id, title, p))
        elif any(k in p for k in ['_pk.', '_tr.', '_eg.', '_ng.', 'ishq_murshid', 'kabli_pulao', 'suno_chanda', 'yaqeen', 'shehr', 'diyar', 'ranjha', 'sar_e_rah', 'kuch_ankahi', 'jaan_e', 'teefa', 'laal_kabootar', 'bin_roye']):
            bad_db.append((item_id, title, p))
    print(f"SQLite bad/fake posters: {len(bad_db)}")
    for b in bad_db:
        print(" ", b)

if __name__ == '__main__':
    audit_moviebox()
    audit_db()
