"""
mdblist_collections.py — Ingests real franchise/collection membership from
MDBList's curated lists into catalog.db's collections/title_collections
tables. Pure metadata (TMDB IDs + factual title/year data), no copyrighted
assets involved.

Only links to titles ALREADY in the catalog (by tmdb_id) — never creates
a fake title stub just because it appeared on someone's list, and never
touches availability/playback.

Generated with qwen2.5-coder:7b via Ollama MCP, assembled and bug-fixed
by Claude (slugify only split on whitespace, so "Fast & Furious" would
have kept the literal "&" in the slug instead of being stripped).
"""
from __future__ import annotations
import argparse
import json
import logging
import os
import re
import sqlite3
import time

import requests

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("mdblist_collections")

BASE_URL = "https://api.mdblist.com"

# (mdblist_username, mdblist_listname, display_name) — parsed from real mdblist.com URLs
FRANCHISE_LISTS: list[tuple[str, str, str]] = [
    ("emilyncards", "avatar", "Avatar"),
    ("vancityguy", "back-to-the-future", "Back to the Future"),
    ("andyhawks", "universe-dune", "Dune"),
    ("wheezer0610", "fast-and-furious", "Fast & Furious"),
    ("muhiso", "harry-potter", "Harry Potter"),
    ("wheezer0610", "hunger-games", "The Hunger Games"),
    ("andyhawks", "universe-indiana-jones", "Indiana Jones"),
    ("hdlists", "james-bond-movies", "James Bond"),
    ("inshanemagic", "john-wick-universe", "John Wick"),
    ("andyhawks", "universe-jurassic-park", "Jurassic Park"),
    ("spudhead15", "lord-of-the-rings-and-hobbit-collection", "Lord of the Rings"),
    ("kingkearney", "marvel-universe", "Marvel Universe"),
    ("pixelshift", "the-matrix", "The Matrix"),
    ("wheezer0610", "mission-impossible", "Mission: Impossible"),
    ("threecrow", "monsterverse", "Monsterverse"),
    ("arghhbooty", "pirates-of-the-caribbean", "Pirates of the Caribbean"),
    ("wheezer0610", "rambo", "Rambo"),
    ("drazzilb", "rocky-creed", "Rocky / Creed"),
    ("takeaflick", "star-trek-universe", "Star Trek"),
    ("andyhawks", "universe-star-wars-complete", "Star Wars"),
    ("michael0deon", "transformers-all", "Transformers"),
    ("andyhawks", "universe-x-men", "X-Men"),
    ("kingkearney", "dc-universe", "DC Universe"),
]


def fetch_list_items(api_key: str, username: str, listname: str) -> dict:
    url = f"{BASE_URL}/lists/{username}/{listname}/items"
    try:
        response = requests.get(url, params={"apikey": api_key}, timeout=15)
        response.raise_for_status()
        data = response.json()
        return {"movies": data.get("movies", []), "shows": data.get("shows", [])}
    except (requests.RequestException, ValueError) as e:
        log.warning("Error fetching list items for %s/%s: %s", username, listname, e)
        return {"movies": [], "shows": []}


def ensure_collection(conn: sqlite3.Connection, slug: str, name: str) -> int:
    # collections.name is also UNIQUE, independent of slug — a pre-existing collection
    # under a different slug but the same (or near-same) name must be reused, not
    # duplicated. Check both before inserting.
    row = conn.execute("SELECT id FROM collections WHERE slug=? OR lower(name)=lower(?)", (slug, name)).fetchone()
    if row:
        return row[0]
    conn.execute("INSERT INTO collections (slug, name, type) VALUES (?, ?, 'franchise')", (slug, name))
    conn.commit()
    row = conn.execute("SELECT id FROM collections WHERE slug=?", (slug,)).fetchone()
    return row[0]


def link_title_to_collection(conn: sqlite3.Connection, tmdb_id: int, collection_id: int) -> str:
    """Returns 'not_in_catalog', 'already_linked', or 'linked' — kept distinct so
    re-running this script doesn't misreport prior successful links as failures."""
    row = conn.execute("SELECT id FROM titles WHERE tmdb_id=?", (tmdb_id,)).fetchone()
    if not row:
        return "not_in_catalog"
    title_id = row[0]
    cur = conn.execute("INSERT OR IGNORE INTO title_collections (title_id, collection_id) VALUES (?,?)", (title_id, collection_id))
    conn.commit()
    return "linked" if cur.rowcount > 0 else "already_linked"


def slugify(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "-", name.lower().strip()).strip("-")


def ingest_collections(db_path: str = "catalog.db", api_key: str | None = None) -> dict:
    api_key = api_key or os.environ.get("MDBLIST_API_KEY")
    if not api_key:
        raise RuntimeError("MDBLIST_API_KEY not set")

    conn = sqlite3.connect(db_path)
    counts = {"linked": 0, "already_linked": 0, "not_in_catalog": 0, "lists_processed": 0, "errors": 0}
    for username, listname, display_name in FRANCHISE_LISTS:
        try:
            data = fetch_list_items(api_key, username, listname)
            collection_id = ensure_collection(conn, slugify(display_name), display_name)
            items = data.get("movies", []) + data.get("shows", [])
            for item in items:
                tmdb_id = item.get("id")
                if not tmdb_id:
                    continue
                counts[link_title_to_collection(conn, tmdb_id, collection_id)] += 1
            counts["lists_processed"] += 1
        except Exception as e:
            log.exception("Error processing list %s/%s: %s", username, listname, e)
            counts["errors"] += 1
        time.sleep(0.3)

    conn.close()
    return counts


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest MDBList franchise collections into catalog.db")
    parser.add_argument("--db", default="catalog.db")
    args = parser.parse_args()

    result = ingest_collections(db_path=args.db)
    print(json.dumps(result, indent=2))
