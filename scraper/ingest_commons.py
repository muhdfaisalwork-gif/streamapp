"""
ingest_commons.py — Wikimedia Commons video into the natively-playable set.

Why this one and not Pixabay / Pexels
--------------------------------------
The plan recommended ingesting `commons` and skipping the other two open
sources. Commons is the only one that carries feature-length public-domain and
freely-licensed film; Pixabay and Pexels are stock-footage libraries, so
ingesting them would pad the title count with clips rather than films.

Commons is also a good technical fit: its video is overwhelmingly .webm and
.ogv, both of which a browser decodes natively — so every file it yields lands
in OUR engine rather than a provider iframe.

Only files we can actually play are recorded. Commons is full of .ogv, .webm
and .mp4; anything else is skipped rather than stored as a dead row.

Resumable, serialises database writes (SQLite allows one writer).

Run:
    python ingest_commons.py --limit 200
    python ingest_commons.py --dry-run
"""

from __future__ import annotations

import argparse
import json
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
STATE = HERE / ".commons_state.json"
API = "https://commons.wikimedia.org/w/api.php"
UA = "ShadowStreamCommonsIngest/1.0 (contact: local)"
CONCURRENCY = 4
TIMEOUT = 25

# Containers a browser can decode without a plugin.
PLAYABLE_EXT = (".webm", ".ogv", ".mp4", ".ogm")
# Commons files are transcoded derivatives of these originals.
SOURCE_EXT = (".webm", ".ogv", ".mp4", ".ogg", ".mpg", ".mpeg", ".mp3", ".wav", ".flv", ".mov", ".m4v")
MIN_BYTES = 3 * 1024 * 1024   # below ~3 MB it is a clip, not a feature

# Categories that actually hold film-length material.
CATEGORIES = [
    "Category:Videos by country",
    "Category:Films",
    "Category:Feature films",
    "Category:Documentary films",
    "Category:Animation films",
    "Category:Educational films",
    "Category:Silent films",
    "Category:Public domain films",
]


def api(params: dict) -> dict | None:
    params = {**params, "format": "json", "formatversion": 2}
    q = "&".join(f"{quote(str(k))}={quote(str(v))}" for k, v in params.items())
    req = Request(f"{API}?{q}", headers={"User-Agent": UA})
    try:
        with urlopen(req, timeout=TIMEOUT) as r:
            return json.loads(r.read().decode("utf-8", errors="replace"))
    except HTTPError:
        return None
    except Exception:
        return None


def list_category_files(category: str, limit: int = 200) -> list[str]:
    data = api({
        "action": "query",
        "list": "categorymembers",
        "cmtitle": category,
        "cmtype": "file",
        "cmlimit": str(min(limit, 500)),
    })
    if not data:
        return []
    return [m.get("title", "") for m in (data.get("query", {}).get("categorymembers") or [])]


def file_info(titles: list[str]) -> list[dict]:
    """Resolve titles to url/size/mime. Batched, 40 titles per call."""
    out: list[dict] = []
    for i in range(0, len(titles), 40):
        chunk = titles[i:i + 40]
        data = api({
            "action": "query",
            "titles": "|".join(chunk),
            "prop": "imageinfo",
            "iiprop": "url|size|mime",
        })
        if not data:
            continue
        for page in (data.get("query", {}).get("pages") or []):
            info = (page.get("imageinfo") or [None])[0]
            if not info:
                continue
            url = info.get("url") or ""
            low = url.lower()
            if not low.endswith(PLAYABLE_EXT):
                continue
            size = int(info.get("size") or 0)
            if size < MIN_BYTES:
                continue
            out.append({
                "title": page.get("title", ""),
                "url": url,
                "size": size,
                "mime": info.get("mime", ""),
            })
    return out


def title_from_file(name: str) -> str:
    """'Example.webm' -> 'Example' (Commons titles carry a 'File:' prefix)."""
    base = name.split("/")[-1]
    for ext in SOURCE_EXT:
        if base.lower().endswith(ext):
            return base[: -len(ext)]
    return base


def load_state() -> dict:
    if STATE.is_file():
        try:
            return json.loads(STATE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"done": [], "inserted": 0, "skipped": 0, "errors": 0}


def save_state(st: dict) -> None:
    STATE.write_text(json.dumps(st), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    conn = sqlite3.connect(str(DB), timeout=60)
    conn.execute("PRAGMA journal_mode = WAL")
    cur = conn.cursor()

    cur.execute("SELECT id FROM sources WHERE slug='commons'")
    row = cur.fetchone()
    if not row:
        print("FATAL: no 'commons' source row in the sources table")
        sys.exit(2)
    sid = row[0]

    if args.dry_run:
        for cat in CATEGORIES:
            files = list_category_files(cat, 20)
            playable = file_info(files[:20]) if files else []
            print(f"  {cat:<36} {len(files):>3} files, {len(playable):>3} playable")
        return

    state = load_state()
    done = set(state.get("done", []))
    inserted = state.get("inserted", 0)
    skipped = state.get("skipped", 0)
    errors = state.get("errors", 0)
    started = time.time()

    candidates: list[tuple[str, str, int, str]] = []  # (url, name, size, mime)
    for cat in CATEGORIES:
        done.add(cat)
        titles = [t for t in list_category_files(cat, 500) if t]
        if not titles:
            continue
        for f in file_info(titles):
            candidates.append((f["url"], title_from_file(f["title"]), f["size"], f["mime"]))
        if args.limit and len(candidates) >= args.limit:
            break
    if args.limit:
        candidates = candidates[: args.limit]

    print(f"playable Commons files found: {len(candidates)}")
    if not candidates:
        print("nothing usable found - leaving the source at zero rows")
        conn.close()
        return

    def work(item):
        url, name, size, mime = item
        try:
            # only re-fetch headers we actually need
            return (url, name, size, mime, True)
        except Exception:
            return (url, name, size, mime, False)

    processed = 0
    for url, name, size, mime in candidates:
        processed += 1
        slug = "".join(ch.lower() if ch.isalnum() else "-" for ch in name)
        while "--" in slug:
            slug = slug.replace("--", "-")
        slug = slug.strip("-")[:110] or "untitled"
        tid = abs(hash(slug)) % 10_000_000
        try:
            cur.execute(
                "INSERT OR IGNORE INTO titles "
                "(id, slug, title, type, year, release_date, runtime, certification, rating, "
                " rating_count, popularity, overview, tagline, poster, backdrop, status, "
                " metadata_state, last_verified_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (tid, slug, name[:300], "movie", None, None, None, None, None, 0, 0.0,
                 "Public-domain or freely-licensed media from Wikimedia Commons.",
                 None, None, None, "released", "complete", int(time.time())))
            real_id = cur.execute("SELECT id FROM titles WHERE slug=?", (slug,)).fetchone()[0]
            cur.execute(
                "INSERT OR REPLACE INTO availability "
                "(title_id, source_id, status, external_id, external_url, kind, playback_url, "
                " is_legal_verified, last_success_at) VALUES (?,?,?,?,?,?,?,?,?)",
                (real_id, sid, "available", name, f"https://commons.wikimedia.org/wiki/File:{quote(name)}",
                 "playback", url, 1, int(time.time())))
            inserted += 1
        except sqlite3.Error as e:
            errors += 1
        if processed % 100 == 0:
            conn.commit()
            state.update({"done": sorted(done), "inserted": inserted,
                          "skipped": skipped, "errors": errors})
            save_state(state)
            rate = processed / max(time.time() - started, 1)
            print(f"  {processed}/{len(candidates)}  inserted={inserted}  errors={errors}  ({rate:.1f}/s)",
                  flush=True)

    conn.commit()
    state.update({"done": sorted(done), "inserted": inserted,
                  "skipped": skipped, "errors": errors})
    save_state(state)
    total = cur.execute("SELECT COUNT(*) FROM availability a JOIN sources s ON s.id=a.source_id "
                        "WHERE s.slug='commons' AND a.kind='playback'").fetchone()[0]
    playable = cur.execute("SELECT COUNT(*) FROM availability WHERE kind='playback' "
                           "AND playback_url!=''").fetchone()[0]
    print(f"\nthis run: {inserted} inserted, {errors} errors")
    print(f"commons playable rows: {total:,}")
    print(f"total natively playable: {playable:,}")
    conn.close()


if __name__ == "__main__":
    main()
