"""Check how many titles are MDBlist-enrichable (have imdb_id, missing rating)."""
import sqlite3
con = sqlite3.connect('catalog.db')
print('Titles with imdb_id but NULL rating:', con.execute("SELECT COUNT(*) FROM titles WHERE imdb_id IS NOT NULL AND rating IS NULL").fetchone()[0])
print('Titles with imdb_id AND rating:', con.execute("SELECT COUNT(*) FROM titles WHERE imdb_id IS NOT NULL AND rating IS NOT NULL").fetchone()[0])
print('Total with imdb_id:', con.execute("SELECT COUNT(*) FROM titles WHERE imdb_id IS NOT NULL").fetchone()[0])