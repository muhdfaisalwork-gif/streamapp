"""
FastAPI Micro-Service for StreamApp Live Scrapers and Unified Catalog.
Runs on port 7800.
"""
from __future__ import annotations

import os
import sys
import asyncio
import logging
import re
import urllib.parse
from pathlib import Path
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, BackgroundTasks, Query, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add current dir to path
CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from sites import get_all_adapters, get_adapter, list_adapters
from tmdb_lane import tmdb_lane
from deep_crawl import Database, deep_warm_all, seed_curated_catalog, DEFAULT_DB_PATH

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("streamapp.live_service")

db = Database(DEFAULT_DB_PATH)
warmup_running = False

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: connect DB and seed base catalog
    await db.connect()
    await seed_curated_catalog(db)
    logger.info("FastAPI Live Service started on http://127.0.0.1:7800")
    yield
    # Shutdown
    await db.close()
    logger.info("FastAPI Live Service shutdown complete.")

app = FastAPI(
    title="StreamApp Live Scraper Service",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Models
class ResolveRequest(BaseModel):
    site: Optional[str] = ""
    url: str
    season: Optional[int] = None
    episode: Optional[int] = None

class ScrapeRequest(BaseModel):
    query: str
    limit: Optional[int] = 30

@app.get("/health")
async def health_check():
    stats = await db.get_stats()
    return {
        "ok": True,
        "status": "healthy",
        "service": "StreamApp Live Scraper",
        "port": 7800,
        "liveAvailable": True,
        "liveTitlesCached": stats.get("total", 0),
        "totalUniqueTitles": stats.get("total", 0),
        "tmdbEnabled": tmdb_lane.enabled,
        "warmupRunning": warmup_running
    }

@app.get("/stats")
async def get_stats():
    return await db.get_stats()

@app.post("/warm")
async def start_warmup(background_tasks: BackgroundTasks, target: int = Query(100000)):
    global warmup_running
    if warmup_running:
        return {"status": "in_progress", "message": "Warmup already running in background"}

    async def run_warm():
        global warmup_running
        warmup_running = True
        try:
            await deep_warm_all(target=target, db_path=DEFAULT_DB_PATH)
        finally:
            warmup_running = False

    background_tasks.add_task(run_warm)
    return {"status": "started", "message": f"Deep warmup initiated for {target:,} target titles"}

@app.get("/search")
async def search_catalog(
    q: str = Query("", description="Search text"),
    genre: str = Query("", description="Genre filter"),
    country: str = Query("", description="Country code/bucket"),
    language: str = Query("", description="Language code/filter"),
    page: int = Query(1, ge=1),
    pageSize: int = Query(50, ge=1, le=5000)
):
    # 1. Query local cache DB
    results = await db.query_titles(
        query=q,
        genre=genre,
        country=country,
        language=language,
        page=page,
        page_size=pageSize
    )

    # 2. If no results found in local cache and we have a query, hit live adapters in background
    live_sources = []
    adapters = get_all_adapters()
    if q and len(results) == 0 and page == 1:
        tasks = []
        for ad in adapters:
            async def bounded_search(target_adapter=ad):
                try:
                    return await asyncio.wait_for(target_adapter.search(q, 1), timeout=2.5)
                except Exception:
                    return []
            tasks.append(bounded_search())

        if tmdb_lane.enabled:
            tasks.append(tmdb_lane.search(q, 1))

        settled = await asyncio.gather(*tasks, return_exceptions=True)
        new_items = []
        for idx, res in enumerate(settled):
            if isinstance(res, list) and res:
                src_name = adapters[idx].name if idx < len(adapters) else "TMDb"
                live_sources.append(src_name)
                new_items.extend(res)

        if new_items:
            await db.insert_titles_batch(new_items)
            # Re-query
            results = await db.query_titles(
                query=q,
                genre=genre,
                country=country,
                language=language,
                page=page,
                page_size=pageSize
            )

    stats = await db.get_stats()
    all_adapter_names = [ad.name for ad in adapters]
    return {
        "query": q,
        "genre": genre,
        "country": country,
        "language": language,
        "page": page,
        "pageSize": pageSize,
        "count": len(results),
        "total": stats.get("total", 0),
        "live": True,
        "sources": list(dict.fromkeys(live_sources + all_adapter_names[:7])),
        "results": results
    }

@app.get("/country-counts")
async def get_country_counts():
    return await db.get_country_counts()

@app.get("/title/{id}")
async def get_title_by_id(id: str):
    item = await db.get_title_by_id(id)
    if not item:
        raise HTTPException(status_code=404, detail="Title not found")
    return item

@app.get("/tv/{id}/episodes")
async def get_tv_episodes(id: str, season: int = Query(1, ge=1)):
    title = await db.get_title_by_id(id)
    tmdb_id = (title.get("tmdbId") if title else "") or (id if id.isdigit() else "")
    imdb_id = (title.get("imdbId") if title else "") or (id if id.startswith("tt") else "")

    c_code = (title.get("country") if title else "").upper()
    num_episodes = 25 if c_code in ("PK", "TR", "EG") else 16 if c_code in ("KR", "CN") else 12

    raw_title = title.get("title", "") if title else id
    clean_title = re.sub(r"\s*-\s*S\d+E\d+.*$", "", raw_title, flags=re.I).strip()

    episodes = []
    for e in range(1, num_episodes + 1):
        sources = []
        if tmdb_id:
            sources.append({
                "label": "VidSrc.me",
                "provider": "vidsrc",
                "url": f"https://vidsrc.me/embed/tv?tmdb={tmdb_id}&season={season}&episode={e}",
                "quality": "1080p",
                "format": "embed"
            })
            sources.append({
                "label": "SuperEmbed",
                "provider": "superembed",
                "url": f"https://multiembed.mov/?video_id={tmdb_id}&tmdb=1&s={season}&e={e}",
                "quality": "1080p",
                "format": "embed"
            })
            sources.append({
                "label": "VidSrc.to",
                "provider": "vidsrc",
                "url": f"https://vidsrc.to/embed/tv/{tmdb_id}/{season}/{e}",
                "quality": "1080p",
                "format": "embed"
            })
            sources.append({
                "label": "2Embed",
                "provider": "2embed",
                "url": f"https://www.2embed.cc/embedtv/{tmdb_id}&s={season}&e={e}",
                "quality": "720p",
                "format": "embed"
            })
        elif imdb_id:
            sources.append({
                "label": "VidSrc.me (IMDb)",
                "provider": "vidsrc",
                "url": f"https://vidsrc.me/embed/tv?imdb={imdb_id}&season={season}&episode={e}",
                "quality": "1080p",
                "format": "embed"
            })
            sources.append({
                "label": "SuperEmbed",
                "provider": "superembed",
                "url": f"https://multiembed.mov/?video_id={imdb_id}&s={season}&e={e}",
                "quality": "1080p",
                "format": "embed"
            })
            sources.append({
                "label": "2Embed",
                "provider": "2embed",
                "url": f"https://www.2embed.cc/embedtv/{imdb_id}&s={season}&e={e}",
                "quality": "720p",
                "format": "embed"
            })

        if clean_title:
            yt_query = urllib.parse.quote_plus(f"{clean_title} Episode {e} full episode HD")
            sources.append({
                "label": "YouTube (Official HD)",
                "provider": "youtube",
                "url": f"https://www.youtube-nocookie.com/embed?listType=search&list={yt_query}",
                "quality": "1080p",
                "format": "embed"
            })

        episodes.append({
            "season": season,
            "episode": e,
            "title": f"Episode {e}",
            "sources": sources
        })

    return {
        "id": id,
        "season": season,
        "count": len(episodes),
        "episodes": episodes
    }

@app.get("/country/{code}")
async def get_by_country(
    code: str,
    page: int = Query(1, ge=1),
    pageSize: int = Query(50, ge=1, le=5000)
):
    c_lower = code.lower()

    # Thematic buckets routing
    thematic_map = {
        "animation": ("genre", "Animation"),
        "horror": ("genre", "Horror"),
        "thriller": ("genre", "Thriller"),
        "documentary": ("genre", "Documentary"),
        "music": ("genre", "Music"),
        "scifi": ("genre", "Sci-Fi"),
        "romance": ("genre", "Romance"),
        "family": ("genre", "Family"),
        "classic": ("classic", None),
        "superhero": ("superhero", None),
    }

    if c_lower in thematic_map:
        t_type, t_val = thematic_map[c_lower]
        if t_type == "genre":
            results = await db.query_titles(genre=t_val, page=page, page_size=pageSize)
        elif t_type == "classic":
            results = await db.query_titles(max_year=1990, page=page, page_size=pageSize)
        else:
            results = await db.query_titles(query="man", genre="Action", page=page, page_size=pageSize)
        return {
            "country": code,
            "page": page,
            "pageSize": pageSize,
            "count": len(results),
            "live": True,
            "results": results
        }

    if c_lower == "all":
        results = await db.query_titles(page=page, page_size=pageSize)
        return {
            "country": code,
            "page": page,
            "pageSize": pageSize,
            "count": len(results),
            "live": True,
            "results": results
        }

    # Map country presets
    c_map = {
        "bollywood": "IN", "india": "IN",
        "pakistan": "PK", "pakistani": "PK",
        "korean": "KR", "korea": "KR",
        "hollywood": "US", "usa": "US",
        "japanese": "JP", "japan": "JP",
        "british": "GB", "uk": "GB", "gb": "GB",
        "french": "FR", "france": "FR", "fr": "FR",
        "chinese": "CN", "china": "CN", "cn": "CN",
        "italian": "IT", "italy": "IT", "it": "IT",
        "spanish": "ES", "spain": "ES", "es": "ES",
        "german": "DE", "germany": "DE", "de": "DE",
        "turkish": "TR", "turkey": "TR",
        "nigeria": "NG", "nigerian": "NG", "nollywood": "NG",
        "egypt": "EG", "egyptian": "EG",
        "indonesia": "ID", "indonesian": "ID",
        "philippines": "PH", "filipino": "PH",
        "mexico": "MX", "mexican": "MX",
        "brazil": "BR", "brazilian": "BR",
        "iran": "IR", "iranian": "IR"
    }
    iso_code = c_map.get(c_lower, code.upper())

    results = await db.query_titles(
        country=iso_code,
        page=page,
        page_size=pageSize
    )

    # If TMDb lane is enabled and count is low, discover on the fly
    if tmdb_lane.enabled and len(results) < 20 and page == 1:
        m_items = await tmdb_lane.discover_movies(country=iso_code, page=1)
        t_items = await tmdb_lane.discover_tv(country=iso_code, page=1)
        combined = m_items + t_items
        if combined:
            await db.insert_titles_batch(combined)
            results = await db.query_titles(country=iso_code, page=page, page_size=pageSize)

    return {
        "country": code,
        "isoCode": iso_code,
        "page": page,
        "pageSize": pageSize,
        "count": len(results),
        "live": True,
        "results": results
    }

@app.get("/genre/{genre}")
async def get_by_genre(
    genre: str,
    page: int = Query(1, ge=1),
    pageSize: int = Query(50, ge=1, le=5000)
):
    results = await db.query_titles(
        genre=genre,
        page=page,
        page_size=pageSize
    )
    return {
        "genre": genre,
        "page": page,
        "pageSize": pageSize,
        "count": len(results),
        "live": True,
        "results": results
    }

@app.post("/resolve")
async def resolve_stream(req: ResolveRequest):
    url = req.url or ""
    site_name = req.site or ""

    import re
    tmdb_id = None
    imdb_id = None

    # Check if URL itself is numeric TMDb ID or has TMDb pattern
    if url.isdigit():
        tmdb_id = url
    else:
        tmdb_match = re.search(r"(?:tmdb[:/-]|movie/|tv/)(\d+)", url)
        if tmdb_match:
            tmdb_id = tmdb_match.group(1)

    # Check if URL is IMDb ID or has IMDb pattern
    if url.startswith("tt") and len(url) >= 7:
        imdb_id = url
    else:
        imdb_match = re.search(r"(tt\d{6,})", url)
        if imdb_match:
            imdb_id = imdb_match.group(1)

    # If not found yet, try looking up title in DB by slug/id
    if not tmdb_id and not imdb_id and url:
        item = await db.get_title_by_id(url)
        if item:
            tmdb_id = item.get("tmdbId")
            imdb_id = item.get("imdbId")

    if tmdb_id:
        if req.season and req.episode:
            return {"streamUrl": f"https://vidsrc.me/embed/tv?tmdb={tmdb_id}&season={req.season}&episode={req.episode}", "provider": "vidsrc"}
        return {"streamUrl": f"https://vidsrc.me/embed/movie?tmdb={tmdb_id}", "provider": "vidsrc"}

    if imdb_id:
        if req.season and req.episode:
            return {"streamUrl": f"https://vidsrc.me/embed/tv?imdb={imdb_id}&season={req.season}&episode={req.episode}", "provider": "vidsrc"}
        return {"streamUrl": f"https://vidsrc.me/embed/movie?imdb={imdb_id}", "provider": "vidsrc"}

    # 2. Try site adapter resolve
    adapter = get_adapter(site_name) if site_name else None
    if adapter and (url.startswith("http://") or url.startswith("https://")):
        stream_url = await adapter.resolve(url)
        if stream_url:
            return {"streamUrl": stream_url, "provider": adapter.name}

    # Only return URL if it's an actual http(s) URL
    if url.startswith("http://") or url.startswith("https://"):
        return {"streamUrl": url, "provider": "direct"}

    return {"streamUrl": None, "error": "Unable to resolve stream"}

@app.post("/scrape")
async def scrape_live(req: ScrapeRequest):
    query = req.query
    limit = req.limit or 30

    adapters = get_all_adapters()
    tasks = [ad.search(query, 1) for ad in adapters]
    if tmdb_lane.enabled:
        tasks.append(tmdb_lane.search(query, 1))

    settled = await asyncio.gather(*tasks, return_exceptions=True)
    combined = []
    seen = set()

    for res in settled:
        if isinstance(res, list):
            for item in res:
                if item["id"] not in seen:
                    seen.add(item["id"])
                    combined.append(item)

    # Persist in background
    if combined:
        asyncio.create_task(db.insert_titles_batch(combined))

    return {
        "query": query,
        "count": len(combined[:limit]),
        "live": True,
        "results": combined[:limit]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("live_service:app", host="127.0.0.1", port=7800, reload=False)
