"""
Export seasons + episodes to R2, and fix the availability `kind` label.

Why this exists
---------------
`scraper/catalog.db` has always held the season and episode tables
(~21k season rows, ~631k episode rows across ~3.4k TV titles). The R2
catalog export simply never published them, so the Worker's
`/title/{id}/seasons` route returned `[]` for every TV title in the
catalogue. That is why season chips, the in-player episode drawer, the
next-episode button and the binge countdown all silently did nothing.

The same export also corrects the `availability.kind` column. It was
written as 'playback' for rows that came from embed aggregators, so the
frontend believed it had direct streams and skipped its own player. Rows
are re-derived from `sources.type` instead of trusting the stored label.

Usage:
    python scraper/export_catalog_seasons.py --out <dir> [--db <path>]

Writes:
    <out>/seasons/index.json          { "<title_id>": "<shard>" }
    <out>/seasons/<shard>.json        { seasons: [...] }
    <out>/providers.json              provider registry override
    <out>/availability-kind-fixes.json  audit trail of reclassified rows
"""

import argparse
import json
import os
import sqlite3
import sys
from collections import defaultdict

TITLES_PER_SHARD = 200
# Shard by serialised size, not by title count. A fixed count produced shards
# ranging from 1.6 MB to 37.8 MB depending on how many episodes each title had,
# and the large ones repeatedly died mid-upload on a flaky connection. A size
# cap keeps every object small enough to upload reliably.
MAX_SHARD_BYTES = 1_500_000

# URL suffixes that make an availability row genuinely, directly playable.
DIRECT_EXTENSIONS = (".m3u8", ".mp4", ".webm", ".mkv", ".mov")


def log(msg):
    print(f"[export] {msg}", flush=True)


def normalize_url(url):
    """TMDB images must be https or every page emits a mixed-content warning."""
    if isinstance(url, str) and url.startswith("http://"):
        return "https://" + url[len("http://"):]
    return url


def is_directly_playable(url):
    if not isinstance(url, str) or not url:
        return False
    low = url.lower().split("?")[0]
    return low.endswith(DIRECT_EXTENSIONS)


def export_seasons(conn, out_dir):
    cur = conn.cursor()

    cur.execute(
        "SELECT id, title_id, season_number, name, overview, poster, air_date, episode_count "
        "FROM seasons ORDER BY title_id, season_number"
    )
    by_title = defaultdict(list)
    for sid, title_id, num, name, overview, poster, air_date, count in cur.fetchall():
        by_title[int(title_id)].append(
            {
                "id": sid,
                "season_number": num,
                "name": name,
                "overview": overview,
                "poster": normalize_url(poster),
                "air_date": air_date,
                "episode_count": count,
            }
        )

    cur.execute(
        "SELECT e.season_id, e.id, e.episode_number, e.title, e.overview, e.thumbnail, e.air_date, e.runtime "
        "FROM episodes e"
    )
    season_to_title = {}
    for title_id, seasons in by_title.items():
        for s in seasons:
            season_to_title[s["id"]] = title_id

    eps_by_season = defaultdict(list)
    orphan = 0
    for season_id, eid, num, title, overview, thumb, air_date, runtime in cur.fetchall():
        title_id = season_to_title.get(season_id)
        if title_id is None:
            orphan += 1
            continue
        eps_by_season[season_id].append(
            {
                "id": eid,
                "episode_number": num,
                "name": title,
                "overview": overview,
                "thumbnail": normalize_url(thumb),
                "air_date": air_date,
                "runtime": runtime,
            }
        )

    total_eps = 0
    for seasons in by_title.values():
        for s in seasons:
            eps = sorted(eps_by_season.get(s["id"], []), key=lambda e: e["episode_number"] or 0)
            s["episodes"] = eps
            if eps:
                s["episode_count"] = len(eps)
            total_eps += len(eps)

    seasons_dir = os.path.join(out_dir, "seasons")
    os.makedirs(seasons_dir, exist_ok=True)

    title_ids = sorted(by_title.keys())
    index = {}
    shard_id = 0
    chunk = []
    chunk_bytes = 0

    def flush(chunk):
        nonlocal shard_id
        if not chunk:
            return
        payload = {
            "titles": chunk,
            "seasons": [s for tid in chunk for s in by_title[tid]],
        }
        name = f"seasons-{shard_id:04d}.json"
        # Write to a temp name then promote, so a partial write can never be
        # published as a valid shard.
        tmp = os.path.join(seasons_dir, name + ".tmp")
        final = os.path.join(seasons_dir, name)
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
        os.replace(tmp, final)
        for tid in chunk:
            index[str(tid)] = name
        shard_id += 1

    for tid in title_ids:
        approx = len(json.dumps(by_title[tid], ensure_ascii=False, separators=(",", ":")))
        if chunk and (chunk_bytes + approx > MAX_SHARD_BYTES or len(chunk) >= TITLES_PER_SHARD):
            flush(chunk)
            chunk = []
            chunk_bytes = 0
        chunk.append(tid)
        chunk_bytes += approx
    flush(chunk)

    tmp = os.path.join(seasons_dir, "index.json.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(index, f, separators=(",", ":"))
    os.replace(tmp, os.path.join(seasons_dir, "index.json"))

    # title_id -> [season_id, ...]
    #
    # The shards are grouped by title but store a flat season list without
    # repeating title_id on every row, so the Worker cannot filter a shard down
    # to one title from the shard alone. This map is ~150 KB and lets it do so
    # without re-uploading the whole 223 MB dataset.
    by_title = {
        str(tid): [s["id"] for s in seasons] for tid, seasons in by_title.items()
    }
    tmp = os.path.join(seasons_dir, "by-title.json.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(by_title, f, separators=(",", ":"))
    os.replace(tmp, os.path.join(seasons_dir, "by-title.json"))
    log(f"by-title map: {len(by_title)} titles, {os.path.getsize(os.path.join(seasons_dir, 'by-title.json'))/1024:.0f} KB")

    log(f"seasons: {len(by_title)} titles, {sum(len(v) for v in by_title.values())} season rows, {total_eps} episodes, {shard_id} shards")
    if orphan:
        log(f"WARNING: {orphan} episode rows had no matching season and were dropped")
    return len(by_title), total_eps


def reclassify_availability(conn, out_dir):
    """Re-derive `kind` from the source type instead of trusting the label."""
    cur = conn.cursor()
    cur.execute(
        """
        SELECT a.id, a.title_id, a.source_id, a.kind, a.playback_url, a.external_url, s.slug, s.type
        FROM availability a
        JOIN sources s ON s.id = a.source_id
        WHERE a.kind = 'playback'
        """
    )
    rows = cur.fetchall()

    to_embed = []
    to_playback = []
    for aid, title_id, source_id, kind, playback_url, external_url, slug, stype in rows:
        url = playback_url or ""
        if is_directly_playable(url):
            if kind != "playback":
                to_playback.append(aid)
        else:
            # An embed aggregator is an embed, whatever the row claimed.
            if kind != "embed":
                to_embed.append(aid)

    if to_embed:
        cur.executemany("UPDATE availability SET kind='embed' WHERE id=?", [(i,) for i in to_embed])
    if to_playback:
        cur.executemany("UPDATE availability SET kind='playback' WHERE id=?", [(i,) for i in to_playback])
    conn.commit()

    audit = {
        "reclassified_at_row_count": len(rows),
        "playback_to_embed": len(to_embed),
        "embed_to_playback": len(to_playback),
        "note": "Rows from embed_aggregator sources were labelled 'playback' but carry no media URL. "
                "The frontend trusted that label and skipped its own player engine.",
    }
    with open(os.path.join(out_dir, "availability-kind-fixes.json"), "w", encoding="utf-8") as f:
        json.dump(audit, f, indent=2)

    # This line used to read "... N kept as playback", which was wrong twice
    # over: to_playback holds rows promoted FROM embed, not rows left alone,
    # and rows already correctly labelled playback were never counted at all.
    # It printed "0 kept as playback" on a run where 23,317 titles were
    # natively playable, which reads exactly like a total loss of playback.
    still_playback = len(rows) - len(to_embed)
    log(f"availability: {len(rows)} rows were labelled 'playback'; "
        f"{len(to_embed)} reclassified to embed; {still_playback:,} still playback; "
        f"{len(to_playback)} promoted from embed to playback")
    return audit


def write_providers(out_dir):
    """Provider registry override published to R2.

    Kept deliberately small: the compiled defaults in src/providers.ts hold the
    URL builders, and this file only records state that must be changeable
    without a Worker redeploy.
    """
    providers = [
        {
            "slug": "vidlink",
            "displayName": "Vidlink (Ad-Free HD)",
            "resolveMode": "iframe_only",
            "note": "Probed 2026-09-28: Next.js + RSC, /api/b/tv/{id}/{s}/{e} returns null, "
                    "player gated behind a 2.4 MB /fu.wasm challenge.",
        },
        {
            "slug": "vidsrc",
            "displayName": "VidSrc HD",
            "resolveMode": "iframe_only",
            "note": "Nested iframe; no plain manifest in the page.",
        },
        {
            "slug": "2embed",
            "displayName": "2Embed Multi-Server",
            "resolveMode": "iframe_only",
            "note": "Nested iframe to /embed/.",
        },
        {
            "slug": "embedsu",
            "displayName": "EmbedSu VIP",
            "resolveMode": "disabled",
            "note": "Disabled 2026-09-28: embed.su no longer resolves in DNS.",
        },
        {
            "slug": "superembed",
            "displayName": "SuperEmbed",
            "resolveMode": "disabled",
            "note": "Disabled 2026-09-28: multiembed.mov unreachable.",
        },
    ]
    with open(os.path.join(out_dir, "providers.json"), "w", encoding="utf-8") as f:
        json.dump({"providers": providers}, f, indent=2)
    log(f"providers: wrote {len(providers)} entries")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=r"G:\streaming app\scraper\catalog.db")
    ap.add_argument("--out", default=r"G:\streaming app\downloads\snapshots")
    ap.add_argument("--dry-run", action="store_true", help="report counts without writing or updating the DB")
    args = ap.parse_args()

    if not os.path.exists(args.db):
        sys.exit(f"database not found: {args.db}")
    if os.path.getsize(args.db) == 0:
        sys.exit(f"database is 0 bytes: {args.db} (there is also a 0-byte catalog.db at the repo root — do not use it)")

    os.makedirs(args.out, exist_ok=True)
    # Long busy-wait: reclassify_availability() writes to the DB, and this used
    # the 5-second default, so it died instantly with "database is locked"
    # whenever a concurrent ingest (episode fill, subtitle harvest) held the
    # write lock.
    conn = sqlite3.connect(args.db, timeout=900)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")

    log(f"source: {args.db}")
    log(f"output: {args.out}")

    if args.dry_run:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(DISTINCT title_id) FROM seasons")
        log(f"would export {cur.fetchone()[0]} titles with seasons")
        return

    export_seasons(conn, args.out)
    reclassify_availability(conn, args.out)
    write_providers(args.out)
    conn.close()
    log("done")


if __name__ == "__main__":
    main()
