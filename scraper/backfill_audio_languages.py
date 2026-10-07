"""Backfill `title_audio_languages` from TMDB's spoken_languages.

TMDB returns each title's available dubs on `/tv/{id}`. The current
`title_audio_languages` table only has 109 multi-audio titles — this
backfills everything episodic that has a tmdb_id, so the player can offer
a real audio track picker.

Checkpointed by title_id, so a re-run resumes rather than re-fetches.
Skips titles already in the table by default; --force re-writes them.
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(r"G:\streaming app\scraper")
DB = HERE / "catalog.db"
ENV = HERE / ".env"
STATE = HERE / ".audio_lang_state.json"

TMDB = "https://api.themoviedb.org/3"
TIMEOUT = 12
# TMDB allows ~50 req/s; stay well under to avoid getting throttled.
RATE_SLEEP = 0.10  # 10 req/s


def load_key() -> str:
    env = ENV.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"\s*TMDB_API_KEY\s*=\s*(.+?)\s*$", env, re.M)
    if not m:
        raise SystemExit("TMDB_API_KEY missing in .env")
    return m.group(1).strip().strip('"').strip("'")


def load_state() -> dict:
    if STATE.is_file():
        try:
            return json.loads(STATE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"done": [], "written": 0, "last_id": 0}


def save_state(s: dict) -> None:
    tmp = STATE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(s), encoding="utf-8")
    tmp.replace(STATE)


def fetch_tv(tmdb_id: int, key: str) -> list[str] | None:
    """Return list of ISO-639-1 language codes, or None on transient failure."""
    url = f"{TMDB}/tv/{int(tmdb_id)}?api_key={key}"
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT) as r:
            d = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return []  # the TMDB id no longer exists; not a transient error
        if e.code in (429, 500, 502, 503, 504):
            return None  # retry
        return []
    except Exception:
        return None
    out = []
    for sl in d.get("spoken_languages", []):
        code = (sl.get("iso_639_1") or "").lower().strip()
        if code and len(code) == 2:
            out.append(code)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="only process N titles (0 = all)")
    ap.add_argument("--min-popularity", type=float, default=0.0,
                    help="skip titles with popularity below this")
    ap.add_argument("--skip-talk-shows", action="store_true",
                    help="exclude talk/variety franchises and non-scripted genre titles")
    ap.add_argument("--force", action="store_true",
                    help="re-write rows even if title is already in the table")
    args = ap.parse_args()

    key = load_key()
    conn = sqlite3.connect(str(DB), timeout=900)
    conn.execute("PRAGMA journal_mode = WAL")
    cur = conn.cursor()

    # language_id lookup
    lang_id = {code: lid for lid, code in cur.execute("SELECT id, code FROM languages")}

    # candidate titles
    if args.force:
        cur.execute("""SELECT id, tmdb_id FROM titles
                       WHERE tmdb_id IS NOT NULL AND tmdb_id > 0
                         AND type IN ('movie','tv','anime','short_drama')""")
    else:
        cur.execute("""SELECT t.id, t.tmdb_id FROM titles t
                       WHERE t.tmdb_id IS NOT NULL AND t.tmdb_id > 0
                         AND t.type IN ('movie','tv','anime','short_drama')
                         AND t.id NOT IN (SELECT title_id FROM title_audio_languages)""")
    todo = [(t, m) for t, m in cur.fetchall() if m]

    # Talk/variety franchise + non-scripted-genre exclusion. The picker is
    # useless on Tonight Show / Watch What Happens Live / Love Island etc —
    # they all carry the same single en dub regardless of TMDB's spoken_languages
    # payload. Excluding them up front is cheap and makes the picker meaningful
    # on real movies and drama.
    if args.skip_talk_shows:
        from classify_scripted import NON_SCRIPTED_GENRES, is_talk_show
        excl = ",".join("?" for _ in NON_SCRIPTED_GENRES)
        # SQLite's default variable cap is 999; chunked lookup keeps us under it
        # even when todo has 50k+ entries. The two passes can each take ~50
        # round trips, total <2 s on the WAL catalog.
        non_scripted_ids = set()
        CHUNK = 500
        ids_only = [t for t, _ in todo]
        for i in range(0, len(ids_only), CHUNK):
            chunk = ids_only[i:i + CHUNK]
            ph = ",".join("?" for _ in chunk)
            cur.execute(f"""SELECT DISTINCT t.id FROM titles t
                            JOIN title_genres tg ON tg.title_id = t.id
                            JOIN genres g ON g.id = tg.genre_id
                            WHERE t.id IN ({ph}) AND g.slug IN ({excl})""",
                        chunk + list(NON_SCRIPTED_GENRES))
            non_scripted_ids.update(row[0] for row in cur.fetchall())
        id_to_title = {}
        for i in range(0, len(ids_only), CHUNK):
            chunk = ids_only[i:i + CHUNK]
            ph = ",".join("?" for _ in chunk)
            cur.execute(f"SELECT id, title FROM titles WHERE id IN ({ph})", chunk)
            id_to_title.update(cur.fetchall())
        before = len(todo)
        todo = [(t, m) for t, m in todo
                if t not in non_scripted_ids and not is_talk_show(id_to_title.get(t, ""))]
        print(f"talk-show filter dropped {before - len(todo):,} of {before:,}")

    # Filter by popularity: skip long tail. The full 54k set has a 1.5-hour fetch
    # cost; the top N (default 10k) covers all popular and most second-tier titles
    # in a few minutes. Override with --min-popularity to tune.
    if args.min_popularity > 0:
        pop = {}
        CHUNK = 500
        ids_only = [t for t, _ in todo]
        for i in range(0, len(ids_only), CHUNK):
            chunk = ids_only[i:i + CHUNK]
            ph = ",".join("?" for _ in chunk)
            cur.execute(f"SELECT t.id, t.popularity FROM titles t WHERE t.id IN ({ph})", chunk)
            pop.update(cur.fetchall())
        todo = [(t, m) for t, m in todo if pop.get(t, 0) >= args.min_popularity]
        print(f"popularity>={args.min_popularity} kept {len(todo):,} of {len(pop):,}")
    if args.limit:
        todo = todo[: args.limit]
    # Sort by popularity descending so the most-visible titles fill first.
    cur.execute(f"""SELECT t.id, t.popularity FROM titles t
                     WHERE t.id IN ({",".join("?" * len(todo))})""",
                 [t for t, _ in todo])
    pop = dict(cur.fetchall())
    todo.sort(key=lambda x: pop.get(x[0], 0), reverse=True)

    state = load_state()
    done = set(state["done"])
    todo = [(t, m) for t, m in todo if t not in done]
    print(f"candidates: {len(todo)}  already done: {len(done)}  limit: {args.limit}")
    if not todo:
        print("nothing to do")
        return 0

    written = state.get("written", 0)
    started = time.time()

    # Worker pool: each thread holds its own DB connection via the existing
    # conn. The rate limit is global to our IP, not per-thread, so a single
    # mutex + 0.1s floor caps at ~10 req/s with up to 8 workers.
    from concurrent.futures import ThreadPoolExecutor, as_completed
    THREADS = 8
    RATE_LOCK = threading.Lock()
    RATE_LAST = [0.0]

    def rate_gate():
        with RATE_LOCK:
            # 0.04s global floor: with 8 workers and the i/o overlap from concurrent
            # fetches this gives ~25 req/s steady, which is right at TMDB's
            # per-IP limit. If we hit 429s, the catch above backs off.
            wait = 0.04 - (time.time() - RATE_LAST[0])
            if wait > 0:
                time.sleep(wait)
            RATE_LAST[0] = time.time()

    def work(tid_tmdb):
        tid, tmdb_id = tid_tmdb
        rate_gate()
        return tid, fetch_tv(tmdb_id, key)

    todo = [(t, m) for t, m in todo if t not in done]
    with ThreadPoolExecutor(max_workers=THREADS) as ex:
        completed_iter = 0
        for fut in as_completed([ex.submit(work, x) for x in todo]):
            completed_iter += 1
            try:
                tid, codes = fut.result()
            except Exception as e:
                print(f"  worker exc: {e}")
                continue
            if codes is None:
                continue  # transient; will be re-fetched on next run
            if codes:
                try:
                    cur.execute("BEGIN IMMEDIATE")
                    for code in codes:
                        lid = lang_id.get(code)
                        if lid is None:
                            cur.execute("INSERT OR IGNORE INTO languages (code, name) VALUES (?, ?)",
                                        (code, code.upper()))
                            lid = cur.execute("SELECT id FROM languages WHERE code=?", (code,)).fetchone()[0]
                            lang_id[code] = lid
                        cur.execute("INSERT OR IGNORE INTO title_audio_languages (title_id, language_id) VALUES (?, ?)",
                                    (tid, lid))
                    conn.commit()
                    written += len(codes)
                except Exception as e:
                    print(f"  db err id={tid}: {e}")
            done.add(tid)
            if completed_iter % 200 == 0 or completed_iter == len(todo):
                state["done"] = sorted(done)
                state["written"] = written
                save_state(state)
                rate = completed_iter / max(time.time() - started, 0.1)
                eta = (len(todo) - completed_iter) / max(rate, 0.01)
                print(f"  {completed_iter}/{len(todo)}  written={written}  {rate:.1f}/s  eta {eta/60:.0f} min")

    # final save + report
    state["done"] = sorted(done)
    state["written"] = written
    save_state(state)
    print(f"\nfinal: processed {len(todo)}  written {written}  in {(time.time()-started)/60:.1f} min")
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
