
import sqlite3

db = sqlite3.connect('G:/streaming app/scraper/catalog.db')
cursor = db.cursor()

cursor.execute('SELECT COUNT(*) FROM titles WHERE type IN (''tv'', ''anime'')')
titles_count = cursor.fetchone()[0]

cursor.execute('SELECT COUNT(*) FROM seasons')
seasons_count = cursor.fetchone()[0]

cursor.execute('SELECT COUNT(*) FROM episodes')
episodes_count = cursor.fetchone()[0]

print(f'TV Titles: {titles_count}')
print(f'Seasons: {seasons_count}')
print(f'Episodes: {episodes_count}')

