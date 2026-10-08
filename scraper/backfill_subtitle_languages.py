#!/usr/bin/env python3
"""Backfill `title_subtitle_languages` from TMDB's translations endpoint.

TMDB returns available translations (subtitles) on `/movie/{id}/translations` 
and `/tv/{id}/translations`. This backfills the subtitle languages table.
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
STATE = HERE / ".subtitle_lang_state.json"

TMDB = "https://api.themoviedb.org/3"
TIMEOUT = 12
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


def fetch_movie_translations(tmdb_id: int, key: str) -> list[str] | None:
    """Return list of ISO-639-1 subtitle language codes for a movie."""
    url = f"{TMDB}/movie/{int(tmdb_id)}/translations?api_key={key}"
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT) as r:
            d = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return []
        if e.code in (429, 500, 502, 503, 504):
            return None
        return []
    except Exception:
        return None
    out = []
    for sl in d.get("translations", []):
        code = (sl.get("iso_639_1") or "").lower().strip()
        if code and len(code) == 2:
            out.append(code)
    return out


def fetch_tv_translations(tmdb_id: int, key: str) -> list[str] | None:
    """Return list of ISO-639-1 subtitle language codes for a TV show."""
    url = f"{TMDB}/tv/{int(tmdb_id)}/translations?api_key={key}"
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT) as r:
            d = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return []
        if e.code in (429, 500, 502, 503, 504):
            return None
        return []
    except Exception:
        return None
    out = []
    for sl in d.get("translations", []):
        code = (sl.get("iso_639_1") or "").lower().strip()
        if code and len(code) == 2:
            out.append(code)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="only process N titles (0 = all)")
    ap.add_argument("--min-popularity", type=float, default=0.0,
                    help="skip titles with popularity below this")
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
        cur.execute("""SELECT id, tmdb_id, type FROM titles
                       WHERE tmdb_id IS NOT NULL AND tmdb_id > 0
                         AND type IN ('movie','tv','anime','short_drama')""")
    else:
        cur.execute("""SELECT t.id, t.tmdb_id, t.type FROM titles t
                       WHERE t.tmdb_id IS NOT NULL AND t.tmdb_id > 0
                         AND t.type IN ('movie','tv','anime','short_drama')
                         AND t.id NOT IN (SELECT title_id FROM title_subtitle_languages)""")
    todo = [(t, m, typ) for t, m, typ in cur.fetchall() if m]

    # Filter by popularity
    if args.min_popularity > 0:
        pop = {}
        CHUNK = 500
        ids_only = [t for t, _, _ in todo]
        for i in range(0, len(ids_only), CHUNK):
            chunk = ids_only[i:i + CHUNK]
            ph = ",".join("?" for _ in chunk)
            cur.execute(f"SELECT t.id, t.popularity FROM titles t WHERE t.id IN ({ph})", chunk)
            pop.update(cur.fetchall())
        todo = [(t, m, typ) for t, m, typ in todo if pop.get(t, 0) >= args.min_popularity]
        print(f"popularity>={args.min_popularity} kept {len(todo):,} of {len(pop):,}")
    if args.limit:
        todo = todo[: args.limit]
    # Sort by popularity descending
    cur.execute(f"""SELECT t.id, t.popularity FROM titles t
                     WHERE t.id IN ({",".join("?" * len(todo))})""",
                [t for t, _, _ in todo])
    pop = dict(cur.fetchall())
    todo.sort(key=lambda x: pop.get(x[0], 0), reverse=True)

    state = load_state()
    done = set(state["done"])
    todo = [(t, m, typ) for t, m, typ in todo if t not in done]
    print(f"candidates: {len(todo)}  already done: {len(done)}  limit: {args.limit}")
    if not todo:
        print("nothing to do")
        return 0

    written = state.get("written", 0)
    started = time.time()

    from concurrent.futures import ThreadPoolExecutor, as_completed
    THREADS = 8
    RATE_LOCK = threading.Lock()
    RATE_LAST = [0.0]

    def rate_gate():
        with RATE_LOCK:
            wait = 0.04 - (time.time() - RATE_LAST[0])
            if wait > 0:
                time.sleep(wait)
            RATE_LAST[0] = time.time()

    def work(tid_tmdb_type):
        tid, tmdb_id, typ = tid_tmdb_type
        rate_gate()
        if typ == 'movie':
            return tid, fetch_movie_translations(tmdb_id, key)
        else:
            return tid, fetch_tv_translations(tmdb_id, key)

    todo = [(t, m, typ) for t, m, typ in todo if t not in done]
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
                        cur.execute("INSERT OR IGNORE INTO title_subtitle_languages (title_id, language_id) VALUES (?, ?)",
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

    state["done"] = sorted(done)
    state["written"] = written
    save_state(state)
    print(f"\nfinal: processed {len(todo)}  written {written}  in {(time.time()-started)/60:.1f} min")
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())