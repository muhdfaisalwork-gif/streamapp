"""
ingest_tmdb_to_100k.py — Pull new titles from TMDB to push catalog past 100K.

What this does:
  - Reads G:\\streaming app\\scraper\\catalog.db (live catalog)
  - Fetches from 11 TMDB endpoints, all pages
  - DEDUPES against existing tmdb_ids in titles table
  - INSERTs only NEW titles + matching availability rows
  - Touches ZERO existing rows

Run:
  cd "G:\\streaming app\\scraper"
  python ingest_tmdb_to_100k.py

Stop with Ctrl-C any time — already-inserted rows stay.

Requirements: httpx (already used in scraper).
"""
from __future__ import annotations
import asyncio
import os
import re
import sqlite3
import sys
import time
from pathlib import Path

import httpx
from dotenv import dotenv_values

HERE = Path(__file__).parent
DB = HERE / "catalog.db"

# TMDB API config (from scraper/.env)
ENV = dotenv_values(str(HERE / ".env"))
API_KEY = ENV.get("TMDB_API_KEY") or ""
ACCESS_TOKEN = ENV.get("TMDB_ACCESS_TOKEN") or ""
BASE = "https://api.themoviedb.org/3"

# TMDB has a hard cap of 500 pages per paginated list endpoint.
MAX_PAGES = 500
PAGE_SIZE = 20  # TMDB default

# Endpoints to ingest (path, params-extras, kind='movie'|'tv')
# Each endpoint contributes a *different* slice, so the union gives breadth.
ENDPOINTS = [
    # Movies — popular / top_rated give recent + all-time classics
    ("movie/popular",          {"sort_by": None},                "movie"),
    ("movie/top_rated",        {"sort_by": None},                "movie"),
    ("movie/now_playing",      {"sort_by": None},                "movie"),
    ("movie/upcoming",         {"sort_by": None},                "movie"),
    # TV — popular / top_rated / airing_today / on_the_air
    ("tv/popular",             {"sort_by": None},                "tv"),
    ("tv/top_rated",           {"sort_by": None},                "tv"),
    ("tv/airing_today",        {"sort_by": None},                "tv"),
    ("tv/on_the_air",          {"sort_by": None},                "tv"),
    # Discover — sort by revenue (blockbusters across all years)
    ("discover/movie",         {"sort_by": "revenue.desc", "primary_release_date.gte": "1970-01-01"}, "movie"),
    # Discover — sort by primary release date desc (newest)
    ("discover/movie",         {"sort_by": "primary_release_date.desc"},                          "movie"),
    # Discover TV — most popular all-time
    ("discover/tv",            {"sort_by": "popularity.desc", "first_air_date.gte": "1970-01-01"}, "tv"),
]


def slugify(s: str) -> str:
    s = (s or "").lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")[:120] or "untitled"


def main() -> None:
    if not API_KEY:
        print("FATAL: TMDB_API_KEY missing from scraper/.env")
        sys.exit(1)

    conn = sqlite3.connect(str(DB), timeout=60)
    conn.execute("PRAGMA journal_mode = WAL")
    cur = conn.cursor()

    # Resolve TMDB source_id (created earlier; type=metadata_only)
    cur.execute("SELECT id, slug FROM sources WHERE slug = 'tmdb'")
    row = cur.fetchone()
    if not row:
        print("FATAL: no 'tmdb' source in sources table — aborting")
        sys.exit(2)
    TMDB_SID = row[0]
    print(f"using sources.id={TMDB_SID} (slug=tmdb)")

    # Snapshot of existing tmdb_ids + slugs
    print("loading existing tmdb_ids + slugs into memory...")
    seen_tmdb: set[int] = set()
    seen_slug: set[str] = set()
    for r in cur.execute("SELECT tmdb_id FROM titles WHERE tmdb_id IS NOT NULL AND tmdb_id > 0"):
        try:
            seen_tmdb.add(int(r[0]))
        except (TypeError, ValueError):
            continue
    for r in cur.execute("SELECT slug FROM titles"):
        if r[0]:
            seen_slug.add(str(r[0]))
    print(f"  {len(seen_tmdb):,} tmdb_ids + {len(seen_slug):,} slugs in catalog")

    base_count = cur.execute("SELECT COUNT(*) FROM titles").fetchone()[0]
    base_avail = cur.execute("SELECT COUNT(*) FROM availability").fetchone()[0]
    print(f"starting titles={base_count:,}, availability rows={base_avail:,}")
    print(f"target: >= 100,000 titles (need +{100000 - base_count:,})")
    print()

    # Fast rate-limit + retry
    sem = asyncio.Semaphore(20)  # TMDB allows ~50 rps; stay well below
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"} if ACCESS_TOKEN else {}

    total_new_titles = 0
    total_new_avail = 0
    total_skipped = 0
    total_api_calls = 0
    started = time.time()

    async def fetch_page(client: httpx.AsyncClient, path: str, params: dict, page: int):
        nonlocal total_api_calls
        params = {**params, "api_key": API_KEY, "page": page}
        async with sem:
            for attempt in range(4):
                try:
                    r = await client.get(
                        f"{BASE}/{path}", params=params, headers=headers, timeout=15.0
                    )
                    total_api_calls += 1
                    if r.status_code == 429:
                        await asyncio.sleep(1.5 * (attempt + 1))
                        continue
                    r.raise_for_status()
                    return r.json()
                except (httpx.HTTPError, httpx.TimeoutException) as e:
                    if attempt == 3:
                        print(f"  ! giving up on page {page}: {e}")
                        return None
                    await asyncio.sleep(0.5 * (attempt + 1))
        return None

    async def ingest_endpoint(client, path, base_params, kind, label):
        nonlocal total_new_titles, total_new_avail, total_skipped

        ep_new_titles = 0
        ep_new_avail = 0
        ep_skipped = 0
        page = 1
        total_pages_seen = 0
        empty_pages = 0

        while page <= MAX_PAGES:
            data = await fetch_page(client, path, base_params, page)
            if not data or "results" not in data:
                break
            results = data["results"]
            if not results:
                break

            total_pages_seen += 1
            # Total pages cap from TMDB
            declared_total_pages = min(int(data.get("total_pages", MAX_PAGES)), MAX_PAGES)

            batch_inserts = []
            batch_avail = []
            for r in results:
                try:
                    tmdb_id = int(r.get("id") or 0)
                except (TypeError, ValueError):
                    ep_skipped += 1
                    continue
                if not tmdb_id or tmdb_id in seen_tmdb:
                    ep_skipped += 1
                    continue

                if kind == "movie":
                    title = r.get("title") or r.get("original_title") or ""
                    rd = r.get("release_date") or ""
                    year = int(rd[:4]) if rd[:4].isdigit() else None
                    original_title = r.get("original_title") or title
                else:
                    title = r.get("name") or r.get("original_name") or ""
                    rd = r.get("first_air_date") or ""
                    year = int(rd[:4]) if rd[:4].isdigit() else None
                    original_title = r.get("original_name") or title

                if not title:
                    ep_skipped += 1
                    continue

                # Slug: title-year-tmdbid to keep uniqueness even on collision
                base_slug = slugify(title)
                slug = f"{base_slug}-{year}" if year else base_slug
                if slug in seen_slug:
                    slug = f"{slug}-{tmdb_id}"
                seen_slug.add(slug)
                seen_tmdb.add(tmdb_id)

                overview = r.get("overview") or ""
                poster = r.get("poster_path") or ""
                if poster and not poster.startswith("http"):
                    poster = f"https://image.tmdb.org/t/p/w500{poster}"
                backdrop = r.get("backdrop_path") or ""
                if backdrop and not backdrop.startswith("http"):
                    backdrop = f"https://image.tmdb.org/t/p/w780{backdrop}"
                popularity = float(r.get("popularity") or 0)
                rating = float(r.get("vote_average") or 0)
                rating_count = int(r.get("vote_count") or 0)
                genre_ids = ",".join(str(g) for g in (r.get("genre_ids") or []))
                original_language = r.get("original_language") or ""

                batch_inserts.append((
                    slug, title, original_title, kind, year,
                    overview, poster, backdrop,
                    tmdb_id, popularity, rating, rating_count,
                    genre_ids, original_language,
                ))

            if batch_inserts:
                cur.executemany(
                    "INSERT OR IGNORE INTO titles "
                    "(slug, title, original_title, type, year, "
                    " overview, poster, backdrop, "
                    " tmdb_id, popularity, rating, rating_count, "
                    " status) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'released')",
                    [(b[0], b[1], b[2], b[3], b[4],
                      b[5], b[6], b[7],
                      b[8], b[9], b[10], b[11]) for b in batch_inserts],
                )

                # Fetch the ids we just inserted to make availability rows
                tmdb_ids_in_batch = [b[8] for b in batch_inserts]
                qmarks = ",".join("?" for _ in tmdb_ids_in_batch)
                cur.execute(
                    f"SELECT id, tmdb_id FROM titles WHERE tmdb_id IN ({qmarks})",
                    tmdb_ids_in_batch,
                )
                id_map = {int(t): int(i) for i, t in cur.fetchall()}
                for b in batch_inserts:
                    tid = id_map.get(int(b[8]))
                    if tid:
                        batch_avail.append((tid, TMDB_SID, "available", None, "metadata"))

            if batch_avail:
                cur.executemany(
                    "INSERT OR IGNORE INTO availability "
                    "(title_id, source_id, status, last_checked_at, external_url) "
                    "VALUES (?, ?, ?, ?, ?)",
                    batch_avail,
                )

            ep_new_titles += len(batch_inserts)
            ep_new_avail += len(batch_avail)
            total_new_titles += len(batch_inserts)
            total_new_avail += len(batch_avail)
            total_skipped += ep_skipped

            conn.commit()

            if page % 25 == 0 or page == 1:
                elapsed = time.time() - started
                titles_now = base_count + total_new_titles
                pct = 100 * titles_now / 100000
                print(
                    f"  [{label}] page {page}/{declared_total_pages}  "
                    f"+{len(batch_inserts)} titles this page  "
                    f"running total titles={titles_now:,} ({pct:.1f}% of 100k)  "
                    f"skipped={ep_skipped}  api_calls={total_api_calls}  "
                    f"elapsed={elapsed:.0f}s"
                )

            # If TMDB declared fewer pages than MAX_PAGES, we can stop early.
            if page >= declared_total_pages:
                break

            page += 1

        print(
            f"  [{label}] DONE  pages={total_pages_seen}  "
            f"new_titles={ep_new_titles}  new_avail={ep_new_avail}  "
            f"skipped={ep_skipped}"
        )
        return ep_new_titles

    async def run():
        async with httpx.AsyncClient(http2=False, timeout=20.0) as client:
            for path, extra, kind in ENDPOINTS:
                base_params = {
                    "language": "en-US",
                    "include_adult": "false",
                    "include_video": "false",
                }
                base_params.update({k: v for k, v in extra.items() if v is not None})
                label = f"{path}?{ '&'.join(f'{k}={v}' for k,v in base_params.items() if k not in ('language','api_key')) }"
                # Hit TMDB first to learn declared total_pages before iterating.
                # Skip the discovery by querying page 1 directly.
                print(f"\n=== {label} ===")
                added = await ingest_endpoint(client, path, base_params, kind, label)
                if added == 0:
                    # No new titles — try the next endpoint.
                    continue
                # Stop early if we've already cleared 100k
                if base_count + total_new_titles >= 100000:
                    print("\n[target reached] >= 100,000 titles, stopping early.")
                    break

    asyncio.run(run())

    # Final report
    elapsed = time.time() - started
    final_titles = cur.execute("SELECT COUNT(*) FROM titles").fetchone()[0]
    final_avail = cur.execute("SELECT COUNT(*) FROM availability").fetchone()[0]
    print()
    print("=" * 60)
    print(f"FINAL: titles {base_count:,} -> {final_titles:,}  (+{final_titles - base_count:,})")
    print(f"FINAL: availability rows {base_avail:,} -> {final_avail:,}  (+{final_avail - base_avail:,})")
    print(f"FINAL: skipped {total_skipped:,} (already had tmdb_id)")
    print(f"FINAL: api calls {total_api_calls:,}, elapsed {elapsed:.0f}s")
    if final_titles >= 100000:
        print("[OK] catalog past 100K")
    else:
        print(f"[INFO] still need {100000 - final_titles:,} more — re-run with broader endpoints")
    print("=" * 60)

    conn.close()


if __name__ == "__main__":
    main()
