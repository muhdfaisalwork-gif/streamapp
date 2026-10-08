"""
wire_embeds_for_new.py — Wire up embed-aggregator source rows for the new
titles added by ingest_recent_global.py, so the player has actual mirrors
instead of just a TMDB metadata stub.

What this does:
  1. For each new title (id > BASELINE_ID) with a tmdb_id, call
     TMDB /movie/{id}?append_to_response=external_ids (or /tv/...) to pull
     the IMDb id. UPDATE titles SET imdb_id WHERE imdb_id IS NULL only.
  2. INSERT OR IGNORE availability rows for ALL 10 registered embed-
     aggregator sources (vidsrc, superembed, multiembed, 2embed, flixhq,
     gomovies, moviebox, cinezone, embedsu, warezcdn) for each new title.
  3. INSERT OR IGNORE only — never updates or deletes any existing row.

Per project policy this app is a personal-use free multi-mirror picker, so
no is_legal gating is applied; is_legal_verified stays at the DB default (0).

Run:
  cd "G:\\streaming app\\scraper"
  python wire_embeds_for_new.py --baseline 110050
  python wire_embeds_for_new.py --baseline 110050 --limit 200   # smoke test
"""
from __future__ import annotations
import argparse
import asyncio
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
API_KEY = ENV.get("TMDB_API_KEY") or ""
ACCESS_TOKEN = ENV.get("TMDB_ACCESS_TOKEN") or ""
BASE = "https://api.themoviedb.org/3"

CONCURRENCY = 8
RATE_LIMIT_SLEEP = 0.05

# Embed-aggregator URL templates. Format placeholders:
#   {kind}    = "movie" or "tv"
#   {imdb}    = IMDb id (e.g. "tt0133093")
#   {tmdb}    = TMDB id
EMBED_TEMPLATES = {
    "vidsrc":     "https://vidsrc.to/embed/{kind}/{imdb}",
    "2embed":     "https://www.2embed.cc/embed/{imdb}",
    "superembed": "https://multiembed.mov/?video_id={imdb}&tmdb=1",
    "multiembed": "https://multiembed.mov/?video_id={imdb}",
    "flixhq":     "https://flixhq.click/watch-{kind}/{imdb}",
    "gomovies":   "https://gomovies.sx/{kind}/{imdb}",
    "moviebox":   "https://movieboxapp.io/{kind}/{tmdb}",
    "cinezone":   "https://cinezone.cz/embed/{kind}/{imdb}",
    "embedsu":    "https://embed.su/embed/{kind}/{imdb}",
    "warezcdn":   "https://warezcdn.com/embed/{kind}/{imdb}",
}


def _hdr() -> dict:
    return {"Authorization": f"Bearer {ACCESS_TOKEN}"} if ACCESS_TOKEN else {}


async def fetch_external_ids(client: httpx.AsyncClient, sem: asyncio.Semaphore,
                             kind: str, tmdb_id: int) -> Optional[str]:
    """Returns imdb_id (e.g. 'tt123') or None."""
    async with sem:
        for attempt in range(3):
            try:
                r = await client.get(
                    f"{BASE}/{kind}/{tmdb_id}",
                    params={"api_key": API_KEY, "append_to_response": "external_ids"},
                    headers=_hdr(),
                    timeout=15.0,
                )
                if r.status_code == 429:
                    await asyncio.sleep(1.5 * (attempt + 1))
                    continue
                if r.status_code == 401:
                    return None
                r.raise_for_status()
                data = r.json()
                ext = data.get("external_ids") or {}
                imdb = ext.get("imdb_id") or data.get("imdb_id")
                await asyncio.sleep(RATE_LIMIT_SLEEP)
                return imdb if imdb else None
            except (httpx.HTTPError, httpx.TimeoutException):
                if attempt == 2:
                    return None
                await asyncio.sleep(0.5 * (attempt + 1))
        return None


def _build_url(slug: str, kind: str, imdb: Optional[str], tmdb: int) -> Optional[str]:
    """Build embed URL from template. Skip if required placeholder missing."""
    tmpl = EMBED_TEMPLATES[slug]
    needs_imdb = "{imdb}" in tmpl
    if needs_imdb and not imdb:
        return None
    try:
        return tmpl.format(kind=kind, imdb=imdb or "", tmdb=tmdb)
    except KeyError:
        return None


async def run(baseline: int, limit: Optional[int]) -> None:
    if not API_KEY:
        print("FATAL: TMDB_API_KEY missing", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(str(DB), timeout=60)
    conn.execute("PRAGMA journal_mode = WAL")
    cur = conn.cursor()

    # Resolve embed-aggregator source IDs
    embed_slugs = list(EMBED_TEMPLATES.keys())
    placeholders = ",".join("?" for _ in embed_slugs)
    rows = cur.execute(
        f"SELECT id, slug FROM sources WHERE slug IN ({placeholders})",
        embed_slugs,
    ).fetchall()
    source_ids = {slug: sid for sid, slug in rows}
    print(f"embed sources wired up: {len(source_ids)}/10 — slugs={list(source_ids.keys())}")
    if len(source_ids) != 10:
        missing = set(embed_slugs) - set(source_ids.keys())
        print(f"  WARNING: missing sources: {missing}")

    # Pull new titles
    sql = (f"SELECT id, type, tmdb_id, imdb_id FROM titles "
           f"WHERE id > ? AND tmdb_id IS NOT NULL ORDER BY id")
    if limit:
        sql += " LIMIT ?"
        new_rows = cur.execute(sql, (baseline, limit)).fetchall()
    else:
        new_rows = cur.execute(sql, (baseline,)).fetchall()
    print(f"new titles to wire up: {len(new_rows):,}")

    imdb_backfilled = 0
    avail_inserted = 0
    no_imdb = 0
    started = time.time()

    sem = asyncio.Semaphore(CONCURRENCY)
    async with httpx.AsyncClient(http2=False, timeout=20.0) as client:
        for i, (tid, kind, tmdb_id, existing_imdb) in enumerate(new_rows):
            imdb_id = existing_imdb
            if not imdb_id:
                fetched = await fetch_external_ids(client, sem, kind, int(tmdb_id))
                if fetched:
                    cur.execute(
                        "UPDATE titles SET imdb_id=? WHERE id=? AND imdb_id IS NULL",
                        (fetched, tid),
                    )
                    conn.commit()
                    imdb_id = fetched
                    imdb_backfilled += 1
                else:
                    no_imdb += 1

            # Insert availability rows for each embed source
            for slug, sid in source_ids.items():
                url = _build_url(slug, kind, imdb_id, int(tmdb_id))
                if not url:
                    continue
                try:
                    cur.execute(
                        "INSERT OR IGNORE INTO availability "
                        "(title_id, source_id, status, kind, external_url, is_legal_verified, requires_auth) "
                        "VALUES (?,?,?,?,?,?,?)",
                        (tid, sid, "available", "playback", url, 0, 0),
                    )
                    if cur.rowcount > 0:
                        avail_inserted += 1
                except sqlite3.IntegrityError:
                    pass
            conn.commit()

            if (i + 1) % 200 == 0 or (i + 1) == len(new_rows):
                elapsed = time.time() - started
                print(f"  [{i+1}/{len(new_rows)}] imdb_backfilled={imdb_backfilled} "
                      f"avail_rows_added={avail_inserted} no_imdb={no_imdb} "
                      f"elapsed={elapsed:.0f}s")

    elapsed = time.time() - started
    print()
    print("=" * 60)
    print(f"DONE: imdb_backfilled={imdb_backfilled}  no_imdb={no_imdb}  "
          f"avail_rows_added={avail_inserted}  elapsed={elapsed:.0f}s")
    print("=" * 60)
    conn.close()


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--baseline", type=int, default=110050,
                   help="Only wire up titles with id > baseline (default 110050 — the pre-this-session snapshot)")
    p.add_argument("--limit", type=int, default=None,
                   help="Cap number of titles processed (for smoke testing)")
    p.add_argument("--db", default=str(DB))
    args = p.parse_args()
    asyncio.run(run(args.baseline, args.limit))
    return 0


if __name__ == "__main__":
    sys.exit(main())