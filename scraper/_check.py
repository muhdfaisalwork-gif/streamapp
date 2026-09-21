import sqlite3
conn = sqlite3.connect('cache.db')
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
print('TABLES:', c.fetchall())
for table_row in c.fetchall():
    table = table_row[0]
    try:
        c.execute(f'SELECT COUNT(*) FROM "{table}"')
        cnt = c.fetchone()[0]
        if cnt == 0:
            continue
        print(f'\n=== {table} ({cnt} rows) ===')
        c.execute(f'PRAGMA table_info("{table}")')
        cols = c.fetchall()
        print('cols:', [c[1] for c in cols])
        # Sample one row
        c.execute(f'SELECT * FROM "{table}" LIMIT 1')
        sample = c.fetchone()
        if sample:
            for col, val in zip([c[1] for c in cols], sample):
                vs = str(val)[:80]
                print(f'  {col}: {vs}')
    except Exception as e:
        print(f'  err {table}: {e}')

# Look for source breakdown in the main table
try:
    for tname in ['media', 'catalog', 'titles', 'items', 'movies', 'shows']:
        try:
            c.execute(f'SELECT source, COUNT(*) FROM "{tname}" GROUP BY source ORDER BY 2 DESC')
            rows = c.fetchall()
            if rows:
                print(f'\n=== {tname} by source ===')
                for r in rows: print(r)
        except: pass
except: pass
