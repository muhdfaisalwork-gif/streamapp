"""Comprehensive live API test against the running catalog service."""
import httpx, json

base = "http://127.0.0.1:7801"
total_endpoints = 0
passed = 0
failed = []


def probe(label, method, path, expect_404=False, **kwargs):
    global total_endpoints, passed
    total_endpoints += 1
    try:
        r = httpx.request(method, base + path, timeout=10.0, **kwargs)
        status = r.status_code
        # expect_404=True means "correct response is 404" — that counts as PASS
        if expect_404:
            if status == 404:
                passed += 1
                print("  [OK 404 expected] " + label)
            else:
                print("  [" + str(status) + "]    " + label + "  (expected 404)")
            return r
        ok = 200 <= status < 300
        if ok:
            passed += 1
            print("  [OK " + str(status) + "] " + label)
        else:
            print("  [" + str(status) + "]    " + label)
        return r
    except Exception as e:
        print("  [ERR]    " + label + "  " + str(e))
        failed.append(label)
        return None


print("=== CORE HEALTH/STATS ===")
probe("/health", "GET", "/health")
probe("/api/v1/stats", "GET", "/api/v1/stats")
print()

print("=== TITLES BROWSE ===")
probe("list (popularity sort)", "GET", "/api/v1/titles", params={"limit": 5, "sort": "popularity"})
probe("list (rating sort)", "GET", "/api/v1/titles", params={"limit": 5, "sort": "rating"})
probe("list (year sort)", "GET", "/api/v1/titles", params={"limit": 5, "sort": "year"})
probe("list (filter movie)", "GET", "/api/v1/titles", params={"limit": 3, "type": "movie"})
probe("list (filter tv)", "GET", "/api/v1/titles", params={"limit": 3, "type": "tv"})
probe("list (filter year=2024)", "GET", "/api/v1/titles", params={"limit": 3, "year": 2024})
probe("list (filter decade=2020s)", "GET", "/api/v1/titles", params={"limit": 3, "decade": 2020})
probe("list (paginated offset)", "GET", "/api/v1/titles", params={"limit": 3, "offset": 100})
print()

print("=== TITLE DETAIL ===")
probe("get Dune 2021", "GET", "/api/v1/title/dune-2021")
probe("get The Matrix 1999", "GET", "/api/v1/title/the-matrix-1999")
probe("get Avengers Endgame", "GET", "/api/v1/title/avengers-endgame-2019")
probe("get nonexistent (expect 404)", "GET", "/api/v1/title/this-does-not-exist-xyz", expect_404=True)
print()

print("=== SOURCES & FACETS ===")
probe("list sources", "GET", "/api/v1/sources")
probe("single source (archive_org)", "GET", "/api/v1/sources/archive_org")
probe("collections list", "GET", "/api/v1/collections")
probe("single collection avatar", "GET", "/api/v1/collections/avatar")
probe("genres list", "GET", "/api/v1/genres")
probe("single genre action", "GET", "/api/v1/genres/action")
print()

print("=== SEARCH ===")
probe("search 'matrix'", "GET", "/api/v1/search", params={"q": "matrix", "limit": 3})
probe("search 'spielberg'", "GET", "/api/v1/search", params={"q": "spielberg", "limit": 3})
probe("search 'breaking bad'", "GET", "/api/v1/search", params={"q": "breaking bad", "limit": 3})
print()

print("=== AVAILABILITY (where to watch) ===")
probe("get availability for Dune 2021", "GET", "/api/v1/title/dune-2021/availability")
probe("get availability for The Matrix 1999", "GET", "/api/v1/title/the-matrix-1999/availability")
print()

print()
print("=" * 50)
print("RESULT: " + str(passed) + "/" + str(total_endpoints) + " probes returned 2xx")
if failed:
    print("FAILED: " + ", ".join(failed))
else:
    print("all probes responded (non-fatal 4xx noted above)")
print("=" * 50)

# Final headline counts from /health
r = httpx.get(base + "/health", timeout=5.0)
d = r.json()
print()
print("HEADLINE COUNTS:")
counts = d.get("counts", {})
for k, v in counts.items():
    print("  " + str(k) + ": " + str(v))
