"""
tvdb_client.py — Minimal TheTVDB v4 API client.

Mirrors tmdb_client.py's style: throttled requests, a custom error type,
and a `_get` helper that returns None for a real 404 rather than raising.

Get a free key at https://thetvdb.com/api-information
"""
from __future__ import annotations
import logging
import os
import threading
import time

import requests

log = logging.getLogger("tvdb")

BASE_URL = "https://api4.thetvdb.com/v4"
DEFAULT_TIMEOUT = 15
MIN_INTERVAL_SEC = 0.1


class TvdbError(RuntimeError):
    """Raised when the upstream TVDB API fails or returns malformed data."""


class TvdbClient:
    def __init__(self, api_key: str | None = None, session: requests.Session | None = None):
        self.api_key = api_key or os.environ.get("TVDB_API_KEY") or ""
        if not self.api_key:
            raise TvdbError("TVDB_API_KEY not set. Get one at https://thetvdb.com/api-information")
        self._session = session or requests.Session()
        self._last_call = 0.0
        self._lock = threading.Lock()
        self._token: str | None = None

    def _throttle(self) -> None:
        with self._lock:
            now = time.monotonic()
            wait = MIN_INTERVAL_SEC - (now - self._last_call)
            if wait > 0:
                time.sleep(wait)
            self._last_call = time.monotonic()

    def _login(self) -> None:
        response = self._session.post(f"{BASE_URL}/login", json={"apikey": self.api_key}, timeout=DEFAULT_TIMEOUT)
        if response.status_code != 200:
            raise TvdbError(f"TVDB login failed: HTTP {response.status_code}")
        data = (response.json() or {}).get("data") or {}
        token = data.get("token")
        if not token:
            raise TvdbError("TVDB login failed: no token in response")
        self._token = token

    def _ensure_token(self) -> None:
        if self._token is None:
            self._login()

    def _get(self, path: str, params: dict | None = None, _retried: bool = False) -> dict | None:
        self._ensure_token()
        self._throttle()
        headers = {"Authorization": f"Bearer {self._token}"}
        try:
            response = self._session.get(f"{BASE_URL}{path}", headers=headers, params=params, timeout=DEFAULT_TIMEOUT)
        except requests.RequestException as e:
            log.warning("TVDB request failed: %s (%s)", path, e)
            return None

        if response.status_code == 401:
            if _retried:
                raise TvdbError("TVDB 401 Unauthorized after re-login")
            self._token = None
            return self._get(path, params, _retried=True)
        if response.status_code == 404:
            return None
        try:
            response.raise_for_status()
        except requests.RequestException as e:
            log.warning("TVDB request failed: %s (%s)", path, e)
            return None

        try:
            return response.json().get("data")
        except ValueError:
            log.warning("TVDB returned non-JSON response for %s", path)
            return None

    def search_series(self, name: str, year: int | None = None) -> list[dict]:
        params: dict = {"query": name, "type": "series"}
        if year:
            params["year"] = year
        result = self._get("/search", params)
        return result if isinstance(result, list) else []

    def series_extended(self, series_id: int) -> dict | None:
        return self._get(f"/series/{series_id}/extended")

    def series_episodes(self, series_id: int, season_type: str = "default", page: int = 0) -> dict | None:
        return self._get(f"/series/{series_id}/episodes/{season_type}", {"page": page})
