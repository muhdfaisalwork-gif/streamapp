#!/usr/bin/env python3
"""
Phase 0 Database Migration Script
Adds series_type, ingestion_state, deduplication_hash, source_priority, and indexes for 200K-scale.
"""
import sqlite3
from pathlib import Path

CATALOG_DB = Path(__file__).parent / "catalog.db"

MIGRATION_SQL = """
PRAGMA foreign_keys = ON;

-- 1. Add series_type column to titles table
-- Values: 'fictional', 'true_story', 'historical', 'biographical', 'historical_fiction'
ALTER TABLE titles ADD COLUMN series_type TEXT CHECK(series_type IN ('fictional', 'true_story', 'historical', 'biographical', 'historical_fiction'));

-- 2. Add deduplication_hash column to titles table
ALTER TABLE titles ADD COLUMN deduplication_hash TEXT;

-- 3. Add source_priority column to availability table
-- 1 = legal sources, 2 = TMDB watch providers, 3 = aggregator fallback
ALTER TABLE availability ADD COLUMN source_priority INTEGER NOT NULL DEFAULT 3;

-- 4. Create ingestion_state table for tracking TMDB/TVDB/MDBlist sync cursors
CREATE TABLE IF NOT EXISTS ingestion_state (
    source_name TEXT PRIMARY KEY,          -- 'tmdb_movies', 'tmdb_tv', 'tmdb_upcoming', 'tvdb', 'mdblist'
    last_sync_timestamp INTEGER NOT NULL,  -- Unix timestamp of last successful sync
    last_page INTEGER DEFAULT 1,           -- For paginated APIs
    total_synced INTEGER DEFAULT 0,        -- Total records synced in last run
    status TEXT DEFAULT 'idle',            -- 'idle', 'running', 'completed', 'failed'
    error_message TEXT,
    updated_at INTEGER NOT NULL DEFAULT (strftime('%s','now'))
);

-- 5. Create indexes for 200K-scale queries
CREATE INDEX IF NOT EXISTS idx_titles_series_type ON titles(series_type);
CREATE INDEX IF NOT EXISTS idx_titles_deduplication_hash ON titles(deduplication_hash);
CREATE INDEX IF NOT EXISTS idx_titles_is_scripted ON titles(is_scripted);
CREATE INDEX IF NOT EXISTS idx_titles_type_year ON titles(type, year);
CREATE INDEX IF NOT EXISTS idx_titles_type_rating ON titles(type, rating);
CREATE INDEX IF NOT EXISTS idx_titles_type_popularity ON titles(type, popularity);
CREATE INDEX IF NOT EXISTS idx_titles_status_year ON titles(status, year);
CREATE INDEX IF NOT EXISTS idx_availability_source_priority ON availability(source_priority);

-- 6. Add unique index on deduplication_hash for fast duplicate detection
CREATE UNIQUE INDEX IF NOT EXISTS uq_titles_deduplication_hash ON titles(deduplication_hash) WHERE deduplication_hash IS NOT NULL;

-- 7. Insert initial ingestion_state records
INSERT OR IGNORE INTO ingestion_state (source_name, last_sync_timestamp, last_page, status)
VALUES
    ('tmdb_movies', 0, 1, 'idle'),
    ('tmdb_tv', 0, 1, 'idle'),
    ('tmdb_upcoming', 0, 1, 'idle'),
    ('tvdb', 0, 1, 'idle'),
    ('mdblist', 0, 1, 'idle');

-- 8. Update existing source priorities based on is_legal flag
UPDATE availability SET source_priority = 1 WHERE source_id IN (SELECT id FROM sources WHERE is_legal = 1);
UPDATE availability SET source_priority = 2 WHERE source_id IN (SELECT id FROM sources WHERE slug = 'tmdb');
UPDATE availability SET source_priority = 3 WHERE source_priority IS NULL OR source_priority = 3;
"""

def run_migration():
    """Execute the migration."""
    print(f"Connecting to {CATALOG_DB}...")
    conn = sqlite3.connect(str(CATALOG_DB))
    conn.executescript(MIGRATION_SQL)
    conn.commit()
    
    # Verify migration
    cur = conn.cursor()
    
    # Check titles table columns
    cur.execute("PRAGMA table_info(titles)")
    titles_cols = [row[1] for row in cur.fetchall()]
    print(f"Titles columns: {', '.join(titles_cols)}")
    
    # Check availability table columns
    cur.execute("PRAGMA table_info(availability)")
    avail_cols = [row[1] for row in cur.fetchall()]
    print(f"Availability columns: {', '.join(avail_cols)}")
    
    # Check ingestion_state table
    cur.execute("SELECT * FROM ingestion_state")
    print("Ingestion state:")
    for row in cur.fetchall():
        print(f"  {row}")
    
    # Verify indexes
    cur.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%' OR name LIKE 'uq_%'")
    indexes = [row[0] for row in cur.fetchall()]
    print(f"Indexes: {', '.join(indexes)}")
    
    # Count titles
    cur.execute("SELECT COUNT(*) FROM titles")
    print(f"Total titles: {cur.fetchone()[0]}")
    
    conn.close()
    print("Migration completed successfully!")

if __name__ == "__main__":
    run_migration()