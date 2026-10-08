"""
finalize_hbo_disney_links.py
Ensures every popular HBO and Disney show/movie is properly mapped in title_streaming_providers
across all duplicate title records, fixes The Night Agent tmdb_id, and ingests Ahsoka.
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

def tmdb_get(path, params):
    params["api_key"] = API_KEY
    url = f"https://api.themoviedb.org/3{path}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))

def main():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 1. Fix The Night Agent tmdb_id if wrong
    cur.execute("UPDATE titles SET tmdb_id = 117376 WHERE id = 440 AND title = 'The Night Agent'")
    conn.commit()

    # 2. Ingest Ahsoka if missing
    cur.execute("SELECT id FROM titles WHERE tmdb_id = 114461")
    row = cur.fetchone()
    if not row:
        data = tmdb_get("/tv/114461", {"append_to_response": "external_ids"})
        if data:
            ext = data.get("external_ids") or {}
            imdb_id = ext.get("imdb_id")
            now = int(time.time())
            poster = f"https://image.tmdb.org/t/p/w500{data.get('poster_path')}" if data.get('poster_path') else None
            backdrop = f"https://image.tmdb.org/t/p/w1280{data.get('backdrop_path')}" if data.get('backdrop_path') else None
            slug = f"ahsoka-114461"
            cur.execute("""
                INSERT OR REPLACE INTO titles
                (slug, title, original_title, type, year, release_date, runtime, rating, rating_count, popularity,
                 overview, poster, backdrop, tmdb_id, imdb_id, status, is_anime, metadata_state, created_at, updated_at)
                VALUES (?, ?, ?, 'tv', 2023, '2023-08-22', 45, ?, ?, ?, ?, ?, ?, 114461, ?, 'released', 0, 'complete', ?, ?)
            """, (slug, "Ahsoka", "Ahsoka", data.get("vote_average", 7.3), data.get("vote_count", 1000),
                  data.get("popularity", 80), data.get("overview", ""), poster, backdrop, imdb_id, now, now))
            conn.commit()
            print("Ahsoka inserted successfully")

    # 3. Map prominent HBO and Disney+ titles by title patterns
    hbo_patterns = [
        "House of the Dragon", "The Last of Us", "Succession", "Euphoria",
        "Game of Thrones", "The Sopranos", "The Wire", "Chernobyl", "True Detective",
        "The White Lotus", "Barry", "Westworld", "Silicon Valley", "Veep",
        "Curb Your Enthusiasm", "Boardwalk Empire", "Deadwood", "Six Feet Under",
        "Band of Brothers", "The Pacific", "Watchmen", "Mare of Easttown",
        "Peacemaker", "Hacks", "Station Eleven", "The Righteous Gemstones", "Dune: Prophecy", "Lanterns"
    ]

    disney_patterns = [
        "The Mandalorian", "Loki", "Andor", "WandaVision", "Ahsoka", "Percy Jackson",
        "Moon Knight", "Hawkeye", "Obi-Wan Kenobi", "The Book of Boba Fett", "Ms. Marvel",
        "She-Hulk", "Secret Invasion", "Echo", "X-Men '97", "What If...?",
        "Star Wars: The Clone Wars", "Star Wars: The Bad Batch", "Star Wars: Rebels",
        "Daredevil: Born Again", "Agatha All Along", "Star Wars: Skeleton Crew"
    ]

    now = int(time.time())
    mapped_count = 0

    for pat in hbo_patterns:
        cur.execute("SELECT id, title, tmdb_id, imdb_id, type FROM titles WHERE title LIKE ? AND type='tv'", (f"%{pat}%",))
        for r in cur.fetchall():
            cur.execute("""
                INSERT OR REPLACE INTO title_streaming_providers
                (title_id, provider_id, availability_type, region, deep_link, last_checked_at)
                VALUES (?, 5, 'subscription', 'US', ?, ?)
            """, (r["id"], f"https://www.themoviedb.org/tv/{r['tmdb_id'] or ''}/watch", now))
            mapped_count += 1

    for pat in disney_patterns:
        cur.execute("SELECT id, title, tmdb_id, imdb_id, type FROM titles WHERE title LIKE ? AND type='tv'", (f"%{pat}%",))
        for r in cur.fetchall():
            cur.execute("""
                INSERT OR REPLACE INTO title_streaming_providers
                (title_id, provider_id, availability_type, region, deep_link, last_checked_at)
                VALUES (?, 3, 'subscription', 'US', ?, ?)
            """, (r["id"], f"https://www.themoviedb.org/tv/{r['tmdb_id'] or ''}/watch", now))
            mapped_count += 1

    # Also ensure all mapped titles have playback mirrors
    cur.execute("SELECT id, slug FROM sources WHERE slug IN ('vidsrc', '2embed', 'superembed', 'multiembed', 'embedsu', 'moviebox')")
    sources = {r["slug"]: r["id"] for r in cur.fetchall()}

    cur.execute("""
        SELECT DISTINCT t.id, t.type, t.tmdb_id, t.imdb_id
        FROM titles t
        JOIN title_streaming_providers tsp ON tsp.title_id = t.id
        WHERE tsp.provider_id IN (3, 5)
    """)
    active_titles = cur.fetchall()
    avail_added = 0

    for r in active_titles:
        tid, kind, tmdb_id, imdb_id = r["id"], r["type"], r["tmdb_id"], r["imdb_id"]
        for s_slug, s_id in sources.items():
            tmpl = EMBED_TEMPLATES.get(s_slug)
            if not tmpl:
                continue
            if "{imdb}" in tmpl and not imdb_id:
                continue
            try:
                url = tmpl.format(kind=kind, imdb=imdb_id or "", tmdb=tmdb_id or 0)
                cur.execute("""
                    INSERT OR IGNORE INTO availability
                    (title_id, source_id, status, kind, external_url, is_legal_verified, requires_auth)
                    VALUES (?, ?, 'available', 'playback', ?, 0, 0)
                """, (tid, s_id, url))
                if cur.rowcount > 0:
                    avail_added += 1
            except Exception:
                pass

    conn.commit()
    conn.close()
    print(f"Finalized! Explicitly mapped {mapped_count} provider links, added {avail_added} playback sources.")

if __name__ == "__main__":
    main()
