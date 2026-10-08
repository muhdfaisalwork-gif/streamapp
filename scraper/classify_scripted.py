"""
classify_scripted.py — separate scripted TV series from talk/variety shows.

The problem this fixes
----------------------
The TV listing is dominated by non-fiction. Right now the top titles by
popularity are:

    The Tonight Show Starring Johnny Carson
    Come Home Love: Lo and Behold          (failed daytime soap)
    Watch What Happens Live with Andy Cohen
    The Late Show with Stephen Colbert
    The Tonight Show Starring Jimmy Fallon

Genre alone does not solve it — only 3,624 of 58,308 TV titles are tagged
news/reality/talk/documentary, because most talk shows simply are not tagged
correctly.

The reliable signal is season structure. Talk shows, game shows, news and
variety panels do not run to seasons; scripted series do. 22,531 TV titles
have at least one season.

Rule applied
------------
    scripted = has at least one season
               AND not tagged news / reality / talk-show / documentary

That leaves roughly 22,000 scripted series. It is a heuristic, not truth: a
failed daytime soap still has seasons, so it survives. But it removes the
talk/variety flood, which is what the listing was actually broken by.

Writes a side table rather than altering `titles`, because titles is the
hottest table in the database and a 200K-row UPDATE on it is slow and
risky next to the running ingests. The export joins this table.

Run:
    python classify_scripted.py --dry-run
    python classify_scripted.py
"""

from __future__ import annotations

import argparse
import re
import sqlite3
import time
from pathlib import Path

HERE = Path(__file__).parent
DB = HERE / "catalog.db"

# Genres that indicate non-scripted broadcast. Documentary is included because
# in a TV context it is overwhelmingly factual/presentational rather than
# scripted drama.
NON_SCRIPTED_GENRES = ("news", "reality", "talk-show", "documentary", "game-show")

# TMDB has no "Talk Shows" genre. A talk show is usually tagged `comedy` or
# carries NO genre at all, so the genre rule alone cannot see them and they came
# through classified as scripted — which is why the home rails were led by The
# Tonight Show, Watch What Happens Live and The Late Show, all of which outrank
# real drama purely because they have aired for decades and therefore accumulate
# enormous season counts.
#
# There is no keywords table in this DB, and the structural signal (many
# seasons, few episodes each) is not usable: it also matches award ceremonies
# and legitimate long-running animation such as Go! Anpanman. So this is an
# explicit, maintained list of talk/variety franchises.
#
# Patterns are matched against the lowercased title with non-alphanumerics
# collapsed to spaces, so "The Tonight Show" matches "tonight show" but
# "The Talk" is deliberately NOT listed on its own - it is far too generic and
# would catch scripted series with the word "talk" in the name.
TALK_SHOW_PATTERNS = (
    # US late-night / talk
    "tonight show", "late show", "late late show", "early show", "daily show",
    "weekend update", "watch what happens", "live with kelly",
    "good morning america", "today show", "the view", "saturday night live",
    "with stephen colbert", "jimmy kimmel", "jay leno", "david letterman",
    "craig ferguson", "graham norton", "seth meyers", "tonight show starring",
    "ellen degeneres", "ellen s show", "the oprah", "kelly clarkson",
    "kathie lee gifford", "wendy williams", "jerry springer", "dr phil",
    "phil mccraw", "steve harvey show", "entertainment tonight",
    "access hollywood", "tmz", "the red table", "conan o brien", "conan obrien",
    # Non-US / regional talk formats
    "good morning britain", "the one show", "loose women", "studio 10",
    "pixel 11 morning", "eyewitness news", "the project", "morning rothko",
    # Variety / competition formats that are not scripted drama.
    # Anchored on distinctive phrases so a scripted series with a similar word
    # in the name is not swept up.
    "survivor series", "big brother", "the voice", "american idol", "x factor",
    "dancing with the stars", "the mask singer", "nailed it", "cupcake wars",
    "top chef", "masterchef", "master chef", "great bake off", "bake off",
    "project runway", "cutthroat kitchen", "great british bake off",
    "americas got talent", "got talent", "whose line", "the circle",
    "ex on the beach", "love island", "jersey shore", "kitchen nightmares",
    "last comic standing", "the bachelor", "worlds funniest home videos",
)


def _norm_title(s: str) -> str:
    """Lowercase and collapse punctuation to single spaces, so 'Jimmy Kimmel
    Live!' and 'the  late  show' both normalise to single-spaced words."""
    out = []
    for ch in (s or "").lower():
        out.append(ch if ch.isalnum() else " ")
    return " ".join("".join(out).split())


# Word-boundary compiled once. Plain substring matching pulled in Conan Gray,
# Extraordinary Measures, Carson's Law and Future Boy Conan, because patterns
# like "conan" and "extra" match inside unrelated words.
_TALK_RE = tuple(re.compile(r"\b" + re.escape(p) + r"\b") for p in TALK_SHOW_PATTERNS)


def is_talk_show(title: str) -> bool:
    n = _norm_title(title)
    return any(rx.search(n) for rx in _TALK_RE)

DDL = """
CREATE TABLE IF NOT EXISTS title_classification (
    title_id   INTEGER PRIMARY KEY,
    is_scripted INTEGER NOT NULL,
    seasons    INTEGER NOT NULL DEFAULT 0,
    reason     TEXT
)
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    # Long busy-wait: this job holds the write lock for a big DELETE + two bulk
    # INSERTs, so it is the one most likely to collide with a concurrent writer.
    conn = sqlite3.connect(str(DB), timeout=900)
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute(DDL)

    # Count what each signal alone would do, so the decision is visible.
    tv = conn.execute("SELECT COUNT(*) FROM titles WHERE type IN ('tv','anime')").fetchone()[0]
    with_seasons = conn.execute(
        "SELECT COUNT(DISTINCT s.title_id) FROM seasons s "
        "JOIN titles t ON t.id = s.title_id WHERE t.type IN ('tv','anime')"
    ).fetchone()[0]

    if args.dry_run:
        placeholders = ",".join("?" for _ in NON_SCRIPTED_GENRES)
        tagged = conn.execute(
            f"""SELECT COUNT(DISTINCT t.id) FROM titles t
                JOIN title_genres tg ON tg.title_id = t.id
                JOIN genres g ON g.id = tg.genre_id
                WHERE t.type IN ('tv','anime') AND g.slug IN ({placeholders})""",
            NON_SCRIPTED_GENRES,
        ).fetchone()[0]
        print(f"tv + anime titles        : {tv:,}")
        print(f"  with >= 1 season       : {with_seasons:,}")
        print(f"  tagged non-scripted    : {tagged:,}  ({', '.join(NON_SCRIPTED_GENRES)})")
        print(f"  would REMAIN scripted  : ~{with_seasons:,} (seasons AND not non-scripted genre)")
        print(f"  would be EXCLUDED      : ~{tv - with_seasons:,}")
        conn.close()
        return

    started = time.time()
    placeholders = ",".join("?" for _ in NON_SCRIPTED_GENRES)

    conn.execute("DELETE FROM title_classification")

    # Scripted = has seasons, carries no non-scripted genre, and is not a
    # talk/variety franchise. The last clause is applied in Python because the
    # pattern list is far more readable here than as a SQL LIKE chain, and the
    # candidate set (episodic titles that already passed the genre test) is
    # small enough to check in one pass.
    genre_excl = ",".join("?" for _ in NON_SCRIPTED_GENRES)
    sql = f"""
        SELECT t.id, t.title, COALESCE(sc.n, 0)
        FROM titles t
        LEFT JOIN (
            SELECT title_id, COUNT(DISTINCT season_number) n
            FROM seasons GROUP BY title_id
        ) sc ON sc.title_id = t.id
        WHERE t.type IN ('tv','anime')
          AND sc.n IS NOT NULL AND sc.n > 0
          AND t.id NOT IN (
              SELECT tg.title_id FROM title_genres tg
              JOIN genres g ON g.id = tg.genre_id
              WHERE g.slug IN ({genre_excl})
          )
    """
    candidates = conn.execute(sql, NON_SCRIPTED_GENRES).fetchall()
    scripted_rows = [r for r in candidates if not is_talk_show(r[1])]
    talk_rows = [r for r in candidates if is_talk_show(r[1])]

    conn.executemany(
        "INSERT OR REPLACE INTO title_classification (title_id, is_scripted, seasons, reason) VALUES (?, 1, ?, 'has-seasons')",
        [(r[0], r[2]) for r in scripted_rows],
    )
    # Give the talk shows their own reason so the audit says why they were
    # dropped rather than mislabelling them as a genre exclusion.
    conn.executemany(
        "INSERT OR REPLACE INTO title_classification (title_id, is_scripted, seasons, reason) VALUES (?, 0, ?, 'talk-variety')",
        [(r[0], r[2]) for r in talk_rows],
    )
    print(f"  talk/variety franchises excluded from scripted: {len(talk_rows):,}")
    scripted = conn.execute("SELECT COUNT(*) FROM title_classification WHERE is_scripted=1").fetchone()[0]

    # Everything else episodic is explicitly non-scripted, so the UI can say so
    # rather than silently dropping rows.
    conn.execute(
        f"""
        INSERT OR IGNORE INTO title_classification (title_id, is_scripted, seasons, reason)
        SELECT t.id,
               0,
               COALESCE(sc.n, 0),
               CASE
                   WHEN sc.n IS NULL OR sc.n = 0 THEN 'no-seasons'
                   ELSE 'non-scripted-genre'
               END
        FROM titles t
        LEFT JOIN (
            SELECT title_id, COUNT(DISTINCT season_number) n
            FROM seasons GROUP BY title_id
        ) sc ON sc.title_id = t.id
        WHERE t.type IN ('tv','anime')
        """,
    )
    conn.commit()

    rows = conn.execute(
        "SELECT is_scripted, reason, COUNT(*) FROM title_classification GROUP BY is_scripted, reason"
    ).fetchall()
    total = conn.execute("SELECT COUNT(*) FROM title_classification").fetchone()[0]

    print(f"classified {total:,} episodic titles in {time.time()-started:.0f}s")
    for is_scripted, reason, n in sorted(rows, key=lambda r: -r[2]):
        print(f"  scripted={is_scripted}  {reason:<22} {n:,}")
    print(f"\nscripted series kept: {scripted:,}")
    conn.close()


if __name__ == "__main__":
    main()
