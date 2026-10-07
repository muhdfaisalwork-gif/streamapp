"""
ingest_tmdb_scale.py — expand the catalogue past 200K titles.

Why a new script
----------------
`ingest_tmdb_to_100k.py` stops at TMDB's hard cap of 500 pages per paginated
list endpoint. 11 endpoints x 500 pages x 20 per page = 110,000 titles, which is
where the catalogue plateaued at 138,796.

To go past that you have to change the *slice*, not just page deeper. TMDB will
happily return a different set of titles for every combination of year window,
genre, and original language, so we walk a grid of those instead of paging one
list to the ceiling. Union of the slices, deduped by tmdb_id.

Also pulls the four "freshness" feeds on every run, because those are what
change daily:
    movie/now_playing, movie/upcoming, tv/on_the_air, tv/airing_today

Resumable: progress is checkpointed per-slice to .tmdb_scale_state.json, so a
killed run continues where it stopped.

Run:
    python ingest_tmdb_scale.py --target 200000
    python ingest_tmdb_scale.py --dry-run
    python ingest_tmdb_scale.py --fresh-only      # just the daily feeds
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import sqlite3
import sys
import time
from pathlib import Path

import httpx
from dotenv import dotenv_values

HERE = Path(__file__).parent
DB = HERE / "catalog.db"
STATE = HERE / ".tmdb_scale_state.json"

ENV = dotenv_values(str(HERE / ".env"))
API_KEY = ENV.get("TMDB_API_KEY") or ""
ACCESS_TOKEN = ENV.get("TMDB_ACCESS_TOKEN") or ""
BASE = "https://api.themoviedb.org/3"

MAX_PAGES = 500
PAGE_SIZE = 20
CONCURRENCY = 15          # TMDB allows ~50 rps; stay well under

# Year windows for the last 40 years plus the deep back-catalogue, split so no
# single window can exhaust 500 pages.
WINDOWS = [
    ("2026-01-01", "2027-12-31"),
    ("2024-01-01", "2025-12-31"),
    ("2022-01-01", "2023-12-31"),
    ("2020-01-01", "2021-12-31"),
    ("2018-01-01", "2019-12-31"),
    ("2016-01-01", "2017-12-31"),
    ("2014-01-01", "2015-12-31"),
    ("2012-01-01", "2013-12-31"),
    ("2010-01-01", "2011-12-31"),
    ("2005-01-01", "2009-12-31"),
    ("2000-01-01", "2004-12-31"),
    ("1990-01-01", "1999-12-31"),
    ("1980-01-01", "1989-12-31"),
    ("1970-01-01", "1979-12-31"),
    ("1900-01-01", "1969-12-31"),
]

GENRES = [28, 12, 16, 35, 80, 99, 18, 10751, 14, 36, 27, 10402, 9648, 37]


def build_slices() -> list[tuple[str, str, dict, str]]:
    """(slice_id, kind, params, label)"""
    slices: list[tuple[str, str, dict, str]] = []

    # Freshness feeds — always walked, these are the daily changelog.
    slices.append(("now_playing", "movie", {}, "movies in cinemas"))
    slices.append(("upcoming", "movie", {}, "upcoming movies"))
    slices.append(("on_the_air", "tv", {}, "TV airing this week"))
    slices.append(("airing_today", "tv", {}, "TV airing today"))

    # Year windows, two orderings each (popularity + release date) so the union
    # of each window is much larger than a single sorted list.
    for gte, lte in WINDOWS:
        slices.append((
            f"movie:pop:{gte}:{lte}", "movie",
            {"sort_by": "popularity.desc", "primary_release_date.gte": gte, "primary_release_date.lte": lte},
            f"popular movies {gte[:4]}-{lte[:4]}",
        ))
        slices.append((
            f"movie:date:{gte}:{lte}", "movie",
            {"sort_by": "primary_release_date.desc", "primary_release_date.gte": gte, "primary_release_date.lte": lte},
            f"movies by date {gte[:4]}-{lte[:4]}",
        ))
        slices.append((
            f"tv:pop:{gte}:{lte}", "tv",
            {"sort_by": "popularity.desc", "first_air_date.gte": gte, "first_air_date.lte": lte},
            f"popular TV {gte[:4]}-{lte[:4]}",
        ))
        slices.append((
            f"tv:date:{gte}:{lte}", "tv",
            {"sort_by": "first_air_date.desc", "first_air_date.gte": gte, "first_air_date.lte": lte},
            f"TV by date {gte[:4]}-{lte[:4]}",
        ))

    # Animation is called out explicitly in the request, so give it its own
    # deep sweep rather than hoping it surfaces inside the general slices.
    slices.append(("anime:all", "tv", {"with_genres": 16, "sort_by": "popularity.desc"}, "all animation (anime)"))
    slices.append(("anime:movies", "movie", {"with_genres": 16, "sort_by": "popularity.desc"}, "animated films"))
    for origin in ("JP", "KR", "CN"):
        slices.append((f"anime:{origin}", "tv",
                       {"with_origin_country": origin, "with_genres": 16, "sort_by": "popularity.desc"},
                       f"animation from {origin}"))

    # Per-genre sweeps, which reach titles the year windows miss.
    for g in GENRES:
        slices.append((f"movie:genre:{g}", "movie",
                       {"with_genres": g, "sort_by": "popularity.desc"}, f"movies in genre {g}"))
        slices.append((f"tv:genre:{g}", "tv",
                       {"with_genres": g, "sort_by": "popularity.desc"}, f"TV in genre {g}"))

    return slices


def slugify(s: str) -> str:
    s = (s or "").lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")[:120] or "untitled"


def load_state() -> dict:
    if STATE.is_file():
        try:
            return json.loads(STATE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"done": [], "counts": {}}


def save_state(st: dict) -> None:
    STATE.write_text(json.dumps(st, indent=1), encoding="utf-8")


async def fetch_page(client: httpx.AsyncClient, path: str, params: dict, page: int, sem: asyncio.Semaphore):
    async with sem:
        p = {k: v for k, v in params.items() if v is not None}
        p["api_key"] = API_KEY
        p["page"] = page
        p["language"] = "en-US"
        for attempt in range(3):
            try:
                r = await client.get(f"{BASE}/{path}", params=p, timeout=30.0)
                if r.status_code == 429:
                    await asyncio.sleep(2.0 * (attempt + 1))
                    continue
                r.raise_for_status()
                return r.json()
            except Exception:
                if attempt == 2:
                    return None
                await asyncio.sleep(1.0 * (attempt + 1))
    return None


def row_for(item: dict, kind: str) -> tuple | None:
    """Build a titles row from a TMDB list item."""
    tmdb_id = item.get("id")
    if not tmdb_id:
        return None
    if kind == "movie":
        title = item.get("title") or item.get("original_title")
        date = item.get("release_date") or ""
        overview = item.get("overview") or ""
    else:
        title = item.get("name") or item.get("original_name")
        date = item.get("first_air_date") or ""
        overview = item.get("overview") or ""
    if not title:
        return None
    year = None
    if len(date) >= 4 and date[:4].isdigit():
        year = int(date[:4])
    poster = item.get("poster_path")
    backdrop = item.get("backdrop_path")
    return (
        int(tmdb_id),
        int(tmdb_id),
        slugify(title),
        title[:300],
        kind,
        year,
        date[:10] if date else None,
        int(item.get("runtime") or 0) or None,
        None,
        round(float(item.get("vote_average") or 0), 2),
        int(item.get("vote_count") or 0) or 0,
        round(float(item.get("popularity") or 0), 4),
        overview[:2000] if overview else None,
        None,
        (f"https://image.tmdb.org/t/p/w500{poster}") if poster else None,
        (f"https://image.tmdb.org/t/p/w1280{backdrop}") if backdrop else None,
        "complete",
    )


async def walk_slice(client, sem, slice_id, kind, params, label, state, seen_tmdb, conn, dry):
    """Walk one slice, inserting unseen titles. Returns (new_titles, seen_ids)."""
    path = "discover/movie" if kind == "movie" else "discover/tv"
    if slice_id in ("now_playing",):
        path = "movie/now_playing"
    elif slice_id == "upcoming":
        path = "movie/upcoming"
    elif slice_id == "on_the_air":
        path = "tv/on_the_air"
    elif slice_id == "airing_today":
        path = "tv/airing_today"

    new_ids: list[int] = []
    first = await fetch_page(client, path, params, 1, sem)
    if not first:
        return 0, 0
    total_pages = min(int(first.get("total_pages") or 1), MAX_PAGES)

    pages = [first]
    if total_pages > 1 and not dry:
        for chunk_start in range(2, total_pages + 1, CONCURRENCY):
            chunk = range(chunk_start, min(chunk_start + CONCURRENCY, total_pages + 1))
            res = await asyncio.gather(*[fetch_page(client, path, params, pg, sem) for pg in chunk])
            pages.extend([r for r in res if r])

    for pg in pages:
        for item in pg.get("results", []):
            tmdb_id = item.get("id")
            if not tmdb_id:
                continue
            if tmdb_id in seen_tmdb:
                continue
            row = row_for(item, kind)
            if not row:
                continue
            seen_tmdb.add(tmdb_id)
            new_ids.append(tmdb_id)
            if not dry:
                try:
                    conn.execute(
                        "INSERT OR IGNORE INTO titles "
                        "(tmdb_id, id, slug, title, type, year, release_date, runtime, certification, "
                        " rating, rating_count, popularity, overview, tagline, poster, backdrop, metadata_state) "
                        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        row,
                    )
                except sqlite3.Error:
                    continue

    return len(new_ids), total_pages


async def run(args):
    if not API_KEY:
        print("FATAL: TMDB_API_KEY missing from scraper/.env")
        sys.exit(1)

    conn = sqlite3.connect(str(DB), timeout=60)
    conn.execute("PRAGMA journal_mode = WAL")
    cur = conn.cursor()
    cur.execute("SELECT id FROM sources WHERE slug = 'tmdb'")
    row = cur.fetchone()
    if not row:
        print("FATAL: no 'tmdb' source row")
        sys.exit(2)
    TMDB_SID = row[0]

    print("loading existing tmdb_ids...")
    seen_tmdb: set[int] = set()
    for (v,) in cur.execute("SELECT tmdb_id FROM titles WHERE tmdb_id IS NOT NULL AND tmdb_id > 0"):
        try:
            seen_tmdb.add(int(v))
        except (TypeError, ValueError):
            pass
    seen_slug: set[str] = {r[0] for r in cur.execute("SELECT slug FROM titles") if r[0]}

    base = cur.execute("SELECT COUNT(*) FROM titles").fetchone()[0]
    print(f"catalogue starts at {base:,} titles ({len(seen_tmdb):,} unique tmdb_ids)")

    state = load_state()
    done = set(state.get("done", []))
    counts = state.get("counts", {})

    slices = build_slices()
    if args.fresh_only:
        slices = [s for s in slices if s[0] in ("now_playing", "upcoming", "on_the_air", "airing_today")]

    todo = [s for s in slices if s[0] not in done]
    if args.dry_run:
        print(f"{len(todo)} slices to walk (of {len(slices)} total)")
        for sid, kind, _p, label in todo[:12]:
            print(f"  {sid:<28} {kind:<6} {label}")
        return

    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"} if ACCESS_TOKEN else {}
    sem = asyncio.Semaphore(CONCURRENCY)
    started = time.time()
    total_new = 0

    async with httpx.AsyncClient(headers=headers, limits=httpx.Limits(max_connections=30)) as client:
        for i, (sid, kind, params, label) in enumerate(todo, 1):
            try:
                new_n, pages = await walk_slice(client, sem, sid, kind, params, label,
                                                state, seen_tmdb, conn, args.dry_run)
            except Exception as e:
                print(f"  [{i}/{len(todo)}] {sid:<28} FAILED {e}")
                continue
            conn.commit()
            counts[sid] = new_n
            done.add(sid)
            state["done"] = sorted(done)
            state["counts"] = counts
            save_state(state)
            total_new += new_n
            now = conn.execute("SELECT COUNT(*) FROM titles").fetchone()[0]
            rate = total_new / max(time.time() - started, 1)
            print(f"  [{i}/{len(todo)}] {sid:<28} pages={pages:<4} new={new_n:<6} total={now:,} ({rate:.0f}/s)")

            if now >= args.target:
                print(f"TARGET REACHED: {now:,} >= {args.target:,}")
                break

    conn.commit()
    final = conn.execute("SELECT COUNT(*) FROM titles").fetchone()[0]
    print(f"\ndone. {base:,} -> {final:,} (+{final - base:,}) in {time.time() - started:.0f}s")
    for q, lbl in [("SELECT COUNT(*) FROM titles WHERE year >= 2024", "2024+"),
                   ("SELECT COUNT(*) FROM titles WHERE year BETWEEN 1986 AND 2026", "last 40y"),
                   ("SELECT COUNT(*) FROM titles WHERE type = 'anime'", "anime"),
                   ("SELECT COUNT(*) FROM titles WHERE status = 'ongoing'", "ongoing"),
                   ("SELECT COUNT(*) FROM titles WHERE status = 'upcoming'", "upcoming")]:
        try:
            print(f"  {lbl:<12} {conn.execute(q).fetchone()[0]:,}")
        except sqlite3.Error:
            pass
    conn.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", type=int, default=200000)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--fresh-only", action="store_true", help="only the 4 daily-changing feeds")
    args = ap.parse_args()
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
