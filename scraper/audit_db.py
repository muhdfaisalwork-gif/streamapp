import sqlite3
import re

conn = sqlite3.connect('scraper/cache.db')
c = conn.cursor()
c.execute("SELECT id, title, poster, imdb_id, tmdb_id FROM titles")
rows = c.fetchall()
print(f"Total titles: {len(rows)}")

empty_posters = []
relative_posters = []
fake_tmdb_posters = []
no_ids = []

for r in rows:
    _id, title, poster, imdb_id, tmdb_id = r
    if not poster or not poster.strip():
        empty_posters.append((_id, title))
    elif poster.startswith('/'):
        relative_posters.append((_id, title, poster))
    elif 'image.tmdb.org' in poster:
        # Real TMDB poster paths look like /7WTsnHkbA0FaG6R9twfFde0I9hl.jpg (alphanumeric hash)
        filename = poster.split('/')[-1]
        basename = filename.replace('.jpg', '').replace('.png', '')
        # if basename has underscores or words like 'welad_rizk', it's fake!
        if '_' in basename or '-' in basename or len(basename) < 15:
            fake_tmdb_posters.append((_id, title, poster))
    if not imdb_id and not tmdb_id:
        no_ids.append((_id, title))

print(f"Empty posters: {len(empty_posters)}")
print(f"Relative posters: {len(relative_posters)}")
print(f"Fake TMDb posters (underscores/words): {len(fake_tmdb_posters)}")
print(f"Titles with NO imdb_id and NO tmdb_id: {len(no_ids)}")

print("\nSample fake TMDb posters:")
for x in fake_tmdb_posters[:10]:
    print(" ", x)

print("\nSample relative posters:")
for x in relative_posters[:10]:
    print(" ", x)

print("\nSample empty posters:")
for x in empty_posters[:10]:
    print(" ", x)
