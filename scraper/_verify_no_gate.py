"""Verify trigger is gone and we can attach availability to vidsrc."""
import sqlite3, os
db = sqlite3.connect(r'G:\streaming app\scraper\catalog.db')
db.row_factory = sqlite3.Row
cur = db.cursor()
cur.execute("SELECT id FROM sources WHERE slug='vidsrc'")
vidsrc = cur.fetchone()
cur.execute("SELECT id FROM titles WHERE slug='the-matrix-1999'")
title = cur.fetchone()
print('vidsrc.id =', vidsrc['id'] if vidsrc else None, '  title.id =', title['id'] if title else None)
if not (vidsrc and title):
    print('missing rows'); raise SystemExit(1)
try:
    cur.execute("""
        INSERT INTO availability
        (title_id, source_id, kind, status, external_url, requires_auth, is_legal_verified, last_checked_at)
        VALUES (?, ?, 'embed', 'available', 'https://vidsrc.me/embed/movie/603', 0, 1, strftime('%s','now'))
    """, (title['id'], vidsrc['id']))
    db.commit()
    print('insert OK — trigger is gone.')
    cur.execute("DELETE FROM availability WHERE title_id=? AND source_id=? AND external_url=?", (title['id'], vidsrc['id'], 'https://vidsrc.me/embed/movie/603'))
    db.commit()
    print('cleaned up test row.')
except sqlite3.IntegrityError as e:
    print('trigger still firing:', e)
db.close()
