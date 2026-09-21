"""
123Movies scraper adapter (123moviesweb.org).
High-yield adapter extracting actual TMDB IDs directly from URLs.
"""
from __future__ import annotations

import re
import logging
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus
from .base import BaseSiteAdapter

logger = logging.getLogger("streamapp.scraper.movies123")

class Movies123Adapter(BaseSiteAdapter):
    name = "123Movies"
    is_spa = True  # Requires StealthyFetcher for Cloudflare challenge bypass
    base_url = "https://123moviesweb.org"
    per_page = 24
    max_pages_per_genre = 30

    def _extract_items(self, doc: Any) -> List[Dict[str, Any]]:
        items = []
        if not doc:
            return items

        anchors = doc.css("a")
        seen_ids = set()

        for a in anchors:
            href = a.attrib.get("href", "")
            if not href or not ("/movie/" in href or "/tv/" in href or "/watch/" in href):
                continue

            # Format: https://123moviesweb.org/movie/1038392/the-conjuring-last-rites
            tmdb_id_match = re.search(r"/(?:movie|tv)/(\d+)/([^/?#]+)", href)
            tmdb_id = tmdb_id_match.group(1) if tmdb_id_match else ""
            slug = tmdb_id_match.group(2) if tmdb_id_match else ""

            if not slug:
                parts = href.strip("/").split("/")
                slug = parts[-1]

            item_key = tmdb_id or slug
            if item_key in seen_ids:
                continue
            seen_ids.add(item_key)

            # Title
            title_text = a.get_all_text().strip()
            if not title_text:
                img = a.css("img")
                if img:
                    title_text = img[0].attrib.get("alt", "") or img[0].attrib.get("title", "")
            if not title_text:
                title_text = slug.replace("-", " ").title()

            # Poster
            img = a.css("img")
            poster = img[0].attrib.get("src", "") if img else ""
            if poster.startswith("data:image"):
                # Check data-src or fallback to TMDB poster path
                data_src = img[0].attrib.get("data-src", "")
                if data_src:
                    poster = data_src

            media_type = "tv" if "/tv/" in href else "movie"
            item_id = f"m123-{tmdb_id}" if tmdb_id else f"m123-{slug}"

            items.append(self.normalize_item(
                item_id=item_id,
                title=title_text,
                media_type=media_type,
                tmdb_id=tmdb_id,
                poster=poster,
                source_url=href
            ))

        return items

    async def browse_genre(self, genre: str, page: int = 1) -> List[Dict[str, Any]]:
        # Try genre endpoint or general /movies/{page}
        url = f"{self.base_url}/genre/{genre.lower()}/{page}" if page > 1 else f"{self.base_url}/genre/{genre.lower()}"
        doc = await self.fetch_html(url, is_spa=True)
        results = self._extract_items(doc)
        if not results:
            # Fall back to general /movies/{page}
            url = f"{self.base_url}/movies/{page}" if page > 1 else f"{self.base_url}/movies"
            doc = await self.fetch_html(url, is_spa=True)
            results = self._extract_items(doc)
        return results

    async def search(self, query: str, page: int = 1) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/search/{quote_plus(query)}"
        if page > 1:
            url = f"{url}/{page}"
        doc = await self.fetch_html(url, is_spa=True)
        return self._extract_items(doc)

    async def resolve(self, url: str) -> Optional[str]:
        # Extract TMDB ID and return VidSrc mirror
        m = re.search(r"/(?:movie|tv)/(\d+)", url)
        if m:
            tmdb_id = m.group(1)
            return f"https://vidsrc.to/embed/movie/{tmdb_id}"
        return url
