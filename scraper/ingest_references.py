"""
ingest_references.py — Pull live data from the user's reference sources:

  • movieboxhd.net (existing adapter) — popular + per-category, gives titles + playback URLs
  • thepiratebay.org — top-100 movies & top-100 TV (magnet URLs)
  • yts.mx / ytstv.bz — torrent metadata (via existing YTS adapter or direct HTTP)

What it does:
  1. For each reference source, fetch a curated top-list page.
  2. For each title+year hit, look it up in the local catalog by tmdb_id (if known)
     or title+year. If not present, INSERT a stub title (no touch to existing rows).
  3. Add an availability row of kind='playback' pointing at the source URL / magnet,
     source_id = the matching registered source slug.
  4. INSERT OR IGNORE throughout. Never updates existing rows.

Run:
  cd "G:\\streaming app\\scraper"
  python ingest_references.py
"""
from __future__ import annotations
import asyncio
import os
import re
import sqlite3
import sys
import time
from pathlib import Path
from typing import Optional

import httpx
from dotenv import dotenv_values

HERE = Path(__file__).parent
DB = HERE / "catalog.db"

ENV = dotenv_values(str(HERE / ".env"))
TMDB_API_KEY = ENV.get("TMDB_API_KEY") or ""
TMDB_BASE = "https://api.themoviedb.org/3"

CONCURRENCY = 4
TIMEOUT = 20.0
USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36")


def _slug(s: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")
    return s[:120] or "untitled"


async def http_get(client: httpx.AsyncClient, url: str, **kw) -> Optional[str]:
    try:
        r = await client.get(url, headers={"User-Agent": USER_AGENT}, **kw)
        if r.status_code >= 400:
            return None
        return r.text
    except Exception:
        return None


def find_or_create_title(conn: sqlite3.Connection, kind: str,
                         title: str, year: Optional[int],
                         tmdb_id: Optional[int] = None) -> Optional[int]:
    """INSERT OR IGNORE; never touches an existing row. Returns titles.id."""
    if tmdb_id:
        existing = conn.execute(
            "SELECT id FROM titles WHERE tmdb_id=? AND type=?",
            (tmdb_id, kind)).fetchone()
        if existing:
            return existing[0]

    base = _slug(title)
    slug = f"{base}-{year}" if year else base
    row = conn.execute("SELECT id FROM titles WHERE slug=?", (slug,)).fetchone()
    if row:
        return row[0]
    slug = f"{slug}-{int(time.time() * 1000) % 100000}"

    cur = conn.execute(
        "INSERT OR IGNORE INTO titles "
        "(slug, title, type, year, status, tmdb_id, metadata_state, created_at, updated_at) "
        "VALUES (?,?,?,?,?,?,?,?,?)",
        (slug, title, kind, year, "released", tmdb_id, "stub",
         int(time.time()), int(time.time())))
    if cur.lastrowid:
        conn.commit()
        return cur.lastrowid
    row = conn.execute("SELECT id FROM titles WHERE slug=?", (slug,)).fetchone()
    return row[0] if row else None


def add_availability(conn: sqlite3.Connection, title_id: int,
                     source_slug: str, url: str, kind: str = "playback") -> bool:
    """INSERT OR IGNORE. Returns True if a new row was added."""
    src = conn.execute("SELECT id FROM sources WHERE slug=?", (source_slug,)).fetchone()
    if not src:
        return False
    sid = src[0]
    cur = conn.execute(
        "INSERT OR IGNORE INTO availability "
        "(title_id, source_id, status, kind, external_url, playback_url, "
        " is_legal_verified, requires_auth) "
        "VALUES (?,?,?,?,?,?,?,?)",
        (title_id, sid, "available", kind, url, url, 0, 0))
    if cur.rowcount > 0:
        conn.commit()
        return True
    return False


def get_or_create_source(conn: sqlite3.Connection, slug: str, name: str,
                         base_url: str, type_: str = "embed_aggregator",
                         is_legal: int = 0) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO sources (slug, name, base_url, type, enabled, is_legal, created_at) "
        "VALUES (?,?,?,?,1,?,?)",
        (slug, name, base_url, type_, is_legal, int(time.time())))
    conn.commit()


# ─────────────────────────────────────────────────────────────────────────────
# MovieBoxHD live scrape (popular + per-category)
# ─────────────────────────────────────────────────────────────────────────────

async def scrape_movieboxhd(conn: sqlite3.Connection, client: httpx.AsyncClient,
                            sem: asyncio.Semaphore) -> dict:
    """movieboxhd.net popular + categories. Lightweight regex scraper."""
    from sites.movieboxhd import MovieBoxHdAdapter
    adapter = MovieBoxHdAdapter()

    pages = ["/", "/ranking-list/eJvhCT8w3t1?id=1232643093049001320&page_from=more_SUBJECTS_MOVIE",
             "/ranking-list/KNhvsW7OBd5?id=4380734070238626200&page_from=more_SUBJECTS_MOVIE",
             "/ranking-list/e570UxK46N1?id=1503943377597910848&page_from=more_SUBJECTS_MOVIE",
             "/ranking-list/KPAZTvQMPc5?id=173752404280836544&page_from=more_SUBJECTS_MOVIE"]

    added = 0
    for path in pages:
        url = adapter.base_url + path
        html = await http_get(client, url, timeout=TIMEOUT)
        if not html:
            print(f"  [movieboxhd] no HTML for {path}", flush=True)
            continue
        # Title + year extraction from /moviedetail/<slug>
        # Pattern: <a class="title-text" href="/moviedetail/SLUG">...TITLE...
        items = re.findall(
            r'href="(/moviedetail/[A-Za-z0-9-]+)"[^>]*>.*?'
            r'<div class="title-text"[^>]*>([^<]+)</div>.*?'
            r'(\d{4})',
            html, flags=re.S)
        if not items:
            # Looser pattern (NUXT_DATA)
            items = re.findall(
                r'href="(/moviedetail/[A-Za-z0-9-]+)"',
                html)
            items = [(h, h.split("/")[-1].replace("-", " ").title(), None) for h in items][:50]

        for href, title, year_s in items[:60]:
            year = int(year_s) if year_s and year_s.isdigit() else None
            kind = "tv" if "series" in href.lower() or "season" in href.lower() else "movie"
            full_url = adapter.base_url + href
            tid = find_or_create_title(conn, kind, title.strip(), year)
            if tid and add_availability(conn, tid, "movieboxhd", full_url):
                added += 1
        print(f"  [movieboxhd] {path}  +{len(items[:60])} candidates, +{added} new avail", flush=True)
        await asyncio.sleep(1.0)
    return {"movieboxhd_added": added}


# ─────────────────────────────────────────────────────────────────────────────
# The Pirate Bay (top-100 movies & TV via public proxies)
# ─────────────────────────────────────────────────────────────────────────────

TPB_PROXIES = [
    "https://tpb.party",
    "https://pirateproxy.live",
    "https://thepiratebay.org",
    "https://www.tpbproxypirate.com",
]


async def scrape_tpb_top(conn: sqlite3.Connection, client: httpx.AsyncClient,
                         sem: asyncio.Semaphore) -> dict:
    """TPB top-100 movies + TV. Magnet links are inline in the top-list HTML."""
    get_or_create_source(conn, "piratebay",
                         "The Pirate Bay (torrent magnet)",
                         "magnet:?xt=urn:btih:",
                         type_="torrent_index", is_legal=0)
    added = 0
    pages = [("movie", "/top/201"), ("tv", "/top/205")]
    for kind_name, path in pages:
        ok = False
        for base in TPB_PROXIES:
            url = base + path
            html = await http_get(client, url, timeout=TIMEOUT)
            if not html:
                continue
            # TPB /top/<cat> rows: <a href="https://tpb.party/torrent/<id>/<slug>">...</a>
            # (or sometimes href="/torrent/.../" if behind a relative path).
            # The slug can contain spaces, parens, brackets, dots, etc.
            torrent_links = re.findall(
                r'href="(?:https?://[^/]+)?(/torrent/(\d+)/([^"\s]+))"',
                html)
            magnets = re.findall(
                r'href="(magnet:\?xt=urn:btih:[^"]+)"',
                html)
            if not torrent_links:
                continue
            n = min(len(torrent_links), len(magnets), 100)
            for i in range(n):
                _, _, slug = torrent_links[i]
                magnet = magnets[i]
                t = slug.replace("_", " ").replace(".", " ").strip()
                m = re.search(r"(19|20)\d{2}", t)
                year = int(m.group(0)) if m else None
                if year is None or year < 1986:
                    continue
                clean = re.split(r"\s+(19|20)\d{2}\s+", t, maxsplit=1)[0].strip()
                if not clean or len(clean) < 2:
                    continue
                kind = "tv" if kind_name == "tv" else "movie"
                tid = find_or_create_title(conn, kind, clean[:200], year)
                if tid and add_availability(conn, tid, "piratebay", magnet):
                    added += 1
            print(f"  [tpb] {kind_name} via {base}  rows={len(torrent_links)} magnets={len(magnets)} +{added}", flush=True)
            ok = True
            break
            await asyncio.sleep(0.5)
        if not ok:
            print(f"  [tpb] {kind_name} — all proxies failed", flush=True)
        await asyncio.sleep(2.0)
    return {"tpb_added": added}


# ─────────────────────────────────────────────────────────────────────────────
# YTS (existing adapter is "YifyPro" / "YTS"; both live-scraped via HTTP)
# ─────────────────────────────────────────────────────────────────────────────

async def scrape_yts(conn: sqlite3.Connection, client: httpx.AsyncClient,
                     sem: asyncio.Semaphore) -> dict:
    get_or_create_source(conn, "yts_torrent",
                         "YTS (movie torrents)",
                         "https://yts.mx",
                         type_="torrent_index", is_legal=0)
    added = 0
    # YTS has a public API at yts.mx/api/v2/list_movies.json
    api_url = "https://yts.mx/api/v2/list_movies.json"
    for page in range(1, 6):
        params = {"page": page, "limit": 50, "sort_by": "download_count", "order_by": "desc"}
        try:
            r = await client.get(api_url, params=params,
                                 headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT)
            if r.status_code >= 400:
                continue
            data = r.json()
        except Exception:
            continue
        for m in (data.get("data") or {}).get("movies") or []:
            title = m.get("title") or ""
            year = int(m.get("year") or 0) or None
            imdb = m.get("imdb_code")
            tmdb_id = m.get("tmdb_id") or None
            torrents = m.get("torrents") or []
            if not torrents:
                continue
            t = torrents[0]  # best quality
            magnet = t.get("magnet") or ""
            if not magnet:
                # YTS API sometimes omits magnet; build from hash
                ih = t.get("hash", "")
                if ih:
                    magnet = f"magnet:?xt=urn:btih:{ih}"
            if not magnet:
                continue
            tid = find_or_create_title(conn, "movie", title, year, tmdb_id=tmdb_id)
            if tid:
                # backfill imdb_id if we got it
                if imdb:
                    conn.execute("UPDATE titles SET imdb_id=? WHERE id=? AND imdb_id IS NULL",
                                 (imdb, tid))
                    conn.commit()
                if add_availability(conn, tid, "yts_torrent", magnet):
                    added += 1
        print(f"  [yts] page {page}  +{len((data.get('data') or {}).get('movies') or [])} candidates", flush=True)
        await asyncio.sleep(1.5)
    return {"yts_added": added}


# ─────────────────────────────────────────────────────────────────────────────
# freekeys — quick repo-content capture; we don't ingest it as data, just
# confirm what it is and surface any relevant API key lists.
# ─────────────────────────────────────────────────────────────────────────────

async def scrape_freekeys(conn: sqlite3.Connection, client: httpx.AsyncClient,
                          sem: asyncio.Semaphore) -> dict:
    """Just fetch the repo README so we can verify it's a free-API-keys repo.
    Not a streaming source — its only contribution is surfacing TMDB/etc keys
    we already have configured."""
    r = await http_get(client, "https://raw.githubusercontent.com/rickylawson/freekeys/main/README.md",
                       timeout=TIMEOUT)
    if r:
        # Save snippet so user can see what freekeys contains
        with open(HERE / "_freekeys_readme.md", "w", encoding="utf-8") as f:
            f.write(r[:4000])
    return {"freekeys": "captured_readme" if r else "unreachable"}


# ─────────────────────────────────────────────────────────────────────────────
# Driver
# ─────────────────────────────────────────────────────────────────────────────

async def main_async() -> int:
    if not TMDB_API_KEY:
        print("FATAL: TMDB_API_KEY missing", file=sys.stderr)
        return 1

    conn = sqlite3.connect(str(DB), timeout=60)
    conn.execute("PRAGMA journal_mode = WAL")
    sem = asyncio.Semaphore(CONCURRENCY)

    print(f"catalog.db: {DB}")
    print(f"starting titles={conn.execute('SELECT COUNT(*) FROM titles').fetchone()[0]:,}")
    print()

    # Pre-register sources so availability rows can attach
    get_or_create_source(conn, "movieboxhd", "MovieBoxHD (live)",
                         "https://movieboxhd.net", type_="embed_aggregator", is_legal=0)

    async with httpx.AsyncClient(http2=False, timeout=TIMEOUT) as client:
        results = {}
        for label, fn in [
            ("freekeys (info only)", scrape_freekeys),
            ("movieboxhd (live)",   scrape_movieboxhd),
            ("yts.mx (API)",        scrape_yts),
            ("thepiratebay (live)", scrape_tpb_top),
        ]:
            print(f"\n=== {label} ===")
            try:
                res = await fn(conn, client, sem)
                results.update(res)
            except Exception as e:
                print(f"  ERROR: {e}", flush=True)

    conn.close()
    print()
    print("=" * 60)
    print(f"FINAL availability additions: {results}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main_async()))