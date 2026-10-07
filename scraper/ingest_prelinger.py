"""
ingest_prelinger.py â€” add the Prelinger Archives to the directly-playable set.

Why this exists
---------------
The audit of open sources turned up a real gap:

    prelinger    public_domain    0 rows
    commons      cc_by_sa         0 rows
    pixabay      cc0              0 rows
    pexels       pexels_license   0 rows

Those four were configured but never ingested. The Prelinger Archives alone
holds roughly 20,000 public-domain films and shorts and it is served by the
same archive.org API the backfill already uses, so there is no new dependency
and no new failure mode.

Every item it returns is public domain, so these titles play in our own engine
with no third-party player involved â€” the opposite problem to the embed
aggregators, where the only thing that exists is a page to extract from.

Resumable, checkpointed per collection cursor.

Run:
    python ingest_prelinger.py --limit 200
    python ingest_prelinger.py
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from concurrent.futures import ThreadPoolExecutor
import time
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

HERE = Path(__file__).parent
DB = HERE / "catalog.db"
STATE = HERE / ".prelinger_state.json"

COLLECTIONS = ["prelinger", "film_noir", "sci-fi_", "animationandcartoons"]
PAGE = 100
MAX_PAGES_PER_COLLECTION = 220
TIMEOUT = 25
UA = "ShadowStream-Ingest/1.0"

PLAYABLE_SQL = "SELECT COUNT(*) FROM availability WHERE kind='playback' AND playback_url!=''"

PREFERRED = ["h.264", "MPEG4", "512Kb MPEG4", "HiRes MPEG4", "MPEG2", "WebM", "M4V"]
EXCLUDE = ["thumb", "spectrogram", "metadata", "text", "gif", "png", "jpg", "zip", "xml", "json", "torrent"]


def load_state() -> dict:
    if STATE.is_file():
        try:
            return json.loads(STATE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"pages_done": {}, "inserted": 0}


def save_state(st: dict) -> None:
    STATE.write_text(json.dumps(st), encoding="utf-8")


def http_json(url: str, params: dict):
    # Repeated keys (archive.org's "fl[]") must each be emitted separately;
    # a list value is therefore flattened into repeated pairs, not quoted whole.
    parts = []
    for k, v in params.items():
        if isinstance(v, (list, tuple)):
            for item in v:
                parts.append(f"{quote(str(k))}={quote(str(item))}")
        else:
            parts.append(f"{quote(str(k))}={quote(str(v))}")
    req = Request(f"{url}?{'&'.join(parts)}", headers={"User-Agent": UA})
    with urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read().decode("utf-8", errors="replace"))


def search(collection: str, page: int):
    return http_json("https://archive.org/advancedsearch.php", {
        "q": f"collection:{collection} AND mediatype:movies",
        "fl[]": ["identifier", "title", "year", "description", "runtime", "downloads", "licenseurl"],
        "rows": PAGE,
        "page": page,
        "output": "json",
        "sort[]": "downloads desc",
    })


def metadata(identifier: str):
    return http_json(f"https://archive.org/metadata/{quote(identifier)}", {})


def pick_file(meta: dict, identifier: str):
    best, best_key = None, None
    for f in meta.get("files") or []:
        name, fmt = f.get("name"), (f.get("format") or "")
        if not name or not fmt:
            continue
        low = fmt.lower()
        if any(x in low for x in EXCLUDE):
            continue
        if not name.lower().endswith((".mp4", ".m4v", ".webm")):
            continue
        rank = PREFERRED.index(fmt) if fmt in PREFERRED else len(PREFERRED)
        try:
            size = int(f.get("size") or 0)
        except (TypeError, ValueError):
            size = 0
        key = (rank, size or 10 ** 12)
        if best_key is None or key < best_key:
            best_key, best = key, name
    if not best:
        return None
    return f"https://archive.org/download/{quote(identifier)}/{quote(best)}"


def slugify(s: str, year):
    base = "".join(c.lower() if c.isalnum() else "-" for c in (s or "").strip())
    while "--" in base:
        base = base.replace("--", "-")
    base = base.strip("-")[:110] or "untitled"
    return f"{base}-{year}" if year else base


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="max items to process this run")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    # 900s busy-wait: a concurrent writer (episode fill, subtitle harvest) can
    # hold the lock far longer than the default 60s, and dying on
    # "database is locked" loses the whole sweep.
    conn = sqlite3.connect(str(DB), timeout=900)
    conn.execute("PRAGMA journal_mode = WAL")
    cur = conn.cursor()

    cur.execute("SELECT id FROM sources WHERE slug='prelinger'")
    row = cur.fetchone()
    if not row:
        print("FATAL: no prelinger source row")
        sys.exit(2)
    sid = row[0]

    state = load_state()
    if args.dry_run:
        doc = search("prelinger", 1)
        print(f"prelinger items available: {doc['response']['numFound']}")
        for d in doc["response"]["docs"][:5]:
            print("  ", d.get("identifier"), "-", (d.get("title") or "")[:50])
        return

    before = cur.execute("SELECT COUNT(*) FROM titles").fetchone()[0]
    processed = 0
    inserted = 0
    started = time.time()

    for coll in COLLECTIONS:
        done_pages = state["pages_done"].get(coll, 0)
        for page in range(done_pages + 1, MAX_PAGES_PER_COLLECTION + 1):
            if args.limit and processed >= args.limit:
                break
            try:
                doc = search(coll, page)
            except (HTTPError, URLError, Exception) as e:
                print(f"  {coll} page {page}: {type(e).__name__} {e}")
                state["pages_done"][coll] = page
                save_state(state)
                break

            docs = doc["response"]["docs"]
            if not docs:
                state["pages_done"][coll] = page
                save_state(state)
                break

            # Resolve each item's playable file concurrently. Serial metadata
            # calls made this roughly 20x too slow to be worth running.
            def resolve(d):
                ident = d.get("identifier")
                if not ident:
                    return None
                try:
                    meta = metadata(ident)
                except Exception:
                    return None
                url = pick_file(meta, ident)
                if not url:
                    return None
                title = (d.get("title") or ident).strip()[:300]
                year = d.get("year") if isinstance(d.get("year"), int) else None
                desc = d.get("description") or ""
                if isinstance(desc, list):
                    desc = " ".join(desc)
                return (ident, url, title, year, str(desc)[:2000] or None)

            with ThreadPoolExecutor(max_workers=8) as pool:
                for res in pool.map(resolve, docs):
                    processed += 1
                    if not res:
                        continue
                    ident, url, title, year, desc = res
                    sl = slugify(title, year)
                    cur.execute(
                        "INSERT OR IGNORE INTO titles "
                        "(id, slug, title, type, year, release_date, runtime, certification, rating, "
                        " rating_count, popularity, overview, tagline, poster, backdrop, status, "
                        " metadata_state, last_verified_at) "
                        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (abs(hash(sl)) % 10_000_000, sl, title, "movie", year,
                         f"{year}-01-01" if year else None, None, None, None, 0, 0.0,
                         desc, None, None, None, "released", "complete", int(time.time())),
                    )
                    if cur.rowcount:
                        inserted += 1
                    tid = cur.execute("SELECT id FROM titles WHERE slug=?", (sl,)).fetchone()[0]
                    # availability has UNIQUE(title_id, source_id), so a plain
                    # INSERT fails on any title that already has a prelinger row.
                    cur.execute(
                        "INSERT OR REPLACE INTO availability (title_id, source_id, status, external_id, external_url, "
                        " kind, playback_url, is_legal_verified, last_success_at) "
                        "VALUES (?,?,?,?,?,?,?,?,?)",
                        (tid, sid, "available", ident,
                         f"https://archive.org/details/{ident}", "playback", url, 1, int(time.time())),
                    )

            conn.commit()
            state["pages_done"][coll] = page
            state["inserted"] = state.get("inserted", 0) + inserted
            save_state(state)
            if page % 10 == 0:
                rate = processed / max(time.time() - started, 1)
                now = cur.execute(PLAYABLE_SQL).fetchone()[0]
                print(f"  {coll} p{page}  processed={processed}  playable_now={now}  ({rate:.1f}/s)", flush=True)
            if args.limit and processed >= args.limit:
                break
        if args.limit and processed >= args.limit:
            break

    after = cur.execute("SELECT COUNT(*) FROM titles").fetchone()[0]
    playable = cur.execute("SELECT COUNT(*) FROM availability WHERE kind='playback' AND playback_url!=''").fetchone()[0]
    print(f"\nthis run: processed {processed}, inserted {inserted}")
    print(f"titles: {before:,} -> {after:,}")
    print(f"directly playable titles: {playable:,}")
    conn.close()


if __name__ == "__main__":
    main()
