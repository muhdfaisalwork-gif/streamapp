"""
Donkey scraper adapter (donkey.to).
SPA aggregator with movie/tv browsing and search endpoints.
"""
from __future__ import annotations

import re
import logging
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus
from .base import BaseSiteAdapter

logger = logging.getLogger("streamapp.scraper.donkey")

class DonkeyAdapter(BaseSiteAdapter):
    name = "Donkey"
    is_spa = True
    base_url = "https://donkey.to"
    per_page = 20
    max_pages_per_genre = 20

    def _extract_items(self, doc: Any) -> List[Dict[str, Any]]:
        items = []
        if not doc:
            return items

        anchors = doc.css("a[href*='/watch/'], a[href*='/movie/'], a[href*='/tv/'], .movie, article")
        seen_urls = set()

        for el in anchors:
            a = el if el.tag == "a" else el.css("a")
            if not a:
                continue
            first_a = a[0] if isinstance(a, list) else a
            href = first_a.attrib.get("href", "")
            if not href or href in seen_urls:
                continue

            seen_urls.add(href)
            slug = href.strip("/").split("/")[-1]
            title = first_a.get_all_text().strip()
            if not title:
                img = first_a.css("img")
                title = img[0].attrib.get("alt", "") if img else slug.replace("-", " ").title()

            img = first_a.css("img")
            poster = img[0].attrib.get("src", "") if img else ""

            # Check for IMDb / TMDb in href
            imdb_id = ""
            tmdb_id = ""
            imdb_match = re.search(r"(tt\d{6,})", href)
            if imdb_match:
                imdb_id = imdb_match.group(1)
            tmdb_match = re.search(r"/(\d{4,8})", href)
            if tmdb_match:
                tmdb_id = tmdb_match.group(1)

            full_url = f"{self.base_url}{href}" if href.startswith("/") else href
            items.append(self.normalize_item(
                item_id=f"donkey-{slug}",
                title=title,
                imdb_id=imdb_id,
                tmdb_id=tmdb_id,
                poster=poster,
                source_url=full_url
            ))

        return items

    async def browse_genre(self, genre: str, page: int = 1) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/media/movie?genre={quote_plus(genre)}&page={page}"
        doc = await self.fetch_html(url, is_spa=True)
        results = self._extract_items(doc)
        if not results:
            url = f"{self.base_url}/featured?mediaType=movie"
            doc = await self.fetch_html(url, is_spa=True)
            results = self._extract_items(doc)
        return results

    async def search(self, query: str, page: int = 1) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/search?query={quote_plus(query)}"
        doc = await self.fetch_html(url, is_spa=True)
        return self._extract_items(doc)

    async def resolve(self, url: str) -> Optional[str]:
        doc = await self.fetch_html(url, is_spa=True)
        if not doc:
            return None
        for ifr in doc.css("iframe"):
            src = ifr.attrib.get("src", "")
            if src:
                return src
        return None
