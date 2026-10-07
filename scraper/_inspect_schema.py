import sqlite3

con = sqlite3.connect('scraper/catalog.db')
cur = con.cursor()
print('TITLES schema:')
for r in cur.execute("PRAGMA table_info(titles)"):
    print(' ', r[1], r[2], 'nullable=' + str(r[3]), 'default=' + str(r[4]))
print()
print('AVAILABILITY schema:')
for r in cur.execute("PRAGMA table_info(availability)"):
    print(' ', r[1], r[2], 'nullable=' + str(r[3]), 'default=' + str(r[4]))
print()
print('SOURCES schema:')
for r in cur.execute("PRAGMA table_info(sources)"):
    print(' ', r[1], r[2], 'nullable=' + str(r[3]), 'default=' + str(r[4]))
print()
print('TITLE_GENRES schema:')
for r in cur.execute("PRAGMA table_info(title_genres)"):
    print(' ', r[1], r[2], 'nullable=' + str(r[3]), 'default=' + str(r[4]))
print()
print('TITLE_COUNTRIES schema:')
for r in cur.execute("PRAGMA table_info(title_countries)"):
    print(' ', r[1], r[2], 'nullable=' + str(r[3]), 'default=' + str(r[4]))
print()
print('GENRES:')
for r in cur.execute("SELECT id, slug, name FROM genres ORDER BY id"):
    print(' ', r)
print()
print('TITLE STATUS VALUES:')
for r in cur.execute("SELECT status, COUNT(*) FROM titles GROUP BY status ORDER BY 2 DESC"):
    print(' ', r)
print()
print('TITLE METADATA_STATE VALUES:')
for r in cur.execute("SELECT metadata_state, COUNT(*) FROM titles GROUP BY metadata_state ORDER BY 2 DESC"):
    print(' ', r)
print()
print('IS_ANIME:')
for r in cur.execute("SELECT is_anime, COUNT(*) FROM titles GROUP BY is_anime ORDER BY 2 DESC"):
    print(' ', r)
print()
print('SAMPLE 3 NEWEST TITLES:')
for r in cur.execute("SELECT id, title, type, year, status, metadata_state FROM titles ORDER BY id DESC LIMIT 5"):
    print(' ', r)
print()
print('TITLE INDEXES:')
for r in cur.execute("SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name='titles'"):
    print(' ', r[0])
print()
print('TMDB SOURCE ROW:')
for r in cur.execute("SELECT * FROM sources WHERE slug='tmdb'"):
    print(' ', r)
print()
print('MOVIEBOX SOURCE ROW:')
for r in cur.execute("SELECT * FROM sources WHERE slug='moviebox'"):
    print(' ', r)