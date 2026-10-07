"""
Upload desktop v2.4.1 release artifacts to R2 streamapp-releases bucket.
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
VERIFY = "https://streamapp-catalog.muhd-faisal-work.workers.dev/downloads"
DIST = Path(r"G:\streaming app\packaging\windows\app\dist-v241")

JOBS = [
    (
        "ShadowStream-Setup-x64.exe",
        DIST / "ShadowStream-Setup-x64.exe",
        "application/vnd.microsoft.portable-executable",
    ),
    (
        "ShadowStream-Setup-x64.exe.blockmap",
        DIST / "ShadowStream-Setup-x64.exe.blockmap",
        "application/octet-stream",
    ),
    (
        "latest.yml",
        DIST / "latest.yml",
        "text/yaml",
    ),
]


def published_map() -> dict[str, int]:
    try:
        req = urllib.request.Request(VERIFY, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read().decode())
            return {o["key"]: o["size"] for o in data}
    except Exception as e:
        print(f"Error checking published: {e}")
        return {}


def put(key: str, path: Path, ctype: str) -> bool:
    cmd = [
        str(WRANGLER), "r2", "object", "put", f"{BUCKET}/{key}",
        "--file", str(path), "--content-type", ctype, "--remote", "-y",
    ]
    try:
        res = subprocess.run(cmd, cwd=WORKER, shell=True, capture_output=True,
                             text=True, encoding="utf-8", errors="replace", timeout=300)
        if res.returncode != 0:
            print(f"    wrangler error ({res.returncode}): {res.stderr.strip()[:200]}")
        return res.returncode == 0
    except subprocess.TimeoutExpired:
        print("    wrangler timed out after 300s")
        return False
    except Exception as e:
        print(f"    wrangler exception: {e}")
        return False


def main() -> int:
    pub = published_map()
    for key, path, ctype in JOBS:
        if not path.is_file():
            print(f"  {key}: ERROR - source missing: {path}")
            return 1
        target_size = path.stat().st_size
        if pub.get(key) == target_size and key != "latest.yml":
            print(f"  {key}: already matches R2 size ({target_size} bytes)")
            continue

        print(f"  {key}: uploading ({target_size:,} bytes)...")
        delay = 10
        for attempt in range(1, 10):
            ok = put(key, path, ctype)
            # verify
            curr = published_map()
            if key == "latest.yml" or curr.get(key) == target_size:
                print(f"  {key}: UPLOADED and verified on attempt {attempt}")
                break
            print(f"  {key}: attempt {attempt} failed or size mismatch (got {curr.get(key)}); retrying in {delay}s...")
            time.sleep(delay)
            delay = min(delay + 15, 60)
        else:
            print(f"  {key}: FAILED after 10 attempts")
            return 1

    print("\nAll artifacts published successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
