import urllib.request
import re
import json

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

titles_to_check = [
    ('Khaie', 'tv', '244673'),
    ('Ishq Murshid', 'tv', '236402'),
    ('Kabli Pulao', 'tv', '229342'),
    ('Suno Chanda', 'tv', '80173'),
    ('Yaqeen Ka Safar', 'tv', '71175'),
    ('Shehr-e-Zaat', 'tv', '46125'),
    ('Diyar-e-Dil', 'tv', '62688'),
    ('Ranjha Ranjha Kardi', 'tv', '84318'),
    ('Sar-e-Rah', 'tv', '219532'),
    ('Kuch Ankahi', 'tv', '217643'),
    ('Jaan-e-Jahan', 'tv', '242013'),
    ('Parizaad', 'tv', '130542'),
    ('Tere Bin', 'tv', '216972'),
    ('Kabhi Main Kabhi Tum', 'tv', '260424'),
    ('Teefa in Trouble', 'movie', '460592'),
    ('Laal Kabootar', 'movie', '587786'),
    ('Bin Roye', 'movie', '349147')
]

results = {}

for name, mtype, tmdb_id in titles_to_check:
    url = f"https://www.themoviedb.org/{mtype}/{tmdb_id}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=5) as res:
            html = res.read().decode('utf-8', errors='ignore')
            # Look for og:image or poster_path
            og_match = re.search(r'property="og:image"\s+content="([^"]+)"', html)
            if not og_match:
                og_match = re.search(r'content="([^"]+)"\s+property="og:image"', html)
            if og_match:
                img_url = og_match.group(1)
                results[name] = img_url
                print(f"[OK] {name} ({tmdb_id}): {img_url}")
            else:
                print(f"[NO OG] {name} ({tmdb_id})")
    except Exception as e:
        print(f"[FAIL] {name} ({tmdb_id}): {e}")

with open('scraper/real_posters.json', 'w') as out:
    json.dump(results, out, indent=2)
print("Done! Saved to scraper/real_posters.json")
