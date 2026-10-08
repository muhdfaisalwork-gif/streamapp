"""
seed_phase3.py — Phase 3 expansion: more anime, TV, short dramas.
Pure metadata seed (no fake playback URLs). Uses ingest_title_record
from seed_master_catalog for consistent schema ingestion.
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from seed_master_catalog import ingest_title_record

DB_PATH = Path(__file__).parent / "catalog.db"


# =====================================================================
# Phase 3A — Anime expansion (canonical shonen/seinen + films)
# =====================================================================
EXTRA_ANIME = [
    # Recent hits
    {"slug":"chainsaw-man-2022","title":"Chainsaw Man","original_title":"チェンソーマン","type":"anime","year":2022,
     "runtime":24,"rating":8.6,"popularity":92.1,"status":"ended",
     "overview":"Denji is a young boy who inherits a devil's power and joins the Public Safety Devil Hunters to pay off his father's debt and live a normal life.",
     "poster":"https://image.tmdb.org/t/p/w500/npdB6eFzizki0WaZ1UV1aVExHOP.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/npdB6eFzizki0WaZ1UV1aVExHOP.jpg",
     "genres":["Animation","Action","Fantasy","Horror"],
     "countries":["JP"],"languages":["ja","en"],"audio_languages":["ja","en"],"subtitle_languages":["en","es","fr","de"],
     "collections":["trending-today","popular-series"]},

    {"slug":"black-clover-2017","title":"Black Clover","original_title":"ブラッククローバー","type":"anime","year":2017,
     "runtime":24,"rating":8.2,"popularity":85.5,"status":"ended",
     "overview":"In a world where everyone has magic, Asta is born with none. He vows to become the Wizard King and join the Black Bulls.",
     "poster":"https://image.tmdb.org/t/p/w500/kaAQKeXNUtRPxPV3vGGGJxh4kFc.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/kaAQKeXNUtRPxPV3vGGGJxh4kFc.jpg",
     "genres":["Animation","Action","Adventure","Fantasy"],
     "countries":["JP"],"languages":["ja","en"],"audio_languages":["ja","en"],"subtitle_languages":["en","es","pt"],
     "collections":["popular-series"]},

    {"slug":"hunter-x-hunter-2011","title":"Hunter x Hunter (2011)","original_title":"ハンター×ハンター","type":"anime","year":2011,
     "runtime":24,"rating":9.0,"popularity":91.2,"status":"ended",
     "overview":"Gon Freecss leaves his home to become a Hunter like his father and find his hidden potential along the way.",
     "poster":"https://image.tmdb.org/t/p/w500/uhXutWN3ZGh7wzW1QcS9ItPjlpw.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/uhXutWN3ZGh7wzW1QcS9ItPjlpw.jpg",
     "genres":["Animation","Action","Adventure","Fantasy"],
     "countries":["JP"],"languages":["ja","en"],"audio_languages":["ja","en"],"subtitle_languages":["en","ar"],
     "collections":["popular-series","top-rated"]},

    {"slug":"my-hero-academia-2016","title":"My Hero Academia","original_title":"僕のヒーローアカデミア","type":"anime","year":2016,
     "runtime":24,"rating":8.1,"popularity":88.3,"status":"ended",
     "overview":"Izuku Midoriya, a quirkless boy, inherits the power of the world's greatest hero and enrolls in UA High to become the next symbol of peace.",
     "poster":"https://image.tmdb.org/t/p/w500/phuY2rcXy1bs1D8T3lWwY7RtMmi.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/phuY2rcXy1bs1D8T3lWwY7RtMmi.jpg",
     "genres":["Animation","Action","Adventure"],
     "countries":["JP"],"languages":["ja","en"],"audio_languages":["ja","en"],"subtitle_languages":["en","es","fr"],
     "collections":["popular-series"]},

    {"slug":"steins-gate-2011","title":"Steins;Gate","original_title":"STEINS;GATE","type":"anime","year":2011,
     "runtime":24,"rating":9.1,"popularity":89.7,"status":"ended",
     "overview":"A self-proclaimed mad scientist and his friends accidentally discover a way to send text messages to the past, with devastating consequences.",
     "poster":"https://image.tmdb.org/t/p/w500/6SyyDGiZzb9fYpL7b3xY9cIuL4b.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/6SyyDGiZzb9fYpL7b3xY9cIuL4b.jpg",
     "genres":["Animation","Drama","Science Fiction","Thriller"],
     "countries":["JP"],"languages":["ja","en"],"audio_languages":["ja","en"],"subtitle_languages":["en","ar","fr"],
     "collections":["top-rated"]},

    {"slug":"mob-psycho-100-2016","title":"Mob Psycho 100","original_title":"モブサイコ100","type":"anime","year":2016,
     "runtime":24,"rating":8.9,"popularity":87.0,"status":"ended",
     "overview":"A powerful psychic middle schooler tries to live a normal life while suppressing his emotions that trigger his powers.",
     "poster":"https://image.tmdb.org/t/p/w500/v1BVH7IzG3tvK6pTSv8HyXPqfHL.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/v1BVH7IzG3tvK6pTSv8HyXPqfHL.jpg",
     "genres":["Animation","Action","Comedy"],
     "countries":["JP"],"languages":["ja","en"],"audio_languages":["ja","en"],"subtitle_languages":["en"],
     "collections":["popular-series"]},

    {"slug":"vinland-saga-2019","title":"Vinland Saga","original_title":"ヴィンランド・サガ","type":"anime","year":2019,
     "runtime":24,"rating":8.8,"popularity":85.9,"status":"ended",
     "overview":"A young Viking boy seeks revenge for his father's murder and gets drawn into the brutal politics of 11th-century England.",
     "poster":"https://image.tmdb.org/t/p/w500/jUHn1fB7oFwYZfGyVPWo6PvnnvL.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/jUHn1fB7oFwYZfGyVPWo6PvnnvL.jpg",
     "genres":["Animation","Action","Adventure","Drama"],
     "countries":["JP"],"languages":["ja","en"],"audio_languages":["ja","en"],"subtitle_languages":["en"],
     "collections":["top-rated"]},

    {"slug":"re-zero-2016","title":"Re:Zero − Starting Life in Another World","original_title":"Re:ゼロから始める異世界生活","type":"anime","year":2016,
     "runtime":24,"rating":8.5,"popularity":86.4,"status":"ongoing",
     "overview":"Subaru is transported to a fantasy world and discovers he has the ability to return from death by a point in time.",
     "poster":"https://image.tmdb.org/t/p/w500/jBmmt5L3yXCc9I2cG9VbB3IbMJi.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/jBmmt5L3yXCc9I2cG9VbB3IbMJi.jpg",
     "genres":["Animation","Drama","Fantasy","Thriller"],
     "countries":["JP"],"languages":["ja","en"],"audio_languages":["ja","en"],"subtitle_languages":["en","ar"],
     "collections":["popular-series"]},

    {"slug":"dr-stone-2019","title":"Dr. Stone","original_title":"Dr.STONE","type":"anime","year":2019,
     "runtime":24,"rating":8.3,"popularity":83.7,"status":"ended",
     "overview":"After humanity is mysteriously petrified for 3,700 years, a genius science-loving boy wakes up and rebuilds civilization with science.",
     "poster":"https://image.tmdb.org/t/p/watuqRC7a5ZPI3BjwoZNLzWtlH4.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/watuqRC7a5ZPI3BjwoZNLzWtlH4.jpg",
     "genres":["Animation","Adventure","Science Fiction"],
     "countries":["JP"],"languages":["ja","en"],"audio_languages":["ja","en"],"subtitle_languages":["en","es"],
     "collections":["popular-series"]},

    {"slug":"made-in-abyss-2017","title":"Made in Abyss","original_title":"メイドインアビス","type":"anime","year":2017,
     "runtime":24,"rating":8.7,"popularity":82.1,"status":"ongoing",
     "overview":"A girl and her robot companion descend into a mysterious abyss in search of her mother, facing escalating dangers at each layer.",
     "poster":"https://image.tmdb.org/t/p/w500/A8ZxZQFqPq2eTzdwsnEvK0yZNvm.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/A8ZxZQFqPq2eTzdwsnEvK0yZNvm.jpg",
     "genres":["Animation","Adventure","Drama","Mystery"],
     "countries":["JP"],"languages":["ja","en"],"audio_languages":["ja","en"],"subtitle_languages":["en"],
     "collections":["popular-series","top-rated"]},

    {"slug":"kaguya-sama-2019","title":"Kaguya-sama: Love is War","original_title":"かぐや様は告らせたい","type":"anime","year":2019,
     "runtime":24,"rating":8.7,"popularity":84.5,"status":"ended",
     "overview":"Two student council leaders pridefully try to make the other confess love first in this romantic comedy of psychological warfare.",
     "poster":"https://image.tmdb.org/t/p/w500/3XujkB5p8fteT3JVBGhfPtYUgZ7.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3XujkB5p8fteT3JVBGhfPtYUgZ7.jpg",
     "genres":["Animation","Comedy","Romance"],
     "countries":["JP"],"languages":["ja","en"],"audio_languages":["ja","en"],"subtitle_languages":["en","es"],
     "collections":["popular-series"]},

    {"slug":"kaguya-sama-movie-2022","title":"Kaguya-sama: Love is War - The First Kiss That Never Ends","original_title":"かぐや様は告らせたい","type":"anime","year":2022,
     "runtime":110,"rating":8.6,"popularity":80.0,"status":"released",
     "overview":"The climactic continuation of the beloved rom-com where Miyuki and Kaguya finally navigate their first kiss and what comes next.",
     "poster":"https://image.tmdb.org/t/p/w500/7gVMi4tZFlr7yL3p7o3oWkGApQE.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/7gVMi4tZFlr7yL3p7o3oWkGApQE.jpg",
     "genres":["Animation","Comedy","Romance"],
     "countries":["JP"],"languages":["ja","en"],"audio_languages":["ja","en"],"subtitle_languages":["en","es"],
     "collections":["popular-series"]},

    # Anime films (more)
    {"slug":"akira-1988-anime","title":"Akira (Anime Film)","original_title":"AKIRA","type":"anime","year":1988,
     "runtime":124,"rating":8.0,"popularity":88.4,"status":"released",
     "overview":"A biker leader tries to save his telekinetically powered friend from a government experiment in Neo-Tokyo.",
     "poster":"https://image.tmdb.org/t/p/w500/3TOaPhdkg4RrCF8kofP3lpfXyLp.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3TOaPhdkg4RrCF8kofP3lpfXyLp.jpg",
     "genres":["Animation","Action","Science Fiction"],
     "countries":["JP"],"languages":["ja","en"],"audio_languages":["ja","en"],"subtitle_languages":["en","es","fr"],
     "collections":["top-rated"]},

    {"slug":"ghost-in-the-shell-1995","title":"Ghost in the Shell","original_title":"攻殻機動隊","type":"anime","year":1995,
     "runtime":83,"rating":8.0,"popularity":80.5,"status":"released",
     "overview":"A cyborg cop and her partner hunt a mysterious hacker known as the Puppet Master in this influential cyberpunk anime film.",
     "poster":"https://image.tmdb.org/t/p/w500/9p7nkHrRfIYR9oJymOPPiqFcgnP.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/9p7nkHrRfIYR9oJymOPPiqFcgnP.jpg",
     "genres":["Animation","Action","Science Fiction"],
     "countries":["JP"],"languages":["ja","en"],"audio_languages":["ja","en"],"subtitle_languages":["en"],
     "collections":["top-rated"]},

    {"slug":"your-name-2016-anime","title":"Your Name. (Anime Film)","original_title":"君の名は。","type":"anime","year":2016,
     "runtime":106,"rating":8.4,"popularity":93.5,"status":"released",
     "overview":"Two strangers find themselves linked in a bizarre way: when the boy and girl fall asleep, they swap bodies.",
     "poster":"https://image.tmdb.org/t/p/w500/q719jXXEzOoYaps6babgKnONONX.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/q719jXXEzOoYaps6babgKnONONX.jpg",
     "genres":["Animation","Romance","Drama"],
     "countries":["JP"],"languages":["ja","en"],"audio_languages":["ja","en"],"subtitle_languages":["en"],
     "collections":["popular-series","top-rated"]},

    # Hindi-dubbed anime
    {"slug":"dragon-ball-z-1989","title":"Dragon Ball Z","original_title":"ドラゴンボールZ","type":"anime","year":1989,
     "runtime":24,"rating":8.7,"popularity":89.3,"status":"ended",
     "overview":"Goku and friends defend Earth against alien villains, gods, and time-traveling threats in this iconic shonen series.",
     "poster":"https://image.tmdb.org/t/p/w500/6VKOfL05u1e9nrX7nzCAworROeR.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/6VKOfL05u1e9nrX7nzCAworROeR.jpg",
     "genres":["Animation","Action","Adventure"],
     "countries":["JP"],"languages":["ja","en","hi"],"audio_languages":["ja","en","hi"],"subtitle_languages":["en","hi"],
     "collections":["popular-series","trending-today"]},

    {"slug":"naruto-2002","title":"Naruto","original_title":"NARUTO -ナルト-","type":"anime","year":2002,
     "runtime":24,"rating":8.4,"popularity":92.8,"status":"ended",
     "overview":"An orphaned boy with a sealed demon fox inside him dreams of becoming the village leader, the Hokage.",
     "poster":"https://image.tmdb.org/t/p/w500/vauCEnR7CglBDv7nKQCqCJZqErx.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/vauCEnR7CglBDv7nKQCqCJZqErx.jpg",
     "genres":["Animation","Action","Adventure"],
     "countries":["JP"],"languages":["ja","en","hi"],"audio_languages":["ja","en","hi"],"subtitle_languages":["en","hi"],
     "collections":["popular-series","trending-today"]},

    {"slug":"bleach-2004","title":"Bleach","original_title":"ブリーチ","type":"anime","year":2004,
     "runtime":24,"rating":8.2,"popularity":88.1,"status":"ongoing",
     "overview":"A teenager with the ability to see ghosts becomes a Soul Reaper and defends the living world from evil spirits.",
     "poster":"https://image.tmdb.org/t/p/w500/2EewmxUe7T8K8VYeadetqV1zbbL.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/2EewmxUe7T8K8VYeadetqV1zbbL.jpg",
     "genres":["Animation","Action","Adventure"],
     "countries":["JP"],"languages":["ja","en","hi"],"audio_languages":["ja","en","hi"],"subtitle_languages":["en","hi"],
     "collections":["popular-series"]},

    # Completed anime
    {"slug":"cowboy-bebop-1998","title":"Cowboy Bebop","original_title":"カウボーイビバップ","type":"anime","year":1998,
     "runtime":24,"rating":8.9,"popularity":89.7,"status":"ended",
     "overview":"A ragtag crew of bounty hunters chases criminals across the solar system in 2071 while dealing with their troubled pasts.",
     "poster":"https://image.tmdb.org/t/p/w500/3bz0XkcMRas4F8j0pYj1gImsdQP.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3bz0XkcMRas4F8j0pYj1gImsdQP.jpg",
     "genres":["Animation","Action","Science Fiction"],
     "countries":["JP"],"languages":["ja","en"],"audio_languages":["ja","en"],"subtitle_languages":["en"],
     "collections":["popular-series","top-rated"]},

    {"slug":"one-punch-man-2015","title":"One-Punch Man","original_title":"ワンパンマン","type":"anime","year":2015,
     "runtime":24,"rating":8.7,"popularity":90.1,"status":"ongoing",
     "overview":"A hero who can defeat any opponent with a single punch grows bored and searches for a worthy challenge.",
     "poster":"https://image.tmdb.org/t/p/w500/iE63sxvW5GJ0RdvLg5aOCei7VOS.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/iE63sxvW5GJ0RdvLg5aOCei7VOS.jpg",
     "genres":["Animation","Action","Comedy"],
     "countries":["JP"],"languages":["ja","en"],"audio_languages":["ja","en"],"subtitle_languages":["en","ar"],
     "collections":["popular-series"]},

    {"slug":"tokyo-ghoul-2014","title":"Tokyo Ghoul","original_title":"東京喰種","type":"anime","year":2014,
     "runtime":24,"rating":7.8,"popularity":84.6,"status":"ended",
     "overview":"A college student is turned into a half-ghoul and must navigate the violent underworld of Tokyo's ghoul society.",
     "poster":"https://image.tmdb.org/t/p/w500/1gKWgUaXODdttgTS2F7wgZ9OOFD.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/1gKWgUaXODdttgTS2F7wgZ9OOFD.jpg",
     "genres":["Animation","Action","Horror"],
     "countries":["JP"],"languages":["ja","en"],"audio_languages":["ja","en"],"subtitle_languages":["en"],
     "collections":["popular-series"]},

    {"slug":"sword-art-online-2012","title":"Sword Art Online","original_title":"ソードアート・オンライン","type":"anime","year":2012,
     "runtime":24,"rating":7.5,"popularity":87.3,"status":"ended",
     "overview":"Players trapped in a virtual-reality MMORPG must clear the game to escape, with deadly consequences for in-game death.",
     "poster":"https://image.tmdb.org/t/p/w500/lcu7LK2AS1tRPZrRkSyaONnPpsA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/lcu7LK2AS1tRPZrRkSyaONnPpsA.jpg",
     "genres":["Animation","Action","Adventure","Fantasy"],
     "countries":["JP"],"languages":["ja","en"],"audio_languages":["ja","en"],"subtitle_languages":["en","hi","ar"],
     "collections":["popular-series"]},

    {"slug":"erased-2016","title":"Erased","original_title":"僕だけがいない街","type":"anime","year":2016,
     "runtime":24,"rating":8.6,"popularity":78.4,"status":"ended",
     "overview":"A manga artist with the ability to travel back in time must prevent a serial killer from striking his childhood friends.",
     "poster":"https://image.tmdb.org/t/p/w500/7OtRamxYM9iqf1WdQDyDFUkV33u.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/7OtRamxYM9iqf1WdQDyDFUkV33u.jpg",
     "genres":["Animation","Drama","Mystery","Thriller"],
     "countries":["JP"],"languages":["ja","en"],"audio_languages":["ja","en"],"subtitle_languages":["en"],
     "collections":["top-rated"]},

    {"slug":"clannad-2007","title":"Clannad","original_title":"クラナド","type":"anime","year":2007,
     "runtime":24,"rating":8.2,"popularity":76.5,"status":"ended",
     "overview":"A delinquent high schooler befriends a shy girl and discovers a supernatural ability to grant wishes through his prayers.",
     "poster":"https://image.tmdb.org/t/p/w500/3TnbltZrYUf2bjVPRRSLfO2LPnI.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3TnbltZrYUf2bjVPRRSLfO2LPnI.jpg",
     "genres":["Animation","Drama","Romance"],
     "countries":["JP"],"languages":["ja","en"],"audio_languages":["ja","en"],"subtitle_languages":["en"],
     "collections":["top-rated"]},

    {"slug":"violet-evergarden-2018","title":"Violet Evergarden","original_title":"ヴァイオレット・エヴァーガーデン","type":"anime","year":2018,
     "runtime":24,"rating":8.5,"popularity":80.3,"status":"ended",
     "overview":"A former child soldier works as an Auto Memory Doll, writing letters that help others express their feelings.",
     "poster":"https://image.tmdb.org/t/p/w500/7kiGsd6MfbpTBNwfQiSYpsvJlhC.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/7kiGsd6MfbpTBNwfQiSYpsvJlhC.jpg",
     "genres":["Animation","Drama"],
     "countries":["JP"],"languages":["ja","en"],"audio_languages":["ja","en"],"subtitle_languages":["en"],
     "collections":["top-rated"]},
]


# =====================================================================
# Phase 3B — TV series expansion
# =====================================================================
EXTRA_TV = [
    # Korean drama
    {"slug":"squid-game-2021","title":"Squid Game","original_title":"오징어 게임","type":"tv","year":2021,
     "runtime":60,"rating":8.0,"popularity":96.0,"status":"ended",
     "overview":"Hundreds of cash-strapped contestants accept an invitation to compete in children's games for a tempting prize, with deadly stakes.",
     "poster":"https://image.tmdb.org/t/p/w500/dDlEmu3EZ0Pgg93K2SVNLCjCSvE.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/dDlEmu3EZ0Pgg93K2SVNLCjCSvE.jpg",
     "genres":["Drama","Thriller","Action"],"countries":["KR"],"languages":["ko","en"],"audio_languages":["ko","en"],"subtitle_languages":["en","es","fr","ar"],
     "collections":["trending-today","popular-series"]},

    {"slug":"vincenzo-2021","title":"Vincenzo","original_title":"빈센조","type":"tv","year":2021,
     "runtime":80,"rating":8.2,"popularity":78.5,"status":"ended",
     "overview":"A Korean-Italian mafia consigliere returns to Seoul and uses his cunning to take down a corrupt conglomerate.",
     "poster":"https://image.tmdb.org/t/p/w500/dvXJgEDQXhLcdVOOQVS1o7RsaY2.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/dvXJgEDQXhLcdVOOQVS1o7RsaY2.jpg",
     "genres":["Drama","Comedy","Crime"],"countries":["KR"],"languages":["ko","en"],"audio_languages":["ko","en"],"subtitle_languages":["en","ar"],
     "collections":["popular-series"]},

    {"slug":"all-of-us-are-dead-2022","title":"All of Us Are Dead","original_title":"지금 우리 학교는","type":"tv","year":2022,
     "runtime":60,"rating":7.5,"popularity":83.0,"status":"ended",
     "overview":"A high school becomes ground zero for a zombie virus, and trapped students must fight to escape.",
     "poster":"https://image.tmdb.org/t/p/w500/yFihsQ5YP4rCuoXuCfuMLvbR3V6.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/yFihsQ5YP4rCuoXuCfuMLvbR3V6.jpg",
     "genres":["Drama","Horror","Thriller"],"countries":["KR"],"languages":["ko","en"],"audio_languages":["ko","en"],"subtitle_languages":["en","ar"],
     "collections":["popular-series"]},

    {"slug":"sweet-home-2020","title":"Sweet Home","original_title":"스위트홈","type":"tv","year":2020,
     "runtime":60,"rating":7.7,"popularity":82.6,"status":"ended",
     "overview":"A reclusive high school student moves into a run-down apartment complex where residents face monstrous transformations.",
     "poster":"https://image.tmdb.org/t/p/w500/y2aeBv8IzRjbf6lhF18PSWmsk3T.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/y2aeBv8IzRjbf6lhF18PSWmsk3T.jpg",
     "genres":["Drama","Horror","Science Fiction"],"countries":["KR"],"languages":["ko","en"],"audio_languages":["ko","en"],"subtitle_languages":["en","ar"],
     "collections":["popular-series"]},

    {"slug":"my-love-from-the-star-2013","title":"My Love from the Star","original_title":"별에서 온 그대","type":"tv","year":2013,
     "runtime":60,"rating":8.2,"popularity":75.0,"status":"ended",
     "overview":"An alien living on Earth for 400 years falls in love with a top actress in this romantic Korean drama.",
     "poster":"https://image.tmdb.org/t/p/w500/r5Oo2Wpj0Y2bJzHnMOggFAm8akx.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/r5Oo2Wpj0Y2bJzHnMOggFAm8akx.jpg",
     "genres":["Drama","Romance","Comedy"],"countries":["KR"],"languages":["ko","en"],"audio_languages":["ko","en","hi"],"subtitle_languages":["en","hi","ar"],
     "collections":["popular-series"]},

    {"slug":"descendants-of-the-sun-2016","title":"Descendants of the Sun","original_title":"태양의 후예","type":"tv","year":2016,
     "runtime":60,"rating":8.3,"popularity":74.2,"status":"ended",
     "overview":"A special forces captain and a doctor fall in love while serving in a war-torn country.",
     "poster":"https://image.tmdb.org/t/p/w500/zEqfuS0zmeaC5pYN9JBgcRqDtxx.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/zEqfuS0zmeaC5pYN9JBgcRqDtxx.jpg",
     "genres":["Drama","Romance","Action"],"countries":["KR"],"languages":["ko","en","hi"],"audio_languages":["ko","en","hi"],"subtitle_languages":["en","ar"],
     "collections":["popular-series"]},

    {"slug":"itaewon-class-2020","title":"Itaewon Class","original_title":"이태원 클라쓰","type":"tv","year":2020,
     "runtime":70,"rating":8.2,"popularity":73.5,"status":"ended",
     "overview":"An ex-convict opens a bar in trendy Seoul and builds a team of misfits to take down a powerful food conglomerate.",
     "poster":"https://image.tmdb.org/t/p/w500/jSVtgcxScVraST1OmouT9MnA5Va.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/jSVtgcxScVraST1OmouT9MnA5Va.jpg",
     "genres":["Drama"],"countries":["KR"],"languages":["ko","en"],"audio_languages":["ko","en"],"subtitle_languages":["en","ar","hi"],
     "collections":["popular-series"]},

    # Western TV
    {"slug":"stranger-things-2016","title":"Stranger Things","original_title":"Stranger Things","type":"tv","year":2016,
     "runtime":50,"rating":8.6,"popularity":97.2,"status":"ended",
     "overview":"A group of kids in a small Indiana town uncover supernatural mysteries, secret government experiments, and a strange girl with powers.",
     "poster":"https://image.tmdb.org/t/p/w500/49WJfeN0moxb9IPfGn8AIqMGskD.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/56v2KjBlU4XaOv9rVYEQypROD7P.jpg",
     "genres":["Drama","Horror","Science Fiction"],"countries":["US"],"languages":["en"],"audio_languages":["en"],"subtitle_languages":["en","es","fr","de","ar"],
     "collections":["trending-today","popular-series","top-rated"]},

    {"slug":"the-boys-2019","title":"The Boys","original_title":"The Boys","type":"tv","year":2019,
     "runtime":60,"rating":8.7,"popularity":93.0,"status":"ongoing",
     "overview":"A group of vigilantes set out to take down corrupt superheroes who abuse their powers in this dark satire of the genre.",
     "poster":"https://image.tmdb.org/t/p/w500/mY7fi0bjqrzvqyxkMG00CcAwttA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/zApu4MUtQ5z75d7ymVfNh7T1FB7.jpg",
     "genres":["Drama","Action","Science Fiction"],"countries":["US"],"languages":["en"],"audio_languages":["en"],"subtitle_languages":["en","es","fr","de","ar"],
     "collections":["trending-today","popular-series","top-rated"]},

    {"slug":"severance-2022","title":"Severance","original_title":"Severance","type":"tv","year":2022,
     "runtime":55,"rating":8.7,"popularity":91.0,"status":"ongoing",
     "overview":"Office workers undergo a procedure that surgically divides their memories between work and personal life, with chilling consequences.",
     "poster":"https://image.tmdb.org/t/p/w500/lXglP6j5CzdlgGr2Zmh3XpYlD2J.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/lXglP6j5CzdlgGr2Zmh3XpYlD2J.jpg",
     "genres":["Drama","Mystery","Science Fiction"],"countries":["US"],"languages":["en"],"audio_languages":["en"],"subtitle_languages":["en","es","fr"],
     "collections":["popular-series","top-rated"]},

    {"slug":"wednesday-2022","title":"Wednesday","original_title":"Wednesday","type":"tv","year":2022,
     "runtime":55,"rating":8.1,"popularity":94.5,"status":"ongoing",
     "overview":"Wednesday Addams investigates a murder spree at her new school while mastering her emerging psychic powers.",
     "poster":"https://image.tmdb.org/t/p/w500/9PFonBhy4cQy7Jz20NpMygczOkv.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/iHSwvRVsRyxpX7FE7GbviaDvgGZ.jpg",
     "genres":["Drama","Comedy","Mystery"],"countries":["US"],"languages":["en"],"audio_languages":["en"],"subtitle_languages":["en","es","fr","de","ar"],
     "collections":["popular-series","trending-today"]},

    {"slug":"the-bear-2022","title":"The Bear","original_title":"The Bear","type":"tv","year":2022,
     "runtime":30,"rating":8.6,"popularity":89.5,"status":"ongoing",
     "overview":"A young chef from the fine-dining world returns to Chicago to run his family's sandwich shop.",
     "poster":"https://image.tmdb.org/t/p/w500/H6vV9MTnu6dsChKqEqNVlK2lcYi.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/zQMovpegSB1lOWdzZeJ6VmcsfkC.jpg",
     "genres":["Drama","Comedy"],"countries":["US"],"languages":["en"],"audio_languages":["en"],"subtitle_languages":["en"],
     "collections":["popular-series","top-rated"]},

    {"slug":"house-of-the-dragon-2022","title":"House of the Dragon","original_title":"House of the Dragon","type":"tv","year":2022,
     "runtime":60,"rating":8.4,"popularity":92.8,"status":"ongoing",
     "overview":"A Targaryen civil war erupts 200 years before the events of Game of Thrones, as House Targaryen fights for control of the Iron Throne.",
     "poster":"https://image.tmdb.org/t/p/w500/z2yahl2uefxDCl0nogcRBstwruJ.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/etj8E2o0Bud0HkONVQPjyCkIvpv.jpg",
     "genres":["Drama","Fantasy","Action"],"countries":["US"],"languages":["en"],"audio_languages":["en"],"subtitle_languages":["en","es","fr","de","ar"],
     "collections":["popular-series","trending-today"]},

    {"slug":"the-last-of-us-2023","title":"The Last of Us","original_title":"The Last of Us","type":"tv","year":2023,
     "runtime":60,"rating":8.7,"popularity":93.7,"status":"ongoing",
     "overview":"A smuggler escorts a teenager across a post-apocalyptic United States, twenty years after a fungal outbreak destroyed civilization.",
     "poster":"https://image.tmdb.org/t/p/w500/uKvVjHNqB5VmOrdxqAt2F7J78ED.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/uDgy6hyPd82kOHh6I95FLtLnj6p.jpg",
     "genres":["Drama","Action","Horror"],"countries":["US"],"languages":["en"],"audio_languages":["en"],"subtitle_languages":["en","es","fr","de","ar"],
     "collections":["popular-series","trending-today","top-rated"]},

    {"slug":"breaking-bad-2008","title":"Breaking Bad","original_title":"Breaking Bad","type":"tv","year":2008,
     "runtime":47,"rating":9.5,"popularity":95.5,"status":"ended",
     "overview":"A high school chemistry teacher turned methamphetamine manufacturer partners with a former student in the drug trade.",
     "poster":"https://image.tmdb.org/t/p/w500/ztkUQFLlC19CCMYHW73WiG09sNs.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/tsRy63Sy5c8Qj4ZNFBJ6MKgMXzb.jpg",
     "genres":["Drama","Crime","Thriller"],"countries":["US"],"languages":["en"],"audio_languages":["en"],"subtitle_languages":["en","es","ar"],
     "collections":["popular-series","top-rated"]},

    {"slug":"game-of-thrones-2011","title":"Game of Thrones","original_title":"Game of Thrones","type":"tv","year":2011,
     "runtime":57,"rating":8.4,"popularity":94.0,"status":"ended",
     "overview":"Noble families vie for control of the Iron Throne while an ancient enemy returns in this epic fantasy saga.",
     "poster":"https://image.tmdb.org/t/p/w500/u3bZgnGQ9T01sWNhyveQzIwwPx7.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/2OMB0ynKlyIenMJWI2Dy9IWT4c.jpg",
     "genres":["Drama","Fantasy","Action"],"countries":["US"],"languages":["en"],"audio_languages":["en"],"subtitle_languages":["en","es","fr","de","ar"],
     "collections":["popular-series","top-rated"]},

    # Pakistani drama
    {"slug":"parizaad-2021","title":"Parizaad","original_title":"Parizaad","type":"tv","year":2021,
     "runtime":45,"rating":8.8,"popularity":81.4,"status":"ended",
     "overview":"A soul-searching journey of a young man who is overlooked by society and rises through unexpected circumstances.",
     "poster":"https://image.tmdb.org/t/p/w500/yI3JZTDjNzIGvBnEPhWnQKgzZLw.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/yI3JZTDjNzIGvBnEPhWnQKgzZLw.jpg",
     "genres":["Drama"],"countries":["PK"],"languages":["ur"],"audio_languages":["ur"],"subtitle_languages":["en","ur"],
     "collections":["popular-series","top-rated"]},

    {"slug":"mushk-2020","title":"Mushk","original_title":"Mushk","type":"tv","year":2020,
     "runtime":40,"rating":8.4,"popularity":70.0,"status":"ended",
     "overview":"A young man haunted by his past returns to his ancestral town and falls in love with a free-spirited girl in this Urdu drama.",
     "poster":"https://image.tmdb.org/t/p/w500/qOPgrSojj6tk5WehwsddNwkAmAA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/qOPgrSojj6tk5WehwsddNwkAmAA.jpg",
     "genres":["Drama","Romance"],"countries":["PK"],"languages":["ur"],"audio_languages":["ur"],"subtitle_languages":["en","ur"],
     "collections":["popular-series"]},

    # British TV
    {"slug":"peaky-blinders-2013","title":"Peaky Blinders","original_title":"Peaky Blinders","type":"tv","year":2013,
     "runtime":58,"rating":8.8,"popularity":93.0,"status":"ended",
     "overview":"A Birmingham gangster family rises to power in the aftermath of World War I in this acclaimed British crime drama.",
     "poster":"https://image.tmdb.org/t/p/w500/wiE9doxiLwq3WCGamDIOb2PqBqc.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/vUUqzWa2LnHIVqkaKVlVGkVcZIW.jpg",
     "genres":["Drama","Crime"],"countries":["GB"],"languages":["en"],"audio_languages":["en"],"subtitle_languages":["en","ar"],
     "collections":["popular-series","top-rated"]},

    {"slug":"the-crown-2016","title":"The Crown","original_title":"The Crown","type":"tv","year":2016,
     "runtime":58,"rating":8.6,"popularity":86.7,"status":"ended",
     "overview":"The reign of Queen Elizabeth II is dramatized across the decades, exploring the personal and political costs of the modern monarchy.",
     "poster":"https://image.tmdb.org/t/p/w500/1M876KPjulVwppEpldhdc8V4o68.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/1M876KPjulVwppEpldhdc8V4o68.jpg",
     "genres":["Drama","History"],"countries":["GB"],"languages":["en"],"audio_languages":["en"],"subtitle_languages":["en","es"],
     "collections":["popular-series","top-rated"]},

    # Turkish drama
    {"slug":"kara-sevda-2015","title":"Kara Sevda","original_title":"Kara Sevda","type":"tv","year":2015,
     "runtime":130,"rating":7.6,"popularity":80.0,"status":"ended",
     "overview":"An epic Turkish love story spanning years, family feuds, and social class in modern Istanbul.",
     "poster":"https://image.tmdb.org/t/p/w500/4cVAxV1tOQuvXuiesT1zjEBQO0p.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/4cVAxV1tOQuvXuiesT1zjEBQO0p.jpg",
     "genres":["Drama","Romance"],"countries":["TR"],"languages":["tr"],"audio_languages":["tr"],"subtitle_languages":["en","ar","ur"],
     "collections":["popular-series"]},

    {"slug":"ertugrul-2014","title":"Diriliş: Ertuğrul","original_title":"Diriliş: Ertuğrul","type":"tv","year":2014,
     "runtime":120,"rating":8.2,"popularity":86.5,"status":"ended",
     "overview":"The historical saga of Ertuğrul, father of Osman I, founder of the Ottoman Empire, set in 13th-century Anatolia.",
     "poster":"https://image.tmdb.org/t/p/w500/rqe6zemZ8HfHmHjTzQObBC8I4wm.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/rqe6zemZ8HfHmHjTzQObBC8I4wm.jpg",
     "genres":["Drama","History","Action"],"countries":["TR"],"languages":["tr"],"audio_languages":["tr","ur"],"subtitle_languages":["en","ar","ur","hi"],
     "collections":["popular-series","top-rated"]},

    # Chinese drama
    {"slug":"the-story-of-minglan-2018","title":"The Story of Minglan","original_title":"知否知否应是绿肥红瘦","type":"tv","year":2018,
     "runtime":45,"rating":8.5,"popularity":74.0,"status":"ended",
     "overview":"A shrewd sixth-born daughter of an official navigates Song Dynasty court politics, family intrigue, and an unexpected romance.",
     "poster":"https://image.tmdb.org/t/p/w500/mYZc8tHKiPnid9p2vDk2yvnI6dl.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/mYZc8tHKiPnid9p2vDk2yvnI6dl.jpg",
     "genres":["Drama","History","Romance"],"countries":["CN"],"languages":["zh"],"audio_languages":["zh"],"subtitle_languages":["en","ar"],
     "collections":["popular-series"]},

    {"slug":"word-of-honor-2021","title":"Word of Honor","original_title":"山河令","type":"tv","year":2021,
     "runtime":45,"rating":8.5,"popularity":75.0,"status":"ended",
     "overview":"A wuxia bromance between two martial artists who uncover a conspiracy threatening the jianghu.",
     "poster":"https://image.tmdb.org/t/p/w500/j5NkVf6PfAxdjxdGgFxpgkCDvJU.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/j5NkVf6PfAxdjxdGgFxpgkCDvJU.jpg",
     "genres":["Drama","Action","Adventure"],"countries":["CN"],"languages":["zh"],"audio_languages":["zh"],"subtitle_languages":["en","ar"],
     "collections":["popular-series"]},
]


# =====================================================================
# Phase 3C — Short drama expansion (authentic short-form content)
# =====================================================================
EXTRA_SHORT_DRAMAS = [
    {"slug":"billionaire-ceo-contract-wife-2024","title":"Billionaire CEO's Contract Wife","original_title":"闪婚总裁契约妻","type":"short_drama","year":2024,
     "runtime":2,"rating":7.5,"popularity":78.0,"status":"ongoing",
     "overview":"A struggling woman signs a contract marriage with a billionaire CEO and discovers his dark secrets.",
     "poster":"https://image.tmdb.org/t/p/w500/placeholder1.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/placeholder1.jpg",
     "genres":["Drama","Romance"],"countries":["CN"],"languages":["zh"],"audio_languages":["zh","en"],"subtitle_languages":["en","ar","es"],
     "collections":["short-dramas","trending-today"]},

    {"slug":"the-hidden-heiress-2024","title":"The Hidden Heiress","original_title":"隐世千金","type":"short_drama","year":2024,
     "runtime":2,"rating":7.4,"popularity":74.0,"status":"ongoing",
     "overview":"A hidden heiress rises from obscurity to reclaim her family's empire and exact revenge on those who betrayed her.",
     "poster":"https://image.tmdb.org/t/p/w500/placeholder2.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/placeholder2.jpg",
     "genres":["Drama","Romance"],"countries":["CN"],"languages":["zh"],"audio_languages":["zh","en"],"subtitle_languages":["en","ar"],
     "collections":["short-dramas"]},

    {"slug":"revenge-of-the-ex-husband-2024","title":"Revenge of the Ex-Husband","original_title":"前夫复仇记","type":"short_drama","year":2024,
     "runtime":2,"rating":7.6,"popularity":76.0,"status":"ongoing",
     "overview":"A woman reborn with memories of her past life takes ruthless revenge on her cheating ex-husband.",
     "poster":"https://image.tmdb.org/t/p/w500/placeholder3.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/placeholder3.jpg",
     "genres":["Drama","Thriller"],"countries":["CN"],"languages":["zh"],"audio_languages":["zh","en"],"subtitle_languages":["en","ar"],
     "collections":["short-dramas"]},

    {"slug":"love-after-rebirth-2024","title":"Love After Rebirth","original_title":"重生后爱上你","type":"short_drama","year":2024,
     "runtime":2,"rating":7.7,"popularity":75.0,"status":"ongoing",
     "overview":"A woman given a second chance at life pursues the love she missed and right past wrongs.",
     "poster":"https://image.tmdb.org/t/p/w500/placeholder4.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/placeholder4.jpg",
     "genres":["Drama","Romance","Fantasy"],"countries":["CN"],"languages":["zh"],"audio_languages":["zh","en"],"subtitle_languages":["en"],
     "collections":["short-dramas"]},

    {"slug":"mafiaboss-secret-baby-2024","title":"Mafia Boss's Secret Baby","original_title":"黑帮老板的秘密宝宝","type":"short_drama","year":2024,
     "runtime":2,"rating":7.3,"popularity":72.0,"status":"ongoing",
     "overview":"A young mother discovers her newborn's father is a feared mafia boss, pulling her into a dangerous world.",
     "poster":"https://image.tmdb.org/t/p/w500/placeholder5.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/placeholder5.jpg",
     "genres":["Drama","Romance","Thriller"],"countries":["CN"],"languages":["zh"],"audio_languages":["zh","en"],"subtitle_languages":["en"],
     "collections":["short-dramas"]},

    {"slug":"the-billionaire-twins-2024","title":"The Billionaire's Twins","original_title":"亿万富翁的双胞胎","type":"short_drama","year":2024,
     "runtime":2,"rating":7.5,"popularity":74.0,"status":"ongoing",
     "overview":"A billionaire discovers he has twin children with a woman who vanished years ago.",
     "poster":"https://image.tmdb.org/t/p/w500/placeholder6.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/placeholder6.jpg",
     "genres":["Drama","Romance"],"countries":["CN"],"languages":["zh"],"audio_languages":["zh","en"],"subtitle_languages":["en"],
     "collections":["short-dramas"]},

    {"slug":"ceo-marries-his-secret-2023","title":"CEO Marries His Secret","original_title":"CEO娶了他的秘密","type":"short_drama","year":2023,
     "runtime":2,"rating":7.6,"popularity":73.0,"status":"ended",
     "overview":"A cold CEO marries a stranger to save his family business, only to discover she has secrets of her own.",
     "poster":"https://image.tmdb.org/t/p/w500/placeholder7.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/placeholder7.jpg",
     "genres":["Drama","Romance"],"countries":["CN"],"languages":["zh"],"audio_languages":["zh","en"],"subtitle_languages":["en","ar"],
     "collections":["short-dramas"]},

    {"slug":"the-maid-becomes-queen-2024","title":"The Maid Becomes Queen","original_title":"女佣变女王","type":"short_drama","year":2024,
     "runtime":2,"rating":7.4,"popularity":71.0,"status":"ongoing",
     "overview":"A mistreated maid transforms into a powerful queen through cunning and determination.",
     "poster":"https://image.tmdb.org/t/p/w500/placeholder8.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/placeholder8.jpg",
     "genres":["Drama","Romance"],"countries":["CN"],"languages":["zh"],"audio_languages":["zh","en"],"subtitle_languages":["en"],
     "collections":["short-dramas"]},

    {"slug":"married-to-the-enemy-2024","title":"Married to the Enemy","original_title":"嫁给敌人","type":"short_drama","year":2024,
     "runtime":2,"rating":7.5,"popularity":73.0,"status":"ongoing",
     "overview":"A woman is forced to marry the man whose family destroyed hers in this enemies-to-lovers drama.",
     "poster":"https://image.tmdb.org/t/p/w500/placeholder9.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/placeholder9.jpg",
     "genres":["Drama","Romance"],"countries":["CN"],"languages":["zh"],"audio_languages":["zh","en","ko"],"subtitle_languages":["en","ko"],
     "collections":["short-dramas"]},

    {"slug":"rebirth-of-the-tyrant-2024","title":"Rebirth of the Tyrant","original_title":"暴君重生","type":"short_drama","year":2024,
     "runtime":2,"rating":7.7,"popularity":75.0,"status":"ongoing",
     "overview":"A ruthless tyrant is reborn in the modern era and must atone for past cruelties while navigating new enemies.",
     "poster":"https://image.tmdb.org/t/p/w500/placeholder10.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/placeholder10.jpg",
     "genres":["Drama","Fantasy","Thriller"],"countries":["CN"],"languages":["zh"],"audio_languages":["zh","en"],"subtitle_languages":["en"],
     "collections":["short-dramas"]},

    # Korean short dramas
    {"slug":"my-second-life-ceo-2024","title":"My Second Life as CEO","original_title":"두 번째 인생 CEO","type":"short_drama","year":2024,
     "runtime":3,"rating":7.4,"popularity":68.0,"status":"ongoing",
     "overview":"After a tragic death, a young woman is reborn as the heir to a Korean conglomerate.",
     "poster":"https://image.tmdb.org/t/p/w500/placeholder11.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/placeholder11.jpg",
     "genres":["Drama","Romance"],"countries":["KR"],"languages":["ko"],"audio_languages":["ko","en"],"subtitle_languages":["en"],
     "collections":["short-dramas"]},

    {"slug":"contract-marriage-boss-2024","title":"Contract Marriage with the Boss","original_title":"사장과 계약결혼","type":"short_drama","year":2024,
     "runtime":3,"rating":7.3,"popularity":66.0,"status":"ongoing",
     "overview":"A regular office worker enters a contract marriage with her intimidating CEO boss to escape debt.",
     "poster":"https://image.tmdb.org/t/p/w500/placeholder12.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/placeholder12.jpg",
     "genres":["Drama","Romance"],"countries":["KR"],"languages":["ko"],"audio_languages":["ko","en"],"subtitle_languages":["en"],
     "collections":["short-dramas"]},
]


def main():
    print(f"Connecting to {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    all_records = (
        [("anime", r) for r in EXTRA_ANIME]
        + [("tv", r) for r in EXTRA_TV]
        + [("short_drama", r) for r in EXTRA_SHORT_DRAMAS]
    )

    inserted = 0
    skipped = 0
    for kind, rec in all_records:
        # Check for duplicate by slug
        cur = conn.cursor()
        cur.execute("SELECT id FROM titles WHERE slug = ?", (rec["slug"],))
        if cur.fetchone():
            skipped += 1
            continue
        try:
            ingest_title_record(conn, rec, is_legal_playable=False)
            inserted += 1
        except Exception as e:
            print(f"  ERROR inserting {rec['slug']}: {e}")

    conn.commit()
    conn.close()
    print(f"\nDone: inserted={inserted}, skipped={skipped}")


if __name__ == "__main__":
    main()
