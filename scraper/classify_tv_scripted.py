"""
classify_tv_scripted.py — decide which TV titles are scripted series.

Why this exists
---------------
The TV listing was dominated by talk shows and soaps, not scripted drama. Two
"obvious" filters were both wrong, verified against the data:

  * "has >= 1 season"  -> The Tonight Show has 32 seasons, Watch What Happens
    Live has 24, while Game of Thrones, Breaking Bad, Stranger Things and Dark
    all have 0. It removes the shows people actually want.
  * "exclude news/reality/talk/documentary genres" -> Game of Thrones,
    Breaking Bad, Stranger Things and Dark have NO genre rows in our database
    at all, so the filter cannot see them.

So we ask TMDB directly. /tv/{id} returns authoritative `genres`, `status`,
`number_of_seasons` and `number_of_episodes`, and TMDB genre 10767 is
explicitly "Talk Show".

Nothing is deleted. This writes a new `is_scripted` column on `titles`
(0 = not yet classified, 1 = scripted series, -1 = non-scripted).

Run:
    python classify_tv_scripted.py --limit 200
    python classify_tv_scripted.py
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sqlite3
import sys
import time
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

HERE = Path(__file__).parent
DB = HERE / "catalog.db"
STATE = HERE / ".scripted_state.json"
OUT = HERE / ".scripted_results.jsonl"
BASE = "https://api.themoviedb.org/3"
UA = "ShadowStreamClassifier/1.0"
CONCURRENCY = 6
TIMEOUT = 25

# TMDB genre ids that mark a show as non-scripted / not fictional drama.
NON_SCRIPTED_GENRES = {
    10767: "Talk Show",
    10763: "News",
    10764: "Reality",
    10768: "Documentary",
    10681: "Kids' TV",     # largely magazine-format, not scripted drama
    10751: "Family",       # overwhelmingly animated features, handled elsewhere
}

# A show is treated as scripted if it carries at least one of these.
SCRIPTED_GENRES = {
    18: "Drama", 35: "Comedy", 80: "Crime", 9648: "Mystery", 10759: "Action & Adventure",
    10765: "Sci-Fi & Fantasy", 37: "Western", 14: "Fantasy", 28: "Action", 12: "Adventure",
    16: "Animation", 10752: "War & Politics", 53: "Thriller", 10749: "Family",
    10755: "Romance", 101: "Documentary", 22: "Drama",
}


def env_values() -> dict:
    vals = {}
    p = HERE / ".env"
    if p.is_file():
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
            s = line.strip()
            if s and not s.startswith("#") and "=" in s:
                k, v = s.split("=", 1)
                vals[k.strip()] = v.strip()
    return vals


ENV = env_values()
API_KEY = ENV.get("TMDB_API_KEY", "")


def fetch(tmdb_id: int):
    url = f"{BASE}/tv/{tmdb_id}?api_key={quote(API_KEY)}&language=en-US"
    req = Request(url, headers={"User-Agent": UA})
    try:
        with urlopen(req, timeout=TIMEOUT) as r:
            return json.loads(r.read().decode("utf-8", errors="replace"))
    except HTTPError as e:
        return None if e.code == 404 else None
    except Exception:
        return None


def classify(d: dict) -> int:
    """1 = scripted series, -1 = non-scripted. TMDB genres are authoritative."""
    if not d:
        return -1
    gids = {g.get("id") for g in (d.get("genres") or []) if g.get("id")}
    if not gids:
        # No genre information at all: fall back to episodic structure.
        # A show with multiple seasons and many episodes is almost certainly
        # scripted; a one-off with a single episode is not.
        seasons = d.get("number_of_seasons") or 0
        eps = d.get("number_of_episodes") or 0
        if seasons >= 2 and eps >= 6:
            return 1
        return -1
    if gids & set(NON_SCRIPTED_GENRES) and not (gids & set(SCRIPTED_GENRES)):
        return -1
    if gids & set(SCRIPTED_GENRES):
        return 1
    return -1


def load_state() -> dict:
    if STATE.is_file():
        try:
            return json.loads(STATE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"done": [], "scripted": 0, "non_scripted": 0, "unknown": 0}


def save_state(st: dict) -> None:
    STATE.write_text(json.dumps(st), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true",
                    help="merge staged .scripted_results.jsonl into titles.is_scripted")
    args = ap.parse_args()

    if args.apply:
        if not OUT.is_file():
            print("FATAL: no staged results to apply")
            sys.exit(2)
        conn = sqlite3.connect(str(DB), timeout=120)
        n = 0
        for line in OUT.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            tid, v = line.split("\t")[:2]
            conn.execute("UPDATE titles SET is_scripted = ? WHERE id = ?", (int(v), int(tid)))
            n += 1
        conn.commit()
        sc = conn.execute("SELECT COUNT(*) FROM titles WHERE type='tv' AND is_scripted=1").fetchone()[0]
        ns = conn.execute("SELECT COUNT(*) FROM titles WHERE type='tv' AND is_scripted=-1").fetchone()[0]
        print(f"applied {n:,} classifications -> scripted={sc:,} non-scripted={ns:,}")
        conn.close()
        return

    if not API_KEY:
        print("FATAL: TMDB_API_KEY not set in scraper/.env")
        sys.exit(3)

    conn = sqlite3.connect(str(DB), timeout=60)
    conn.execute("PRAGMA journal_mode = WAL")
    cur = conn.cursor()

    # Additive: a new column, defaulting to 0 (unclassified).
    cols = {r[1] for r in cur.execute("PRAGMA table_info(titles)")}
    if "is_scripted" not in cols:
        cur.execute("ALTER TABLE titles ADD COLUMN is_scripted INTEGER NOT NULL DEFAULT 0")
        conn.commit()
        print("added titles.is_scripted (0 = unclassified)")

    rows = cur.execute(
        "SELECT id, tmdb_id FROM titles WHERE type='tv' AND tmdb_id IS NOT NULL AND tmdb_id > 0 "
        "ORDER BY popularity DESC, id"
    ).fetchall()
    state = load_state()
    done = set(state.get("done", []))
    pending = [(i, t) for i, t in rows if str(i) not in done]

    print(f"tv titles with a tmdb_id : {len(rows):,}")
    print(f"already classified      : {len(done):,}")
    print(f"pending                 : {len(pending):,}")

    if args.dry_run:
        print("  sample:", pending[:5])
        return
    if args.limit:
        pending = pending[: args.limit]

    scripted = state.get("scripted", 0)
    non_scripted = state.get("non_scripted", 0)
    started = time.time()

    from concurrent.futures import ThreadPoolExecutor

    def lookup(tmdb_id):
        # network only — no database handle crosses the thread boundary
        return classify(fetch(tmdb_id))

    with ThreadPoolExecutor(max_workers=CONCURRENCY) as ex:
        for i, v in enumerate(ex.map(lambda j: lookup(j[1]), pending), 1):
            tid = pending[i - 1][0]
            done.add(str(tid))
            if v == 1:
                scripted += 1
            else:
                non_scripted += 1
            with open(OUT, "a", encoding="utf-8") as fh:
                fh.write(f"{tid}\t{v}\n")
            if i % 250 == 0:
                conn.commit()
                state.update({"done": sorted(done), "scripted": scripted,
                              "non_scripted": non_scripted})
                save_state(state)
                rate = i / max(time.time() - started, 1)
                print(f"  {i}/{len(pending)}  scripted={scripted}  non-scripted={non_scripted}  ({rate:.1f}/s)",
                      flush=True)

    conn.commit()
    state.update({"done": sorted(done), "scripted": scripted, "non_scripted": non_scripted})
    save_state(state)

    tot = conn.execute("SELECT COUNT(*) FROM titles WHERE type='tv'").fetchone()[0]
    sc = conn.execute("SELECT COUNT(*) FROM titles WHERE type='tv' AND is_scripted=1").fetchone()[0]
    ns = conn.execute("SELECT COUNT(*) FROM titles WHERE type='tv' AND is_scripted=-1").fetchone()[0]
    print(f"\nthis run: scripted={scripted}  non-scripted={non_scripted}")
    print(f"TV total {tot:,}  ->  scripted {sc:,}  non-scripted {ns:,}")
    conn.close()


if __name__ == "__main__":
    main()
