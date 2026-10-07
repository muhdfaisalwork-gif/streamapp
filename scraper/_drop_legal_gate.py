"""Drop the law-only gate and re-add pirate aggregator sources."""
import sqlite3
import os
import sys

db_path = r'G:\streaming app\scraper\catalog.db'
if not os.path.exists(db_path):
    print('DB not found:', db_path)
    sys.exit(1)

db = sqlite3.connect(db_path)
db.row_factory = sqlite3.Row
cur = db.cursor()

# 1. Drop the legal-only trigger
cur.execute("SELECT name FROM sqlite_master WHERE type='trigger' AND name='trg_availability_must_be_legal'")
print('trigger existed:', bool(cur.fetchone()))
cur.execute('DROP TRIGGER IF EXISTS trg_availability_must_be_legal')
db.commit()
print('trigger dropped.')

# 2. Re-add pirate embed-aggregator sources (the multi-source mirrors the player uses)
SOURCES = [
    ('vidsrc',      'VidSrc',           'https://vidsrc.me',          'embed_aggregator'),
    ('superembed',  'SuperEmbed',       'https://multiembed.mov',     'embed_aggregator'),
    ('multiembed',  'MultiEmbed',       'https://multiembed.mov',     'embed_aggregator'),
    ('2embed',      '2Embed',           'https://www.2embed.cc',      'embed_aggregator'),
    ('flixhq',      'FlixHQ',           'https://flixhq.com',         'embed_aggregator'),
    ('gomovies',    'GoMovies',         'https://gomovies.sx',        'embed_aggregator'),
    ('moviebox',    'MovieBox mirrors', 'https://movieboxapp.io',     'embed_aggregator'),
    ('cinezone',    'CineZone',         'https://cinezone.to',        'embed_aggregator'),
    ('embedsu',     'EmbedSu',          'https://embed.su',           'embed_aggregator'),
    ('warezcdn',    'WarezCDN mirrors', 'https://warezcdn.com',       'embed_aggregator'),
]
added = 0
for slug, name, url, stype in SOURCES:
    cur.execute("""
        INSERT INTO sources (slug, name, base_url, type, enabled, is_legal)
        VALUES (?, ?, ?, ?, 1, 0)
        ON CONFLICT(slug) DO UPDATE SET
            name=excluded.name,
            base_url=excluded.base_url,
            type=excluded.type,
            enabled=1,
            is_legal=0
    """, (slug, name, url, stype))
    added += cur.rowcount
db.commit()

cur.execute('SELECT COUNT(*) c FROM sources WHERE is_legal=0')
print('illegal sources in DB:', cur.fetchone()['c'])
cur.execute('SELECT COUNT(*) c FROM sources WHERE is_legal=1')
print('legal sources still in DB:', cur.fetchone()['c'])

print('\nAll illegal sources now registered:')
cur.execute("""
SELECT slug, name, base_url, type, enabled
FROM sources WHERE is_legal=0 ORDER BY slug
""")
for r in cur.fetchall():
    print(f'  {r["slug"]:14s} {r["name"]:25s} enabled={r["enabled"]} {r["base_url"]}')

db.close()
print('\nDone.')
