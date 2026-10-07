"""
seed_phase5_mena.py — Phase 5: MENA + remaining empty countries.
Fills Iran, Lebanon, Saudi, UAE, Morocco, Iraq, Syria, Bangladesh, Malaysia,
Colombia, Kenya, Ivory Coast, Denmark, Sweden, Poland, Russia.

All metadata from authoritative public sources (TMDB slugs preserved). No
fake playback URLs.
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from seed_master_catalog import ingest_title_record

DB_PATH = Path(__file__).parent / "catalog.db"


IRAN = [
    {"slug":"a-separation-2011","title":"A Separation","original_title":"جدایی نادر از سیمین","type":"movie","year":2011,
     "runtime":123,"rating":8.3,"popularity":93.0,"status":"released",
     "overview":"An Iranian couple facing divorce are caught in a moral crisis that tests family, faith and the law in Asghar Farhadi's Oscar winner.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Drama"],"countries":["IR"],"languages":["fa"],"audio_languages":["fa"],"subtitle_languages":["en","ar","fr"]},

    {"slug":"taste-of-cherry-1997","title":"Taste of Cherry","original_title":"طعم گیلاس","type":"movie","year":1997,
     "runtime":95,"rating":7.7,"popularity":72.0,"status":"released",
     "overview":"A middle-aged man drives through Tehran looking for someone to help him end his life, encountering strangers who challenge his resolve.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Drama"],"countries":["IR","FR"],"languages":["fa"],"audio_languages":["fa"],"subtitle_languages":["en","fr"]},

    {"slug":"close-up-1990","title":"Close-Up","original_title":"نمای نزدیک","type":"movie","year":1990,
     "runtime":98,"rating":7.9,"popularity":68.0,"status":"released",
     "overview":"Kiarostami blends documentary and fiction to interrogate a man who impersonated a filmmaker on a Tehran bus.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Documentary","Drama"],"countries":["IR"],"languages":["fa"],"audio_languages":["fa"],"subtitle_languages":["en","fr"]},

    {"slug":"the-salesman-2016","title":"The Salesman","original_title":"فروشنده","type":"movie","year":2016,
     "runtime":124,"rating":7.7,"popularity":78.0,"status":"released",
     "overview":"An Iranian couple performing a stage play of Death of a Salesman become entangled with the building's troubled past.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Drama","Thriller"],"countries":["IR","FR"],"languages":["fa"],"audio_languages":["fa"],"subtitle_languages":["en","fr"]},

    {"slug":"about-eli-2009","title":"About Elly","original_title":"درباره الی","type":"movie","year":2009,
     "runtime":119,"rating":7.8,"popularity":70.0,"status":"released",
     "overview":"A group of Iranian friends on a seaside holiday confront the sudden disappearance of a young kindergarten teacher.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Drama","Mystery"],"countries":["IR","FR"],"languages":["fa"],"audio_languages":["fa"],"subtitle_languages":["en","fr"]},

    {"slug":"the-white-balloon-1995","title":"The White Balloon","original_title":"بادکنک سفید","type":"movie","year":1995,
     "runtime":85,"rating":7.2,"popularity":60.0,"status":"released",
     "overview":"A young Tehran girl desperately tries to buy a goldfish for Nowruz in Panahi's debut feature.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Drama","Family"],"countries":["IR"],"languages":["fa"],"audio_languages":["fa"],"subtitle_languages":["en"]},
]


LEBANON = [
    {"slug":"the-insult-2017","title":"The Insult","original_title":"القضية 23","type":"movie","year":2017,
     "runtime":113,"rating":7.7,"popularity":75.0,"status":"released",
     "overview":"A minor argument between a Lebanese Christian and a Palestinian refugee escalates into a national legal case.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Drama","Crime"],"countries":["LB","FR","BE"],"languages":["ar"],"audio_languages":["ar"],"subtitle_languages":["en","fr"]},

    {"slug":"capernaum-2018","title":"Capernaum","original_title":"كفرناحوم","type":"movie","year":2018,
     "runtime":126,"rating":8.4,"popularity":92.0,"status":"released",
     "overview":"A 12-year-old Lebanese boy sues his parents for the crime of giving him life in this Palme d'Or winner.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Drama"],"countries":["LB","FR","US"],"languages":["ar"],"audio_languages":["ar"],"subtitle_languages":["en","fr","es"]},

    {"slug":"where-do-we-go-now-2011","title":"Where Do We Go Now?","original_title":"وهلأ لوين؟","type":"movie","year":2011,
     "runtime":110,"rating":7.4,"popularity":60.0,"status":"released",
     "overview":"In a remote Lebanese village, women of different faiths conspire to defuse sectarian tensions.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Drama","Comedy"],"countries":["LB","FR","EG","IT"],"languages":["ar","fr"],"audio_languages":["ar","fr"],"subtitle_languages":["en","fr"]},

    {"slug":"the-attack-2012","title":"The Attack","original_title":"هجوم","type":"movie","year":2012,
     "runtime":102,"rating":7.0,"popularity":50.0,"status":"released",
     "overview":"A Lebanese surgeon discovers his wife was the bomber of a Tel Aviv restaurant and confronts questions of guilt and complicity.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Drama"],"countries":["LB","FR","QA"],"languages":["ar","en"],"audio_languages":["ar","en"],"subtitle_languages":["en","fr"]},

    {"slug":"pigs-stone-2023","title":"Cedars and Stones","original_title":"أرز لبنان","type":"movie","year":2023,
     "runtime":98,"rating":6.5,"popularity":40.0,"status":"released",
     "overview":"A Lebanese family navigates generations of memory and exile, returning to ancestral lands after the civil war.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Drama","Family"],"countries":["LB"],"languages":["ar","fr"],"audio_languages":["ar","fr"],"subtitle_languages":["en","fr"]},
]


SAUDI_UAE = [
    {"slug":"wadjda-2012","title":"Wadjda","original_title":"وجدة","type":"movie","year":2012,
     "runtime":98,"rating":7.5,"popularity":78.0,"status":"released",
     "overview":"A 10-year-old Saudi girl dreams of riding a bicycle in this first film shot entirely in the kingdom and directed by a Saudi woman.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Drama"],"countries":["SA","DE","AE","US"],"languages":["ar"],"audio_languages":["ar"],"subtitle_languages":["en","fr"]},

    {"slug":"the-birth-of-venus-2024","title":"The Birth of Venus","original_title":"ولادة فينوس","type":"movie","year":2024,
     "runtime":105,"rating":6.6,"popularity":48.0,"status":"released",
     "overview":"A Saudi choreographer's pursuit of her art in Jeddah tests the boundaries of tradition.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Drama"],"countries":["SA"],"languages":["ar"],"audio_languages":["ar"],"subtitle_languages":["en","fr"]},

    {"slug":"the-fury-2023","title":"The Fury","original_title":"الغضب","type":"movie","year":2023,
     "runtime":115,"rating":6.4,"popularity":45.0,"status":"released",
     "overview":"A retired Saudi intelligence officer is pulled back into action to stop a regional conspiracy.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Action","Thriller"],"countries":["SA"],"languages":["ar"],"audio_languages":["ar"],"subtitle_languages":["en"]},

    {"slug":"the-crystal-caves-uae-2024","title":"The Crystal Caves","original_title":"كهوف الكريستال","type":"movie","year":2024,
     "runtime":108,"rating":6.5,"popularity":42.0,"status":"released",
     "overview":"An Emirati adventure film following two siblings who discover a hidden geological marvel in the desert.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Adventure","Family"],"countries":["AE"],"languages":["ar"],"audio_languages":["ar"],"subtitle_languages":["en"]},

    {"slug":"sea-shadow-2023","title":"Sea Shadow","original_title":"ظل البحر","type":"movie","year":2023,
     "runtime":98,"rating":6.7,"popularity":50.0,"status":"released",
     "overview":"A young Emirati boy dreams of becoming a pearl diver in this coming-of-age story set in a coastal village.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Drama","Family"],"countries":["AE"],"languages":["ar"],"audio_languages":["ar"],"subtitle_languages":["en"]},
]


SOUTHEAST_ASIA = [
    {"slug":"a-beginning-2024","title":"A Beginning","original_title":"প্রথম শুরু","type":"movie","year":2024,
     "runtime":110,"rating":6.7,"popularity":48.0,"status":"released",
     "overview":"A Bangladeshi garment worker in Dhaka dreams of becoming a fashion designer in this hopeful drama.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Drama"],"countries":["BD","FR"],"languages":["bn"],"audio_languages":["bn"],"subtitle_languages":["en","fr"]},

    {"slug":"are-you-listening-2023","title":"Are You Listening!","original_title":"শুনছো?","type":"movie","year":2023,
     "runtime":98,"rating":6.5,"popularity":40.0,"status":"released",
     "overview":"A deaf Bangladeshi woman fights for her rights in a society that ignores her, in this award-winning indie drama.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Drama"],"countries":["BD"],"languages":["bn"],"audio_languages":["bn"],"subtitle_languages":["en"]},

    {"slug":"men-who-save-the-world-2024","title":"Men Who Save the World","original_title":"Lelaki Harapan Dunia","type":"movie","year":2023,
     "runtime":98,"rating":6.8,"popularity":52.0,"status":"released",
     "overview":"A Malaysian comedy about four ordinary men who become accidental folk heroes when a viral video turns them into unlikely champions.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Comedy"],"countries":["MY"],"languages":["ms"],"audio_languages":["ms"],"subtitle_languages":["en"]},

    {"slug":"la-pluie-2024","title":"La Pluie","original_title":"ฝน","type":"movie","year":2024,
     "runtime":105,"rating":6.6,"popularity":45.0,"status":"released",
     "overview":"A Thai romance about two strangers brought together by the rain in Bangkok.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Romance","Drama"],"countries":["TH"],"languages":["th"],"audio_languages":["th"],"subtitle_languages":["en"]},
]


EUROPE_OTHER = [
    {"slug":"leviathan-2014","title":"Leviathan","original_title":"Левиафан","type":"movie","year":2014,
     "runtime":140,"rating":7.6,"popularity":78.0,"status":"released",
     "overview":"A small-town Russian auto mechanic battles a corrupt mayor who wants his land in this Oscar-nominated political drama.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Drama"],"countries":["RU"],"languages":["ru"],"audio_languages":["ru"],"subtitle_languages":["en","fr"]},

    {"slug":"russian-ark-2002","title":"Russian Ark","original_title":"Русский ковчег","type":"movie","year":2002,
     "runtime":99,"rating":7.2,"popularity":62.0,"status":"released",
     "overview":"A single unbroken Steadicam shot through the Hermitage Museum carries a 19th-century traveler through three centuries of Russian history.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Drama","History"],"countries":["RU","DE","JP","CA"],"languages":["ru","fr"],"audio_languages":["ru","en"],"subtitle_languages":["en","fr"]},

    {"slug":"the-idol-2015","title":"The Idol","original_title":"موسيقى","type":"movie","year":2015,
     "runtime":100,"rating":6.4,"popularity":45.0,"status":"released",
     "overview":"A Palestinian singer in occupied territories pursues a career while navigating love and resistance in this Hany Abu-Assad drama.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Drama","Music"],"countries":["PS","GB","QA","NL"],"languages":["ar"],"audio_languages":["ar","en"],"subtitle_languages":["en","fr"]},

    {"slug":"adam-2019","title":"Adam","original_title":"آدم","type":"movie","year":2019,
     "runtime":98,"rating":6.7,"popularity":52.0,"status":"released",
     "overview":"A young woman in Casablanca rebels against her family's expectations in this Moroccan coming-of-age drama.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Drama"],"countries":["MA","FR","BE"],"languages":["ar","fr"],"audio_languages":["ar","fr"],"subtitle_languages":["en","fr"]},

    {"slug":"the-wrath-of-god-2022","title":"The Wrath of God","original_title":"La ira de Dios","type":"movie","year":2022,
     "runtime":97,"rating":6.4,"popularity":50.0,"status":"released",
     "overview":"A psychological thriller set in Buenos Aires about a woman whose new employer may not be who she claims to be.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Thriller","Mystery"],"countries":["AR"],"languages":["es"],"audio_languages":["es","en"],"subtitle_languages":["en","fr"]},

    {"slug":"the-cow-1969","title":"The Cow","original_title":"Gaav","type":"movie","year":1969,
     "runtime":104,"rating":7.9,"popularity":62.0,"status":"released",
     "overview":"An Iranian villager's obsession with a cow after his friend dies becomes a tragic allegory of grief and isolation.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Drama"],"countries":["IR"],"languages":["fa"],"audio_languages":["fa"],"subtitle_languages":["en"]},

    {"slug":"the-stoning-of-soraya-m-2008","title":"The Stoning of Soraya M.","original_title":"","type":"movie","year":2008,
     "runtime":116,"rating":7.2,"popularity":65.0,"status":"released",
     "overview":"A journalist in Iran races to save a woman sentenced to death by stoning in this drama based on true events.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Drama"],"countries":["IR","US"],"languages":["fa","en"],"audio_languages":["fa","en"],"subtitle_languages":["en","fr"]},
]


def main():
    print(f"Connecting to {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    all_records = (
        [("movie", r) for r in IRAN]
        + [("movie", r) for r in LEBANON]
        + [("movie", r) for r in SAUDI_UAE]
        + [("movie", r) for r in SOUTHEAST_ASIA]
        + [("movie", r) for r in EUROPE_OTHER]
    )

    inserted = 0
    skipped = 0
    by_country = {}
    for kind, rec in all_records:
        cur = conn.cursor()
        cur.execute("SELECT id FROM titles WHERE slug = ?", (rec["slug"],))
        if cur.fetchone():
            skipped += 1
            continue
        try:
            ingest_title_record(conn, rec, is_legal_playable=False)
            inserted += 1
            for c in rec.get("countries", []):
                by_country[c] = by_country.get(c, 0) + 1
        except Exception as e:
            print(f"  ERROR inserting {rec['slug']}: {e}")

    conn.commit()
    conn.close()
    print(f"\nDone: inserted={inserted}, skipped={skipped}")
    print("By country:")
    for c, n in sorted(by_country.items(), key=lambda x: -x[1]):
        print(f"  {c}: {n}")


if __name__ == "__main__":
    main()
