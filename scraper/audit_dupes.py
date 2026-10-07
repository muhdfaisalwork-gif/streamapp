import sqlite3

c = sqlite3.connect(r"G:\streaming app\scraper\catalog.db")
for name in ["Your Name", "Erased", "Word of Honor", "My Love from the Star"]:
    print(f"\n=== {name} ===")
    q = """SELECT t.id, t.slug, t.title, t.year, t.type,
                (SELECT COUNT(*) FROM seasons s WHERE s.title_id=t.id) nseasons,
                (SELECT COUNT(*) FROM availability a WHERE a.title_id=t.id) navail
         FROM titles t WHERE t.title = ? OR t.original_title = ? ORDER BY t.id"""
    rows = c.execute(q, (name, name)).fetchall()
    for r in rows:
        print(f"   id={r[0]:<8} slug={r[1]:<34} {str(r[3]):<6} {r[4]:<11} seasons={r[5]:<4} avail={r[6]}")
    if not rows:
        print("   (none found by exact title)")
        q2 = """SELECT id, slug, title, year, type FROM titles WHERE title LIKE ? ORDER BY id LIMIT 12"""
        for r in c.execute(q2, (f"%{name.split()[0]}%",)):
            print(f"   ~ id={r[0]:<8} slug={r[1]:<34} {str(r[3]):<6} {r[4]:<11} {r[2]}")
c.close()