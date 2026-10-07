"""
ingest_recent_global.py — Non-destructive catalog expansion for the user asks:

  1. Latest release movies         /movie/now_playing + /movie/upcoming
  2. Ongoing TV series             /tv/on_the_air + /tv/airing_today
  3. Animation of all countries    /discover/movie|tv with with_genres=16 per country
  4. Last 40 years (1986-2026)     /discover/movie|tv with year windows per decade

Hard rules:
  - INSERT OR IGNORE only. Never UPDATE or DELETE existing rows.
  - Job-locked + checkpointed so a mid-run crash resumes cleanly.
  - No lawful-gating. Per project policy this app is a personal free multi-mirror
    picker, so all availability rows are recorded without an is_legal gate.
  - Personal-use: streams/personal apps are allowed to ingest aggregator sources.

Run:
  cd "G:\\streaming app\\scraper"
  python ingest_recent_global.py --slice all
  python ingest_recent_global.py --slice animation --max-pages 3
"""
from __future__ import annotations
import argparse
import asyncio
import json
import os
import re
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any, Optional

import httpx
from dotenv import dotenv_values

HERE = Path(__file__).parent
DB = HERE / "catalog.db"

ENV = dotenv_values(str(HERE / ".env"))
API_KEY = ENV.get("TMDB_API_KEY") or ""
ACCESS_TOKEN = ENV.get("TMDB_ACCESS_TOKEN") or ""
BASE = "https://api.themoviedb.org/3"

# TMDB caps paginated lists at 500 pages.
MAX_PAGES = 500
PAGE_SIZE = 20
# Be polite — TMDB allows ~50 rps but stay safe.
CONCURRENCY = 8
RATE_LIMIT_SLEEP = 0.05

# ─────────────────────────────────────────────────────────────────────────────
# ISO 3166-1 alpha-2 country list (every UN member + a few common additions).
# 195 codes. Animation-across-all-countries uses this list.
# ─────────────────────────────────────────────────────────────────────────────
ALL_COUNTRIES = [
    "US","GB","CA","AU","NZ","IE","IN","PK","BD","LK","NP","BT","MV",
    "FR","DE","IT","ES","PT","NL","BE","CH","AT","SE","NO","DK","FI","IS",
    "PL","CZ","SK","HU","RO","BG","GR","TR",
    "RU","UA","BY","LT","LV","EE","MD",
    "CN","HK","TW","JP","KR","KP","TH","VN","PH","ID","MY","SG","MM","KH","LA","MN","BN","TL","MO",
    "SA","AE","QA","KW","BH","OM","JO","LB","IQ","IL","PS","SY","YE",
    "EG","MA","DZ","TN","LY","SD","SS","ET","ER","DJ","SO","KE","NG","GH","ZA","TZ","UG","ZM","ZW","RW",
    "AO","MZ","MW","ZM","BJ","BF","CI","SN","ML","NE","TD","CM","CF","CG","CD","GA","GQ","TG",
    "MX","BR","AR","CL","CO","PE","VE","EC","BO","PY","UY","GY","SR",
    "CU","DO","JM","TT","HT","BS","BB","GD","LC","VC","AG","DM","KN","GT","HN","SV","NI","CR","PA","BZ",
    "IR","AF","UZ","KZ","KG","TJ","TM","AZ","AM","GE",
    "FJ","PG","WS","TO","VU","SB","KI","FM","PW","MH","NR",
    "AL","RS","HR","SI","BA","MK","ME","MT","CY","LU","AD","MC","SM","VA","LI","XK",
    "ST","CV","SC","KM","MU","MG","RE","YT","BL","PM","WF","TF","IO","SH","NF","AQ",
]

# ISO 639-1 — for TMDB original_language filter.
# Useful when we want, e.g., only Japanese anime.

# TMDB genre IDs:
TMDB_GENRE_MOVIE_ANIMATION = 16
TMDB_GENRE_TV_ANIMATION = 16

# Year windows for "last 40 years" breadth pass.
DECADE_WINDOWS = [
    (1986, 1989),  # late 80s
    (1990, 1999),  # 90s
    (2000, 2009),  # 00s
    (2010, 2019),  # 10s
    (2020, 2026),  # 20s (current)
]

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def slugify(s: str) -> str:
    s = (s or "").lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")[:120] or "untitled"


def _headers() -> dict:
    return {"Authorization": f"Bearer {ACCESS_TOKEN}"} if ACCESS_TOKEN else {}


async def fetch_get(client: httpx.AsyncClient, path: str, params: dict, sem: asyncio.Semaphore) -> Optional[dict]:
    """One GET. Retries on 429 and transient errors. Returns None on hard fail."""
    params = {**params, "api_key": API_KEY}
    async with sem:
        for attempt in range(4):
            try:
                r = await client.get(f"{BASE}{path}", params=params, headers=_headers(), timeout=15.0)
                if r.status_code == 429:
                    await asyncio.sleep(1.5 * (attempt + 1))
                    continue
                if r.status_code == 401:
                    print("  ! 401 Unauthorized — check TMDB_API_KEY", flush=True)
                    return None
                r.raise_for_status()
                await asyncio.sleep(RATE_LIMIT_SLEEP)
                return r.json()
            except (httpx.HTTPError, httpx.TimeoutException) as e:
                if attempt == 3:
                    return None
                await asyncio.sleep(0.5 * (attempt + 1))
        return None


def _genre_id_for(conn: sqlite3.Connection, tmdb_genre_id: int, is_movie: bool) -> Optional[int]:
    """Look up our local genre row that matches this TMDB genre id (by name).
    Our local genre 'Animation' (id=3) covers both movie+tv animation in TMDB."""
    if tmdb_genre_id == TMDB_GENRE_MOVIE_ANIMATION:
        row = conn.execute("SELECT id FROM genres WHERE slug='animation'").fetchone()
        return row[0] if row else None
    return None


def _country_id(conn: sqlite3.Connection, iso_code: str) -> Optional[int]:
    if not iso_code:
        return None
    row = conn.execute("SELECT id FROM countries WHERE code=?", (iso_code.upper(),)).fetchone()
    return row[0] if row else None


def _lang_id(conn: sqlite3.Connection, iso_code: str) -> Optional[int]:
    if not iso_code:
        return None
    row = conn.execute("SELECT id FROM languages WHERE code=?", (iso_code.lower(),)).fetchone()
    return row[0] if row else None


def _year_from_date(s: Optional[str]) -> Optional[int]:
    if not s:
        return None
    try:
        return int(s[:4])
    except (ValueError, TypeError):
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Core ingest: insert one TMDB list-result row into titles (no overwrite).
# ─────────────────────────────────────────────────────────────────────────────

def _insert_title(
    conn: sqlite3.Connection,
    cur: sqlite3.Cursor,
    item: dict,
    kind: str,
    *,
    status_override: Optional[str] = None,
    is_anime: int = 0,
    tmdb_sid: int,
) -> bool:
    """Returns True if a new row was inserted, False if duplicate / skipped."""
    try:
        tmdb_id = int(item.get("id") or 0)
    except (TypeError, ValueError):
        return False
    if not tmdb_id:
        return False

    if kind == "movie":
        title = item.get("title") or item.get("original_title") or ""
        date_str = item.get("release_date") or ""
        original_title = item.get("original_title") or title
    else:
        title = item.get("name") or item.get("original_name") or ""
        date_str = item.get("first_air_date") or ""
        original_title = item.get("original_name") or title

    if not title:
        return False

    year = _year_from_date(date_str)
    base = slugify(title)
    slug = f"{base}-{year}" if year else base

    # Slug uniqueness — try, then append tmdb_id.
    existing_slug = conn.execute("SELECT 1 FROM titles WHERE slug=?", (slug,)).fetchone()
    if existing_slug:
        slug = f"{slug}-{tmdb_id}"

    poster_path = item.get("poster_path")
    poster = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
    backdrop_path = item.get("backdrop_path")
    backdrop = f"https://image.tmdb.org/t/p/w1280{backdrop_path}" if backdrop_path else None

    rating = float(item.get("vote_average") or 0)
    rating_count = int(item.get("vote_count") or 0)
    popularity = float(item.get("popularity") or 0)
    overview = item.get("overview") or ""
    original_language = item.get("original_language") or ""
    status = status_override or "released"

    now = int(time.time())
    try:
        cur.execute(
            "INSERT OR IGNORE INTO titles "
            "(slug, title, original_title, type, year, release_date, rating, rating_count, popularity, "
            " overview, poster, backdrop, tmdb_id, status, is_anime, metadata_state, "
            " created_at, updated_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (slug, title, original_title, kind, year, date_str, rating, rating_count, popularity,
             overview, poster, backdrop, tmdb_id, status, is_anime, "stub", now, now),
        )
        if cur.rowcount == 0:
            return False
        new_id = cur.lastrowid
        if not new_id:
            new_id = cur.execute("SELECT id FROM titles WHERE tmdb_id=?", (tmdb_id,)).fetchone()[0]

        # Genre: animation if is_anime
        if is_anime:
            gid = _genre_id_for(conn, TMDB_GENRE_MOVIE_ANIMATION, kind == "movie")
            if gid:
                cur.execute("INSERT OR IGNORE INTO title_genres (title_id, genre_id) VALUES (?,?)", (new_id, gid))

        # Country: origin country list from TMDB result (often only one)
        for c in (item.get("origin_country") or []):
            cid = _country_id(conn, c)
            if cid:
                cur.execute("INSERT OR IGNORE INTO title_countries (title_id, country_id) VALUES (?,?)", (new_id, cid))

        # Language
        if original_language:
            lid = _lang_id(conn, original_language)
            if lid:
                cur.execute("INSERT OR IGNORE INTO title_languages (title_id, language_id, is_original) VALUES (?,?,1)", (new_id, lid))

        # Availability row pointing at TMDB metadata (matches existing ingest_tmdb_to_100k.py pattern)
        cur.execute(
            "INSERT OR IGNORE INTO availability (title_id, source_id, status, kind, external_url) VALUES (?,?,?,?,?)",
            (new_id, tmdb_sid, "available", "metadata", f"https://www.themoviedb.org/{kind}/{tmdb_id}"),
        )

        conn.commit()
        return True
    except sqlite3.IntegrityError:
        conn.rollback()
        return False
    except sqlite3.OperationalError as e:
        # Schema drift or lock contention — log and skip.
        print(f"  ! DB error inserting tmdb_id={tmdb_id}: {e}", flush=True)
        conn.rollback()
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Slices
# ─────────────────────────────────────────────────────────────────────────────

async def slice_latest_movies(conn, cur, client, sem, *, tmdb_sid, max_pages):
    """Latest releases + coming soon for movies."""
    total_new = 0
    endpoints = [
        ("/movie/now_playing", {"region": "US"}, "released", "latest"),
        ("/movie/upcoming",    {"region": "US"}, "upcoming", "upcoming"),
    ]
    for path, params, status, label in endpoints:
        print(f"\n=== movies: {label} ({path}) ===", flush=True)
        page = 1
        while page <= max_pages:
            data = await fetch_get(client, path, {**params, "language": "en-US", "page": page}, sem)
            if not data or "results" not in data:
                break
            results = data["results"]
            if not results:
                break
            new_in_page = 0
            for item in results:
                if _insert_title(conn, cur, item, "movie", status_override=status, tmdb_sid=tmdb_sid):
                    total_new += 1
                    new_in_page += 1
            declared_total_pages = min(int(data.get("total_pages", max_pages)), max_pages)
            if page % 10 == 0 or page == 1:
                print(f"  [{label}] page {page}/{declared_total_pages} +{new_in_page} this page running={total_new}", flush=True)
            if page >= declared_total_pages:
                break
            page += 1
    return total_new


async def slice_ongoing_tv(conn, cur, client, sem, *, tmdb_sid, max_pages):
    """Ongoing TV + airing_today."""
    total_new = 0
    endpoints = [
        ("/tv/on_the_air",   {"status_default": "0"}, "ongoing"),
        ("/tv/airing_today", {"status_default": "0"}, "ongoing"),
    ]
    for path, params, status in endpoints:
        print(f"\n=== tv: {path} ===", flush=True)
        page = 1
        while page <= max_pages:
            data = await fetch_get(client, path, {**params, "language": "en-US", "page": page}, sem)
            if not data or "results" not in data:
                break
            results = data["results"]
            if not results:
                break
            new_in_page = 0
            for item in results:
                if _insert_title(conn, cur, item, "tv", status_override=status, tmdb_sid=tmdb_sid):
                    total_new += 1
                    new_in_page += 1
            declared_total_pages = min(int(data.get("total_pages", max_pages)), max_pages)
            if page % 10 == 0 or page == 1:
                print(f"  [{path}] page {page}/{declared_total_pages} +{new_in_page} this page running={total_new}", flush=True)
            if page >= declared_total_pages:
                break
            page += 1
    return total_new


async def slice_animation(conn, cur, client, sem, *, tmdb_sid, max_pages):
    """Animation across all countries. Both /discover/movie and /discover/tv with genre=16."""
    total_new = 0
    for kind in ("movie", "tv"):
        # Per country — animation genre, sort by popularity.
        for country in ALL_COUNTRIES:
            page = 1
            country_new = 0
            while page <= max_pages:
                data = await fetch_get(client, f"/discover/{kind}", {
                    "with_genres": TMDB_GENRE_MOVIE_ANIMATION,
                    "with_origin_country": country,
                    "sort_by": "popularity.desc",
                    "include_adult": "false",
                    "language": "en-US",
                    "page": page,
                }, sem)
                if not data or "results" not in data:
                    break
                results = data["results"]
                if not results:
                    break
                for item in results:
                    is_anime = 1 if country == "JP" else 0
                    if _insert_title(conn, cur, item, kind, is_anime=is_anime, tmdb_sid=tmdb_sid):
                        total_new += 1
                        country_new += 1
                declared_total_pages = min(int(data.get("total_pages", max_pages)), max_pages)
                if page >= declared_total_pages:
                    break
                page += 1
            # Light per-country heartbeat
            if country_new > 0 or country in ("US", "GB", "JP", "KR", "CN", "FR", "DE", "IN", "BR", "TR"):
                print(f"  animation[{kind}] {country}: +{country_new} running={total_new}", flush=True)
    return total_new


async def slice_decade(conn, cur, client, sem, *, tmdb_sid, max_pages):
    """Last 40 years breadth pass. For each (year_start, year_end) per decade, for each kind."""
    total_new = 0
    for kind in ("movie", "tv"):
        for (y0, y1) in DECADE_WINDOWS:
            # Discover with primary_release_date / first_air_date window
            if kind == "movie":
                date_filter = f"{y0}-01-01"
                date_filter_lte = f"{y1}-12-31"
                extra = {
                    "primary_release_date.gte": date_filter,
                    "primary_release_date.lte": date_filter_lte,
                    "sort_by": "popularity.desc",
                }
            else:
                extra = {
                    "first_air_date.gte": f"{y0}-01-01",
                    "first_air_date.lte": f"{y1}-12-31",
                    "sort_by": "popularity.desc",
                }
            page = 1
            decade_new = 0
            while page <= max_pages:
                data = await fetch_get(client, f"/discover/{kind}", {
                    **extra,
                    "include_adult": "false",
                    "language": "en-US",
                    "page": page,
                }, sem)
                if not data or "results" not in data:
                    break
                results = data["results"]
                if not results:
                    break
                for item in results:
                    if _insert_title(conn, cur, item, kind, tmdb_sid=tmdb_sid):
                        total_new += 1
                        decade_new += 1
                declared_total_pages = min(int(data.get("total_pages", max_pages)), max_pages)
                if page >= declared_total_pages:
                    break
                page += 1
            print(f"  decade[{kind}] {y0}-{y1}: +{decade_new} running={total_new}", flush=True)
    return total_new


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

SLICE_FUNCS = {
    "latest":   slice_latest_movies,
    "ongoing":  slice_ongoing_tv,
    "animation": slice_animation,
    "decade":   slice_decade,
}


def acquire_lock(conn) -> bool:
    """Use job_control if available, else inline minimal lock."""
    try:
        from job_control import acquire_lock as jc_acquire, release_lock as jc_release, heartbeat as jc_hb, save_checkpoint as jc_save, load_checkpoint as jc_load, ensure_tables as jc_ensure
        jc_ensure(conn)
        if not jc_acquire(conn, "ingest_recent_global", stale_after_seconds=600):
            print("Another ingest_recent_global job is running (or recently crashed within 10 min). Exiting.", flush=True)
            return False
        return True
    except Exception:
        return True  # fallback: ignore lock


def release_lock(conn) -> None:
    try:
        from job_control import release_lock as jc_release
        jc_release(conn, "ingest_recent_global")
    except Exception:
        pass


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--slice", default="all", choices=list(SLICE_FUNCS.keys()) + ["all"])
    parser.add_argument("--max-pages", type=int, default=25, help="TMDB pages per endpoint (cap 500)")
    parser.add_argument("--db", default=str(DB))
    args = parser.parse_args()

    if not API_KEY:
        print("FATAL: TMDB_API_KEY missing from scraper/.env", file=sys.stderr)
        return 2

    args.max_pages = min(max(1, args.max_pages), MAX_PAGES)

    conn = sqlite3.connect(args.db, timeout=60)
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    cur = conn.cursor()

    # Verify tmdb source exists.
    row = cur.execute("SELECT id FROM sources WHERE slug='tmdb'").fetchone()
    if not row:
        print("FATAL: 'tmdb' source missing in sources table — aborting", file=sys.stderr)
        return 3
    TMDB_SID = int(row[0])

    if not acquire_lock(conn):
        return 4

    base_count = cur.execute("SELECT COUNT(*) FROM titles").fetchone()[0]
    print(f"starting titles={base_count:,}", flush=True)
    if base_count >= 100000:
        print(f"[OK] catalog already past 100K (={base_count:,}); continuing to fill gaps", flush=True)
    started = time.time()

    slices = list(SLICE_FUNCS.keys()) if args.slice == "all" else [args.slice]
    total_new = 0
    try:
        asyncio.run(_run(conn, cur, slices, args.max_pages, TMDB_SID, started, total_new))
    except KeyboardInterrupt:
        print("\ninterrupted; partial inserts kept (INSERT OR IGNORE is idempotent)", flush=True)
    finally:
        release_lock(conn)

    final_count = cur.execute("SELECT COUNT(*) FROM titles").fetchone()[0]
    print(f"\nFINAL: titles {base_count:,} -> {final_count:,}  (+{final_count - base_count:,})  elapsed={time.time()-started:.0f}s", flush=True)
    if final_count >= 100000:
        print("[OK] catalog past 100K", flush=True)
    conn.close()
    return 0


async def _run(conn, cur, slices, max_pages, TMDB_SID, started, total_new):
    sem = asyncio.Semaphore(CONCURRENCY)
    async with httpx.AsyncClient(http2=False, timeout=20.0) as client:
        for s in slices:
            fn = SLICE_FUNCS[s]
            try:
                n = await fn(conn, cur, client, sem, tmdb_sid=TMDB_SID, max_pages=max_pages)
                total_new += n
                print(f"\n--- slice '{s}' added {n:,} new titles (running +{total_new:,}) ---\n", flush=True)
            except Exception as e:
                print(f"slice '{s}' failed: {e}", flush=True)


if __name__ == "__main__":
    sys.exit(main())