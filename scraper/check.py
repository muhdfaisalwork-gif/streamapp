import sqlite3
import requests
import json

conn = sqlite3.connect('scraper/cache.db')
c = conn.cursor()
c.execute('SELECT COUNT(*) FROM items')
print('Total items in cache.db:', c.fetchone()[0])
c.execute("SELECT COUNT(*) FROM items WHERE title LIKE '%Volume %'")
print('Volume titles in cache.db:', c.fetchone()[0])
c.execute("SELECT COUNT(*) FROM items WHERE poster LIKE '%poster_%'")
print('Fake posters in cache.db:', c.fetchone()[0])

c.execute("SELECT id, title, poster, imdb_id, tmdb_id FROM items WHERE title LIKE '%Jawan%'")
print('Jawan rows:', c.fetchall())

c.execute("SELECT id, title, poster, imdb_id, tmdb_id FROM items WHERE title LIKE '%Doctor Who%'")
print('Doctor Who rows:', c.fetchall())

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
    print('7800 Action titles sample:', [x.get('title') for x in data[:10]])
    print('7800 Action posters sample:', [x.get('poster') for x in data[:5]])
except Exception as e:
    print('7800 action error:', e)

try:
    r = requests.get('http://localhost:3000/api/v1/categories', timeout=3)
    data = r.json()
    action = data.get('categories', {}).get('Action', [])
    print('3000 categories Action sample count:', len(action))
    print('3000 categories Action sample titles:', [x.get('title') for x in action[:5]])
    print('3000 categories Action sample posters:', [x.get('poster') for x in action[:5]])
except Exception as e:
    print('3000 categories error:', e)
