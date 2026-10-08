"""
ingest_movie_releases.py — release type + where-to-watch for movies.

What exists today
-----------------
142,481 movies, but only 1,599 title_streaming_providers rows and a single
flat `release_date`. Nothing distinguishes a cinema release from a digital one,
and there is no per-country release information. So "running on all the
streaming platforms, digital release and cinema release" is not answerable
from the current data.

This adds both halves, from the two keys already provisioned:

  * TMDB   /movie/{id}/release_dates  -> release_type per country
           (2=premiere, 3=theatrical limited, 4=theatrical, 5=digital,
            6=physical, 7=TV) with the date for each
  * MDBList /movie/{id}/stream       -> where it streams, by region

Scope
-----
Movies only, and only those without a release record yet, so re-runs are cheap
and already-populated titles are never re-fetched. Ordered by popularity
descending, so the films people actually search for are covered first.

Network calls run in parallel; every database write happens on one cursor,
because sqlite3 is not thread-safe across workers.

Run:
    python ingest_movie_releases.py --dry-run
    python ingest_movie_releases.py --limit 200
    python ingest_movie_releases.py
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sqlite3
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen
from urllib.error import HTTPError

HERE = Path(__file__).parent
DB = HERE / "catalog.db"
STATE = HERE / ".movie_releases_state.json"
TMDB = "https://api.themoviedb.org/3"
MDB = "https://api.mdblist.com"
UA = "ShadowStreamMovieReleases/1.0"
CONCURRENCY = 6
TIMEOUT = 25

# TMDB release_type codes
RELEASE_TYPES = {
    1: "premiere", 2: "theatrical_limited", 3: "digital", 4: "physical",
    5: "tv", 6: "digital", 7: "physical", 8: "tv",
}


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
TMDB_KEY = ENV.get("TMDB_API_KEY", "")
MDB_KEY = ENV.get("MDBLIST_API_KEY", "")

DDL_RELEASE = """
CREATE TABLE IF NOT EXISTS movie_releases (
    id           INTEGER PRIMARY KEY,
    title_id     INTEGER NOT NULL,
    iso_3166_1   TEXT,
    country      TEXT,
    release_type INTEGER,
    release_kind TEXT,
    release_date TEXT,
    note         TEXT,
    UNIQUE(title_id, country, release_type, release_date)
)
"""
DDL_WATCH = """
CREATE TABLE IF NOT EXISTS title_watch_sources (
    id            INTEGER PRIMARY KEY,
    title_id      INTEGER NOT NULL,
    provider_slug TEXT,
    provider_name TEXT,
    region        TEXT,
    offer_type    TEXT,
    release_year  INTEGER,
    UNIQUE(title_id, provider_slug, region, offer_type)
)
"""


def get_json(url: str, headers: dict):
    req = Request(url, headers=headers)
    try:
        with urlopen(req, timeout=TIMEOUT) as r:
            return json.loads(r.read().decode("utf-8", errors="replace"))
    except HTTPError as e:
        if e.code in (429, 401, 403):
            time.sleep(1.0)
        return None
    except Exception:
        return None


def fetch_tmdb_releases(tmdb_id: int):
    url = (f"{TMDB}/movie/{tmdb_id}/release_dates?api_key={quote(TMDB_KEY)}"
           f"&append_to_response=external_ids")
    d = get_json(url, {"User-Agent": UA, "Accept": "application/json"})
    if not d:
        return []
    out = []
    for r in (d.get("results") or []):
        iso = r.get("iso_3166_1")
        name = None
        for c in (r.get("release_dates") or []):
            t = c.get("type")
            # TMDB type 3 is the theatrical bucket; keep every distinct type.
            out.append((iso, iso, int(t), RELEASE_TYPES.get(int(t), "other"),
                        c.get("release_date"), (c.get("note") or "")[:300]))
    return out


def fetch_mdblist(tmdb_id: int):
    """MDBList detail by TMDB id.

    The path is /tmdb/movie/{id}, NOT /movie/{id}/stream — the latter returns
    "Invalid media_type", which reads like a bad key but is a bad path.
    Carries `released` (cinema), `released_digital` and `watch_providers`,
    which is the whole point of this script.
    """
    url = f"{MDB}/tmdb/movie/{tmdb_id}?apikey={quote(MDB_KEY)}"
    d = get_json(url, {"User-Agent": UA})
    if not isinstance(d, dict):
        return [], {}
    offers = []
    for p in (d.get("watch_providers") or []):
        name = p.get("name")
        if not name:
            continue
        offers.append((str(p.get("id") or name), name, "global", "stream", d.get("year")))
    meta = {
        "released": d.get("released"),
        "released_digital": d.get("released_digital"),
    }
    return offers, meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not TMDB_KEY:
        print("FATAL: TMDB_API_KEY not set")
        sys.exit(3)

    conn = sqlite3.connect(str(DB), timeout=300)
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA foreign_keys=OFF")
    conn.execute(DDL_RELEASE)
    conn.execute(DDL_WATCH)
    cur = conn.cursor()

    rows = cur.execute("""
        SELECT id, tmdb_id FROM titles
        WHERE type = 'movie' AND tmdb_id IS NOT NULL AND tmdb_id > 0
          AND id NOT IN (SELECT title_id FROM movie_releases)
        ORDER BY popularity DESC
    """).fetchall()

    if args.dry_run:
        print(f"movies awaiting release data: {len(rows):,}")
        print(f"  MDBList key present: {bool(MDB_KEY)}")
        print(f"  already have releases: {cur.execute('SELECT COUNT(DISTINCT title_id) FROM movie_releases').fetchone()[0]:,}")
        for r in rows[:5]:
            print(f"    would fetch tmdb={r[1]}")
        conn.close()
        return

    if args.limit:
        rows = rows[: args.limit]

    state = {}
    if STATE.is_file():
        try:
            state = json.loads(STATE.read_text(encoding="utf-8"))
        except Exception:
            state = {}
    done = set(state.get("done", []))

    started = time.time()
    rel_n = watch_n = errs = 0
    processed = 0
    db_lock = __import__("threading").Lock()

    def work(row):
        tid, tmdb_id = row
        rel = fetch_tmdb_releases(tmdb_id)
        watch, mdmeta = fetch_mdblist(tmdb_id) if MDB_KEY else ([], {})
        return tid, rel, watch, mdmeta

    def write(chunk):
        nonlocal rel_n, watch_n, errs, processed
        with db_lock:
            for tid, rel, watch, mdmeta in chunk:
                processed += 1
                done.add(str(tid))
                for iso, cname, rtype, rkind, rdate, note in rel:
                    cur.execute(
                        "INSERT OR IGNORE INTO movie_releases "
                        "(title_id, iso_3166_1, country, release_type, release_kind, release_date, note) "
                        "VALUES (?,?,?,?,?,?,?)",
                        (tid, iso, cname, rtype, rkind, rdate, note),
                    )
                    rel_n += 1
                if mdmeta.get("released_digital"):
                    cur.execute(
                        "INSERT OR IGNORE INTO movie_releases "
                        "(title_id, iso_3166_1, country, release_type, release_kind, release_date, note) "
                        "VALUES (?,?,?,?,?,?,?)",
                        (tid, None, "global", 6, "digital", mdmeta["released_digital"], "mdblist"),
                    )
                    rel_n += 1
                for slug, name, region, offer, year in watch:
                    cur.execute(
                        "INSERT OR IGNORE INTO title_watch_sources "
                        "(title_id, provider_slug, provider_name, region, offer_type, release_year) "
                        "VALUES (?,?,?,?,?,?)",
                        (tid, slug, name, region, offer, year),
                    )
                    watch_n += 1
            conn.commit()
            if processed % 50 == 0:
                state["done"] = sorted(done)
                STATE.write_text(json.dumps(state), encoding="utf-8")
                rate = processed / max(time.time() - started, 1)
                print(f"  {processed}/{len(rows)}  releases={rel_n}  watch={watch_n}  "
                      f"errors={errs}  ({rate:.1f}/s)", flush=True)

    WINDOW = CONCURRENCY * 8
    with ThreadPoolExecutor(max_workers=CONCURRENCY) as ex:
        for i in range(0, len(rows), WINDOW):
            batch = rows[i:i + WINDOW]
            write(list(ex.map(work, batch)))

    state["done"] = sorted(done)
    STATE.write_text(json.dumps(state), encoding="utf-8")

    tot_rel = cur.execute("SELECT COUNT(*) FROM movie_releases").fetchone()[0]
    tot_watch = cur.execute("SELECT COUNT(*) FROM title_watch_sources").fetchone()[0]
    covered = cur.execute("SELECT COUNT(DISTINCT title_id) FROM movie_releases").fetchone()[0]
    print(f"\nprocessed {processed:,} in {time.time()-started:.0f}s")
    print(f"movie_releases rows        : {tot_rel:,}  (covering {covered:,} titles)")
    print(f"title_watch_sources rows   : {tot_watch:,}")
    print("sample release kinds:")
    for r in cur.execute("SELECT release_kind, COUNT(*) FROM movie_releases GROUP BY 1 ORDER BY 2 DESC"):
        print(f"   {r[0]:<20} {r[1]:,}")
    conn.close()


if __name__ == "__main__":
    main()
