"""
ingest_hbo_disney.py — Comprehensive enrichment for HBO/Max and Disney+ content.
1. Discovers top HBO (net 49), Max (net 3186), and Disney+ (net 2739) shows.
2. Discovers top movies on Max (provider 1899/384) and Disney+ (provider 337).
3. Ingests missing titles into `titles`, `title_genres`, `title_countries`, `title_languages`.
4. Maps all of them to `title_streaming_providers`.
5. Wires up embed availability rows (vidsrc, 2embed, superembed, multiembed, embedsu, moviebox) with IMDB IDs.
"""
import sqlite3
import json
import time
import re
import urllib.request
import urllib.parse
from pathlib import Path
from dotenv import dotenv_values

HERE = Path(r"G:\streaming app\scraper")
DB_PATH = HERE / "catalog.db"
ENV = dotenv_values(str(HERE / ".env"))
API_KEY = ENV.get("TMDB_API_KEY", "")
if not API_KEY:
    raise SystemExit("TMDB_API_KEY not set in scraper/.env")
BASE_URL = "https://api.themoviedb.org/3"

EMBED_TEMPLATES = {
    "vidsrc":     "https://vidsrc.to/embed/{kind}/{imdb}",
    "2embed":     "https://www.2embed.cc/embed/{imdb}",
    "superembed": "https://multiembed.mov/?video_id={imdb}&tmdb=1",
    "multiembed": "https://multiembed.mov/?video_id={imdb}",
    "flixhq":     "https://flixhq.click/watch-{kind}/{imdb}",
    "gomovies":   "https://gomovies.sx/{kind}/{imdb}",
    "moviebox":   "https://movieboxapp.io/{kind}/{tmdb}",
    "cinezone":   "https://cinezone.cz/embed/{kind}/{imdb}",
    "embedsu":    "https://embed.su/embed/{kind}/{imdb}",
    "warezcdn":   "https://warezcdn.com/embed/{kind}/{imdb}",
}

def slugify(s: str) -> str:
    s = (s or "").lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")[:120] or "untitled"

def tmdb_get(path, params):
    params["api_key"] = API_KEY
    url = f"{BASE_URL}{path}?{urllib.parse.urlencode(params)}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            if attempt == 2:
                print(f"Error requesting {path}: {e}")
                return None
            time.sleep(1.0)
    return None

def main():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Get provider IDs
    cur.execute("SELECT id, slug FROM streaming_providers")
    prov_map = {r["slug"]: r["id"] for r in cur.fetchall()}
    max_pid = prov_map.get("max", 5)
    disney_pid = prov_map.get("disney-plus", 3)

    # Get embed source IDs
    placeholders = ",".join("?" for _ in EMBED_TEMPLATES.keys())
    cur.execute(f"SELECT id, slug FROM sources WHERE slug IN ({placeholders})", list(EMBED_TEMPLATES.keys()))
    source_ids = {r["slug"]: r["id"] for r in cur.fetchall()}
    print(f"Found {len(source_ids)} embed sources")

    tasks = [
        # (type, param_dict, provider_id, label, max_pages)
        ("tv", {"with_networks": "49", "sort_by": "popularity.desc"}, max_pid, "HBO Shows", 5),
        ("tv", {"with_networks": "3186", "sort_by": "popularity.desc"}, max_pid, "Max Original Shows", 5),
        ("tv", {"with_networks": "2739", "sort_by": "popularity.desc"}, disney_pid, "Disney+ Shows", 8),
        ("movie", {"with_watch_providers": "1899|384", "watch_region": "US", "sort_by": "popularity.desc"}, max_pid, "Max Movies", 6),
        ("movie", {"with_watch_providers": "337", "watch_region": "US", "sort_by": "popularity.desc"}, disney_pid, "Disney+ Movies", 6),
    ]

    total_added = 0
    total_linked = 0
    total_avail = 0

    for kind, params, pid, label, max_pages in tasks:
        print(f"\n--- Processing {label} (Provider ID: {pid}) ---")
        endpoint = f"/discover/{kind}"
        for page in range(1, max_pages + 1):
            p = dict(params)
            p["page"] = page
            data = tmdb_get(endpoint, p)
            if not data or not data.get("results"):
                break

            results = data["results"]
            for item in results:
                tmdb_id = item.get("id")
                if not tmdb_id:
                    continue

                if kind == "movie":
                    title = item.get("title") or item.get("original_title") or ""
                    date_str = item.get("release_date") or ""
                else:
                    title = item.get("name") or item.get("original_name") or ""
                    date_str = item.get("first_air_date") or ""

                if not title:
                    continue

                # Check if exists in titles
                cur.execute("SELECT id, imdb_id, status FROM titles WHERE tmdb_id=? AND type=?", (tmdb_id, kind))
                existing = cur.fetchone()

                now = int(time.time())
                title_id = None
                imdb_id = None

                if existing:
                    title_id = existing["id"]
                    imdb_id = existing["imdb_id"]
                else:
                    # Fetch details to get external_ids (IMDb id)
                    details = tmdb_get(f"/{kind}/{tmdb_id}", {"append_to_response": "external_ids"})
                    if details:
                        ext = details.get("external_ids") or {}
                        imdb_id = ext.get("imdb_id") or details.get("imdb_id")
                        runtime = details.get("runtime") if kind == "movie" else (details.get("episode_run_time") or [None])[0]
                    else:
                        runtime = None

                    year = int(date_str[:4]) if date_str and len(date_str) >= 4 else None
                    base_slug = slugify(title)
                    slug = f"{base_slug}-{year}" if year else base_slug

                    # Check slug conflict
                    cur.execute("SELECT 1 FROM titles WHERE slug=?", (slug,))
                    if cur.fetchone():
                        slug = f"{slug}-{tmdb_id}"

                    poster = f"https://image.tmdb.org/t/p/w500{item.get('poster_path')}" if item.get('poster_path') else None
                    backdrop = f"https://image.tmdb.org/t/p/w1280{item.get('backdrop_path')}" if item.get('backdrop_path') else None

                    # Check status
                    from datetime import date
                    today_str = date.today().isoformat()
                    if date_str and date_str > today_str:
                        status = "upcoming"
                    else:
                        status = "released"

                    cur.execute("""
                        INSERT OR IGNORE INTO titles
                        (slug, title, original_title, type, year, release_date, runtime, rating, rating_count, popularity,
                         overview, poster, backdrop, tmdb_id, imdb_id, status, is_anime, metadata_state, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 'full', ?, ?)
                    """, (slug, title, item.get("original_title") or item.get("original_name") or title,
                          kind, year, date_str, runtime, item.get("vote_average", 0), item.get("vote_count", 0),
                          item.get("popularity", 0), item.get("overview", ""), poster, backdrop,
                          tmdb_id, imdb_id, status, now, now))
                    conn.commit()

                    title_id = cur.lastrowid
                    if not title_id:
                        cur.execute("SELECT id FROM titles WHERE tmdb_id=? AND type=?", (tmdb_id, kind))
                        r = cur.fetchone()
                        title_id = r[0] if r else None

                    total_added += 1

                if not title_id:
                    continue

                # Ensure imdb_id is populated
                if not imdb_id:
                    ext_data = tmdb_get(f"/{kind}/{tmdb_id}/external_ids", {})
                    if ext_data and ext_data.get("imdb_id"):
                        imdb_id = ext_data["imdb_id"]
                        cur.execute("UPDATE titles SET imdb_id=? WHERE id=? AND imdb_id IS NULL", (imdb_id, title_id))
                        conn.commit()

                # Link in title_streaming_providers
                cur.execute("""
                    INSERT OR REPLACE INTO title_streaming_providers
                    (title_id, provider_id, availability_type, region, deep_link, last_checked_at)
                    VALUES (?, ?, 'subscription', 'US', ?, ?)
                """, (title_id, pid, f"https://www.themoviedb.org/{kind}/{tmdb_id}/watch", now))
                if cur.rowcount > 0:
                    total_linked += 1

                # Wire up embed availability
                for s_slug, s_id in source_ids.items():
                    tmpl = EMBED_TEMPLATES.get(s_slug)
                    if not tmpl:
                        continue
                    if "{imdb}" in tmpl and not imdb_id:
                        continue
                    try:
                        url = tmpl.format(kind=kind, imdb=imdb_id or "", tmdb=tmdb_id)
                        cur.execute("""
                            INSERT OR IGNORE INTO availability
                            (title_id, source_id, status, kind, external_url, is_legal_verified, requires_auth)
                            VALUES (?, ?, 'available', 'playback', ?, 0, 0)
                        """, (title_id, s_id, url))
                        if cur.rowcount > 0:
                            total_avail += 1
                    except Exception:
                        pass

                conn.commit()

            print(f"  Page {page}/{max_pages} done.")
            time.sleep(0.2)

    conn.close()
    print("\n==========================================")
    print(f"COMPLETE! New titles added: {total_added}")
    print(f"Provider links created/updated: {total_linked}")
    print(f"Embed availability rows added: {total_avail}")
    print("==========================================")

if __name__ == "__main__":
    main()
