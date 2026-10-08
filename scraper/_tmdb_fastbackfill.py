"""
_tmdb_fastbackfill.py — Fast parallel TMDB backfill.

Strategy:
  1. Rows that already have tmdb_id set: fetch /movie/{id}/images directly (no search)
     — fast because we skip the search/resolve step.
  2. Row count: typically ~13k titles.
  3. Up to 25 concurrent requests (TMDB allows ~50 req/sec on v3 keys).

Run: TMDB_API_KEY=... python _tmdb_fastbackfill.py
"""
import os
import sys
import sqlite3
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from tmdb_client import TmdbClient, TmdbError

DB_PATH = Path(__file__).parent / "catalog.db"


def looks_fake(url):
    if not url:
        return True
    low = url.lower()
    if "placeholder" in low or "/poster_" in low or "/backdrop_" in low:
        return True
    if "image.tmdb.org" in low and "/t/p/" in low:
        fname = low.rsplit("/", 1)[-1]
        stem = fname.rsplit(".", 1)[0]
        if not stem or not all(c in "0123456789abcdef" for c in stem):
            return False  # i1.wp.com wrapper is fine if it actually wraps a real path
    return False


def fast_backfill_tmdb_ids(client: TmdbClient):
    """Process rows that already have tmdb_id but no real poster.
    One row per request, parallel with ThreadPoolExecutor."""
    db = sqlite3.connect(str(DB_PATH), timeout=30)
    db.row_factory = sqlite3.Row
    cur = db.execute("""
        SELECT id, tmdb_id, type, poster, backdrop, rating, imdb_id, runtime, status, release_date
        FROM titles
        WHERE tmdb_id IS NOT NULL AND tmdb_id > 0
    """)
    rows = cur.fetchall()
    print(f"Processing {len(rows)} rows with existing tmdb_id…")

    enriched = skipped = failed = 0

    def process_one(r):
        # Check what fields need updating
        updates = {}
        tid = r["tmdb_id"]
        kind = r["type"] if r["type"] in ("movie", "tv") else "movie"
        try:
            md  = client.movie(tid) if kind != "tv" else client.tv(tid)
            imgs = client.movie_images(tid) if kind != "tv" else client.tv_images(tid)
        except TmdbError:
            return ("failed", r["id"])
        if not md:
            return ("failed", r["id"])
        if (looks_fake(r["poster"]) or not r["poster"]) and imgs and imgs.get("posters"):
            p = imgs["posters"][0].get("file_path")
            if p:
                updates["poster"] = client.poster_url(p)
        if (looks_fake(r["backdrop"]) or not r["backdrop"]) and imgs and imgs.get("backdrops"):
            b = imgs["backdrops"][0].get("file_path")
            if b:
                updates["backdrop"] = client.backdrop_url(b)
        # Only update NULL fields (don't overwrite real data)
        if (not r["runtime"]) and md.get("runtime"):
            updates["runtime"] = md.get("runtime") or (md.get("episode_run_time") or [None])[0]
        if (not r["status"]) and md.get("status"):
            updates["status"] = md.get("status")
        if (not r["release_date"]) and (md.get("release_date") or md.get("first_air_date")):
            updates["release_date"] = md.get("release_date") or md.get("first_air_date")
        if (not r["rating"]) and md.get("vote_average"):
            updates["rating"] = float(md["vote_average"])
        if (not r["imdb_id"]) and md.get("imdb_id"):
            updates["imdb_id"] = md["imdb_id"]
        if updates:
            return ("enriched", r["id"], updates)
        return ("skipped", r["id"])

    # Run in parallel batches
    batch = []
    results = []
    BATCH = 50
    for r in rows:
        batch.append(r)
        if len(batch) >= BATCH:
            with ThreadPoolExecutor(max_workers=20) as pool:
                futures = [pool.submit(process_one, row) for row in batch]
                for f in as_completed(futures):
                    results.append(f.result())
            batch = []
    if batch:
        with ThreadPoolExecutor(max_workers=20) as pool:
            futures = [pool.submit(process_one, row) for row in batch]
            for f in as_completed(futures):
                results.append(f.result())

    # Apply DB updates
    for r in results:
        kind = r[0]
        if kind == "enriched":
            _, id_, updates = r
            sets = []
            params = []
            for col, val in updates.items():
                sets.append(f"{col}=?")
                params.append(val)
            params.append(id_)
            db.execute(f"UPDATE titles SET {', '.join(sets)} WHERE id=?", params)
            enriched += 1
        elif kind == "skipped":
            skipped += 1
        else:
            failed += 1

    db.commit()
    db.close()
    print(f"Done. enriched={enriched} skipped={skipped} failed={failed}")
    return enriched, skipped, failed


if __name__ == "__main__":
    try:
        client = TmdbClient()
    except TmdbError as e:
        print(f"FATAL: {e}", file=sys.stderr)
        sys.exit(2)
    if not client._configured:
        client.configure()
    t0 = time.time()
    fast_backfill_tmdb_ids(client)
    print(f"Total time: {time.time() - t0:.1f}s")
