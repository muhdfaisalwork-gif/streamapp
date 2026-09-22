"""
catalog_schema.py — Normalized multi-facet catalog schema (Phase 2)

One canonical title record. Many relationships. Many availability records.
No duplication across categorization paths.

Tables:
  sources           - registry of stream sources
  titles            - canonical movie/show record (one row per unique title)
  title_genres      - junction: title x genre
  title_countries   - junction: title x production country
  title_languages   - junction: title x spoken language
  title_audio_languages    - available dubbing languages
  title_subtitle_languages - available subtitle languages
  title_collections - junction: title x collection/franchise
  title_aka         - alternative/localized titles
  seasons           - TV season metadata
  episodes          - TV episode metadata
  availability      - per-source availability for a title (separates meta from playback)
  genres            - canonical genre list
  countries         - canonical country list
  languages         - canonical language list
  collections       - canonical collection/franchise list
  crawl_state       - per-source freshness tracking
  ingest_log        - per-source ingest audit (new, updated, rejected, duplicates)
  user_watchlist    - per-user watchlist (when auth lands)
  user_history      - per-user viewing history (when auth lands)
"""
from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import Iterable

SCHEMA_SQL = """
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA foreign_keys = ON;

-- Canonical genre list (taxonomy) ----------------------------------
CREATE TABLE IF NOT EXISTS genres (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  slug        TEXT NOT NULL UNIQUE,         -- action, sci-fi, science-fiction
  name        TEXT NOT NULL UNIQUE,         -- "Action", "Science Fiction" (canonical)
  name_aliases TEXT NOT NULL DEFAULT '[]',  -- JSON list of accepted variants
  parent_id   INTEGER REFERENCES genres(id),
  sort_order  INTEGER NOT NULL DEFAULT 100,
  created_at  INTEGER NOT NULL DEFAULT (strftime('%s','now'))
);

-- Canonical country list ------------------------------------------
CREATE TABLE IF NOT EXISTS countries (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  code        TEXT NOT NULL UNIQUE,         -- ISO 3166-1 alpha-2
  name        TEXT NOT NULL UNIQUE,
  flag        TEXT,                         -- emoji
  region      TEXT,                         -- asia, europe, americas, africa, oceania
  sort_order  INTEGER NOT NULL DEFAULT 100
);

-- Canonical language list -----------------------------------------
CREATE TABLE IF NOT EXISTS languages (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  code        TEXT NOT NULL UNIQUE,         -- ISO 639-1
  name        TEXT NOT NULL UNIQUE,
  native_name TEXT,
  flag        TEXT
);

-- Canonical collection/franchise list -------------------------------
CREATE TABLE IF NOT EXISTS collections (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  slug        TEXT NOT NULL UNIQUE,         -- marvel-cinematic-universe, star-wars
  name        TEXT NOT NULL UNIQUE,         -- "Marvel Cinematic Universe"
  type        TEXT NOT NULL DEFAULT 'franchise', -- franchise, universe, saga, brand
  poster      TEXT,
  backdrop    TEXT,
  overview    TEXT,
  sort_order  INTEGER NOT NULL DEFAULT 100
);

-- Canonical title record -------------------------------------------
CREATE TABLE IF NOT EXISTS titles (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  slug            TEXT NOT NULL UNIQUE,             -- URL-safe slug (e.g. "inception-2010")
  title           TEXT NOT NULL,
  original_title  TEXT,
  type            TEXT NOT NULL CHECK(type IN ('movie','tv','anime','short_drama','documentary','special','reality','game_show','talk_show','musical','concert','sport','kids','adult_animation')),
  year            INTEGER,
  release_date    TEXT,
  runtime         INTEGER,                          -- minutes
  certification    TEXT,
  rating          REAL,                             -- 0-10 normalized numeric
  rating_count    INTEGER DEFAULT 0,                -- # votes
  popularity      REAL DEFAULT 0,                    -- internal score
  overview        TEXT,
  tagline         TEXT,
  poster          TEXT,
  backdrop        TEXT,
  trailer_url     TEXT,
  tmdb_id         INTEGER,
  imdb_id         TEXT,
  status          TEXT DEFAULT 'released',          -- released, upcoming, ongoing, ended, returning, canceled
  is_anime        INTEGER NOT NULL DEFAULT 0,        -- 0/1 shortcut for type='anime'
  is_short_drama  INTEGER NOT NULL DEFAULT 0,
  created_at      INTEGER NOT NULL DEFAULT (strftime('%s','now')),
  updated_at      INTEGER NOT NULL DEFAULT (strftime('%s','now'))
);

CREATE INDEX IF NOT EXISTS idx_titles_type ON titles(type);
CREATE INDEX IF NOT EXISTS idx_titles_year ON titles(year);
CREATE INDEX IF NOT EXISTS idx_titles_rating ON titles(rating);
CREATE INDEX IF NOT EXISTS idx_titles_status ON titles(status);
CREATE INDEX IF NOT EXISTS idx_titles_popularity ON titles(popularity);
CREATE INDEX IF NOT EXISTS idx_titles_tmdb ON titles(tmdb_id);
CREATE INDEX IF NOT EXISTS idx_titles_imdb ON titles(imdb_id);
CREATE INDEX IF NOT EXISTS idx_titles_slug ON titles(slug);

-- Junction tables ---------------------------------------------------
CREATE TABLE IF NOT EXISTS title_genres (
  title_id    INTEGER NOT NULL REFERENCES titles(id) ON DELETE CASCADE,
  genre_id    INTEGER NOT NULL REFERENCES genres(id) ON DELETE CASCADE,
  PRIMARY KEY (title_id, genre_id)
);
CREATE INDEX IF NOT EXISTS idx_tg_genre ON title_genres(genre_id);

CREATE TABLE IF NOT EXISTS title_countries (
  title_id    INTEGER NOT NULL REFERENCES titles(id) ON DELETE CASCADE,
  country_id  INTEGER NOT NULL REFERENCES countries(id) ON DELETE CASCADE,
  PRIMARY KEY (title_id, country_id)
);
CREATE INDEX IF NOT EXISTS idx_tc_country ON title_countries(country_id);

CREATE TABLE IF NOT EXISTS title_languages (
  title_id    INTEGER NOT NULL REFERENCES titles(id) ON DELETE CASCADE,
  language_id INTEGER NOT NULL REFERENCES languages(id) ON DELETE CASCADE,
  is_original INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (title_id, language_id)
);
CREATE INDEX IF NOT EXISTS idx_tl_language ON title_languages(language_id);

CREATE TABLE IF NOT EXISTS title_audio_languages (
  title_id    INTEGER NOT NULL REFERENCES titles(id) ON DELETE CASCADE,
  language_id INTEGER NOT NULL REFERENCES languages(id) ON DELETE CASCADE,
  PRIMARY KEY (title_id, language_id)
);

CREATE TABLE IF NOT EXISTS title_subtitle_languages (
  title_id    INTEGER NOT NULL REFERENCES titles(id) ON DELETE CASCADE,
  language_id INTEGER NOT NULL REFERENCES languages(id) ON DELETE CASCADE,
  PRIMARY KEY (title_id, language_id)
);

CREATE TABLE IF NOT EXISTS title_collections (
  title_id      INTEGER NOT NULL REFERENCES titles(id) ON DELETE CASCADE,
  collection_id INTEGER NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
  PRIMARY KEY (title_id, collection_id)
);
CREATE INDEX IF NOT EXISTS idx_tcc_collection ON title_collections(collection_id);

-- Alternative titles -------------------------------------------------
CREATE TABLE IF NOT EXISTS title_aka (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  title_id    INTEGER NOT NULL REFERENCES titles(id) ON DELETE CASCADE,
  aka_title   TEXT NOT NULL,
  language_id INTEGER REFERENCES languages(id),     -- NULL = unspecified language
  region      TEXT                                 -- IN, KR, JP, etc.
);
CREATE INDEX IF NOT EXISTS idx_aka_title ON title_aka(title_id);
CREATE INDEX IF NOT EXISTS idx_aka_aka ON title_aka(aka_title);

-- TV seasons/episodes ----------------------------------------------
CREATE TABLE IF NOT EXISTS seasons (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  title_id     INTEGER NOT NULL REFERENCES titles(id) ON DELETE CASCADE,
  season_number INTEGER NOT NULL,
  name         TEXT,
  overview     TEXT,
  poster       TEXT,
  air_date     TEXT,
  episode_count INTEGER DEFAULT 0,
  UNIQUE(title_id, season_number)
);
CREATE INDEX IF NOT EXISTS idx_seasons_title ON seasons(title_id);

CREATE TABLE IF NOT EXISTS episodes (
  id             INTEGER PRIMARY KEY AUTOINCREMENT,
  season_id      INTEGER NOT NULL REFERENCES seasons(id) ON DELETE CASCADE,
  episode_number INTEGER NOT NULL,
  title          TEXT,
  overview       TEXT,
  thumbnail      TEXT,
  air_date       TEXT,
  runtime        INTEGER,
  UNIQUE(season_id, episode_number)
);
CREATE INDEX IF NOT EXISTS idx_episodes_season ON episodes(season_id);

-- Sources + availability -------------------------------------------
CREATE TABLE IF NOT EXISTS sources (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  slug        TEXT NOT NULL UNIQUE,           -- "movieboxhd", "yts", "curated"
  name        TEXT NOT NULL,                  -- "MovieBox HD"
  base_url    TEXT,
  type        TEXT NOT NULL DEFAULT 'scraper', -- scraper, aggregator, public
  enabled     INTEGER NOT NULL DEFAULT 1,
  is_legal    INTEGER NOT NULL DEFAULT 0,     -- lawful-source flag
  created_at  INTEGER NOT NULL DEFAULT (strftime('%s','now'))
);

CREATE TABLE IF NOT EXISTS availability (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  title_id        INTEGER NOT NULL REFERENCES titles(id) ON DELETE CASCADE,
  source_id       INTEGER NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
  status          TEXT NOT NULL DEFAULT 'available', -- available, unavailable, coming_soon, expired, unknown
  external_id     TEXT,                       -- source's own ID for this title
  external_url    TEXT,
  quality_options TEXT NOT NULL DEFAULT '[]', -- ["1080p","720p"]
  format_options  TEXT NOT NULL DEFAULT '[]', -- ["embed","hls","mp4"]
  last_checked_at INTEGER,
  last_success_at INTEGER,
  UNIQUE(title_id, source_id)
);
CREATE INDEX IF NOT EXISTS idx_avail_status ON availability(status);
CREATE INDEX IF NOT EXISTS idx_avail_source ON availability(source_id);

-- Ingest audit ----------------------------------------------------
CREATE TABLE IF NOT EXISTS ingest_log (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  source_id    INTEGER NOT NULL REFERENCES sources(id),
  ran_at       INTEGER NOT NULL DEFAULT (strftime('%s','now')),
  new_records  INTEGER NOT NULL DEFAULT 0,
  updated_records INTEGER NOT NULL DEFAULT 0,
  rejected_records INTEGER NOT NULL DEFAULT 0,
  duplicates   INTEGER NOT NULL DEFAULT 0,
  errors       INTEGER NOT NULL DEFAULT 0,
  notes        TEXT
);

-- Per-source freshness --------------------------------------------
CREATE TABLE IF NOT EXISTS crawl_state (
  source_id       INTEGER PRIMARY KEY REFERENCES sources(id) ON DELETE CASCADE,
  total_records   INTEGER DEFAULT 0,
  last_page       INTEGER,
  last_crawled_at INTEGER,
  in_progress     INTEGER DEFAULT 0
);

-- User state (placeholder until auth ships) -----------------------
CREATE TABLE IF NOT EXISTS user_watchlist (
  user_id     TEXT NOT NULL,
  title_id    INTEGER NOT NULL REFERENCES titles(id) ON DELETE CASCADE,
  added_at    INTEGER NOT NULL DEFAULT (strftime('%s','now')),
  PRIMARY KEY (user_id, title_id)
);

CREATE TABLE IF NOT EXISTS user_history (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id     TEXT NOT NULL,
  title_id    INTEGER NOT NULL REFERENCES titles(id) ON DELETE CASCADE,
  episode_id  INTEGER REFERENCES episodes(id) ON DELETE SET NULL,
  position_sec INTEGER,
  duration_sec INTEGER,
  pct         REAL,
  completed   INTEGER DEFAULT 0,
  ts          INTEGER NOT NULL DEFAULT (strftime('%s','now'))
);
CREATE INDEX IF NOT EXISTS idx_uhistory_user_ts ON user_history(user_id, ts DESC);
CREATE INDEX IF NOT EXISTS idx_uhistory_title ON user_history(title_id);
"""

# Canonical taxonomies (single source of truth) ----------------------
CANONICAL_GENRES = [
    ("action", "Action", ["act"]),
    ("adventure", "Adventure", ["adv"]),
    ("animation", "Animation", ["animated"]),
    ("biography", "Biography", ["bio"]),
    ("comedy", "Comedy", []),
    ("crime", "Crime", []),
    ("documentary", "Documentary", ["doc"]),
    ("drama", "Drama", []),
    ("family", "Family", ["kids"]),
    ("fantasy", "Fantasy", []),
    ("history", "History", ["historical"]),
    ("horror", "Horror", []),
    ("music", "Music", ["musical"]),
    ("musical", "Musical", []),
    ("mystery", "Mystery", ["myst"]),
    ("romance", "Romance", []),
    ("science-fiction", "Science Fiction", ["sci-fi", "scifi", "sci fi", "sf"]),
    ("sport", "Sport", ["sports"]),
    ("thriller", "Thriller", []),
    ("war", "War", []),
    ("western", "Western", []),
    ("film-noir", "Film-Noir", ["noir"]),
    ("reality", "Reality", ["reality-tv"]),
    ("game-show", "Game Show", ["game_show"]),
    ("talk-show", "Talk Show", ["talk_show"]),
    ("news", "News", []),
    ("short", "Short", ["short-film"]),
    ("anime", "Anime", ["animation-japanese"]),
]

CANONICAL_COUNTRIES = [
    ("US", "United States", "🇺🇸", "americas"),
    ("GB", "United Kingdom", "🇬🇧", "europe"),
    ("KR", "South Korea", "🇰🇷", "asia"),
    ("JP", "Japan", "🇯🇵", "asia"),
    ("CN", "China", "🇨🇳", "asia"),
    ("IN", "India", "🇮🇳", "asia"),
    ("PK", "Pakistan", "🇵🇰", "asia"),
    ("BD", "Bangladesh", "🇧🇩", "asia"),
    ("ID", "Indonesia", "🇮🇩", "asia"),
    ("TH", "Thailand", "🇹🇭", "asia"),
    ("MY", "Malaysia", "🇲🇾", "asia"),
    ("PH", "Philippines", "🇵🇭", "asia"),
    ("TR", "Turkey", "🇹🇷", "asia"),
    ("NG", "Nigeria", "🇳🇬", "africa"),
    ("EG", "Egypt", "🇪🇬", "africa"),
    ("MA", "Morocco", "🇲🇦", "africa"),
    ("SA", "Saudi Arabia", "🇸🇦", "asia"),
    ("LB", "Lebanon", "🇱🇧", "asia"),
    ("IQ", "Iraq", "🇮🇶", "asia"),
    ("SY", "Syria", "🇸🇾", "asia"),
    ("CI", "Ivory Coast", "🇨🇮", "africa"),
    ("KE", "Kenya", "🇰🇪", "africa"),
    ("ZA", "South Africa", "🇿🇦", "africa"),
    ("FR", "France", "🇫🇷", "europe"),
    ("DE", "Germany", "🇩🇪", "europe"),
    ("IT", "Italy", "🇮🇹", "europe"),
    ("ES", "Spain", "🇪🇸", "europe"),
    ("MX", "Mexico", "🇲🇽", "americas"),
    ("RU", "Russia", "🇷🇺", "europe"),
]

CANONICAL_LANGUAGES = [
    ("en", "English", "English", "🇺🇸"),
    ("es", "Spanish", "Español", "🇪🇸"),
    ("fr", "French", "Français", "🇫🇷"),
    ("de", "German", "Deutsch", "🇩🇪"),
    ("it", "Italian", "Italiano", "🇮🇹"),
    ("pt", "Portuguese", "Português", "🇵🇹"),
    ("ja", "Japanese", "日本語", "🇯🇵"),
    ("ko", "Korean", "한국어", "🇰🇷"),
    ("zh", "Chinese", "中文", "🇨🇳"),
    ("hi", "Hindi", "हिन्दी", "🇮🇳"),
    ("ur", "Urdu", "اردو", "🇵🇰"),
    ("ar", "Arabic", "العربية", "🇸🇦"),
    ("tr", "Turkish", "Türkçe", "🇹🇷"),
    ("ru", "Russian", "Русский", "🇷🇺"),
    ("bn", "Bengali", "বাংলা", "🇧🇩"),
    ("ta", "Tamil", "தமிழ்", "🇮🇳"),
    ("te", "Telugu", "తెలుగు", "🇮🇳"),
    ("ml", "Malayalam", "മലയാളം", "🇮🇳"),
    ("kn", "Kannada", "ಕನ್ನಡ", "🇮🇳"),
    ("pa", "Punjabi", "ਪੰਜਾਬੀ", "🇮🇳"),
    ("fa", "Persian", "فارسی", "🇮🇷"),
    ("id", "Indonesian", "Bahasa Indonesia", "🇮🇩"),
    ("tl", "Filipino", "Filipino", "🇵🇭"),
]

CANONICAL_COLLECTIONS = [
    ("marvel-cinematic-universe", "Marvel Cinematic Universe", "universe"),
    ("dc-extended-universe", "DC Extended Universe", "universe"),
    ("star-wars", "Star Wars", "franchise"),
    ("harry-potter", "Harry Potter", "franchise"),
    ("lord-of-the-rings", "Lord of the Rings", "franchise"),
    ("fast-and-furious", "Fast & Furious", "franchise"),
    ("mission-impossible", "Mission: Impossible", "franchise"),
    ("jurassic-park", "Jurassic Park", "franchise"),
    ("pixar", "Pixar", "brand"),
    ("disney", "Disney", "brand"),
    ("anime-shonen", "Shonen Anime", "genre"),
    ("anime-isekai", "Isekai Anime", "genre"),
    ("k-drama", "K-Drama", "region"),
    ("c-drama", "C-Drama", "region"),
    ("j-drama", "J-Drama", "region"),
    ("turkish-dizi", "Turkish Dizi", "region"),
    ("anime-english-dub", "Anime English Dub", "language"),
    ("anime-hindi-dub", "Anime Hindi Dub", "language"),
    ("anime-arabic-dub", "Anime Arabic Dub", "language"),
    ("short-drama-romance", "Short Drama Romance", "genre"),
    ("short-drama-revenge", "Short Drama Revenge", "genre"),
    ("short-drama-billionaire", "Short Drama Billionaire", "genre"),
    ("short-drama-chinese", "Chinese Short Drama", "region"),
    ("short-drama-korean", "Korean Short Drama", "region"),
    ("short-drama-hindi", "Hindi Short Drama", "region"),
]

CANONICAL_SOURCES = [
    ("curated", "Curated Catalog", None, "curated", 1, 1),
    ("movieboxhd", "MovieBoxHD", "https://movieboxhd.net", "scraper", 1, 0),
    ("beetv", "BeeTV", "https://beetvs.com.co", "scraper", 1, 0),
    ("hdobox", "HDO Box", "https://hdoboxapkpro.com", "scraper", 1, 0),
    ("onstream", "OnStream", None, "scraper", 1, 0),
    ("123movies", "123Movies", "https://123moviesweb.org", "scraper", 1, 0),
    ("yts", "YTS", "https://yts.mx", "scraper", 1, 0),
    ("yify", "YIFY", "https://yify.pro", "scraper", 1, 0),
    ("tmovies", "TMovies", "https://tmovies.co", "scraper", 1, 0),
    ("donkey", "Donkey", "https://donkey.to", "scraper", 1, 0),
    ("uflix", "UFlix", None, "scraper", 1, 0),
    ("vidsrc", "VidSrc.me", "https://vidsrc.me", "embed", 1, 1),
    ("superembed", "SuperEmbed", "https://multiembed.mov", "embed", 1, 1),
    ("2embed", "2Embed", "https://www.2embed.cc", "embed", 1, 1),
]


def init_catalog(db_path: str | Path) -> sqlite3.Connection:
    """Create the catalog database with normalized schema and seed taxonomies."""
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.executescript(SCHEMA_SQL)

    cur = conn.cursor()

    # Seed genres
    cur.executemany(
        "INSERT OR IGNORE INTO genres (slug, name, name_aliases) VALUES (?, ?, ?)",
        [(slug, name, str(aliases).replace("'", '"')) for slug, name, aliases in CANONICAL_GENRES]
    )
    # Seed countries
    cur.executemany(
        "INSERT OR IGNORE INTO countries (code, name, flag, region) VALUES (?, ?, ?, ?)",
        CANONICAL_COUNTRIES
    )
    # Seed languages
    cur.executemany(
        "INSERT OR IGNORE INTO languages (code, name, native_name, flag) VALUES (?, ?, ?, ?)",
        CANONICAL_LANGUAGES
    )
    # Seed collections
    cur.executemany(
        "INSERT OR IGNORE INTO collections (slug, name, type) VALUES (?, ?, ?)",
        CANONICAL_COLLECTIONS
    )
    # Seed sources
    cur.executemany(
        "INSERT OR IGNORE INTO sources (slug, name, base_url, type, enabled, is_legal) VALUES (?, ?, ?, ?, ?, ?)",
        CANONICAL_SOURCES
    )

    conn.commit()
    return conn


if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "scraper/catalog.db"
    conn = init_catalog(target)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM genres")
    print(f"genres: {cur.fetchone()[0]}")
    cur.execute("SELECT COUNT(*) FROM countries")
    print(f"countries: {cur.fetchone()[0]}")
    cur.execute("SELECT COUNT(*) FROM languages")
    print(f"languages: {cur.fetchone()[0]}")
    cur.execute("SELECT COUNT(*) FROM collections")
    print(f"collections: {cur.fetchone()[0]}")
    cur.execute("SELECT COUNT(*) FROM sources")
    print(f"sources: {cur.fetchone()[0]}")
    conn.close()
    print(f"Catalog schema initialized at: {target}")
