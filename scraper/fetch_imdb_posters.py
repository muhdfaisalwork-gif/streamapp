import urllib.request
import urllib.parse
import json
import sqlite3
import time
import sys

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

def get_imdb_meta(query):
    encoded = urllib.parse.quote(query)
    url = f"https://v3.sg.media-imdb.com/suggestion/x/{encoded}.json"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=5) as res:
            data = json.loads(res.read())
            results = data.get('d', [])
            for r in results:
                # Prefer entry that has an image and is a movie or TV series
                qid = r.get('qid', '')
                if 'i' in r and 'imageUrl' in r['i']:
                    imdb_id = r.get('id', '')
                    if imdb_id.startswith('tt'):
                        return {
                            'imdbId': imdb_id,
                            'title': r.get('l'),
                            'year': r.get('y'),
                            'poster': r['i']['imageUrl'],
                            'type': 'tv' if 'tv' in qid.lower() or 'TV' in r.get('q', '') else 'movie'
                        }
            # Fallback to first with image
            for r in results:
                if 'i' in r and 'imageUrl' in r['i'] and r.get('id', '').startswith('tt'):
                    return {
                        'imdbId': r.get('id'),
                        'title': r.get('l'),
                        'year': r.get('y'),
                        'poster': r['i']['imageUrl'],
                        'type': 'tv' if 'tv' in r.get('qid', '').lower() else 'movie'
                    }
    except Exception as e:
        pass
    return None

conn = sqlite3.connect('scraper/cache.db')
c = conn.cursor()

rows = c.execute("SELECT id, title, type, imdb_id, tmdb_id, poster FROM titles").fetchall()

targets = []
for r in rows:
    item_id, title, mtype, imdb_id, tmdb_id, poster = r
    p = poster or ''
    is_bad = (
        not p or
        not p.startswith('http') or
        '7WTsnHkbA0FaG6R9twfFde0I9hl.jpg' in p or
        any(k in p for k in ['_pk.', '_tr.', '_eg.', '_ng.', 'ishq_murshid', 'kabli_pulao', 'suno_chanda', 'yaqeen', 'shehr', 'diyar', 'ranjha', 'sar_e_rah', 'kuch_ankahi', 'jaan_e', 'teefa', 'laal_kabootar', 'bin_roye', 'welad', 'hashashin'])
    )
    if is_bad:
        targets.append((item_id, title, mtype, imdb_id, tmdb_id, poster))

print(f"Total titles needing authentic poster: {len(targets)}")

updated_count = 0
for item_id, title, mtype, imdb_id, tmdb_id, old_poster in targets:
    clean_title = title.split('(')[0].split('-')[0].strip()
    meta = get_imdb_meta(clean_title)
    if meta and meta.get('poster'):
        new_poster = meta['poster']
        new_imdb = meta['imdbId'] if meta.get('imdbId') and meta['imdbId'].startswith('tt') else imdb_id
        c.execute("UPDATE titles SET poster = ?, backdrop = ?, imdb_id = CASE WHEN imdb_id IS NULL OR imdb_id = '' THEN ? ELSE imdb_id END WHERE id = ?",
                  (new_poster, new_poster, new_imdb, item_id))
        updated_count += 1
        safe_title = title.encode('ascii', 'replace').decode('ascii')
        print(f"[UPDATED] {safe_title} -> {new_poster[:65]}")
    else:
        # Fallback to verified Dune 2 or high-res default
        safe_title = title.encode('ascii', 'replace').decode('ascii')
        print(f"[NO META] {safe_title}")
    
    if updated_count % 20 == 0:
        conn.commit()
    time.sleep(0.05)

conn.commit()
conn.close()

print(f"\nFINISHED! Successfully updated {updated_count} / {len(targets)} titles with authentic posters!")
