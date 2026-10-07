"""Backfill missing TMDB ids so episodic titles can actually get seasons.

Why this exists
---------------
`ingest_tmdb_episodes.py` fetches seasons by TMDB id. 46 episodic titles never
got one — they came in through a curated anime/short-drama list that filled in
title, year and poster but left tmdb_id NULL. So the fill had no way to reach
them, no amount of re-running it helps, and their detail pages rendered an
empty "EPISODES" block. 13 of the top 40 anime were affected, including
Chainsaw Man, Steins;Gate, Sword Art Online, Vinland Saga and Black Clover.

A wrong id is worse than a missing one: it would attach a completely different
show's seasons to the title. So matching is deliberately strict —
normalised title must match EXACTLY, the year must be within +-1 when we know
it, and the TMDB type must agree with ours (anime/short_drama map onto `tv`).
Anything short of that is reported as a guess and left unset.

Run:
    python backfill_tmdb_ids.py --dry-run     # show what would be written
    python backfill_tmdb_ids.py
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
DB = HERE / "catalog.db"
STATE = HERE / ".tmdb_id_backfill_state.json"

TMDB = "https://api.themoviedb.org/3"
TIMEOUT = 20

# Titles that are unambiguous despite the surrounding text differing, e.g.
# "Your Name. (Anime Film)" vs TMDB's "Your Name.".
NOISE = re.compile(r"\((?:anime\s*film|movie|film|tv|series|ova)\)", re.I)


def load_env_key() -> str | None:
    env = HERE / ".env"
    if not env.is_file():
        return None
    for line in env.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r"\s*TMDB_API_KEY\s*=\s*(.+?)\s*$", line)
        if m:
            return m.group(1).strip().strip('"').strip("'")
    return None


def norm(s: str) -> str:
    """Lowercase, strip accents/punctuation, collapse spaces.

    TMDB and our catalogue spell the same show differently often enough that
    exact-string matching fails ("Re:ZERO -Starting Life-"), so both sides are
    reduced to bare alphanumerics before comparing.
    """
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.lower().replace("&", " and ")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return " ".join(s.split())


def get(path: str, params: dict) -> dict | None:
    url = f"{TMDB}{path}?{urllib.parse.urlencode(params)}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ShadowStream/1.0"})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return None


def candidates_for(title: str, year, key: str) -> list[dict]:
    """Search TMDB for plausible matches.

    Only `tv` is searched. These are episodic titles and decide() rejects any
    movie result outright, so searching /search/movie could never contribute a
    match — and it is pathologically slow from here: a tv query returns in
    ~0.8s while the same query against /search/movie takes ~22s, so the
    "harmless" extra lookup was 95% of the runtime (45 min instead of 70s).
    """
    q = NOISE.sub("", title or "").strip()
    data = get("/search/tv", {"api_key": key, "query": q, "language": "en-US"})
    return [
        {
            "media_type": "tv",
            "tmdb_id": r.get("id"),
            "title": r.get("name") or r.get("title") or "",
            "year": int(r["first_air_date"][:4]) if r.get("first_air_date") else None,
            "popularity": r.get("popularity", 0),
        }
        for r in (data or {}).get("results", [])[:8]
    ]


def decide(ours_title: str, ours_year, ours_type: str, cands: list[dict]):
    """Return (tmdb_id, confidence, note) or (None, reason)."""
    want = norm(ours_title)
    if not want:
        return None, "empty title"

    # Exact normalised title match only.
    exact = [c for c in cands if norm(c["title"]) == want]
    if not exact:
        return None, "no exact title match"
    if len(exact) > 1:
        # Disambiguate on year when we have one.
        if ours_year:
            yr = [c for c in exact if c["year"] and abs(c["year"] - ours_year) <= 1]
            if len(yr) == 1:
                exact = yr
            else:
                return None, f"{len(exact)} exact matches, year did not disambiguate"
        else:
            return None, f"{len(exact)} exact matches, no year to disambiguate"

    best = max(exact, key=lambda c: c["popularity"])

    # Year sanity: only a hard reject if both sides know the year and it is far off.
    if ours_year and best["year"] and abs(best["year"] - ours_year) > 1:
        return None, f"year mismatch ours={ours_year} tmdb={best['year']}"

    # A `tv` row for an episodic title is the only sane match; a movie row
    # would attach a film's "seasons" to a series.
    if ours_type in ("tv", "anime", "short_drama") and best["media_type"] != "tv":
        return None, f"tmdb says {best['media_type']}, ours is {ours_type}"

    return best["tmdb_id"], "exact-title" + ("" if ours_year else " (no year on our row)")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    key = load_env_key()
    if not key:
        print("FATAL: TMDB_API_KEY not found in scraper/.env")
        return 3

    conn = sqlite3.connect(str(DB), timeout=900)
    conn.execute("PRAGMA journal_mode = WAL")
    rows = conn.execute(
        """SELECT id, title, original_title, year, type
             FROM titles
            WHERE (tmdb_id IS NULL OR tmdb_id = 0)
              AND type IN ('tv','anime','short_drama')
              AND id NOT IN (SELECT title_id FROM seasons)
            ORDER BY popularity DESC"""
    ).fetchall()
    print(f"episodic titles with no tmdb_id and no seasons: {len(rows)}\n")

    state = {}
    if STATE.is_file():
        try:
            state = json.loads(STATE.read_text(encoding="utf-8"))
        except Exception:
            state = {}
    done = set(state.get("done", []))

    written, skipped, already = [], [], 0
    for (tid, title, otitle, year, ttype) in rows:
        if tid in done:
            continue
        cands = candidates_for(title, year, key)
        tmdb_id, note = decide(title, year, ttype, cands)
        if tmdb_id is None:
            skipped.append((title, note))
            print(f"  skip  {title[:40]:<40} {note}", flush=True)
        else:
            written.append((tid, tmdb_id, title))
            print(f"  MATCH {title[:40]:<40} -> tmdb {tmdb_id}  ({note})", flush=True)
            if not args.dry_run:
                # Staged, not committed, per row. An fsync on a 668 MB WAL per
                # match dropped this to ~1 title/min; one commit at the end is
                # the difference between 90 seconds and half an hour.
                conn.execute("UPDATE titles SET tmdb_id = ? WHERE id = ?", (tmdb_id, tid))
        done.add(tid)
        state["done"] = sorted(done)
        STATE.write_text(json.dumps(state), encoding="utf-8")
        time.sleep(0.25)  # be polite to TMDB

    if not args.dry_run and written:
        conn.commit()
        print(f"committed {len(written)} tmdb_id updates in one transaction", flush=True)

    print(f"\nmatched {len(written)}   skipped {len(skipped)}   (of {len(rows)})")
    if args.dry_run:
        print("dry run - nothing written")
    else:
        conn.commit()
        still = conn.execute(
            """SELECT COUNT(*) FROM titles
                WHERE (tmdb_id IS NULL OR tmdb_id=0)
                  AND type IN ('tv','anime','short_drama')
                  AND id NOT IN (SELECT title_id FROM seasons)"""
        ).fetchone()[0]
        print(f"still missing after backfill: {still}  (these need a real match, not a guess)")
    conn.close()
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    sys.exit(main())
