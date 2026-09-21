"""
BeeTV scraper adapter (beetvs.com.co).
Search-driven and post-category extraction.
"""
from __future__ import annotations

import re
import logging
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus
from .base import BaseSiteAdapter

logger = logging.getLogger("streamapp.scraper.beetv")

class BeeTvAdapter(BaseSiteAdapter):
    name = "BeeTV"
    is_spa = False
    base_url = "https://beetvs.com.co"
    per_page = 20
    max_pages_per_genre = 25

    def _extract_items(self, doc: Any) -> List[Dict[str, Any]]:
        items = []
        if not doc:
            return items

        elements = doc.css(".movie-item, .video-item, article, [data-item], .entry-title a, h2 a")
        seen_links = set()

        for el in elements:
            link = el if el.tag == "a" else el.css("a")
            if not link:
                continue
            first_link = link[0] if isinstance(link, list) else link
            href = first_link.attrib.get("href", "")
            title = first_link.get_all_text().strip()

            if not href or not title or href in seen_links:
                continue
            if any(ign in href.lower() for ign in ["#", "javascript:", "/page/", "/category/"]):
                continue

            seen_links.add(href)
            slug = href.strip("/").split("/")[-1]
            if not slug or len(slug) < 2:
                continue

            img = el.css("img") if el.tag != "a" else []
            poster = img[0].attrib.get("src", "") if img else ""

            items.append(self.normalize_item(
                item_id=f"beetv-{slug}",
                title=title,
                poster=poster,
                source_url=href
            ))

        return items

    async def browse_genre(self, genre: str, page: int = 1) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/category/{genre.lower()}/"
        if page > 1:
            url = f"{url}page/{page}/"
        doc = await self.fetch_html(url)
        results = self._extract_items(doc)
        if not results and page == 1:
            return await self.search(genre, 1)
        return results

    async def search(self, query: str, page: int = 1) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/?s={quote_plus(query)}"
        if page > 1:
            url = f"{self.base_url}/page/{page}/?s={quote_plus(query)}"
        doc = await self.fetch_html(url)
        return self._extract_items(doc)

    async def resolve(self, url: str) -> Optional[str]:
        doc = await self.fetch_html(url)
        if not doc:
            return url
        for ifr in doc.css("iframe"):
            src = ifr.attrib.get("src", "")
            if src and any(k in src for k in ["embed", "vidsrc", "player"]):
                return src
        return url
