import sqlite3

def test_catalog():
    conn = sqlite3.connect('catalog.db')
    cur = conn.cursor()
    fk_errors = cur.execute("PRAGMA foreign_key_check").fetchall()
    print(f"FK errors count: {len(fk_errors)}")
    if fk_errors:
        print("FK errors:", fk_errors[:10])

    print("\nCounts:")
    for t in ['titles', 'genres', 'countries', 'languages', 'collections', 'seasons', 'episodes', 'availability', 'title_collections']:
        cnt = cur.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
        print(f"  {t}: {cnt}")

    print("\nVerified Playable Streams:")
    for r in cur.execute("SELECT t.title, a.kind, a.playback_url FROM availability a JOIN titles t ON a.title_id = t.id WHERE a.playback_url IS NOT NULL LIMIT 5"):
        print(f"  {r[0]} -> {r[1]} -> {r[2]}")

if __name__ == '__main__':
    test_catalog()
