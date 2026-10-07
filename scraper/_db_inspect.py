import sqlite3

def main():
    conn = sqlite3.connect('catalog.db')
    cur = conn.cursor()
    print("--- Availability detail ---")
    for r in cur.execute("SELECT source_id, kind, status, count(*) FROM availability GROUP BY source_id, kind, status"):
        print(f"  source_id={r[0]}, kind={r[1]}, status={r[2]}: {r[3]}")

    print("\n--- Availability sample ---")
    cur.execute("PRAGMA table_info(availability)")
    cols = [c[1] for c in cur.fetchall()]
    print("Cols:", cols)
    for r in cur.execute("SELECT * FROM availability LIMIT 5"):
        print(dict(zip(cols, r)))

    print("\n--- Titles sample (with posters, year, etc.) ---")
    cur.execute("PRAGMA table_info(titles)")
    tcols = [c[1] for c in cur.fetchall()]
    for r in cur.execute("SELECT * FROM titles WHERE type='tv' LIMIT 3"):
        print("TV:", dict(zip(tcols, r)))
    for r in cur.execute("SELECT * FROM titles WHERE type='anime' LIMIT 3"):
        print("Anime:", dict(zip(tcols, r)))

if __name__ == '__main__':
    main()
