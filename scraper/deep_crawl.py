"""
Deep Crawl Engine for StreamApp.
Orchestrates parallel multi-source scraping + TMDb enrichment into high-performance SQLite cache.
"""
from __future__ import annotations

import os
import sys
import re
import time
import json
import asyncio
import urllib.parse
import logging
import argparse
from pathlib import Path
from typing import Any, Dict, List, Optional
import aiosqlite

# Add current dir to path
CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from sites import get_all_adapters, list_adapters
from tmdb_lane import tmdb_lane

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("streamapp.deep_crawl")

DEFAULT_DB_PATH = CURRENT_DIR / "cache.db"

INIT_SQL = """
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA cache_size = -64000;  -- 64MB cache

CREATE TABLE IF NOT EXISTS titles (
  id              TEXT PRIMARY KEY,
  source          TEXT NOT NULL,
  title           TEXT NOT NULL,
  year            INTEGER,
  type            TEXT,
  imdb_id         TEXT,
  tmdb_id         TEXT,
  genres          TEXT,
  rating          TEXT,
  runtime         INTEGER,
  overview        TEXT,
  poster          TEXT,
  backdrop        TEXT,
  country         TEXT,
  language        TEXT,
  source_url      TEXT,
  fetched_at      INTEGER NOT NULL,
  UNIQUE(source, source_url)
);

CREATE INDEX IF NOT EXISTS idx_titles_imdb ON titles(imdb_id);
CREATE INDEX IF NOT EXISTS idx_titles_tmdb ON titles(tmdb_id);
CREATE INDEX IF NOT EXISTS idx_titles_genres ON titles(genres);
CREATE INDEX IF NOT EXISTS idx_titles_year ON titles(year);
CREATE INDEX IF NOT EXISTS idx_titles_title ON titles(title);
CREATE INDEX IF NOT EXISTS idx_titles_country ON titles(country);
CREATE INDEX IF NOT EXISTS idx_titles_source ON titles(source);

CREATE TABLE IF NOT EXISTS crawl_state (
  source          TEXT PRIMARY KEY,
  total           INTEGER,
  last_page       INTEGER,
  last_crawled_at INTEGER,
  in_progress     INTEGER
);
"""

class Database:
    def __init__(self, db_path: Path = DEFAULT_DB_PATH) -> None:
        self.db_path = db_path
        self._conn: Optional[aiosqlite.Connection] = None

    async def connect(self) -> aiosqlite.Connection:
        if self._conn is None:
            self._conn = await aiosqlite.connect(str(self.db_path))
            self._conn.row_factory = aiosqlite.Row
            await self._conn.executescript(INIT_SQL)
            await self._conn.commit()
        return self._conn

    async def close(self) -> None:
        if self._conn:
            await self._conn.close()
            self._conn = None

    async def insert_titles_batch(self, items: List[Dict[str, Any]]) -> int:
        if not items:
            return 0
        conn = await self.connect()
        now = int(time.time())

        rows = []
        for it in items:
            genres_json = json.dumps(it.get("genres") or [])
            rows.append((
                it["id"],
                it.get("source", "unknown"),
                it["title"],
                it.get("year") or 0,
                it.get("type", "movie"),
                it.get("imdbId", ""),
                it.get("tmdbId", ""),
                genres_json,
                str(it.get("rating", "NR")),
                it.get("runtime", 0),
                it.get("overview", ""),
                it.get("poster", ""),
                it.get("backdrop", ""),
                it.get("country", ""),
                it.get("language", "en"),
                it.get("sourceUrl", "") or f"urn:{it['id']}",
                now
            ))

        sql = """
        INSERT OR REPLACE INTO titles (
            id, source, title, year, type, imdb_id, tmdb_id, genres,
            rating, runtime, overview, poster, backdrop, country,
            language, source_url, fetched_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        try:
            cursor = await conn.executemany(sql, rows)
            await conn.commit()
            return cursor.rowcount
        except Exception as e:
            logger.error(f"Error inserting titles batch: {e}")
            return 0

    async def get_total_count(self) -> int:
        conn = await self.connect()
        async with conn.execute("SELECT COUNT(*) FROM titles") as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

    async def get_stats(self) -> Dict[str, Any]:
        conn = await self.connect()
        total = await self.get_total_count()
        by_source = {}
        async with conn.execute("SELECT source, COUNT(*) as count FROM titles GROUP BY source") as cursor:
            async for row in cursor:
                by_source[row["source"]] = row["count"]

        return {
            "total": total,
            "by_source": by_source,
            "tmdb_enabled": tmdb_lane.enabled
        }

    async def get_country_counts(self) -> Dict[str, int]:
        conn = await self.connect()
        counts = {}
        async with conn.execute("SELECT country, COUNT(*) as count FROM titles WHERE country != '' GROUP BY country") as cursor:
            async for row in cursor:
                counts[row["country"]] = row["count"]

        # Aggregate thematic/genre bucket counts for Express router
        thematic_genres = {
            "ANIM": "%Animation%",
            "HORROR": "%Horror%",
            "THRILLER": "%Thriller%",
            "DOC": "%Documentary%",
            "MUSIC": "%Music%",
            "SCIFI": "%Sci-Fi%",
            "ROMANCE": "%Romance%",
            "FAMILY": "%Family%",
        }
        for code, pattern in thematic_genres.items():
            async with conn.execute("SELECT COUNT(*) FROM titles WHERE genres LIKE ?", (pattern,)) as c:
                row = await c.fetchone()
                counts[code] = row[0] if row else 0

        async with conn.execute("SELECT COUNT(*) FROM titles WHERE year > 0 AND year <= 1990") as c:
            row = await c.fetchone()
            counts["CLASSIC"] = row[0] if row else 0

        async with conn.execute("SELECT COUNT(*) FROM titles WHERE genres LIKE '%Action%' AND (title LIKE '%man%' OR title LIKE '%hero%' OR title LIKE '%bat%' OR title LIKE '%spider%' OR title LIKE '%avenger%')") as c:
            row = await c.fetchone()
            counts["HERO"] = row[0] if row else 0

        return counts

    async def get_title_by_id(self, identifier: str) -> Optional[Dict[str, Any]]:
        conn = await self.connect()
        sql = "SELECT * FROM titles WHERE id = ? OR tmdb_id = ? OR imdb_id = ? LIMIT 1"
        async with conn.execute(sql, (identifier, identifier, identifier)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            genres = json.loads(row["genres"]) if row["genres"] else []
            tmdb_id = row["tmdb_id"] or ""
            imdb_id = row["imdb_id"] or ""
            m_type = row["type"] or "movie"
            streams = []
            if tmdb_id:
                if m_type == "tv":
                    streams.append({"label": "VidSrc.me", "provider": "vidsrc", "url": f"https://vidsrc.me/embed/tv?tmdb={tmdb_id}&season=1&episode=1", "quality": "1080p", "format": "embed"})
                    streams.append({"label": "SuperEmbed", "provider": "superembed", "url": f"https://multiembed.mov/?video_id={tmdb_id}&tmdb=1&s=1&e=1", "quality": "1080p", "format": "embed"})
                    streams.append({"label": "VidSrc.to", "provider": "vidsrc", "url": f"https://vidsrc.to/embed/tv/{tmdb_id}/1/1", "quality": "1080p", "format": "embed"})
                    streams.append({"label": "2Embed", "provider": "2embed", "url": f"https://www.2embed.cc/embedtv/{tmdb_id}&s=1&e=1", "quality": "720p", "format": "embed"})
                else:
                    streams.append({"label": "VidSrc.me", "provider": "vidsrc", "url": f"https://vidsrc.me/embed/movie?tmdb={tmdb_id}", "quality": "1080p", "format": "embed"})
                    streams.append({"label": "SuperEmbed", "provider": "superembed", "url": f"https://multiembed.mov/?video_id={tmdb_id}&tmdb=1", "quality": "1080p", "format": "embed"})
                    streams.append({"label": "VidSrc.to", "provider": "vidsrc", "url": f"https://vidsrc.to/embed/movie/{tmdb_id}", "quality": "1080p", "format": "embed"})
                    streams.append({"label": "2Embed", "provider": "2embed", "url": f"https://www.2embed.cc/embed/{tmdb_id}", "quality": "720p", "format": "embed"})
            elif imdb_id:
                if m_type == "tv":
                    streams.append({"label": "VidSrc.me (IMDb)", "provider": "vidsrc", "url": f"https://vidsrc.me/embed/tv?imdb={imdb_id}&season=1&episode=1", "quality": "1080p", "format": "embed"})
                    streams.append({"label": "SuperEmbed", "provider": "superembed", "url": f"https://multiembed.mov/?video_id={imdb_id}&s=1&e=1", "quality": "1080p", "format": "embed"})
                    streams.append({"label": "2Embed", "provider": "2embed", "url": f"https://www.2embed.cc/embedtv/{imdb_id}&s=1&e=1", "quality": "720p", "format": "embed"})
                else:
                    streams.append({"label": "VidSrc.me (IMDb)", "provider": "vidsrc", "url": f"https://vidsrc.me/embed/movie?imdb={imdb_id}", "quality": "1080p", "format": "embed"})
                    streams.append({"label": "SuperEmbed", "provider": "superembed", "url": f"https://multiembed.mov/?video_id={imdb_id}", "quality": "1080p", "format": "embed"})
                    streams.append({"label": "2Embed", "provider": "2embed", "url": f"https://www.2embed.cc/embed/{imdb_id}", "quality": "720p", "format": "embed"})

            if row["title"]:
                yt_term = f"{row['title']} Episode 1 full episode HD" if m_type == "tv" else f"{row['title']} full movie HD"
                streams.append({
                    "label": "YouTube (Official HD)",
                    "provider": "youtube",
                    "url": f"https://www.youtube-nocookie.com/embed?listType=search&list={urllib.parse.quote_plus(yt_term)}",
                    "quality": "1080p",
                    "format": "embed"
                })

            raw_poster = row["poster"] or ""
            if not raw_poster or raw_poster.startswith("/") or any(k in raw_poster for k in ["_pk.jpg", "_tr.jpg", "_eg.jpg", "welad", "hashashin", "sang_e_mah"]):
                clean_poster = "https://image.tmdb.org/t/p/w500/7WTsnHkbA0FaG6R9twfFde0I9hl.jpg"
            else:
                clean_poster = raw_poster

            return {
                "id": row["id"],
                "source": row["source"],
                "title": row["title"],
                "year": row["year"],
                "type": row["type"],
                "imdbId": imdb_id,
                "tmdbId": tmdb_id,
                "genres": genres,
                "rating": row["rating"],
                "runtime": row["runtime"],
                "durationMinutes": row["runtime"],
                "overview": row["overview"] or "",
                "poster": clean_poster,
                "backdrop": row["backdrop"] or clean_poster,
                "country": row["country"] or "",
                "language": row["language"] or "en",
                "sourceUrl": row["source_url"] or "",
                "sourceName": row["source"],
                "sourceOrigin": f"{row['source'].lower()}-scraper",
                "streams": streams
            }

    async def query_titles(
        self,
        query: str = "",
        genre: str = "",
        country: str = "",
        language: str = "",
        max_year: Optional[int] = None,
        page: int = 1,
        page_size: int = 50
    ) -> List[Dict[str, Any]]:
        conn = await self.connect()
        conditions = []
        params: List[Any] = []

        # Always require at least one playable ID and exclude synthetic volume duplicates
        conditions.append("((tmdb_id IS NOT NULL AND tmdb_id != '') OR (imdb_id IS NOT NULL AND imdb_id != ''))")
        conditions.append("(title NOT LIKE '%Volume %')")

        if query:
            q_clean = query.strip()
            q_fuzzy = "%".join(q_clean.replace("-", " ").split())
            sub_fuzzy = re.sub(r"(spider|bat|super|iron|ant|aqua|x)(man|men)", r"\1%\2", q_clean, flags=re.I)
            conditions.append("(title LIKE ? OR overview LIKE ? OR title LIKE ? OR title LIKE ?)")
            params.extend([f"%{q_clean}%", f"%{q_clean}%", f"%{q_fuzzy}%", f"%{sub_fuzzy}%"])

        if genre and genre.lower() != "all":
            conditions.append("genres LIKE ?")
            params.append(f"%{genre}%")

        if country and country.lower() != "all":
            conditions.append("country = ?")
            params.append(country.upper())

        if language and language.lower() != "all":
            conditions.append("(language = ? OR language LIKE ?)")
            params.extend([language.lower(), f"%{language.lower()}%"])

        if max_year is not None:
            conditions.append("year > 0 AND year <= ?")
            params.append(max_year)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        offset = (page - 1) * page_size
        sql = f"""
        SELECT * FROM titles
        {where_clause}
        ORDER BY year DESC, fetched_at DESC
        LIMIT ? OFFSET ?
        """
        params.extend([page_size, offset])

        items = []
        async with conn.execute(sql, params) as cursor:
            async for row in cursor:
                genres = json.loads(row["genres"]) if row["genres"] else []
                # Reconstruct streams
                tmdb_id = row["tmdb_id"] or ""
                imdb_id = row["imdb_id"] or ""
                m_type = row["type"] or "movie"
                streams = []
                m_title = row["title"] or ""
                if tmdb_id:
                    if m_type == "tv":
                        streams.append({"label": "VidSrc.me", "provider": "vidsrc", "url": f"https://vidsrc.me/embed/tv?tmdb={tmdb_id}&season=1&episode=1", "quality": "1080p", "format": "embed"})
                        streams.append({"label": "SuperEmbed", "provider": "superembed", "url": f"https://multiembed.mov/?video_id={tmdb_id}&tmdb=1&s=1&e=1", "quality": "1080p", "format": "embed"})
                        streams.append({"label": "VidSrc.to", "provider": "vidsrc", "url": f"https://vidsrc.to/embed/tv/{tmdb_id}/1/1", "quality": "1080p", "format": "embed"})
                        streams.append({"label": "2Embed", "provider": "2embed", "url": f"https://www.2embed.cc/embedtv/{tmdb_id}&s=1&e=1", "quality": "720p", "format": "embed"})
                    else:
                        streams.append({"label": "VidSrc.me", "provider": "vidsrc", "url": f"https://vidsrc.me/embed/movie?tmdb={tmdb_id}", "quality": "1080p", "format": "embed"})
                        streams.append({"label": "SuperEmbed", "provider": "superembed", "url": f"https://multiembed.mov/?video_id={tmdb_id}&tmdb=1", "quality": "1080p", "format": "embed"})
                        streams.append({"label": "VidSrc.to", "provider": "vidsrc", "url": f"https://vidsrc.to/embed/movie/{tmdb_id}", "quality": "1080p", "format": "embed"})
                        streams.append({"label": "2Embed", "provider": "2embed", "url": f"https://www.2embed.cc/embed/{tmdb_id}", "quality": "720p", "format": "embed"})
                elif imdb_id:
                    if m_type == "tv":
                        streams.append({"label": "VidSrc.me", "provider": "vidsrc", "url": f"https://vidsrc.me/embed/tv?imdb={imdb_id}&season=1&episode=1", "quality": "1080p", "format": "embed"})
                        streams.append({"label": "SuperEmbed", "provider": "superembed", "url": f"https://multiembed.mov/?video_id={imdb_id}&s=1&e=1", "quality": "1080p", "format": "embed"})
                        streams.append({"label": "VidSrc.to", "provider": "vidsrc", "url": f"https://vidsrc.to/embed/tv/{imdb_id}/1/1", "quality": "1080p", "format": "embed"})
                        streams.append({"label": "2Embed", "provider": "2embed", "url": f"https://www.2embed.cc/embedtv/{imdb_id}&s=1&e=1", "quality": "720p", "format": "embed"})
                    else:
                        streams.append({"label": "VidSrc.me", "provider": "vidsrc", "url": f"https://vidsrc.me/embed/movie?imdb={imdb_id}", "quality": "1080p", "format": "embed"})
                        streams.append({"label": "SuperEmbed", "provider": "superembed", "url": f"https://multiembed.mov/?video_id={imdb_id}", "quality": "1080p", "format": "embed"})
                        streams.append({"label": "VidSrc.to", "provider": "vidsrc", "url": f"https://vidsrc.to/embed/movie/{imdb_id}", "quality": "1080p", "format": "embed"})
                        streams.append({"label": "2Embed", "provider": "2embed", "url": f"https://www.2embed.cc/embed/{imdb_id}", "quality": "720p", "format": "embed"})

                if m_title:
                    clean_m_title = m_title.replace(" - S1E1", "").strip()
                    yt_q = f"{clean_m_title} Episode 1 full episode HD" if m_type == "tv" else f"{clean_m_title} full movie HD"
                    streams.append({
                        "label": "YouTube (Official HD)",
                        "provider": "youtube",
                        "url": f"https://www.youtube-nocookie.com/embed?listType=search&list={urllib.parse.quote(yt_q)}",
                        "quality": "1080p",
                        "format": "embed"
                    })

                raw_poster = row["poster"] or ""
                if not raw_poster or raw_poster.startswith("/") or any(k in raw_poster for k in ["_pk.jpg", "_tr.jpg", "_eg.jpg", "welad", "hashashin", "sang_e_mah"]):
                    clean_poster = "https://image.tmdb.org/t/p/w500/7WTsnHkbA0FaG6R9twfFde0I9hl.jpg"
                else:
                    clean_poster = raw_poster

                items.append({
                    "id": row["id"],
                    "source": row["source"],
                    "title": row["title"],
                    "year": row["year"],
                    "type": row["type"],
                    "imdbId": imdb_id,
                    "tmdbId": tmdb_id,
                    "genres": genres,
                    "rating": row["rating"],
                    "runtime": row["runtime"],
                    "durationMinutes": row["runtime"],
                    "overview": row["overview"] or "",
                    "poster": clean_poster,
                    "backdrop": row["backdrop"] or clean_poster,
                    "posterPath": "",
                    "backdropPath": "",
                    "country": row["country"] or "",
                    "language": row["language"] or "en",
                    "sourceUrl": row["source_url"] or "",
                    "sourceName": row["source"],
                    "sourceOrigin": f"{row['source'].lower()}-scraper",
                    "streams": streams
                })
        return items

async def seed_curated_catalog(db: Database) -> int:
    """Loads curated baseline titles from MovieBox catalog (854 curated movies + TV series)."""
    curated_json = CURRENT_DIR / "curated_catalog.json"
    moviebox_file = CURRENT_DIR.parent / "backend" / "src" / "scrapers" / "MovieBoxScraper.js"
    
    # Read country mapping from routes.js if available
    id_to_country = {}
    routes_file = CURRENT_DIR.parent / "backend" / "src" / "api" / "routes.js"
    if routes_file.exists():
        try:
            r_content = routes_file.read_text(encoding="utf-8")
            bucket_re = re.finditer(r"'([a-z0-9_-]+)':\s*\{\s*code:\s*'([A-Z]{2})'[\s\S]*?ids:\s*\[([^\]]+)\]", r_content)
            for bm in bucket_re:
                code = bm.group(2)
                id_list = [i.strip(" '\"]") for i in bm.group(3).split(",") if i.strip(" '\"]")]
                for cid in id_list:
                    id_to_country[cid] = code
        except Exception as e:
            logger.warning(f"Could not load routes.js country buckets: {e}")

    raw_items = []
    if curated_json.exists():
        try:
            raw_items = json.loads(curated_json.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning(f"Error loading {curated_json}: {e}")

    items = []
    if raw_items:
        for entry in raw_items:
            item_id = entry.get("id")
            if not item_id:
                continue
            poster_path = entry.get("posterPath", "")
            if poster_path and poster_path.startswith("/"):
                poster = f"https://image.tmdb.org/t/p/w500{poster_path}"
            elif poster_path and poster_path.startswith("http"):
                poster = poster_path
            else:
                poster = "https://image.tmdb.org/t/p/w500/7WTsnHkbA0FaG6R9twfFde0I9hl.jpg"

            backdrop_path = entry.get("backdropPath", "")
            if backdrop_path and backdrop_path.startswith("/"):
                backdrop = f"https://image.tmdb.org/t/p/w1280{backdrop_path}"
            elif backdrop_path and backdrop_path.startswith("http"):
                backdrop = backdrop_path
            else:
                backdrop = poster

            item_type = entry.get("type", "movie")
            tmdb = str(entry.get("tmdbId", ""))
            imdb = str(entry.get("imdbId", ""))

            items.append({
                "id": item_id,
                "source": "curated",
                "title": entry.get("title", item_id),
                "year": entry.get("year", 2024),
                "type": item_type,
                "imdbId": imdb,
                "tmdbId": tmdb,
                "genres": entry.get("genres", []),
                "rating": str(entry.get("rating", "8.0")),
                "runtime": entry.get("runtime", 120),
                "overview": entry.get("overview", ""),
                "poster": poster,
                "backdrop": backdrop,
                "country": id_to_country.get(item_id, ""),
                "sourceUrl": f"https://www.themoviedb.org/{item_type}/{tmdb}" if tmdb else f"https://www.imdb.com/title/{imdb}"
            })
    elif moviebox_file.exists():
        try:
            content = moviebox_file.read_text(encoding="utf-8")
            pattern_m = re.compile(
                r"m\(\s*'([^']+)'\s*,\s*('[^']+'|\"[^\"]+\")\s*,\s*(\d+)\s*,\s*'([^']*)'\s*,\s*'([^']*)'\s*,\s*\[([^\]]*)\]\s*,\s*([0-9.]+)\s*,\s*(\d+)\s*,\s*('((?:[^'\\]|\\.)*)'|\"((?:[^\"\\]|\\.)*)\")\s*,\s*'([^']*)'",
                re.MULTILINE
            )
            pattern_v = re.compile(
                r"v\(\s*'([^']+)'\s*,\s*('[^']+'|\"[^\"]+\")\s*,\s*(\d+)\s*,\s*'([^']*)'\s*,\s*'([^']*)'\s*,\s*(\d+)\s*,\s*\[([^\]]*)\]\s*,\s*([0-9.]+)\s*,\s*(\d+)\s*,\s*('((?:[^'\\]|\\.)*)'|\"((?:[^\"\\]|\\.)*)\")\s*,\s*'([^']*)'",
                re.MULTILINE
            )
            for m in pattern_m.finditer(content):
                item_id, title_raw, year, imdb, tmdb, raw_genres, rating, runtime = m.group(1), m.group(2).strip("'\""), int(m.group(3)), m.group(4), m.group(5), m.group(6), m.group(7), int(m.group(8))
                poster_path = m.group(13)
                poster = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path and not poster_path.startswith("http") else poster_path
                items.append({
                    "id": item_id, "source": "curated", "title": title_raw, "year": year, "type": "movie",
                    "imdbId": imdb, "tmdbId": tmdb, "genres": [g.strip(" '\"]") for g in raw_genres.split(",") if g.strip(" '\"]")],
                    "rating": rating, "runtime": runtime, "overview": m.group(10) or "", "poster": poster,
                    "country": id_to_country.get(item_id, ""),
                    "sourceUrl": f"https://www.themoviedb.org/movie/{tmdb}" if tmdb else f"https://www.imdb.com/title/{imdb}"
                })
            for v in pattern_v.finditer(content):
                item_id, title_raw, year, imdb, tmdb, seasons, raw_genres, rating, runtime = v.group(1), v.group(2).strip("'\""), int(v.group(3)), v.group(4), v.group(5), int(v.group(6)), v.group(7), v.group(8), int(v.group(9))
                poster_path = v.group(14)
                poster = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path and not poster_path.startswith("http") else poster_path
                items.append({
                    "id": item_id, "source": "curated", "title": title_raw, "year": year, "type": "tv",
                    "imdbId": imdb, "tmdbId": tmdb, "genres": [g.strip(" '\"]") for g in raw_genres.split(",") if g.strip(" '\"]")],
                    "rating": rating, "runtime": runtime, "overview": v.group(11) or "", "poster": poster,
                    "country": id_to_country.get(item_id, ""),
                    "sourceUrl": f"https://www.themoviedb.org/tv/{tmdb}" if tmdb else f"https://www.imdb.com/title/{imdb}"
                })
        except Exception as e:
            logger.error(f"Fallback parsing error: {e}")

    count = await db.insert_titles_batch(items)
    logger.info(f"Seeded {count} curated titles (Movies & TV Series) into cache.db")

    # Clean unplayable junk and bad posters
    try:
        conn = await db.connect()
        await conn.execute("DELETE FROM titles WHERE (imdb_id IS NULL OR imdb_id = '') AND (tmdb_id IS NULL OR tmdb_id = '')")
        await conn.execute("DELETE FROM titles WHERE poster LIKE '%/poster_%' OR title LIKE '%Volume %'")
        await conn.execute("""
            UPDATE titles
            SET poster = 'https://image.tmdb.org/t/p/w500/7WTsnHkbA0FaG6R9twfFde0I9hl.jpg',
                backdrop = 'https://image.tmdb.org/t/p/w500/7WTsnHkbA0FaG6R9twfFde0I9hl.jpg'
            WHERE poster IS NULL OR poster = '' OR poster LIKE '/%'
               OR poster LIKE '%_pk.jpg%' OR poster LIKE '%_tr.jpg%' OR poster LIKE '%_eg.jpg%'
        """)
        await conn.commit()
    except Exception as ce:
        logger.warning(f"Cleanup error: {ce}")

    # Seed rich national slates per 15-page Global Audiovisual Inventory census
    try:
        from national_slates import get_national_slates
        slates = get_national_slates()
        s_count = await db.insert_titles_batch(slates)
        logger.info(f"Seeded {s_count} national slate titles into cache.db")
        count += s_count
    except Exception as se:
        logger.warning(f"Failed to seed national slates: {se}")

    return count


async def crawl_adapter(adapter, db: Database, target: int) -> int:
    """Crawls an individual adapter across genres and pages."""
    added = 0
    logger.info(f"[{adapter.name}] Starting crawl across {len(adapter.genres)} genres...")

    for genre in adapter.genres:
        current_total = await db.get_total_count()
        if current_total >= target:
            logger.info(f"Target of {target} titles reached. Stopping crawl.")
            break

        max_pages = min(adapter.max_pages_per_genre, 100)
        consecutive_zeros = 0
        for page in range(1, max_pages + 1):
            try:
                items = await adapter.browse_genre(genre, page)
                if not items:
                    break
                inserted = await db.insert_titles_batch(items)
                added += inserted
                if inserted == 0:
                    consecutive_zeros += 1
                    if consecutive_zeros >= 2:
                        break
                else:
                    consecutive_zeros = 0

                await asyncio.sleep(0.3)  # Politeness delay
            except Exception as e:
                logger.warning(f"[{adapter.name}] Error crawling {genre} p{page}: {e}")
                break

    logger.info(f"[{adapter.name}] Crawl finished. Added {added} items.")
    return added

async def crawl_tmdb_lane(db: Database, target: int) -> int:
    """Fans out TMDb discover endpoints if TMDB_API_KEY is configured."""
    if not tmdb_lane.enabled:
        return 0

    logger.info("[TMDb Lane] Starting high-volume discovery across countries & genres...")
    added = 0
    countries = ["US", "IN", "PK", "KR", "JP", "GB", "FR", "TR", "NG", "EG", "CN", "IT", "ES", "DE"]

    for country in countries:
        current_total = await db.get_total_count()
        if current_total >= target:
            break

        for page in range(1, 20):
            try:
                m_items = await tmdb_lane.discover_movies(country=country, page=page)
                t_items = await tmdb_lane.discover_tv(country=country, page=page)
                combined = m_items + t_items
                if not combined:
                    break
                inserted = await db.insert_titles_batch(combined)
                added += inserted
                await asyncio.sleep(0.2)
            except Exception as e:
                logger.warning(f"[TMDb Lane] Error crawling {country} p{page}: {e}")
                break

    logger.info(f"[TMDb Lane] Finished. Added {added} titles.")
    return added

async def deep_warm_all(target: int = 100000, db_path: Path = DEFAULT_DB_PATH) -> Dict[str, Any]:
    """
    Main orchestration routine.
    Crawls baseline, all 10 adapters, and TMDb lane until target reached or sources exhausted.
    """
    db = Database(db_path)
    await db.connect()

    start_time = time.time()
    logger.info(f"--- Starting Deep Warmup (Target: {target:,} titles) ---")

    # 1. Seed baseline
    await seed_curated_catalog(db)

    # 2. Run adapters with bounded concurrency
    adapters = get_all_adapters()
    semaphore = asyncio.Semaphore(3)

    async def worker(ad):
        async with semaphore:
            return await crawl_adapter(ad, db, target)

    tasks = [worker(ad) for ad in adapters]
    if tmdb_lane.enabled:
        tasks.append(crawl_tmdb_lane(db, target))

    await asyncio.gather(*tasks, return_exceptions=True)

    elapsed = time.time() - start_time
    stats = await db.get_stats()
    logger.info(f"--- Deep Warmup Complete in {elapsed:.1f}s. Total titles: {stats['total']:,} ---")
    return stats

def main():
    parser = argparse.ArgumentParser(description="StreamApp Deep Crawl Engine")
    parser.add_argument("--target", type=int, default=100000, help="Target unique titles (default: 100,000)")
    parser.add_argument("--db", type=str, default=str(DEFAULT_DB_PATH), help="Path to SQLite cache DB")
    args = parser.parse_args()

    asyncio.run(deep_warm_all(target=args.target, db_path=Path(args.db)))

if __name__ == "__main__":
    main()
