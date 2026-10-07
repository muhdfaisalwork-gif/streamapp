"""
migrate_people_studios.py — Adds studios / animation_studios / decades /
actors / directors tables (plus their title junction tables) to catalog.db.
These were already defined in catalog_schema.py but never migrated into the
live database — same gap as streaming_providers was before tonight's fix.

Seed data covers exactly the people/studios/decades already wired into the
frontend's categoryAssets.js manifest, using the same TMDB person/company IDs
verified against the live TMDB API earlier this session (4 of 28 person IDs
and 4 of 22 collection/studio IDs were wrong when taken from memory — do not
hand-type new IDs here without verifying them the same way).

Idempotent: safe to run more than once.
"""
from __future__ import annotations
import argparse
import json
import sqlite3

DECADES = [
    ("1980", "1980s", 1980, 1989),
    ("1990", "1990s", 1990, 1999),
    ("2000", "2000s", 2000, 2009),
    ("2010", "2010s", 2010, 2019),
    ("2020", "2020s", 2020, 2029),
]

ACTORS = [
    ("adam-sandler", "Adam Sandler", 19292),
    ("arnold-schwarzenegger", "Arnold Schwarzenegger", 1100),
    ("christian-bale", "Christian Bale", 3894),
    ("clint-eastwood", "Clint Eastwood", 190),
    ("denzel-washington", "Denzel Washington", 5292),
    ("dwayne-johnson", "Dwayne Johnson", 18918),
    ("harrison-ford", "Harrison Ford", 3),
    ("jackie-chan", "Jackie Chan", 18897),
    ("jason-statham", "Jason Statham", 976),
    ("matt-damon", "Matt Damon", 1892),
    ("morgan-freeman", "Morgan Freeman", 192),
    ("nicolas-cage", "Nicolas Cage", 2963),
    ("robert-downey-jr", "Robert Downey Jr.", 3223),
    ("robin-williams", "Robin Williams", 2157),
    ("ryan-reynolds", "Ryan Reynolds", 10859),
    ("samuel-l-jackson", "Samuel L. Jackson", 2231),
    ("sylvester-stallone", "Sylvester Stallone", 16483),
    ("tom-cruise", "Tom Cruise", 500),
]

DIRECTORS = [
    ("alfred-hitchcock", "Alfred Hitchcock", 2636),
    ("brian-de-palma", "Brian De Palma", 1150),
    ("christopher-nolan", "Christopher Nolan", 525),
    ("david-fincher", "David Fincher", 7467),
    ("denis-villeneuve", "Denis Villeneuve", 137427),
    ("john-carpenter", "John Carpenter", 11770),
    ("martin-scorsese", "Martin Scorsese", 1032),
    ("paul-thomas-anderson", "Paul Thomas Anderson", 4762),
    ("stanley-kubrick", "Stanley Kubrick", 240),
    ("steven-spielberg", "Steven Spielberg", 488),
]

STUDIOS = [
    ("dc-studios", "DC Studios", 184898),
    ("dreamworks-pictures", "DreamWorks Pictures", 7),
    ("lionsgate", "Lionsgate", 1632),
    ("marvel-studios", "Marvel Studios", 420),
    ("universal-pictures", "Universal Pictures", 33),
    ("walt-disney-pictures", "Walt Disney Pictures", 2),
    ("warner-bros", "Warner Bros", 174),
]

ANIM_STUDIOS = [
    ("blue-sky-animation", "Blue Sky Animation", 9383),
    ("dreamworks-animation", "DreamWorks Animation", 521),
    ("illumination", "Illumination", 6704),
    ("pixar", "Pixar", 3),
    ("sony-pictures-animation", "Sony Pictures Animation", 2251),
    ("walt-disney-animation", "Walt Disney Animation", 6125),
    ("warner-bros-animation", "Warner Bros Animation", 2785),
]

TABLES_CREATED = [
    "studios", "animation_studios", "decades", "actors", "directors",
    "title_actors", "title_directors", "title_studios", "title_animation_studios",
]


def create_tables(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS studios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL UNIQUE,
            logo_url TEXT,
            tmdb_company_id INTEGER,
            country TEXT,
            founded INTEGER,
            sort_order INTEGER NOT NULL DEFAULT 100,
            created_at INTEGER NOT NULL DEFAULT (strftime('%s','now'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS animation_studios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL UNIQUE,
            logo_url TEXT,
            tmdb_company_id INTEGER,
            parent_studio_id INTEGER REFERENCES studios(id) ON DELETE SET NULL,
            sort_order INTEGER NOT NULL DEFAULT 100,
            created_at INTEGER NOT NULL DEFAULT (strftime('%s','now'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS decades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT NOT NULL UNIQUE,
            label TEXT NOT NULL UNIQUE,
            start_year INTEGER NOT NULL,
            end_year INTEGER NOT NULL,
            poster_url TEXT,
            sort_order INTEGER NOT NULL DEFAULT 100
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS actors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL UNIQUE,
            photo_url TEXT,
            tmdb_person_id INTEGER,
            sort_order INTEGER NOT NULL DEFAULT 100,
            created_at INTEGER NOT NULL DEFAULT (strftime('%s','now'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS directors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL UNIQUE,
            photo_url TEXT,
            tmdb_person_id INTEGER,
            sort_order INTEGER NOT NULL DEFAULT 100,
            created_at INTEGER NOT NULL DEFAULT (strftime('%s','now'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS title_actors (
            title_id INTEGER NOT NULL REFERENCES titles(id) ON DELETE CASCADE,
            actor_id INTEGER NOT NULL REFERENCES actors(id) ON DELETE CASCADE,
            character_name TEXT,
            billing_order INTEGER NOT NULL DEFAULT 100,
            role_type TEXT NOT NULL DEFAULT 'cast',
            PRIMARY KEY (title_id, actor_id, role_type)
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ta_actor ON title_actors(actor_id)")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS title_directors (
            title_id INTEGER NOT NULL REFERENCES titles(id) ON DELETE CASCADE,
            director_id INTEGER NOT NULL REFERENCES directors(id) ON DELETE CASCADE,
            role TEXT NOT NULL DEFAULT 'director',
            PRIMARY KEY (title_id, director_id)
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_td_director ON title_directors(director_id)")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS title_studios (
            title_id INTEGER NOT NULL REFERENCES titles(id) ON DELETE CASCADE,
            studio_id INTEGER NOT NULL REFERENCES studios(id) ON DELETE CASCADE,
            role TEXT NOT NULL DEFAULT 'production',
            PRIMARY KEY (title_id, studio_id, role)
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ts_studio ON title_studios(studio_id)")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS title_animation_studios (
            title_id INTEGER NOT NULL REFERENCES titles(id) ON DELETE CASCADE,
            animation_studio_id INTEGER NOT NULL REFERENCES animation_studios(id) ON DELETE CASCADE,
            role TEXT NOT NULL DEFAULT 'animation',
            PRIMARY KEY (title_id, animation_studio_id, role)
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_tas_studio ON title_animation_studios(animation_studio_id)")
    conn.commit()


def seed_reference_data(conn: sqlite3.Connection) -> None:
    conn.executemany(
        "INSERT OR IGNORE INTO decades (slug, label, start_year, end_year) VALUES (?, ?, ?, ?)", DECADES
    )
    conn.executemany(
        "INSERT OR IGNORE INTO actors (slug, name, tmdb_person_id) VALUES (?, ?, ?)", ACTORS
    )
    conn.executemany(
        "INSERT OR IGNORE INTO directors (slug, name, tmdb_person_id) VALUES (?, ?, ?)", DIRECTORS
    )
    conn.executemany(
        "INSERT OR IGNORE INTO studios (slug, name, tmdb_company_id) VALUES (?, ?, ?)", STUDIOS
    )
    conn.executemany(
        "INSERT OR IGNORE INTO animation_studios (slug, name, tmdb_company_id) VALUES (?, ?, ?)", ANIM_STUDIOS
    )
    conn.commit()


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate actors/directors/studios reference tables into catalog.db")
    parser.add_argument("--db", default="catalog.db")
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.execute("PRAGMA busy_timeout = 15000")

    create_tables(conn)
    seed_reference_data(conn)

    counts = {
        t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        for t in ("studios", "animation_studios", "decades", "actors", "directors")
    }
    conn.close()

    print(json.dumps({"row_counts": counts, "tables_created": TABLES_CREATED}, indent=2))


if __name__ == "__main__":
    main()
