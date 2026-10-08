"""
cleanup_dub_suffix_titles.py — Fixes junk title rows with a language suffix
baked into the title string (e.g. "Attack on Titan [English]") — exactly the
"Reacher [Hindi]" anti-pattern the project spec calls out by name.

These rows were a batch import meant to seed an "Anime English Dub"
collection but got created as broken duplicate titles instead: wrong type
(mostly 'movie' for what are actually anime/TV series), is_anime=0, no real
tmdb_id, and the dub language baked into the title text.

Correct fix: merge into the real, properly-classified title as an
audio-language link (title_audio_languages -> English), or strip the junk
suffix in place if no real match exists (never delete the only record).

Generated with qwen2.5-coder:7b via Ollama MCP, assembled and bug-fixed by
Claude (find_real_match crashed with TypeError when junk_year was None and
multiple same-titled candidates existed — the "return the first" branch for
that case was never actually implemented).
"""
from __future__ import annotations
import argparse
import json
import logging
import re
import sqlite3

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("cleanup_dub_suffix")

SUFFIX_PATTERN = re.compile(r"\s*\[(English|Hindi|Dubbed|Sub)\]\s*$", re.IGNORECASE)


def find_junk_rows(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT id, title, year, tmdb_id FROM titles "
        "WHERE title LIKE '%[English]%' OR title LIKE '%[Hindi]%' "
        "OR title LIKE '%[Dubbed]%' OR title LIKE '%[Sub]%'"
    ).fetchall()


def find_real_match(conn: sqlite3.Connection, clean_title: str, junk_id: int, junk_year: int | None) -> int | None:
    rows = conn.execute(
        "SELECT id, year FROM titles WHERE lower(title) = lower(?) AND id != ? "
        "AND tmdb_id IS NOT NULL AND tmdb_id != ''",
        (clean_title, junk_id),
    ).fetchall()
    if not rows:
        return None
    if len(rows) == 1:
        return rows[0]["id"]
    if junk_year is None:
        return rows[0]["id"]
    dated = [r for r in rows if r["year"] is not None]
    if not dated:
        return rows[0]["id"]
    return min(dated, key=lambda r: abs(r["year"] - junk_year))["id"]


def get_english_language_id(conn: sqlite3.Connection) -> int | None:
    row = conn.execute("SELECT id FROM languages WHERE code='en'").fetchone()
    return row["id"] if row else None


def cleanup(db_path: str = "catalog.db") -> dict:
    counts = {"merged": 0, "cleaned_in_place": 0, "skipped_no_english_lang": 0, "errors": 0}
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    english_id = get_english_language_id(conn)

    for row in find_junk_rows(conn):
        try:
            clean_title = SUFFIX_PATTERN.sub("", row["title"]).strip()
            match_id = find_real_match(conn, clean_title, row["id"], row["year"])
            if match_id:
                if not english_id:
                    counts["skipped_no_english_lang"] += 1
                    log.warning("Skipping junk row %s: no 'en' row in languages table", row["id"])
                    continue
                conn.execute(
                    "INSERT OR IGNORE INTO title_audio_languages (title_id, language_id) VALUES (?,?)",
                    (match_id, english_id),
                )
                conn.execute("DELETE FROM titles WHERE id = ?", (row["id"],))
                conn.commit()
                counts["merged"] += 1
                log.info("Merged junk id=%s ('%s') into real id=%s ('%s')", row["id"], row["title"], match_id, clean_title)
            else:
                conn.execute("UPDATE titles SET title = ? WHERE id = ?", (clean_title, row["id"]))
                conn.commit()
                counts["cleaned_in_place"] += 1
                log.info("Cleaned in place id=%s: '%s' -> '%s'", row["id"], row["title"], clean_title)
        except Exception as e:
            log.exception("Error processing junk row %s: %s", row["id"], e)
            counts["errors"] += 1

    conn.close()
    return counts


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cleanup junk dub-suffix title rows")
    parser.add_argument("--db", default="catalog.db")
    args = parser.parse_args()

    result = cleanup(db_path=args.db)
    print(json.dumps(result, indent=2))
