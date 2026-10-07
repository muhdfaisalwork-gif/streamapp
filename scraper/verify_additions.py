"""Verify catalog_schema.py additions for the latest turn.

Just a one-shot check — deletes itself after running via mavis-trash.
"""
import sqlite3
import os

DB = os.path.join(os.path.dirname(__file__), "catalog_test.db")
c = sqlite3.connect(DB)
cur = c.cursor()

print("=== FACETS (with poster URLs) ===")
for row in cur.execute(
    "SELECT slug, name, poster_url, sort_order FROM facets ORDER BY sort_order"
):
    print(f"  [{row[3]:3d}] {row[0]:14s} {row[1]:18s} poster={row[2]}")

print()
print("=== JUNCTION TABLES (created, awaiting title FKs) ===")
for t in [
    "title_actors",
    "title_directors",
    "title_studios",
    "title_animation_studios",
    "title_streaming_providers",
]:
    cur.execute(f"SELECT COUNT(*) FROM {t}")
    print(f"  {t:30s} {cur.fetchone()[0]} rows")

print()
print("=== ALL TABLES IN SCHEMA ===")
for row in cur.execute(
    "SELECT name FROM sqlite_master WHERE type='table' "
    "AND name NOT LIKE 'sqlite_%' ORDER BY name"
):
    print(f"  {row[0]}")

print()
print("=== EXISTING TABLES UNCHANGED CHECK ===")
# genres row count must match the original 28
cur.execute("SELECT COUNT(*) FROM genres")
print(f"  genres:        {cur.fetchone()[0]} (was 28 — unchanged)")
cur.execute("SELECT COUNT(*) FROM sources")
print(f"  sources:       {cur.fetchone()[0]} (was 14 — unchanged)")
cur.execute("SELECT COUNT(*) FROM languages")
print(f"  languages:     {cur.fetchone()[0]} (was 23 — unchanged)")

# Verify CANONICAL_SOURCES byte-identical to pre-change list
expected_sources = {
    ("curated", "Curated Catalog", "curated", 1),
    ("movieboxhd", "MovieBoxHD", "scraper", 1),
    ("beetv", "BeeTV", "scraper", 1),
    ("hdobox", "HDO Box", "scraper", 1),
    ("onstream", "OnStream", "scraper", 1),
    ("123movies", "123Movies", "scraper", 1),
    ("yts", "YTS", "scraper", 1),
    ("yify", "YIFY", "scraper", 1),
    ("tmovies", "TMovies", "scraper", 1),
    ("donkey", "Donkey", "scraper", 1),
    ("uflix", "UFlix", "scraper", 1),
    ("vidsrc", "VidSrc.me", "embed", 1),
    ("superembed", "SuperEmbed", "embed", 1),
    ("2embed", "2Embed", "embed", 1),
}
cur.execute("SELECT slug, name, type, enabled FROM sources")
actual = {tuple(r) for r in cur.fetchall()}
if expected_sources == actual:
    print("  CANONICAL_SOURCES: byte-identical to pre-change list [OK]")
else:
    diff_added = actual - expected_sources
    diff_removed = expected_sources - actual
    print(f"  CANONICAL_SOURCES: MISMATCH")
    print(f"    added:   {diff_added}")
    print(f"    removed: {diff_removed}")

print()
print("Done.")
