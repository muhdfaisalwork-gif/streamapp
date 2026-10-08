import sqlite3, json, urllib.request, random
from concurrent.futures import ThreadPoolExecutor

random.seed(7)
conn = sqlite3.connect('scraper/catalog.db')
c = conn.cursor()
rows = []
for t, n in (('movie', 60), ('tv', 60), ('anime', 40)):
    c.execute("SELECT slug, type FROM titles WHERE rating >= 6 AND tmdb_id IS NOT NULL AND type=? ORDER BY RANDOM() LIMIT ?", (t, n))
    rows += c.fetchall()

BASE = 'https://streamapp-catalog.muhd-faisal-work.workers.dev'

def check(r):
    slug, typ = r
    try:
        q = '?season=1&episode=1' if typ != 'movie' else ''
        with urllib.request.urlopen(urllib.request.Request(f'{BASE}/title/{slug}/availability{q}', headers={'User-Agent': 'Mozilla/5.0'}), timeout=30) as resp:
            d = json.loads(resp.read())
            n = len([a for a in d.get('availability', []) if a.get('url')])
            return (slug, typ, n, None)
    except Exception as e:
        return (slug, typ, 0, str(e))

with ThreadPoolExecutor(8) as ex:
    res = list(ex.map(check, rows))

bad = [r for r in res if r[2] == 0]
print(f"checked {len(res)}, no playable source: {len(bad)}")
for r in bad[:30]:
    print(r)
