"""Retry-release uploads to the R2 releases bucket.

The Windows rebuilds are done and verified, but the network on this machine
degrades badly for long stretches: `wrangler r2 object put` on a 37 MB binary
fails with a bare `TypeError: fetch failed` after ~64s, while a few-hundred-byte
probe file succeeds immediately. That is a transport timeout, not a
permissions or config problem -- both buckets accept small writes and the
catalogue uploader pushed 620 MB shards earlier the same day.

So this driver just keeps retrying with backoff and stops as soon as each
object lands. It verifies via the public /downloads endpoint rather than
trusting wrangler's exit code, because wrangler has already reported
"Upload complete" for writes that went to a LOCAL instance.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

WORKER = Path(r"G:\streaming app\downloads\streamapp-worker")
WRANGLER = WORKER / "node_modules" / ".bin" / "wrangler.cmd"
BUCKET = "streamapp-releases"
VERIFY = "https://streamapp-catalog.muhd-faisal-work.workers.dev/api/v1/downloads"

JOBS = [
    (
        "ShadowStream-win-x64.zip",
        Path(r"G:\streaming app\packaging\windows\ShadowStream-win-x64.zip"),
        "application/zip",
    ),
]


def published() -> set[str]:
    try:
        req = urllib.request.Request(VERIFY, headers={"User-Agent": "ShadowStream/1.0"})
        with urllib.request.urlopen(req, timeout=60) as r:
            return {o["key"] for o in json.loads(r.read().decode())}
    except Exception:
        return set()


def put(key: str, path: Path, ctype: str) -> bool:
    cmd = [
        str(WRANGLER), "r2", "object", "put", f"{BUCKET}/{key}",
        "--file", str(path), "--content-type", ctype, "--remote", "-y",
    ]
    try:
        res = subprocess.run(cmd, cwd=WORKER, shell=True, capture_output=True,
                             text=True, encoding="utf-8", errors="replace", timeout=900)
        return res.returncode == 0
    except subprocess.TimeoutExpired:
        return False
    except Exception:
        return False


def main() -> int:
    have = published()
    pending = [(k, p, c) for (k, p, c) in JOBS if k not in have]
    if not pending:
        print("nothing to do - all objects already published")
        return 0
    print(f"pending: {[k for k, _, _ in pending]}")

    for key, path, ctype in pending:
        if not path.is_file():
            print(f"  {key}: SKIP - source missing ({path})")
            continue
        delay = 60
        for attempt in range(1, 16):
            ok = put(key, path, ctype)
            if ok and key in published():
                print(f"  {key}: UPLOADED and verified on attempt {attempt}")
                break
            if ok:
                print(f"  {key}: attempt {attempt} reported ok but not visible; retrying")
            else:
                print(f"  {key}: attempt {attempt} failed; waiting {delay}s", flush=True)
            time.sleep(delay)
            delay = min(delay + 30, 300)
        else:
            print(f"  {key}: GAVE UP after 15 attempts", flush=True)

    print("final published set:")
    for k in sorted(published()):
        print("   ", k)
    return 0


if __name__ == "__main__":
    sys.exit(main())

