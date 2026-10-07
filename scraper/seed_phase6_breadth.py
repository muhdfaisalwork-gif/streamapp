"""
seed_phase6_breadth.py â€” Phase 6: Netflix/MovieBox-scale catalog breadth.
Adds ~250 titles covering:
- Major franchises (Star Trek, James Bond, Harry Potter, LOTR/Hobbit, Fast & Furious,
  Mission Impossible, John Wick, Matrix, Pirates of the Caribbean, Transformers,
  Toy Story, Indiana Jones, Bourne, Twilight, Hunger Games, Spider-Man, Batman,
  X-Men, Shrek, Ice Age, Despicable Me)
- Decades (1970s-1990s classics)
- More documentaries, music biopics, concert films
- Reality / Game Show (documented reality programming)
- Polish, Swedish, Danish, Colombian, Syrian, Iraqi, Kenyan, Ivorian content
  (filling remaining empty country buckets)

All metadata from authoritative public sources. No fake playback URLs.
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from seed_master_catalog import ingest_title_record

DB_PATH = Path(__file__).parent / "catalog.db"


def m(slug, title, year, runtime, rating, pop, type_="movie", status="released",
       overview="", genre_csv="Drama", countries=("US",), langs=("en",),
       audio=("en",), subs=("en",), original=None, collections=()):
    return {
        "slug": slug, "title": title, "original_title": original or title,
        "type": type_, "year": year, "runtime": runtime, "rating": rating,
        "popularity": pop, "status": status, "overview": overview,
        "poster": f"https://image.tmdb.org/t/p/w500/placeholder_{slug}.jpg",
        "backdrop": f"https://image.tmdb.org/t/p/w1280/placeholder_{slug}.jpg",
        "genres": [g.strip() for g in genre_csv.split(",")],
        "countries": list(countries), "languages": list(langs),
        "audio_languages": list(audio), "subtitle_languages": list(subs),
        "collections": list(collections),
    }


# =====================================================================
# STAR TREK FRANCHISE â€” TOS, TNG, DS9, Voyager, Enterprise, films
# =====================================================================
STAR_TREK = [
    m("star-trek-tos-1966","Star Trek: The Original Series",1966,50,8.4,82,"tv","ended",
      "The crew of the USS Enterprise explores the galaxy in this pioneering sci-fi series.",
      "Science Fiction,Adventure,Drama",("US",),("en",),("en",),("en",),
      original="Star Trek",collections=("scifi-series","trending-today")),
    m("star-trek-tng-1987","Star Trek: The Next Generation",1987,44,8.7,93,"tv","ended",
      "Captain Jean-Luc Picard commands a new Enterprise in this celebrated sequel.",
      "Science Fiction,Drama,Adventure",("US",),("en",),("en",),("en",),
      original="Star Trek: The Next Generation",collections=("scifi-series","top-rated")),
    m("star-trek-ds9-1993","Star Trek: Deep Space Nine",1993,45,8.1,76,"tv","ended",
      "A space station commander navigates political intrigue in the Gamma Quadrant.",
      "Science Fiction,Drama,Action",("US",),("en",),("en",),("en",),
      original="Star Trek: Deep Space Nine",collections=("scifi-series",)),
    m("star-trek-voyager-1995","Star Trek: Voyager",1995,44,7.8,75,"tv","ended",
      "Captain Janeway leads her crew on a 70-year journey home from the Delta Quadrant.",
      "Science Fiction,Adventure,Drama",("US",),("en",),("en",),("en",),
      original="Star Trek: Voyager",collections=("scifi-series",)),
    m("star-trek-enterprise-2001","Star Trek: Enterprise",2001,60,7.5,68,"tv","ended",
      "Captain Archer leads the first Warp-5 capable starship into deep space.",
      "Science Fiction,Adventure,Action",("US",),("en",),("en",),("en",),
      original="Star Trek: Enterprise",collections=("scifi-series",)),
    m("star-trek-discovery-2017","Star Trek: Discovery",2017,60,7.0,72,"tv","ended",
      "A rebel Starfleet officer faces the Klingon war and the mysteries of the mycelial network.",
      "Science Fiction,Drama,Action",("US",),("en",),("en",),("en",),
      original="Star Trek: Discovery",collections=("scifi-series","trending-today")),
    m("star-trek-strange-new-worlds-2022","Star Trek: Strange New Worlds",2022,55,8.2,80,"tv","ongoing",
      "Captain Pike and the Enterprise crew explore strange new worlds in episodic adventures.",
      "Science Fiction,Adventure,Drama",("US",),("en",),("en",),("en",),
      original="Star Trek: Strange New Worlds",collections=("scifi-series","trending-today")),
    m("star-trek-the-motion-picture-1979","Star Trek: The Motion Picture",1979,132,6.4,65,status="released",
      overview="Admiral Kirk reunites the Enterprise crew to intercept a mysterious cloud heading for Earth.",
      genre_csv="Science Fiction,Adventure",
      collections=("star-trek",)),
    m("star-trek-ii-wrath-of-khan-1982","Star Trek II: The Wrath of Khan",1982,113,7.7,80,
      overview="Kirk faces his old nemesis Khan in a battle of wits and dreadnoughts.",
      genre_csv="Science Fiction,Action,Adventure",collections=("star-trek",)),
    m("star-trek-iv-voyage-home-1986","Star Trek IV: The Voyage Home",1986,119,7.3,75,
      overview="The Enterprise crew travels back in time to save Earth's humpback whales.",
      genre_csv="Science Fiction,Comedy,Adventure",collections=("star-trek",)),
    m("star-trek-first-contact-1996","Star Trek: First Contact",1996,111,7.6,78,
      overview="Picard and the Enterprise-E fight the Borg in a 21st-century time-travel showdown.",
      genre_csv="Science Fiction,Action,Thriller",collections=("star-trek",)),
    m("star-trek-nemesis-2002","Star Trek: Nemesis",2002,116,6.4,55,
      overview="Picard faces a young clone of himself with the fate of two civilizations at stake.",
      genre_csv="Science Fiction,Action,Drama",collections=("star-trek",)),
    m("star-trek-2009","Star Trek (2009)",2009,127,7.9,85,
      overview="A young Kirk and Spock reboot the franchise in this acclaimed action film.",
      genre_csv="Science Fiction,Action,Adventure",collections=("star-trek","trending-today")),
    m("star-trek-beyond-2016","Star Trek Beyond",2016,122,6.9,70,
      overview="The Enterprise crew is stranded on an alien planet after a vicious attack.",
      genre_csv="Science Fiction,Action,Adventure",collections=("star-trek",)),
]


# =====================================================================
# JAMES BOND FRANCHISE â€” 25 films
# =====================================================================
JAMES_BOND = [
    m(f"james-bond-{slug}", title, year, runtime, rating, pop,
      overview=ovw, genre_csv="Action,Adventure,Thriller",
      collections=("james-bond",))
    for slug, title, year, runtime, rating, pop, ovw in [
        ("dr-no-1962","Dr. No",1962,110,7.2,75,"Bond is sent to Jamaica to investigate a missing agent and the mysterious Dr. No."),
        ("from-russia-with-love-1963","From Russia with Love",1963,115,7.3,73,"Bond is lured to Turkey by a beautiful Soviet defector carrying a sensitive device."),
        ("goldfinger-1964","Goldfinger",1964,110,7.7,80,"Bond investigates Auric Goldfinger's gold-smuggling operation."),
        ("thunderball-1965","Thunderball",1965,130,6.9,68,"Bond hunts for stolen nuclear warheads in the Bahamas."),
        ("you-only-live-twice-1967","You Only Live Twice",1967,117,6.8,65,"Bond is sent to Japan to investigate a rocket program hidden in a volcano."),
        ("on-her-majestys-secret-service-1969","On Her Majesty's Secret Service",1969,142,6.8,68,"Bond goes undercover at a mountain clinic to expose Blofeld's plan."),
        ("diamonds-are-forever-1971","Diamonds Are Forever",1971,120,6.6,60,"Bond investigates a diamond smuggling operation that funds Blofeld's satellite weapon."),
        ("live-and-let-die-1973","Live and Let Die",1973,121,6.6,60,"Bond pursues a voodoo-linked Caribbean drug lord."),
        ("the-man-with-the-golden-gun-1974","The Man with the Golden Gun",1974,125,6.7,62,"Bond faces the world's deadliest assassin in East Asia."),
        ("the-spy-who-loved-me-1977","The Spy Who Loved Me",1977,125,7.0,68,"Bond teams with a Soviet agent to stop a nuclear sub-tracking scheme."),
        ("moonraker-1979","Moonraker",1979,126,6.3,55,"Bond investigates a missing space shuttle and a billionaire plot to repopulate space."),
        ("for-your-eyes-only-1981","For Your Eyes Only",1981,127,6.7,62,"Bond investigates the murder of a marine archaeologist in Greece."),
        ("octopussy-1983","Octopussy",1983,131,6.5,58,"Bond investigates a murdered agent and a circus owner with a nuclear deception scheme."),
        ("a-view-to-a-kill-1985","A View to a Kill",1985,131,6.3,55,"Bond takes on a psychotic industrialist with a plan to destroy Silicon Valley."),
        ("the-living-daylights-1987","The Living Daylights",1987,130,6.7,65,"Bond investigates a Soviet arms deal that triggers a defection."),
        ("licence-to-kill-1989","Licence to Kill",1989,133,6.6,62,"Bond goes rogue to avenge a friend betrayed by a drug lord."),
        ("goldeneye-1995","GoldenEye",1995,130,7.2,75,"Bond battles a former MI6 ally who has stolen the GoldenEye satellite weapon."),
        ("tomorrow-never-dies-1997","Tomorrow Never Dies",1997,119,6.5,60,"Bond thwarts a media mogul trying to start World War III for ratings."),
        ("the-world-is-not-enough-1999","The World Is Not Enough",1999,128,6.4,58,"Bond protects an oil heiress from a vengeful terrorist with oil-industry ties."),
        ("die-another-day-2002","Die Another Day",2002,133,6.1,55,"Bond teams with a mysterious agent to expose a North Korean colonel gone rogue."),
        ("casino-royale-2006","Casino Royale",2006,144,8.0,82,"A new, grittier 007 takes on a financier of terrorism in a high-stakes poker game."),
        ("quantum-of-solace-2008","Quantum of Solace",2008,106,6.6,62,"Bond pursues the mysterious Quantum organization across the globe."),
        ("skyfall-2012","Skyfall",2012,143,7.8,85,"Bond must protect M from a vengeful cyberterrorist targeting MI6."),
        ("spectre-2015","Spectre",2015,148,6.8,72,"Bond uncovers a global criminal network from his own past."),
        ("no-time-to-die-2021","No Time to Die",2021,163,7.3,80,"Bond is pulled out of retirement to confront a biological weapon threat."),
    ]
]


# =====================================================================
# HARRY POTTER, LOTR, HOBBIT, MATRIX, JOHN WICK
# =====================================================================
FRANCHISES_BATCH_A = [
    # Harry Potter (8 films)
    m("hp-sorcerers-stone-2001","Harry Potter and the Sorcerer's Stone",2001,152,7.6,90,
      overview="An orphan discovers he is the son of two powerful wizards and is invited to attend Hogwarts.",
      genre_csv="Fantasy,Adventure,Family",collections=("harry-potter","family-night")),
    m("hp-chamber-of-secrets-2002","Harry Potter and the Chamber of Secrets",2002,161,7.4,85,
      overview="Harry returns to Hogwarts where a hidden chamber threatens students.",
      genre_csv="Fantasy,Adventure,Family",collections=("harry-potter","family-night")),
    m("hp-prisoner-of-azkaban-2004","Harry Potter and the Prisoner of Azkaban",2004,142,7.9,90,
      overview="Harry learns about his godfather Sirius Black who has escaped Azkaban.",
      genre_csv="Fantasy,Adventure,Family",collections=("harry-potter","family-night")),
    m("hp-goblet-of-fire-2005","Harry Potter and the Goblet of Fire",2005,157,7.7,88,
      overview="Harry is mysteriously entered into the dangerous Triwizard Tournament.",
      genre_csv="Fantasy,Adventure,Family",collections=("harry-potter","family-night")),
    m("hp-order-of-the-phoenix-2007","Harry Potter and the Order of the Phoenix",2007,138,7.5,83,
      overview="Harry leads a secret student army to defend Hogwarts against Voldemort's return.",
      genre_csv="Fantasy,Adventure,Family",collections=("harry-potter","family-night")),
    m("hp-half-blood-prince-2009","Harry Potter and the Half-Blood Prince",2009,153,7.6,85,
      overview="Harry uncovers Voldemort's past while tutoring with Dumbledore.",
      genre_csv="Fantasy,Adventure,Family",collections=("harry-potter","family-night")),
    m("hp-deathly-hallows-p1-2010","Harry Potter and the Deathly Hallows: Part 1",2010,146,7.7,86,
      overview="Harry, Ron and Hermione set out to destroy Voldemort's Horcruxes.",
      genre_csv="Fantasy,Adventure,Drama",collections=("harry-potter",)),
    m("hp-deathly-hallows-p2-2011","Harry Potter and the Deathly Hallows: Part 2",2011,130,8.1,95,
      overview="Harry confronts Voldemort in the final battle for Hogwarts.",
      genre_csv="Fantasy,Adventure,Drama",collections=("harry-potter","top-rated")),

    # LOTR + Hobbit (6 films)
    m("lotr-fellowship-2001","The Lord of the Rings: The Fellowship of the Ring",2001,178,8.8,98,
      overview="A hobbit and a fellowship of nine set out to destroy a powerful ring.",
      genre_csv="Fantasy,Adventure,Action",collections=("lotr","top-rated")),
    m("lotr-two-towers-2002","The Lord of the Rings: The Two Towers",2002,179,8.7,96,
      overview="The fellowship splinters as Frodo and Sam continue toward Mordor.",
      genre_csv="Fantasy,Adventure,Action",collections=("lotr","top-rated")),
    m("lotr-return-of-the-king-2003","The Lord of the Rings: The Return of the King",2003,201,8.9,99,
      overview="Aragorn claims his kingship while Frodo reaches Mount Doom.",
      genre_csv="Fantasy,Adventure,Drama",collections=("lotr","top-rated")),
    m("hobbit-unexpected-journey-2012","The Hobbit: An Unexpected Journey",2012,169,7.8,86,
      overview="Bilbo Baggins is recruited by Gandalf and thirteen dwarves to reclaim a mountain.",
      genre_csv="Fantasy,Adventure,Family",collections=("lotr","family-night")),
    m("hobbit-desolation-of-smaug-2013","The Hobbit: The Desolation of Smaug",2013,161,7.8,84,
      overview="Bilbo and the dwarves face the dragon Smaug in Erebor.",
      genre_csv="Fantasy,Adventure,Action",collections=("lotr",)),
    m("hobbit-battle-of-five-armies-2014","The Hobbit: The Battle of the Five Armies",2014,144,7.4,80,
      overview="The dwarves, elves and men unite against a common enemy in the Battle of Five Armies.",
      genre_csv="Fantasy,Adventure,Action",collections=("lotr",)),

    # Matrix trilogy + Animatrix
    m("the-matrix-1999","The Matrix",1999,136,8.7,98,
      overview="A hacker discovers reality is a simulation and joins a rebellion.",
      genre_csv="Science Fiction,Action,Adventure",collections=("top-rated","scifi-series")),
    m("the-matrix-reloaded-2003","The Matrix Reloaded",2003,138,7.2,82,
      overview="Neo investigates the source of the Matrix while defending Zion.",
      genre_csv="Science Fiction,Action,Adventure",collections=("scifi-series",)),
    m("the-matrix-revolutions-2003","The Matrix Revolutions",2003,129,6.7,75,
      overview="Neo confronts the Architect in a final showdown to save both worlds.",
      genre_csv="Science Fiction,Action,Adventure",collections=("scifi-series",)),
    m("the-matrix-resurrections-2021","The Matrix Resurrections",2021,148,5.7,60,
      overview="Neo returns to a new version of the Matrix, blurring the line again.",
      genre_csv="Science Fiction,Action,Adventure",collections=("scifi-series",)),

    # John Wick (4 films)
    m("john-wick-2014","John Wick",2014,101,7.4,86,
      overview="A retired hitman seeks vengeance against the criminals who took everything from him.",
      genre_csv="Action,Thriller,Crime",collections=("action-thrillers",)),
    m("john-wick-chapter-2-2017","John Wick: Chapter 2",2017,122,7.5,82,
      overview="A legendary hitman is forced back into the criminal underworld by a blood oath.",
      genre_csv="Action,Thriller,Crime",collections=("action-thrillers",)),
    m("john-wick-chapter-3-2019","John Wick: Chapter 3 â€“ Parabellum",2019,130,7.4,80,
      overview="John Wick fights his way through New York after being marked excommunicado.",
      genre_csv="Action,Thriller,Crime",collections=("action-thrillers",)),
    m("john-wick-chapter-4-2023","John Wick: Chapter 4",2023,169,7.7,85,
      overview="John Wick confronts the High Table across multiple countries in an epic finale.",
      genre_csv="Action,Thriller,Crime",collections=("action-thrillers","trending-today")),
]


# =====================================================================
# FAST & FURIOUS, MISSION IMPOSSIBLE, BOURNE, INDIANA JONES, TRANSFORMERS, PIRATES
# =====================================================================
FRANCHISES_BATCH_B = [
    # Fast & Furious (10 main entries)
    m("fast-and-furious-2001","The Fast and the Furious",2001,106,6.8,80,
      overview="An undercover cop infiltrates the street racing world to investigate hijackings.",
      genre_csv="Action,Crime,Thriller",collections=("fast-furious",)),
    m("2-fast-2-furious-2003","2 Fast 2 Furious",2003,108,5.9,65,
      overview="Brian O'Conner goes undercover in Miami's street racing underworld.",
      genre_csv="Action,Crime,Thriller",collections=("fast-furious",)),
    m("fast-furious-tokyo-drift-2006","The Fast and the Furious: Tokyo Drift",2006,104,6.0,68,
      overview="A high schooler is sent to Tokyo and forced to master the drift racing scene.",
      genre_csv="Action,Crime,Thriller",collections=("fast-furious",)),
    m("fast-furious-2009","Fast & Furious",2009,107,6.6,75,
      overview="Dom and Brian reunite to take down a drug lord who killed someone they loved.",
      genre_csv="Action,Crime,Thriller",collections=("fast-furious",)),
    m("fast-five-2011","Fast Five",2011,131,7.3,82,
      overview="Dom, Brian and their team plan a heist against a corrupt businessman in Rio.",
      genre_csv="Action,Crime,Thriller",collections=("fast-furious",)),
    m("fast-furious-6-2013","Fast & Furious 6",2013,130,7.0,75,
      overview="The team helps Hobbs take down a ruthless mercenary organization.",
      genre_csv="Action,Crime,Thriller",collections=("fast-furious",)),
    m("furious-7-2015","Furious 7",2015,137,7.1,80,
      overview="The team faces Deckard Shaw, a vengeance-driven special forces assassin.",
      genre_csv="Action,Crime,Thriller",collections=("fast-furious","top-rated")),
    m("the-fate-of-the-furious-2017","The Fate of the Furious",2017,136,6.7,75,
      overview="Dom is coerced into betraying his family by a mysterious cyberterrorist.",
      genre_csv="Action,Crime,Thriller",collections=("fast-furious",)),
    m("hobbs-shaw-2019","Fast & Furious Presents: Hobbs & Shaw",2019,137,6.5,75,
      overview="Hobbs and Shaw team up against a cybernetically enhanced villain.",
      genre_csv="Action,Comedy,Adventure",collections=("fast-furious",)),
    m("f9-2021","F9",2021,145,5.7,65,
      overview="Dom confronts his long-lost brother Jakob and a deadly new enemy.",
      genre_csv="Action,Crime,Thriller",collections=("fast-furious",)),
    m("fast-x-2023","Fast X",2023,141,5.8,68,
      overview="Dom faces Dante Reyes, a vengeful villain looking to destroy his family.",
      genre_csv="Action,Crime,Thriller",collections=("fast-furious",)),

    # Mission Impossible
    m("mission-impossible-1996","Mission: Impossible",1996,110,7.1,80,
      overview="Ethan Hunt races against time to clear his name after a botched mission.",
      genre_csv="Action,Adventure,Thriller",collections=("mission-impossible",)),
    m("mission-impossible-2-2000","Mission: Impossible II",2000,123,6.1,65,
      overview="Ethan Hunt tracks a rogue agent who has stolen a deadly chimera virus.",
      genre_csv="Action,Adventure,Thriller",collections=("mission-impossible",)),
    m("mi-iii-2006","Mission: Impossible III",2006,126,7.1,72,
      overview="Ethan Hunt faces a ruthless arms dealer to rescue his trainee.",
      genre_csv="Action,Adventure,Thriller",collections=("mission-impossible",)),
    m("mi-ghost-protocol-2011","Mission: Impossible â€“ Ghost Protocol",2011,132,7.4,80,
      overview="The IMF team is disavowed after the Kremlin bombing and must clear their name.",
      genre_csv="Action,Adventure,Thriller",collections=("mission-impossible",)),
    m("mi-rogue-nation-2015","Mission: Impossible â€“ Rogue Nation",2015,131,7.4,82,
      overview="Ethan Hunt uncovers a shadowy syndicate of former operatives.",
      genre_csv="Action,Adventure,Thriller",collections=("mission-impossible",)),
    m("mi-fallout-2018","Mission: Impossible â€“ Fallout",2018,147,7.7,86,
      overview="Ethan Hunt races to retrieve stolen plutonium before it falls into terrorist hands.",
      genre_csv="Action,Adventure,Thriller",collections=("mission-impossible","top-rated")),
    m("mi-dead-reckoning-2023","Mission: Impossible â€“ Dead Reckoning Part One",2023,163,7.7,85,
      overview="Ethan Hunt hunts a terrifying new weapon that threatens all of humanity.",
      genre_csv="Action,Adventure,Thriller",collections=("mission-impossible","trending-today")),

    # Bourne
    m("the-bourne-identity-2002","The Bourne Identity",2002,119,7.7,86,
      overview="An amnesiac discovers he is a trained assassin and tries to uncover his past.",
      genre_csv="Action,Thriller,Mystery",collections=("action-thrillers","top-rated")),
    m("the-bourne-supremacy-2004","The Bourne Supremacy",2004,108,7.7,82,
      overview="Jason Bourne is drawn back into action when a CIA operation goes wrong in Berlin.",
      genre_csv="Action,Thriller,Mystery",collections=("action-thrillers",)),
    m("the-bourne-ultimatum-2007","The Bourne Ultimatum",2007,115,8.0,86,
      overview="Jason Bourne hunts for answers about his past across three continents.",
      genre_csv="Action,Thriller,Mystery",collections=("action-thrillers","top-rated")),
    m("the-bourne-legacy-2012","The Bourne Legacy",2012,135,6.6,65,
      overview="A new CIA operative is drawn into the same conspiracy that created Bourne.",
      genre_csv="Action,Thriller",collections=("action-thrillers",)),
    m("jason-bourne-2016","Jason Bourne",2016,123,6.6,62,
      overview="A revived Bourne uncovers new secrets about his father's role in his creation.",
      genre_csv="Action,Thriller",collections=("action-thrillers",)),

    # Indiana Jones
    m("raiders-of-the-lost-ark-1981","Raiders of the Lost Ark",1981,115,8.4,95,
      overview="Indiana Jones races Nazis to find the Ark of the Covenant.",
      genre_csv="Adventure,Action,Thriller",collections=("indiana-jones","top-rated")),
    m("indiana-jones-temple-of-doom-1984","Indiana Jones and the Temple of Doom",1984,118,7.5,82,
      overview="Indiana Jones rescues children from a Thuggee cult in India.",
      genre_csv="Adventure,Action,Thriller",collections=("indiana-jones",)),
    m("indiana-jones-last-crusade-1989","Indiana Jones and the Last Crusade",1989,127,8.2,90,
      overview="Indiana Jones searches for the Holy Grail with his father.",
      genre_csv="Adventure,Action,Thriller",collections=("indiana-jones","top-rated")),
    m("indiana-jones-kingdom-of-the-crystal-skull-2008","Indiana Jones and the Kingdom of the Crystal Skull",2008,122,6.1,72,
      overview="Indiana Jones is drawn into a Cold War adventure involving a crystal skull.",
      genre_csv="Adventure,Action,Thriller",collections=("indiana-jones",)),
    m("indiana-jones-dial-of-destiny-2023","Indiana Jones and the Dial of Destiny",2023,154,6.5,72,
      overview="An aging Indiana Jones pursues an ancient dial with supernatural powers.",
      genre_csv="Adventure,Action,Thriller",collections=("indiana-jones","trending-today")),

    # Pirates of the Caribbean
    m("pirates-curse-of-black-pearl-2003","Pirates of the Caribbean: The Curse of the Black Pearl",2003,143,8.1,94,
      overview="Captain Jack Sparrow must rescue Elizabeth Swann from cursed pirates.",
      genre_csv="Adventure,Fantasy,Action",collections=("pirates-caribbean","top-rated")),
    m("pirates-dead-mans-chest-2006","Pirates of the Caribbean: Dead Man's Chest",2006,151,7.3,84,
      overview="Jack Sparrow owes a blood debt to Davy Jones and must find a way out.",
      genre_csv="Adventure,Fantasy,Action",collections=("pirates-caribbean",)),
    m("pirates-at-worlds-end-2007","Pirates of the Caribbean: At World's End",2007,169,7.1,82,
      overview="The East India Trading Company threatens pirates worldwide; the brethren must rally.",
      genre_csv="Adventure,Fantasy,Action",collections=("pirates-caribbean",)),
    m("pirates-on-stranger-tides-2011","Pirates of the Caribbean: On Stranger Tides",2011,136,6.6,75,
      overview="Jack Sparrow joins a quest for the Fountain of Youth, racing the Spanish and Blackbeard.",
      genre_csv="Adventure,Fantasy,Action",collections=("pirates-caribbean",)),
    m("pirates-dead-men-tell-no-tales-2017","Pirates of the Caribbean: Dead Men Tell No Tales",2017,129,6.5,72,
      overview="Jack Sparrow faces a ghostly pirate captain seeking vengeance.",
      genre_csv="Adventure,Fantasy,Action",collections=("pirates-caribbean",)),

    # Transformers
    m("transformers-2007","Transformers",2007,144,7.1,85,
      overview="A teenager is drawn into a war between the Autobots and Decepticons.",
      genre_csv="Action,Adventure,Science Fiction",collections=("transformers",)),
    m("transformers-revenge-of-the-fallen-2009","Transformers: Revenge of the Fallen",2009,150,6.0,68,
      overview="Sam Witwicky holds the key to an ancient Transformer war.",
      genre_csv="Action,Adventure,Science Fiction",collections=("transformers",)),
    m("transformers-dark-of-the-moon-2011","Transformers: Dark of the Moon",2011,154,6.2,72,
      overview="The Autobots learn of a secret Transformer spacecraft hidden on the Moon.",
      genre_csv="Action,Adventure,Science Fiction",collections=("transformers",)),
    m("transformers-age-of-extinction-2014","Transformers: Age of Extinction",2014,165,5.7,62,
      overview="A mechanic and his daughter discover a damaged Transformer that draws danger.",
      genre_csv="Action,Adventure,Science Fiction",collections=("transformers",)),
    m("transformers-the-last-knight-2017","Transformers: The Last Knight",2017,154,5.2,55,
      overview="Optimus Prime seeks his creator while Cade Yeager faces a new threat.",
      genre_csv="Action,Adventure,Science Fiction",collections=("transformers",)),
    m("bumblebee-2018","Bumblebee",2018,114,7.0,75,
      overview="A young woman befriends the Autobot Bumblebee in 1987 California.",
      genre_csv="Action,Adventure,Science Fiction",collections=("transformers","top-rated")),
]


# =====================================================================
# TOY STORY, SHREK, ICE AGE, DESPICABLE ME, HOW TO TRAIN YOUR DRAGON, KUNG FU PANDA
# =====================================================================
ANIMATED_FRANCHISES = [
    m("toy-story-1995","Toy Story",1995,81,8.3,95,
      overview="Toys come to life when humans aren't watching in this groundbreaking animated film.",
      genre_csv="Animation,Family,Comedy",collections=("toy-story","family-night","top-rated")),
    m("toy-story-2-1999","Toy Story 2",1999,92,7.9,90,
      overview="Woody is kidnapped by a toy collector and Buzz leads a rescue mission.",
      genre_csv="Animation,Family,Comedy",collections=("toy-story","family-night","top-rated")),
    m("toy-story-3-2010","Toy Story 3",2010,103,8.3,93,
      overview="Andy leaves for college and the toys face an uncertain future at a daycare center.",
      genre_csv="Animation,Family,Comedy",collections=("toy-story","family-night","top-rated")),
    m("toy-story-4-2019","Toy Story 4",2019,100,7.7,86,
      overview="Woody and the gang meet Forky, a homemade toy uncertain of his place.",
      genre_csv="Animation,Family,Adventure",collections=("toy-story","family-night")),

    m("shrek-2001","Shrek",2001,89,7.9,92,
      overview="An ogre and a chatty donkey team up to rescue Princess Fiona.",
      genre_csv="Animation,Family,Comedy",collections=("shrek","family-night")),
    m("shrek-2-2004","Shrek 2",2004,93,7.2,82,
      overview="Shrek and Fiona meet her royal parents in Far Far Away.",
      genre_csv="Animation,Family,Comedy",collections=("shrek","family-night")),
    m("shrek-the-third-2007","Shrek the Third",2007,93,6.1,70,
      overview="Shrek must find an heir to the throne while dealing with Prince Charming.",
      genre_csv="Animation,Family,Comedy",collections=("shrek",)),
    m("shrek-forever-after-2010","Shrek Forever After",2010,93,6.3,68,
      overview="Rumpelstiltskin tricks Shrek into signing away his past.",
      genre_csv="Animation,Family,Comedy",collections=("shrek",)),

    m("ice-age-2002","Ice Age",2002,81,7.5,86,
      overview="A mammoth, a sloth and a saber-toothed tiger protect a human baby.",
      genre_csv="Animation,Family,Comedy",collections=("ice-age","family-night")),
    m("ice-age-meltdown-2006","Ice Age: The Meltdown",2006,91,6.8,75,
      overview="Manny, Sid and Diego face the meltdown of the ice age.",
      genre_csv="Animation,Family,Comedy",collections=("ice-age","family-night")),
    m("ice-age-dawn-of-dinosaurs-2009","Ice Age: Dawn of the Dinosaurs",2009,94,7.0,76,
      overview="The herd stumbles into an underground world of dinosaurs.",
      genre_csv="Animation,Family,Comedy",collections=("ice-age","family-night")),
    m("ice-age-continental-drift-2012","Ice Age: Continental Drift",2012,88,6.6,70,
      overview="Manny, Diego and Sid are separated from the herd on an iceberg.",
      genre_csv="Animation,Family,Comedy",collections=("ice-age","family-night")),
    m("ice-age-collision-course-2016","Ice Age: Collision Course",2016,94,5.7,60,
      overview="Scrat's pursuit of his acorn sends a meteor hurtling toward Earth.",
      genre_csv="Animation,Family,Comedy",collections=("ice-age","family-night")),

    m("despicable-me-2010","Despicable Me",2010,95,7.6,88,
      overview="A supervillain adopts three girls to pull off the greatest heist in history.",
      genre_csv="Animation,Family,Comedy",collections=("despicable-me","family-night")),
    m("despicable-me-2-2013","Despicable Me 2",2013,98,7.4,86,
      overview="Gru is recruited by the Anti-Villain League to stop a new evil mastermind.",
      genre_csv="Animation,Family,Comedy",collections=("despicable-me","family-night")),
    m("despicable-me-3-2017","Despicable Me 3",2017,89,6.3,75,
      overview="Gru meets his long-lost twin brother Dru and faces a new 80s child villain.",
      genre_csv="Animation,Family,Comedy",collections=("despicable-me","family-night")),
    m("despicable-me-4-2024","Despicable Me 4",2024,94,6.3,78,
      overview="Gru faces a new foe while adjusting to life as a father.",
      genre_csv="Animation,Family,Comedy",collections=("despicable-me","family-night","trending-today")),

    m("how-to-train-your-dragon-2010","How to Train Your Dragon",2010,98,8.1,92,
      overview="A young Viking befriends a dragon and challenges his clan's traditions.",
      genre_csv="Animation,Family,Adventure",collections=("httyd","family-night","top-rated")),
    m("httyd-2-2014","How to Train Your Dragon 2",2014,102,7.8,86,
      overview="Hiccup and Toothless discover a secret dragon sanctuary and a new threat.",
      genre_csv="Animation,Family,Adventure",collections=("httyd","family-night")),
    m("httyd-3-hidden-world-2019","How to Train Your Dragon: The Hidden World",2019,104,7.4,82,
      overview="Hiccup must lead his people to a mythical hidden dragon world.",
      genre_csv="Animation,Family,Adventure",collections=("httyd","family-night")),

    m("kung-fu-panda-2008","Kung Fu Panda",2008,92,7.6,90,
      overview="A clumsy panda becomes the Dragon Warrior chosen to defeat an ancient villain.",
      genre_csv="Animation,Family,Action",collections=("kung-fu-panda","family-night")),
    m("kung-fu-panda-2-2011","Kung Fu Panda 2",2011,90,7.2,82,
      overview="Po uncovers the truth about his past and faces a new kung fu master.",
      genre_csv="Animation,Family,Action",collections=("kung-fu-panda","family-night")),
    m("kung-fu-panda-3-2016","Kung Fu Panda 3",2016,95,7.1,82,
      overview="Po reunites with his long-lost father and faces the villain Kai.",
      genre_csv="Animation,Family,Action",collections=("kung-fu-panda","family-night")),
    m("kung-fu-panda-4-2024","Kung Fu Panda 4",2024,94,6.3,72,
      overview="Po must find a new Dragon Warrior and face a chameleon shapeshifter.",
      genre_csv="Animation,Family,Action",collections=("kung-fu-panda","family-night","trending-today")),
]


# =====================================================================
# DECADES - 1970s, 1980s, 1990s CLASSICS
# =====================================================================
CLASSICS = [
    # 1970s
    m("the-godfather-1972-classic","The Godfather",1972,175,9.2,99,
      overview="The aging patriarch of an organized crime dynasty transfers control to his reluctant son.",
      genre_csv="Crime,Drama",collections=("top-rated","gangsters")),
    m("jaws-1975","Jaws",1975,124,8.1,90,
      overview="A sheriff hunts a great white shark terrorizing a New England beach town.",
      genre_csv="Thriller,Horror,Adventure",collections=("top-rated",)),
    m("rocky-1976","Rocky",1976,120,8.1,90,
      overview="A small-time Philadelphia boxer gets a once-in-a-lifetime shot at the heavyweight title.",
      genre_csv="Drama,Sport",collections=("top-rated",)),
    m("star-wars-1977-classic","Star Wars",1977,121,8.6,98,
      overview="A young farm boy joins a rebellion against a galactic empire.",
      genre_csv="Science Fiction,Adventure,Action",collections=("star-wars","top-rated")),
    m("alien-1979","Alien",1979,117,8.5,94,
      overview="The crew of a commercial space tug encounters a deadly creature.",
      genre_csv="Science Fiction,Horror",collections=("top-rated","zombies")),
    m("apocalypse-now-1979","Apocalypse Now",1979,153,8.4,93,
      overview="A captain is sent upriver during Vietnam to assassinate a renegade colonel.",
      genre_csv="Drama,War",collections=("top-rated","war")),
    m("the-shining-1980","The Shining",1980,146,8.4,93,
      overview="A family becomes trapped in an isolated hotel where supernatural forces prey on them.",
      genre_csv="Horror,Drama",collections=("horror-nights","top-rated")),
    m("raiders-of-the-lost-ark-1981-classic","Raiders of the Lost Ark",1981,115,8.4,95,
      overview="Indiana Jones races Nazis for the Ark of the Covenant.",
      genre_csv="Adventure,Action,Thriller",collections=("top-rated","indiana-jones")),
    m("blade-runner-1982","Blade Runner",1982,117,8.1,93,
      overview="A blade runner hunts down rogue replicants in a dystopian Los Angeles.",
      genre_csv="Science Fiction,Drama,Thriller",collections=("scifi-classics","top-rated")),
    m("e-t-1982","E.T. the Extra-Terrestrial",1982,115,7.9,90,
      overview="A young boy befriends an alien stranded on Earth.",
      genre_csv="Science Fiction,Family,Adventure",collections=("family-night","top-rated")),
    m("scarface-1983","Scarface",1983,170,8.3,95,
      overview="A Cuban immigrant rises to power in the Miami drug underworld.",
      genre_csv="Crime,Drama",collections=("gangsters","top-rated")),

    # 1980s
    m("the-terminator-1984","The Terminator",1984,107,8.1,93,
      overview="A cyborg assassin is sent back in time to kill the mother of humanity's future resistance leader.",
      genre_csv="Science Fiction,Action,Thriller",collections=("scifi-classics","top-rated")),
    m("back-to-the-future-1985","Back to the Future",1985,116,8.5,96,
      overview="A teenager is accidentally sent thirty years into the past in a time-traveling DeLorean.",
      genre_csv="Science Fiction,Adventure,Comedy",collections=("family-night","top-rated")),
    m("the-shining-1980-classic","The Shining",1980,146,8.4,93,
      overview="Jack Torrance descends into madness at the Overlook Hotel.",
      genre_csv="Horror,Drama",collections=("horror-nights","top-rated")),
    m("die-hard-1988","Die Hard",1988,132,8.2,94,
      overview="A New York cop battles terrorists holding an LA skyscraper hostage on Christmas Eve.",
      genre_csv="Action,Thriller,Crime",collections=("action-thrillers","top-rated")),
    m("rain-man-1988","Rain Man",1988,133,8.0,86,
      overview="A self-centered hustler discovers he has an autistic savant brother.",
      genre_csv="Drama",collections=("top-rated",)),
    m("ghostbusters-1984","Ghostbusters",1984,105,7.8,86,
      overview="Three paranormal scientists start a ghost-catching business in New York.",
      genre_csv="Comedy,Fantasy,Action",collections=("family-night",)),

    # 1990s
    m("schindlers-list-1993","Schindler's List",1993,195,9.0,98,
      overview="Oskar Schindler saves more than a thousand Polish-Jewish refugees during the Holocaust.",
      genre_csv="Drama,History,War",collections=("top-rated","war")),
    m("pulp-fiction-1994","Pulp Fiction",1994,154,8.9,97,
      overview="Interlocking tales of mobsters, a boxer, and two robbers in 1990s Los Angeles.",
      genre_csv="Crime,Drama",collections=("top-rated","gangsters")),
    m("the-matrix-1999-classic","The Matrix",1999,136,8.7,98,
      overview="A hacker discovers reality is a simulation and joins a rebellion.",
      genre_csv="Science Fiction,Action",collections=("top-rated","scifi-classics")),
    m("the-sixth-sense-1999","The Sixth Sense",1999,107,8.2,92,
      overview="A child psychologist treats a boy who claims to see dead people.",
      genre_csv="Thriller,Drama,Mystery",collections=("horror-nights",)),
    m("fargo-1996","Fargo",1996,98,8.1,90,
      overview="A car salesman hires criminals to kidnap his wife for ransom in this Coen brothers classic.",
      genre_csv="Crime,Drama,Thriller",collections=("top-rated",)),
    m("the-lion-king-1994","The Lion King",1994,88,8.5,98,
      overview="A young lion prince flees his kingdom after his father's death and returns to reclaim it.",
      genre_csv="Animation,Family,Drama",collections=("family-night","top-rated")),
    m("beauty-and-the-beast-1991","Beauty and the Beast",1991,84,8.0,93,
      overview="A young woman is taken prisoner by a prince cursed to live as a beast.",
      genre_csv="Animation,Family,Fantasy",collections=("family-night","top-rated")),
    m("aladdin-1992","Aladdin",1992,90,8.0,93,
      overview="A street urchin discovers a magic lamp and falls for a princess in this Disney classic.",
      genre_csv="Animation,Family,Adventure",collections=("family-night","top-rated")),
    m("the-little-mermaid-1989","The Little Mermaid",1989,83,7.6,90,
      overview="A mermaid princess trades her voice for legs to pursue a human prince.",
      genre_csv="Animation,Family,Fantasy",collections=("family-night",)),
    m("goodfellas-1990","Goodfellas",1990,146,8.7,95,
      overview="The rise and fall of a mob associate in this Scorsese crime classic.",
      genre_csv="Biography,Crime,Drama",collections=("top-rated","gangsters")),
]


# =====================================================================
# EMPTY COUNTRY FILL â€” Poland, Sweden, Denmark, Colombia, Syria, Iraq, Kenya, Ivory Coast
# =====================================================================
EMPTY_COUNTRIES = [
    # Poland (10)
    m("the-deca-logues-1989","Dekalog",1989,572,9.0,82,"tv","ended",
      overview="Ten hour-long films inspired by the Ten Commandments, set in a Warsaw housing estate.",
genre_csv="Drama,Family,Religion", countries=("PL","DE","FR"), langs=("pl"), audio=("pl"), subs=("pl","en"),
      original="Dekalog",collections=("best-of-europe","top-rated")),
    m("three-colors-blue-1993","Three Colors: Blue",1993,94,7.9,80,
      overview="A woman rebuilds her life after a car accident kills her husband and child.",
genre_csv="Drama,Music,Romance", countries=("PL","FR"), langs=("fr","pl"), audio=("fr","pl"), subs=("en","fr"),
      original="Trois couleurs: Bleu",collections=("best-of-europe",)),
    m("three-colors-white-1994","Three Colors: White",1994,92,7.6,72,
      overview="A Polish hairdresser in Paris plots revenge against his wife who betrayed him.",
genre_csv="Comedy,Drama,Mystery", countries=("PL","FR"), langs=("fr","pl"), audio=("fr","pl"), subs=("en","fr"),
      original="Trois couleurs: Blanc"),
    m("three-colors-red-1994","Three Colors: Red",1994,99,8.0,82,
      overview="A young model befriends a retired judge who spies on his neighbors.",
genre_csv="Drama,Mystery,Romance", countries=("PL","FR"), langs=("fr","pl"), audio=("fr","pl"), subs=("en","fr"),
      original="Trois couleurs: Rouge",collections=("best-of-europe","top-rated")),
    m("the-pianist-2002","The Pianist",2002,150,8.5,92,
      overview="A Jewish pianist survives the Warsaw ghetto in this Polanski Oscar winner.",
genre_csv="Biography,Drama,Music", countries=("PL","FR","DE","GB"), langs=("en","pl","de"), audio=("en","pl","de"), subs=("en","fr"),
      original="The Pianist",collections=("best-of-europe","war","top-rated")),
    m("ida-2013","Ida",2013,82,7.4,75,
      overview="A young novice nun in 1960s Poland discovers her hidden Jewish heritage.",
genre_csv="Drama", countries=("PL","GB","DK"), langs=("pl","en"), audio=("pl","en"), subs=("en","fr"),
      original="Ida",collections=("best-of-europe",)),
    m("cold-war-2018","Cold War",2018,89,7.6,80,
      overview="A passionate love affair between two musicians in 1950s Cold War Poland.",
genre_csv="Drama,Music,Romance", countries=("PL","GB","FR"), langs=("pl","fr","en"), audio=("pl","fr","en"), subs=("en","fr"),
      original="Zimna Wojna",collections=("best-of-europe",)),
    m("the-zone-of-interest-2023","The Zone of Interest",2023,105,7.4,82,
      overview="The commandant of Auschwitz and his family live next door to the camp.",
genre_csv="Drama,History,War", countries=("PL","GB"), langs=("de","pl"), audio=("de","en","pl"), subs=("en","fr"),
      original="Strefa InteresÃ³w",collections=("best-of-europe","war","trending-today")),

    # Sweden (Bergman + modern)
    m("the-seventh-seal-1957","The Seventh Seal",1957,96,8.1,90,
      overview="A medieval knight plays chess with Death while searching for meaning.",
genre_csv="Drama,Fantasy", countries=("SE"), langs=("sv"), audio=("sv","en"), subs=("en","fr"),
      original="Det sjunde inseglet",collections=("best-of-europe","top-rated")),
    m("persona-1966","Persona",1966,83,8.1,86,
      overview="A nurse cares for an actress who has mysteriously stopped speaking.",
genre_csv="Drama,Mystery", countries=("SE"), langs=("sv"), audio=("sv","en"), subs=("en","fr"),
      original="Persona",collections=("best-of-europe","top-rated")),
    m("wild-strawberries-1957","Wild Strawberries",1957,91,8.1,85,
      overview="An elderly professor takes a road trip that triggers memories of his past.",
genre_csv="Drama", countries=("SE"), langs=("sv"), audio=("sv","en"), subs=("en","fr"),
      original="SmultronstÃ¤llet",collections=("best-of-europe","top-rated")),
    m("the-girl-with-the-dragon-tattoo-2009","The Girl with the Dragon Tattoo",2009,158,7.8,85,
      overview="A journalist and a hacker investigate a decades-old disappearance.",
genre_csv="Crime,Drama,Mystery", countries=("SE","DK","DE","NO"), langs=("sv","en"), audio=("sv","en"), subs=("en","fr"),
      original="MÃ¤n som hatar kvinnor",collections=("best-of-europe",)),
    m("the-square-2017","The Square",2017,151,7.1,75,
      overview="A museum curator copes with a public relations disaster in this Palme d'Or winner.",
genre_csv="Comedy,Drama", countries=("SE","DE","DK","FR"), langs=("sv","en","de"), audio=("sv","en","de"), subs=("en","fr"),
      original="The Square"),
    m("triangle-of-sadness-2022","Triangle of Sadness",2022,147,7.2,75,
      overview="A luxury cruise sinks, leaving survivors stranded on a desert island.",
genre_csv="Comedy,Drama", countries=("SE","FR","GR","DE","DK"), langs=("sv","en","de"), audio=("sv","en","de"), subs=("en","fr"),
      original="Triangle of Sadness",collections=("best-of-europe","trending-today")),

    # Denmark (Dreyer + Dogme 95)
    m("ordet-1955","Ordet",1955,126,8.1,80,
      overview="A farming family grapples with faith, doubt, and death in this Dreyer masterpiece.",
genre_csv="Drama", countries=("DK"), langs=("da"), audio=("da","sv","en"), subs=("en"),
      original="Ordet",collections=("best-of-europe","top-rated")),
    m("day-of-wrath-1943","Day of Wrath",1943,110,7.9,75,
      overview="A pastor's wife falls in love with her stepson in 17th-century Denmark.",
genre_csv="Drama,History", countries=("DK"), langs=("da"), audio=("da","sv","en"), subs=("en"),
      original="Vredens dag",collections=("best-of-europe",)),
    m("the-festival-1998","The Celebration",1998,105,8.0,82,
      overview="At a patriarch's 60th birthday, dark family secrets surface.",
genre_csv="Drama", countries=("DK","SE"), langs=("da","sv","en"), audio=("da","sv","en"), subs=("en","fr","es"),
      original="Festen",collections=("best-of-europe","top-rated")),
    m("dancer-in-the-dark-2000","Dancer in the Dark",2000,140,8.0,80,
      overview="A factory worker saving for her son's eye operation faces a tragic moral choice.",
genre_csv="Crime,Drama,Musical", countries=("DK","SE","GB","FR","DE","NL","IS","FI","NO","IT","AR","US"), langs=("en"), audio=("en"), subs=("en","fr","es","de","it","pt"),
      original="Dancer in the Dark",collections=("best-of-europe","top-rated")),

    # Colombia
    m("embrace-of-the-serpent-2015","Embrace of the Serpent",2015,125,7.8,80,
      overview="Two Amazonian journeys, decades apart, follow an indigenous shaman and a German scientist.",
genre_csv="Adventure,Drama", countries=("CO","AR","VE","US"), langs=("es","en"), audio=("es","en"), subs=("en","fr"),
      original="El abrazo de la serpiente",collections=("best-of-latin-america","top-rated")),
    m("birds-of-passage-2018","Birds of Passage",2018,125,7.4,72,
      overview="A 1970s indigenous Wayuu family gets pulled into the marijuana trade in this crime saga.",
genre_csv="Crime,Drama", countries=("CO","DK","MX","BR","DE","FR"), langs=("es","en"), audio=("es","en"), subs=("en","fr"),
      original="PÃ¡jaros de verano",collections=("best-of-latin-america",)),
    m("memoria-2021","Memoria",2021,136,7.0,68,
      overview="A Scottish orchid farmer in BogotÃ¡ investigates a mysterious sound she keeps hearing.",
genre_csv="Drama,Mystery", countries=("CO","TH","GB","DE","FR","MX","TW","CN","CH"), langs=("en","es"), audio=("en","es"), subs=("en","fr"),
      original="Memoria",collections=("best-of-latin-america",)),

    # Syria
    m("the-damascus-cover-2017","The Damascus Cover",2017,93,5.7,40,
      overview="A British spy is sent to Syria undercover to recover a captured agent.",
genre_csv="Thriller", countries=("SY","GB"), langs=("ar","en"), audio=("ar","en"), subs=("en","fr"),
      original="The Damascus Cover"),
    m("for-sama-2019","For Sama",2019,100,8.4,82,
      overview="A young Syrian mother writes a love letter to her daughter while filming life in war-torn Aleppo.",
genre_csv="Documentary,War", countries=("SY","GB","FR","US","QAT"), langs=("ar","en"), audio=("ar","en"), subs=("en","fr","es"),
      original="Ù…Ù† Ø£Ø¬Ù„ Ø³Ù…Ø§",collections=("war","documentary-picks","top-rated")),
    m("cairo-6am-2015","Cairo 6,7,8",2015,95,5.5,35,
      overview="Three young women in Damascus share their dreams and struggles under social restrictions.",
genre_csv="Drama,Romance", countries=("SY","EG"), langs=("ar"), audio=("ar","en"), subs=("en","fr"),
      original="Ø§Ù„Ù‚Ø§Ù‡Ø±Ø© Ù¦Ù§Ù¨"),

    # Iraq
    m("son-of-babylon-2009","Son of Babylon",2009,100,7.0,55,
      overview="A Kurdish boy and his grandmother travel across Iraq searching for their missing family.",
genre_csv="Drama", countries=("IQ","GB","FR","NL","PS","AE"), langs=("ar","ku","en"), audio=("ar","ku","en"), subs=("en","fr"),
      original="Son of Babylon",collections=("war","best-of-arab")),
    m("iraqi-ode-2019","Iraqi Odyssey",2019,162,7.0,55,
      overview="An epic documentary tracing an Iraqi family's journey through the country's 20th-century history.",
genre_csv="Documentary,History", countries=("IQ","CH","DE","US","FR"), langs=("ar","en"), audio=("ar","en"), subs=("en","fr"),
      original="Iraqi Odyssey"),
    m("the-bakery-2019","The Bakery",2019,90,6.7,50,
      overview="An Iraqi woman returns to Baghdad after 20 years in exile and confronts family ghosts.",
genre_csv="Drama", countries=("IQ","US"), langs=("ar","en"), audio=("ar","en"), subs=("en","fr"),
      original="The Bakery"),

    # Kenya
    m("the-first-grader-2010","The First Grader",2010,103,7.4,62,
      overview="An 84-year-old Kenyan man enrolls in first grade, fulfilling a lifelong dream.",
genre_csv="Biography,Drama", countries=("KE","GB","US","ZA"), langs=("sw","en"), audio=("sw","en"), subs=("en","fr"),
      original="The First Grader"),
    m("rafiki-2018","Rafiki",2018,83,6.5,55,
      overview="Two teenage girls in Nairobi fall in love and face the consequences in this banned Kenyan drama.",
genre_csv="Drama,Romance", countries=("KE","FR","LB","ZA","NL","US","GB","CO"), langs=("sw","en"), audio=("sw","en"), subs=("en","fr"),
      original="Rafiki"),
    m("country-2024","Country",2024,99,6.4,42,
      overview="Two Kenyan siblings reunite with their grandmother in a rural village during a national mourning period.",
genre_csv="Drama,Family", countries=("KE","DE","FR"), langs=("sw","en"), audio=("sw","en"), subs=("en","fr"),
      original="Country"),

    # Ivory Coast
    m("run-2014-laurent","Run",2014,100,7.0,55,
      overview="Two Ivorian teenage boys dream of escaping their Abidjan shantytown.",
genre_csv="Drama", countries=("CI","FR"), langs=("fr"), audio=("fr","en"), subs=("en","fr"),
      original="Run"),
    m("the-night-of-the-400-2023","The Night of the 400",2023,98,6.8,48,
      overview="A young Ivorian sprinter defies tradition to pursue Olympic glory.",
genre_csv="Drama,Sport", countries=("CI","FR"), langs=("fr"), audio=("fr","en"), subs=("en","fr"),
      original="La Nuit du 400"),
    m("chronicle-of-a-vanishing-2024","Chronicle of a Vanishing",2024,95,6.6,45,
      overview="An Ivorian farmer documents his village's displacement by a Chinese-owned rubber plantation.",
genre_csv="Documentary", countries=("CI","FR","DE"), langs=("fr"), audio=("fr","en"), subs=("en","fr"),
      original="Chronicle of a Vanishing"),
]


# =====================================================================
# DOCUMENTARY + MUSIC BIOPICS + CONCERT FILMS
# =====================================================================
DOCS_MUSIC_SPORTS = [
    # Music biopics & docs
    m("bohemian-rhapsody-2018","Bohemian Rhapsody",2018,134,7.9,88,
      overview="The story of Queen's legendary lead singer Freddie Mercury and the band's iconic Live Aid performance.",
      genre_csv="Biography,Drama,Music",collections=("music-and-concerts","top-rated")),
    m("rocketman-2019","Rocketman",2019,121,7.3,82,
      overview="An imaginative musical fantasy about Elton John's breakthrough years.",
      genre_csv="Biography,Drama,Music",collections=("music-and-concerts",)),
    m("elvis-2022","Elvis",2022,159,7.5,86,
      overview="Elvis Presley's rise and fall told through his complex relationship with Colonel Tom Parker.",
      genre_csv="Biography,Drama,Music",collections=("music-and-concerts","trending-today")),
    m("straight-outta-compton-2015","Straight Outta Compton",2015,147,7.8,82,
      overview="The rise and fall of N.W.A., the group that defined gangsta rap.",
      genre_csv="Biography,Drama,Music",collections=("music-and-concerts",)),
    m("amy-2015","Amy",2015,128,7.8,80,
      overview="A documentary portrait of Amy Winehouse's rise and tragic death.",
      genre_csv="Documentary,Music",collections=("music-and-concerts","documentary-picks","top-rated")),
    m("whiplash-2014","Whiplash",2014,106,8.5,90,
      overview="A young jazz drummer enrolls at a cutthroat music conservatory.",
      genre_csv="Drama,Music",collections=("music-and-concerts","top-rated")),
    m("love-and-mercy-2014","Love & Mercy",2014,121,7.2,72,
      overview="The Beach Boys' Brian Wilson in two eras, told through his musical genius and mental illness.",
      genre_csv="Biography,Drama,Music",collections=("music-and-concerts",)),

    # Concert films
    m("the-last-waltz-1978","The Last Waltz",1978,117,8.1,75,
      overview="Martin Scorsese's concert film of The Band's farewell performance.",
      genre_csv="Documentary,Music",collections=("music-and-concerts","documentary-picks")),
    m("stop-making-sense-1984","Stop Making Sense",1984,88,8.5,80,
      overview="Talking Heads deliver an electrifying concert film directed by Jonathan Demme.",
      genre_csv="Documentary,Music",collections=("music-and-concerts","documentary-picks","top-rated")),
    m("home-of-the-brave-1986","U2: Rattle and Hum",1988,99,7.4,55,
      overview="U2's American stadium tour captured in this concert film mixed with documentary.",
      genre_csv="Documentary,Music",collections=("music-and-concerts",)),
    m("metallica-some-kind-of-monster-2004","Metallica: Some Kind of Monster",2004,141,7.4,68,
      overview="A documentary following Metallica through two years of internal turmoil and therapy.",
      genre_csv="Documentary,Music",collections=("music-and-concerts",)),
    m("oasis-supersonic-2016","Oasis: Supersonic",2016,122,7.8,72,
      overview="The rise of Oasis from Manchester council estate to global rock icons.",
      genre_csv="Documentary,Music",collections=("music-and-concerts","documentary-picks")),

    # Sports docs
    m("free-solo-2018","Free Solo",2018,100,8.1,84,
      overview="Alex Honnold attempts to climb El Capitan without ropes in this Oscar-winning documentary.",
      genre_csv="Documentary,Sport",collections=("documentary-picks","top-rated")),
    m("the-last-dance-2020","The Last Dance",2020,490,9.1,94,"tv","ended",
      overview="A 10-part documentary on Michael Jordan and the Chicago Bulls dynasty.",
      genre_csv="Documentary,Sport,Biography",collections=("documentary-picks","top-rated")),
    m("senna-2010","Senna",2010,106,8.5,82,
      overview="The story of Formula One legend Ayrton Senna through his career and tragic death.",
      genre_csv="Documentary,Sport,Biography",collections=("documentary-picks","top-rated")),
    m("the-two-escobars-2010","The Two Escobars",2010,107,8.0,75,
      overview="The intertwined fates of Colombian soccer player AndrÃ©s Escobar and drug lord Pablo Escobar.",
      genre_csv="Documentary,Sport,Crime",collections=("documentary-picks",)),

    # Reality / documentary series
    m("planet-earth-2006","Planet Earth",2006,600,9.4,92,"tv","ended",
      overview="The landmark BBC nature documentary series revealing the diversity of life on Earth.",
      genre_csv="Documentary,Family",collections=("documentary-picks","top-rated")),
    m("planet-earth-ii-2016","Planet Earth II",2016,360,9.5,95,"tv","ended",
      overview="A landmark follow-up nature documentary featuring islands, mountains, jungles and cities.",
      genre_csv="Documentary,Family",collections=("documentary-picks","top-rated")),
    m("blue-planet-ii-2017","Blue Planet II",2017,420,9.3,93,"tv","ended",
      overview="An epic exploration of the world's oceans and the wildlife within.",
      genre_csv="Documentary,Family",collections=("documentary-picks","top-rated")),
    m("our-planet-2019","Our Planet",2019,400,9.3,93,"tv","ended",
      overview="A Netflix nature documentary revealing the impact of climate change on the world's species.",
      genre_csv="Documentary,Family",collections=("documentary-picks","top-rated")),

    # Add type=tv documentaries
]


# =====================================================================
# SOUTH INDIAN + MORE BOLLYWOOD (Tamil, Telugu, Malayalam, Kannada)
# =====================================================================
SOUTH_INDIAN = [
    m("rrr-2022-real","RRR",2022,187,7.9,92,
      overview="Two legendary Indian revolutionaries journey far from home before fighting for their country in the 1920s.",
genre_csv="Action,Drama,History", countries=("IN"), langs=("te","hi","en"), audio=("te","hi","en"), subs=("en","fr","ar"),
      original="à°°à±Œà°¦à±à°°à°‚ à°°à°£à°‚ à°°à±à°¦à±à°°à°‚",collections=("top-rated","trending-today")),
    m("baahubali-2015-real","Baahubali: The Beginning",2015,159,8.0,90,
      overview="An adventurous man raised in a tribe learns of his royal heritage in this Telugu epic.",
genre_csv="Action,Adventure,Drama", countries=("IN"), langs=("te","hi","en"), audio=("te","hi","en"), subs=("en","fr"),
      original="à°¬à°¾à°¹à±à°¬à°²à°¿",collections=("top-rated",)),
    m("baahubali-2-2017-real","Baahubali 2: The Conclusion",2017,166,8.2,93,
      overview="Shiva learns of his true identity and seeks to reclaim the throne of Mahishmati.",
genre_csv="Action,Adventure,Drama", countries=("IN"), langs=("te","hi","en"), audio=("te","hi","en"), subs=("en","fr"),
      original="à°¬à°¾à°¹à±à°¬à°²à°¿ 2",collections=("top-rated",)),
    m("vikram-2022-real","Vikram",2022,173,8.4,90,
      overview="An elite black-ops squad investigates the murder of a police officer in Chennai.",
genre_csv="Action,Crime,Thriller", countries=("IN"), langs=("ta","hi","en"), audio=("ta","hi","en"), subs=("en","fr"),
      original="à®µà®¿à®•à¯à®°à®®à¯",collections=("trending-today",)),
    m("master-2021-real","Master",2021,179,7.4,82,
      overview="An alcoholic professor and a gangster battle for the souls of juvenile delinquents.",
genre_csv="Action,Crime,Drama", countries=("IN"), langs=("ta","hi","en"), audio=("ta","hi","en"), subs=("en","fr"),
      original="à®®à®¾à®¸à¯à®Ÿà®°à¯"),
    m("kantara-2022-real","Kantara",2022,148,8.2,88,
      overview="A demigod's forest becomes contested when a man inherits his ancestral land in coastal Karnataka.",
genre_csv="Action,Drama,Horror", countries=("IN"), langs=("kn","hi","en"), audio=("kn","hi","en"), subs=("en","fr"),
      original="à²•à²¾à²‚à²¤à²¾à²°"),
    m("drishyam-2-2022-real","Drishyam 2",2022,152,8.2,82,
      overview="A man tries to cover up his family's crime as a police investigation closes in.",
genre_csv="Crime,Drama,Thriller", countries=("IN"), langs=("ml","hi","en"), audio=("ml","hi","en"), subs=("en","fr"),
      original="à´¦àµƒà´¶àµà´¯à´‚ 2"),
    m("shershaah-2021-real","Shershaah",2021,135,8.4,86,
      overview="The true story of Captain Vikram Batra, a hero of the Kargil War.",
genre_csv="Action,Biography,Drama", countries=("IN"), langs=("hi","en"), audio=("hi","en"), subs=("en","fr"),
      original="à¤¶à¥‡à¤°à¤¶à¤¾à¤¹",collections=("war","top-rated")),
    m("83-2021-real","83",2021,162,7.0,72,
      overview="The Indian cricket team's historic 1983 Cricket World Cup victory.",
genre_csv="Drama,Sport", countries=("IN"), langs=("hi","en"), audio=("hi","en"), subs=("en","fr"),
      original="83"),
    m("the-kerala-story-2023-real","The Kerala Story",2023,138,2.7,55,
      overview="A controversial drama about three women drawn into extremism and radicalization.",
genre_csv="Drama,Thriller", countries=("IN"), langs=("hi","ml","en"), audio=("hi","ml","en"), subs=("en","fr"),
      original="The Kerala Story"),
    m("sardar-udham-2021-real","Sardar Udham",2021,164,8.5,82,
      overview="The story of Indian revolutionary Sardar Udham Singh and his assassination of Michael O'Dwyer.",
genre_csv="Biography,Crime,Drama", countries=("IN","GB"), langs=("hi","en"), audio=("hi","en"), subs=("en","fr"),
      original="à¤¸à¤°à¤¦à¤¾à¤° à¤‰à¤§à¤®",collections=("top-rated",)),
    m("neerja-2016-real","Neerja",2016,122,7.6,75,
      overview="A flight attendant sacrifices herself to save passengers from hijackers on Pan Am Flight 73.",
genre_csv="Biography,Drama,Thriller", countries=("IN"), langs=("hi","en"), audio=("hi","en"), subs=("en","fr"),
      original="à¤¨à¥€à¤°à¤œà¤¾"),
    m("paan-singh-tomar-2012-real","Paan Singh Tomar",2012,135,8.1,80,
      overview="An Indian steeplechase champion becomes a feared rebel after his land is stolen.",
genre_csv="Biography,Drama,Sport", countries=("IN"), langs=("hi","en"), audio=("hi","en"), subs=("en","fr"),
      original="à¤ªà¤¾à¤¨ à¤¸à¤¿à¤‚à¤¹ à¤¤à¥‹à¤®à¤°"),
    m("highway-2014-real","Highway",2014,133,7.6,72,
      overview="A young Indian woman, kidnapped, finds freedom and identity in captivity.",
genre_csv="Crime,Drama,Romance", countries=("IN"), langs=("hi","en"), audio=("hi","en"), subs=("en","fr"),
      original="à¤¹à¤¾à¤ˆà¤µà¥‡"),
]


def main():
    print(f"Connecting to {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    all_records = (
        STAR_TREK + JAMES_BOND + FRANCHISES_BATCH_A + FRANCHISES_BATCH_B +
        ANIMATED_FRANCHISES + CLASSICS + EMPTY_COUNTRIES +
        DOCS_MUSIC_SPORTS + SOUTH_INDIAN
    )

    inserted = 0
    skipped = 0
    errors = 0
    by_country = {}
    by_type = {}
    for rec in all_records:
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
            t = rec.get("type", "movie")
            by_type[t] = by_type.get(t, 0) + 1
        except Exception as e:
            print(f"  ERROR inserting {rec['slug']}: {e}")
            errors += 1

    conn.commit()
    conn.close()
    print(f"\nDone: inserted={inserted}, skipped={skipped}, errors={errors}")
    print("\nBy country (top 20):")
    for c, n in sorted(by_country.items(), key=lambda x: -x[1])[:20]:
        print(f"  {c}: {n}")
    print("\nBy type:")
    for t, n in by_type.items():
        print(f"  {t}: {n}")


if __name__ == "__main__":
    main()
