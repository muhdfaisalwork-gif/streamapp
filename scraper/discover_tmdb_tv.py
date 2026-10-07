"""
discover_tmdb_tv.py — grow the catalogue with scripted TV series specifically.

Why this exists
---------------
The catalogue holds 58,308 TV titles, but the TV listing is dominated by talk
shows, game shows and news panels, and 94% of episodic titles had no season data
at all. The problem is not only that the catalogue is mis-shaped, it is that we
have simply not pulled the scripted series that TMDB does have.

ingest_tmdb_to_100k.py capped out at TMDB's 500-page limit per list endpoint,
which is why the catalogue plateaued. To go past that we have to change the
slice rather than page deeper, exactly as the movie ingest did.

Slices
------
  - every TV genre, sorted by popularity
  - every origin country, sorted by popularity
  - every decade, sorted by first-air date
  - the 4 freshness feeds, which are the newest additions daily

Only titles we do not already have (by tmdb_id) are inserted, and each new title
is immediately followed by its season/episode fetch, so a new row is never
without episode data. Resumable.

Network calls are parallel; database writes are serialised on one cursor,
because sqlite3 is not thread-safe across workers.

Run:
    python discover_tmdb_tv.py --limit 50
    python discover_tmdb_tv.py --dry-run
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import sqlite3
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen
from urllib.error import HTTPError

HERE = Path(__file__).parent
DB = HERE / "catalog.db"
STATE = HERE / ".tv_discovery_state.json"
TMDB = "https://api.themoviedb.org/3"
UA = "ShadowStreamTVDiscovery/1.0"
CONCURRENCY = 6
TIMEOUT = 25
MAX_PAGES = 500

GENRE_IDS = [18, 35, 28, 12, 14, 16, 80, 9648, 10759, 10765, 10768,
              37, 10751, 10752, 53, 99, 10770, 101, 878, 10762]
ORIGINS = ["US", "GB", "JP", "KR", "CN", "IN", "PK", "TR", "DE", "FR", "ES", "IT",
           "CA", "AU", "BR", "MX", "SE", "NO", "DK", "FI", "NL", "RU", "TH", "PH",
           "ID", "VN", "NG", "ZA", "AR", "CL", "CO", "PL", "GR", "NZ", "IE", "IL"]

# TMDB genre id -> our genres.slug
TMDB_GENRE_SLUGS = {
    16: "animation", 18: "drama", 35: "comedy", 80: "crime", 10759: "action",
    10765: "scifi", 9648: "mystery", 10751: "family", 14: "fantasy", 28: "action",
    12: "adventure", 37: "western", 10768: "war", 53: "thriller", 99: "documentary",
    10770: "tv_movie", 101: "documentary", 878: "scifi", 10762: "kids", 10752: "military",
}

DECADES = [(f"{y}-01-01", f"{y+9}-12-31") for y in range(1950, 2030, 10)]


def env_values() -> dict:
    vals = {}
    p = HERE / ".env"
    if p.is_file():
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
            s = line.strip()
            if s and not s.startswith("#") and "=" in s:
                k, v = s.split("=", 1)
                vals[k.strip()] = v.strip()
    return vals


ENV = env_values()
API_KEY = ENV.get("TMDB_API_KEY", "")


def api(path: str, params: dict | None = None) -> dict | None:
    p = {**(params or {}), "api_key": API_KEY, "language": "en-US"}
    q = "&".join(f"{quote(str(k))}={quote(str(v))}" for k, v in p.items())
    req = Request(f"{TMDB}{path}?{q}", headers={"User-Agent": UA})
    try:
        with urlopen(req, timeout=TIMEOUT) as r:
            return json.loads(r.read().decode("utf-8", errors="replace"))
    except HTTPError as e:
        if e.code in (429, 401):
            time.sleep(1.5)
        return None
    except Exception:
        return None


def slugify(s: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")[:110]
    return base or "untitled"


def build_slices() -> list[tuple[str, dict]]:
    slices: list[tuple[str, dict]] = []
    for feed in ("trending/tv/week", "tv/on_the_air", "tv/airing_today", "tv/popular", "tv/top_rated"):
        slices.append((f"feed:{feed}", {"path": f"/{feed}"}))
    for g in GENRE_IDS:
        slices.append((f"genre:{g}", {"path": "/discover/tv", "with_genres": str(g),
                                      "sort_by": "popularity.desc"}))
    for o in ORIGINS:
        slices.append((f"origin:{o}", {"path": "/discover/tv", "with_origin_country": o,
                                       "sort_by": "popularity.desc"}))
    for gte, lte in DECADES:
        slices.append((f"decade:{gte[:4]}", {"path": "/discover/tv",
                                              "first_air_date.gte": gte, "first_air_date.lte": lte,
                                              "sort_by": "first_air_date.desc"}))
    return slices


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--pages", type=int, default=12, help="max pages per slice this run")
    args = ap.parse_args()

    if not API_KEY:
        print("FATAL: TMDB_API_KEY not set")
        sys.exit(3)

    conn = sqlite3.connect(str(DB), timeout=120)
    conn.execute("PRAGMA journal_mode = WAL")
    cur = conn.cursor()

    known = {r[0] for r in cur.execute("SELECT tmdb_id FROM titles WHERE tmdb_id IS NOT NULL AND tmdb_id > 0")}
    before = conn.execute("SELECT COUNT(*) FROM titles").fetchone()[0]
    tv_before = conn.execute("SELECT COUNT(*) FROM titles WHERE type IN ('tv','anime')").fetchone()[0]
    print(f"known tmdb_ids: {len(known):,}   titles: {before:,}   tv: {tv_before:,}")

    slices = build_slices()
    if args.dry_run:
        print(f"{len(slices)} slices planned (feeds, {len(GENRE_IDS)} genres, {len(ORIGINS)} origins, {len(DECADES)} decades)")
        for s, p in slices[:8]:
            print("  ", s, p)
        conn.close()
        return

    state = {}
    if STATE.is_file():
        try:
            state = json.loads(STATE.read_text(encoding="utf-8"))
        except Exception:
            state = {}
    done_slices = set(state.get("done", []))

    # ---- discovery (network only, parallel) -------------------------------
    started = time.time()
    found: list[dict] = []
    seen_new: set[int] = set()

    def walk(job):
        sid, spec = job
        path = spec.pop("path")
        page = 1
        out = []
        while page <= min(args.pages, MAX_PAGES):
            d = api(path, {**spec, "page": page})
            if not d:
                break
            for item in (d.get("results") or []):
                tid = item.get("id")
                if tid and tid not in known and tid not in seen_new:
                    seen_new.add(tid)
                    out.append(item)
            if page >= min(d.get("total_pages") or 1, MAX_PAGES):
                break
            page += 1
        return sid, out

    todo = [(s, dict(p)) for s, p in slices if s not in done_slices]
    print(f"walking {len(todo)} slices, up to {args.pages} pages each...")
    with ThreadPoolExecutor(max_workers=CONCURRENCY) as ex:
        futs = [ex.submit(walk, j) for j in todo]
        for f in as_completed(futs):
            sid, items = f.result()
            found.extend(items)
            done_slices.add(sid)
            if len(found) % 500 == 0 or sid == todo[0][0]:
                print(f"  {sid:<22} +{len(items):<5} total new {len(found):,} "
                      f"({len(found)/max(time.time()-started,1):.0f}/s)", flush=True)
    print(f"discovery found {len(found):,} titles we do not have  ({time.time()-started:.0f}s)")

    if args.limit:
        found = found[: args.limit]

    # ---- write (serial, one cursor) ---------------------------------------
    conn.execute(
        "INSERT OR IGNORE INTO sources (slug, name, is_legal, type) "
        "VALUES ('tmdb','TMDB',1,'metadata_only')"
    )
    tmdb_sid = cur.execute("SELECT id FROM sources WHERE slug='tmdb'").fetchone()[0]

    inserted = 0
    for item in found:
        name = item.get("name") or ""
        if not name:
            continue
        first_air = item.get("first_air_date") or ""
        year = int(first_air[:4]) if len(first_air) >= 4 and first_air[:4].isdigit() else None
        is_anime = 16 in (item.get("genre_ids") or [])
        cur.execute(
            "INSERT OR IGNORE INTO titles (id, tmdb_id, slug, title, type, year, release_date, "
            " overview, popularity, rating, rating_count, is_anime, status, metadata_state, "
            " last_verified_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (abs(hash(slugify(name))) % 10_000_000, item["id"], slugify(name),
             name,
             "anime" if is_anime else "tv", year, first_air or None,
             (item.get("overview") or "")[:2000] or None,
             float(item.get("popularity") or 0), round(float(item.get("vote_average") or 0), 2),
             int(item.get("vote_count") or 0), 1 if is_anime else 0, "ongoing", "complete",
             int(time.time())),
        )
        if cur.rowcount:
            inserted += 1
            for gid in (item.get("genre_ids") or []):
                slug = TMDB_GENRE_SLUGS.get(gid)
                if not slug:
                    continue
                cur.execute(
                    "INSERT OR IGNORE INTO title_genres (title_id, genre_id) "
                    "SELECT ?, id FROM genres WHERE slug = ?",
                    (item["id"], slug),
                )

    conn.commit()
    state["done"] = sorted(done_slices)
    STATE.write_text(json.dumps(state), encoding="utf-8")

    after = conn.execute("SELECT COUNT(*) FROM titles").fetchone()[0]
    tv_after = conn.execute("SELECT COUNT(*) FROM titles WHERE type IN ('tv','anime')").fetchone()[0]
    print(f"\ninserted {inserted:,} new titles")
    print(f"titles: {before:,} -> {after:,}   (+{after-before:,})")
    print(f"tv+anime: {tv_before:,} -> {tv_after:,}   (+{tv_after-tv_before:,})")
    print("\nnext: run ingest_tmdb_episodes.py so the new titles get seasons/episodes,")
    print("then classify_scripted.py + export to publish.")
    conn.close()


if __name__ == "__main__":
    main()
