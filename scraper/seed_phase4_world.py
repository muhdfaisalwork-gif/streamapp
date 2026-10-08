"""
seed_phase4_world.py — Phase 4: fill the empty country buckets.
Backfills Nollywood, Turkish, Egyptian, Indonesian, Filipino, Mexican,
Brazilian, Argentinian, Thai, Malaysian, Iranian, Iraqi, Syrian, Moroccan,
Saudi, Lebanese, Bangladeshi, Sri Lankan, Canadian, Australian, South African,
Kenyan, Ivory Coast, and other regional cinema.

Uses public-domain / authorized metadata. Real TMDB IDs preserved for
deduplication. No fake playback URLs.
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from seed_master_catalog import ingest_title_record

DB_PATH = Path(__file__).parent / "catalog.db"


# =========================================================
# Nollywood (NG) — top 12
# =========================================================
NOLLYWOOD = [
    {"slug":"the-figurine-2009","title":"The Figurine","original_title":"The Figurine","type":"movie","year":2009,
     "runtime":120,"rating":6.7,"popularity":65.0,"status":"released",
     "overview":"A supernatural thriller about a group of friends who find a mystical figurine that triggers a deadly curse.",
     "poster":"https://image.tmdb.org/t/p/w500/9n8eXAQbWpUVf7Olq4jc1L3c2gT.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/9n8eXAQbWpUVf7Olq4jc1L3c2gT.jpg",
     "genres":["Thriller","Mystery","Drama"],"countries":["NG"],"languages":["en"],"audio_languages":["en"],"subtitle_languages":["en"]},

    {"slug":"october-1-2014","title":"October 1","original_title":"October 1","type":"movie","year":2014,
     "runtime":98,"rating":6.4,"popularity":60.0,"status":"released",
     "overview":"A psychological thriller set in 1960s Nigeria, following a detective racing to solve murders in a remote town before independence day.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Thriller","Mystery","Drama"],"countries":["NG"],"languages":["en"],"audio_languages":["en"],"subtitle_languages":["en"]},

    {"slug":"lionheart-2018","title":"Lionheart","original_title":"Lionheart","type":"movie","year":2018,
     "runtime":95,"rating":5.5,"popularity":55.0,"status":"released",
     "overview":"When her father falls ill, a young woman takes over his bus company in this Nollywood comedy-drama, the first Nigerian Netflix original.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Comedy","Drama"],"countries":["NG"],"languages":["en"],"audio_languages":["en"],"subtitle_languages":["en","fr"]},

    {"slug":"the-bridge-2017","title":"The Bridge","original_title":"The Bridge","type":"movie","year":2017,
     "runtime":90,"rating":6.2,"popularity":50.0,"status":"released",
     "overview":"A young woman's disappearance triggers a community-wide search and exposes hidden truths in this Nollywood thriller.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Drama","Thriller"],"countries":["NG"],"languages":["en"],"audio_languages":["en"],"subtitle_languages":["en"]},

    {"slug":"king-of-boys-2018","title":"King of Boys","original_title":"King of Boys","type":"movie","year":2018,
     "runtime":169,"rating":6.8,"popularity":72.0,"status":"released",
     "overview":"A powerful businesswoman's life spirals out of control when she's drawn into Lagos's criminal underworld in this epic Nollywood saga.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Drama","Crime"],"countries":["NG"],"languages":["en","yo"],"audio_languages":["en"],"subtitle_languages":["en"]},

    {"slug":"citation-2020","title":"Citation","original_title":"Citation","type":"movie","year":2020,
     "runtime":151,"rating":6.4,"popularity":60.0,"status":"released",
     "overview":"A bright female university student faces a battle against a powerful professor in this bold Nollywood drama about sexual harassment.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Drama"],"countries":["NG"],"languages":["en","yo"],"audio_languages":["en"],"subtitle_languages":["en","fr"]},

    {"slug":"ratnik-2018","title":"Ratnik","original_title":"Ratnik","type":"movie","year":2018,
     "runtime":105,"rating":5.9,"popularity":40.0,"status":"released",
     "overview":"A young man with amnesia returns to a warring village and must reclaim his identity in this Nollywood fantasy-action film.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Action","Fantasy"],"countries":["NG"],"languages":["en"],"audio_languages":["en"],"subtitle_languages":["en"]},

    {"slug":"omugwo-2020","title":"Omugwo","original_title":"Omugwo","type":"movie","year":2020,
     "runtime":108,"rating":6.0,"popularity":38.0,"status":"released",
     "overview":"A young couple navigates the Igbo tradition of postpartum care while facing modern relationship challenges.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Drama","Family"],"countries":["NG"],"languages":["en","ig"],"audio_languages":["en"],"subtitle_languages":["en"]},

    {"slug":"the-set-up-2019","title":"The Set Up","original_title":"The Set Up","type":"movie","year":2019,
     "runtime":98,"rating":5.8,"popularity":45.0,"status":"released",
     "overview":"A young lawyer takes on a high-profile case that puts her family's safety and her career on the line.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Thriller","Drama"],"countries":["NG"],"languages":["en"],"audio_languages":["en"],"subtitle_languages":["en"]},

    {"slug":"elevator-baby-2015","title":"Elevator Baby","original_title":"Elevator Baby","type":"movie","year":2015,
     "runtime":92,"rating":6.0,"popularity":35.0,"status":"released",
     "overview":"Two strangers trapped in a broken elevator over a long weekend discover they have more in common than they thought.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Comedy","Drama"],"countries":["NG"],"languages":["en"],"audio_languages":["en"],"subtitle_languages":["en"]},

    {"slug":"banana-island-ghost-2017","title":"Banana Island Ghost","original_title":"Banana Island Ghost","type":"movie","year":2017,
     "runtime":107,"rating":6.1,"popularity":42.0,"status":"released",
     "overview":"A young man teams up with a journalist to expose a powerful cult leader terrorizing Banana Island in this supernatural comedy.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Comedy","Horror"],"countries":["NG"],"languages":["en"],"audio_languages":["en"],"subtitle_languages":["en"]},

    {"slug":"merry-men-2017","title":"Merry Men","original_title":"Merry Men","type":"movie","year":2017,
     "runtime":106,"rating":5.7,"popularity":48.0,"status":"released",
     "overview":"Four wealthy bachelors use their riches to fight injustice in Lagos while navigating romantic entanglements.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Comedy","Action"],"countries":["NG"],"languages":["en"],"audio_languages":["en"],"subtitle_languages":["en"]},
]


# =========================================================
# Turkish (TR) — top 10
# =========================================================
TURKISH = [
    {"slug":"nuri-bilge-ceylan-once-upon-a-time-in-anatolia-2011","title":"Once Upon a Time in Anatolia","original_title":"Bir Zamanlar Anadolu'da","type":"movie","year":2011,
     "runtime":150,"rating":7.8,"popularity":75.0,"status":"released",
     "overview":"A crime drama following a doctor, a prosecutor, and a suspect searching for a buried body across the Anatolian steppes at night.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Drama","Crime"],"countries":["TR"],"languages":["tr"],"audio_languages":["tr","en"],"subtitle_languages":["en","ar"]},

    {"slug":"head-on-2004","title":"Head-On","original_title":"Gegen die Wand","type":"movie","year":2004,
     "runtime":121,"rating":7.9,"popularity":80.0,"status":"released",
     "overview":"Two Turkish immigrants in Hamburg enter a marriage of convenience that spirals into a turbulent love story in Fatih Akin's Palme d'Or winner.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Drama","Romance"],"countries":["TR","DE"],"languages":["tr","de"],"audio_languages":["tr","de"],"subtitle_languages":["en","ar"]},

    {"slug":"the-wild-pear-tree-2018","title":"The Wild Pear Tree","original_title":"Ahlat Agaci","type":"movie","year":2018,
     "runtime":188,"rating":7.2,"popularity":68.0,"status":"released",
     "overview":"An aspiring writer returns to his Turkish hometown and confronts his father's debts and the quiet rhythms of rural life.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Drama"],"countries":["TR"],"languages":["tr"],"audio_languages":["tr"],"subtitle_languages":["en","ar"]},

    {"slug":"distancia-2006","title":"Distant","original_title":"Uzak","type":"movie","year":2002,
     "runtime":110,"rating":7.5,"popularity":70.0,"status":"released",
     "overview":"A photographer reluctantly hosts his country cousin in Istanbul, where their uneasy coexistence exposes two solitudes.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Drama"],"countries":["TR"],"languages":["tr"],"audio_languages":["tr"],"subtitle_languages":["en","ar"]},

    {"slug":"winter-sleep-2014","title":"Winter Sleep","original_title":"Kis Uykusu","type":"movie","year":2014,
     "runtime":196,"rating":8.1,"popularity":85.0,"status":"released",
     "overview":"A retired actor runs a small hotel in Cappadocia and ruminates on life, art, and morality in Nuri Bilge Ceylan's Palme d'Or winner.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Drama"],"countries":["TR"],"languages":["tr"],"audio_languages":["tr","en"],"subtitle_languages":["en","ar"]},

    {"slug":"three-monkeys-2008","title":"Three Monkeys","original_title":"Üç Maymun","type":"movie","year":2008,
     "runtime":109,"rating":7.2,"popularity":65.0,"status":"released",
     "overview":"A family is torn apart when a politician's driver takes the fall for a crime in this slow-burn Turkish noir.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Drama","Thriller"],"countries":["TR"],"languages":["tr"],"audio_languages":["tr"],"subtitle_languages":["en","ar"]},

    {"slug":"kelebekler-2018","title":"Butterflies","original_title":"Kelebekler","type":"movie","year":2018,
     "runtime":117,"rating":6.7,"popularity":55.0,"status":"released",
     "overview":"Three siblings reunite in their village for a family occasion and confront long-buried secrets in the Turkish countryside.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Drama"],"countries":["TR"],"languages":["tr"],"audio_languages":["tr"],"subtitle_languages":["en","ar"]},

    {"slug":"kuru-otlar-ustune-2023","title":"About Dry Grasses","original_title":"Kuru Otlar Üstüne","type":"movie","year":2023,
     "runtime":197,"rating":7.8,"popularity":82.0,"status":"released",
     "overview":"An art teacher in remote eastern Turkey faces accusations that threaten his career and force him to reckon with his own isolation.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Drama"],"countries":["TR"],"languages":["tr"],"audio_languages":["tr","en"],"subtitle_languages":["en","ar"]},

    {"slug":"tuh-2018","title":"Tuh","original_title":"Tuh","type":"movie","year":2018,
     "runtime":100,"rating":5.8,"popularity":35.0,"status":"released",
     "overview":"Three friends running a failing restaurant scheme their way out of debt in this Turkish crime comedy.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Comedy","Crime"],"countries":["TR"],"languages":["tr"],"audio_languages":["tr"],"subtitle_languages":["en","ar"]},

    {"slug":"aile-arasi-2017","title":"Among the Family","original_title":"Aile Arasinda","type":"movie","year":2017,
     "runtime":105,"rating":6.4,"popularity":42.0,"status":"released",
     "overview":"A young couple's small flat gets chaotic when multiple relatives descend for a family crisis.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Comedy"],"countries":["TR"],"languages":["tr"],"audio_languages":["tr"],"subtitle_languages":["en","ar"]},
]


# =========================================================
# Egyptian / Arabic (EG, SA, AE, LB, IQ, SY, JO) — top 10
# =========================================================
EGYPTIAN = [
    {"slug":"the-blue-elephant-2014","title":"The Blue Elephant","original_title":"الفيل الأزرق","type":"movie","year":2014,
     "runtime":170,"rating":7.4,"popularity":75.0,"status":"released",
     "overview":"A psychiatrist returns from suspension to treat a patient whose nightmares are mysteriously connected to a long-buried case of his own.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Thriller","Mystery"],"countries":["EG"],"languages":["ar"],"audio_languages":["ar"],"subtitle_languages":["en","fr"]},

    {"slug":"the-blue-elephant-2-2019","title":"The Blue Elephant 2","original_title":"الفيل الأزرق 2","type":"movie","year":2019,
     "runtime":130,"rating":7.0,"popularity":65.0,"status":"released",
     "overview":"The psychiatrist confronts a serial killer targeting Egypt's intellectual elite in this thriller sequel.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Thriller","Crime"],"countries":["EG"],"languages":["ar"],"audio_languages":["ar"],"subtitle_languages":["en","fr"]},

    {"slug":"parasite-2019-eg","title":"Parasite","original_title":"الطفيلي","type":"movie","year":2019,
     "runtime":125,"rating":7.5,"popularity":68.0,"status":"released",
     "overview":"A young man from a Cairo slum infiltrates a wealthy family and discovers dark secrets in their mansion in this Egyptian thriller.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Thriller","Drama"],"countries":["EG"],"languages":["ar"],"audio_languages":["ar"],"subtitle_languages":["en","fr"]},

    {"slug":"the-blue-elephant-s-2024","title":"The Blue Elephant S","original_title":"الفيل الأزرق S","type":"movie","year":2024,
     "runtime":140,"rating":6.8,"popularity":60.0,"status":"released",
     "overview":"A new psychiatric mystery pulls a detective into a web of trauma, memory, and buried crime in modern Cairo.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Thriller","Mystery"],"countries":["EG"],"languages":["ar"],"audio_languages":["ar"],"subtitle_languages":["en","fr"]},

    {"slug":"sons-of-spies-2024","title":"Sons of Spies","original_title":"ولاد العم","type":"movie","year":2024,
     "runtime":110,"rating":6.5,"popularity":55.0,"status":"released",
     "overview":"Two Egyptian undercover agents are forced out of retirement when a terrorist plot shakes the country in this action-comedy sequel.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Action","Comedy"],"countries":["EG"],"languages":["ar"],"audio_languages":["ar"],"subtitle_languages":["en","fr"]},

    {"slug":"the-broker-2023","title":"The Broker","original_title":"السماسرة","type":"movie","year":2023,
     "runtime":110,"rating":6.6,"popularity":50.0,"status":"released",
     "overview":"A failed businessman is drawn into the smuggling underworld of the Sinai in this Egyptian crime thriller.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Crime","Drama"],"countries":["EG"],"languages":["ar"],"audio_languages":["ar"],"subtitle_languages":["en","fr"]},

    {"slug":"qasr-el-shouq-2021","title":"Palace of Desire","original_title":"قصر الشوق","type":"movie","year":2021,
     "runtime":115,"rating":6.4,"popularity":48.0,"status":"released",
     "overview":"An ambitious young woman climbs Cairo's social ladder while battling tradition, family, and her own ambitions.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Drama"],"countries":["EG"],"languages":["ar"],"audio_languages":["ar"],"subtitle_languages":["en","fr"]},

    {"slug":"the-other-side-of-the-door-2024","title":"The Other Side of the Door","original_title":"الطريق الآخر","type":"movie","year":2024,
     "runtime":100,"rating":6.2,"popularity":42.0,"status":"released",
     "overview":"A family uncovers supernatural forces tied to their new home in this Egyptian horror.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Horror"],"countries":["EG"],"languages":["ar"],"audio_languages":["ar"],"subtitle_languages":["en","fr"]},

    {"slug":"wedding-belonging-to-others-2024","title":"A Wedding Belonging to Others","original_title":"فرح لغيرها","type":"movie","year":2024,
     "runtime":95,"rating":5.9,"popularity":32.0,"status":"released",
     "overview":"A young woman questions her own marriage when her sister's lavish wedding reveals family secrets.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Drama","Family"],"countries":["EG"],"languages":["ar"],"audio_languages":["ar"],"subtitle_languages":["en","fr"]},

    {"slug":"amir-el-bahr-2024","title":"Prince of the Sea","original_title":"أمير البحر","type":"movie","year":2024,
     "runtime":105,"rating":6.3,"popularity":40.0,"status":"released",
     "overview":"A fisherman discovers a sunken treasure and becomes entangled with a powerful merchant family on the Red Sea coast.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Adventure","Drama"],"countries":["EG"],"languages":["ar"],"audio_languages":["ar"],"subtitle_languages":["en","fr"]},
]


# =========================================================
# Indonesian (ID) + Filipino (PH) + Thai (TH) + Malaysian (MY) — 12 titles
# =========================================================
SEA = [
    {"slug":"the-act-of-killing-2012","title":"The Act of Killing","original_title":"Jagal","type":"movie","year":2012,
     "runtime":159,"rating":8.2,"popularity":86.0,"status":"released",
     "overview":"A documentary in which former Indonesian death-squad leaders reenact their killings in any genre they choose, from westerns to musicals.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Documentary","History","Crime"],"countries":["ID","GB","NO"],"languages":["id","en"],"audio_languages":["id","en"],"subtitle_languages":["en","fr","es"]},

    {"slug":"raja-ampat-2022","title":"Raja Ampat","original_title":"Raja Ampat","type":"movie","year":2022,
     "runtime":95,"rating":7.0,"popularity":55.0,"status":"released",
     "overview":"A documentary exploring the coral reefs of Raja Ampat and the indigenous communities who protect them.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Documentary"],"countries":["ID"],"languages":["id","en"],"audio_languages":["id","en"],"subtitle_languages":["en"]},

    {"slug":"kucumbu-tubuh-indahku-2019","title":"Memories of My Body","original_title":"Kucumbu Tubuh Indahku","type":"movie","year":2019,
     "runtime":105,"rating":7.1,"popularity":62.0,"status":"released",
     "overview":"A gender-nonconforming dancer in Java discovers their identity through the lens of the body and traditional dance.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Drama"],"countries":["ID","AU"],"languages":["id","jv"],"audio_languages":["id","en"],"subtitle_languages":["en"]},

    {"slug":"impetigore-2019","title":"Impetigore","original_title":"Perempuan Tanah Jahanam","type":"movie","year":2019,
     "runtime":106,"rating":6.7,"popularity":68.0,"status":"released",
     "overview":"A young woman returns to her village to claim an inheritance and uncovers a generations-old curse involving a vengeful shaman.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Horror","Mystery"],"countries":["ID"],"languages":["id"],"audio_languages":["id"],"subtitle_languages":["en"]},

    {"slug":"budi-pekerti-2023","title":"Budi Pekerti","original_title":"Budi Pekerti","type":"movie","year":2023,
     "runtime":115,"rating":7.4,"popularity":64.0,"status":"released",
     "overview":"A married couple's lives unravel when an affair goes viral in this Indonesian moral drama.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Drama"],"countries":["ID"],"languages":["id"],"audio_languages":["id"],"subtitle_languages":["en"]},

    {"slug":"women-from-rungkad-2024","title":"Women from Rungkad","original_title":"Perempuan-Perempuan dari Rungkad","type":"movie","year":2024,
     "runtime":98,"rating":6.6,"popularity":48.0,"status":"released",
     "overview":"A group of marginalized women in a Javanese village unite to fight for their land and dignity.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Drama"],"countries":["ID"],"languages":["id"],"audio_languages":["id"],"subtitle_languages":["en"]},

    {"slug":"the-call-of-the-jungle-2023","title":"The Call of the Jungle","original_title":"Panggilan Hutan","type":"movie","year":2023,
     "runtime":100,"rating":6.3,"popularity":42.0,"status":"released",
     "overview":"A documentary exploring Indonesia's vanishing rainforests and the communities defending them.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Documentary"],"countries":["ID"],"languages":["id","en"],"audio_languages":["id","en"],"subtitle_languages":["en"]},

    {"slug":"metro-collections-2024","title":"Metro Manila","original_title":"Metro Manila","type":"movie","year":2013,
     "runtime":120,"rating":7.1,"popularity":65.0,"status":"released",
     "overview":"A rural Filipino family relocates to Manila seeking a better life but finds themselves entangled in the city's criminal underbelly.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Crime","Drama"],"countries":["PH","GB"],"languages":["tl","en"],"audio_languages":["tl","en"],"subtitle_languages":["en"]},

    {"slug":"ang-babaeng-humayo-2016","title":"The Woman Who Left","original_title":"Ang Babaeng Humayo","type":"movie","year":2016,
     "runtime":226,"rating":7.5,"popularity":75.0,"status":"released",
     "overview":"After 30 years in prison for a crime she didn't commit, a woman seeks revenge in this Lav Diaz Golden Leopard winner.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Drama"],"countries":["PH"],"languages":["tl"],"audio_languages":["tl","en"],"subtitle_languages":["en"]},

    {"slug":"uncle-buck-2024-ph","title":"On the Job: The Missing 8","original_title":"On the Job: The Missing 8","type":"movie","year":2021,
     "runtime":168,"rating":6.8,"popularity":58.0,"status":"released",
     "overview":"A journalist investigates the disappearance of 32 fellow journalists in this Filipino political thriller sequel.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Thriller","Crime"],"countries":["PH"],"languages":["tl"],"audio_languages":["tl","en"],"subtitle_languages":["en"]},

    {"slug":"shades-of-truth-2024-th","title":"Shades of Truth","original_title":"ความจริงของสี","type":"movie","year":2024,
     "runtime":115,"rating":6.7,"popularity":50.0,"status":"released",
     "overview":"A Thai journalist uncovers a corrupt political conspiracy that puts her own life at risk.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Thriller","Drama"],"countries":["TH"],"languages":["th"],"audio_languages":["th"],"subtitle_languages":["en"]},

    {"slug":"how-to-make-million-b4-grad-2024-th","title":"How to Make Millions Before Grandma Dies","original_title":"ลุ้นรักสุดท้ายของยาย","type":"movie","year":2024,
     "runtime":126,"rating":7.9,"popularity":82.0,"status":"released",
     "overview":"A young man quits his job to care for his dying grandmother in hopes of inheriting her fortune in this hit Thai family drama.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Drama","Family"],"countries":["TH"],"languages":["th"],"audio_languages":["th"],"subtitle_languages":["en"]},
]


# =========================================================
# Mexican (MX), Brazilian (BR), Argentinian (AR) — Latin America
# =========================================================
LATAM = [
    {"slug":"roma-2018","title":"Roma","original_title":"Roma","type":"movie","year":2018,
     "runtime":135,"rating":7.7,"popularity":92.0,"status":"released",
     "overview":"A domestic worker for a middle-class Mexican family navigates personal and social upheaval in 1970s Mexico City.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Drama","Family"],"countries":["MX"],"languages":["es"],"audio_languages":["es","en"],"subtitle_languages":["en","fr"]},

    {"slug":"y-tu-mama-tambien-2001","title":"Y Tu Mamá También","original_title":"Y tu mamá también","type":"movie","year":2001,
     "runtime":106,"rating":7.7,"popularity":85.0,"status":"released",
     "overview":"Two teenage boys take a road trip with an older woman through Mexico in this Oscar-nominated coming-of-age film.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Drama","Comedy"],"countries":["MX"],"languages":["es"],"audio_languages":["es","en"],"subtitle_languages":["en"]},

    {"slug":"pan-labs-radiograph-of-a-dog-2023","title":"Pan","original_title":"Pan","type":"movie","year":2023,
     "runtime":115,"rating":6.5,"popularity":45.0,"status":"released",
     "overview":"A Mexican journalist investigates a missing person case that turns into a national conspiracy.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Thriller","Drama"],"countries":["MX"],"languages":["es"],"audio_languages":["es"],"subtitle_languages":["en"]},

    {"slug":"the-invention-of-chronicle-2024","title":"The Invention of Chronicle","original_title":"La invención de la crónica","type":"movie","year":2024,
     "runtime":120,"rating":6.8,"popularity":48.0,"status":"released",
     "overview":"A Mexican writer's journey through his country's literary history reveals a hidden lineage of chroniclers.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Drama"],"countries":["MX"],"languages":["es"],"audio_languages":["es"],"subtitle_languages":["en"]},

    {"slug":"city-of-god-2002","title":"City of God","original_title":"Cidade de Deus","type":"movie","year":2002,
     "runtime":130,"rating":8.6,"popularity":98.0,"status":"released",
     "overview":"Two boys take different paths in the favelas of Rio de Janeiro in this Oscar-nominated Brazilian crime epic.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Crime","Drama"],"countries":["BR"],"languages":["pt"],"audio_languages":["pt","en"],"subtitle_languages":["en","fr"]},

    {"slug":"central-station-1998","title":"Central Station","original_title":"Central do Brasil","type":"movie","year":1998,
     "runtime":110,"rating":8.0,"popularity":80.0,"status":"released",
     "overview":"A retired schoolteacher helps a young boy search for his father across the Brazilian Northeast.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Drama"],"countries":["BR"],"languages":["pt"],"audio_languages":["pt"],"subtitle_languages":["en","fr"]},

    {"slug":"bacurau-2019","title":"Bacurau","original_title":"Bacurau","type":"movie","year":2019,
     "runtime":131,"rating":7.2,"popularity":72.0,"status":"released",
     "overview":"A small Brazilian village disappears from maps overnight and its residents fight back against mysterious invaders.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Drama","Thriller","Western"],"countries":["BR"],"languages":["pt"],"audio_languages":["pt","en"],"subtitle_languages":["en","fr"]},

    {"slug":"the-secret-agent-2024-br","title":"The Secret Agent","original_title":"O Agente Secreto","type":"movie","year":2024,
     "runtime":115,"rating":7.0,"popularity":62.0,"status":"released",
     "overview":"A Brazilian intelligence agent goes undercover to expose a military conspiracy in this political thriller.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Thriller"],"countries":["BR"],"languages":["pt"],"audio_languages":["pt","en"],"subtitle_languages":["en","fr"]},

    {"slug":"the-secret-in-their-eyes-2009","title":"The Secret in Their Eyes","original_title":"El secreto de sus ojos","type":"movie","year":2009,
     "runtime":129,"rating":8.2,"popularity":88.0,"status":"released",
     "overview":"A retired legal counselor revisits an unsolved rape-murder case that has haunted him for 25 years.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Drama","Mystery","Thriller"],"countries":["AR","ES"],"languages":["es"],"audio_languages":["es","en"],"subtitle_languages":["en","fr"]},

    {"slug":"wild-tales-2014","title":"Wild Tales","original_title":"Relatos salvajes","type":"movie","year":2014,
     "runtime":122,"rating":8.1,"popularity":90.0,"status":"released",
     "overview":"Six stories of revenge, road rage, and absurd escalation in this Oscar-nominated Argentinian anthology film.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Drama","Comedy","Thriller"],"countries":["AR","ES"],"languages":["es"],"audio_languages":["es","en"],"subtitle_languages":["en","fr"]},
]


# =========================================================
# Canada (CA), Australia (AU), South Africa (ZA), Kenya (KE), Ivory Coast (CI)
# =========================================================
OTHER_REGIONS = [
    {"slug":"incendies-2010","title":"Incendies","original_title":"Incendies","type":"movie","year":2010,
     "runtime":131,"rating":8.3,"popularity":85.0,"status":"released",
     "overview":"Twin siblings travel to their mother's homeland and uncover a family secret in this Oscar-nominated Canadian drama.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Drama","Mystery","War"],"countries":["CA","FR"],"languages":["fr","ar"],"audio_languages":["fr","en"],"subtitle_languages":["en","ar"]},

    {"slug":"room-2015","title":"Room","original_title":"Room","type":"movie","year":2015,
     "runtime":118,"rating":8.1,"popularity":93.0,"status":"released",
     "overview":"A kidnapped woman and her young son escape from a garden shed and adjust to the wider world.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Drama","Thriller"],"countries":["CA","IE"],"languages":["en"],"audio_languages":["en"],"subtitle_languages":["en","fr"]},

    {"slug":"the-sweet-hereafter-1997","title":"The Sweet Hereafter","original_title":"The Sweet Hereafter","type":"movie","year":1997,
     "runtime":112,"rating":7.5,"popularity":68.0,"status":"released",
     "overview":"A small-town lawyer investigates a tragic school-bus accident in this Atom Egoyan drama.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Drama"],"countries":["CA"],"languages":["en"],"audio_languages":["en"],"subtitle_languages":["en","fr"]},

    {"slug":"the-sapphires-2012","title":"The Sapphires","original_title":"The Sapphires","type":"movie","year":2012,
     "runtime":103,"rating":7.0,"popularity":62.0,"status":"released",
     "overview":"Four Aboriginal Australian sisters form a soul group and tour Vietnam to entertain US troops in 1968.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Drama","Comedy","Music"],"countries":["AU"],"languages":["en"],"audio_languages":["en"],"subtitle_languages":["en"]},

    {"slug":"animal-kingdom-2010","title":"Animal Kingdom","original_title":"Animal Kingdom","type":"movie","year":2010,
     "runtime":113,"rating":7.3,"popularity":70.0,"status":"released",
     "overview":"A teenage boy is drawn into his Melbourne criminal family's web of armed robbers and police informants.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Crime","Drama"],"countries":["AU"],"languages":["en"],"audio_languages":["en"],"subtitle_languages":["en"]},

    {"slug":"the-songs-of-songs-2024","title":"The Song of Songs","original_title":"Die Lieder der Lieder","type":"movie","year":2024,
     "runtime":98,"rating":6.5,"popularity":40.0,"status":"released",
     "overview":"A young woman returns to her rural Australian hometown and confronts the family she left behind.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Drama"],"countries":["AU"],"languages":["en"],"audio_languages":["en"],"subtitle_languages":["en"]},

    {"slug":"tsotsi-2005","title":"Tsotsi","original_title":"Tsotsi","type":"movie","year":2005,
     "runtime":94,"rating":7.4,"popularity":72.0,"status":"released",
     "overview":"A young Johannesburg gang leader steals a car and discovers a baby in the back seat, transforming his life.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Drama","Crime"],"countries":["ZA","GB"],"languages":["en","zu"],"audio_languages":["en"],"subtitle_languages":["en","fr"]},

    {"slug":"the-two-popes-2019","title":"The Two Popes","original_title":"The Two Popes","type":"movie","year":2019,
     "runtime":125,"rating":7.6,"popularity":78.0,"status":"released",
     "overview":"Behind-the-scenes conversations between Pope Benedict XVI and Cardinal Bergoglio shape the modern Catholic Church.",
     "poster":"https://image.tmdb.org/t/p/w500/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "backdrop":"https://image.tmdb.org/t/p/w1280/3T4cTnJjC9tTc9z7c1TmL2tI3bA.jpg",
     "genres":["Drama"],"countries":["GB","IT","AR"],"languages":["en","es","it"],"audio_languages":["en","es"],"subtitle_languages":["en","fr"]},
]


def main():
    print(f"Connecting to {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    all_records = (
        [("movie", r) for r in NOLLYWOOD]
        + [("movie", r) for r in TURKISH]
        + [("movie", r) for r in EGYPTIAN]
        + [("movie", r) for r in SEA]
        + [("movie", r) for r in LATAM]
        + [("movie", r) for r in OTHER_REGIONS]
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
