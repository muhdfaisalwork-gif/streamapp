"""
_tmdb_rescue.py — Safer backfill that searches by title + year first.

Why this exists:
  The seed data assigned sequential `tmdb_id` values to titles, but those IDs
  sometimes point at DIFFERENT movies than the title claims. Doing a direct
  /movie/{id} fetch silently overwrites posters with WRONG-MOVIE artwork.

  This rescue script ignores the stored tmdb_id and instead searches TMDB by
  the row's title + year. When the best match has a high confidence score it
  replaces the wrong poster/backdrop/runtime/overview with the real TMDB
  metadata for THIS movie.

Idempotent:
  - Skips rows that already have a real poster URL.
  - Skips rows where the best TMDB match is below the confidence threshold.

Speed: target 8-15 rows/sec with 50 concurrent workers → ~13k rows in 25min.
"""
import os
import sys
import sqlite3
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, str(Path(__file__).parent))
from tmdb_client import TmdbClient, TmdbError

DB_PATH = Path(__file__).parent / "catalog.db"

PLACEHOLDER_PATTERNS = ("placeholder", "/poster_", "/backdrop_")


def has_bad_poster(url):
    if not url:
        return True
    low = url.lower()
    if any(p in low for p in PLACEHOLDER_PATTERNS):
        return True
    if "image.tmdb.org" in low and "/t/p/" in low:
        stem = low.rsplit("/", 1)[-1].rsplit(".", 1)[0]
        if not all(c in "0123456789abcdef" for c in stem) and len(stem) >= 24:
            return True
    return False


def similarity(a, b):
    a = (a or "").lower().strip()
    b = (b or "").lower().strip()
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    if a.startswith(b) or b.startswith(a):
        return 0.85
    ta = set(a.split())
    tb = set(b.split())
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def main(limit=None, workers=40, min_confidence=0.45):
    client = TmdbClient()
    client.configure()

    db = sqlite3.connect(str(DB_PATH), timeout=10)
    db.row_factory = sqlite3.Row
    if limit:
        rows = list(db.execute("""
            SELECT id, slug, title, original_title, type, year, poster, backdrop, rating, runtime
            FROM titles
            WHERE (poster IS NULL OR poster = '' OR poster LIKE '%placeholder%' OR poster LIKE '%/poster_%')
            ORDER BY popularity DESC NULLS LAST
            LIMIT ?
        """, (limit,)))
    else:
        rows = list(db.execute("""
            SELECT id, slug, title, original_title, type, year, poster, backdrop, rating, runtime
            FROM titles
            WHERE (poster IS NULL OR poster = '' OR poster LIKE '%placeholder%' OR poster LIKE '%/poster_%')
            ORDER BY popularity DESC NULLS LAST
        """))
    print(f"Rescuing up to {len(rows)} rows with {workers} workers…")

    def proc(r):
        title = r["title"]
        kind = r["type"] if r["type"] in ("movie", "tv") else "movie"
        year = r["year"]
        try:
            results = (client.search_tv(title, year=year) if kind == "tv"
                       else client.search_movie(title, year=year))
        except TmdbError as e:
            return ("error", r["id"], str(e)[:50])
        if not results:
            return ("notfound", r["id"], "")
        best = None
        best_score = -1.0
        for c in results[:6]:
            cname = c.get("title") or c.get("name") or ""
            yr = (c.get("release_date") or c.get("first_air_date") or "0000")[:4]
            try:
                yr_int = int(yr)
            except ValueError:
                yr_int = 0
            score = similarity(title, cname)
            if year and yr_int:
                if abs(year - yr_int) <= 1:
                    score += 0.20
                elif abs(year - yr_int) <= 3:
                    score += 0.05
                else:
                    score -= 0.10 * max(0, abs(year - yr_int) - 3)
            score += min(0.10, (c.get("popularity") or 0) / 1000.0)
            if score > best_score:
                best, best_score = c, score
        if not best or best_score < min_confidence:
            return ("lowconf", r["id"], f"{best_score:.2f}")
        tid = best["id"]
        try:
            md = client.movie(tid) if kind != "tv" else client.tv(tid)
            imgs = client.movie_images(tid) if kind != "tv" else client.tv_images(tid)
        except TmdbError:
            return ("error", r["id"], "fetch md failed")
        if not md:
            return ("error", r["id"], "no md")
        upd = {"tmdb_id": tid}
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
        if md.get("imdb_id"):
            upd["imdb_id"] = md["imdb_id"]
        if upd:
            return ("ok", r["id"], upd)
        return ("noop", r["id"], "")

    t0 = time.time()
    applied = 0
    skipped = 0
    failed = 0
    notfound = 0
    lowconf = 0
    # Process in chunks so partial progress is saved
    CHUNK = 200
    for i in range(0, len(rows), CHUNK):
        chunk = rows[i:i + CHUNK]
        with ThreadPoolExecutor(max_workers=workers) as pool:
            out = [f.result() for f in [pool.submit(proc, r) for r in chunk]]
        # Apply DB updates immediately
        for kind, id_, payload in out:
            if kind == "ok" and isinstance(payload, dict):
                sets = ", ".join(f"{col}=?" for col in payload.keys())
                params = list(payload.values()) + [id_]
                db.execute(f"UPDATE titles SET {sets} WHERE id=?", params)
                applied += 1
            elif kind == "noop":
                skipped += 1
            elif kind in ("notfound", "lowconf"):
                if kind == "notfound": notfound += 1
                else: lowconf += 1
            else:
                failed += 1
        db.commit()
        elapsed = time.time() - t0
        rate = (i + len(chunk)) / max(0.1, elapsed)
        print(f"  [{i+len(chunk)}/{len(rows)}] applied={applied} lowconf={lowconf} notfound={notfound} failed={failed} rate={rate:.1f}/s", flush=True)
    db.close()
    print(f"Done. applied={applied} lowconf={lowconf} notfound={notfound} failed={failed} skipped={skipped}")

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--workers", type=int, default=40)
    p.add_argument("--min-confidence", type=float, default=0.45)
    a = p.parse_args()
    main(a.limit or None, a.workers, a.min_confidence)
