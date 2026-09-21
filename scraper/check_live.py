import sqlite3
import requests
import sys
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('scraper/cache.db')
c = conn.cursor()
c.execute('SELECT COUNT(*) FROM titles')
print('Total titles in cache.db:', c.fetchone()[0])
c.execute("SELECT COUNT(*) FROM titles WHERE title LIKE '%Volume %'")
print('Volume titles in cache.db:', c.fetchone()[0])
c.execute("SELECT COUNT(*) FROM titles WHERE poster LIKE '%poster_%'")
print('Fake posters in cache.db:', c.fetchone()[0])

c.execute("SELECT id, title, poster, imdb_id, tmdb_id FROM titles WHERE title LIKE '%Jawan%'")
print('Jawan rows:', c.fetchall())

c.execute("SELECT id, title, poster, imdb_id, tmdb_id FROM titles WHERE title LIKE '%Doctor Who%'")
print('Doctor Who rows:', c.fetchall())

# Let's inspect Action titles in cache.db
c.execute("SELECT id, title, poster, imdb_id, tmdb_id FROM titles WHERE genres LIKE '%Action%' LIMIT 10")
print('Action rows sample in cache.db:', c.fetchall())

try:
    r = requests.get('http://127.0.0.1:7800/stats', timeout=3)
    print('7800 stats:', r.json())
except Exception as e:
    print('7800 error:', e)

try:
    r = requests.get('http://localhost:3000/api/v1/meta/stats', timeout=3)
    print('3000 stats:', r.json())
except Exception as e:
    print('3000 error:', e)

try:
    r = requests.get('http://127.0.0.1:7800/catalog?genre=Action&limit=10', timeout=3)
    data = r.json()
    print('7800 Action titles count returned:', len(data))
    for x in data[:5]:
        print('  7800 item:', x.get('title'), '| poster:', x.get('poster'), '| tmdb:', x.get('tmdb_id'), '| imdb:', x.get('imdb_id'))
except Exception as e:
    print('7800 action error:', e)

try:
    r = requests.get('http://localhost:3000/api/v1/categories', timeout=3)
    data = r.json()
    action = data.get('categories', {}).get('Action', [])
    print('3000 categories Action count:', len(action))
    for x in action[:5]:
        print('  3000 Action item:', x.get('title'), '| poster:', x.get('poster'), '| tmdb:', x.get('tmdbId'), '| imdb:', x.get('imdbId'), '| sources:', len(x.get('sources', [])))
except Exception as e:
    print('3000 categories error:', e)
