import sqlite3
db = sqlite3.connect('catalog.db')
db.row_factory = sqlite3.Row
print("Recently backfilled (real TMDB poster URLs):")
for r in db.execute("SELECT id, slug, tmdb_id, rating, imdb_id, poster, backdrop FROM titles WHERE tmdb_id IS NOT NULL AND poster LIKE '%image.tmdb.org%' ORDER BY id DESC LIMIT 10"):
    p = (r['poster'] or '')[:80]
    b = (r['backdrop'] or '')[:80]
    print(f"  id={r['id']} tmdb={r['tmdb_id']} rating={r['rating']} imdb={r['imdb_id']}")
    print(f"    poster:   {p}")
    print(f"    backdrop: {b}")
