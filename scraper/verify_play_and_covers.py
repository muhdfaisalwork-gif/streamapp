import urllib.request
import json
import sys

BASE = 'http://localhost:3000/api/v1'

def get(path):
    req = urllib.request.Request(f"{BASE}{path}", headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=8) as res:
        return json.loads(res.read())

def post(path, body):
    data = json.dumps(body).encode('utf-8')
    req = urllib.request.Request(f"{BASE}{path}", data=data, headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=8) as res:
        return json.loads(res.read())

print("============================================================")
print("RUNNING STREAMAPP PLAYBACK & COVER VERIFICATION")
print("============================================================")

# 1. Health
h = get('/health')
print(f"Health: {h.get('status')} | liveTitles: {h.get('liveTitlesCached')} | total: {h.get('totalUniqueTitles')}")

# 2. Audit Pakistani Titles & Covers
pk = get('/live/country/pakistan')
print(f"\nPakistani titles returned: {pk.get('count', 0)}")
bad_pk_posters = 0
for it in pk.get('results', []):
    poster = it.get('poster') or ''
    if not poster.startswith('http') or any(k in poster for k in ['_pk.', 'ishq_murshid', 'kabli_pulao', 'suno_chanda']):
        bad_pk_posters += 1
        print(f"  [BAD POSTER] {it.get('title')}: {poster}")
print(f"  Bad posters in Pakistani slate: {bad_pk_posters}")
assert bad_pk_posters == 0, "Found bad posters in Pakistani slate!"

# 3. Test Khaie S1E1 Stream Resolution
khaie_body = {
    "url": "pk-khaie",
    "sourceName": "StreamApp National Slate",
    "title": "Khaie",
    "tmdbId": "244673",
    "imdbId": "tt30477931",
    "season": 1,
    "episode": 1
}
k_res = post('/stream', khaie_body)
print(f"\nPOST /stream (Khaie S1E1): status={k_res.get('status')}")
print(f"  Primary Stream URL: {k_res.get('streamUrl')}")
streams = k_res.get('streams', [])
print(f"  Total Mirrors: {len(streams)}")
has_vidsrc_xyz = False
for s in streams:
    print(f"    - [{s.get('label')}] ({s.get('quality')}): {s.get('url')}")
    if 'vidsrc.xyz' in s.get('url', ''):
        has_vidsrc_xyz = True
assert not has_vidsrc_xyz, "FATAL: Dead vidsrc.xyz still found in Khaie streams!"
assert any('youtube' in s.get('provider', '') for s in streams), "YouTube mirror missing from Khaie!"
assert k_res.get('streamUrl') and not 'vidsrc.xyz' in k_res.get('streamUrl'), "Primary stream is dead or missing!"

# 4. Test TV Episodes Endpoint with title
ep_res = get('/tv/244673/episodes?season=1&title=Khaie')
print(f"\nGET /tv/244673/episodes?season=1&title=Khaie: count={ep_res.get('count')}")
episodes = ep_res.get('episodes', [])
assert len(episodes) > 0, "No episodes returned!"
ep1_sources = episodes[0].get('sources', [])
print(f"  Episode 1 sources count: {len(ep1_sources)}")
for s in ep1_sources:
    print(f"    - [{s.get('label')}]: {s.get('url')}")
    assert 'vidsrc.xyz' not in s.get('url', ''), "vidsrc.xyz found in episode sources!"

# 5. Test Jawan Playback
jawan_body = {
    "title": "Jawan",
    "tmdbId": "939335",
    "imdbId": "tt15340522"
}
j_res = post('/stream', jawan_body)
print(f"\nPOST /stream (Jawan Movie): status={j_res.get('status')}")
print(f"  Primary Stream URL: {j_res.get('streamUrl')}")
j_streams = j_res.get('streams', [])
print(f"  Mirrors count: {len(j_streams)}")
for s in j_streams:
    assert 'vidsrc.xyz' not in s.get('url', ''), "vidsrc.xyz found in Jawan streams!"

# 6. Categories & Genres Audit
cat_res = get('/categories')
all_cats = cat_res.get('categories', [])
print(f"\nAuditing {len(all_cats)} categories for blank/bad covers...")
total_cat_bad = 0
for cat in all_cats:
    for item in cat.get('items', []):
        p = item.get('poster') or ''
        if not p.startswith('http') or any(k in p for k in ['_pk.', '_tr.', 'ishq_murshid', 'kabli_pulao']):
            total_cat_bad += 1
            print(f"  [BAD POSTER in {cat.get('id')}]: {item.get('title')}: {p}")

print(f"Total bad covers across all categories: {total_cat_bad}")
assert total_cat_bad == 0, "Found bad covers in categories!"

print("\n============================================================")
print("SUCCESS: ALL PLAYBACK & COVER VERIFICATIONS PASSED 100%!")
print("============================================================")
