"""
batch_wire_all_embeds.py — Fast batch embed wiring for all titles in catalog.db.
INSERT OR IGNORE only. Never overwrites or deletes anything.
Wires embed aggregator mirrors (vidsrc, superembed, moviebox, 2embed, embedsu, flixhq, gomovies)
using tmdb_id and imdb_id so every title, including newly added ones and coming soon titles,
has playable streams/mirrors.
"""
import sqlite3
import time
from pathlib import Path

HERE = Path(__file__).parent
DB = HERE / "catalog.db"

def main():
    conn = sqlite3.connect(str(DB), timeout=60)
    conn.execute("PRAGMA journal_mode = WAL")
    cur = conn.cursor()

    # Source IDs
    sources = dict(cur.execute("SELECT slug, id FROM sources").fetchall())
    
    # Check sources
    needed = ["vidsrc", "superembed", "moviebox", "2embed", "embedsu", "flixhq", "gomovies"]
    for s in needed:
        if s not in sources:
            print(f"Warning: source {s} not found in sources table")

    vidsrc_id = sources.get("vidsrc")
    superembed_id = sources.get("superembed")
    moviebox_id = sources.get("moviebox")
    twoembed_id = sources.get("2embed")
    embedsu_id = sources.get("embedsu")
    flixhq_id = sources.get("flixhq")
    gomovies_id = sources.get("gomovies")

    print("Fetching titles needing embed wiring...")
    # Fetch titles with tmdb_id
    rows = cur.execute("SELECT id, type, tmdb_id, imdb_id FROM titles WHERE tmdb_id IS NOT NULL").fetchall()
    print(f"Total titles with tmdb_id: {len(rows):,}")

    batch = []
    now = int(time.time())

    for tid, kind, tmdb_id, imdb_id in rows:
        k = "movie" if kind == "movie" else "tv"
        
        # 1. SuperEmbed (supports tmdb_id)
        if superembed_id:
            url = f"https://multiembed.mov/?video_id={tmdb_id}&tmdb=1"
            batch.append((tid, superembed_id, "available", "embed", url, url))

        # 2. MovieBox (supports tmdb_id)
        if moviebox_id:
            url = f"https://movieboxapp.io/{k}/{tmdb_id}"
            batch.append((tid, moviebox_id, "available", "embed", url, url))

        # 3. VidSrc (supports tmdb_id)
        if vidsrc_id:
            url = f"https://vidsrc.to/embed/{k}/{tmdb_id}"
            batch.append((tid, vidsrc_id, "available", "embed", url, url))

        # 4. 2Embed (supports tmdb_id)
        if twoembed_id:
            url = f"https://www.2embed.cc/embed/tmdb/{k}?id={tmdb_id}"
            batch.append((tid, twoembed_id, "available", "embed", url, url))

        # 5. EmbedSu (supports tmdb_id)
        if embedsu_id:
            url = f"https://embed.su/embed/{k}/{tmdb_id}"
            batch.append((tid, embedsu_id, "available", "embed", url, url))

        # If imdb_id is available, add flixhq and gomovies
        if imdb_id:
            if flixhq_id:
                url = f"https://flixhq.click/watch-{k}/{imdb_id}"
                batch.append((tid, flixhq_id, "available", "embed", url, url))
            if gomovies_id:
                url = f"https://gomovies.sx/{k}/{imdb_id}"
                batch.append((tid, gomovies_id, "available", "embed", url, url))

        if len(batch) >= 50000:
            cur.executemany(
                "INSERT OR IGNORE INTO availability (title_id, source_id, status, kind, external_url, playback_url) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                batch
            )
            conn.commit()
            print(f"  Flushed batch... total queued processed")
            batch = []

    if batch:
        cur.executemany(
            "INSERT OR IGNORE INTO availability (title_id, source_id, status, kind, external_url, playback_url) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            batch
        )
        conn.commit()

    total_avail = cur.execute("SELECT COUNT(*) FROM availability").fetchone()[0]
    print(f"Done! Total availability rows in catalog: {total_avail:,}")

if __name__ == "__main__":
    main()
