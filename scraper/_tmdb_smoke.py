"""Fast parallel TMDB backfill — proper concurrency tuning."""
import sys
import time
import sqlite3
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, str(Path(__file__).parent))
from tmdb_client import TmdbClient, TmdbError

DB_PATH = Path(__file__).parent / "catalog.db"

def has_bad_poster(url):
    if not url: return True
    p = url.lower()
    if any(x in p for x in ('placeholder', '/poster_', '/backdrop_')):
        return True
    if 'image.tmdb.org' in p and '/t/p/' in p:
        stem = p.rsplit('/', 1)[-1].rsplit('.', 1)[0]
        if not all(c in '0123456789abcdef' for c in stem):
            return True
    return False

def main(limit, workers=80):
    client = TmdbClient()
    client.configure()

    db = sqlite3.connect(str(DB_PATH), timeout=10)
    db.row_factory = sqlite3.Row
    rows = list(db.execute("""
        SELECT id, tmdb_id, type, poster, backdrop, rating, imdb_id, runtime
        FROM titles
        WHERE tmdb_id IS NOT NULL AND tmdb_id > 0
        ORDER BY popularity DESC NULLS LAST
        LIMIT ?
    """, (limit,)))
    print(f"Processing {len(rows)} rows with {workers} workers…")

    def proc(r):
        tid = r["tmdb_id"]
        kind = r["type"] if r["type"] in ("movie","tv") else "movie"
        try:
            md = client.movie(tid) if kind != "tv" else client.tv(tid)
            imgs = client.movie_images(tid) if kind != "tv" else client.tv_images(tid)
        except TmdbError as e:
            return ("failed", r["id"], str(e)[:50])
        if not md:
            return ("failed", r["id"], "no md")
        upd = {}
        if has_bad_poster(r["poster"]) and imgs and imgs.get("posters"):
            p = imgs["posters"][0].get("file_path")
            if p: upd["poster"] = client.poster_url(p)
        if has_bad_poster(r["backdrop"]) and imgs and imgs.get("backdrops"):
            b = imgs["backdrops"][0].get("file_path")
            if b: upd["backdrop"] = client.backdrop_url(b)
        if (not r["runtime"]) and md.get("runtime"):
            upd["runtime"] = md["runtime"]
        if (not r["rating"]) and md.get("vote_average"):
            upd["rating"] = float(md["vote_average"])
        if (not r["imdb_id"]) and md.get("imdb_id"):
            upd["imdb_id"] = md["imdb_id"]
        if upd:
            return ("ok", r["id"], upd)
        return ("noop", r["id"], "")

    t0 = time.time()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        out = [f.result() for f in [pool.submit(proc, r) for r in rows]]
    elapsed = time.time() - t0

    from collections import Counter
    c = Counter(o[0] for o in out)
    real = sum(1 for o in out if o[0] == "ok")
    print(f"time={elapsed:.1f}s, {len(rows)} rows, results={dict(c)}, real-updates={real}, rate={len(rows)/elapsed:.1f} rows/s")

    # Apply DB updates
    db_apply = sqlite3.connect(str(DB_PATH))
    applied = 0
    for kind, id_, upd in out:
        if kind == "ok" and upd:
            sets = ", ".join(f"{col}=?" for col in upd.keys())
            params = list(upd.values()) + [id_]
            db_apply.execute(f"UPDATE titles SET {sets} WHERE id=?", params)
            applied += 1
    db_apply.commit()
    db_apply.close()
    db.close()
    print(f"applied {applied} updates to DB")

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--limit", type=int, default=200)
    p.add_argument("--workers", type=int, default=80)
    a = p.parse_args()
    main(a.limit, a.workers)
