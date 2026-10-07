"""
backfill_archive_playback.py — turn the public-domain catalogue into natively
playable content.

The problem
-----------
23,485 titles already carry an Internet Archive identifier, but their
availability rows were written with kind='embed' and an empty playback_url, so
the player had nothing to load and fell through to the provider-iframe path
for content that is actually public domain and directly streamable.

For those titles the archive.org identifier is all we need. One metadata call
per item returns the file list; pick a real MP4 and the title becomes playable
in our own HLS/MP4 engine with no third-party player involved at all.

This is the single highest-leverage change available for "our own player":
it converts tens of thousands of titles from iframe playback to native decode.

Resumable: progress is checkpointed per identifier.

Run:
    python backfill_archive_playback.py --limit 500      # try a batch
    python backfill_archive_playback.py                  # all of them
    python backfill_archive_playback.py --dry-run
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
from urllib.error import HTTPError, URLError

HERE = Path(__file__).parent
DB = HERE / "catalog.db"
STATE = HERE / ".archive_backfill_state.json"

PREFERRED_FORMATS = ["h.264", "MPEG4", "512Kb MPEG4", "HiRes MPEG4", "MPEG2", "Ogg Video", "WebM", "M4V"]
EXCLUDE_FORMATS = ["thumb", "spectrogram", "metadata", "text", "gif", "png", "jpg", "zip", "xml", "json"]
CONCURRENCY = 6
TIMEOUT = 25


def load_state() -> dict:
    if STATE.is_file():
        try:
            return json.loads(STATE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"done": [], "resolved": 0, "no_media": 0, "errors": 0}


def save_state(st: dict) -> None:
    STATE.write_text(json.dumps(st), encoding="utf-8")


def fetch_metadata(identifier: str):
    url = f"https://archive.org/metadata/{quote(identifier)}"
    req = Request(url, headers={"User-Agent": "ShadowStream-Backfill/1.0"})
    with urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read().decode("utf-8", errors="replace"))


def pick_playable(meta: dict, identifier: str):
    """Choose the best directly-decodable file for this item."""
    files = meta.get("files") or []
    best = None
    best_rank = 10 ** 9
    best_size = 0
    for f in files:
        name = f.get("name")
        fmt = (f.get("format") or "").strip()
        if not name or not fmt:
            continue
        low = fmt.lower()
        if any(x in low for x in EXCLUDE_FORMATS):
            continue
        # Only formats a browser can decode natively, or that we transcode-free
        # HLS handles. Reject Ogg/Theora and unknown containers.
        if not any(pf.lower() in low for pf in ("mpeg4", "h.264", "512kb", "hires mpeg4", "webm", "m4v", "mp4")):
            continue
        low_name = name.lower()
        if low_name.endswith((".mp4", ".m4v", ".webm")):
            rank = PREFERRED_FORMATS.index(fmt) if fmt in PREFERRED_FORMATS else len(PREFERRED_FORMATS)
            try:
                size = int(f.get("size") or 0)
            except (TypeError, ValueError):
                size = 0
            # Prefer a browser-decodable container, then a smaller copy so the
            # player starts faster on poor connections.
            key = (rank, size if size else 10 ** 12)
            if key < (best_rank, best_size or 10 ** 12):
                best_rank, best_size, best = rank, size, name
    if not best:
        return None
    return f"https://archive.org/download/{quote(identifier)}/{quote(best)}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    conn = sqlite3.connect(str(DB), timeout=60)
    conn.execute("PRAGMA journal_mode = WAL")
    cur = conn.cursor()

    cur.execute("SELECT id FROM sources WHERE slug = 'archive_org'")
    row = cur.fetchone()
    if not row:
        print("FATAL: no archive_org source row")
        sys.exit(2)
    sid = row[0]

    state = load_state()
    done = set(state.get("done", []))

    cur.execute(
        "SELECT id, external_id FROM availability "
        "WHERE source_id = ? AND kind = 'embed' AND external_id IS NOT NULL AND external_id != ''",
        (sid,),
    )
    rows = cur.fetchall()
    pending = [(rid, ext) for rid, ext in rows if ext not in done]
    print(f"{len(rows)} archive.org rows total; {len(done)} already attempted; {len(pending)} pending")
    if args.dry_run:
        for rid, ext in pending[:5]:
            print(f"  would resolve {ext}")
        return
    if args.limit:
        pending = pending[: args.limit]

    started = time.time()
    resolved = state.get("resolved", 0)
    no_media = state.get("no_media", 0)
    errors = state.get("errors", 0)

    def work(job):
        rid, ext = job
        try:
            meta = fetch_metadata(ext)
        except HTTPError as e:
            return rid, ext, None, f"HTTP {e.code}"
        except URLError:
            return rid, ext, None, "network"
        except Exception:
            return rid, ext, None, "error"
        return rid, ext, pick_playable(meta, ext), None

    with ThreadPoolExecutor(max_workers=CONCURRENCY) as ex:
        futs = [ex.submit(work, j) for j in pending]
        for i, fut in enumerate(as_completed(futs), 1):
            rid, ext, url, err = fut.result()
            done.add(ext)
            if url:
                cur.execute(
                    "UPDATE availability SET kind='playback', playback_url=?, status='available', "
                    "is_legal_verified=1, last_success_at=? WHERE id=?",
                    (url, int(time.time()), rid),
                )
                resolved += 1
            elif err:
                errors += 1
            else:
                no_media += 1

            if i % 25 == 0:
                conn.commit()
                state.update({"done": sorted(done), "resolved": resolved,
                              "no_media": no_media, "errors": errors})
                save_state(state)
                rate = i / max(time.time() - started, 1)
                print(f"  {i}/{len(pending)}  resolved={resolved}  no_media={no_media}  "
                      f"errors={errors}  ({rate:.1f}/s)", flush=True)

    conn.commit()
    state.update({"done": sorted(done), "resolved": resolved, "no_media": no_media, "errors": errors})
    save_state(state)

    total_playable = cur.execute(
        "SELECT COUNT(*) FROM availability a JOIN sources s ON s.id=a.source_id "
        "WHERE s.slug='archive_org' AND a.kind='playback' AND a.playback_url IS NOT NULL AND a.playback_url!=''"
    ).fetchone()[0]
    print(f"\nthis run: resolved {resolved}, no media {no_media}, errors {errors}")
    print(f"archive.org titles now natively playable: {total_playable:,}")
    print("run: python export_worker_snapshot.py && python upload_worker_export_to_r2.py")
    conn.close()


if __name__ == "__main__":
    main()
