"""
apply_omni_images.py — attach artwork from the DuckKota/omni-images GitLab repo
to the catalogue's taxonomy tables.

The repo is a plain set of images on a public GitLab raw path. We store the
remote URL rather than vendoring 3 MB PNGs per genre into the repo, so the
catalogue stays small and the artwork can be changed upstream without a reindex.

    https://gitlab.com/DuckKota/omni-images/-/raw/main/<folder>/<file>

Mapping
    genres/<name>.png                -> genres.image_url        (column added)
    decades/<year>.jpg                -> decades.poster_url
    collections/<slug>.png            -> collections.poster
    studios/<slug>.png                -> studios.logo_url
    animation_studios/<slug>.png      -> animation_studios.logo_url
    actors/<slug>.jpg                 -> actors.photo_url
    directors/<slug>.jpg              -> directors.photo_url
    streaming_services/<slug>.jpg     -> streaming_providers.logo_url

Existing values are only replaced when empty, so real TMDB artwork is never
clobbered by a generic genre icon.

Run:
    python apply_omni_images.py            # apply
    python apply_omni_images.py --dry-run  # show the mapping, touch nothing
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).parent
DB = HERE / "catalog.db"
BASE = "https://gitlab.com/DuckKota/omni-images/-/raw/main"

# (folder, table, column, [file stems])
SPEC = [
    ("genres", "genres", "image_url", [
        "trending", "action", "adventure", "animation", "comedy", "crime",
        "documentary", "drama", "fantasy", "historical", "horror", "musical",
        "mystery", "romance", "sci-fi", "thriller", "war",
    ]),
    ("decades", "decades", "poster_url", ["1980", "1990", "2000", "2010", "2020"]),
    ("collections", "collections", "poster", [
        "avatar", "back_to_the_future", "dune", "fast_and_furious", "harry_potter",
        "hunger_games", "indiana_jones", "james_bond", "john_wick", "jurassic_park",
        "lord_of_the_rings", "marvel", "matrix", "mission_impossible", "monsterverse",
        "pirates_of_the_caribbean", "rambo", "rocky", "star_trek", "star_wars",
        "transformers", "x_men",
    ]),
    ("studios", "studios", "logo_url", [
        "dc_studios", "dreamworks_pictures", "lionsgate", "marvel_studios",
        "universal_pictures", "walt_disney_pictures", "warner_bros_pictures",
    ]),
    ("animation_studios", "animation_studios", "logo_url", [
        "blue_sky_animation", "dreamworks_animation", "illumination", "pixar",
        "sony_pictures_animation", "walt_disney_animation", "warner_bros_animation",
    ]),
    ("actors", "actors", "photo_url", [
        "adam_sandler", "arnold_schwarzenegger", "christian_bale", "clint_eastwood",
        "denzel_washington", "dwayne_johnson", "harrison_ford", "jackie_chan",
        "jason_statham", "matt_damon", "morgan_freeman", "nicolas_cage",
        "robert_downey_jr", "robin_williams", "ryan_reynolds", "samuel_l_jackson",
        "sylvester_stallone", "tom_cruise",
    ]),
    ("directors", "directors", "photo_url", [
        "alfred_hitchcock", "brian_de_palma", "christopher_nolan", "david_fincher",
        "denis_villeneuve", "john_carpenter", "martin_scorsese",
        "paul_thomas_anderson", "stanley_kubrick", "steven_speilberg",
    ]),
    ("streaming_services", "streaming_providers", "logo_url", [
        "apple_tv", "discovery_plus", "disney_plus", "max", "hulu", "netflix",
        "paramount_plus", "peacock", "prime_video",
    ]),
]

# genres live under the /genres/ folder but a couple of slugs differ from the
# file stem; the rest match directly.
GENRE_SLUG_ALIASES = {
    "trending": "trending",
    "sci-fi": "sci-fi",
}


# The catalogue's own slugs differ from the image repo's file stems in a few
# places. These map the file stem onto the real row.
SLUG_OVERRIDES = {
    ("genres", "sci-fi"): "science-fiction",
    ("genres", "music"): "musical",
    ("genres", "history"): "historical",
    ("collections", "hunger_games"): "the-hunger-games",
    ("collections", "matrix"): "the-matrix",
    ("collections", "rocky"): "rocky-creed",
    ("collections", "star_wars"): "star-wars",
}


def slugify(s: str) -> str:
    out = []
    for ch in (s or "").lower().strip():
        out.append(ch if ch.isalnum() else "-")
    slug = "".join(out)
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    conn = sqlite3.connect(str(DB), timeout=60)
    cur = conn.cursor()

    # genres has no image column in the existing schema.
    cols = {r[1] for r in cur.execute("PRAGMA table_info(genres)")}
    if "image_url" not in cols:
        if not args.dry_run:
            cur.execute("ALTER TABLE genres ADD COLUMN image_url TEXT")
        print("added genres.image_url")

    total_set = 0
    for folder, table, column, stems in SPEC:
        ext = "jpg" if folder in ("decades", "actors", "directors", "streaming_services") else "png"

        # Decades are keyed by the decade year in the filename, not a slug.
        if table == "decades":
            lookup = {
                "1980": "1980", "1990": "1990", "2000": "2000",
                "2010": "2010", "2020": "2020",
            }
        else:
            lookup = {}

        matched = unmatched = 0
        for stem in stems:
            url = f"{BASE}/{folder}/{stem}.{ext}"

            if table == "decades":
                rows = cur.execute(
                    f"SELECT id FROM decades WHERE label = ? OR slug = ?",
                    (f"{stem}s", stem),
                ).fetchall()
            else:
                target = SLUG_OVERRIDES.get((table, stem), stem)
                rows = cur.execute(
                    f"SELECT id FROM {table} WHERE slug = ? OR slug = ?",
                    (target, slugify(target)),
                ).fetchall()

            if not rows:
                unmatched += 1
                if args.dry_run:
                    print(f"  [miss] {table:<20} {stem}")
                continue

            matched += 1
            if args.dry_run:
                print(f"  [ ok ] {table:<20} {stem:<26} -> {len(rows)} row(s)")
            else:
                # Only fill blanks — never overwrite real TMDB artwork.
                cur.execute(
                    f"UPDATE {table} SET {column} = ? WHERE id = ? AND "
                    f"({column} IS NULL OR {column} = '')",
                    (url, rows[0][0]),
                )
                total_set += 1

        print(f"{table:<20} matched {matched}, unmatched {unmatched}")

    if args.dry_run:
        print("\ndry run — nothing written")
    else:
        conn.commit()
        print(f"\nwrote {total_set} image URLs")
        for table, _f, column, _s in [(s[1], s[0], s[2], s[3]) for s in SPEC]:
            try:
                n = conn.execute(
                    f"SELECT COUNT(*) FROM {table} WHERE {column} IS NOT NULL AND {column} != ''"
                ).fetchone()[0]
                print(f"  {table:<20} {n} rows with artwork")
            except sqlite3.Error as e:
                print(f"  {table:<20} ERR {e}")

    conn.close()


if __name__ == "__main__":
    main()
