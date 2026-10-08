import sqlite3

conn = sqlite3.connect('scraper/catalog.db')
c = conn.cursor()

print("Total titles:", c.execute("SELECT COUNT(*) FROM titles").fetchone()[0])
print("Titles by type:", c.execute("SELECT type, COUNT(*) FROM titles GROUP BY type").fetchall())
print("Titles by year range:")
print("  >= 2025:", c.execute("SELECT COUNT(*) FROM titles WHERE year >= 2025").fetchone()[0])
print("  2020-2024:", c.execute("SELECT COUNT(*) FROM titles WHERE year BETWEEN 2020 AND 2024").fetchone()[0])
print("  2010-2019:", c.execute("SELECT COUNT(*) FROM titles WHERE year BETWEEN 2010 AND 2019").fetchone()[0])
print("  2000-2009:", c.execute("SELECT COUNT(*) FROM titles WHERE year BETWEEN 2000 AND 2009").fetchone()[0])
print("  1990-1999:", c.execute("SELECT COUNT(*) FROM titles WHERE year BETWEEN 1990 AND 1999").fetchone()[0])
print("  1986-1989:", c.execute("SELECT COUNT(*) FROM titles WHERE year BETWEEN 1986 AND 1989").fetchone()[0])
print("  < 1986:", c.execute("SELECT COUNT(*) FROM titles WHERE year < 1986").fetchone()[0])

print("Upcoming titles:", c.execute("SELECT COUNT(*) FROM titles WHERE status = 'upcoming' OR year >= 2026").fetchone()[0])
print("Upcoming titles with availability:", c.execute("""
    SELECT COUNT(DISTINCT t.id) 
    FROM titles t 
    JOIN availability a ON t.id = a.title_id 
    WHERE (t.status = 'upcoming' OR t.year >= 2026) AND a.status = 'available'
""").fetchone()[0])

print("Ongoing TV series:", c.execute("SELECT COUNT(*) FROM titles WHERE type='tv' AND status IN ('returning', 'ongoing', 'in_production')").fetchone()[0])
