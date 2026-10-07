import sqlite3

conn = sqlite3.connect("scraper/catalog.db")
tables = [t[0] for t in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print("Tables:", tables)

for t in ["collection_titles", "title_collections", "collections"]:
    if t in tables:
        print(f"\nSchema of {t}:", [c[1] for c in conn.execute(f"PRAGMA table_info({t})").fetchall()])
        print(f"Count of {t}:", conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0])
