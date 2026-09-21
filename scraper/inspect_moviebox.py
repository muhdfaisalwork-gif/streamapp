import re

with open('backend/src/scrapers/MovieBoxScraper.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern for m(id, title, year, imdb, tmdb, genres, rating, runtime, desc, poster)
pattern = re.compile(
    r"(m|v)\(\s*'([^']+)'\s*,\s*'([^']+)'\s*,\s*(\d+)\s*,\s*'([^']*)'\s*,\s*'([^']*)'\s*,\s*\[([^\]]*)\]\s*,\s*([0-9.]+)\s*,\s*(\d+)\s*,\s*'((?:[^'\\]|\\.)*)'\s*,\s*'([^']*)'"
)

matches = list(pattern.finditer(content))
print(f"Total entries in MovieBoxScraper.js: {len(matches)}")

no_poster = []
no_ids = []
fake_posters = []
valid_entries = []

for m in matches:
    fn, mid, title, year, imdb, tmdb, genres, rating, runtime, desc, poster = m.groups()
    if not poster or not poster.strip():
        no_poster.append((mid, title))
    elif '_' in poster.split('/')[-1] or '-' in poster.split('/')[-1]:
        fake_posters.append((mid, title, poster))
    if not imdb and not tmdb:
        no_ids.append((mid, title))

print(f"No poster: {len(no_poster)}")
print(f"Fake poster: {len(fake_posters)}")
print(f"No IDs: {len(no_ids)}")

print("\nSample fake posters in MovieBoxScraper.js:")
for x in fake_posters[:5]:
    print(" ", x)
