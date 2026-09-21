"""
Base site adapter interface for StreamApp scrapers.
"""
from __future__ import annotations

import re
import asyncio
import logging
from typing import Any, Dict, List, Optional
from scrapling import AsyncFetcher, StealthyFetcher

logger = logging.getLogger("streamapp.scraper.base")

# Global concurrency limiter for headless browser sessions to avoid memory exhaustion
BROWSER_SEMAPHORE = asyncio.Semaphore(2)

STANDARD_GENRES = [
    "Action", "Adventure", "Animation", "Biography", "Comedy", "Crime",
    "Drama", "Family", "Fantasy", "History", "Horror", "Music",
    "Mystery", "Romance", "Sci-Fi", "Thriller", "War", "Western", "Documentary"
]

class BaseSiteAdapter:
    name: str = "base"
    is_spa: bool = False
    base_url: str = ""
    per_page: int = 20
    max_pages_per_genre: int = 50
    genres: List[str] = STANDARD_GENRES

    def __init__(self) -> None:
        self.semaphore = asyncio.Semaphore(2)

    async def fetch_html(self, url: str, is_spa: Optional[bool] = None, timeout: int = 20000) -> Optional[Any]:
        """
        Fetches a page using AsyncFetcher (for SSR) or StealthyFetcher (for SPAs)
        with concurrency protection and timeout.
        """
        use_spa = self.is_spa if is_spa is None else is_spa
        try:
            if use_spa:
                async with BROWSER_SEMAPHORE:
                    return await asyncio.wait_for(
                        StealthyFetcher.async_fetch(url, headless=True, timeout=timeout),
                        timeout=timeout / 1000.0 + 5.0
                    )
            else:
                async with self.semaphore:
                    return await asyncio.wait_for(
                        AsyncFetcher.get(url, timeout=timeout),
                        timeout=timeout / 1000.0 + 5.0
                    )
        except Exception as e:
            logger.warning(f"[{self.name}] Failed to fetch {url}: {e}")
            return None

    def build_streams(self, tmdb_id: str = "", imdb_id: str = "", page_url: str = "", media_type: str = "movie") -> List[Dict[str, Any]]:
        """
        Builds unified stream mirrors for VidSrc, SuperEmbed, and MultiEmbed.
        """
        streams = []
        if tmdb_id:
            if media_type == "tv":
                streams.append({
                    "label": "VidSrc",
                    "provider": "vidsrc",
                    "url": f"https://vidsrc.to/embed/tv/{tmdb_id}/1/1",
                    "quality": "1080p",
                    "format": "embed"
                })
            else:
                streams.append({
                    "label": "VidSrc",
                    "provider": "vidsrc",
                    "url": f"https://vidsrc.to/embed/movie/{tmdb_id}",
                    "quality": "1080p",
                    "format": "embed"
                })

        if imdb_id:
            streams.append({
                "label": "VidSrc.me",
                "provider": "vidsrc",
                "url": f"https://vidsrc.me/embed/movie?imdb={imdb_id}",
                "quality": "1080p",
                "format": "embed"
            })
            streams.append({
                "label": "SuperEmbed",
                "provider": "superembed",
                "url": f"https://multiembed.mov/?video_id={imdb_id}",
                "quality": "1080p",
                "format": "embed"
            })
            streams.append({
                "label": "VidSrc.to",
                "provider": "vidsrc",
                "url": f"https://vidsrc.to/embed/movie/{imdb_id}",
                "quality": "1080p",
                "format": "embed"
            })
            streams.append({
                "label": "2Embed",
                "provider": "2embed",
                "url": f"https://www.2embed.cc/embed/{imdb_id}",
                "quality": "720p",
                "format": "embed"
            })

        if page_url:
            streams.append({
                "label": self.name,
                "provider": self.name.lower(),
                "url": page_url,
                "quality": "720p",
                "format": "page"
            })

        return streams

    def normalize_title(self, raw_title: str) -> tuple[str, Optional[int]]:
        """
        Extracts clean title and 4-digit release year if present.
        """
        if not raw_title:
            return "", None
        clean = raw_title.strip()
        year_match = re.search(r"\(?((?:19|20)\d{2})\)?(?:\s*$|\s*[-–:])", clean)
        year = None
        if year_match:
            try:
                year = int(year_match.group(1))
                clean = re.sub(r"\s*\(?(?:19|20)\d{2}\)?.*$", "", clean).strip()
            except ValueError:
                pass
        return clean, year

    def normalize_item(
        self,
        item_id: str,
        title: str,
        year: Optional[int] = None,
        media_type: str = "movie",
        imdb_id: str = "",
        tmdb_id: str = "",
        genres: Optional[List[str]] = None,
        rating: str = "NR",
        runtime: int = 0,
        overview: str = "",
        poster: str = "",
        backdrop: str = "",
        country: str = "",
        language: str = "en",
        source_url: str = "",
        streams: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Constructs canonical catalog item matching StreamApp unified schema.
        """
        clean_title, parsed_year = self.normalize_title(title)
        final_year = year or parsed_year or 0

        # Ensure valid streams array
        item_streams = streams or self.build_streams(
            tmdb_id=tmdb_id,
            imdb_id=imdb_id,
            page_url=source_url,
            media_type=media_type
        )

        return {
            "id": item_id,
            "source": self.name,
            "title": clean_title or title,
            "year": final_year,
            "type": media_type or "movie",
            "imdbId": imdb_id or "",
            "tmdbId": tmdb_id or "",
            "genres": genres or [],
            "rating": str(rating) if rating is not None else "NR",
            "runtime": runtime or 0,
            "durationMinutes": runtime or 0,
            "overview": overview or "",
            "poster": poster or "",
            "backdrop": backdrop or "",
            "posterPath": "",
            "backdropPath": "",
            "country": country or "",
            "language": language or "en",
            "sourceUrl": source_url or "",
            "sourceName": self.name,
            "sourceOrigin": f"{self.name.lower()}-scraper",
            "streams": item_streams
        }

    async def browse_genre(self, genre: str, page: int = 1) -> List[Dict[str, Any]]:
        """Browse items in genre at specified page."""
        raise NotImplementedError

    async def search(self, query: str, page: int = 1) -> List[Dict[str, Any]]:
        """Search items matching query at specified page."""
        raise NotImplementedError

    async def resolve(self, url: str) -> Optional[str]:
        """Resolve stream embed URL from title/media URL."""
        return None
