"""
YTS official scraper adapter (www13.yts-official.to).
SSR HTML scraping replacing the defunct public JSON API.
"""
from __future__ import annotations

import re
import logging
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus
from .base import BaseSiteAdapter

logger = logging.getLogger("streamapp.scraper.yts")

class YtsAdapter(BaseSiteAdapter):
    name = "YTS"
    is_spa = False
    base_url = "https://en.yts-official.biz"
    per_page = 20
    max_pages_per_genre = 50

    def _extract_items(self, doc: Any) -> List[Dict[str, Any]]:
        items = []
        if not doc:
            return items

        seen_urls = set()
        wraps = doc.css(".browse-movie-wrap")
        if wraps:
            for wrap in wraps:
                title_a = wrap.css("a.browse-movie-title")
                link_a = wrap.css("a.browse-movie-link")
                img = wrap.css("img")
                year_div = wrap.css(".browse-movie-year")
                rating_div = wrap.css("h4.rating")

                href = ""
                if link_a:
                    href = link_a[0].attrib.get("href", "")
                elif title_a:
                    href = title_a[0].attrib.get("href", "")

                if not href or href in seen_urls:
                    continue
                seen_urls.add(href)

                slug = href.strip("/").split("/")[-1]
                title_text = title_a[0].get_all_text().strip() if title_a else ""
                if not title_text and img:
                    title_text = img[0].attrib.get("alt", "") or img[0].attrib.get("title", "")
                if not title_text:
                    title_text = re.sub(r"-((?:19|20)\d{2})$", "", slug).replace("-", " ").title()

                poster = img[0].attrib.get("src", "") if img else ""
                year_str = year_div[0].get_all_text().strip() if year_div else ""
                year_m = re.search(r"((?:19|20)\d{2})", year_str or slug)
                year = int(year_m.group(1)) if year_m else 0

                rating_str = rating_div[0].get_all_text().strip() if rating_div else ""
                rating = rating_str.split("/")[0].strip() if "/" in rating_str else rating_str

                items.append(self.normalize_item(
                    item_id=f"yts-{slug}",
                    title=title_text,
                    year=year,
                    rating=rating or "NR",
                    poster=poster,
                    source_url=f"{self.base_url}{href}" if href.startswith("/") else href
                ))
            return items

        # Fallback if no .browse-movie-wrap
        anchors = doc.css("a.browse-movie-title, a[href*='/movies/']")
        for first_a in anchors:
            href = first_a.attrib.get("href", "")
            if not href or href in seen_urls:
                continue
            seen_urls.add(href)
            slug = href.strip("/").split("/")[-1]
            if not slug or slug in ["movies", "movie"]:
                continue

            title_text = first_a.get_all_text().strip()
            if not title_text:
                img = first_a.css("img")
                title_text = img[0].attrib.get("alt", "") or img[0].attrib.get("title", "") if img else ""
            if not title_text:
                title_text = slug.replace("-", " ").title()

            img = first_a.css("img")
            poster = img[0].attrib.get("src", "") if img else ""

            year_match = re.search(r"-((?:19|20)\d{2})$", slug)
            year = int(year_match.group(1)) if year_match else 0

            imdb_id = ""
            tmdb_id = ""
            imdb_m = re.search(r"(tt\d{6,})", href)
            if imdb_m:
                imdb_id = imdb_m.group(1)

            items.append(self.normalize_item(
                item_id=f"yts-{slug}",
                title=title_text,
                year=year,
                imdb_id=imdb_id,
                tmdb_id=tmdb_id,
                poster=poster,
                source_url=href
            ))

        return items

    async def browse_genre(self, genre: str, page: int = 1) -> List[Dict[str, Any]]:
        g = "all" if genre.lower() in ["all", "popular"] else genre.lower()
        url = f"{self.base_url}/browse-movies?genre={g}&page={page}"
        doc = await self.fetch_html(url)
        results = self._extract_items(doc)
        if not results and page == 1:
            # Fall back to homepage
            home = await self.fetch_html(self.base_url)
            results = self._extract_items(home)
        return results

    async def search(self, query: str, page: int = 1) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/browse-movies?keyword={quote_plus(query)}&page={page}"
        doc = await self.fetch_html(url)
        return self._extract_items(doc)

    async def resolve(self, url: str) -> Optional[str]:
        doc = await self.fetch_html(url)
        if not doc:
            return None
        # Look for magnet link or embed
        for a in doc.css("a[href^='magnet:']"):
            return a.attrib.get("href")
        for ifr in doc.css("iframe"):
            return ifr.attrib.get("src")
        return None
