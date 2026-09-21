import requests
import sys

sys.stdout.reconfigure(encoding='utf-8')

print("=" * 60)
print("RUNNING COMPREHENSIVE STREAMAPP VERIFICATION")
print("=" * 60)

# 1. Test Node Health & Python stats
r = requests.get('http://localhost:3000/api/v1/health')
print(f"Health: {r.status_code} - {r.json()}")

# 2. Test Action Genre endpoint
r = requests.get('http://localhost:3000/api/v1/live/genre/Action?page=1&limit=50')
data = r.json()
results = data.get('results', [])
print(f"\n/live/genre/Action: returned {len(results)} items")
bad_posters = [x for x in results if not x.get('poster') or not x.get('poster', '').startswith('http')]
volume_titles = [x for x in results if 'Volume ' in x.get('title', '')]
unplayable = [x for x in results if not x.get('tmdbId') and not x.get('imdbId')]
print(f"  Bad posters: {len(bad_posters)}")
print(f"  Volume titles: {len(volume_titles)}")
print(f"  Unplayable items (no IDs): {len(unplayable)}")

print("\nSample Action Items:")
for i, item in enumerate(results[:5]):
    print(f"  {i+1}. {item['title']} ({item.get('year')}) | TMDb: {item.get('tmdbId')} | Poster: {item.get('poster')[:60]}...")

# 3. Test Jawan search
r = requests.get('http://localhost:3000/api/v1/search?q=Jawan')
data = r.json()
results = data.get('results', [])
print(f"\nSearch 'Jawan': returned {len(results)} items")
jawan = next((x for x in results if x.get('title') == 'Jawan'), None)
if jawan:
    print(f"  Jawan item found: TMDb={jawan.get('tmdbId')} (expected 939335) | IMDb={jawan.get('imdbId')} | Poster={jawan.get('poster')}")
    assert str(jawan.get('tmdbId')) == '939335', f"Expected 939335, got {jawan.get('tmdbId')}"
else:
    print("  WARNING: Jawan not found in search results!")

# 4. Test Doctor Who search
r = requests.get('http://localhost:3000/api/v1/search?q=Doctor+Who')
data = r.json()
results = data.get('results', [])
print(f"\nSearch 'Doctor Who': returned {len(results)} items")
dw = next((x for x in results if 'Doctor Who' in x.get('title', '') and x.get('type') == 'tv'), None)
if dw:
    print(f"  Doctor Who TV found: TMDb={dw.get('tmdbId')} (expected 57243) | IMDb={dw.get('imdbId')} | Type={dw.get('type')}")
    assert str(dw.get('tmdbId')) == '57243', f"Expected 57243, got {dw.get('tmdbId')}"
else:
    print("  WARNING: Doctor Who TV series not found!")

# 5. Test Multi-Mirror Stream Resolution
r = requests.post('http://localhost:3000/api/v1/stream', json={'tmdbId': '939335'})
data = r.json()
print(f"\nPOST /stream (Jawan TMDb 939335): status={r.status_code}")
print(f"  Primary stream: {data.get('streamUrl')}")
mirrors = data.get('streams', [])
print(f"  Mirrors count: {len(mirrors)}")
for m in mirrors:
    print(f"    - [{m.get('label')}] ({m.get('quality')}): {m.get('url')}")
assert len(mirrors) >= 4, f"Expected at least 4 mirrors, got {len(mirrors)}"

# 6. Test Categories endpoint
r = requests.get('http://localhost:3000/api/v1/categories')
data = r.json()
categories = data.get('categories', [])
print(f"\nCategories: returned {len(categories)} categories")
cat_bad_posters = 0
cat_volume_titles = 0
cat_unplayable = 0
for cat in categories:
    for it in cat.get('items', []):
        if not it.get('poster') or not it.get('poster', '').startswith('http'):
            cat_bad_posters += 1
        if 'Volume ' in it.get('title', ''):
            cat_volume_titles += 1
        if not it.get('tmdbId') and not it.get('imdbId'):
            cat_unplayable += 1

print(f"  All categories total items audited:")
print(f"    Bad posters across all categories: {cat_bad_posters}")
print(f"    Volume titles across all categories: {cat_volume_titles}")
print(f"    Unplayable items across all categories: {cat_unplayable}")

assert cat_bad_posters == 0, f"Found {cat_bad_posters} bad posters"
assert cat_volume_titles == 0, f"Found {cat_volume_titles} volume titles"
assert cat_unplayable == 0, f"Found {cat_unplayable} unplayable items"

print("\nALL VERIFICATION CHECKS PASSED PERFECTLY!")
