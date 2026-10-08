import sqlite3, json, os

DB = r"G:\streaming app\scraper\catalog.db"
c = sqlite3.connect(DB)

def one(q):
    try:
        return c.execute(q).fetchone()[0]
    except Exception as e:
        return f"ERR {e}"

print("=== CATALOGUE ===")
print("titles                :", one("SELECT COUNT(*) FROM titles"))
print("titles by type:")
for t, n in c.execute("SELECT type, COUNT(*) FROM titles GROUP BY type ORDER BY 2 DESC"):
    print(f"   {t:<14} {n:,}")
print("tmdb_id present       :", one("SELECT COUNT(*) FROM titles WHERE tmdb_id IS NOT NULL AND tmdb_id>0"))
print("status:")
for s, n in c.execute("SELECT status, COUNT(*) FROM titles GROUP BY status ORDER BY 2 DESC LIMIT 8"):
    print(f"   {str(s):<14} {n:,}")
print("seasons rows          :", one("SELECT COUNT(*) FROM seasons"))
print("episodes rows         :", one("SELECT COUNT(*) FROM episodes"))
print("countries             :", one("SELECT COUNT(*) FROM countries"))
print("languages             :", one("SELECT COUNT(*) FROM languages"))
print("audio mappings        :", one("SELECT COUNT(*) FROM title_audio_languages"))
print("  titles 2+ dubs      :", one("SELECT COUNT(*) FROM (SELECT title_id FROM title_audio_languages GROUP BY title_id HAVING COUNT(*)>=2)"))
print("  titles exactly 1 dub:", one("SELECT COUNT(*) FROM (SELECT title_id FROM title_audio_languages GROUP BY title_id HAVING COUNT(*)=1)"))

print()
print("=== TOP COUNTRIES ===")
q = """SELECT c.code, c.name, COUNT(*) n
       FROM title_countries tc JOIN countries c ON c.id=tc.country_id
       GROUP BY c.code ORDER BY n DESC LIMIT 15"""
for code, name, n in c.execute(q):
    print(f"   {code:<4} {str(name):<22} {n:,}")

print()
print("=== STATE FILES (scraper/) ===")
HERE = r"G:\streaming app\scraper"
for f in sorted(os.listdir(HERE)):
    if f.startswith('.') and f.endswith('.json'):
        p = os.path.join(HERE, f)
        try:
            d = json.load(open(p, encoding='utf-8'))
            if isinstance(d, dict):
                summary = {k: (len(v) if isinstance(v, (list, dict)) else v) for k, v in d.items()}
            else:
                summary = f"list len={len(d)}"
            print(f"   {f:<38} {summary}")
        except Exception as e:
            print(f"   {f:<38} unreadable: {e}")
c.close()