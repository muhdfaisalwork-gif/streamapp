"""
migrate_watch_providers.py — Adds streaming_providers / title_streaming_providers
tables to catalog.db for legal "Watch on Netflix"-style badges (TMDB watch/providers
data), matching the schema already sketched in catalog_schema.py but never migrated
into the live database. Idempotent: safe to run more than once.

Generated with qwen2.5-coder:7b via Ollama MCP, assembled by Claude.
"""
from __future__ import annotations
import argparse
import json
import sqlite3

PROVIDERS = [
    ("netflix", "Netflix", "https://www.netflix.com"),
    ("prime-video", "Prime Video", "https://www.primevideo.com"),
    ("disney-plus", "Disney+", "https://www.disneyplus.com"),
    ("hulu", "Hulu", "https://www.hulu.com"),
    ("max", "Max", "https://www.max.com"),
    ("apple-tv-plus", "Apple TV+", "https://tv.apple.com"),
    ("paramount-plus", "Paramount+", "https://www.paramountplus.com"),
    ("peacock", "Peacock", "https://www.peacocktv.com"),
    ("crunchyroll", "Crunchyroll", "https://www.crunchyroll.com"),
]


def create_tables(cursor: sqlite3.Cursor) -> None:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS streaming_providers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL UNIQUE,
            base_url TEXT,
            logo_url TEXT,
            region TEXT NOT NULL DEFAULT 'US',
            is_legal INTEGER NOT NULL DEFAULT 1,
            enabled INTEGER NOT NULL DEFAULT 1,
            sort_order INTEGER NOT NULL DEFAULT 100,
            created_at INTEGER NOT NULL DEFAULT (strftime('%s','now'))
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS title_streaming_providers (
            title_id INTEGER NOT NULL REFERENCES titles(id) ON DELETE CASCADE,
            provider_id INTEGER NOT NULL REFERENCES streaming_providers(id) ON DELETE CASCADE,
            availability_type TEXT NOT NULL DEFAULT 'subscription',
            region TEXT NOT NULL DEFAULT 'US',
            deep_link TEXT,
            last_checked_at INTEGER,
            PRIMARY KEY (title_id, provider_id, availability_type, region)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tsp_provider ON title_streaming_providers(provider_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tsp_title ON title_streaming_providers(title_id)")


def seed_providers(cursor: sqlite3.Cursor) -> None:
    cursor.executemany(
        "INSERT OR IGNORE INTO streaming_providers (slug, name, base_url) VALUES (?, ?, ?)",
        PROVIDERS,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate watch-provider tables into catalog.db")
    parser.add_argument("--db", default="catalog.db")
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    cursor = conn.cursor()

    create_tables(cursor)
    seed_providers(cursor)
    conn.commit()

    providers_seeded = cursor.execute("SELECT COUNT(*) FROM streaming_providers").fetchone()[0]
    conn.close()

    print(json.dumps({
        "providers_seeded": providers_seeded,
        "tables_created": ["streaming_providers", "title_streaming_providers"],
    }, indent=2))


if __name__ == "__main__":
    main()
