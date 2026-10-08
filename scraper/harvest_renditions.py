"""
harvest_renditions.py — record every playable rendition per natively-playable title.

Why
---
The backfill picks ONE file per title: the smallest browser-decodable one, so
playback starts fast on a poor connection. But most items ship several — a
Matroska original and an h.264 transcode, or 512Kb and HiRes MP4s. Those extra
renditions are real quality options and they are thrown away today.

This records all of them into availability.quality_options as JSON, which the
Worker exposes and the player's quality menu switches between. The player
already had a quality menu wired to hls.js levels — for progressive MP4 there
are no HLS levels, so it showed nothing. This fills that gap.

Only titles that play in OUR engine are touched. Embed titles decode inside a
provider iframe, so switching the source on our side would change nothing.

Run:
    python harvest_renditions.py --limit 200
    python harvest_renditions.py
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
STATE = HERE / ".rendition_state.json"
CONCURRENCY = 6
UA = "ShadowStreamRenditionHarvester/1.0"

VIDEO_EXT = (".mp4", ".m4v", ".webm")
CONTAINER_EXT = (".mp4", ".m4v", ".webm", ".mkv", ".ogv")

# Rough labels from the archive.org format field.
LABELS = [
    (("hires", "hi-res", "original", "matroska"), "Original"),
    (("h.264", "mpeg4", "512kb", "256kb"), "MP4"),
    (("webm", "vp8", "vp9"), "WebM"),
    (("mpeg2",), "MPEG"),
]


def human_size(n: int) -> str:
    if n >= 1024 ** 3:
        return "%d.%d GB" % (n / 1024 ** 3, (n % 1024 ** 3) // (1024 ** 2) // 10 % 10)
    if n >= 1024 ** 2:
        return "%d MB" % (n / 1024 ** 2)
    if n >= 1024:
        return "%d KB" % (n / 1024)
    return "%d B" % n


def label_for(fmt: str) -> str:
    low = (fmt or "").lower()
    for keys, label in LABELS:
        if any(k in low for k in keys):
            return label
    return (fmt or "Video").strip().title()[:18]


def fetch_metadata(identifier: str):
    req = Request(f"https://archive.org/metadata/{quote(identifier)}", headers={"User-Agent": UA})
    with urlopen(req, timeout=25) as r:
        return json.loads(r.read().decode("utf-8", errors="replace"))


def renditions_for(meta: dict, identifier: str) -> list[dict]:
    """Every video rendition, best label first, each with a real URL."""
    out = []
    for f in meta.get("files") or []:
        name = f.get("name") or ""
        low = name.lower()
        if not low.endswith(CONTAINER_EXT):
            continue
        # Track every rendition, but flag which ones a browser can play
        # directly so the player can mark the rest as download-only.
        browser_ok = low.endswith(VIDEO_EXT)
        try:
            size = int(f.get("size") or 0)
        except (TypeError, ValueError):
            size = 0
        out.append({
            # For progressive files there is no resolution metadata, so the
            # only meaningful differentiator is size. A bare "MP4" label made
            # every option look identical in the player.
            "label": f"{label_for(f.get('format', ''))} · {human_size(size)}" if size else label_for(f.get("format", "")),
            "format": f.get("format", ""),
            "url": f"https://archive.org/download/{quote(identifier)}/{quote(name)}",
            "size": size,
            "container": low.rsplit(".", 1)[-1],
            "browserPlayable": browser_ok,
        })
    out.sort(key=lambda r: (not r["browserPlayable"], r["size"] or 10**12))
    return out


def load_state() -> dict:
    if STATE.is_file():
        try:
            return json.loads(STATE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"done": [], "multi": 0, "items": 0, "errors": 0}


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

    rows = cur.execute("""
        SELECT a.id, a.external_id, a.title_id, t.title
        FROM availability a
        JOIN sources s ON s.id = a.source_id
        JOIN titles t ON t.id = a.title_id
        WHERE a.kind = 'playback' AND a.playback_url != '' AND a.external_id IS NOT NULL
    """).fetchall()

    state = load_state()
    done = set(state.get("done", []))
    pending = [r for r in rows if str(r[1]) not in done]

    print(f"natively-playable items: {len(rows)}")
    print(f"already scanned: {len(done)}   pending: {len(pending)}")
    if args.dry_run:
        for r in pending[:5]:
            print(f"  would scan {r[3][:44]!r}")
        return
    if args.limit:
        pending = pending[: args.limit]

    multi = state.get("multi", 0)
    items = state.get("items", 0)
    errors = state.get("errors", 0)
    started = time.time()

    def work(row):
        aid, ext, tid, title = row
        try:
            return (aid, ext, tid, title, renditions_for(fetch_metadata(ext), ext), True)
        except Exception:
            return (aid, ext, tid, title, None, False)

    with ThreadPoolExecutor(max_workers=CONCURRENCY) as ex:
        futs = [ex.submit(work, r) for r in pending]
        for i, fut in enumerate(as_completed(futs), 1):
            aid, ext, tid, title, rends, ok = fut.result()
            done.add(str(ext))
            if not ok or rends is None:
                errors += 1
                continue
            items += 1
            if len(rends) > 1:
                multi += 1
            cur.execute(
                "UPDATE availability SET quality_options = ? WHERE id = ?",
                (json.dumps(rends, separators=(",", ":")), aid),
            )
            if i % 100 == 0:
                conn.commit()
                state.update({"done": sorted(done), "multi": multi,
                              "items": items, "errors": errors})
                save_state(state)
                rate = i / max(time.time() - started, 1)
                print(f"  {i}/{len(pending)}  items={items}  multi-rendition={multi}  errors={errors}  ({rate:.1f}/s)",
                      flush=True)

    conn.commit()
    state.update({"done": sorted(done), "multi": multi, "items": items, "errors": errors})
    save_state(state)
    with_opts = cur.execute(
        "SELECT COUNT(*) FROM availability WHERE kind='playback' AND quality_options IS NOT NULL "
        "AND quality_options NOT IN ('[]','')"
    ).fetchone()[0]
    print(f"\nthis run: scanned {items}, {multi} with multiple renditions, {errors} errors")
    print(f"playable rows now carrying renditions: {with_opts:,}")
    conn.close()


if __name__ == "__main__":
    main()
