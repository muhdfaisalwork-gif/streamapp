"""
tmdb_discovery.py — Metadata-only TMDB catalog discovery.

Fans out TMDB's /discover/movie and /discover/tv across countries, adding
title METADATA for browse/search variety. This NEVER creates a fake
availability/playback row — every title lands with metadata_state='stub'
and no availability record, consistent with the project's rule against
fake playability (spec: "NO BROKEN PLAY BUTTONS", "DO NOT PROMISE 100%
PLAYABILITY"). Actual playback comes only from lawful sources like
archive_org_ingest.py.

Generated with qwen2.5-coder:7b via Ollama MCP, assembled and bug-fixed
by Claude (year-parse ordering, missing `re` import, genre-map merge
priority, type-hint cleanup).
"""
from __future__ import annotations
import argparse
import json
import logging
import os
import re
import sqlite3
import sys
import time
from typing import Any, Optional

import requests

from tmdb_client import TmdbClient

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("tmdb_discovery")

TMDB_BASE = "https://api.themoviedb.org/3"

# ISO 3166-1 alpha-2 codes for TMDB's with_origin_country filter (production countries).
ALL_COUNTRIES = [
    "US", "GB", "CA", "AU", "NZ", "IE", "IN", "PK", "BD", "LK", "NP",
    "FR", "DE", "IT", "ES", "PT", "NL", "BE", "CH", "AT", "SE", "NO",
    "DK", "FI", "IS", "PL", "CZ", "SK", "HU", "RO", "BG", "GR", "TR",
    "RU", "UA", "BY", "LT", "LV", "EE",
    "CN", "HK", "TW", "JP", "KR", "KP", "TH", "VN", "PH", "ID", "MY",
    "SG", "MM", "KH", "LA", "MN",
    "SA", "AE", "QA", "KW", "BH", "OM", "JO", "LB", "IQ", "IL", "PS", "SY", "YE",
    "EG", "MA", "DZ", "TN", "LY", "SD", "ET", "KE", "NG", "GH", "ZA",
    "SN", "CI", "CM", "UG", "TZ", "ZM", "ZW", "RW", "AO", "MZ",
    "MX", "BR", "AR", "CL", "CO", "PE", "VE", "EC", "BO", "PY", "UY",
    "CU", "DO", "JM", "TT", "GT", "HN", "SV", "NI", "CR", "PA",
    "IR", "AF", "UZ", "KZ", "KG", "TJ", "TM", "AZ", "AM", "GE",
    "FJ", "PG", "XK", "AL", "RS", "HR", "SI", "BA", "MK", "ME", "MT", "CY", "LU",
]

MOVIE_ONLY_FIELDS = {"title", "original_title", "release_date"}


def discover_movies(api_key: str, page: int, with_origin_country: Optional[str] = None,
                     sort_by: str = "popularity.desc") -> dict:
    params = {
        "api_key": api_key,
        "page": page,
        "sort_by": sort_by,
        "include_adult": "false",
    }
    if with_origin_country:
        params["with_origin_country"] = with_origin_country
    try:
        response = requests.get(f"{TMDB_BASE}/discover/movie", params=params, timeout=15)
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, json.JSONDecodeError) as e:
        log.warning("Failed to discover movies (country=%s page=%s): %s", with_origin_country, page, e)
        return {}


def discover_tv(api_key: str, page: int, with_origin_country: Optional[str] = None,
                 sort_by: str = "popularity.desc") -> dict:
    params = {
        "api_key": api_key,
        "page": page,
        "sort_by": sort_by,
        "include_adult": "false",
    }
    if with_origin_country:
        params["with_origin_country"] = with_origin_country
    try:
        response = requests.get(f"{TMDB_BASE}/discover/tv", params=params, timeout=15)
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, json.JSONDecodeError) as e:
        log.warning("Failed to discover TV (country=%s page=%s): %s", with_origin_country, page, e)
        return {}


def build_genre_map(client: TmdbClient) -> dict[int, str]:
    movie_map = {g["id"]: g["name"] for g in client.movie_genres()}
    tv_map = {g["id"]: g["name"] for g in client.tv_genres()}
    return {**tv_map, **movie_map}  # movie names win on id clash (movie spread last)


def resolve_genre_ids(conn: sqlite3.Connection, tmdb_genre_ids: list[int], genre_map: dict[int, str]) -> list[int]:
    resolved: list[int] = []
    for gid in tmdb_genre_ids:
        name = genre_map.get(gid)
        if not name:
            continue
        row = conn.execute("SELECT id FROM genres WHERE lower(name)=lower(?)", (name,)).fetchone()
        if row:
            resolved.append(row[0])
    return resolved


def slugify(title: str, year: Optional[int]) -> str:
    base = re.sub(r"[^a-zA-Z0-9]+", "-", title.lower().strip()).strip("-")
    return f"{base}-{year}" if year else base


def get_or_create_country_id(conn: sqlite3.Connection, iso_code: str) -> Optional[int]:
    row = conn.execute("SELECT id FROM countries WHERE code=?", (iso_code.upper(),)).fetchone()
    return row[0] if row else None


def get_language_id(conn: sqlite3.Connection, iso_code: str) -> Optional[int]:
    row = conn.execute("SELECT id FROM languages WHERE code=?", (iso_code.lower(),)).fetchone()
    return row[0] if row else None


def upsert_discovered_title(conn: sqlite3.Connection, item: dict[str, Any], media_type: str,
                             genre_map: dict[int, str], origin_country: Optional[str]) -> tuple[Optional[int], bool]:
    tmdb_id = item.get("id")
    if not tmdb_id:
        return None, False

    existing = conn.execute("SELECT id FROM titles WHERE tmdb_id=?", (tmdb_id,)).fetchone()
    if existing:
        return existing[0], False

    title = (item.get("title") or item.get("name") or "").strip()
    if not title:
        return None, False

    date_str = item.get("release_date") or item.get("first_air_date")
    year: Optional[int] = None
    if date_str:
        try:
            year = int(date_str[:4])
        except (ValueError, TypeError):
            year = None

    genre_ids_tmdb = item.get("genre_ids", [])
    is_anime = 1 if (16 in genre_ids_tmdb and origin_country == "JP") else 0
    final_type = "anime" if is_anime else media_type

    base_slug = slugify(title, year)
    slug = base_slug
    suffix = 2
    while conn.execute("SELECT id FROM titles WHERE slug=?", (slug,)).fetchone():
        slug = f"{base_slug}-{suffix}"
        suffix += 1

    poster = f"https://image.tmdb.org/t/p/w500{item['poster_path']}" if item.get("poster_path") else None
    backdrop = f"https://image.tmdb.org/t/p/w1280{item['backdrop_path']}" if item.get("backdrop_path") else None
    now = int(time.time())

    cur = conn.execute(
        "INSERT INTO titles (slug,title,original_title,type,year,release_date,rating,rating_count,"
        "popularity,overview,poster,backdrop,tmdb_id,status,is_anime,metadata_state,created_at,updated_at) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (slug, title, item.get("original_title") or item.get("original_name"), final_type, year, date_str,
         item.get("vote_average"), item.get("vote_count", 0), item.get("popularity", 0), item.get("overview"),
         poster, backdrop, tmdb_id, "released", is_anime, "stub", now, now),
    )
    new_id = cur.lastrowid

    for gid in resolve_genre_ids(conn, genre_ids_tmdb, genre_map):
        conn.execute("INSERT OR IGNORE INTO title_genres (title_id, genre_id) VALUES (?,?)", (new_id, gid))

    if origin_country:
        cid = get_or_create_country_id(conn, origin_country)
        if cid:
            conn.execute("INSERT OR IGNORE INTO title_countries (title_id, country_id) VALUES (?,?)", (new_id, cid))

    original_language = item.get("original_language")
    if original_language:
        lid = get_language_id(conn, original_language)
        if lid:
            conn.execute(
                "INSERT OR IGNORE INTO title_languages (title_id, language_id, is_original) VALUES (?,?,1)",
                (new_id, lid),
            )

    conn.commit()
    return new_id, True


def run_discovery(db_path: str, api_key: str, country_codes: list[str], media_types: list[str],
                   max_pages_per_country: int = 5, target: Optional[int] = None) -> dict:
    conn = sqlite3.connect(db_path)
    client = TmdbClient(api_key=api_key)
    client.configure()
    genre_map = build_genre_map(client)
    counts = {"new": 0, "existing": 0, "skipped": 0}

    for country in country_codes:
        for media_type in media_types:
            for page in range(1, max_pages_per_country + 1):
                if target is not None and counts["new"] >= target:
                    conn.close()
                    return counts

                data = (discover_movies(api_key, page, with_origin_country=country) if media_type == "movie"
                        else discover_tv(api_key, page, with_origin_country=country))
                results = data.get("results", [])
                if not results:
                    break

                for item in results:
                    try:
                        title_id, was_new = upsert_discovered_title(conn, item, media_type, genre_map, country)
                        if title_id is None:
                            counts["skipped"] += 1
                        elif was_new:
                            counts["new"] += 1
                        else:
                            counts["existing"] += 1
                    except Exception as e:
                        log.exception("Error processing item: %s", e)
                        counts["skipped"] += 1
                time.sleep(0.05)

    conn.close()
    return counts


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="catalog.db")
    parser.add_argument("--target", type=int, default=None)
    parser.add_argument("--max-pages", type=int, default=5)
    parser.add_argument("--countries", default=None)
    parser.add_argument("--media-types", default="movie,tv")
    args = parser.parse_args()

    api_key = os.environ.get("TMDB_API_KEY")
    if not api_key:
        print("FATAL: TMDB_API_KEY not set", file=sys.stderr)
        sys.exit(2)

    countries = args.countries.split(",") if args.countries else ALL_COUNTRIES
    media_types = args.media_types.split(",")

    result = run_discovery(db_path=args.db, api_key=api_key, country_codes=countries,
                            media_types=media_types, max_pages_per_country=args.max_pages, target=args.target)
    print(json.dumps(result, indent=2))
