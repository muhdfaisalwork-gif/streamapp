# StreamApp Scrapy Service

Python Scrapy micro-service for the StreamApp backend. Spiders scrape torrent-index sites (YTS) and HTTP aggregator sites (tmovies, donkey, uflix), then write the merged catalog to `output/scraped_catalog.json`, which the Node backend reads via `ScrapyFeedScraper`.

## Setup

### Windows
```powershell
cd G:\streaming app\scraper
.\install_python.ps1
```

### macOS / Linux
```bash
cd /path/to/streaming\ app/scraper
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

## Run

```bash
# All spiders sequentially
./run_spiders.sh
# or on Windows
.\run_spiders.ps1

# Individual spider
scrapy crawl yts
scrapy crawl donkey
```

Output goes to `output/scraped_catalog.json`. The Node backend reads this on startup. If missing or >24h old, `ScrapyFeedScraper` returns empty results without error — the rest of the catalog stays usable.

## Spider inventory

| Spider | Target | Notes |
|--------|--------|-------|
| `yts` | https://www13.yts-official.to | Torrent magnet + TMDB id per title |
| `donkey` | https://donkey.to | Embed iframes |
| `tmovies` | https://tmovies.watch | Embed iframes |
| `uflix` | https://uflix.cc | Embed iframes |

## Output schema

```json
{
  "scraped_at": "2026-09-19T22:00:00Z",
  "count": 1234,
  "items": [
    {
      "id": "the-matrix-1999",
      "title": "The Matrix",
      "year": 1999,
      "type": "movie",
      "imdb_id": "tt0133093",
      "tmdb_id": "603",
      "genres": ["Action", "Sci-Fi"],
      "rating": 8.2,
      "runtime": 136,
      "overview": "...",
      "poster_path": "https://yts.mx/assets/images/movies/the_matrix_1999/medium-cover.jpg",
      "embed_url": "https://...",
      "torrent_magnet": "magnet:?xt=...",
      "quality": "1080p",
      "source_site": "yts",
      "scraped_at": "..."
    }
  ]
}
```

## Caveats

- **YTS** is torrent-only (returns magnets). The Node backend will fall back to a VidSrc embed when no embed_url is present.
- **Aggregator sites** are volatile. The PDF research section notes OnStream is permanently gone. Spider failures are logged but don't crash the run.
- **Polite crawling**: `DOWNLOAD_DELAY=2.0` + `ROBOTSTXT_OBEY=True`. Don't lower these without thinking.
