import sqlite3
con = sqlite3.connect('scraper/catalog.db')
print('=== Final state ===')
print('Titles total:', con.execute('SELECT COUNT(*) FROM titles').fetchone()[0])
print('New titles with imdb_id now:', con.execute('SELECT COUNT(*) FROM titles WHERE id > 110050 AND imdb_id IS NOT NULL').fetchone()[0])
print()
print('Availability rows by source (kind=playback):')
for r in con.execute("SELECT s.slug, COUNT(*) FROM availability a JOIN sources s ON s.id=a.source_id WHERE a.kind='playback' GROUP BY s.slug ORDER BY 2 DESC"):
    print('  {:20s} {:,}'.format(r[0], r[1]))
print()
print('New titles (id > 110050) with embed availability:', con.execute("SELECT COUNT(DISTINCT t.id) FROM titles t JOIN availability a ON a.title_id=t.id JOIN sources s ON s.id=a.source_id WHERE t.id > 110050 AND s.type='embed_aggregator'").fetchone()[0])
print('New titles total:', con.execute('SELECT COUNT(*) FROM titles WHERE id > 110050').fetchone()[0])