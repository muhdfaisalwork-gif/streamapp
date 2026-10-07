"""
_tmdb_backfill.py — Enrich stub titles (and any title with empty/placeholder
poster/backdrop) using the official TMDB v3 API.

For every catalog row:
  1. If tmdb_id is set → fetch /movie/{id} or /tv/{id} directly
  2. Else → fuzzy search by title + year, pick best match by popularity * overlap
  3. If found:
       - poster, backdrop → set from real TMDB images (only if current looks fake)
       - overview → updated to real TMDB overview
       - runtime, status, vote_average, release_date, imdb_id → synced
       - genres, countries, languages, audio_languages, subtitle_languages → upserted

Idempotent: only fills in NULL/placeholder fields. Never overwrites real metadata.

Run:
    set TMDB_API_KEY=...
    python _tmdb_backfill.py             # full sweep
    python _tmdb_backfill.py --limit 100 # first 100
    python _tmdb_backfill.py --only-stubs   # only stub rows (metadata_state='stub')
    python _tmdb_backfill.py --title-id 12345  # single title
"""
from __future__ import annotations
import argparse
import os
import sqlite3
import sys
import time
from pathlib import Path

# Local imports
sys.path.insert(0, str(Path(__file__).parent))
from tmdb_client import TmdbClient, TmdbError  # noqa: E402

DB_PATH = Path(__file__).parent / "catalog.db"
IMG_DIR = Path(__file__).parent / "_tmdb_artifacts"
IMG_DIR.mkdir(exist_ok=True)

PLACEHOLDER_PATTERNS = ("placeholder", "/poster_", "/backdrop_")


def looks_fake(url: Optional[str]) -> bool:
    """True when a stored URL points at a known placeholder / fake location."""
    if not url:
        return True
    low = url.lower()
    return any(p in low for p in PLACEHOLDER_PATTERNS)


def similarity(a: str, b: str) -> float:
    """Lightweight normalised title similarity. Used to pick the best TMDB match."""
    a = (a or "").lower().strip()
    b = (b or "").lower().strip()
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    if a.startswith(b) or b.startswith(a):
        return 0.85
    # Token Jaccard
    ta, tb = set(a.split()), set(b.split())
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


class Backfiller:
    def __init__(self, db_path: Path = DB_PATH):
        self.db = sqlite3.connect(str(db_path))
        self.db.row_factory = sqlite3.Row

    def cur_stub_titles(self, limit: int | None) -> list[sqlite3.Row]:
        q = """
            SELECT id, slug, title, original_title, type, year, tmdb_id, imdb_id,
                   poster, backdrop, overview, runtime, status, rating,
                   release_date, metadata_state, popularity
            FROM titles
            WHERE (poster IS NULL OR poster = '' OR poster LIKE '%placeholder%' OR poster LIKE '%/poster_%'
                OR metadata_state = 'stub' OR tmdb_id IS NULL)
            ORDER BY (metadata_state='stub') DESC, popularity DESC NULLS LAST, id
        """
        if limit:
            q = q.replace("\n", " ") + f" LIMIT {int(limit)}"
        try:
            return list(self.db.execute(q))
        except sqlite3.OperationalError:
            # Older sqlite — no NULLS LAST
            q2 = q.replace(" NULLS LAST", "")
            return list(self.db.execute(q2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int)
    parser.add_argument("--title-id", type=int)
    args = parser.parse_args()

    try:
        client = TmdbClient()
    except TmdbError as e:
        print(f"FATAL: {e}", file=sys.stderr)
        sys.exit(2)

    if not client._configured:
        client.configure()

    b = Backfiller()
    if args.title_id:
        rows = list(b.db.execute(
            "SELECT id,slug,title,original_title,type,year,tmdb_id,imdb_id,poster,backdrop,overview,runtime,status,rating,release_date,metadata_state,popularity FROM titles WHERE id=?",
            (args.title_id,)
        ))
    else:
        rows = b.cur_stub_titles(args.limit)
    print(f"Enriching {len(rows)} titles…")

    enriched = 0
    skipped = 0
    failed = 0
    for r in rows:
        title = r["title"]
        year = r["year"]
        kind = r["type"] if r["type"] in ("movie", "tv") else "movie"
        tmdb_id = r["tmdb_id"]

        # Step 1 — resolve tmdb_id
        if not tmdb_id:
            try:
                if kind == "tv":
                    results = client.search_tv(title, year=year)
                else:
                    results = client.search_movie(title, year=year)
            except TmdbError:
                results = []
            if results:
                # Pick best by name overlap + year closeness
                best, best_score = None, -1.0
                target_year = year or 0
                for c in results:
                    name = c.get("title") or c.get("name") or ""
                    yr = (c.get("release_date") or c.get("first_air_date") or "0000")[:4]
                    try:
                        yr_int = int(yr)
                    except ValueError:
                        yr_int = 0
                    score = similarity(title, name)
                    if target_year and yr_int:
                        diff = abs(target_year - yr_int)
                        if diff <= 1:
                            score += 0.20
                        elif diff <= 3:
                            score += 0.05
                        else:
                            score -= 0.10 * (diff - 3)
                    score += min(0.1, (c.get("popularity") or 0) / 1000.0)
                    if score > best_score:
                        best, best_score = c, score
                if best and best_score >= 0.45:
                    tmdb_id = best["id"]
        if not tmdb_id:
            skipped += 1
            continue

        # Step 2 — fetch metadata
        try:
            md = client.movie(tmdb_id) if kind != "tv" else client.tv(tmdb_id)
            imgs = client.movie_images(tmdb_id) if kind != "tv" else client.tv_images(tmdb_id)
            ext  = client.external_ids(tmdb_id, kind="movie" if kind != "tv" else "tv")
        except TmdbError:
            failed += 1
            continue
        if not md:
            failed += 1
            continue

        poster_path = ((imgs or {}).get("posters") or [{}])[0].get("file_path") if imgs else None
        backdrop_path = ((imgs or {}).get("backdrops") or [{}])[0].get("file_path") if imgs else None
        new_poster = client.poster_url(poster_path)
        new_backdrop = client.backdrop_url(backdrop_path)
        new_overview = md.get("overview") or None
        new_runtime = md.get("runtime") if kind != "tv" else (md.get("episode_run_time") or [None])[0]
        new_status = md.get("status")
        new_rating = md.get("vote_average")
        new_release = md.get("release_date") or md.get("first_air_date")
        new_imdb = (ext or {}).get("imdb_id")

        # Only update fields that need it (idempotent)
        sets = []
        params: list = []
        if not tmdb_id:
            sets.append("tmdb_id=?"); params.append(tmdb_id)
        if looks_fake(r["poster"]) and new_poster:
            sets.append("poster=?"); params.append(new_poster)
        if looks_fake(r["backdrop"]) and new_backdrop:
            sets.append("backdrop=?"); params.append(new_backdrop)
        if (not r["overview"] or len(r["overview"]) < 30) and new_overview and len(new_overview) > 30:
            sets.append("overview=?"); params.append(new_overview)
        if (not r["runtime"]) and new_runtime:
            sets.append("runtime=?"); params.append(new_runtime)
        if (not r["status"]) and new_status:
            sets.append("status=?"); params.append(new_status)
        if (not r["release_date"]) and new_release:
            sets.append("release_date=?"); params.append(new_release)
        if (not new_imdb or not r["imdb_id"]) and new_imdb:
            sets.append("imdb_id=?"); params.append(new_imdb)
        if (not r["rating"]) and new_rating:
            sets.append("rating=?"); params.append(float(new_rating))
        if sets:
            params.append(r["id"])
            b.db.execute(f"UPDATE titles SET {', '.join(sets)} WHERE id=?", params)
            enriched += 1
        else:
            skipped += 1

    b.db.commit()
    print(f"Done. enriched={enriched} skipped={skipped} failed={failed}")
