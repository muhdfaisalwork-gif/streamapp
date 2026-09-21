"""
MovieBoxHD scraper adapter (movieboxhd.net).
Server-rendered HTML / Nuxt 3 dataset with category pagination.
"""
from __future__ import annotations

import re
import json
import logging
from typing import Any, Dict, List, Optional
from .base import BaseSiteAdapter

logger = logging.getLogger("streamapp.scraper.movieboxhd")

class MovieBoxHdAdapter(BaseSiteAdapter):
    name = "MovieBoxHD"
    is_spa = False
    base_url = "https://movieboxhd.net"
    per_page = 24
    max_pages_per_genre = 50

    CATEGORIES = [
        {"slug": "popular", "path": "/", "name": "Popular"},
        {"slug": "action", "path": "/ranking-list/eJvhCT8w3t1?id=1232643093049001320&page_from=more_SUBJECTS_MOVIE", "name": "Action"},
        {"slug": "k-drama", "path": "/ranking-list/KNhvsW7OBd5?id=4380734070238626200&page_from=more_SUBJECTS_MOVIE", "name": "K-Drama"},
        {"slug": "sa-drama", "path": "/ranking-list/e570UxK46N1?id=1503943377597910848&page_from=more_SUBJECTS_MOVIE", "name": "Bollywood & Pakistani"},
        {"slug": "anime", "path": "/ranking-list/0UA0warzA4?id=62133389738001440&page_from=more_SUBJECTS_MOVIE", "name": "Anime"},
        {"slug": "c-drama", "path": "/ranking-list/KPAZTvQMPc?id=173752404280836544&page_from=more_SUBJECTS_MOVIE", "name": "C-Drama"},
        {"slug": "black-drama", "path": "/ranking-list/8Y0h9BbEi8a?id=8505361996374835640&page_from=more_SUBJECTS_MOVIE", "name": "Black Drama"},
    ]
    genres = [c["slug"] for c in CATEGORIES]

    def _extract_items_from_html(self, html_doc: Any) -> List[Dict[str, Any]]:
        items = []
        if not html_doc:
            return items

        # Method 1: Check DOM cards (<a class="movie-card" ...>)
        cards = html_doc.css(".movie-card, a[href*='/moviedetail/']")
        seen_slugs = set()

        # Pre-scan Nuxt data for image URLs if present
        nuxt_images = {}
        nuxt_script = html_doc.css("#__NUXT_DATA__")
        if nuxt_script:
            try:
                data = json.loads(nuxt_script[0].text)
                if isinstance(data, list):
                    all_imgs = [x for x in data if isinstance(x, str) and (x.startswith("http") and (".jpg" in x or ".webp" in x or ".png" in x))]
                    all_slugs = [x for x in data if isinstance(x, str) and re.match(r"^[a-z0-9-]+-[a-z0-9]{8,}$", x)]
                    for i, slg in enumerate(all_slugs):
                        if i < len(all_imgs):
                            nuxt_images[slg] = all_imgs[i]
            except Exception:
                pass

        for card in cards:
            href = card.attrib.get("href", "")
            if not href or href in seen_slugs:
                continue
            seen_slugs.add(href)

            # Title extraction - prioritize dedicated title classes
            title_el = card.css(".title-text, .subject-title, .film-title, h3")
            title_text = title_el[0].get_all_text().strip() if title_el else ""
            if not title_text:
                title_attr = card.attrib.get("title", "")
                m = re.search(r"go to (.+?) detail page", title_attr, re.I)
                title_text = m.group(1).strip() if m else title_attr
            if not title_text:
                p_el = card.css("p")
                title_text = p_el[0].get_all_text().strip() if p_el else ""

            # Slug
            slug_match = re.search(r"/moviedetail/([^/?#]+)", href)
            slug = slug_match.group(1) if slug_match else re.sub(r"[^a-zA-Z0-9_-]", "-", title_text.lower() if title_text else "untitled")

            if not title_text:
                # Deduce from slug
                title_text = re.sub(r"-[a-z0-9]{8,}$", "", slug).replace("-", " ").title()

            # Year, Rating, Genres, Overview
            year_el = card.css(".detail-year")
            year = 0
            if year_el:
                ym = re.search(r"((?:19|20)\d{2})", year_el[0].get_all_text())
                if ym:
                    year = int(ym.group(1))

            genre_el = card.css(".detail-genre")
            genres = [g.strip() for g in genre_el[0].get_all_text().split(",") if g.strip()] if genre_el else []

            rate_el = card.css(".rate-value")
            rating = rate_el[0].get_all_text().strip() if rate_el else "NR"

            desc_el = card.css(".desc-text")
            overview = desc_el[0].get_all_text().strip() if desc_el else ""

            # Poster
            poster = nuxt_images.get(slug, "")
            if not poster:
                img = card.css("img:not(.detail-icon):not(.rate-icon):not(.play-icon)")
                poster = img[0].attrib.get("src", "") if img else ""

            item_id = f"mb-{slug}"
            media_type = "tv" if "series" in href.lower() or "tv" in href.lower() or "season" in href.lower() else "movie"

            items.append(self.normalize_item(
                item_id=item_id,
                title=title_text,
                year=year,
                media_type=media_type,
                genres=genres,
                rating=rating,
                overview=overview,
                poster=poster,
                source_url=f"{self.base_url}{href}" if href.startswith("/") else href
            ))

        # Method 2: If DOM had few cards, check __NUXT_DATA__ payload
        if len(items) < 10:
            nuxt_script = html_doc.css("#__NUXT_DATA__")
            if nuxt_script:
                try:
                    data = json.loads(nuxt_script[0].text)
                    if isinstance(data, list):
                        for el in data:
                            if isinstance(el, dict) and "title" in el:
                                t_val = el.get("title")
                                if isinstance(t_val, int) and t_val < len(data) and isinstance(data[t_val], str):
                                    raw_name = data[t_val]
                                    if len(raw_name) > 1 and not raw_name.startswith("http") and not raw_name in seen_slugs:
                                        seen_slugs.add(raw_name)
                                        items.append(self.normalize_item(
                                            item_id=f"mb-{re.sub(r'[^a-zA-Z0-9_-]', '-', raw_name.lower())}",
                                            title=raw_name,
                                            source_url=self.base_url
                                        ))
                except Exception as e:
                    logger.debug(f"[MovieBoxHD] Nuxt parse fallback exception: {e}")

        return items

    async def browse_genre(self, genre: str, page: int = 1) -> List[Dict[str, Any]]:
        lc = genre.lower()
        matched_cat = next((c for c in self.CATEGORIES if lc in c["slug"] or lc in c["name"].lower()), None)
        path = matched_cat["path"] if matched_cat else "/"
        url = f"{self.base_url}{path}"
        if page > 1:
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}page={page}"

        doc = await self.fetch_html(url)
        items = self._extract_items_from_html(doc)
        if matched_cat:
            cat_slug = matched_cat.get("slug", "")
            country_map = {
                "k-drama": "KR",
                "c-drama": "CN",
                "sa-drama": "IN",
                "anime": "JP",
                "black-drama": "NG"
            }
            c_code = country_map.get(cat_slug, "")
            if c_code:
                for it in items:
                    it["country"] = c_code
        return items

    async def search(self, query: str, page: int = 1) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/search?keyword={query}&page={page}"
        doc = await self.fetch_html(url)
        results = self._extract_items_from_html(doc)
        if not results and page == 1:
            # Fall back to homepage filter
            home_doc = await self.fetch_html(self.base_url)
            all_home = self._extract_items_from_html(home_doc)
            q_lc = query.lower()
            return [it for it in all_home if q_lc in it["title"].lower()]
        return results

    async def resolve(self, url: str) -> Optional[str]:
        doc = await self.fetch_html(url)
        if not doc:
            return None
        # Look for iframe or video source
        iframes = doc.css("iframe")
        for f in iframes:
            src = f.attrib.get("src", "")
            if src and ("embed" in src or "player" in src or "vidsrc" in src):
                return src
        return None
