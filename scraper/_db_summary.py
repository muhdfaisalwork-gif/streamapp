import sqlite3

def main():
    conn = sqlite3.connect('catalog.db')
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cur.fetchall()]
    print(f"Total tables: {len(tables)}")
    for t in sorted(tables):
        try:
            cnt = cur.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
            print(f"  {t:30}: {cnt}")
        except Exception as e:
            print(f"  {t:30}: ERROR {e}")

    print("\n--- Types in titles ---")
    for r in cur.execute("SELECT type, count(*) FROM titles GROUP BY type"):
        print(f"  {r[0]}: {r[1]}")

    print("\n--- Sources in sources table ---")
    for r in cur.execute("SELECT id, name, is_legal FROM sources"):
        print(f"  {r[0]}: {r[1]} (legal={r[2]})")

    print("\n--- Availability status counts ---")
    for r in cur.execute("SELECT status, count(*) FROM availability GROUP BY status"):
        print(f"  {r[0]}: {r[1]}")

    print("\n--- Top genres ---")
    for r in cur.execute("SELECT g.name, count(tg.title_id) FROM genres g LEFT JOIN title_genres tg ON g.id=tg.genre_id GROUP BY g.id ORDER BY count(tg.title_id) DESC LIMIT 15"):
        print(f"  {r[0]}: {r[1]}")

    print("\n--- Top countries ---")
    for r in cur.execute("SELECT c.name, count(tc.title_id) FROM countries c LEFT JOIN title_countries tc ON c.id=tc.country_id GROUP BY c.id ORDER BY count(tc.title_id) DESC LIMIT 15"):
        print(f"  {r[0]}: {r[1]}")

    print("\n--- Top languages ---")
    for r in cur.execute("SELECT l.name, count(tl.title_id) FROM languages l LEFT JOIN title_languages tl ON l.id=tl.language_id GROUP BY l.id ORDER BY count(tl.title_id) DESC LIMIT 15"):
        print(f"  {r[0]}: {r[1]}")

if __name__ == '__main__':
    main()
