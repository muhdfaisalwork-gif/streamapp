"""
apply_addendum.py — Create a SEPARATE additional catalog database.

What this does:
  - Creates G:\\streaming app\\scraper\\catalog_addendum.db (NEW file)
  - Touches NOTHING in the existing catalog.db
  - Builds 17 new tables (TEXT slug PKs, no FKs to live DB)
  - Seeds them with the DuckKota omni-images URLs and freekeys repo data
  - Idempotent — re-running is safe (INSERT OR IGNORE / REPLACE)

The addendum can be JOIN'd to the live catalog at the app layer on slug
strings (collections.slug, genres.slug, etc.) when you're ready.

To run:
  cd "G:\\streaming app\\scraper"
  python apply_addendum.py
"""
from __future__ import annotations
import sqlite3
from pathlib import Path

# ---------------------------------------------------------------------------
# Target DB path (NEW file, does not touch the live catalog.db)
# ---------------------------------------------------------------------------
HERE = Path(__file__).parent
TARGET = HERE / "catalog_addendum.db"

OMNI_BASE = "https://gitlab.com/DuckKota/omni-images/-/raw/main"
FREEKEYS  = "https://github.com/rickylawson/freekeys"

# ---------------------------------------------------------------------------
# Schema (TEXT slug PKs; cross-DB JOINs happen on slug, not on integer FKs)
# ---------------------------------------------------------------------------
SCHEMA_SQL = f"""
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;

-- Paid streaming services (where-to-watch reference data, never scraped)
CREATE TABLE IF NOT EXISTS streaming_providers (
  slug            TEXT PRIMARY KEY,
  name            TEXT NOT NULL,
  base_url        TEXT,
  logo_url        TEXT,
  free_access_ref TEXT,
  region          TEXT NOT NULL DEFAULT 'US',
  is_legal        INTEGER NOT NULL DEFAULT 1,
  enabled         INTEGER NOT NULL DEFAULT 0,
  sort_order      INTEGER NOT NULL DEFAULT 100,
  created_at      INTEGER NOT NULL DEFAULT (strftime('%s','now'))
);

-- Production studios (live-action)
CREATE TABLE IF NOT EXISTS studios (
  slug        TEXT PRIMARY KEY,
  name        TEXT NOT NULL,
  logo_url    TEXT,
  country     TEXT,
  sort_order  INTEGER NOT NULL DEFAULT 100
);

-- Animation studios (subset)
CREATE TABLE IF NOT EXISTS animation_studios (
  slug              TEXT PRIMARY KEY,
  name              TEXT NOT NULL,
  logo_url          TEXT,
  parent_studio_slug TEXT,
  sort_order        INTEGER NOT NULL DEFAULT 100
);

-- Decades (1980s-2020s)
CREATE TABLE IF NOT EXISTS decades (
  slug        TEXT PRIMARY KEY,
  label       TEXT NOT NULL,
  start_year  INTEGER NOT NULL,
  end_year    INTEGER NOT NULL,
  poster_url  TEXT,
  sort_order  INTEGER NOT NULL DEFAULT 100
);

-- Home-page facets (wires trending.png)
CREATE TABLE IF NOT EXISTS facets (
  slug        TEXT PRIMARY KEY,
  name        TEXT NOT NULL,
  poster_url  TEXT,
  sort_order  INTEGER NOT NULL DEFAULT 100,
  created_at  INTEGER NOT NULL DEFAULT (strftime('%s','now'))
);

-- Collection/franchise poster images (mapping; live collections.poster
-- column is untouched)
CREATE TABLE IF NOT EXISTS collection_posters (
  collection_slug TEXT PRIMARY KEY,
  poster_url      TEXT NOT NULL
);

-- Genre poster images (live genres table has no poster column)
CREATE TABLE IF NOT EXISTS genre_posters (
  genre_slug TEXT PRIMARY KEY,
  poster_url TEXT NOT NULL
);

-- Free access methods per provider (freekeys repo reference)
CREATE TABLE IF NOT EXISTS free_access_methods (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  provider_slug   TEXT NOT NULL,
  method          TEXT NOT NULL,
  description     TEXT,
  reference_url   TEXT,
  UNIQUE(provider_slug, method, reference_url)
);

-- Country-level production stats (PDF pp.3-8)
CREATE TABLE IF NOT EXISTS country_production (
  country_code             TEXT PRIMARY KEY,
  annual_films_min         INTEGER,
  annual_films_max         INTEGER,
  annual_tv_titles_min     INTEGER,
  annual_tv_titles_max     INTEGER,
  annual_tv_episodes_est   INTEGER,
  annual_hours_est         INTEGER,
  domestic_box_office_pct  TEXT,
  primary_format           TEXT,
  regulatory_body          TEXT,
  production_characteristic TEXT,
  source_pdf_page          TEXT
);

-- Regional broadcast formats
CREATE TABLE IF NOT EXISTS regional_formats (
  slug                  TEXT PRIMARY KEY,
  name                  TEXT NOT NULL,
  origin_country_code   TEXT,
  description           TEXT,
  typical_episode_count TEXT,
  typical_runtime_min   INTEGER,
  source_pdf_page       TEXT
);

-- Animation production centers
CREATE TABLE IF NOT EXISTS animation_centers (
  id                INTEGER PRIMARY KEY AUTOINCREMENT,
  country_code      TEXT NOT NULL,
  animation_type    TEXT NOT NULL,
  annual_volume_min INTEGER,
  annual_volume_max INTEGER,
  leading_studios   TEXT,
  source_pdf_page   TEXT,
  UNIQUE(country_code, animation_type)
);

-- Global audiovisual format statistics
CREATE TABLE IF NOT EXISTS global_format_stats (
  format_key            TEXT PRIMARY KEY,
  display_name          TEXT NOT NULL,
  estimated_volume      INTEGER NOT NULL,
  share_pct             REAL NOT NULL,
  structural_definition TEXT,
  primary_source        TEXT,
  source_pdf_page       TEXT
);

-- Actor roster (mirrors live 'people' rows for actors)
CREATE TABLE IF NOT EXISTS actors (
  slug        TEXT PRIMARY KEY,
  name        TEXT NOT NULL,
  photo_url   TEXT,
  birth_year  INTEGER,
  nationality TEXT,
  sort_order  INTEGER NOT NULL DEFAULT 100
);

-- Director roster
CREATE TABLE IF NOT EXISTS directors (
  slug        TEXT PRIMARY KEY,
  name        TEXT NOT NULL,
  photo_url   TEXT,
  birth_year  INTEGER,
  nationality TEXT,
  sort_order  INTEGER NOT NULL DEFAULT 100
);

-- Title <-> Actor junction (mirrors live title_cast, but keyed by slug)
CREATE TABLE IF NOT EXISTS title_actors (
  title_slug       TEXT NOT NULL,
  actor_slug       TEXT NOT NULL,
  character_name   TEXT,
  billing_order    INTEGER NOT NULL DEFAULT 100,
  role_type        TEXT NOT NULL DEFAULT 'cast',
  PRIMARY KEY (title_slug, actor_slug, role_type)
);

-- Title <-> Director junction (mirrors live title_crew)
CREATE TABLE IF NOT EXISTS title_directors (
  title_slug    TEXT NOT NULL,
  director_slug TEXT NOT NULL,
  role          TEXT NOT NULL DEFAULT 'director',
  PRIMARY KEY (title_slug, director_slug)
);

-- Title <-> Studio junction
CREATE TABLE IF NOT EXISTS title_studios (
  title_slug TEXT NOT NULL,
  studio_slug TEXT NOT NULL,
  role        TEXT NOT NULL DEFAULT 'production',
  PRIMARY KEY (title_slug, studio_slug, role)
);

-- Title <-> Animation studio junction
CREATE TABLE IF NOT EXISTS title_animation_studios (
  title_slug            TEXT NOT NULL,
  animation_studio_slug TEXT NOT NULL,
  role                  TEXT NOT NULL DEFAULT 'animation',
  PRIMARY KEY (title_slug, animation_studio_slug, role)
);

-- Title <-> Streaming provider junction (where-to-watch)
CREATE TABLE IF NOT EXISTS title_streaming_providers (
  title_slug         TEXT NOT NULL,
  provider_slug      TEXT NOT NULL,
  availability_type  TEXT NOT NULL DEFAULT 'subscription',
  region             TEXT NOT NULL DEFAULT 'US',
  deep_link          TEXT,
  free_access_ref    TEXT,
  PRIMARY KEY (title_slug, provider_slug, availability_type, region)
);

CREATE INDEX IF NOT EXISTS idx_tsp_provider  ON title_streaming_providers(provider_slug);
CREATE INDEX IF NOT EXISTS idx_ta_actor      ON title_actors(actor_slug);
CREATE INDEX IF NOT EXISTS idx_td_director   ON title_directors(director_slug);
CREATE INDEX IF NOT EXISTS idx_ts_studio     ON title_studios(studio_slug);
CREATE INDEX IF NOT EXISTS idx_tas_animstudio ON title_animation_studios(animation_studio_slug);
CREATE INDEX IF NOT EXISTS idx_ac_country    ON animation_centers(country_code);
"""


def url(path: str) -> str:
    return f"{OMNI_BASE}/{path}"


# ---------------------------------------------------------------------------
# Data (verbatim from DuckKota omni-images + rickylawson/freekeys)
# ---------------------------------------------------------------------------
STREAMING_PROVIDERS = [
    ("netflix",         "Netflix",         "https://www.netflix.com",        url("streaming_services/netflix.jpg"),         FREEKEYS, "US"),
    ("disney-plus",     "Disney+",         "https://www.disneyplus.com",     url("streaming_services/disney_plus.jpg"),     FREEKEYS, "US"),
    ("prime-video",     "Prime Video",     "https://www.amazon.com/Prime-Video", url("streaming_services/prime_video.jpg"), FREEKEYS, "US"),
    ("apple-tv-plus",   "Apple TV+",       "https://tv.apple.com",           url("streaming_services/apple_tv.jpg"),        FREEKEYS, "US"),
    ("max",             "Max",             "https://www.max.com",            url("streaming_services/max.jpg"),              FREEKEYS, "US"),
    ("hulu",            "Hulu",            "https://www.hulu.com",           url("streaming_services/hulu.jpg"),             FREEKEYS, "US"),
    ("paramount-plus",  "Paramount+",      "https://www.paramountplus.com",  url("streaming_services/paramount_plus.jpg"),  FREEKEYS, "US"),
    ("peacock",         "Peacock",         "https://www.peacocktv.com",      url("streaming_services/peacock.jpg"),          FREEKEYS, "US"),
    ("discovery-plus",  "Discovery+",      "https://www.discoveryplus.com",  url("streaming_services/discovery_plus.jpg"),  FREEKEYS, "US"),
]

GENRE_POSTERS = [
    ("action",          url("genres/action.png")),
    ("adventure",       url("genres/adventure.png")),
    ("animation",       url("genres/animation.png")),
    ("comedy",          url("genres/comedy.png")),
    ("crime",           url("genres/crime.png")),
    ("documentary",     url("genres/documentary.png")),
    ("drama",           url("genres/drama.png")),
    ("fantasy",         url("genres/fantasy.png")),
    ("history",         url("genres/historical.png")),
    ("horror",          url("genres/horror.png")),
    ("musical",         url("genres/musical.png")),
    ("mystery",         url("genres/mystery.png")),
    ("romance",         url("genres/romance.png")),
    ("science-fiction", url("genres/sci-fi.png")),
    ("thriller",        url("genres/thriller.png")),
    ("war",             url("genres/war.png")),
]

COLLECTION_POSTERS = [
    ("avatar",                    url("collections/avatar.png")),
    ("back-to-the-future",        url("collections/back_to_the_future.png")),
    ("dune",                      url("collections/dune.png")),
    ("fast-and-furious",          url("collections/fast_and_furious.png")),
    ("harry-potter",              url("collections/harry_potter.png")),
    ("the-hunger-games",          url("collections/hunger_games.png")),
    ("indiana-jones",             url("collections/indiana_jones.png")),
    ("james-bond",                url("collections/james_bond.png")),
    ("john-wick",                 url("collections/john_wick.png")),
    ("jurassic-park",             url("collections/jurassic_park.png")),
    ("lord-of-the-rings",         url("collections/lord_of_the_rings.png")),
    ("marvel",                    url("collections/marvel.png")),
    ("marvel-universe",           url("collections/marvel.png")),
    ("the-matrix",                url("collections/matrix.png")),
    ("mission-impossible",        url("collections/mission_impossible.png")),
    ("monsterverse",              url("collections/monsterverse.png")),
    ("pirates-of-the-caribbean",  url("collections/pirates_of_the_caribbean.png")),
    ("rambo",                     url("collections/rambo.png")),
    ("rocky-creed",               url("collections/rocky.png")),
    ("star-trek",                 url("collections/star_trek.png")),
    ("star-wars",                 url("collections/star_wars.png")),
    ("transformers",              url("collections/transformers.png")),
    ("x-men",                     url("collections/x_men.png")),
]

STUDIOS = [
    ("warner-bros-pictures", "Warner Bros. Pictures",   url("studios/warner_bros_pictures.png"),  "US"),
    ("walt-disney-pictures", "Walt Disney Pictures",    url("studios/walt_disney_pictures.png"),  "US"),
    ("universal-pictures",  "Universal Pictures",      url("studios/universal_pictures.png"),    "US"),
    ("marvel-studios",      "Marvel Studios",          url("studios/marvel_studios.png"),        "US"),
    ("dc-studios",          "DC Studios",              url("studios/dc_studios.png"),            "US"),
    ("lionsgate",           "Lionsgate",               url("studios/lionsgate.png"),             "US"),
    ("dreamworks-pictures", "DreamWorks Pictures",     url("studios/dreamworks_pictures.png"),   "US"),
]

ANIMATION_STUDIOS = [
    ("pixar",                  "Pixar",                          url("animation_studios/pixar.png"),                  "walt-disney-pictures"),
    ("walt-disney-animation",  "Walt Disney Animation Studios",  url("animation_studios/walt_disney_animation.png"),  "walt-disney-pictures"),
    ("dreamworks-animation",   "DreamWorks Animation",           url("animation_studios/dreamworks_animation.png"),   "dreamworks-pictures"),
    ("illumination",           "Illumination",                   url("animation_studios/illumination.png"),           "universal-pictures"),
    ("sony-pictures-animation","Sony Pictures Animation",       url("animation_studios/sony_pictures_animation.png"), None),
    ("blue-sky-animation",     "Blue Sky Studios",               url("animation_studios/blue_sky_animation.png"),     None),
    ("warner-bros-animation",  "Warner Bros. Animation",         url("animation_studios/warner_bros_animation.png"),  "warner-bros-pictures"),
]

DECADES = [
    ("1980", "1980s", 1980, 1989, url("decades/1980.jpg")),
    ("1990", "1990s", 1990, 1999, url("decades/1990.jpg")),
    ("2000", "2000s", 2000, 2009, url("decades/2000.jpg")),
    ("2010", "2010s", 2010, 2019, url("decades/2010.jpg")),
    ("2020", "2020s", 2020, 2029, url("decades/2020.jpg")),
]

# trending.png is wired HERE — it has no genre slug, so genre_posters
# does not accept it (FK would fail). facets table is its home.
FACETS = [
    ("trending",      "Trending Now",    url("genres/trending.png"),     10),
    ("new_releases",  "New Releases",    None,                           20),
    ("top_rated",     "Top Rated",       None,                           30),
    ("most_popular",  "Most Popular",    None,                           40),
    ("coming_soon",   "Coming Soon",     None,                           50),
    ("free_to_watch", "Free to Watch",   None,                           60),
]

ACTORS = [
    ("adam_sandler",         "Adam Sandler",           url("actors/adam_sandler.jpg"),         1966, "US"),
    ("arnold_schwarzenegger","Arnold Schwarzenegger",  url("actors/arnold_schwarzenegger.jpg"),1947, "AT"),
    ("christian_bale",       "Christian Bale",         url("actors/christian_bale.jpg"),       1974, "GB"),
    ("clint_eastwood",       "Clint Eastwood",         url("actors/clint_eastwood.jpg"),       1930, "US"),
    ("denzel_washington",    "Denzel Washington",      url("actors/denzel_washington.jpg"),    1954, "US"),
    ("dwayne_johnson",       "Dwayne Johnson",         url("actors/dwayne_johnson.jpg"),       1972, "US"),
    ("harrison_ford",        "Harrison Ford",          url("actors/harrison_ford.jpg"),        1942, "US"),
    ("jackie_chan",          "Jackie Chan",            url("actors/jackie_chan.jpg"),          1954, "HK"),
    ("jason_statham",        "Jason Statham",          url("actors/jason_statham.jpg"),        1967, "GB"),
    ("matt_damon",           "Matt Damon",             url("actors/matt_damon.jpg"),           1970, "US"),
    ("morgan_freeman",       "Morgan Freeman",         url("actors/morgan_freeman.jpg"),       1937, "US"),
    ("nicolas_cage",         "Nicolas Cage",           url("actors/nicolas_cage.jpg"),         1964, "US"),
    ("robert_downey_jr",     "Robert Downey Jr.",      url("actors/robert_downey_jr.jpg"),     1965, "US"),
    ("robin_williams",       "Robin Williams",         url("actors/robin_williams.jpg"),       1951, "US"),
    ("ryan_reynolds",        "Ryan Reynolds",          url("actors/ryan_reynolds.jpg"),        1976, "CA"),
    ("samuel_l_jackson",     "Samuel L. Jackson",      url("actors/samuel_l_jackson.jpg"),     1948, "US"),
    ("sylvester_stallone",   "Sylvester Stallone",     url("actors/sylvester_stallone.jpg"),   1946, "US"),
    ("tom_cruise",           "Tom Cruise",             url("actors/tom_cruise.jpg"),           1962, "US"),
]

DIRECTORS = [
    ("alfred_hitchcock",       "Alfred Hitchcock",     url("directors/alfred_hitchcock.jpg"),       1899, "GB"),
    ("brian_de_palma",         "Brian De Palma",       url("directors/brian_de_palma.jpg"),         1940, "US"),
    ("christopher_nolan",      "Christopher Nolan",    url("directors/christopher_nolan.jpg"),      1970, "GB"),
    ("david_fincher",          "David Fincher",        url("directors/david_fincher.jpg"),          1962, "US"),
    ("denis_villeneuve",       "Denis Villeneuve",     url("directors/denis_villeneuve.jpg"),       1967, "CA"),
    ("john_carpenter",         "John Carpenter",       url("directors/john_carpenter.jpg"),         1948, "US"),
    ("martin_scorsese",        "Martin Scorsese",      url("directors/martin_scorsese.jpg"),        1942, "US"),
    ("paul_thomas_anderson",   "Paul Thomas Anderson", url("directors/paul_thomas_anderson.jpg"),   1970, "US"),
    ("stanley_kubrick",        "Stanley Kubrick",      url("directors/stanley_kubrick.jpg"),        1928, "US"),
    # NOTE: source URL had a typo ("speilberg"); preserved as-is in the
    # image filename but corrected in the human-readable name.
    ("steven_spielberg",       "Steven Spielberg",     url("directors/steven_speilberg.jpg"),       1946, "US"),
]

COUNTRY_PRODUCTION = [
    # (country_code, films_min, films_max, tv_titles_min, tv_titles_max,
    #  tv_eps_est, hours_est, dom_box_pct, primary_format,
    #  regulatory_body, characteristic, source_pdf_page)
    ("IN",    1800, 2500, None, None, None, None, "~90%",  None,
     "Central Board of Film Certification (CBFC)",
     "Multilingual private commercial film industries",
     "pp.3-4"),
    ("NG",    1200, 2500, None, None, None, None, ">95%",  None,
     "National Film and Video Censors Board (NFVCB)",
     "Direct-to-digital / informal video commerce (Nollywood)",
     "pp.3-4"),
    ("CN",    700,  1050, None, None, None, None, "~74%",  None,
     "National Radio and Television Administration (NRTA)",
     "State-backed enterprises and major private tech studios",
     "pp.3,5"),
    ("US",    600,  800,  400,  600,  None, 7000, "~52% (Global share)",
     "limited_series_prestige",
     "Motion Picture Association (MPA)",
     "Studio conglomerates, private equity, streaming slates",
     "pp.3,8"),
    ("JP",    500,  650,  None, None, None, None, "~76%",  None,
     "Motion Picture Producers Association of Japan (EIREN)",
     "Studio-distributor consortia and production committees",
     "pp.3-4"),
    ("IT",    300,  360,  None, None, None, None, "~20-30%", None,
     "Direzione Generale Cinema e Audiovisivo (DGCA)",
     "Direct public subsidies, selective tax credits, TV presales",
     "p.4"),
    ("ES",    280,  320,  None, None, None, None, "~15-25%", None,
     "Instituto de la Cinematografía y de las Artes Audiovisuales",
     "Regional tax incentives, European co-productions",
     "p.4"),
    ("FR",    230,  280,  None, None, None, None, "~35-40%", None,
     "Centre National du Cinéma et de l'image animée (CNC)",
     "Mandatory broadcaster reinvestment and CNC levies",
     "p.4"),
    ("GB",    220,  270,  None, None, None, None, "~15-30%", None,
     "British Film Institute (BFI)",
     "Inward studio investment, National Lottery support",
     "p.4"),
    ("KR",    200,  260,  None, None, None, None, "~50-60%", None,
     "Korean Film Council (KOFIC)",
     "Conglomerate financing, theatrical-streaming windows",
     "p.4"),
    ("TR",    350,  450,  50,   70,   None, None, "~45-60%", "dizi",
     "RTÜK / Turkish Radio and Television Supreme Council",
     "World's 2nd largest scripted TV exporter; $600M+ global distribution revenue",
     "pp.5,7"),
    ("ID",    180,  240,  80,   80,   2000, None, ">60%",   "sinetron",
     "Indonesian Film Censorship Board (LSF)",
     "Largest SE Asian cinema market; 80M+ tickets/yr; daily sinetron serial production",
     "pp.5,7"),
    ("PK",    25,   45,   150,  250,  None, None, "~25-35%", "finite_drama_serial",
     "Pakistan Electronic Media Regulatory Authority (PEMRA)",
     "High-prestige scripted serials; 20-35 ep finite runs; emerging theatrical revival",
     "pp.5,8"),
    ("PH",    120,  180,  80,   120,  None, None, "~30-45%", "teleserye",
     "MTRCB",
     "Prolific commercial studio sector; multi-hundred episode broadcast runs",
     "p.6"),
    ("MX",    100,  140,  100,  100,  None, None, "~10-18%", "telenovela",
     "RTC / Mexican regulatory authority",
     "Latin American broadcast hub (TelevisaUnivision); high-volume telenovela pipelines",
     "p.6"),
    ("BR",    130,  170,  80,   80,   None, None, "~12-20%", "telenovela",
     "ANCINE",
     "High-budget daily serials (TV Globo); internationally syndicated telenovela production",
     "p.6"),
    ("EG",    35,   55,   40,   60,   None, None, "~70-80%", "musalsalat",
     "Egyptian Radio and Television Union (ERTU)",
     "Historical pan-Arab cinematic library (>4,000 features); Ramadan television production center",
     "p.6"),
    ("IR",    90,   130,  30,   50,   None, None, ">80%",   None,
     "Farabi Cinema Foundation / Ministry of Culture",
     "State-regulated cinema via Farabi Cinema Foundation; distinct auteur festival circuit",
     "p.7"),
    ("EU",    1200, 1400, 1200, 1400, 23000,14000, None,
     "high_end_series_telenovela_soap",
     "European Audiovisual Observatory",
     "EU27+UK+Norway+Switzerland; 6% title contraction in 2023, 5% in 2024",
     "p.8"),
    ("LATAM", 250,  400,  250,  400,  None, 9500,  None, "telenovela",
     "Various national regulators",
     "Brazil + Mexico + Colombia; high-volume daily telenovelas (>50 ep runs)",
     "pp.8-9"),
    ("EASIA", 600,  900,  600,  900,  None, 8500,  None,
     "miniseries_16_24_ep_arcs",
     "Various national regulators",
     "S. Korea + Japan + China; miniseries & standardized 16-to-24-episode arcs",
     "p.9"),
]

REGIONAL_FORMATS = [
    ("dizi",       "Dizi",       "TR",
     "Turkish prime-time weekly drama serial; world's 2nd largest scripted TV export category",
     "50-70 new series/year", 135, "p.7"),
    ("sinetron",   "Sinetron",   "ID",
     "Indonesian daily serialized television drama; very long runs (500-1000+ episodes)",
     "Thousands of episodes/year", 60, "p.7"),
    ("telenovela", "Telenovela", "MX",
     "Latin American high-volume daily serial; >50 episode runs; TelevisaUnivision pipeline",
     ">50 ep runs", 45, "pp.6,8"),
    ("teleserye",  "Teleserye",  "PH",
     "Filipino multi-hundred-episode daily serial; commercial studio sector backbone",
     "100s of episodes", 45, "p.6"),
    ("musalsalat", "Musalsalat", "EG",
     "Arabic (Egyptian) serial; heavy Ramadan-cycle production; pan-Arab distribution",
     "40-60 new titles/year", 45, "p.6"),
    ("donghua",    "Donghua",    "CN",
     "Chinese animation; OVA/ONA and theatrical; rivals Japanese anime in domestic market",
     "Variable", 25, "p.10"),
    ("k-drama",    "K-Drama",    "KR",
     "Korean scripted television drama; miniseries & 16-24 episode arcs",
     "16-24 ep arcs", 70, "p.9"),
    ("j-drama",    "J-Drama",    "JP",
     "Japanese scripted drama; production-committee financed",
     "10-12 ep arcs", 50, "p.9"),
    ("c-drama",    "C-Drama",    "CN",
     "Mainland Chinese scripted drama; state broadcaster and tech-conglomerate commissions",
     "Variable", 45, "p.9"),
]

ANIMATION_CENTERS = [
    ("US", "feature_film",   11, 14, "Pixar, Disney Animation, Illumination, DreamWorks Animation", "p.10"),
    ("JP", "feature_film",   11, 14, "Studio Ghibli, Toei, Madhouse, Bones, MAPPA",                  "p.10"),
    ("CN", "feature_film",   11, 14, "Ne Zha studios, domestic adaptations of classical literature", "p.10"),
    ("FR", "feature_film",   11, 14, "Gaumont Animation, Ankama, Mac Guff",                         "p.10"),
    ("JP", "tv_series",      12, 14, "Production committees (Aniplex, Toho, Sunrise, MAPPA)",        "p.10"),
    ("KR", "tv_series",      12, 14, "Outsourcing partner to JP (Studio Mir, SAKUGA)",               "p.10"),
    ("CN", "tv_series",      12, 14, "Bilibili, Tencent Video, iQIYI in-house animation",           "p.10"),
    ("JP", "ova_ona",         7,  9, "OVA/ONA pipeline (Aniplex, KyoAni)",                           "p.10"),
    ("CN", "ova_ona",         7,  9, "Donghua ONA platforms (Bilibili)",                              "p.10"),
    ("FR", "short_film",    150, 200, "Festival-circuit producers (Annecy ecosystem)",                "p.10"),
    ("US", "short_film",    150, 200, "SVA, CalArts, indie animation studios",                         "p.10"),
    ("GB", "short_film",    150, 200, "Aardman, Channel 4 shorts",                                     "p.10"),
    ("CA", "short_film",    150, 200, "NFB (National Film Board), Nelvana shorts",                    "p.10"),
    ("US", "children_series", 8,  12, "Nickelodeon, Disney Channel, PBS Kids",                         "p.10"),
    ("CA", "children_series", 8,  12, "Nelvana, WildBrain, 9 Story",                                    "p.10"),
    ("FR", "children_series", 8,  12, "Gaumont Animation, Xilam, Ankama",                             "p.10"),
    ("GB", "children_series", 8,  12, "Aardman, BBC Children's",                                       "p.10"),
]

GLOBAL_FORMAT_STATS = [
    ("tv_episodes",            "Television Episodes (tvEpisode)",
     23264000, 71.2, "Individual serialized narrative units",
     "Database registries / Broadcast logs", "pp.1-2"),
    ("feature_films",          "Standalone Feature Films (movie)",
     2131000, 7.7, "Narrative / documentary features (>40 min)",
     "Statutory registries / IMDb", "p.2"),
    ("short_films",            "Short Films (short / tvShort)",
     1030000, 3.7, "Non-episodic short works (<=40 min)",
     "Archival vaults / Festival registries", "p.2"),
    ("tv_series",              "Television Series (tvSeries)",
     417000, 1.5, "Multi-episode serialized programs",
     "Network catalogs / IMDb", "p.2"),
    ("direct_to_video",        "Direct-to-Video Releases (video)",
     419000, 1.5, "Home video and non-theatrical physical releases",
     "Consumer software registries", "p.2"),
    ("tv_movies",              "Made-for-Television Films (tvMovie)",
     140000, 0.5, "Single-installment broadcast features",
     "Linear network programming ledgers", "p.2"),
    ("miniseries_specials",    "Miniseries & Specials (tvMiniSeries / tvSpecial)",
     180000, 0.7, "Closed-ended narrative runs and broadcasts",
     "Network logs / Database registries", "p.2"),
    ("ancillary_media",        "Ancillary Media (Video Games, Podcasts, Web)",
     1200000, 4.3, "Interactive software, podcasts, and digital media",
     "Multi-format registries", "p.2"),
    ("uncataloged_ephemeral",  "Uncataloged / Ephemeral Celluloid Holdings",
     2500000, 9.0, "Lost silent films, local newsreels, non-circulating reels",
     "FIAF / National preservation vaults", "p.2"),
]


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------
def main() -> None:
    if TARGET.exists():
        print(f"[addendum] target exists, will be re-initialized: {TARGET}")
    TARGET.unlink(missing_ok=True)

    conn = sqlite3.connect(str(TARGET))
    cur = conn.cursor()
    cur.executescript(SCHEMA_SQL)

    cur.executemany(
        "INSERT OR REPLACE INTO streaming_providers "
        "(slug, name, base_url, logo_url, free_access_ref, region) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        STREAMING_PROVIDERS,
    )
    cur.executemany(
        "INSERT OR REPLACE INTO genre_posters (genre_slug, poster_url) VALUES (?, ?)",
        GENRE_POSTERS,
    )
    cur.executemany(
        "INSERT OR REPLACE INTO collection_posters (collection_slug, poster_url) VALUES (?, ?)",
        COLLECTION_POSTERS,
    )
    cur.executemany(
        "INSERT OR REPLACE INTO studios (slug, name, logo_url, country) VALUES (?, ?, ?, ?)",
        STUDIOS,
    )
    cur.executemany(
        "INSERT OR REPLACE INTO animation_studios "
        "(slug, name, logo_url, parent_studio_slug) VALUES (?, ?, ?, ?)",
        ANIMATION_STUDIOS,
    )
    cur.executemany(
        "INSERT OR REPLACE INTO decades "
        "(slug, label, start_year, end_year, poster_url) VALUES (?, ?, ?, ?, ?)",
        DECADES,
    )
    cur.executemany(
        "INSERT OR REPLACE INTO facets (slug, name, poster_url, sort_order) VALUES (?, ?, ?, ?)",
        FACETS,
    )
    cur.executemany(
        "INSERT OR REPLACE INTO actors (slug, name, photo_url, birth_year, nationality) "
        "VALUES (?, ?, ?, ?, ?)",
        ACTORS,
    )
    cur.executemany(
        "INSERT OR REPLACE INTO directors (slug, name, photo_url, birth_year, nationality) "
        "VALUES (?, ?, ?, ?, ?)",
        DIRECTORS,
    )
    cur.executemany(
        "INSERT OR REPLACE INTO country_production "
        "(country_code, annual_films_min, annual_films_max, "
        " annual_tv_titles_min, annual_tv_titles_max, "
        " annual_tv_episodes_est, annual_hours_est, "
        " domestic_box_office_pct, primary_format, regulatory_body, "
        " production_characteristic, source_pdf_page) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        COUNTRY_PRODUCTION,
    )
    cur.executemany(
        "INSERT OR REPLACE INTO regional_formats "
        "(slug, name, origin_country_code, description, "
        " typical_episode_count, typical_runtime_min, source_pdf_page) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        REGIONAL_FORMATS,
    )
    cur.executemany(
        "INSERT OR REPLACE INTO animation_centers "
        "(country_code, animation_type, annual_volume_min, annual_volume_max, "
        " leading_studios, source_pdf_page) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        ANIMATION_CENTERS,
    )
    cur.executemany(
        "INSERT OR REPLACE INTO global_format_stats "
        "(format_key, display_name, estimated_volume, share_pct, "
        " structural_definition, primary_source, source_pdf_page) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        GLOBAL_FORMAT_STATS,
    )

    # One umbrella free_access row per streaming provider, pointing at
    # the rickylawson/freekeys repo.
    cur.executemany(
        "INSERT OR IGNORE INTO free_access_methods "
        "(provider_slug, method, description, reference_url) "
        "VALUES (?, ?, ?, ?)",
        [
            (slug, "free_trial_key_repo",
             "Free trials / shared keys / student bundles — see rickylawson/freekeys repo",
             FREEKEYS)
            for slug, *_ in STREAMING_PROVIDERS
        ],
    )

    conn.commit()

    # ---- report -----------------------------------------------------------
    print()
    print(f"[addendum] wrote: {TARGET}")
    print()
    print("=== Addendum row counts ===")
    for (t,) in cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ):
        cur.execute("SELECT COUNT(*) FROM " + t)
        print("  " + t.ljust(28) + " " + str(cur.fetchone()[0]))

    print()
    print("=== Sample: streaming providers (with logos) ===")
    for row in cur.execute(
        "SELECT slug, name, logo_url, free_access_ref FROM streaming_providers ORDER BY sort_order"
    ):
        print(f"  {row[0]:18s} {row[1]:18s} {row[2]}")

    print()
    print("=== Sample: facets (trending.png wired) ===")
    for row in cur.execute(
        "SELECT slug, name, poster_url FROM facets ORDER BY sort_order"
    ):
        print(f"  {row[0]:14s} {row[1]:18s} {row[2]}")

    print()
    print("=== Sample: collection_posters (first 5) ===")
    for row in cur.execute(
        "SELECT collection_slug, poster_url FROM collection_posters LIMIT 5"
    ):
        print(f"  {row[0]:30s} {row[1]}")

    print()
    print("=== Live catalog.db row counts (UNTOUCHED) ===")
    live = sqlite3.connect(str(HERE / "catalog.db"))
    lcur = live.cursor()
    for row in lcur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ):
        t = row[0]
        try:
            lcur.execute("SELECT COUNT(*) FROM " + t)
            print("  " + t.ljust(30) + " " + str(lcur.fetchone()[0]))
        except Exception as e:
            print("  " + t.ljust(30) + " ERR: " + str(e))
    live.close()

    conn.close()


if __name__ == "__main__":
    main()
