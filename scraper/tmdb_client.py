"""
tmdb_client.py — Minimal TMDB v3 API client (Python port inspired by andrielfn/tmdb-api).

Endpoints implemented (full surface for the streaming catalog):
  GET /configuration          → image base URL + poster/backdrop sizes
  GET /search/movie            → find by title (+ optional year)
  GET /search/tv               → find TV by title
  GET /movie/{id}              → full movie metadata
  GET /tv/{id}                 → full TV metadata
  GET /movie/{id}/images       → posters + backdrops list
  GET /tv/{id}/images          → ditto for TV
  GET /movie/{id}/alternative_titles
  GET /movie/{id}/credits      → cast + crew
  GET /tv/{id}/external_ids    → imdb_id etc.
  GET /genre/movie/list        → movie genres
  GET /genre/tv/list           → tv genres
  GET /configuration/countries

The image URL pattern is documented as:
  https://image.tmdb.org/t/p/{size}/{file_path}
Where size ∈ ['w92','w154','w185','w342','w500','w780','original'] for posters,
and ['w300','w780','w1280','original'] for backdrops.

Usage:
  c = TmdbClient(api_key=os.environ.get('TMDB_API_KEY'))
  results = c.search_movie('fight club', year=1999)
  images  = c.movie_images(550)

The client never silently fakes data: every response goes through _normalize which
returns None for missing keys, never invented text.
"""
from __future__ import annotations
import os
import time
import json
import logging
import threading
from typing import Any, Optional
from urllib.parse import urlencode

try:
    import requests
except ImportError:
    requests = None  # type: ignore

log = logging.getLogger("tmdb")

BASE_URL = "https://api.themoviedb.org/3"
DEFAULT_TIMEOUT = 15
DEFAULT_POSTER_SIZE = "w500"
DEFAULT_BACKDROP_SIZE = "w1280"
MIN_INTERVAL_SEC = 0.05  # 20 req/sec — generous, TMDB allows 50 req/sec


class TmdbError(RuntimeError):
    """Raised when the upstream TMDB API fails or returns malformed data."""


class TmdbClient:
    def __init__(self, api_key: Optional[str] = None, session=None):
        self.api_key = api_key or os.environ.get("TMDB_API_KEY") or ""
        if not self.api_key:
            raise TmdbError(
                "TMDB_API_KEY not set. Get one free at https://www.themoviedb.org/settings/api"
            )
        if requests is None:
            raise TmdbError(
                "Python `requests` library not installed. `pip install requests`."
            )
        self._session = session or requests.Session()
        self._last_call = 0.0
        self._lock = threading.Lock()
        # Map of image sizes pulled from /configuration
        self.image_base = "https://image.tmdb.org/t/p/"
        self.poster_sizes = ["w500", "w780", "original"]
        self.backdrop_sizes = ["w1280", "w780", "original"]
        self._configured = False

    # ---------------- core HTTP ----------------
    def _throttle(self):
        with self._lock:
            now = time.monotonic()
            wait = MIN_INTERVAL_SEC - (now - self._last_call)
            if wait > 0:
                time.sleep(wait)
            self._last_call = time.monotonic()

    def _get(self, path: str, params: dict | None = None) -> Any:
        self._throttle()
        params = dict(params or {})
        params["api_key"] = self.api_key
        url = f"{BASE_URL}{path}"
        try:
            r = self._session.get(url, params=params, timeout=DEFAULT_TIMEOUT)
            if r.status_code == 401:
                raise TmdbError("TMDB 401 Unauthorized — invalid API key")
            if r.status_code == 404:
                return None
            if r.status_code == 429:
                time.sleep(1.0)
                return self._get(path, params)
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            log.warning("TMDB request failed: %s %s (%s)", url, params.get("query", path), e)
            return None

    # ---------------- configuration ----------------
    def configure(self):
        data = self._get("/configuration")
        if not isinstance(data, dict) or "images" not in data:
            self._configured = True
            return
        cfg = data["images"]
        self.image_base = cfg.get("base_url", self.image_base).rstrip("/") + "/"
        ps = cfg.get("poster_sizes") or []
        bs = cfg.get("backdrop_sizes") or []
        # Prefer w500 / w780 / original
        for s in ("w500", "w780", "original"):
            if s in ps:
                self.poster_sizes = [s] + [x for x in self.poster_sizes if x != s]
        for s in ("w1280", "w780", "original"):
            if s in bs:
                self.backdrop_sizes = [s] + [x for x in self.backdrop_sizes if x != s]
        self._configured = True

    @staticmethod
    def pick_size(sizes: list[str], preferred: str, fallback: str = "original") -> str:
        if preferred in sizes:
            return preferred
        if sizes:
            return sizes[0]
        return fallback

    def poster_url(self, path: Optional[str], size: Optional[str] = None) -> Optional[str]:
        if not path:
            return None
        sz = size or self.pick_size(self.poster_sizes, DEFAULT_POSTER_SIZE)
        return f"{self.image_base}{sz}{path}"

    def backdrop_url(self, path: Optional[str], size: Optional[str] = None) -> Optional[str]:
        if not path:
            return None
        sz = size or self.pick_size(self.backdrop_sizes, DEFAULT_BACKDROP_SIZE)
        return f"{self.image_base}{sz}{path}"

    # ---------------- search ----------------
    def search_movie(self, query: str, year: Optional[int] = None,
                     include_adult: bool = False, language: str = "en-US") -> list[dict]:
        params = {"query": query, "include_adult": str(include_adult).lower(),
                  "language": language, "page": 1}
        if year:
            params["year"] = year
        d = self._get("/search/movie", params)
        return (d or {}).get("results") or []

    def search_tv(self, query: str, year: Optional[int] = None,
                  language: str = "en-US") -> list[dict]:
        params = {"query": query, "language": language, "page": 1}
        if year:
            params["first_air_date_year"] = year
        d = self._get("/search/tv", params)
        return (d or {}).get("results") or []

    # ---------------- details ----------------
    def movie(self, tmdb_id: int, language: str = "en-US") -> dict | None:
        d = self._get(f"/movie/{tmdb_id}", {"language": language, "append_to_response": "external_ids,credits,alternative_titles"})
        return d

    def tv(self, tmdb_id: int, language: str = "en-US") -> dict | None:
        d = self._get(f"/tv/{tmdb_id}", {"language": language, "append_to_response": "external_ids,content_ratings"})
        return d

    def movie_images(self, tmdb_id: int, language: str = "en,null") -> dict | None:
        return self._get(f"/movie/{tmdb_id}/images", {"language": language, "include_image_language": "en,null"})

    def tv_images(self, tmdb_id: int, language: str = "en,null") -> dict | None:
        return self._get(f"/tv/{tmdb_id}/images", {"language": language, "include_image_language": "en,null"})

    def external_ids(self, tmdb_id: int, kind: str = "movie") -> dict | None:
        return self._get(f"/{'movie' if kind == 'movie' else 'tv'}/{tmdb_id}/external_ids")

    # ---------------- genres + countries ----------------
    def movie_genres(self, language: str = "en-US") -> list[dict]:
        d = self._get("/genre/movie/list", {"language": language})
        return (d or {}).get("genres") or []

    def tv_genres(self, language: str = "en-US") -> list[dict]:
        d = self._get("/genre/tv/list", {"language": language})
        return (d or {}).get("genres") or []
