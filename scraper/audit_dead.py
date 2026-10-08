import sqlite3

c = sqlite3.connect(r"G:\streaming app\scraper\catalog.db")

print("=== DEAD SHADOW ROWS: seasons=0 AND no availability ===")
q = """
SELECT COUNT(*) FROM titles t
WHERE (SELECT COUNT(*) FROM seasons s WHERE s.title_id=t.id) = 0
  AND (SELECT COUNT(*) FROM availability a WHERE a.title_id=t.id) = 0
"""
print("total dead rows:", c.execute(q).fetchone()[0])

print("\nby type:")
q2 = """
SELECT t.type, COUNT(*) FROM titles t
WHERE (SELECT COUNT(*) FROM seasons s WHERE s.title_id=t.id) = 0
  AND (SELECT COUNT(*) FROM availability a WHERE a.title_id=t.id) = 0
GROUP BY t.type ORDER BY 2 DESC
"""
for t, n in c.execute(q2):
    print(f"   {t:<14} {n:,}")

print("\ntop dead rows that share a title with a LIVE row (real shadow duplicates):")
q3 = """
SELECT d.id, d.slug, d.title, d.year, d.type, k.id, k.slug, k.type,
       (SELECT COUNT(*) FROM availability a WHERE a.title_id=k.id) k_avail
FROM titles d
JOIN titles k ON k.title = d.title AND k.id <> d.id
WHERE (SELECT COUNT(*) FROM seasons s WHERE s.title_id=d.id) = 0
  AND (SELECT COUNT(*) FROM availability a WHERE a.title_id=d.id) = 0
  AND (SELECT COUNT(*) FROM availability a WHERE a.title_id=k.id) > 0
ORDER BY d.id LIMIT 40
"""
rows = c.execute(q3).fetchall()
print("   shadow-against-live pairs:", len(rows))
for r in rows:
    print(f"   dead id={r[0]:<8} {r[1]:<34} {str(r[3]):<6} {r[4]:<8}  <-  live id={r[5]:<8} {r[6]:<34} avail={r[8]}")

print("\n=== 'Your Name' variants (any suffix) ===")
for r in c.execute("""SELECT id, slug, title, year, type FROM titles
                      WHERE title LIKE '%your name%' OR original_title LIKE '%your name%'
                      ORDER BY id LIMIT 20"""):
    print(f"   id={r[0]:<8} slug={r[1]:<36} {str(r[3]):<6} {r[4]:<8} {r[2]}")
c.close()