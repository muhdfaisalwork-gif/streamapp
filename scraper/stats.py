import sqlite3
c = sqlite3.connect(r"G:\streaming app\scraper\catalog.db")
print("titles:", c.execute("SELECT COUNT(*) FROM titles").fetchone()[0])
print("audio rows:", c.execute("SELECT COUNT(*) FROM title_audio_languages").fetchone()[0])
print("titles with 2+ dubs:", c.execute("SELECT COUNT(*) FROM (SELECT title_id FROM title_audio_languages GROUP BY title_id HAVING COUNT(*) >= 2)").fetchone()[0])
print("titles with 1 dub:", c.execute("SELECT COUNT(*) FROM (SELECT title_id FROM title_audio_languages GROUP BY title_id HAVING COUNT(*) = 1)").fetchone()[0])