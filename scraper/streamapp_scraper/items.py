"""Item definitions for the StreamApp catalog service."""

import scrapy


class MediaItem(scrapy.Item):
    """A movie or TV show scraped from an aggregator site."""
    id = scrapy.Field()                # stable slug, e.g. "the-matrix-1999"
    title = scrapy.Field()
    year = scrapy.Field()
    type = scrapy.Field()              # 'movie' or 'tv'
    imdb_id = scrapy.Field()           # 'tt0133093'
    tmdb_id = scrapy.Field()           # '603'
    genres = scrapy.Field()            # ['Action', 'Sci-Fi']
    rating = scrapy.Field()            # 8.2 (float)
    runtime = scrapy.Field()           # minutes
    overview = scrapy.Field()
    poster_path = scrapy.Field()       # '/abc.jpg'
    backdrop_path = scrapy.Field()
    embed_url = scrapy.Field()         # resolved iframe URL if available
    torrent_magnet = scrapy.Field()    # for YTS
    quality = scrapy.Field()           # '1080p' / '720p'
    source_site = scrapy.Field()       # 'YTS' / 'Donkey' / etc.
    scraped_at = scrapy.Field()        # ISO timestamp
