import sqlite3

con = sqlite3.connect('scraper/catalog.db')
cur = con.cursor()
print('TITLES TOTAL:', cur.execute('SELECT COUNT(*) FROM titles').fetchone()[0])
print()
print('TITLES BY TYPE:')
for r in cur.execute('SELECT type, COUNT(*) FROM titles GROUP BY type ORDER BY 2 DESC'):
    print(' ', r[0], r[1])
print()
print('SOURCES:')
for r in cur.execute('SELECT slug, name, type FROM sources'):
    print(' ', r[0], '|', r[1], '|', r[2])
print()
print('AVAILABILITY BY STATUS:')
for r in cur.execute('SELECT status, COUNT(*) FROM availability GROUP BY status ORDER BY 2 DESC'):
    print(' ', r[0], r[1])
print()
print('YEARS RANGE:')
y = cur.execute('SELECT MIN(year), MAX(year) FROM titles WHERE year IS NOT NULL').fetchone()
print(' ', y)
print()
print('AVAILABILITY BY SOURCE:')
for r in cur.execute('SELECT s.slug, COUNT(*) FROM availability a JOIN sources s ON s.id=a.source_id GROUP BY s.slug ORDER BY 2 DESC'):
    print(' ', r[0], r[1])
print()
print('TRIGGERS:')
for r in cur.execute("SELECT name FROM sqlite_master WHERE type='trigger'"):
    print(' ', r[0])
print()
print('LEGAL GATE TRIGGER CHECK:')
for r in cur.execute("SELECT sql FROM sqlite_master WHERE type='trigger' AND name LIKE '%legal%'"):
    print(r[0][:400])
print()
print('LAST 5 YEARS COUNTS:')
for r in cur.execute("SELECT year, COUNT(*) FROM titles WHERE year BETWEEN 2021 AND 2026 GROUP BY year ORDER BY year DESC"):
    print(' ', r[0], r[1])