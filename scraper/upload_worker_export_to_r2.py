"""
upload_worker_export_to_r2.py — publish the main catalogue snapshots to R2.

Same command shape the repo already used (sync_snapshot_to_r2.py), but with a
per-file checkpoint so a killed run resumes instead of starting over. R2 puts
on this network occasionally take minutes, and the dataset is ~400 MB across
~500 objects, so losing an uncheckpointed run is expensive.

Resumable via a state file next to the export.

Run:
    python upload_worker_export_to_r2.py                 # upload everything
    python upload_worker_export_to_r2.py --dry-run
    python upload_worker_export_to_r2.py --workers 3
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

SRC = Path(r"G:\streaming app\scraper\worker_export")
BUCKET = "streamapp-catalog"
WORKER_DIR = r"G:\streaming app\downloads\streamapp-worker"
STATE = Path(r"G:\streaming app\scraper\worker_export\.r2_uploaded.json")

CONTENT_TYPES = {
    ".json": "application/json",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".svg": "image/svg+xml",
    ".webp": "image/webp",
}


def load_state() -> set:
    if STATE.is_file():
        try:
            return set(json.loads(STATE.read_text(encoding="utf-8")))
        except Exception:
            return set()
    return set()


def save_state(done: set) -> None:
    STATE.write_text(json.dumps(sorted(done)), encoding="utf-8")


def upload(key: str, path: Path, attempts: int = 4):
    ct = CONTENT_TYPES.get(path.suffix.lower(), "application/octet-stream")
    cmd = [
        "npx", "wrangler", "r2", "object", "put", f"{BUCKET}/{key}",
        "--file", str(path),
        "--content-type", ct,
        "--remote", "-y",
    ]
    for i in range(attempts):
        res = subprocess.run(
            cmd, cwd=WORKER_DIR, shell=True, capture_output=True, text=True,
            encoding="utf-8", errors="replace",
        )
        if res.returncode == 0:
            return key, True, ""
        lines = (res.stderr or res.stdout or "").strip().splitlines()
        last = (lines[-1] if lines else "unknown error")[:140]
        time.sleep(2 * (i + 1))
    return key, False, last


def collect():
    jobs = []
    for p in sorted(SRC.rglob("*")):
        if not p.is_file():
            continue
        if p.name.startswith("."):
            continue
        jobs.append((p.relative_to(SRC).as_posix(), p))
    return jobs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    all_jobs = collect()
    done = load_state()
    jobs = [j for j in all_jobs if j[0] not in done]

    total = sum(p.stat().st_size for _k, p in all_jobs)
    pending = sum(p.stat().st_size for _k, p in jobs)
    print(f"{len(all_jobs)} objects, {total/1024/1024:.1f} MB total")
    print(f"{len(done)} done; {len(jobs)} pending, {pending/1024/1024:.1f} MB")
    if args.dry_run:
        for k, p in jobs[:10]:
            print(f"  {k:<52} {p.stat().st_size/1024/1024:>7.2f} MB")
        return
    if args.limit:
        jobs = jobs[: args.limit]

    started = time.time()
    ok = fail = 0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = [ex.submit(upload, k, p) for k, p in jobs]
        for fut in as_completed(futs):
            key, good, detail = fut.result()
            if good:
                ok += 1
                done.add(key)
                save_state(done)
            else:
                fail += 1
                print(f"  [FAIL] {key}: {detail}", file=sys.stderr, flush=True)
            if (ok + fail) % 25 == 0:
                rate = (ok + fail) / max(time.time() - started, 1)
                print(f"  {ok + fail}/{len(jobs)} ({rate:.1f}/s, {fail} failed)", flush=True)

    save_state(done)
    remaining = len([j for j in all_jobs if j[0] not in done])
    print(f"this run: {ok} ok, {fail} failed; done {len(done)}/{len(all_jobs)}; remaining {remaining}")
    sys.exit(2 if remaining else 0)


if __name__ == "__main__":
    main()
