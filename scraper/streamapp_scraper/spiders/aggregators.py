"""Generic aggregator spider for HTTP-only movie sites (tmovies, donkey, uflix, etc.)."""

import scrapy
from streamapp_scraper.items import MediaItem


class GenericAggregatorSpider(scrapy.Spider):
    """Base class for aggregator spiders. Subclass and set `name` + `start_urls`."""
    name = "generic"
    allowed_domains = []
    custom_settings = {
        "PLAYWRIGHT_LAUNCH_OPTIONS": {"headless": True},
        "DOWNLOAD_DELAY": 2.0,
    }

    def parse(self, response):
        # Site-agnostic: look for h2/h3/a tags containing movie titles
        for card in response.css("article, .movie, .film, .item, .post"):
            title = card.css("h2::text, h3::text, .title::text, a::text").get("")
            title = (title or "").strip()
            if not title or len(title) < 2:
                continue
            href = card.css("a::attr(href)").get("")
            year_text = card.css(".year::text, .date::text").get("")
            try:
                year = int(str(year_text)[:4]) if year_text else None
            except ValueError:
                year = None

            if href:
                yield response.follow(
                    href,
                    meta={"playwright": True},
                    callback=self.parse_detail,
                    cb_kwargs={"fallback_title": title, "fallback_year": year},
                )

    def parse_detail(self, response, fallback_title, fallback_year):
        title = response.css("h1::text, h2::text").get("") or fallback_title
        title = title.strip()

        # Look for an embed iframe - this is the playable URL
        embed_url = response.css("iframe::attr(src), iframe[src*='embed']::attr(src)").get("")

        # Genres from breadcrumbs or list
        genres = [g.strip() for g in response.css(".genre a::text, [data-qa='genre']::text").getall() if g.strip()]

        # IMDB id from links
        imdb_id = response.css("a[href*='imdb.com/title/']::attr(href)").re_first(r"title/(tt\d+)")

        yield MediaItem(
            id=None,
            title=title,
            year=fallback_year,
            type="movie",
            imdb_id=imdb_id,
            genres=genres,
            embed_url=embed_url,
        )


class DonkeySpider(GenericAggregatorSpider):
    name = "donkey"
    allowed_domains = ["donkey.to"]
    start_urls = ["https://donkey.to"]

    def start_requests(self):
        # Donkey doesn't have a search endpoint; index page lists recent
        yield scrapy.Request("https://donkey.to", meta={"playwright": True}, callback=self.parse)


class TmoviesSpider(GenericAggregatorSpider):
    name = "tmovies"
    allowed_domains = ["tmovies.watch"]
    start_urls = ["https://tmovies.watch"]


class UflixSpider(GenericAggregatorSpider):
    name = "uflix"
    allowed_domains = ["uflix.cc"]
    start_urls = ["https://uflix.cc/movies"]
