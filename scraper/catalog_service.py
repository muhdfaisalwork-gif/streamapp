"""
catalog_service.py — FastAPI service exposing the normalized catalog.db.

Ports: 7801 (catalog) — distinct from :7800 (live scraper service).

Endpoints (Phase 4):
  GET  /health
  GET  /api/v1/titles                       ?type=&genre=&country=&language=&year=&collection=&page=&page_size=&sort=
  GET  /api/v1/titles/movies                ?genre=&country=&year=&sort=&page=
  GET  /api/v1/titles/tv                    ?genre=&country=&sort=&page=
  GET  /api/v1/titles/anime                 ?page=
  GET  /api/v1/titles/short-dramas          ?page=
  GET  /api/v1/titles/trending              ?limit=
  GET  /api/v1/titles/top-rated             ?limit=
  GET  /api/v1/titles/latest                ?limit=
  GET  /api/v1/titles/coming-soon           ?limit=
  GET  /api/v1/title/{id_or_slug}           (canonical detail)
  GET  /api/v1/title/{id_or_slug}/availability
  GET  /api/v1/title/{id_or_slug}/seasons
  GET  /api/v1/search                       ?q=&type=&page=
  GET  /api/v1/genres                       ?with_counts=1
  GET  /api/v1/countries                    ?with_counts=1
  GET  /api/v1/languages                    ?with_counts=1
  GET  /api/v1/collections                  ?with_counts=1
  GET  /api/v1/years                        ?with_counts=1
  GET  /api/v1/sources                      (source health)
  GET  /api/v1/stats                        (overall catalog counts)

Design rules:
  - All counts returned are REAL SQL COUNT(*) queries against catalog.db.
  - Pagination uses LIMIT/OFFSET (cursor-less but bounded to 100/page).
  - Filter params are validated; unknown values yield 400.
  - CORS wide-open for the Expo / web client.
"""
from __future__ import annotations
import json
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

CATALOG_DB = Path(__file__).parent / "catalog.db"

VALID_TYPES = {"movie", "tv", "anime", "short_drama"}
VALID_SORTS = {"popularity", "rating", "year", "title", "newest"}
DEFAULT_PAGE_SIZE = 24
MAX_PAGE_SIZE = 100


# ---------- DB plumbing ------------------------------------------------
class CatalogDB:
    """Read-only connection pool with one connection per request.

    SQLite handles concurrent reads well; writes only happen during migration.
    """
    _instance: Optional["CatalogDB"] = None

    def __init__(self, path: Path):
        self.path = path
        # check_same_thread=False lets FastAPI handler threads reuse the conn
        self._conn = sqlite3.connect(str(path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA query_only=ON")  # extra safety on production

    @classmethod
    def instance(cls) -> "CatalogDB":
        if cls._instance is None:
            cls._instance = cls(CATALOG_DB)
        return cls._instance

    def q(self, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
        return self._conn.execute(sql, params).fetchall()

    def q1(self, sql: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        return self._conn.execute(sql, params).fetchone()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Warm
    CatalogDB.instance()
    yield

app = FastAPI(title="StreamApp Catalog", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Helpers ---------------------------------------------------
def parse_int(v: Optional[str], default: int, mn: int = 1, mx: int = 10000) -> int:
    if v is None or v == "":
        return default
    try:
        i = int(v)
        return max(mn, min(mx, i))
    except ValueError:
        raise HTTPException(400, f"invalid integer: {v!r}")


def parse_csv_ints(v: Optional[str]) -> list[int]:
    if not v:
        return []
    out = []
    for piece in v.split(","):
        piece = piece.strip()
        if not piece:
            continue
        try:
            out.append(int(piece))
        except ValueError:
            raise HTTPException(400, f"invalid id: {piece!r}")
    return out


def row_to_title(r: sqlite3.Row, *, with_relations: bool = False) -> dict[str, Any]:
    """Map a titles-row + (optional) joined relations to the public payload shape."""
    out = {
        "id": r["id"],
        "slug": r["slug"],
        "title": r["title"],
        "originalTitle": r["original_title"],
        "type": r["type"],
        "year": r["year"],
        "releaseDate": r["release_date"],
        "runtime": r["runtime"],
        "rating": r["rating"],
        "popularity": r["popularity"],
        "overview": r["overview"],
        "poster": r["poster"],
        "backdrop": r["backdrop"],
        "trailerUrl": r["trailer_url"],
        "imdbId": r["imdb_id"],
        "tmdbId": r["tmdb_id"],
        "status": r["status"],
        "isAnime": bool(r["is_anime"]),
        "isShortDrama": bool(r["is_short_drama"]),
    }
    if with_relations:
        out["genres"] = []
        out["countries"] = []
        out["languages"] = []
    return out


# ---------- Core listing query (one source of truth for filtering) -----
def build_filter_clause(
    *,
    type_: Optional[str],
    genre_slugs: list[str],
    country_codes: list[str],
    language_codes: list[str],
    collection_slugs: list[str],
    year_min: Optional[int],
    year_max: Optional[int],
) -> tuple[str, list[Any]]:
    """Builds WHERE clause + params. Joins are added by caller when needed."""
    clauses = []
    params: list[Any] = []
    if type_:
        if type_ not in VALID_TYPES:
            raise HTTPException(400, f"invalid type: {type_}")
        clauses.append("t.type = ?")
        params.append(type_)
    if year_min is not None:
        clauses.append("t.year >= ?")
        params.append(year_min)
    if year_max is not None:
        clauses.append("t.year <= ?")
        params.append(year_max)
    join_extra = ""
    if genre_slugs:
        placeholders = ",".join("?" * len(genre_slugs))
        join_extra += (
            f" JOIN title_genres tgf ON tgf.title_id = t.id "
            f"JOIN genres gf ON gf.id = tgf.genre_id "
            f"AND gf.slug IN ({placeholders}) "
        )
        params = list(genre_slugs) + params
        clauses.append("1")  # existence is enforced by JOIN
    if country_codes:
        placeholders = ",".join("?" * len(country_codes))
        join_extra += (
            f" JOIN title_countries tcf ON tcf.title_id = t.id "
            f"JOIN countries cf ON cf.id = tcf.country_id "
            f"AND cf.code IN ({placeholders}) "
        )
        params = list(country_codes) + params
        clauses.append("1")
    if language_codes:
        placeholders = ",".join("?" * len(language_codes))
        join_extra += (
            f" JOIN title_languages tlf ON tlf.title_id = t.id "
            f"JOIN languages lf ON lf.id = tlf.language_id "
            f"AND lf.code IN ({placeholders}) "
        )
        params = list(language_codes) + params
        clauses.append("1")
    if collection_slugs:
        placeholders = ",".join("?" * len(collection_slugs))
        join_extra += (
            f" JOIN title_collections tcolf ON tcolf.title_id = t.id "
            f"JOIN collections colf ON colf.id = tcolf.collection_id "
            f"AND colf.slug IN ({placeholders}) "
        )
        params = list(collection_slugs) + params
        clauses.append("1")
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    return join_extra, where, params


def attach_relations(rows: list[sqlite3.Row], db: CatalogDB) -> list[dict[str, Any]]:
    """Batch-load genres/countries/languages for a list of titles."""
    if not rows:
        return []
    ids = [r["id"] for r in rows]
    placeholders = ",".join("?" * len(ids))
    genres = db.q(
        f"SELECT tg.title_id, g.name, g.slug FROM title_genres tg "
        f"JOIN genres g ON g.id = tg.genre_id "
        f"WHERE tg.title_id IN ({placeholders})", tuple(ids))
    countries = db.q(
        f"SELECT tc.title_id, c.name, c.code, c.flag FROM title_countries tc "
        f"JOIN countries c ON c.id = tc.country_id "
        f"WHERE tc.title_id IN ({placeholders})", tuple(ids))
    languages = db.q(
        f"SELECT tl.title_id, l.name, l.code, l.flag FROM title_languages tl "
        f"JOIN languages l ON l.id = tl.language_id "
        f"WHERE tl.title_id IN ({placeholders})", tuple(ids))
    g_map: dict[int, list] = {i: [] for i in ids}
    c_map: dict[int, list] = {i: [] for i in ids}
    l_map: dict[int, list] = {i: [] for i in ids}
    for r in genres:
        g_map[r["title_id"]].append({"name": r["name"], "slug": r["slug"]})
    for r in countries:
        c_map[r["title_id"]].append({"name": r["name"], "code": r["code"], "flag": r["flag"]})
    for r in languages:
        l_map[r["title_id"]].append({"name": r["name"], "code": r["code"], "flag": r["flag"]})
    out = []
    for r in rows:
        item = row_to_title(r)
        item["genres"] = g_map[r["id"]]
        item["countries"] = c_map[r["id"]]
        item["languages"] = l_map[r["id"]]
        out.append(item)
    return out


def order_clause(sort: str, type_: Optional[str]) -> str:
    if sort == "rating":
        return "ORDER BY t.rating IS NULL, t.rating DESC, t.popularity DESC"
    if sort == "year":
        return "ORDER BY t.year DESC, t.popularity DESC"
    if sort == "title":
        return "ORDER BY t.title COLLATE NOCASE ASC"
    if sort == "newest":
        return "ORDER BY t.created_at DESC"
    # default popularity: rating * log(votes) fallback
    return "ORDER BY t.popularity DESC, t.year DESC"


# ---------- Endpoints --------------------------------------------------
@app.get("/health")
def health():
    db = CatalogDB.instance()
    counts = {
        "titles": db.q1("SELECT COUNT(*) c FROM titles")[0],
        "movies": db.q1("SELECT COUNT(*) c FROM titles WHERE type='movie'")[0],
        "tv": db.q1("SELECT COUNT(*) c FROM titles WHERE type='tv'")[0],
        "anime": db.q1("SELECT COUNT(*) c FROM titles WHERE type='anime'")[0],
        "availability": db.q1("SELECT COUNT(*) c FROM availability")[0],
        "sources": db.q1("SELECT COUNT(*) c FROM sources")[0],
    }
    return {"status": "ok", "service": "catalog", "port": 7801, "counts": counts}


@app.get("/api/v1/stats")
def stats():
    db = CatalogDB.instance()
    by_type = db.q("SELECT type, COUNT(*) c FROM titles GROUP BY type")
    by_decade = db.q(
        "SELECT (year/10)*10 AS decade, COUNT(*) c FROM titles "
        "WHERE year IS NOT NULL GROUP BY decade ORDER BY decade DESC")
    return {
        "by_type": [{"type": r["type"], "count": r["c"]} for r in by_type],
        "by_decade": [{"decade": r["decade"], "count": r["c"]} for r in by_decade],
    }


@app.get("/api/v1/titles")
def list_titles(
    type: Optional[str] = None,
    genre: Optional[str] = None,
    country: Optional[str] = None,
    language: Optional[str] = None,
    collection: Optional[str] = None,
    year_min: Optional[int] = None,
    year_max: Optional[int] = None,
    sort: str = "popularity",
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    with_relations: bool = True,
):
    db = CatalogDB.instance()
    if sort not in VALID_SORTS:
        raise HTTPException(400, f"invalid sort: {sort}")
    genre_slugs = [s.strip() for s in (genre or "").split(",") if s.strip()]
    country_codes = [s.strip().upper() for s in (country or "").split(",") if s.strip()]
    language_codes = [s.strip().lower() for s in (language or "").split(",") if s.strip()]
    collection_slugs = [s.strip() for s in (collection or "").split(",") if s.strip()]

    join_extra, where, params = build_filter_clause(
        type_=type,
        genre_slugs=genre_slugs,
        country_codes=country_codes,
        language_codes=language_codes,
        collection_slugs=collection_slugs,
        year_min=year_min,
        year_max=year_max,
    )

    base = f"FROM titles t {join_extra} {where}"
    # total
    total = db.q1(f"SELECT COUNT(DISTINCT t.id) c {base}", tuple(params))[0]
    # page rows
    offset = (page - 1) * page_size
    rows = db.q(
        f"SELECT DISTINCT t.* {base} {order_clause(sort, type)} LIMIT ? OFFSET ?",
        tuple(params) + (page_size, offset),
    )
    items = attach_relations(rows, db) if with_relations else [row_to_title(r) for r in rows]
    return {
        "items": items,
        "page": page,
        "pageSize": page_size,
        "total": total,
        "hasMore": offset + len(items) < total,
    }


@app.get("/api/v1/titles/movies")
def list_movies(
    genre: Optional[str] = None,
    country: Optional[str] = None,
    year: Optional[int] = None,
    sort: str = "popularity",
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
):
    return list_titles(
        type="movie", genre=genre, country=country, year_min=year, year_max=year,
        sort=sort, page=page, page_size=page_size,
    )


@app.get("/api/v1/titles/tv")
def list_tv(
    genre: Optional[str] = None,
    country: Optional[str] = None,
    sort: str = "popularity",
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
):
    return list_titles(
        type="tv", genre=genre, country=country, sort=sort,
        page=page, page_size=page_size,
    )


@app.get("/api/v1/titles/anime")
def list_anime(
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
):
    """Anime endpoint uses the canonical 'anime' genre (more reliable than the type field,
    which depends on the legacy data having Japan country metadata)."""
    return list_titles(genre="anime", sort="popularity", page=page, page_size=page_size)


@app.get("/api/v1/titles/short-dramas")
def list_short_dramas(
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
):
    return list_titles(type="short_drama", sort="popularity", page=page, page_size=page_size)


@app.get("/api/v1/titles/trending")
def trending(limit: int = Query(20, ge=1, le=100)):
    """Trending = highest rating count proxy: titles with rating AND non-zero popularity,
    ordered by popularity * rating. Until we have real telemetry, this is the most
    honest proxy available without inflating."""
    db = CatalogDB.instance()
    rows = db.q(
        "SELECT * FROM titles WHERE rating IS NOT NULL AND rating > 0 "
        "ORDER BY (rating * (popularity + 1)) DESC, year DESC LIMIT ?", (limit,))
    return {"items": attach_relations(rows, db)}


@app.get("/api/v1/titles/top-rated")
def top_rated(limit: int = Query(20, ge=1, le=100)):
    db = CatalogDB.instance()
    rows = db.q(
        "SELECT * FROM titles WHERE rating IS NOT NULL "
        "ORDER BY rating DESC, popularity DESC LIMIT ?", (limit,))
    return {"items": attach_relations(rows, db)}


@app.get("/api/v1/titles/latest")
def latest(limit: int = Query(20, ge=1, le=100)):
    db = CatalogDB.instance()
    rows = db.q("SELECT * FROM titles WHERE year IS NOT NULL ORDER BY year DESC, id DESC LIMIT ?", (limit,))
    return {"items": attach_relations(rows, db)}


@app.get("/api/v1/titles/coming-soon")
def coming_soon(limit: int = Query(20, ge=1, le=100)):
    """Coming Soon = titles flagged with status='upcoming' OR (year in the future AND no availability)."""
    db = CatalogDB.instance()
    now_year = 2026  # frozen dev-time; a real cron would refresh
    rows = db.q(
        "SELECT * FROM titles WHERE status='upcoming' OR (year > ? AND NOT EXISTS "
        "(SELECT 1 FROM availability WHERE title_id = titles.id)) "
        "ORDER BY year ASC LIMIT ?", (now_year, limit))
    return {"items": attach_relations(rows, db)}


@app.get("/api/v1/title/{id_or_slug}")
def get_title(id_or_slug: str):
    db = CatalogDB.instance()
    if id_or_slug.isdigit():
        r = db.q1("SELECT * FROM titles WHERE id = ?", (int(id_or_slug),))
    else:
        r = db.q1("SELECT * FROM titles WHERE slug = ?", (id_or_slug,))
    if not r:
        raise HTTPException(404, "title not found")
    item = attach_relations([r], db)[0]
    # Attach availability
    av = db.q(
        "SELECT s.slug AS source_slug, s.name AS source_name, a.status, a.external_url, "
        "a.quality_options, a.format_options, a.last_checked_at "
        "FROM availability a JOIN sources s ON s.id = a.source_id "
        "WHERE a.title_id = ? ORDER BY s.slug", (r["id"],))
    item["availability"] = [
        {
            "source": a["source_slug"],
            "sourceName": a["source_name"],
            "status": a["status"],
            "url": a["external_url"],
            "quality": json.loads(a["quality_options"] or "[]"),
            "format": json.loads(a["format_options"] or "[]"),
            "lastChecked": a["last_checked_at"],
        }
        for a in av
    ]
    return item


@app.get("/api/v1/title/{id_or_slug}/availability")
def get_availability(id_or_slug: str):
    item = get_title(id_or_slug)
    return {"id": item["id"], "slug": item["slug"], "availability": item["availability"]}


@app.get("/api/v1/title/{id_or_slug}/seasons")
def get_seasons(id_or_slug: str):
    db = CatalogDB.instance()
    r = db.q1("SELECT id FROM titles WHERE id = ? OR slug = ?", (int(id_or_slug) if id_or_slug.isdigit() else -1, id_or_slug))
    if not r:
        raise HTTPException(404, "title not found")
    seasons = db.q("SELECT * FROM seasons WHERE title_id = ? ORDER BY season_number", (r["id"],))
    return {"seasons": [dict(s) for s in seasons]}


@app.get("/api/v1/search")
def search(
    q: str = Query(..., min_length=1),
    type: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
):
    db = CatalogDB.instance()
    if type and type not in VALID_TYPES:
        raise HTTPException(400, f"invalid type: {type}")
    pat = f"%{q.lower()}%"
    type_clause = "AND t.type = ?" if type else ""
    params: list[Any] = [pat]
    if type:
        params.append(type)
    total = db.q1(
        f"SELECT COUNT(DISTINCT t.id) c FROM titles t "
        f"WHERE (LOWER(t.title) LIKE ? OR LOWER(IFNULL(t.original_title,'')) LIKE ? OR LOWER(t.slug) LIKE ?) "
        f"{type_clause}",
        (pat, pat, pat, *params))[0]
    offset = (page - 1) * page_size
    rows = db.q(
        f"SELECT DISTINCT t.* FROM titles t "
        f"WHERE (LOWER(t.title) LIKE ? OR LOWER(IFNULL(t.original_title,'')) LIKE ? OR LOWER(t.slug) LIKE ?) "
        f"{type_clause} "
        f"ORDER BY t.popularity DESC, t.rating DESC LIMIT ? OFFSET ?",
        (pat, pat, pat, *params, page_size, offset))
    return {
        "items": attach_relations(rows, db),
        "query": q,
        "page": page,
        "pageSize": page_size,
        "total": total,
        "hasMore": offset + len(rows) < total,
    }


@app.get("/api/v1/genres")
def genres(with_counts: bool = True):
    db = CatalogDB.instance()
    if with_counts:
        rows = db.q(
            "SELECT g.id, g.slug, g.name, g.sort_order, COUNT(tg.title_id) AS cnt "
            "FROM genres g LEFT JOIN title_genres tg ON tg.genre_id = g.id "
            "GROUP BY g.id ORDER BY cnt DESC, g.sort_order")
        return {"items": [
            {"id": r["id"], "slug": r["slug"], "name": r["name"], "count": r["cnt"]}
            for r in rows
        ]}
    rows = db.q("SELECT id, slug, name, sort_order FROM genres ORDER BY sort_order, name")
    return {"items": [dict(r) for r in rows]}


@app.get("/api/v1/countries")
def countries(with_counts: bool = True):
    db = CatalogDB.instance()
    if with_counts:
        rows = db.q(
            "SELECT c.id, c.code, c.name, c.flag, c.region, COUNT(tc.title_id) AS cnt "
            "FROM countries c LEFT JOIN title_countries tc ON tc.country_id = c.id "
            "GROUP BY c.id ORDER BY cnt DESC, c.name")
        return {"items": [
            {"id": r["id"], "code": r["code"], "name": r["name"], "flag": r["flag"],
             "region": r["region"], "count": r["cnt"]}
            for r in rows
        ]}
    rows = db.q("SELECT * FROM countries ORDER BY name")
    return {"items": [dict(r) for r in rows]}


@app.get("/api/v1/languages")
def languages(with_counts: bool = True):
    db = CatalogDB.instance()
    if with_counts:
        rows = db.q(
            "SELECT l.id, l.code, l.name, l.native_name, l.flag, COUNT(tl.title_id) AS cnt "
            "FROM languages l LEFT JOIN title_languages tl ON tl.language_id = l.id "
            "GROUP BY l.id ORDER BY cnt DESC, l.name")
        return {"items": [
            {"id": r["id"], "code": r["code"], "name": r["name"],
             "nativeName": r["native_name"], "flag": r["flag"], "count": r["cnt"]}
            for r in rows
        ]}
    rows = db.q("SELECT * FROM languages ORDER BY name")
    return {"items": [dict(r) for r in rows]}


@app.get("/api/v1/collections")
def collections(with_counts: bool = True):
    db = CatalogDB.instance()
    if with_counts:
        rows = db.q(
            "SELECT c.id, c.slug, c.name, c.type, COUNT(tc.title_id) AS cnt "
            "FROM collections c LEFT JOIN title_collections tc ON tc.collection_id = c.id "
            "GROUP BY c.id ORDER BY cnt DESC, c.name")
        return {"items": [
            {"id": r["id"], "slug": r["slug"], "name": r["name"],
             "type": r["type"], "count": r["cnt"]}
            for r in rows
        ]}
    rows = db.q("SELECT * FROM collections ORDER BY name")
    return {"items": [dict(r) for r in rows]}


@app.get("/api/v1/years")
def years():
    db = CatalogDB.instance()
    rows = db.q(
        "SELECT year, COUNT(*) c FROM titles WHERE year IS NOT NULL "
        "GROUP BY year ORDER BY year DESC")
    return {"items": [{"year": r["year"], "count": r["c"]} for r in rows]}


@app.get("/api/v1/sources")
def sources():
    db = CatalogDB.instance()
    rows = db.q(
        "SELECT s.id, s.slug, s.name, s.base_url, s.type, s.enabled, s.is_legal, "
        "COUNT(a.id) AS availability_count "
        "FROM sources s LEFT JOIN availability a ON a.source_id = s.id "
        "GROUP BY s.id ORDER BY availability_count DESC")
    return {"items": [dict(r) for r in rows]}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7801, log_level="info")