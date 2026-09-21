import sqlite3, glob

print('DB files:', glob.glob('**/*.db', recursive=True))
for db in glob.glob('**/*.db', recursive=True):
    try:
        conn = sqlite3.connect(db)
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = c.fetchall()
        print(db, 'tables:', tables)
        for t in tables:
            tname = t[0]
            c.execute(f"SELECT COUNT(*) FROM [{tname}]")
            count = c.fetchone()[0]
            print(f"  {tname}: {count} rows")
            c.execute(f"PRAGMA table_info([{tname}])")
            cols = [col[1] for col in c.fetchall()]
            print(f"  columns: {cols}")
    except Exception as e:
        print(db, 'error:', e)
