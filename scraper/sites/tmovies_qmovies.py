"""
TMovies / QMovies scraper adapter (qmovies.co / tmovies.watch).
"""
from __future__ import annotations

import re
import logging
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus
from .base import BaseSiteAdapter

logger = logging.getLogger("streamapp.scraper.tmovies")

class TMoviesAdapter(BaseSiteAdapter):
    name = "TMovies"
    is_spa = True
    base_url = "https://qmovies.co"
    per_page = 20
    max_pages_per_genre = 25

    def _extract_items(self, doc: Any) -> List[Dict[str, Any]]:
        items = []
        if not doc:
            return items

        elements = doc.css(".item, .movie, .film, a[href*='/movie/'], a[href*='/watch/']")
        seen_links = set()

        for el in elements:
            link = el if el.tag == "a" else el.css("a")
            if not link:
                continue
            first_link = link[0] if isinstance(link, list) else link
            href = first_link.attrib.get("href", "")
            if not href or href in seen_links:
                continue

            seen_links.add(href)
            slug = href.strip("/").split("/")[-1]
            title = first_link.get_all_text().strip()
            if not title:
                title = slug.replace("-", " ").title()

            img = el.css("img") if el.tag != "a" else []
            poster = img[0].attrib.get("src", "") if img else ""

            items.append(self.normalize_item(
                item_id=f"tm-{slug}",
                title=title,
                poster=poster,
                source_url=f"{self.base_url}{href}" if href.startswith("/") else href
            ))

        return items

    async def browse_genre(self, genre: str, page: int = 1) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/genre/{genre.lower()}?page={page}"
        doc = await self.fetch_html(url, is_spa=True)
        return self._extract_items(doc)

    async def search(self, query: str, page: int = 1) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/search?keyword={quote_plus(query)}"
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
