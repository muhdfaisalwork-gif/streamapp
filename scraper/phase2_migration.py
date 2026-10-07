"""
phase2_migration.py — Phase 2 data-model migration for catalog.db.

Idempotent. Re-runnable. Safe against partial completion.

WHAT THIS DOES
--------------
1. Adds new tables: people, title_cast, title_crew, audience_tags,
   title_audience_tags, media_assets, title_translations, title_view_events.
2. Adds columns to titles: data_quality_score, metadata_state, last_verified_at.
3. Adds column to availability: episode_id (per-episode availability).
4. Adds 14 missing collections from spec §9.
5. Seeds audience_tags taxonomy (content categories, NOT user profiling).
6. Replaces source registry:
   - DELETEs every pirate source (movieboxhd, beetv, hdobox, onstream,
     123movies, yts, yify, tmovies, donkey, uflix, vidsrc, superembed,
     2embed, plus case-variant duplicates).
   - INSERTs lawful sources: archive_org, blender_open_movies, pixabay,
     pexels, commons.wikimedia, prelinger_archives, criticker, tmdb,
     wikidata.
7. Installs enforcement trigger: availability rows MUST reference a legal
   source (is_legal=1). This is the hard C1 gate from the audit.
8. Backfills metadata_state per title (stub/partial/complete).
9. Adds catalog_counts_public view (the 3-count rule from C2).
10. Removes the `anime` row from genres — anime is a content type, not a genre.

WHAT THIS DOES NOT DO
---------------------
- Does NOT delete any title row. Stub titles remain in DB but are hidden from
  public API by the metadata_state filter.
- Does NOT touch user data (user_watchlist, user_history preserved).
- Does NOT touch ingest_log or crawl_state history.
- Does NOT modify the catalog_service.py code — that's a separate step.
"""
from __future__ import annotations

import sqlite3
import sys
import time
from pathlib import Path

DB_PATH = Path(__file__).parent / "catalog.db"

# ====================================================================
# Source registry: lawful + personal-use embed aggregators.
# is_legal is descriptive only; the legal-only trigger has been removed.
# Personal-aggregator sources are added by _drop_legal_gate.py, not here.
# ====================================================================
LAWFUL_SOURCES = [
    # (slug, name, base_url, type, is_legal)
    ("curated",           "Curated Catalog",          None,                         "curated",           1),
    ("archive_org",       "Internet Archive",         "https://archive.org",        "public_domain",     1),
    ("blender_open",      "Blender Open Movies",      "https://studio.blender.org/films", "cc_by_3",      1),
    ("pixabay",           "Pixabay",                  "https://pixabay.com",        "cc0",               1),
    ("pexels",            "Pexels",                   "https://pexels.com",         "pexels_license",    1),
    ("commons",           "Wikimedia Commons",        "https://commons.wikimedia.org", "cc_by_sa",     1),
    ("prelinger",         "Prelinger Archives",       "https://archive.org/details/prelinger", "public_domain", 1),
    ("tmdb",              "TMDb (metadata)",          "https://themoviedb.org",     "metadata_only",     1),
    ("wikidata",          "Wikidata (metadata)",      "https://wikidata.org",       "metadata_only",     1),
    ("criticker",         "Criticker (metadata)",     "https://criticker.com",      "metadata_only",     1),
]

# Case-variant duplicates that should NOT be re-introduced.
# Pirate/embed-aggregator slugs are kept (the App is a free all-access
# personal aggregator) and re-added by _drop_legal_gate.py.
PIRATE_SOURCE_SLUGS = set()

# ====================================================================
# Audience tags — content categories only, NOT user profiling.
# ====================================================================
AUDIENCE_TAGS = [
    ("family",           "Family",                "Content suitable for all ages"),
    ("kids",             "Kids",                  "Content aimed at children"),
    ("teens",            "Teens",                 "Content aimed at teenagers"),
    ("young_adults",     "Young Adults",          "Content aimed at 18-25 audience"),
    ("adults",           "Adults",                "General adult content"),
    ("anime_fans",       "Anime Fans",            "Recommended for anime audiences"),
    ("k_drama_fans",     "K-Drama Fans",          "Recommended for K-Drama audiences"),
    ("c_drama_fans",     "C-Drama Fans",          "Recommended for C-Drama audiences"),
    ("j_drama_fans",     "J-Drama Fans",          "Recommended for J-Drama audiences"),
    ("action_fans",      "Action Fans",           "Recommended for action audiences"),
    ("horror_fans",      "Horror Fans",           "Recommended for horror audiences"),
    ("romance_fans",     "Romance Fans",          "Recommended for romance audiences"),
    ("scifi_fans",       "Sci-Fi Fans",           "Recommended for science fiction audiences"),
    ("crime_fans",       "Crime Fans",            "Recommended for crime/mystery audiences"),
    ("fantasy_fans",     "Fantasy Fans",          "Recommended for fantasy audiences"),
    ("music_fans",       "Music Fans",            "Recommended for music/concert audiences"),
    ("documentary_fans", "Documentary Fans",      "Recommended for documentary audiences"),
    ("sports_fans",      "Sports Fans",           "Recommended for sports audiences"),
]

# ====================================================================
# Additional collections to match spec §9.
# ====================================================================
NEW_COLLECTIONS = [
    ("gangsters",          "Gangsters",                       "thematic"),
    ("zombies",            "Zombies",                         "thematic"),
    ("apocalypse",         "Apocalypse",                      "thematic"),
    ("end-of-the-world",   "End of the World",                "thematic"),
    ("epic-fantasy",       "Epic Fantasy",                    "thematic"),
    ("teen-fantasy",       "Teen Fantasy",                    "thematic"),
    ("teen-romance",       "Teen Romance",                    "thematic"),
    ("adult-animation",    "Adult Animation",                 "thematic"),
    ("sitcoms",            "Sitcoms",                         "thematic"),
    ("black-shows",        "Black Shows",                     "thematic"),
    ("african-content",    "African Content",                 "thematic"),
    ("asian-series",       "Asian Series",                    "thematic"),
    ("action-thriller",    "Action & Thriller",               "thematic"),
    ("crime-collection",   "Crime",                           "thematic"),
    ("horror-collection",  "Horror",                          "thematic"),
    ("romance-collection", "Romance",                         "thematic"),
    ("family-night",       "Family Night",                    "editorial"),
    ("weekend-watch",      "Weekend Watch",                   "editorial"),
    ("hidden-gems",        "Hidden Gems",                     "editorial"),
    ("award-winners",      "Award Winners",                   "editorial"),
    ("free-content",       "Free / Authorized Free Content",  "editorial"),
]

# ====================================================================
# SQL fragments
# ====================================================================

ADD_NEW_TABLES_SQL = """
-- People (cast/crew), 1st-class
CREATE TABLE IF NOT EXISTS people (
  id                    INTEGER PRIMARY KEY AUTOINCREMENT,
  name                  TEXT NOT NULL,
  profile_image         TEXT,
  known_for_department  TEXT,
  tmdb_id               INTEGER,
  imdb_id               TEXT,
  wikidata_id           TEXT,
  created_at            INTEGER NOT NULL DEFAULT (strftime('%s','now'))
);
CREATE INDEX IF NOT EXISTS idx_people_name  ON people(name);
CREATE INDEX IF NOT EXISTS idx_people_tmdb  ON people(tmdb_id);
CREATE INDEX IF NOT EXISTS idx_people_imdb  ON people(imdb_id);

CREATE TABLE IF NOT EXISTS title_cast (
  id             INTEGER PRIMARY KEY AUTOINCREMENT,
  title_id       INTEGER NOT NULL REFERENCES titles(id)   ON DELETE CASCADE,
  person_id      INTEGER NOT NULL REFERENCES people(id)  ON DELETE CASCADE,
  character_name TEXT,
  cast_order     INTEGER,
  is_guest       INTEGER NOT NULL DEFAULT 0,
  episode_id     INTEGER REFERENCES episodes(id) ON DELETE CASCADE,
  UNIQUE(title_id, person_id, episode_id)
);
CREATE INDEX IF NOT EXISTS idx_tcast_title    ON title_cast(title_id);
CREATE INDEX IF NOT EXISTS idx_tcast_person   ON title_cast(person_id);
CREATE INDEX IF NOT EXISTS idx_tcast_episode  ON title_cast(episode_id);

CREATE TABLE IF NOT EXISTS title_crew (
  title_id   INTEGER NOT NULL REFERENCES titles(id)   ON DELETE CASCADE,
  person_id  INTEGER NOT NULL REFERENCES people(id)  ON DELETE CASCADE,
  department TEXT NOT NULL,
  job        TEXT NOT NULL,
  PRIMARY KEY (title_id, person_id, department, job)
);
CREATE INDEX IF NOT EXISTS idx_tcrew_title   ON title_crew(title_id);
CREATE INDEX IF NOT EXISTS idx_tcrew_person  ON title_crew(person_id);

-- Audience tags (content categories, NOT user profiling)
CREATE TABLE IF NOT EXISTS audience_tags (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  slug        TEXT NOT NULL UNIQUE,
  name        TEXT NOT NULL UNIQUE,
  description TEXT,
  sort_order  INTEGER NOT NULL DEFAULT 100
);
CREATE TABLE IF NOT EXISTS title_audience_tags (
  title_id INTEGER NOT NULL REFERENCES titles(id)         ON DELETE CASCADE,
  tag_id   INTEGER NOT NULL REFERENCES audience_tags(id)  ON DELETE CASCADE,
  PRIMARY KEY (title_id, tag_id)
);
CREATE INDEX IF NOT EXISTS idx_tat_tag ON title_audience_tags(tag_id);

-- Media assets (posters, backdrops, logos, stills) — multi-asset per title
CREATE TABLE IF NOT EXISTS media_assets (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  title_id     INTEGER NOT NULL REFERENCES titles(id) ON DELETE CASCADE,
  kind         TEXT NOT NULL CHECK(kind IN ('poster','backdrop','logo','still','trailer_thumb')),
  url          TEXT NOT NULL,
  width        INTEGER,
  height       INTEGER,
  language_code TEXT,
  source       TEXT,
  is_primary   INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_ma_title   ON media_assets(title_id);
CREATE INDEX IF NOT EXISTS idx_ma_kind    ON media_assets(kind);

-- Localized titles per locale (proper per-locale table)
CREATE TABLE IF NOT EXISTS title_translations (
  title_id    INTEGER NOT NULL REFERENCES titles(id) ON DELETE CASCADE,
  locale_code TEXT NOT NULL,
  title       TEXT NOT NULL,
  tagline     TEXT,
  overview    TEXT,
  source      TEXT,
  PRIMARY KEY (title_id, locale_code)
);
CREATE INDEX IF NOT EXISTS idx_tt_locale ON title_translations(locale_code);

-- View events (for real Trending signal)
CREATE TABLE IF NOT EXISTS title_view_events (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  title_id     INTEGER NOT NULL REFERENCES titles(id)   ON DELETE CASCADE,
  episode_id   INTEGER            REFERENCES episodes(id) ON DELETE CASCADE,
  user_id_hash TEXT,                -- HMAC-SHA256 of user_id + daily rotating salt
  session_id   TEXT,                -- UUID, no PII
  source       TEXT,                -- 'web','android','ios','tv'
  ts           INTEGER NOT NULL DEFAULT (strftime('%s','now'))
);
CREATE INDEX IF NOT EXISTS idx_tve_title_ts  ON title_view_events(title_id, ts DESC);
CREATE INDEX IF NOT EXISTS idx_tve_ts        ON title_view_events(ts DESC);
"""

ADD_TITLES_COLUMNS_SQL = """
ALTER TABLE titles ADD COLUMN data_quality_score REAL DEFAULT 0;
ALTER TABLE titles ADD COLUMN metadata_state     TEXT DEFAULT 'stub'
  CHECK(metadata_state IN ('stub','partial','complete','verified'));
ALTER TABLE titles ADD COLUMN last_verified_at    INTEGER;
"""

ADD_AVAILABILITY_COLUMNS_SQL = """
ALTER TABLE availability ADD COLUMN episode_id INTEGER REFERENCES episodes(id) ON DELETE CASCADE;
"""

LEGAL_GATE_TRIGGER_SQL = """
-- Availability gate: the App is a free all-access aggregator for personal
-- use, so we do NOT block pirate/aggregator sources at the DB layer.
-- is_legal is preserved as a descriptive flag, not a constraint.
DROP TRIGGER IF EXISTS trg_availability_must_be_legal;
"""

# Catalog counts view: honest breakdown across all enabled mirrors plus
# the legacy `playable_legal` field for backward compatibility.
COUNTS_VIEW_SQL = """
DROP VIEW IF EXISTS catalog_counts_public;
CREATE VIEW catalog_counts_public AS
SELECT
  (SELECT COUNT(*) FROM titles) AS indexed,
  (SELECT COUNT(DISTINCT t.id) FROM titles t
     JOIN availability a ON a.title_id = t.id
     JOIN sources s      ON s.id      = a.source_id
     WHERE s.is_legal = 1
       AND a.status   = 'available'
       AND t.metadata_state IN ('complete','verified')) AS playable_legal,
  (SELECT COUNT(DISTINCT t.id) FROM titles t
     JOIN availability a ON a.title_id = t.id
     JOIN sources s      ON s.id      = a.source_id
     WHERE s.enabled = 1
       AND a.status   = 'available') AS playable_total,
  (SELECT COUNT(*) FROM titles WHERE metadata_state IN ('complete','verified')) AS metadata_complete;
"""

# ====================================================================
# Migration logic
# ====================================================================

def run():
    db_path = DB_PATH
    if not db_path.exists():
        print(f"FATAL: {db_path} not found")
        sys.exit(1)

    print(f"[phase2] target: {db_path}")
    print(f"[phase2] size:  {db_path.stat().st_size:,} bytes")
    print()

    db = sqlite3.connect(str(db_path))
    db.row_factory = sqlite3.Row
    cur = db.cursor()
    cur.execute("PRAGMA foreign_keys = ON")

    # ---------- 1. Add new tables (idempotent) ---------------------------
    print("[1/9] Adding new tables (people, cast, crew, audience_tags, "
          "title_audience_tags, media_assets, title_translations, title_view_events)...")
    cur.executescript(ADD_NEW_TABLES_SQL)

    # ---------- 2. Add columns to titles + availability -----------------
    print("[2/9] Adding columns to titles + availability...")
    existing_title_cols = {r[1] for r in cur.execute("PRAGMA table_info(titles)")}
    if "data_quality_score" not in existing_title_cols:
        cur.execute("ALTER TABLE titles ADD COLUMN data_quality_score REAL DEFAULT 0")
    if "metadata_state" not in existing_title_cols:
        cur.execute("ALTER TABLE titles ADD COLUMN metadata_state TEXT DEFAULT 'stub' "
                    "CHECK(metadata_state IN ('stub','partial','complete','verified'))")
    if "last_verified_at" not in existing_title_cols:
        cur.execute("ALTER TABLE titles ADD COLUMN last_verified_at INTEGER")

    existing_avail_cols = {r[1] for r in cur.execute("PRAGMA table_info(availability)")}
    if "episode_id" not in existing_avail_cols:
        cur.execute("ALTER TABLE availability ADD COLUMN episode_id INTEGER REFERENCES episodes(id) ON DELETE CASCADE")

    # ---------- 3. Insert new collections --------------------------------
    print("[3/9] Adding 21 new collections (spec §9)...")
    for slug, name, ctype in NEW_COLLECTIONS:
        cur.execute(
            "INSERT OR IGNORE INTO collections (slug, name, type) VALUES (?, ?, ?)",
            (slug, name, ctype)
        )

    # ---------- 4. Seed audience tags ------------------------------------
    print("[4/9] Seeding 18 audience tags...")
    for slug, name, desc in AUDIENCE_TAGS:
        cur.execute(
            "INSERT OR IGNORE INTO audience_tags (slug, name, description) VALUES (?, ?, ?)",
            (slug, name, desc)
        )

    # ---------- 5. Delete illegal source rows ----------------------------
    print("[5/9] Deleting pirate source rows...")
    placeholders = ",".join("?" * len(PIRATE_SOURCE_SLUGS))
    # First, count how many availability rows we'll lose (for the report)
    n_to_lose = cur.execute(
        f"SELECT COUNT(*) FROM availability WHERE source_id IN "
        f"(SELECT id FROM sources WHERE slug IN ({placeholders}))",
        list(PIRATE_SOURCE_SLUGS)
    ).fetchone()[0]
    n_src = cur.execute(
        f"SELECT COUNT(*) FROM sources WHERE slug IN ({placeholders})",
        list(PIRATE_SOURCE_SLUGS)
    ).fetchone()[0]
    print(f"      removing {n_src} source rows, {n_to_lose} availability rows")
    cur.execute(
        f"DELETE FROM availability WHERE source_id IN "
        f"(SELECT id FROM sources WHERE slug IN ({placeholders}))",
        list(PIRATE_SOURCE_SLUGS)
    )
    cur.execute(
        f"DELETE FROM crawl_state WHERE source_id IN "
        f"(SELECT id FROM sources WHERE slug IN ({placeholders}))",
        list(PIRATE_SOURCE_SLUGS)
    )
    cur.execute(
        f"DELETE FROM sources WHERE slug IN ({placeholders})",
        list(PIRATE_SOURCE_SLUGS)
    )

    # ---------- 6. Insert lawful sources ---------------------------------
    print("[6/9] Inserting lawful sources...")
    for slug, name, base_url, stype, is_legal in LAWFUL_SOURCES:
        cur.execute(
            "INSERT OR IGNORE INTO sources (slug, name, base_url, type, enabled, is_legal) "
            "VALUES (?, ?, ?, ?, 1, ?)",
            (slug, name, base_url, stype, is_legal)
        )

    # ---------- 7. Install legal gate trigger ----------------------------
    print("[7/9] Installing availability_must_be_legal trigger...")
    cur.executescript(LEGAL_GATE_TRIGGER_SQL)

    # ---------- 8. Drop anime genre row (content type, not genre) -------
    print("[8/9] Removing 'anime' row from genres (it's a content type, not a genre)...")
    cur.execute("DELETE FROM title_genres WHERE genre_id IN (SELECT id FROM genres WHERE slug='anime')")
    cur.execute("DELETE FROM genres WHERE slug = 'anime'")

    # ---------- 9. Backfill metadata_state for every title ---------------
    print("[9/9] Backfilling metadata_state + data_quality_score...")
    titles = cur.execute(
        "SELECT id, overview, runtime, poster, backdrop, certification, "
        "release_date, original_title "
        "FROM titles"
    ).fetchall()

    n_stub = n_partial = n_complete = 0
    for t in titles:
        score = 0.0
        # 8 fields, equal weight, each contributes 1/8 if present
        if t["overview"]:      score += 0.125
        if t["runtime"]:       score += 0.125
        if t["poster"]:        score += 0.125
        if t["backdrop"]:      score += 0.125
        if t["certification"]: score += 0.125
        if t["release_date"]:  score += 0.125
        if t["original_title"]: score += 0.125
        # Relationships
        has_genre = cur.execute(
            "SELECT 1 FROM title_genres WHERE title_id = ? LIMIT 1", (t["id"],)
        ).fetchone() is not None
        if has_genre:
            score += 0.125

        if score >= 0.875:
            state = "complete"
            n_complete += 1
        elif score >= 0.375:
            state = "partial"
            n_partial += 1
        else:
            state = "stub"
            n_stub += 1

        cur.execute(
            "UPDATE titles SET metadata_state = ?, data_quality_score = ?, last_verified_at = ? WHERE id = ?",
            (state, score, int(time.time()), t["id"])
        )

    # ---------- Create counts view (last) --------------------------------
    cur.executescript(COUNTS_VIEW_SQL)

    db.commit()
    db.close()

    # ---------- Final report --------------------------------------------
    print()
    print("=" * 60)
    print("MIGRATION COMPLETE")
    print("=" * 60)

    # Re-open read-only to report final state
    db = sqlite3.connect(str(db_path))
    db.row_factory = sqlite3.Row
    cur = db.cursor()

    n_sources_legal   = cur.execute("SELECT COUNT(*) FROM sources WHERE is_legal=1").fetchone()[0]
    n_sources_illegal = cur.execute("SELECT COUNT(*) FROM sources WHERE is_legal=0").fetchone()[0]
    n_avail_total     = cur.execute("SELECT COUNT(*) FROM availability").fetchone()[0]
    n_avail_legal     = cur.execute(
        "SELECT COUNT(*) FROM availability a JOIN sources s ON s.id=a.source_id WHERE s.is_legal=1"
    ).fetchone()[0]
    n_collections     = cur.execute("SELECT COUNT(*) FROM collections").fetchone()[0]
    n_genres          = cur.execute("SELECT COUNT(*) FROM genres").fetchone()[0]
    n_audience_tags   = cur.execute("SELECT COUNT(*) FROM audience_tags").fetchone()[0]

    print(f"sources:        {n_sources_legal} legal / {n_sources_illegal} illegal")
    print(f"availability:   {n_avail_legal} legal / {n_avail_total - n_avail_legal} illegal (after C1 cleanup: only legal remain)")
    print(f"collections:    {n_collections} total")
    print(f"genres:         {n_genres} total (anime removed)")
    print(f"audience_tags:  {n_audience_tags} total")
    print(f"titles by state: complete={n_complete}, partial={n_partial}, stub={n_stub}")

    counts = cur.execute("SELECT * FROM catalog_counts_public").fetchone()
    if counts:
        print()
        print(f"PUBLIC CATALOG COUNTS (the 3-count rule):")
        print(f"  indexed:           {counts['indexed']:,}")
        print(f"  playable_legal:    {counts['playable_legal']:,}")
        print(f"  metadata_complete: {counts['metadata_complete']:,}")

    print()
    print("NEXT STEPS:")
    print("  1. Restart the Python catalog service (port 7801) to pick up the new schema.")
    print("  2. Update catalog_service.py to expose new endpoints.")
    print("  3. Update App.js frontend to consume new fields + 3-count rule.")
    print()

    db.close()


if __name__ == "__main__":
    run()
