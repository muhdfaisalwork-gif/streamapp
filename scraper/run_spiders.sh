#!/usr/bin/env bash
# Run all Scrapy spiders sequentially. Output: ./output/scraped_catalog.json
set -e

cd "$(dirname "$0")"

# Activate venv if it exists
[ -d .venv ] && source .venv/bin/activate

# Run spiders. Each exits non-zero on error → bash -e aborts.
scrapy crawl yts
scrapy crawl donkey
scrapy crawl tmovies
scrapy crawl uflix

echo "Done. Output: $(pwd)/output/scraped_catalog.json"
