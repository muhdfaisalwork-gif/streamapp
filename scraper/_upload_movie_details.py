import os
import glob
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

movie_dir = Path(r"G:\streaming app\scraper\worker_export\titles-by-type\movie")
files = sorted(movie_dir.glob("detail-*.json"))
print(f"Total movie detail files on disk: {len(files)}")

# Check each file or upload
def upload_file(p):
    key = f"titles-by-type/movie/{p.name}"
    cmd = [
        "npx", "wrangler", "r2", "object", "put", f"streamapp-catalog/{key}",
        "--file", str(p),
        "--content-type", "application/json",
        "--remote",
    ]
    res = subprocess.run(cmd, cwd=r"G:\streaming app\downloads\streamapp-worker", shell=True, capture_output=True, text=True)
    if res.returncode == 0:
        return (p.name, True, "")
    else:
        return (p.name, False, res.stderr or res.stdout)

# We can run with 4 workers
print("Uploading movie detail shards with --remote...")
with ThreadPoolExecutor(max_workers=4) as executor:
    futures = {executor.submit(upload_file, p): p for p in files}
    done = 0
    for f in as_completed(futures):
        name, success, err = f.result()
        done += 1
        if success:
            print(f"[{done}/{len(files)}] Uploaded {name}")
        else:
            print(f"[{done}/{len(files)}] FAILED {name}: {err[:80]}")
