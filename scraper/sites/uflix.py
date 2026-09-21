"""
uFlix scraper adapter (uflix.cc).
Direct port and enhancement of UflixHtmlScraper with detail page IMDb extraction.
"""
from __future__ import annotations

import re
import logging
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus
from .base import BaseSiteAdapter

logger = logging.getLogger("streamapp.scraper.uflix")

class UflixAdapter(BaseSiteAdapter):
    name = "uflix"
    is_spa = False
    base_url = "https://uflix.cc"
    per_page = 18
    max_pages_per_genre = 100

    def __init__(self) -> None:
        super().__init__()
        self._detail_cache: Dict[str, Dict[str, Any]] = {}

    def _parse_slug_title_year(self, slug: str) -> tuple[str, int]:
        m = re.match(r"^(.+)-(\d{4})$", slug)
        if m:
            clean = " ".join(w.capitalize() for w in m.group(1).split("-"))
            return clean, int(m.group(2))
        clean = " ".join(w.capitalize() for w in slug.split("-"))
        return clean, 0

    def _extract_items_from_html(self, doc: Any) -> List[Dict[str, Any]]:
        items = []
        if not doc:
            return items

        cards = doc.css("a.card.card-movie, a[href*='/movie/']")
        seen_slugs = set()

        for card in cards:
            href = card.attrib.get("href", "")
            if not href or "/movie/" not in href:
                continue

            slug_match = re.search(r"/movie/([^/?#]+)", href)
            if not slug_match:
                continue
            slug = slug_match.group(1)
            if slug in seen_slugs:
                continue
            seen_slugs.add(slug)

            default_title, year = self._parse_slug_title_year(slug)

            # Title element
            title_el = card.css("h3.title, .title")
            title = title_el[0].get_all_text().strip() if title_el else default_title

            # Poster
            img = card.css("img")
            poster_src = img[0].attrib.get("src", "") if img else ""
            if poster_src and not poster_src.startswith("http"):
                poster_src = f"{self.base_url}{poster_src}"

            # Rating
            rating_el = card.css("span")
            rating = "NR"
            if rating_el:
                r_text = rating_el[0].get_all_text().strip()
                if re.match(r"^[0-9.]+$", r_text):
                    rating = r_text

            # Genre
            genre_el = card.css("li.list-inline-item")
            genres = [g.attrib.get("title", "").strip() or g.get_all_text().strip() for g in genre_el]
            genres = [g for g in genres if g]

            full_url = f"{self.base_url}/movie/{slug}"

            items.append(self.normalize_item(
                item_id=f"uflix-{slug}",
                title=title,
                year=year,
                genres=genres,
                rating=rating,
                poster=poster_src,
                source_url=full_url
            ))

        return items

    async def fetch_detail(self, slug: str) -> Dict[str, Any]:
        """Fetches title detail page to extract IMDb ID and description."""
        if slug in self._detail_cache:
            return self._detail_cache[slug]

        url = f"{self.base_url}/movie/{slug}"
        doc = await self.fetch_html(url)
        detail = {"imdb_id": "", "description": "", "genres": []}
        if doc:
            html_text = doc.text or str(doc.body)
            imdb_m = re.search(r"imdb\.com/title/(tt\d+)", html_text)
            if imdb_m:
                detail["imdb_id"] = imdb_m.group(1)

            desc_el = doc.css("div.description")
            if desc_el:
                detail["description"] = desc_el[0].get_all_text().strip()

        self._detail_cache[slug] = detail
        return detail

    async def browse_genre(self, genre: str, page: int = 1) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/movies?page={page}" if page > 1 else f"{self.base_url}/movies"
        doc = await self.fetch_html(url)
        all_items = self._extract_items_from_html(doc)
        g_lc = genre.lower()
        if genre.lower() != "all":
            matched = [it for it in all_items if any(g_lc in g.lower() for g in it.get("genres", []))]
            return matched if matched else all_items
        return all_items

    async def search(self, query: str, page: int = 1) -> List[Dict[str, Any]]:
        # Try search URL
        url = f"{self.base_url}/search/{quote_plus(query)}"
        doc = await self.fetch_html(url)
        results = self._extract_items_from_html(doc)
        if not results:
            # Fallback to listings filter
            page_url = f"{self.base_url}/movies" if page == 1 else f"{self.base_url}/movies/page/{page}/"
            doc = await self.fetch_html(page_url)
            items = self._extract_items_from_html(doc)
            q_lc = query.lower()
            return [it for it in items if q_lc in it["title"].lower()]
        return results

    async def resolve(self, url: str) -> Optional[str]:
        slug = url.strip("/").split("/")[-1].replace("uflix-", "")
        detail = await self.fetch_detail(slug)
        if detail.get("imdb_id"):
            return f"https://vidsrc.to/embed/movie/{detail['imdb_id']}"
        return f"{self.base_url}/movie/{slug}"
