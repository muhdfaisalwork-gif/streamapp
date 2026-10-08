"""
ingest_subtitles.py — fetch subtitle tracks for natively-playable titles.

Scope, deliberately
-------------------
Only titles that play in OUR engine get subtitles. Embed titles decode inside
a cross-origin provider iframe, and you cannot inject a <track> into someone
else's <video> element — so a subtitle for those would be data nobody can
render. The database already marks exactly which titles those are:

    availability.kind = 'playback' AND availability.playback_url != ''

At the time of writing that is the archive.org / Blender / curated set, so
this script targets the titles where subtitles are actually usable.

OpenSubtitles REST API: search by IMDB id or TMDB id, then download the
compressed (gzip) subtitle blob. Results are written to media_assets, which
already has the right shape (url, language_code, kind) and was empty.

Requires OPENSUBTITLES_API_KEY in scraper/.env.

Run:
    python ingest_subtitles.py --limit 50
    python ingest_subtitles.py --dry-run
"""

from __future__ import annotations

import argparse
import gzip
import io
import json
import sqlite3
import sys
import time
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

HERE = Path(__file__).parent
DB = HERE / "catalog.db"
STATE = HERE / ".subtitle_state.json"
OUT_DIR = HERE / "subtitles"

BASE = "https://api.opensubtitles.com/api/v1"
TIMEOUT = 25


def env_values() -> dict:
    vals = {}
    p = HERE / ".env"
    if p.is_file():
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
            m = line.strip()
            if not m or m.startswith("#") or "=" not in m:
                continue
            k, v = m.split("=", 1)
            vals[k.strip()] = v.strip()
    return vals


ENV = env_values()
API_KEY = ENV.get("OPENSUBTITLES_API_KEY", "")
USERNAME = ENV.get("OPENSUBTITLES_USERNAME", "")
PASSWORD = ENV.get("OPENSUBTITLES_PASSWORD", "")
UA = ENV.get("OPENSUBTITLES_USER_AGENT", "ShadowStreamSubtitleFetcher_v1.0")
TOKEN_CACHE = HERE / ".opensubtitles_token.json"

# The API key authorises search. Downloads need a JWT, which the API only
# issues from POST /login with an account username and password. Verified
# 2026-10-01:
#   GET  /infos/user -> 401 {"errors":["No token in request"]}
#   POST /login      -> 401 "Error, invalid username/password"   (endpoint exists)
#   GET  /subtitles  -> 200                                        (key is fine)
# So the key alone can find subtitles but cannot download a single one.
_TOKEN: str = ""


def login_token() -> str:
    """Exchange username+password for a JWT, cached for a day."""
    global _TOKEN
    if _TOKEN:
        return _TOKEN
    if not (USERNAME and PASSWORD):
        return ""
    if TOKEN_CACHE.is_file():
        try:
            cached = json.loads(TOKEN_CACHE.read_text(encoding="utf-8"))
            if cached.get("token") and time.time() - cached.get("at", 0) < 86400:
                _TOKEN = cached["token"]
                return _TOKEN
        except Exception:
            pass
    req = Request(
        f"{BASE}/login",
        data=json.dumps({"username": USERNAME, "password": PASSWORD}).encode("utf-8"),
        headers={"Api-Key": API_KEY, "Content-Type": "application/json",
                 "User-Agent": UA, "Accept": "application/json"},
        method="POST",
    )
    try:
        with urlopen(req, timeout=TIMEOUT) as r:
            token = json.loads(r.read().decode("utf-8")).get("token", "")
    except Exception:
        return ""
    if token:
        _TOKEN = token
        try:
            TOKEN_CACHE.write_text(
                json.dumps({"token": token, "at": time.time()}), encoding="utf-8"
            )
            TOKEN_CACHE.chmod(0o600)
        except Exception:
            pass
    return token


def load_state() -> dict:
    if STATE.is_file():
        try:
            return json.loads(STATE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"done": [], "written": 0, "no_subs": 0, "errors": 0}


def save_state(st: dict) -> None:
    STATE.write_text(json.dumps(st), encoding="utf-8")


def api(path: str, params: dict | None = None, binary: bool = False):
    parts = []
    for k, v in (params or {}).items():
        if v not in (None, ""):
            parts.append(f"{quote(str(k))}={quote(str(v))}")
    url = f"{BASE}{path}" + ("?" + "&".join(parts) if parts else "")
    headers = {
        "Api-Key": API_KEY,
        "User-Agent": UA,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    token = login_token()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = Request(url, headers=headers)
    with urlopen(req, timeout=TIMEOUT) as r:
        data = r.read()
    return data if binary else json.loads(data.decode("utf-8", errors="replace"))


def download_subtitle(file_id: int) -> bytes | None:
    try:
        raw = api(f"/subtitles/{file_id}/content", binary=True)
    except Exception:
        return None
    # OpenSubtitles returns gzip by default; fall back to plain text.
    if raw[:2] == b"\x1f\x8b":
        try:
            return gzip.decompress(raw)
        except Exception:
            return raw
    return raw


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not API_KEY:
        print("FATAL: OPENSUBTITLES_API_KEY not set in scraper/.env")
        sys.exit(3)

    conn = sqlite3.connect(str(DB), timeout=60)
    conn.execute("PRAGMA journal_mode = WAL")
    cur = conn.cursor()

    # Only titles that play in our own engine. Everything else renders inside a
    # cross-origin iframe where a <track> would be useless.
    rows = cur.execute("""
        SELECT DISTINCT t.id, t.title, t.imdb_id, t.tmdb_id
        FROM titles t
        JOIN availability a ON a.title_id = t.id
        WHERE a.kind = 'playback' AND a.playback_url IS NOT NULL AND a.playback_url != ''
          AND (t.imdb_id IS NOT NULL OR t.tmdb_id IS NOT NULL)
    """).fetchall()

    state = load_state()
    done = set(state.get("done", []))
    pending = [r for r in rows if str(r[0]) not in done]

    print(f"natively-playable titles with an id: {len(rows)}")
    print(f"already attempted: {len(done)}   pending: {len(pending)}")
    if args.dry_run:
        for r in pending[:6]:
            print(f"  would fetch for {r[1][:40]!r} imdb={r[2]} tmdb={r[3]}")
        return
    if args.limit:
        pending = pending[: args.limit]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    written = state.get("written", 0)
    no_subs = state.get("no_subs", 0)
    errors = state.get("errors", 0)
    started = time.time()

    for i, (tid, title, imdb_id, tmdb_id) in enumerate(pending, 1):
        done.add(str(tid))
        try:
            if imdb_id:
                res = api("/subtitles", {"imdb_id": str(imdb_id).lstrip("tt"), "query": title[:60]})
            else:
                res = api("/subtitles", {"tmdb_id": str(tmdb_id), "query": title[:60]})
        except HTTPError as e:
            errors += 1
            if e.code in (401, 403):
                print("  auth rejected the key — stopping:", e.code)
                save_state({"done": sorted(done), "written": written,
                            "no_subs": no_subs, "errors": errors})
                sys.exit(4)
            continue
        except Exception:
            errors += 1
            continue

        # OpenSubtitles v1 returns JSON:API — the real payload is nested under
        # `attributes`, and the downloadable file id lives in attributes.files.
        subs = res.get("data") or []
        if not subs:
            no_subs += 1
            continue

        got = 0
        seen_langs = set()
        for item in subs[:12]:  # scan a few so we can pick distinct languages
            attrs = item.get("attributes") or {}
            lang = (attrs.get("language") or "und").lower()
            if lang in seen_langs:
                continue
            files = attrs.get("files") or []
            if not files or not files[0].get("file_id"):
                continue

            content = download_subtitle(files[0]["file_id"])
            if not content:
                errors += 1
                continue

            seen_langs.add(lang)
            name = f"sub-{tid}-{lang}.srt"
            (OUT_DIR / name).write_bytes(content)
            cur.execute(
                "INSERT INTO media_assets (title_id, kind, url, language_code, source, is_primary) "
                "VALUES (?,?,?,?,?,?)",
                (tid, "subtitle", f"/subtitles/{name}", lang, "opensubtitles", 1 if got == 0 else 0),
            )
            got += 1
            written += 1
            if got >= 4:
                break

        if i % 10 == 0:
            conn.commit()
            state.update({"done": sorted(done), "written": written,
                          "no_subs": no_subs, "errors": errors})
            save_state(state)
            rate = i / max(time.time() - started, 1)
            print(f"  {i}/{len(pending)}  written={written}  no_subs={no_subs}  errors={errors}  ({rate:.2f}/s)",
                  flush=True)

    conn.commit()
    state.update({"done": sorted(done), "written": written, "no_subs": no_subs, "errors": errors})
    save_state(state)
    print(f"\nthis run: {written} tracks written, {no_subs} titles with none, {errors} errors")
    print("serve the subtitles/ folder from the Worker as static files, then")
    print("expose them via /api/v1/title/{id}/subtitles and pass them to the player.")
    conn.close()


if __name__ == "__main__":
    main()
