"""
TMDb Enrichment Lane (Lane B & Lane C).
Gracefully activates when TMDB_API_KEY is present in environment or .env.
"""
from __future__ import annotations

import os
import logging
from typing import Any, Dict, List, Optional
import httpx

logger = logging.getLogger("streamapp.scraper.tmdb")

TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"
TMDB_BACKDROP_BASE = "https://image.tmdb.org/t/p/w1280"

# TMDb Genre ID mapping
TMDB_GENRE_MAP = {
    28: "Action", 12: "Adventure", 16: "Animation", 35: "Comedy",
    80: "Crime", 99: "Documentary", 18: "Drama", 10751: "Family",
    14: "Fantasy", 36: "History", 27: "Horror", 10402: "Music",
    9648: "Mystery", 10749: "Romance", 878: "Sci-Fi", 10770: "TV Movie",
    53: "Thriller", 10752: "War", 37: "Western",
    10759: "Action & Adventure", 10762: "Kids", 10763: "News",
    10764: "Reality", 10765: "Sci-Fi & Fantasy", 10766: "Soap",
    10767: "Talk", 10768: "War & Politics"
}

class TmdbLane:
    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or os.getenv("TMDB_API_KEY", "").strip()
        self.enabled = bool(self.api_key)
        self.client = httpx.AsyncClient(timeout=10.0)

    def status(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "reason": "active" if self.enabled else "no TMDB_API_KEY configured"
        }

    def _normalize_tmdb_item(self, raw: Dict[str, Any], media_type: str = "movie") -> Dict[str, Any]:
        tmdb_id = str(raw.get("id", ""))
        title = raw.get("title") or raw.get("name") or raw.get("original_title") or "Untitled"
        release_date = raw.get("release_date") or raw.get("first_air_date") or ""
        year = int(release_date[:4]) if release_date and len(release_date) >= 4 and release_date[:4].isdigit() else 0

        genre_ids = raw.get("genre_ids") or []
        genres = [TMDB_GENRE_MAP[gid] for gid in genre_ids if gid in TMDB_GENRE_MAP]

        poster_path = raw.get("poster_path")
        poster = f"{TMDB_IMAGE_BASE}{poster_path}" if poster_path else ""

        backdrop_path = raw.get("backdrop_path")
        backdrop = f"{TMDB_BACKDROP_BASE}{backdrop_path}" if backdrop_path else ""

        vote_avg = raw.get("vote_average", 0.0)
        rating = f"{vote_avg:.1f}" if vote_avg > 0 else "NR"
        overview = raw.get("overview", "")
        origin_country = raw.get("origin_country", [])
        country = origin_country[0] if isinstance(origin_country, list) and origin_country else ""
        original_language = raw.get("original_language", "en")

        streams = []
        if media_type == "tv":
            streams.append({
                "label": "VidSrc.me",
                "provider": "vidsrc",
                "url": f"https://vidsrc.me/embed/tv?tmdb={tmdb_id}&season=1&episode=1",
                "quality": "1080p",
                "format": "embed"
            })
            streams.append({
                "label": "SuperEmbed",
                "provider": "superembed",
                "url": f"https://multiembed.mov/?video_id={tmdb_id}&tmdb=1&s=1&e=1",
                "quality": "1080p",
                "format": "embed"
            })
            streams.append({
                "label": "VidSrc.to",
                "provider": "vidsrc",
                "url": f"https://vidsrc.to/embed/tv/{tmdb_id}/1/1",
                "quality": "1080p",
                "format": "embed"
            })
            streams.append({
                "label": "2Embed",
                "provider": "2embed",
                "url": f"https://www.2embed.cc/embedtv/{tmdb_id}&s=1&e=1",
                "quality": "720p",
                "format": "embed"
            })
        else:
            streams.append({
                "label": "VidSrc.me",
                "provider": "vidsrc",
                "url": f"https://vidsrc.me/embed/movie?tmdb={tmdb_id}",
                "quality": "1080p",
                "format": "embed"
            })
            streams.append({
                "label": "SuperEmbed",
                "provider": "superembed",
                "url": f"https://multiembed.mov/?video_id={tmdb_id}&tmdb=1",
                "quality": "1080p",
                "format": "embed"
            })
            streams.append({
                "label": "VidSrc.to",
                "provider": "vidsrc",
                "url": f"https://vidsrc.to/embed/movie/{tmdb_id}",
                "quality": "1080p",
                "format": "embed"
            })
            streams.append({
                "label": "2Embed",
                "provider": "2embed",
                "url": f"https://www.2embed.cc/embed/{tmdb_id}",
                "quality": "720p",
                "format": "embed"
            })

        return {
            "id": f"tmdb-{tmdb_id}",
            "source": "TMDb",
            "title": title,
            "year": year,
            "type": media_type,
            "imdbId": "",
            "tmdbId": tmdb_id,
            "genres": genres,
            "rating": rating,
            "runtime": 0,
            "durationMinutes": 0,
            "overview": overview,
            "poster": poster,
            "backdrop": backdrop,
            "posterPath": poster_path or "",
            "backdropPath": backdrop_path or "",
            "country": country,
            "language": original_language,
            "sourceUrl": f"https://www.themoviedb.org/{media_type}/{tmdb_id}",
            "sourceName": "TMDb",
            "sourceOrigin": "tmdb-lane",
            "streams": streams
        }

    async def discover_movies(self, country: Optional[str] = None, genre_id: Optional[int] = None, page: int = 1) -> List[Dict[str, Any]]:
        if not self.enabled:
            return []
        params: Dict[str, Any] = {
            "api_key": self.api_key,
            "page": min(500, max(1, page)),
            "sort_by": "popularity.desc"
        }
        if country:
            params["with_origin_country"] = country.upper()
        if genre_id:
            params["with_genres"] = genre_id

        try:
            res = await self.client.get(f"{TMDB_BASE_URL}/discover/movie", params=params)
            if res.status_code == 200:
                data = res.json()
                return [self._normalize_tmdb_item(m, "movie") for m in data.get("results", [])]
        except Exception as e:
            logger.warning(f"[TmdbLane] discover_movies error: {e}")
        return []

    async def discover_tv(self, country: Optional[str] = None, genre_id: Optional[int] = None, page: int = 1) -> List[Dict[str, Any]]:
        if not self.enabled:
            return []
        params: Dict[str, Any] = {
            "api_key": self.api_key,
            "page": min(500, max(1, page)),
            "sort_by": "popularity.desc"
        }
        if country:
            params["with_origin_country"] = country.upper()
        if genre_id:
            params["with_genres"] = genre_id

        try:
            res = await self.client.get(f"{TMDB_BASE_URL}/discover/tv", params=params)
            if res.status_code == 200:
                data = res.json()
                return [self._normalize_tmdb_item(t, "tv") for t in data.get("results", [])]
        except Exception as e:
            logger.warning(f"[TmdbLane] discover_tv error: {e}")
        return []

    async def search(self, query: str, page: int = 1) -> List[Dict[str, Any]]:
        if not self.enabled or not query:
            return []
        try:
            res = await self.client.get(
                f"{TMDB_BASE_URL}/search/multi",
                params={"api_key": self.api_key, "query": query, "page": page}
            )
            if res.status_code == 200:
                data = res.json()
                results = []
                for item in data.get("results", []):
                    m_type = item.get("media_type")
                    if m_type in ["movie", "tv"]:
                        results.append(self._normalize_tmdb_item(item, m_type))
                return results
        except Exception as e:
            logger.warning(f"[TmdbLane] search error: {e}")
        return []

# Singleton instance
tmdb_lane = TmdbLane()
