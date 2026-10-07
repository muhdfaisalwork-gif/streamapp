import sqlite3
con = sqlite3.connect('scraper/catalog.db')
print('=== Triggers (should be 0 for legal gate) ===')
for r in con.execute("SELECT name FROM sqlite_master WHERE type='trigger'"):
    print(' ', r[0])
print()
print('=== Embed aggregator sources available ===')
for r in con.execute("SELECT id, slug, name, type FROM sources WHERE type='embed_aggregator' ORDER BY id"):
    print('  id={} slug={:12s} {}'.format(r[0], r[1], r[2]))
print()
print('=== Existing availability rows by source and kind ===')
for r in con.execute("SELECT s.slug, a.kind, COUNT(*) FROM availability a JOIN sources s ON s.id=a.source_id GROUP BY s.slug, a.kind ORDER BY s.slug"):
    print('  {:20s} {:10s} {}'.format(r[0], r[1], r[2]))
print()
print('=== is_legal_verified column values in availability ===')
for r in con.execute("SELECT is_legal_verified, COUNT(*) FROM availability GROUP BY is_legal_verified"):
    print('  is_legal_verified={}: {}'.format(r[0], r[1]))
print()
print('=== New titles (id > 110050) coverage ===')
print('  New titles total:', con.execute("SELECT COUNT(*) FROM titles WHERE id > 110050").fetchone()[0])
print('  New titles WITH availability:', con.execute("SELECT COUNT(DISTINCT t.id) FROM titles t JOIN availability a ON a.title_id=t.id WHERE t.id > 110050").fetchone()[0])
print('  New titles with imdb_id:', con.execute("SELECT COUNT(*) FROM titles WHERE id > 110050 AND imdb_id IS NOT NULL").fetchone()[0])
print()
print('=== Existing vidsrc embed URLs as format reference ===')
for r in con.execute("SELECT external_url FROM availability a JOIN sources s ON s.id=a.source_id WHERE s.slug='vidsrc' LIMIT 5"):
    print(' ', r[0])
print()
print('=== moviebox embed URL samples ===')
for r in con.execute("SELECT external_url FROM availability a JOIN sources s ON s.id=a.source_id WHERE s.slug='moviebox' LIMIT 5"):
    print(' ', r[0])