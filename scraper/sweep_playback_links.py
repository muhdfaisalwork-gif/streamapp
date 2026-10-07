"""Link-rot sweeper for the playable catalogue.

The 23k `kind='playback'` rows point at archive.org (and a couple at Google's
retired gtv-videos-bucket). archive.org moves files around, so a URL that
resolved at ingest can 404 months later and the title then shows as playable
but the player errors out. This walks the set, HEADs each URL, and records the
outcome on the row itself.

Writes, for each row:
    status           available | unavailable
    last_checked_at  unix ts of this check
    last_success_at  unix ts of the last 200

A 404 is treated as permanent rot and flips the row to unavailable. 503 and
network errors are treated as TRANSIENT and change nothing except the checked
timestamp — archive.org rate-limits and returns 503 under load, and flipping
rows unavailable on a transient blip would quietly delete playable titles from
the catalogue.

Checkpoints by row id, so a re-run resumes instead of re-fetching everything.

Run:
    python sweep_playback_links.py                 # full sweep
    python sweep_playback_links.py --limit 500     # quick sample
    python sweep_playback_links.py --workers 8
    python sweep_playback_links.py --reset         # ignore checkpoint
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).parent
DB = HERE / "catalog.db"
STATE = HERE / ".playback_sweep_state.json"

UA = "Mozilla/5.0 (compatible; ShadowStreamLinkCheck/1.0)"
TIMEOUT = 12
RETRIES = 1  # only for transient failures

# archive.org is a free volunteer-run service and it rate-limits by IP — hard.
# During a throttle window it stops answering entirely, and a 23k sweep then
# produces nothing but transient verdicts, which is worse than not running at
# all: it cannot tell real link rot from throttling. If more than this fraction
# of the first checks comes back transient we stop immediately rather than
# grinding — and grinding is what gets the IP blocked in the first place.
#
# ABORT_AFTER is deliberately tiny. Each check can burn 2 x TIMEOUT, so a large
# value means the breaker fires minutes after the host is already refusing us.
ABORT_TRANSIENT_RATIO = 0.5
ABORT_AFTER = 12


def load_state() -> dict:
    if STATE.is_file():
        try:
            return json.loads(STATE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"checked": [], "dead": 0, "alive": 0, "transient": 0}


def save_state(st: dict) -> None:
    # Write-then-rename so an interrupted save cannot corrupt the checkpoint.
    tmp = STATE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(st), encoding="utf-8")
    tmp.replace(STATE)


def head(url: str) -> tuple[str, int | None]:
    """Return (verdict, status_code). verdict is alive|dead|transient."""
    last_code = None
    for attempt in range(RETRIES + 1):
        try:
            req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                if r.status == 200:
                    return "alive", r.status
                # 2xx that isn't 200 is fine; anything else is a judgement call
                if 200 <= r.status < 300:
                    return "alive", r.status
                last_code = r.status
        except urllib.error.HTTPError as e:
            last_code = e.code
            if e.code in (404, 410):
                return "dead", e.code
            # 403 on the retired Google bucket is permanent, not transient.
            if e.code in (401, 403) and "googleapis" in url:
                return "dead", e.code
            if e.code not in (429, 500, 502, 503, 504):
                return "transient", e.code
        except Exception:
            pass  # timeout / DNS / connection reset -> transient
        if attempt < RETRIES:
            time.sleep(1.5 * (attempt + 1))
    return "transient", last_code


_print_lock = threading.Lock()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="only check N rows (0 = all)")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--reset", action="store_true", help="ignore the checkpoint")
    args = ap.parse_args()

    st = {"checked": [], "dead": 0, "alive": 0, "transient": 0} if args.reset else load_state()
    done = set(st["checked"])

    conn = sqlite3.connect(str(DB), timeout=900)
    conn.execute("PRAGMA journal_mode = WAL")
    rows = conn.execute(
        "SELECT id, playback_url FROM availability "
        "WHERE kind='playback' AND playback_url IS NOT NULL AND playback_url != ''"
    ).fetchall()
    conn.close()

    todo = [r for r in rows if r[0] not in done]
    if args.limit:
        todo = todo[: args.limit]

    total = len(todo)
    print(f"playback rows total : {len(rows):,}")
    print(f"already checked     : {len(done):,}")
    print(f"to check this run   : {total:,}  (workers={args.workers})")
    if not total:
        print("nothing to do")
        return 0

    started = time.time()
    now = int(time.time())

    def work(row):
        rid, url = row
        verdict, code = head(url)
        if verdict == "alive":
            return rid, "available", now, now
        if verdict == "dead":
            return rid, "unavailable", now, None
        return rid, None, now, None  # transient: touch only

    def flush(batch):
        """Commit a batch and fold it into the checkpoint. Returns False on
        error. Split out of the loop so the tail is committed too — the first
        version only wrote every 200 rows, so any run smaller than that (every
        --limit test) silently persisted nothing."""
        if not batch:
            return
        conn = sqlite3.connect(str(DB), timeout=900)
        try:
            conn.execute("BEGIN IMMEDIATE")
            conn.executemany(
                "UPDATE availability SET status=?, last_checked_at=?, "
                "last_success_at=COALESCE(?, last_success_at) WHERE id=?",
                [(s, ca, ls, rid) for rid, s, ca, ls in batch if s is not None],
            )
            conn.executemany(
                "UPDATE availability SET last_checked_at=? WHERE id=?",
                [(ca, rid) for rid, s, ca, ls in batch if s is None],
            )
            conn.commit()
        finally:
            conn.close()
        for rid, s, ca, ls in batch:
            st["checked"].append(rid)
            st["alive" if s == "available" else ("dead" if s == "unavailable" else "transient")] += 1
        save_state(st)
        batch.clear()

    aborted = False
    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        for i, out in enumerate(ex.map(work, todo), 1):
            results.append(out)

            if i >= ABORT_AFTER:
                # `seen` must be EVERY check done so far, not just the transient
                # ones. Counting only transients makes the ratio 100% whenever
                # any single check is transient, which aborts a perfectly
                # healthy run on one network blip.
                seen = i
                transient = st["transient"] + sum(1 for _, s, _, _ in results if s is None)
                if transient / seen > ABORT_TRANSIENT_RATIO:
                    aborted = True
                    print(
                        f"\nABORT: {transient}/{seen} checks came back transient "
                        f"(> {int(ABORT_TRANSIENT_RATIO*100)}%). The host is not "
                        f"answering — this is throttling or an outage, not link rot.",
                        flush=True,
                    )
                    break

            if i % 200 == 0 or i == total:
                flush(results)
                rate = i / max(time.time() - started, 1)
                eta = (total - i) / max(rate, 0.01)
                with _print_lock:
                    print(
                        f"  {i}/{total}  alive={st['alive']:,}  dead={st['dead']:,}  "
                        f"transient={st['transient']:,}  ({rate:.1f}/s, eta {eta/60:.0f}m)",
                        flush=True,
                    )

    flush(results)  # always commit the tail

    conn = sqlite3.connect(str(DB), timeout=900)
    av = conn.execute("SELECT status, COUNT(*) FROM availability WHERE kind='playback' GROUP BY status").fetchall()
    conn.close()

    print(f"\nfinal playback status: {dict(av)}")
    print(f"newly marked unavailable: {st['dead']:,}")
    if aborted:
        print("sweep aborted early; re-run later when the host is responding")
    return 2 if aborted else 0


if __name__ == "__main__":
    sys.exit(main())
