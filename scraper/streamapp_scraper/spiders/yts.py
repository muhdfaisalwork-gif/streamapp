"""YTS torrent-index spider.

Scrapes YTS (yts-official.to) for movies with torrent magnets and TMDB IDs.
"""

import scrapy
from streamapp_scraper.items import MediaItem


class YtsSpider(scrapy.Spider):
    name = "yts"

    custom_settings = {
        "PLAYWRIGHT_LAUNCH_OPTIONS": {"headless": True},
        "DOWNLOAD_DELAY": 2.0,
    }

    def __init__(self, start_page=1, max_pages=10, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_page = int(start_page)
        self.max_pages = int(max_pages)

    def start_requests(self):
        # YTS browse page (returns a JSON-like HTML list)
        for p in range(self.start_page, self.start_page + self.max_pages):
            url = f"https://www13.yts-official.to/browse-movies?page={p}"
            yield scrapy.Request(
                url,
                meta={"playwright": True},
                callback=self.parse_listing,
            )

    async def parse_listing(self, response):
        # YTS browse page lists movie cards with /movie/{slug} links
        for href in response.css("a.browse-movie-link::attr(href), a[href*='/movie/']::attr(href)").getall():
            yield response.follow(
                href,
                meta={"playwright": True},
                callback=self.parse_movie,
            )

    async def parse_movie(self, response):
        title = response.css("h1::text, [data-qa='movie-title']::text").get("").strip()
        if not title:
            return

        year_text = response.css(".movie-year, [itemprop='datePublished']::attr(content)").get("")
        try:
            year = int(str(year_text)[:4]) if year_text else None
        except ValueError:
            year = None

        imdb_id = response.css("a[href*='imdb.com/title/']::attr(href)").re_first(r"title/(tt\d+)")
        tmdb_id = response.css("a[href*='themoviedb.org/movie/']::attr(href)").re_first(r"/movie/(\d+)")

        genres = [g.strip() for g in response.css(".genre-list a::text, [data-qa='movie-genres'] a::text").getall() if g.strip()]

        rating_text = response.css("[itemprop='ratingValue']::attr(content), .rating-imdb::text").get("")
        try:
            rating = float(rating_text) if rating_text else None
        except ValueError:
            rating = None

        overview = response.css(".synopsis p::text, [data-qa='movie-synopsis'] p::text").get("").strip()

        runtime_text = response.css("[itemprop='duration']::attr(datetime), .runtime::text").get("")
        runtime = None
        if runtime_text:
            import re
            m = re.search(r"(\d+)", runtime_text)
            if m:
                runtime = int(m.group(1))

        # Poster / backdrop
        poster_path = response.css(".movie-poster img::attr(src), img.poster-img::attr(src)").get("")
        if "/upload/poster" in poster_path:
            # YTS posters use /upload/poster/{hash}.jpg - already a usable URL
            pass
        backdrop_path = response.css(".movie-backdrop img::attr(src), img.bg-img::attr(src)").get("") or poster_path

        # Torrent magnet (the actual stream source)
        torrent_magnet = response.css("a[href^='magnet:']::attr(href)").get("")

        # Quality info from torrent links
        quality = response.css(".torrent-info .quality::text").get("1080p")
        if quality:
            quality = quality.strip()

        yield MediaItem(
            id=None,  # populated by NormalizePipeline
            title=title,
            year=year,
            type="movie",
            imdb_id=imdb_id,
            tmdb_id=tmdb_id,
            genres=genres,
            rating=rating,
            runtime=runtime,
            overview=overview,
            poster_path=poster_path,
            backdrop_path=backdrop_path,
            torrent_magnet=torrent_magnet,
            quality=quality,
        )
