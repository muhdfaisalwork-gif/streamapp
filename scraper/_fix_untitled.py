import sqlite3

db = sqlite3.connect('catalog.db')
cur = db.cursor()

# Fix Lord of the Rings — copy original_title into title
cur.execute("""
UPDATE titles
SET title = original_title
WHERE id = 13293 AND (title = 'Untitled' OR title IS NULL OR title = '')
""")
print(f'Fixed LOTR: rowcount={cur.rowcount}')

# Remove stub with no real title
cur.execute("""
DELETE FROM titles
WHERE id = 12538 AND (title = 'Untitled' OR title IS NULL OR title = '')
  AND (original_title = 'Untitled' OR original_title IS NULL OR original_title = '')
""")
print(f'Removed stub: rowcount={cur.rowcount}')

db.commit()
db.close()
print('Done.')
