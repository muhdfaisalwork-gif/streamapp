"""
archive_org_ingest.py — Lawful content ingestion adapter for the Internet Archive.

Internet Archive (archive.org) hosts real public-domain and openly-licensed
films with direct, playable video files. This module ONLY ingests from
archive.org — no copyrighted or pirated sources, consistent with this
project's lawful-only ingestion policy (see REPORT_AND_PLAN.md Phase 2).

Generated with qwen2.5-coder:7b via Ollama MCP, assembled and bug-fixed
by Claude (page-increment placement, cursor.lastrowid, slug collision suffix).
"""
from __future__ import annotations
import argparse
import json
import logging
import re
import sqlite3
import time
from urllib.parse import quote

import requests

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("archive_ingest")

PREFERRED_FORMATS = ["h.264 IA", "MPEG4", "h.264", "Matroska", "OGV", "MPEG2"]
EXCLUDE_FORMATS = ["Thumbnail", "Metadata", "Text", "Subtitle", "JSON", "XML", "Archive BitTorrent"]
DEFAULT_QUERIES = [
    "collection:feature_films",
    "collection:prelinger",
    "collection:classic_tv",
    "collection:silentfilms",
    "collection:film_noir",
    "collection:newsreels",
    "collection:educationalfilms",
    "collection:animationandcartoons",
    "collection:shortformfilms",
    "collection:moviesandfilms",
]


def search_archive(query: str, page: int, rows: int = 50, mediatype: str = "movies") -> list[dict]:
    params = {
        "q": f"{query} AND mediatype:{mediatype}",
        "fl[]": ["identifier", "title", "year", "description", "mediatype", "licenseurl", "runtime", "downloads"],
        "output": "json",
        "rows": rows,
        "page": page,
    }
    try:
        response = requests.get("https://archive.org/advancedsearch.php", params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        return data["response"]["docs"]
    except (requests.RequestException, json.JSONDecodeError, KeyError) as e:
        log.warning("Failed to search Archive.org (query=%r page=%s): %s", query, page, e)
        return []


def get_item_metadata(identifier: str) -> dict | None:
    try:
        response = requests.get(f"https://archive.org/metadata/{identifier}", timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        log.warning("Failed to fetch metadata for %s: %s", identifier, e)
        return None


def pick_playable_file(item_metadata: dict, fallback_identifier: str | None = None) -> dict | None:
    identifier = item_metadata.get("metadata", {}).get("identifier") or fallback_identifier
    files = item_metadata.get("files", [])
    candidates = []
    for f in files:
        fmt = f.get("format", "")
        if not fmt:
            continue
        if any(exclude.lower() in fmt.lower() for exclude in EXCLUDE_FORMATS):
            continue
        try:
            size = int(f.get("size", 0))
        except (TypeError, ValueError):
            size = 0
        candidates.append({"name": f.get("name"), "format": fmt, "size": size})
    if not candidates:
        return None
    best = min(
        candidates,
        key=lambda c: PREFERRED_FORMATS.index(c["format"]) if c["format"] in PREFERRED_FORMATS else len(PREFERRED_FORMATS),
    )
    return {
        "url": f"https://archive.org/download/{identifier}/{quote(best['name'])}",
        "format": best["format"],
        "size": best["size"],
    }


JUNK_IDENTIFIER_PATTERNS = [
    re.compile(r"^test[-_]", re.IGNORECASE),
    re.compile(r"home[-_]?movie", re.IGNORECASE),
    re.compile(r"^sample[-_]", re.IGNORECASE),
    re.compile(r"^untitled", re.IGNORECASE),
]
MIN_DESCRIPTION_LENGTH = 40
MIN_DOWNLOADS = 5
MIN_RUNTIME_SECONDS = 180  # 3 minutes — reject very short clips, not very short films


def is_acceptable_item(doc: dict) -> bool:
    """Curation gate: decide if an Internet Archive search result is real,
    catalog-worthy film/TV content vs junk (home videos, test uploads, etc).
    """
    title = (doc.get("title") or "").strip()
    if not title:
        return False

    description = (doc.get("description") or "").strip()
    if len(description) < MIN_DESCRIPTION_LENGTH:
        return False

    try:
        downloads = int(doc.get("downloads", 0))
    except (ValueError, TypeError):
        downloads = 0
    if downloads < MIN_DOWNLOADS:
        return False

    runtime = doc.get("runtime")
    if runtime:
        try:
            if int(runtime) < MIN_RUNTIME_SECONDS:
                return False
        except (ValueError, TypeError):
            pass  # unparseable runtime doesn't disqualify on its own

    identifier = (doc.get("identifier") or "").strip()
    if any(pattern.search(identifier) for pattern in JUNK_IDENTIFIER_PATTERNS):
        return False

    license_url = (doc.get("licenseurl") or "").lower()
    if "publicdomain" in license_url or "creativecommons" in license_url:
        log.info("Strong lawful-license signal for %s: %s", identifier, license_url)

    return True


def slugify(title: str, year: int | None) -> str:
    base = re.sub(r"[^a-zA-Z0-9]+", "-", title.lower().strip()).strip("-")
    return f"{base}-{year}" if year else base


def ensure_source(conn: sqlite3.Connection) -> int:
    conn.execute(
        "INSERT OR IGNORE INTO sources (slug, name, base_url, type, enabled, is_legal) "
        "VALUES ('archive_org', 'Internet Archive', 'https://archive.org', 'public', 1, 1)"
    )
    conn.commit()
    row = conn.execute("SELECT id FROM sources WHERE slug='archive_org'").fetchone()
    return row[0]


def upsert_title(conn: sqlite3.Connection, doc: dict, playable_file: dict) -> int:
    title = doc.get("title") or doc["identifier"]
    year = int(doc["year"]) if doc.get("year") else None

    existing = conn.execute(
        "SELECT id FROM titles WHERE lower(title)=lower(?) AND (year=? OR (year IS NULL AND ? IS NULL))",
        (title, year, year),
    ).fetchone()
    if existing:
        return existing[0]

    base_slug = slugify(title, year)
    slug = base_slug
    suffix = 2
    while conn.execute("SELECT id FROM titles WHERE slug=?", (slug,)).fetchone():
        slug = f"{base_slug}-{suffix}"
        suffix += 1

    now = int(time.time())
    cur = conn.execute(
        "INSERT INTO titles (slug, title, type, year, overview, poster, status, created_at, updated_at) "
        "VALUES (?, ?, 'movie', ?, ?, ?, 'released', ?, ?)",
        (slug, title, year, doc.get("description"), f"https://archive.org/services/img/{doc['identifier']}", now, now),
    )
    conn.commit()
    return cur.lastrowid


def upsert_availability(conn: sqlite3.Connection, title_id: int, source_id: int, doc: dict, playable_file: dict) -> None:
    now = int(time.time())
    quality_options = json.dumps([playable_file["format"]])
    fmt_lower = playable_file["format"].lower()
    format_options = json.dumps(["mp4"]) if ("mp4" in fmt_lower or "h.264" in fmt_lower) else json.dumps(["video"])
    conn.execute(
        "INSERT INTO availability "
        "(title_id, source_id, status, external_id, external_url, quality_options, format_options, last_checked_at, last_success_at) "
        "VALUES (?,?,?,?,?,?,?,?,?) "
        "ON CONFLICT(title_id, source_id) DO UPDATE SET "
        "status=excluded.status, external_id=excluded.external_id, external_url=excluded.external_url, "
        "quality_options=excluded.quality_options, format_options=excluded.format_options, "
        "last_checked_at=excluded.last_checked_at, last_success_at=excluded.last_success_at",
        (title_id, source_id, "available", doc["identifier"], playable_file["url"], quality_options, format_options, now, now),
    )
    conn.commit()


def ingest(db_path: str = "catalog.db", target: int = 500, queries: list[str] | None = None) -> dict:
    queries = queries or DEFAULT_QUERIES
    conn = sqlite3.connect(db_path)
    source_id = ensure_source(conn)
    counts = {"new": 0, "duplicates": 0, "rejected": 0, "errors": 0}
    seen_identifiers: set[str] = set()

    for query in queries:
        page = 1
        while counts["new"] < target:
            docs = search_archive(query, page)
            if not docs:
                break
            for doc in docs:
                if counts["new"] >= target:
                    break
                identifier = doc.get("identifier")
                if not identifier or identifier in seen_identifiers:
                    counts["duplicates"] += 1
                    continue
                seen_identifiers.add(identifier)
                try:
                    if not is_acceptable_item(doc):
                        counts["rejected"] += 1
                        continue
                    metadata = get_item_metadata(identifier)
                    if not metadata:
                        counts["errors"] += 1
                        continue
                    playable = pick_playable_file(metadata, fallback_identifier=identifier)
                    if not playable:
                        counts["rejected"] += 1
                        continue
                    title_id = upsert_title(conn, doc, playable)
                    upsert_availability(conn, title_id, source_id, doc, playable)
                    counts["new"] += 1
                except NotImplementedError:
                    raise
                except Exception as e:
                    log.exception("Error processing %s: %s", identifier, e)
                    counts["errors"] += 1
            page += 1
            if counts["new"] >= target:
                break

    conn.execute(
        "INSERT INTO ingest_log (source_id, ran_at, new_records, rejected_records, duplicates, errors, notes) "
        "VALUES (?,?,?,?,?,?,?)",
        (source_id, int(time.time()), counts["new"], counts["rejected"], counts["duplicates"], counts["errors"],
         f"archive_org ingest target={target}"),
    )
    conn.commit()
    conn.close()
    return counts


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=int, default=500)
    parser.add_argument("--db", default="catalog.db")
    args = parser.parse_args()

    result = ingest(db_path=args.db, target=args.target)
    print(json.dumps(result, indent=2))
