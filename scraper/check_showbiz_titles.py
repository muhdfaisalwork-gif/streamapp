import sqlite3

conn = sqlite3.connect("scraper/catalog.db")
cursor = conn.cursor()

topics_to_check = [
    ("Spider-Man", "SELECT id, title, year, poster, backdrop, type FROM titles WHERE title LIKE '%Spider-Man%' LIMIT 3"),
    ("Resident Evil", "SELECT id, title, year, poster, backdrop, type FROM titles WHERE title LIKE '%Resident Evil%' LIMIT 3"),
    ("Reacher", "SELECT id, title, year, poster, backdrop, type FROM titles WHERE title LIKE '%Reacher%' LIMIT 3"),
    ("Breaking Bad", "SELECT id, title, year, poster, backdrop, type FROM titles WHERE title LIKE '%Breaking Bad%' LIMIT 3"),
    ("Squid Game", "SELECT id, title, year, poster, backdrop, type FROM titles WHERE title LIKE '%Squid Game%' LIMIT 3"),
    ("Attack on Titan", "SELECT id, title, year, poster, backdrop, type FROM titles WHERE title LIKE '%Attack on Titan%' LIMIT 3"),
    ("Bleach", "SELECT id, title, year, poster, backdrop, type FROM titles WHERE title LIKE '%Bleach%' LIMIT 3"),
    ("Doraemon", "SELECT id, title, year, poster, backdrop, type FROM titles WHERE title LIKE '%Doraemon%' LIMIT 3"),
    ("The Dark Knight", "SELECT id, title, year, poster, backdrop, type FROM titles WHERE title LIKE '%Dark Knight%' LIMIT 3"),
    ("Inception", "SELECT id, title, year, poster, backdrop, type FROM titles WHERE title LIKE '%Inception%' LIMIT 3"),
    ("Upcoming 2025/2026", "SELECT id, title, year, poster, backdrop, type FROM titles WHERE year >= 2025 ORDER BY popularity DESC LIMIT 5")
]

for name, q in topics_to_check:
    res = cursor.execute(q).fetchall()
    print(f"=== {name} ===")
    for r in res:
        print(f"  ID: {r[0]} | Title: {r[1]} ({r[2]}) | Type: {r[5]} | Poster: {bool(r[3])}")

conn.close()
