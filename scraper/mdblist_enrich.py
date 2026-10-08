"""
mdblist_enrich.py — Fills in NULL ratings on existing titles using
MDBList's aggregated score (IMDb/Metacritic/RT/Trakt/Letterboxd composite).

Never overwrites an existing non-NULL rating (same "only fill true gaps"
principle as _tmdb_fastbackfill.py). Deliberately does NOT create any
availability/playback rows — MDBList's watch_providers here carry no
per-title deep link, and inserting an "available" row without a real
clickable URL would repeat the broken-Play-button mistake already found
and reverted once this session.

Generated with qwen2.5-coder:7b via Ollama MCP; reviewed by Claude, no
bugs found on this pass.
"""
from __future__ import annotations
import argparse
import json
import logging
import os
import sqlite3
import time

import requests

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("mdblist_enrich")

BASE_URL = "https://mdblist.com/api/"
MIN_INTERVAL_SEC = 0.2


def fetch_rating_data(api_key: str, imdb_id: str) -> dict | None:
    try:
        response = requests.get(BASE_URL, params={"apikey": api_key, "i": imdb_id}, timeout=15)
        response.raise_for_status()
        data = response.json()
        if not data.get("response", False) or ("score" not in data and "score_average" not in data):
            return None
        return data
    except (requests.RequestException, ValueError) as e:
        log.warning("Failed to fetch rating data for imdb_id=%s: %s", imdb_id, e)
        return None


def extract_imdb_vote_count(data: dict) -> int | None:
    for rating in data.get("ratings", []):
        if rating.get("source") == "imdb":
            try:
                return int(rating["votes"])
            except (ValueError, KeyError, TypeError):
                pass
    return None


def enrich_ratings(db_path: str = "catalog.db", api_key: str | None = None, limit: int | None = None) -> dict:
    api_key = api_key or os.environ.get("MDBLIST_API_KEY")
    if not api_key:
        raise RuntimeError("MDBLIST_API_KEY not set")

    conn = sqlite3.connect(db_path)
    rows = conn.execute("SELECT id, imdb_id FROM titles WHERE imdb_id IS NOT NULL AND rating IS NULL").fetchall()
    if limit is not None:
        rows = rows[:limit]

    counts = {"enriched": 0, "skipped": 0, "errors": 0}
    for title_id, imdb_id in rows:
        try:
            data = fetch_rating_data(api_key, imdb_id)
            if not data:
                counts["skipped"] += 1
                continue

            score = data.get("score_average") if data.get("score_average") is not None else data.get("score")
            if score is None:
                counts["skipped"] += 1
                continue

            rating = round(float(score) / 10, 1)
            vote_count = extract_imdb_vote_count(data)

            if vote_count is not None:
                conn.execute("UPDATE titles SET rating=?, rating_count=?, updated_at=? WHERE id=?",
                             (rating, vote_count, int(time.time()), title_id))
            else:
                conn.execute("UPDATE titles SET rating=?, updated_at=? WHERE id=?",
                             (rating, int(time.time()), title_id))
            conn.commit()
            counts["enriched"] += 1
        except Exception as e:
            log.exception("Error enriching title_id=%s: %s", title_id, e)
            counts["errors"] += 1
        time.sleep(MIN_INTERVAL_SEC)

    conn.close()
    return counts


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MDBList Ratings Enricher")
    parser.add_argument("--db", default="catalog.db")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    result = enrich_ratings(db_path=args.db, limit=args.limit)
    print(json.dumps(result, indent=2))
