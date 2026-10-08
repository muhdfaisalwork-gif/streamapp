import sqlite3, sys
db = sqlite3.connect(r'G:\streaming app\scraper\catalog.db')
db.row_factory = sqlite3.Row
cur = db.cursor()
print('--- sources & their availability rows ---')
cur.execute('''
SELECT s.slug, s.name, s.is_legal, s.enabled,
       COUNT(a.id) AS n
FROM sources s
LEFT JOIN availability a ON a.source_id = s.id
GROUP BY s.id
ORDER BY n DESC, s.slug
''')
for r in cur.fetchall():
    print(f'  {r["slug"]:14s}  is_legal={r["is_legal"]} enabled={r["enabled"]} rows={r["n"]}')

print()
cur.execute('SELECT COUNT(*) c FROM availability')
print(f'TOTAL availability rows: {cur.fetchone()["c"]}')

print()
print('--- availability by kind + is_legal ---')
cur.execute('''
SELECT a.kind, s.is_legal, COUNT(*) c
FROM availability a JOIN sources s ON s.id=a.source_id
GROUP BY a.kind, s.is_legal
ORDER BY c DESC
''')
for r in cur.fetchall():
    print(f'  kind={r["kind"]}  is_legal={r["is_legal"]}  count={r["c"]}')

print()
print('--- availability distinct titles ---')
cur.execute('SELECT COUNT(DISTINCT title_id) c FROM availability')
print('distinct titles with availability: ', cur.fetchone()['c'])
