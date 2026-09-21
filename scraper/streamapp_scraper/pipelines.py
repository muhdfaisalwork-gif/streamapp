"""Item pipelines: normalize, dedupe, and write to JSON."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path


OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"
OUTPUT_FILE = OUTPUT_DIR / "scraped_catalog.json"


class NormalizePipeline:
    """Coerce raw scraped fields into the canonical MediaItem shape."""

    def process_item(self, item, spider):
        # Normalize id
        if not item.get("id"):
            title = (item.get("title") or "").lower().strip()
            year = item.get("year") or ""
            item["id"] = "-".join(p for p in [title.replace(" ", "-"), str(year)] if p).strip("-")

        # Normalize year
        if not item.get("year"):
            release = item.get("release_date") or ""
            if release:
                item["year"] = int(release[:4]) if release[:4].isdigit() else None

        # Normalize rating
        rating = item.get("rating")
        if isinstance(rating, str):
            try:
                item["rating"] = float(rating)
            except ValueError:
                pass

        # Normalize genres to array of strings
        genres = item.get("genres")
        if isinstance(genres, str):
            item["genres"] = [g.strip() for g in genres.split(",") if g.strip()]
        elif genres is None:
            item["genres"] = []

        # Timestamp
        item["scraped_at"] = datetime.now(timezone.utc).isoformat()

        # Source attribution
        item["source_site"] = spider.name

        return item


class DedupePipeline:
    """Drop duplicates based on imdb_id, then title+year."""

    def __init__(self):
        self.seen_ids = set()
        self.seen_keys = set()

    def process_item(self, item, spider):
        imdb = item.get("imdb_id")
        if imdb:
            if imdb in self.seen_ids:
                spider.logger.debug(f"Drop duplicate imdb_id={imdb}")
                raise DropItem(f"Duplicate imdb_id: {imdb}")
            self.seen_ids.add(imdb)

        key = (item.get("title", "").lower().strip(), str(item.get("year") or ""))
        if key in self.seen_keys:
            spider.logger.debug(f"Drop duplicate title+year={key}")
            raise DropItem(f"Duplicate title+year: {key}")
        self.seen_keys.add(key)

        return item


class JsonWriterPipeline:
    """Write all scraped items to output/scraped_catalog.json."""

    def open_spider(self, spider):
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        self.items = []

    def process_item(self, item, spider):
        # Convert Item to plain dict
        d = {k: v for k, v in item.items() if v is not None}
        self.items.append(d)
        return item

    def close_spider(self, spider):
        # Merge with existing catalog if any (Spider chaining would be cleaner)
        existing = []
        if OUTPUT_FILE.exists():
            try:
                with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    existing = data if isinstance(data, list) else data.get("items", [])
            except Exception:
                pass

        # Dedup by id
        existing_by_id = {x.get("id"): x for x in existing if x.get("id")}
        for it in self.items:
            if it.get("id"):
                existing_by_id[it["id"]] = it
        merged = list(existing_by_id.values())

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump({"scraped_at": datetime.now(timezone.utc).isoformat(),
                       "count": len(merged),
                       "items": merged}, f, ensure_ascii=False, indent=2)
        spider.logger.info(f"Wrote {len(merged)} items to {OUTPUT_FILE}")


from scrapy.exceptions import DropItem
