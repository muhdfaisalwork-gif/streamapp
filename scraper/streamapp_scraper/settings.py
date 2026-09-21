"""Scrapy settings for the StreamApp catalog service."""

BOT_NAME = "streamapp_scraper"

SPIDER_MODULES = ["streamapp_scraper.spiders"]
NEWSPIDER_MODULE = "streamapp_scraper.spiders"

# Crawl politely
ROBOTSTXT_OBEY = True
CONCURRENT_REQUESTS = 4
DOWNLOAD_DELAY = 1.5
COOKIES_ENABLED = False
TELNETCONSOLE_ENABLED = False
LOG_LEVEL = "INFO"

# Playwright for JS-heavy aggregator sites
DOWNLOAD_HANDLERS = {
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
PLAYWRIGHT_BROWSER_TYPE = "chromium"
PLAYWRIGHT_LAUNCH_OPTIONS = {"headless": True}

# Output: written by pipelines.JsonWriterPipeline to ./output/scraped_catalog.json
FEEDS = {}
ITEM_PIPELINES = {
    "streamapp_scraper.pipelines.NormalizePipeline": 100,
    "streamapp_scraper.pipelines.DedupePipeline": 200,
    "streamapp_scraper.pipelines.JsonWriterPipeline": 900,
}

# Default request headers
DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}
