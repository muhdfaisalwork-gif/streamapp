"""Export the top-rated MovieHub picks as a static JSON for the bundle."""
import sqlite3, json, os, re
db_path = r'G:\streaming app\scraper\catalog.db'
out_path = r'G:\streaming app\frontend\dist\featured.json'
db = sqlite3.connect(db_path)
db.row_factory = sqlite3.Row
cur = db.cursor()

# Top movies + TV with poster & backdrop — visible offline in the HomeScreen.
cur.execute("""
SELECT id, slug, title, original_title, type, year, runtime, rating,
       overview, poster, backdrop, certification, popularity,
       (SELECT GROUP_CONCAT(g.name, ', ')
          FROM title_genres tg JOIN genres g ON tg.genre_id=g.id
          WHERE tg.title_id=t.id) AS genres,
       (SELECT c.code FROM title_countries tc
          JOIN countries c ON tc.country_id=c.id
          WHERE tc.title_id=t.id LIMIT 1) AS country_code,
       (SELECT c.name FROM title_countries tc
          JOIN countries c ON tc.country_id=c.id
          WHERE tc.title_id=t.id LIMIT 1) AS country_name,
       (SELECT GROUP_CONCAT(l.code, ',')
          FROM title_languages tl JOIN languages l ON tl.language_id=l.id
          WHERE tl.title_id=t.id) AS languages
FROM titles t
WHERE poster IS NOT NULL AND poster <> ''
  AND backdrop IS NOT NULL AND backdrop <> ''
  AND rating IS NOT NULL AND rating >= 6.5
ORDER BY (rating * 1.5 + COALESCE(popularity, 0)) DESC
LIMIT 80
""")
rows = cur.fetchall()

def safe_str(s, max_len=200):
    if s is None: return None
    s = re.sub(r'\s+', ' ', str(s))
    return s[:max_len] if len(s) > max_len else s

picks = []
for r in rows:
    picks.append({
        'id': r['id'],
        'slug': r['slug'],
        'title': safe_str(r['title'], 200),
        'original_title': safe_str(r['original_title'], 200),
        'type': r['type'],
        'year': r['year'],
        'runtime': r['runtime'],
        'rating': r['rating'],
        'overview': safe_str(r['overview'], 400),
        'poster': r['poster'],
        'backdrop': r['backdrop'],
        'certification': r['certification'],
        'popularity': r['popularity'],
        'genres': safe_str(r['genres'], 200),
        'country_code': r['country_code'],
        'country_name': r['country_name'],
        'languages': safe_str(r['languages'], 200),
    })

db.close()

payload = {
    'source': 'streamapp-static',
    'generated_at': __import__('datetime').datetime.utcnow().isoformat() + 'Z',
    'pick_count': len(picks),
    'picks': picks,
}

with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(payload, f, ensure_ascii=False, indent=1)

print(f'wrote {len(picks)} featured picks to {out_path}')
print(f'size: {os.path.getsize(out_path):,} bytes')
print('top 5 by rating*popularity:')
for p in picks[:5]:
    print(f'  - {p["title"]} ({p["year"]}) rating={p["rating"]:.1f} type={p["type"]}')
