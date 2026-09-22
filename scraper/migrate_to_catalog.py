"""
migrate_to_catalog.py — One-shot migration from legacy cache.db (single flat table)
into the new normalized catalog.db schema.

Honest rules (per spec §32, §33):
  - Reject malformed rows (missing title, invalid year).
  - Deduplicate by imdbId first, then by (title_norm, year).
  - Normalize genres into canonical taxonomy; drop garbage values.
  - Map country strings to canonical country list; drop unknowns.
  - Do NOT inflate counts. Every figure reported is a real DB query.
"""
from __future__ import annotations
import sqlite3
import re
import sys
from pathlib import Path
from typing import Any

from catalog_schema import init_catalog, CANONICAL_GENRES, CANONICAL_COUNTRIES, CANONICAL_LANGUAGES

LEGACY = Path("cache.db")
TARGET = Path("catalog.db")

# Slugify -----------------------------------------------------------------
def slugify(text: str) -> str:
    s = (text or "").lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "untitled"

def normalize_title(t: str) -> str:
    return re.sub(r"\s+", " ", (t or "").strip()).lower()

# Build lookup tables from canonical lists --------------------------------
GENRE_LOOKUP: dict[str, tuple[int, str]] = {}   # variant -> (genre_id, canonical_name)
for _slug, _name, _aliases in CANONICAL_GENRES:
    variants = {_name.lower(), _slug.lower().replace("-", " ")}
    variants |= {a.lower() for a in _aliases}
    variants.add(_slug.lower())
    # Multi-word genre aliases that the legacy CSV splitter breaks:
    # e.g. legacy has "Science Fiction" as TWO csv values "Science","Fiction"
    if " " in _name.lower():
        variants.add(_name.lower().replace(" ", "-"))
        variants.add(_name.lower().replace(" ", ""))
    if " " in _slug.lower():
        variants.add(_slug.lower().replace(" ", "-"))
        variants.add(_slug.lower().replace(" ", ""))

COUNTRY_LOOKUP: dict[str, int] = {}             # variant -> country_id
for _code, _name, *_ in CANONICAL_COUNTRIES:
    COUNTRY_LOOKUP[_name.lower()] = None  # filled after init_catalog

LANGUAGE_LOOKUP: dict[str, int] = {}            # name/code -> language_id
for _code, _name, *_ in CANONICAL_LANGUAGES:
    LANGUAGE_LOOKUP[_name.lower()] = None
    LANGUAGE_LOOKUP[_code.lower()] = None


def load_lookups(cur: sqlite3.Cursor):
    """After init_catalog() seeded taxonomies, fill GENRE_LOOKUP / COUNTRY_LOOKUP / LANGUAGE_LOOKUP."""
    cur.execute("SELECT id, slug, name, name_aliases FROM genres")
    for gid, slug, name, aliases_json in cur.fetchall():
        try:
            import json
            aliases = json.loads(aliases_json) if aliases_json else []
        except Exception:
            aliases = []
        variants = {name.lower(), slug.lower(), slug.lower().replace("-", " ")}
        variants |= {a.lower() for a in aliases}
        for v in variants:
            GENRE_LOOKUP[v] = (gid, name)
    cur.execute("SELECT id, code, name FROM countries")
    for cid, code, name in cur.fetchall():
        COUNTRY_LOOKUP[name.lower()] = cid
        COUNTRY_LOOKUP[code.lower()] = cid
    cur.execute("SELECT id, code, name FROM languages")
    for lid, code, name in cur.fetchall():
        LANGUAGE_LOOKUP[name.lower()] = lid
        LANGUAGE_LOOKUP[code.lower()] = lid


# Field parsers -----------------------------------------------------------
def split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    parts = re.split(r"[,|/;]+", value)
    return [p.strip() for p in parts if p.strip()]

def parse_genres(raw: str | None) -> list[int]:
    """Parse legacy genres field. Legacy uses JSON arrays where each element may be:
       - a single quoted token: \"Animation\"
       - a CSV inside quoted string: \"Action, Adventure, Sci-Fi\"
       - a year leak: \"2026\"
       - a multi-word genre split as separate array elements: [\"Science\",\"Fiction\"]
    Returns canonical genre ids, de-duped, garbage dropped.
    """
    if not raw:
        return []
    # Try JSON parse first
    tokens: list[str] = []
    try:
        import json
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            for el in parsed:
                if not isinstance(el, str):
                    continue
                # Each element may itself be a CSV string
                for tok in re.split(r"[,|/;]+", el):
                    tok = tok.strip().strip('"').strip("'")
                    if tok:
                        tokens.append(tok)
        else:
            tokens = re.split(r"[,|/;]+", str(parsed))
    except Exception:
        tokens = re.split(r"[,|/;]+", raw)

    out: list[int] = []
    seen: set[int] = set()
    # First pass: single tokens
    singles: list[str] = []
    for tok in tokens:
        key = tok.strip().lower()
        if not key:
            continue
        if re.fullmatch(r"\d{1,4}", key):
            continue  # year leak
        if len(key) > 30:
            continue
        singles.append(key)
    # Second pass: try pairs (e.g. "Science" + "Fiction" -> "Science Fiction")
    pair_idx_used: set[int] = set()
    for i in range(len(singles) - 1):
        if i in pair_idx_used:
            continue
        joined = singles[i] + " " + singles[i + 1]
        if joined in GENRE_LOOKUP:
            gid, _ = GENRE_LOOKUP[joined]
            if gid not in seen:
                seen.add(gid)
                out.append(gid)
            pair_idx_used.add(i)
            pair_idx_used.add(i + 1)
    # Third pass: unmatched singles
    for i, key in enumerate(singles):
        if i in pair_idx_used:
            continue
        if key in GENRE_LOOKUP:
            gid, _ = GENRE_LOOKUP[key]
            if gid not in seen:
                seen.add(gid)
                out.append(gid)
    return out

def parse_countries(raw: str | None) -> list[int]:
    if not raw:
        return []
    out: list[int] = []
    seen: set[int] = set()
    for piece in split_csv(raw):
        key = piece.strip().lower()
        # Skip non-country words (e.g. leaked from genre field)
        if key in COUNTRY_LOOKUP:
            cid = COUNTRY_LOOKUP[key]
            if cid not in seen:
                seen.add(cid)
                out.append(cid)
    return out

def parse_languages(raw: str | None) -> list[int]:
    if not raw:
        return []
    out: list[int] = []
    seen: set[int] = set()
    for piece in split_csv(raw):
        key = piece.strip().lower()
        if key in LANGUAGE_LOOKUP:
            lid = LANGUAGE_LOOKUP[key]
            if lid not in seen:
                seen.add(lid)
                out.append(lid)
    return out

def parse_rating(raw: str | None) -> float | None:
    if raw is None:
        return None
    try:
        v = float(str(raw).strip())
        if 0 <= v <= 10:
            return round(v, 1)
        return None
    except (ValueError, TypeError):
        return None

def parse_year(raw: Any) -> int | None:
    if raw is None or raw == "":
        return None
    try:
        y = int(raw)
        if 1900 <= y <= 2030:
            return y
        return None
    except (ValueError, TypeError):
        return None

def parse_runtime(raw: Any) -> int | None:
    if raw is None or raw == "":
        return None
    try:
        r = int(raw)
        if 1 <= r <= 600:
            return r
        return None
    except (ValueError, TypeError):
        return None


def detect_anime_from_genres(genre_ids: list[int], title: str, country_ids: list[int]) -> bool:
    """Heuristic: legacy never stored 'anime' as a literal — it stored 'Animation' +
    a country like Japan. Flag anime if genre is Animation AND any country is JP.
    """
    animation_id = None
    for gid, name in GENRE_LOOKUP.values():
        if name.lower() == "animation":
            animation_id = gid
            break
    if not animation_id:
        return False
    if animation_id not in genre_ids:
        return False
    # Country = Japan (id from COUNTRY_LOOKUP)
    jp_id = COUNTRY_LOOKUP.get("japan")
    return jp_id is not None and jp_id in country_ids


# Migration driver --------------------------------------------------------
def main(legacy_path: Path = LEGACY, target_path: Path = TARGET):
    print(f"[migrate] legacy = {legacy_path}  target = {target_path}")
    if not legacy_path.exists():
        print(f"[migrate] FATAL: legacy DB not found at {legacy_path}")
        sys.exit(1)

    # 1. Open legacy
    src = sqlite3.connect(str(legacy_path))
    src.row_factory = sqlite3.Row
    scur = src.cursor()
    scur.execute("SELECT COUNT(*) FROM titles")
    legacy_total = scur.fetchone()[0]
    print(f"[migrate] legacy rows: {legacy_total}")

    # 2. Init fresh catalog.db
    if target_path.exists():
        # Recreate to ensure clean state — old catalog.db is empty anyway
        target_path.unlink()
    dst = init_catalog(target_path)
    dst.row_factory = sqlite3.Row
    dcur = dst.cursor()
    load_lookups(dcur)

    scur.execute("SELECT * FROM titles")
    rows = scur.fetchall()

    # Dedup map: imdb_id -> title_id (preferred), (title_norm|year) -> title_id (fallback)
    by_imdb: dict[str, int] = {}
    by_ty: dict[tuple[str, int], int] = {}

    stats = {
        "total_legacy": legacy_total,
        "rejected_no_title": 0,
        "rejected_invalid_year": 0,
        "rejected_no_year": 0,
        "duplicate_imdb": 0,
        "duplicate_title_year": 0,
        "inserted": 0,
        "skipped_curated_conflict": 0,
        "anime_flagged": 0,
    }

    # Pre-collect curated titles to ensure they win on collision
    scur.execute("SELECT * FROM titles WHERE source='curated'")
    curated_rows = [dict(r) for r in scur.fetchall()]

    # Pass 1: insert curated first (they're the most enriched)
    inserted_ids: set[int] = set()
    for r in curated_rows:
        title = (r["title"] or "").strip()
        if not title:
            stats["rejected_no_title"] += 1
            continue
        year = parse_year(r["year"])
        if year is None:
            stats["rejected_no_year"] += 1
            continue
        # Insert curated
        slug = f"{slugify(title)}-{year}"
        # Dedupe slug
        s_counter = 0
        final_slug = slug
        while dcur.execute("SELECT 1 FROM titles WHERE slug=?", (final_slug,)).fetchone():
            s_counter += 1
            final_slug = f"{slug}-{s_counter}"
        rating = parse_rating(r["rating"])
        runtime = parse_runtime(r["runtime"])
        gids = parse_genres(r["genres"])
        cids = parse_countries(r["country"])
        lids = parse_languages(r["language"])
        type_ = "movie" if (r["type"] or "movie").lower() == "movie" else "tv"
        is_anime = 1 if detect_anime_from_genres(gids, title, cids) else 0
        if is_anime:
            type_ = "anime"
        try:
            dcur.execute("""
                INSERT INTO titles
                  (slug, title, original_title, type, year, runtime, rating,
                   overview, poster, backdrop, imdb_id, tmdb_id,
                   is_anime, is_short_drama)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,0)
            """, (
                final_slug, title, r["title"], type_, year, runtime, rating,
                r["overview"], r["poster"], r["backdrop"], r["imdb_id"], r["tmdb_id"],
                is_anime,
            ))
        except sqlite3.IntegrityError as e:
            print(f"[migrate] curated insert dup skipped: {title} ({year}) -> {e}")
            stats["skipped_curated_conflict"] += 1
            continue
        tid = dcur.lastrowid
        inserted_ids.add(tid)
        for gid in gids:
            dcur.execute("INSERT OR IGNORE INTO title_genres (title_id, genre_id) VALUES (?,?)", (tid, gid))
        for cid in cids:
            dcur.execute("INSERT OR IGNORE INTO title_countries (title_id, country_id) VALUES (?,?)", (tid, cid))
        for lid in lids:
            dcur.execute("INSERT OR IGNORE INTO title_languages (title_id, language_id, is_original) VALUES (?,?,1)", (tid, lid))
        # Availability
        dcur.execute("SELECT id FROM sources WHERE slug=?", (r["source"] or "curated",))
        src_row = dcur.fetchone()
        if src_row is None:
            dcur.execute("INSERT INTO sources (slug, name, type, enabled, is_legal) VALUES (?,?,?,?,?)",
                         (r["source"] or "curated", r["source"] or "curated", "scraper", 1, 0))
            src_id = dcur.lastrowid
        else:
            src_id = src_row[0]
        dcur.execute("""INSERT OR REPLACE INTO availability
            (title_id, source_id, status, external_id, external_url, last_checked_at, last_success_at)
            VALUES (?,?,?,?,?,?,?)""",
            (tid, src_id, "available", r["id"], r["source_url"], r["fetched_at"], r["fetched_at"]))
        stats["inserted"] += 1
        if is_anime:
            stats["anime_flagged"] += 1
        # Track for dedup
        if r["imdb_id"]:
            by_imdb[r["imdb_id"]] = tid
        try:
            by_ty[(normalize_title(title), year)] = tid
        except Exception:
            pass

    # Pass 2: walk non-curated rows
    scur.execute("SELECT * FROM titles WHERE source != 'curated'")
    for r in scur.fetchall():
        title = (r["title"] or "").strip()
        if not title:
            stats["rejected_no_title"] += 1
            continue
        year = parse_year(r["year"])
        if year is None:
            stats["rejected_no_year"] += 1
            continue
        if not (1900 <= year <= 2030):
            stats["rejected_invalid_year"] += 1
            continue

        # Dedup by imdb_id first
        existing_id = None
        if r["imdb_id"] and r["imdb_id"] in by_imdb:
            existing_id = by_imdb[r["imdb_id"]]
            stats["duplicate_imdb"] += 1
        else:
            tkey = (normalize_title(title), year)
            if tkey in by_ty:
                existing_id = by_ty[tkey]
                stats["duplicate_title_year"] += 1

        if existing_id:
            # Just add availability for this source
            dcur.execute("SELECT id FROM sources WHERE slug=?", (r["source"] or "scraper",))
            src_row = dcur.fetchone()
            if src_row is None:
                dcur.execute("INSERT INTO sources (slug, name, type, enabled, is_legal) VALUES (?,?,?,?,?)",
                             (r["source"] or "scraper", r["source"] or "scraper", "scraper", 1, 0))
                src_id = dcur.lastrowid
            else:
                src_id = src_row[0]
            dcur.execute("""INSERT OR IGNORE INTO availability
                (title_id, source_id, status, external_id, external_url, last_checked_at, last_success_at)
                VALUES (?,?,?,?,?,?,?)""",
                (existing_id, src_id, "available", r["id"], r["source_url"], r["fetched_at"], r["fetched_at"]))
            continue

        # New title — insert
        slug = f"{slugify(title)}-{year}"
        s_counter = 0
        final_slug = slug
        while dcur.execute("SELECT 1 FROM titles WHERE slug=?", (final_slug,)).fetchone():
            s_counter += 1
            final_slug = f"{slug}-{s_counter}"
        rating = parse_rating(r["rating"])
        runtime = parse_runtime(r["runtime"])
        gids = parse_genres(r["genres"])
        cids = parse_countries(r["country"])
        lids = parse_languages(r["language"])
        type_ = "movie" if (r["type"] or "movie").lower() == "movie" else "tv"
        is_anime = 1 if detect_anime_from_genres(gids, title, cids) else 0
        if is_anime:
            type_ = "anime"
        try:
            dcur.execute("""
                INSERT INTO titles
                  (slug, title, original_title, type, year, runtime, rating,
                   overview, poster, backdrop, imdb_id, tmdb_id,
                   is_anime, is_short_drama)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,0)
            """, (
                final_slug, title, r["title"], type_, year, runtime, rating,
                r["overview"], r["poster"], r["backdrop"], r["imdb_id"], r["tmdb_id"],
                is_anime,
            ))
        except sqlite3.IntegrityError:
            # Lost dedup race
            stats["duplicate_title_year"] += 1
            continue
        tid = dcur.lastrowid
        for gid in gids:
            dcur.execute("INSERT OR IGNORE INTO title_genres (title_id, genre_id) VALUES (?,?)", (tid, gid))
        for cid in cids:
            dcur.execute("INSERT OR IGNORE INTO title_countries (title_id, country_id) VALUES (?,?)", (tid, cid))
        for lid in lids:
            dcur.execute("INSERT OR IGNORE INTO title_languages (title_id, language_id, is_original) VALUES (?,?,1)", (tid, lid))
        dcur.execute("SELECT id FROM sources WHERE slug=?", (r["source"] or "scraper",))
        src_row = dcur.fetchone()
        if src_row is None:
            dcur.execute("INSERT INTO sources (slug, name, type, enabled, is_legal) VALUES (?,?,?,?,?)",
                         (r["source"] or "scraper", r["source"] or "scraper", "scraper", 1, 0))
            src_id = dcur.lastrowid
        else:
            src_id = src_row[0]
        dcur.execute("""INSERT OR IGNORE INTO availability
            (title_id, source_id, status, external_id, external_url, last_checked_at, last_success_at)
            VALUES (?,?,?,?,?,?,?)""",
            (tid, src_id, "available", r["id"], r["source_url"], r["fetched_at"], r["fetched_at"]))
        stats["inserted"] += 1
        if is_anime:
            stats["anime_flagged"] += 1
        if r["imdb_id"]:
            by_imdb[r["imdb_id"]] = tid
        try:
            by_ty[(normalize_title(title), year)] = tid
        except Exception:
            pass

    dst.commit()

    # Honest count report
    dcur.execute("SELECT COUNT(*) FROM titles")
    real_total = dcur.fetchone()[0]
    dcur.execute("SELECT COUNT(*) FROM titles WHERE type='movie'")
    movies = dcur.fetchone()[0]
    dcur.execute("SELECT COUNT(*) FROM titles WHERE type='tv'")
    tvs = dcur.fetchone()[0]
    dcur.execute("SELECT COUNT(*) FROM titles WHERE type='anime'")
    animes = dcur.fetchone()[0]
    dcur.execute("SELECT COUNT(*) FROM title_genres")
    genre_links = dcur.fetchone()[0]
    dcur.execute("SELECT COUNT(*) FROM title_countries")
    country_links = dcur.fetchone()[0]
    dcur.execute("SELECT COUNT(*) FROM title_languages")
    language_links = dcur.fetchone()[0]
    dcur.execute("SELECT COUNT(*) FROM availability")
    avail = dcur.fetchone()[0]
    dcur.execute("SELECT COUNT(*) FROM sources")
    srcs = dcur.fetchone()[0]

    print("\n[migrate] STATS")
    for k, v in stats.items():
        print(f"  {k}: {v}")
    print("\n[migrate] CATALOG.db COUNTS (real, post-dedup)")
    print(f"  titles:           {real_total}")
    print(f"    movies:         {movies}")
    print(f"    tv:             {tvs}")
    print(f"    anime:          {animes}")
    print(f"  title_genres:     {genre_links}")
    print(f"  title_countries:  {country_links}")
    print(f"  title_languages:  {language_links}")
    print(f"  availability:     {avail}")
    print(f"  sources:          {srcs}")

    src.close()
    dst.close()
    print(f"\n[migrate] DONE. catalog.db at: {target_path.absolute()}")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else LEGACY,
         Path(sys.argv[2]) if len(sys.argv) > 2 else TARGET)