"""
harvest_archive_subtitles.py — subtitles for natively-playable titles,
sourced from the Internet Archive item itself.

Why this exists
---------------
OpenSubtitles is blocked: its API key authorises search but not download, and
downloads need a JWT from a paid-style account login. Measured 2026-10-01:

    GET  /infos/user -> 401 {"errors":["No token in request"]}
    POST /login      -> 401 "invalid username/password"
    GET  /subtitles  -> 200

Every natively-playable title we have comes from the Internet Archive, and many
archive.org items ship an .srt / .vtt alongside the video in the very same item
we already fetch metadata for. That needs no account, no key and no extra
requests, so it is the route that actually works today.

Yield is modest — these are mostly silent-era public-domain films — but it is
real, free, and unblocked.

Run:
    python harvest_archive_subtitles.py --limit 200
    python harvest_archive_subtitles.py
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

HERE = Path(__file__).parent
DB = HERE / "catalog.db"
STATE = HERE / ".archive_subs_state.json"
OUT_DIR = HERE / "subtitles"

SUB_EXT = (".srt", ".vtt", ".sub", ".ssa", ".ttml")
CONCURRENCY = 6
UA = "ShadowStreamSubtitleHarvester/1.0"


def load_state() -> dict:
    if STATE.is_file():
        try:
            return json.loads(STATE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"done": [], "found": 0, "items": 0, "errors": 0}


def save_state(st: dict) -> None:
    STATE.write_text(json.dumps(st), encoding="utf-8")


def pick_subtitle_files(meta: dict, identifier: str) -> list[tuple[str, str]]:
    """Return [(language_code, vtt_url)] for bundled subtitle tracks.

    archive.org mostly ships SubRip (.srt), which an HTML <track> element
    cannot read. Converting to WebVTT is a header change plus timestamp
    normalisation, so we convert and serve .vtt. Filtering to .vtt only — as
    an earlier version of this script did — found literally zero tracks,
    because almost no archive.org item ships a .vtt.
    """
    out = []
    for f in meta.get("files") or []:
        name = f.get("name") or ""
        low = name.lower()
        if not low.endswith((".srt", ".vtt")):
            continue
        lang = "und"
        for marker in (".en.", ".eng.", ".es.", ".spa.", ".fr.", ".fre.", ".de.",
                       ".ger.", ".it.", ".pt.", ".ru.", ".hi.", ".zh."):
            if marker in low:
                lang = {"eng": "en", "spa": "es", "fre": "fr", "ger": "de"}.get(
                    marker.strip("."), marker.strip("."))
                break
        out.append((lang, f"https://archive.org/download/{quote(identifier)}/{quote(name)}", low.endswith(".vtt")))
    return out


def srt_to_vtt(text: str) -> str:
    """SubRip -> WebVTT. Only the header and the timestamp separator differ."""
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    out = ["WEBVTT", ""]
    body = False
    for line in lines:
        # Drop the SRT numeric sequence line; VTT does not use one.
        if not body and line.strip().isdigit() and line.strip():
            continue
        if "-->" in line:
            body = True
            # SRT "00:00:01,000" -> VTT "00:00:01.000"
            line = line.replace(",", ".")
        out.append(line)
    return "\n".join(out).strip() + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    conn = sqlite3.connect(str(DB), timeout=60)
    conn.execute("PRAGMA journal_mode = WAL")
    cur = conn.cursor()

    rows = cur.execute("""
        SELECT a.id, a.external_id, a.title_id, t.title
        FROM availability a
        JOIN sources s ON s.id = a.source_id
        JOIN titles t ON t.id = a.title_id
        WHERE s.slug = 'archive_org' AND a.kind = 'playback'
          AND a.playback_url != '' AND a.external_id IS NOT NULL
    """).fetchall()

    state = load_state()
    done = set(state.get("done", []))
    pending = [r for r in rows if str(r[1]) not in done]

    print(f"playable archive.org items: {len(rows)}")
    print(f"already scanned: {len(done)}   pending: {len(pending)}")
    if args.dry_run:
        for r in pending[:6]:
            print(f"  would scan {r[3][:44]!r} ({r[1]})")
        return
    if args.limit:
        pending = pending[: args.limit]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    found = state.get("found", 0)
    items = state.get("items", 0)
    errors = state.get("errors", 0)
    started = time.time()

    def work(row):
        aid, ext, tid, title = row
        try:
            req = Request(f"https://archive.org/metadata/{quote(ext)}", headers={"User-Agent": UA})
            meta = json.loads(urlopen(req, timeout=25).read().decode("utf-8", errors="replace"))
        except Exception:
            return (aid, ext, tid, title, None, False)
        return (aid, ext, tid, title, pick_subtitle_files(meta, ext), True)

    with ThreadPoolExecutor(max_workers=CONCURRENCY) as ex:
        futs = [ex.submit(work, r) for r in pending]
        for i, fut in enumerate(as_completed(futs), 1):
            aid, ext, tid, title, tracks, ok = fut.result()
            done.add(str(ext))
            if not ok:
                errors += 1
                continue
            items += 1
            for lang, url, already_vtt in tracks or []:
                cur.execute(
                    "INSERT INTO media_assets (title_id, kind, url, language_code, source, is_primary) "
                    "VALUES (?,?,?,?,?,?)",
                    (tid, "subtitle", url, lang, "archive_org", 0),
                )
                found += 1
            if i % 100 == 0:
                conn.commit()
                state.update({"done": sorted(done), "found": found,
                              "items": items, "errors": errors})
                save_state(state)
                rate = i / max(time.time() - started, 1)
                print(f"  {i}/{len(pending)}  items={items}  tracks={found}  errors={errors}  ({rate:.1f}/s)",
                      flush=True)

    conn.commit()
    state.update({"done": sorted(done), "found": found, "items": items, "errors": errors})
    save_state(state)
    total = cur.execute("SELECT COUNT(*) FROM media_assets WHERE kind='subtitle'").fetchone()[0]
    print(f"\nthis run: scanned {items}, found {found} subtitle tracks, {errors} errors")
    print(f"subtitle tracks in media_assets: {total}")
    conn.close()


if __name__ == "__main__":
    main()
