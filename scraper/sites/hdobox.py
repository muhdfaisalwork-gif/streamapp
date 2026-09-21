"""
HDO Box scraper adapter (hdoboxapkpro.com).
SSR WordPress layout with movie catalog articles and search endpoints.
"""
from __future__ import annotations

import re
import logging
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus
from .base import BaseSiteAdapter

logger = logging.getLogger("streamapp.scraper.hdobox")

class HdoBoxAdapter(BaseSiteAdapter):
    name = "HDOBox"
    is_spa = False
    base_url = "https://hdoboxapkpro.com"
    per_page = 15
    max_pages_per_genre = 30

    def _extract_items(self, doc: Any) -> List[Dict[str, Any]]:
        items = []
        if not doc:
            return items

        posts = doc.css("article, .post, .entry, div.post-content")
        if not posts:
            posts = doc.css("h2 a, h3 a")

        seen_links = set()
        for el in posts:
            link_el = el if el.tag == "a" else el.css("a")
            if not link_el:
                continue
            first_link = link_el[0] if isinstance(link_el, list) else link_el
            href = first_link.attrib.get("href", "")
            title = first_link.get_all_text().strip()

            if not href or not title or href in seen_links:
                continue
            if any(ign in href.lower() for ign in ["category", "tag", "about-us", "contact", "privacy", "terms"]):
                continue

            seen_links.add(href)
            slug = href.strip("/").split("/")[-1]
            if not slug:
                continue

            # Extract image if present
            img = el.css("img") if el.tag != "a" else []
            poster = img[0].attrib.get("src", "") if img else ""

            items.append(self.normalize_item(
                item_id=f"hdo-{slug}",
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
        return url
