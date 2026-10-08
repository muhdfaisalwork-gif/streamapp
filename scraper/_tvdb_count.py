import sys, sqlite3
sys.path.insert(0, '.')
con = sqlite3.connect('catalog.db')
print('TV titles without seasons:', con.execute("SELECT COUNT(*) FROM titles WHERE type='tv' AND id NOT IN (SELECT DISTINCT title_id FROM seasons)").fetchone()[0])
print('TV titles total:', con.execute("SELECT COUNT(*) FROM titles WHERE type='tv'").fetchone()[0])
print('TV titles WITH seasons:', con.execute("SELECT COUNT(DISTINCT title_id) FROM seasons").fetchone()[0])
print('New TV titles (since 110050) without seasons:', con.execute("SELECT COUNT(*) FROM titles WHERE type='tv' AND id > 110050 AND id NOT IN (SELECT DISTINCT title_id FROM seasons)").fetchone()[0])