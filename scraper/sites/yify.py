"""
YifyPro scraper adapter (yify.pro).
Server-rendered HTML with movie browsing, TMDb ID extraction and search.
"""
from __future__ import annotations

import re
import logging
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus
from .base import BaseSiteAdapter

logger = logging.getLogger("streamapp.scraper.yify")

class YifyAdapter(BaseSiteAdapter):
    name = "YifyPro"
    is_spa = False
    base_url = "https://yify.pro"
    per_page = 36
    max_pages_per_genre = 300

    def _extract_items(self, doc: Any) -> List[Dict[str, Any]]:
        items = []
        if not doc:
            return items

        films: Dict[str, Dict[str, Any]] = {}
        for a in doc.css("a[href*='/film/']"):
            href = a.attrib.get("href", "")
            m = re.search(r"/film/(\d+)/([^/]+)", href)
            if not m:
                continue
            tmdb_id, slug = m.group(1), m.group(2)
            if tmdb_id not in films:
                films[tmdb_id] = {
                    "tmdb_id": tmdb_id,
                    "slug": slug,
                    "href": href,
                    "title": "",
                    "rating": "NR",
                    "poster": "",
                    "genres": []
                }

            txt = a.get_all_text().strip()
            img = a.css("img")
            if img:
                poster = img[0].attrib.get("data-src") or img[0].attrib.get("data-lazy-src") or img[0].attrib.get("src", "")
                if not poster.startswith("data:"):
                    films[tmdb_id]["poster"] = poster

            if "★" in txt:
                rm = re.search(r"★\s*([0-9.]+)", txt)
                if rm:
                    films[tmdb_id]["rating"] = rm.group(1)
                # extract possible genre text
                g_text = re.sub(r"(HD|★|[0-9.]+\s*/\s*10|View Details)", "", txt).strip()
                if g_text:
                    films[tmdb_id]["genres"] = [g.strip() for g in g_text.split() if g.strip()]
            elif txt and not "View Details" in txt:
                films[tmdb_id]["title"] = txt

        for tmdb_id, f in films.items():
            title = f["title"] or f["slug"].replace("-", " ").title()
            items.append(self.normalize_item(
                item_id=f"yify-{tmdb_id}",
                title=title,
                tmdb_id=tmdb_id,
                genres=f["genres"],
                rating=f["rating"],
                poster=f["poster"],
                source_url=f["href"]
            ))

        return items

    async def browse_genre(self, genre: str, page: int = 1) -> List[Dict[str, Any]]:
        # yify.pro uses /browse-movies/{page}/ or /genre/{genre}/{page}/
        url = f"{self.base_url}/browse-movies/{page}/" if page > 1 else f"{self.base_url}/browse-movies/"
        doc = await self.fetch_html(url)
        results = self._extract_items(doc)
        if not results:
            url = f"{self.base_url}/genre/{genre.lower()}/{page}/" if page > 1 else f"{self.base_url}/genre/{genre.lower()}/"
            doc = await self.fetch_html(url)
            results = self._extract_items(doc)
        return results

    async def search(self, query: str, page: int = 1) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/page/{page}/?s={quote_plus(query)}" if page > 1 else f"{self.base_url}/?s={quote_plus(query)}"
        doc = await self.fetch_html(url)
        return self._extract_items(doc)

    async def resolve(self, url: str) -> Optional[str]:
        doc = await self.fetch_html(url)
        if not doc:
            return None
        for ifr in doc.css("iframe"):
            src = ifr.attrib.get("src", "")
            if src:
                return src
        return None
