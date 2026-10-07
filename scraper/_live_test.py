"""Live API tests against the running catalog service."""
import httpx, json

base = "http://127.0.0.1:7801"

print("=== /api/v1/titles?limit=5 ===")
r = httpx.get(base + "/api/v1/titles", params={"limit": 5, "sort": "popularity"}, timeout=10.0)
d = r.json()
items = d.get("items", d.get("results", d))
if isinstance(items, list):
    for t in items[:5]:
        title = t.get("title") or t.get("name") or "?"
        year = t.get("year") or "?"
        slug = t.get("slug") or "?"
        rating = t.get("rating") or 0
        print("  [" + str(year) + "] " + str(title) + "  (slug=" + str(slug) + ", rating=" + str(rating) + ")")
else:
    print(json.dumps(d, indent=2)[:1500])
print()

print("=== /api/v1/title/dune-2021 (Dune 2021) ===")
r = httpx.get(base + "/api/v1/title/dune-2021", timeout=10.0)
print("status:", r.status_code)
if r.status_code == 200:
    d = r.json()
    print("  title:  " + str(d.get("title")))
    print("  year:   " + str(d.get("year")))
    print("  rating: " + str(d.get("rating")))
    print("  tmdb_id:" + str(d.get("tmdb_id")))
    print("  poster: " + (str(d.get("poster")) or "")[:80])
else:
    print("  body:", r.text[:200])
print()

print("=== /api/v1/titles?type=movie&year=2024&limit=3 ===")
r = httpx.get(base + "/api/v1/titles", params={"type": "movie", "year": 2024, "limit": 3}, timeout=10.0)
print("status:", r.status_code)
d = r.json()
items = d.get("items", d.get("results", d))
if isinstance(items, list):
    for t in items[:3]:
        print("  [" + str(t.get("year")) + "] " + str(t.get("title")) + "  rating=" + str(t.get("rating")))
else:
    print(json.dumps(d, indent=2)[:1000])
print()

print("=== /api/v1/sources ===")
r = httpx.get(base + "/api/v1/sources", timeout=10.0)
d = r.json()
items = d.get("items", d.get("sources", d))
if isinstance(items, list):
    print("  total sources:", len(items))
    for s in items[:5]:
        print("  " + str(s.get("slug")) + " (" + str(s.get("name")) + ")  rows=" + str(s.get("availability_records", "?")))
else:
    print(json.dumps(d, indent=2)[:1000])
print()

print("=== /api/v1/featured ===")
r = httpx.get(base + "/api/v1/featured", timeout=10.0)
print("status:", r.status_code)
d = r.json()
if isinstance(d, list):
    print("  rails:", len(d))
    for rail in d[:3]:
        print("    " + str(rail.get("slug") or rail.get("title")) + " - " + str(len(rail.get("items", []))) + " items")
elif isinstance(d, dict):
    print("  keys:", list(d.keys())[:10])
