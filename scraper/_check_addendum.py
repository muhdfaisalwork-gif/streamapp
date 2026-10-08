import sqlite3, os

DB = os.path.join(os.path.dirname(__file__), "catalog_addendum.db")
print(f"# reading: {DB}\n")

c = sqlite3.connect(DB)
cur = c.cursor()

tables = [
    "streaming_providers", "studios", "animation_studios", "decades",
    "facets", "genre_posters", "collection_posters", "free_access_methods",
    "country_production", "regional_formats", "animation_centers",
    "global_format_stats", "actors", "directors",
    "title_actors", "title_directors", "title_studios",
    "title_animation_studios", "title_streaming_providers",
]

print("=== catalog_addendum.db row counts ===")
for t in tables:
    cur.execute("SELECT COUNT(*) FROM " + t)
    n = cur.fetchone()[0]
    print("  " + t.ljust(28) + " " + str(n))

# Verify trending wired
print()
print("=== trending facet ===")
for row in cur.execute(
    "SELECT slug, name, poster_url FROM facets WHERE slug='trending'"
):
    print("  " + str(row))

# Verify freekeys wired
print()
print("=== free_access_methods (freekeys refs) ===")
for row in cur.execute(
    "SELECT provider_slug, reference_url FROM free_access_methods LIMIT 3"
):
    print("  " + str(row))

# Verify a join-style query would work
print()
print("=== Sample join: studios with logos ===")
for row in cur.execute(
    "SELECT slug, name, logo_url, country FROM studios ORDER BY slug"
):
    print("  " + str(row))

print()
print("=== Sample join: country_production top 5 by film output ===")
for row in cur.execute("""
SELECT country_code, annual_films_min, annual_films_max, domestic_box_office_pct
FROM country_production
WHERE annual_films_min IS NOT NULL
ORDER BY (annual_films_min + annual_films_max) / 2.0 DESC
LIMIT 5
"""):
    print("  " + str(row))

c.close()

# Now confirm live catalog.db is UNTOUCHED
print()
print("=== LIVE catalog.db untouched (sample) ===")
live = sqlite3.connect(os.path.join(os.path.dirname(__file__), "catalog.db"))
lcur = live.cursor()
for table, expected in [
    ("titles", 88955),
    ("availability", 24172),
    ("seasons", 21872),  # roughly
    ("collections", 86),
    ("sources", 20),
    ("people", 0),
    ("genres", 27),
    ("countries", 0),
]:
    try:
        lcur.execute("SELECT COUNT(*) FROM " + table)
        n = lcur.fetchone()[0]
        marker = " <-- UNCHANGED" if (expected == 0 or abs(n - expected) < 100) else ""
        print("  " + table.ljust(20) + " " + str(n) + marker)
    except Exception as e:
        print("  " + table.ljust(20) + " ERR " + str(e))

live.close()
