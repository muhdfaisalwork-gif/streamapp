"""Read-only snapshot of current catalog.db stats.

Just prints. Does not write.
"""
import sqlite3
import os

DB = os.path.join(os.path.dirname(__file__), "catalog.db")
print(f"# catalog: {DB}\n")

c = sqlite3.connect(DB)
cur = c.cursor()


def one(label, sql, *params):
    try:
        cur.execute(sql, params)
        v = cur.fetchone()[0]
    except sqlite3.OperationalError as e:
        v = f"<missing: {e}>"
    print(f"  {label:36s} {v}")


print("=== TOP-LINE (matches the session summary you pasted) ===")

# total titles
one("Total titles", "SELECT COUNT(*) FROM titles")

# by type
print()
print("  By type:")
for t in ("movie", "tv", "anime", "short_drama", "documentary"):
    one(f"    {t:18s}", "SELECT COUNT(*) FROM titles WHERE type = ?", t)

# playable (matches the catalog_service.py definition: status='available' AND playback_url IS NOT NULL)
one("Playable (avail + playback_url)",
    "SELECT COUNT(*) FROM availability WHERE status = 'available' AND playback_url IS NOT NULL")

# archive.org rows in availability
one("Archive.org rows (source)",
    "SELECT COUNT(*) FROM availability a JOIN sources s ON a.source_id = s.id "
    "WHERE s.slug = 'archiveorg' OR s.slug LIKE '%archive%'")

# language tag
one("With language tag (title_languages)",
    "SELECT COUNT(*) FROM (SELECT DISTINCT title_id FROM title_languages)")

# TV episodes (sum of episode_count in seasons)
one("TV episodes (sum of season.episode_count)",
    "SELECT COALESCE(SUM(episode_count), 0) FROM seasons")

# franchise collection links (title_collections rows)
one("Franchise collection links",
    "SELECT COUNT(*) FROM title_collections")

print()
print("=== TYPE BREAKDOWN (movies / TV / anime / short drama) ===")
cur.execute("""
  SELECT type, COUNT(*) FROM titles
  GROUP BY type ORDER BY COUNT(*) DESC
""")
for r in cur.fetchall():
    print(f"  {r[0] or '<null>':18s} {r[1]}")

print()
print("=== AVAILABILITY STATUS ===")
cur.execute("""
  SELECT status, COUNT(*) FROM availability
  GROUP BY status ORDER BY COUNT(*) DESC
""")
for r in cur.fetchall():
    print(f"  {r[0] or '<null>':18s} {r[1]}")

print()
print("=== TOP 10 SOURCES BY ROWS ===")
cur.execute("""
  SELECT s.slug, s.name, COUNT(a.id) AS rows,
         SUM(CASE WHEN a.status='available' AND a.playback_url IS NOT NULL THEN 1 ELSE 0 END) AS playable
  FROM sources s LEFT JOIN availability a ON a.source_id = s.id
  GROUP BY s.id ORDER BY rows DESC LIMIT 10
""")
for r in cur.fetchall():
    print(f"  {r[0]:15s} {r[1]:22s} rows={r[2]:>7} playable={r[3] or 0:>7}")

print()
print("=== NEW TABLES (from this session's additions) ===")
for t in [
    "streaming_providers",
    "studios",
    "animation_studios",
    "decades",
    "actors",
    "directors",
    "genre_images",
    "collection_images",
    "free_access_methods",
    "country_production",
    "regional_formats",
    "animation_centers",
    "global_format_stats",
    "facets",
    "title_actors",
    "title_directors",
    "title_studios",
    "title_animation_studios",
    "title_streaming_providers",
]:
    one(f"  {t:30s}", f"SELECT COUNT(*) FROM {t}")

c.close()
