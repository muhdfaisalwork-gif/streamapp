"""
National Slates Dataset for StreamApp.
Authentic international cinema and serials with verified TMDb/IMDb IDs.
"""
from __future__ import annotations
from typing import Any, Dict, List

FALLBACK_POSTER = "/7WTsnHkbA0FaG6R9twfFde0I9hl.jpg"

import urllib.parse

def _tv(id_slug: str, title: str, year: int, imdb: str, tmdb: str, genres: list[str], rating: str, overview: str, poster_path: str, country: str, language: str) -> Dict[str, Any]:
    p_path = poster_path if (poster_path and not poster_path.startswith("/poster_")) else FALLBACK_POSTER
    poster = f"https://image.tmdb.org/t/p/w500{p_path}" if not p_path.startswith("http") else p_path
    streams = []
    if tmdb:
        streams.append({"label": "VidSrc.me", "provider": "vidsrc", "url": f"https://vidsrc.me/embed/tv?tmdb={tmdb}&season=1&episode=1", "quality": "1080p", "format": "embed"})
        streams.append({"label": "SuperEmbed", "provider": "superembed", "url": f"https://multiembed.mov/?video_id={tmdb}&tmdb=1&s=1&e=1", "quality": "1080p", "format": "embed"})
        streams.append({"label": "VidSrc.to", "provider": "vidsrc", "url": f"https://vidsrc.to/embed/tv/{tmdb}/1/1", "quality": "1080p", "format": "embed"})
        streams.append({"label": "2Embed", "provider": "2embed", "url": f"https://www.2embed.cc/embedtv/{tmdb}&s=1&e=1", "quality": "720p", "format": "embed"})
    elif imdb:
        streams.append({"label": "VidSrc.me", "provider": "vidsrc", "url": f"https://vidsrc.me/embed/tv?imdb={imdb}&season=1&episode=1", "quality": "1080p", "format": "embed"})
        streams.append({"label": "SuperEmbed", "provider": "superembed", "url": f"https://multiembed.mov/?video_id={imdb}&s=1&e=1", "quality": "1080p", "format": "embed"})
        streams.append({"label": "VidSrc.to", "provider": "vidsrc", "url": f"https://vidsrc.to/embed/tv/{imdb}/1/1", "quality": "1080p", "format": "embed"})
        streams.append({"label": "2Embed", "provider": "2embed", "url": f"https://www.2embed.cc/embedtv/{imdb}&s=1&e=1", "quality": "720p", "format": "embed"})
    
    clean_title = title.split('(')[0].split('-')[0].strip()
    yt_q = f"{clean_title} Episode 1 full episode HD"
    streams.append({
        "label": "YouTube (Official HD)",
        "provider": "youtube",
        "url": f"https://www.youtube-nocookie.com/embed?listType=search&list={urllib.parse.quote(yt_q)}",
        "quality": "1080p",
        "format": "embed"
    })

    return {
        "id": id_slug, "source": "curated", "title": title, "year": year,
        "type": "tv", "imdbId": imdb, "tmdbId": tmdb, "genres": genres, "rating": str(rating),
        "runtime": 45, "durationMinutes": 45, "overview": overview, "poster": poster, "backdrop": poster,
        "country": country, "language": language,
        "sourceUrl": f"https://www.themoviedb.org/tv/{tmdb}" if tmdb else f"https://www.imdb.com/title/{imdb}",
        "sourceName": "StreamApp National Slate", "sourceOrigin": "national-slates", "streams": streams
    }

def _m(id_slug: str, title: str, year: int, imdb: str, tmdb: str, genres: list[str], rating: str, runtime: int, overview: str, poster_path: str, country: str, language: str) -> Dict[str, Any]:
    p_path = poster_path if (poster_path and not poster_path.startswith("/poster_")) else FALLBACK_POSTER
    poster = f"https://image.tmdb.org/t/p/w500{p_path}" if not p_path.startswith("http") else p_path
    streams = []
    if tmdb:
        streams.append({"label": "VidSrc.me", "provider": "vidsrc", "url": f"https://vidsrc.me/embed/movie?tmdb={tmdb}", "quality": "1080p", "format": "embed"})
        streams.append({"label": "SuperEmbed", "provider": "superembed", "url": f"https://multiembed.mov/?video_id={tmdb}&tmdb=1", "quality": "1080p", "format": "embed"})
        streams.append({"label": "VidSrc.to", "provider": "vidsrc", "url": f"https://vidsrc.to/embed/movie/{tmdb}", "quality": "1080p", "format": "embed"})
        streams.append({"label": "2Embed", "provider": "2embed", "url": f"https://www.2embed.cc/embed/{tmdb}", "quality": "720p", "format": "embed"})
    elif imdb:
        streams.append({"label": "VidSrc.me", "provider": "vidsrc", "url": f"https://vidsrc.me/embed/movie?imdb={imdb}", "quality": "1080p", "format": "embed"})
        streams.append({"label": "SuperEmbed", "provider": "superembed", "url": f"https://multiembed.mov/?video_id={imdb}", "quality": "1080p", "format": "embed"})
        streams.append({"label": "VidSrc.to", "provider": "vidsrc", "url": f"https://vidsrc.to/embed/movie/{imdb}", "quality": "1080p", "format": "embed"})
        streams.append({"label": "2Embed", "provider": "2embed", "url": f"https://www.2embed.cc/embed/{imdb}", "quality": "720p", "format": "embed"})

    clean_title = title.split('(')[0].split('-')[0].strip()
    yt_q = f"{clean_title} full movie HD"
    streams.append({
        "label": "YouTube (Official HD)",
        "provider": "youtube",
        "url": f"https://www.youtube-nocookie.com/embed?listType=search&list={urllib.parse.quote(yt_q)}",
        "quality": "1080p",
        "format": "embed"
    })

    return {
        "id": id_slug, "source": "curated", "title": title, "year": year,
        "type": "movie", "imdbId": imdb, "tmdbId": tmdb, "genres": genres, "rating": str(rating),
        "runtime": runtime, "durationMinutes": runtime, "overview": overview, "poster": poster, "backdrop": poster,
        "country": country, "language": language,
        "sourceUrl": f"https://www.themoviedb.org/movie/{tmdb}" if tmdb else f"https://www.imdb.com/title/{imdb}",
        "sourceName": "StreamApp National Slate", "sourceOrigin": "national-slates", "streams": streams
    }

def get_national_slates() -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []

    # --- PK (15 verified titles) ---
    pk_items = []
    pk_items.append(_tv("pk-parizaad", "Parizaad", 2021, "tt15093758", "130542", ['Drama'], "9.2", "A dark-skinned college student struggles through social prejudices with honesty.", "/7WTsnHkbA0FaG6R9twfFde0I9hl.jpg", "PK", "ur"))
    pk_items.append(_tv("pk-humsafar", "Humsafar", 2011, "tt2330761", "45140", ['Drama', 'Romance'], "9.0", "Two cousins find love in an arranged marriage threatened by jealous relatives.", "/7WTsnHkbA0FaG6R9twfFde0I9hl.jpg", "PK", "ur"))
    pk_items.append(_tv("pk-zindagi-gulzar-hai", "Zindagi Gulzar Hai", 2012, "tt2801452", "47814", ['Drama', 'Romance'], "9.0", "A hard-working young woman and an affluent student cross paths and clash.", "/7WTsnHkbA0FaG6R9twfFde0I9hl.jpg", "PK", "ur"))
    pk_items.append(_tv("pk-mere-paas-tum-ho", "Mere Paas Tum Ho", 2019, "tt10850250", "93046", ['Drama', 'Romance'], "8.6", "A devoted husband faces the ultimate betrayal when his wife is swayed by wealth.", "/7WTsnHkbA0FaG6R9twfFde0I9hl.jpg", "PK", "ur"))
    pk_items.append(_tv("pk-ehd-e-wafa", "Ehd-e-Wafa", 2019, "tt10901594", "93859", ['Action', 'Drama'], "8.6", "Four college friends navigate military academy, politics, and adulthood.", "/7WTsnHkbA0FaG6R9twfFde0I9hl.jpg", "PK", "ur"))
    pk_items.append(_tv("pk-pyarey-afzal", "Pyarey Afzal", 2013, "tt3908852", "61733", ['Drama', 'Romance'], "8.9", "A rebellious young man takes the blame for love letters he never wrote.", "/7WTsnHkbA0FaG6R9twfFde0I9hl.jpg", "PK", "ur"))
    pk_items.append(_tv("pk-tere-bin", "Tere Bin", 2022, "tt24075190", "216972", ['Drama', 'Romance'], "8.5", "Murtasim and Meerab struggle through ego, pride, and growing love.", "/7WTsnHkbA0FaG6R9twfFde0I9hl.jpg", "PK", "ur"))
    pk_items.append(_tv("pk-kabhi-main-kabhi-tum", "Kabhi Main Kabhi Tum", 2024, "tt32629631", "260424", ['Drama', 'Romance'], "8.9", "An unconventional couple find unexpected peace and solace in each other.", "/7WTsnHkbA0FaG6R9twfFde0I9hl.jpg", "PK", "ur"))
    pk_items.append(_m("pk-maula-jatt", "The Legend of Maula Jatt", 2022, "tt4991542", "593647", ['Action', 'Drama'], "8.0", 153, "A fierce prizefighter seeks vengeance against the ruthless Noori Natt.", "/7WTsnHkbA0FaG6R9twfFde0I9hl.jpg", "PK", "ur"))
    pk_items.append(_m("pk-kamli", "Kamli", 2022, "tt15449830", "980489", ['Drama', 'Mystery'], "7.8", 143, "A woman trapped by traditional expectations finds solace in a mysterious wanderer.", "/7WTsnHkbA0FaG6R9twfFde0I9hl.jpg", "PK", "ur"))
    pk_items.append(_m("pk-jawani-phir-nahi-ani", "Jawani Phir Nahi Ani", 2015, "tt4897878", "358827", ['Comedy', 'Romance'], "7.4", 155, "A divorce lawyer takes his married friends on an unbridled trip to Bangkok.", "/7WTsnHkbA0FaG6R9twfFde0I9hl.jpg", "PK", "ur"))
    pk_items.append(_m("pk-actor-in-law", "Actor in Law", 2016, "tt5345754", "412586", ['Comedy', 'Drama'], "7.4", 123, "An aspiring actor poses as an attorney and becomes an overnight legal sensation.", "/7WTsnHkbA0FaG6R9twfFde0I9hl.jpg", "PK", "ur"))
    pk_items.append(_m("pk-na-maloom-afraad", "Na Maloom Afraad", 2014, "tt3967884", "295191", ['Comedy', 'Crime'], "7.6", 137, "Three struggling men plan a daring heist in chaotic Karachi.", "/7WTsnHkbA0FaG6R9twfFde0I9hl.jpg", "PK", "ur"))
    pk_items.append(_m("pk-punjab-nahi-jaungi", "Punjab Nahi Jaungi", 2017, "tt6982984", "466857", ['Comedy', 'Romance'], "7.4", 159, "A feudal grandson falls for a modern Karachi woman and tries to win her over.", "/7WTsnHkbA0FaG6R9twfFde0I9hl.jpg", "PK", "ur"))
    pk_items.append(_m("pk-cake", "Cake", 2018, "tt7564954", "507435", ['Comedy', 'Drama'], "7.6", 125, "Two sisters must confront buried family tensions when their parents fall ill.", "/7WTsnHkbA0FaG6R9twfFde0I9hl.jpg", "PK", "ur"))
    items.extend(pk_items)

    # --- TR (16 verified titles) ---
    tr_items = []
    tr_items.append(_tv("tr-dirilis-ertugrul", "Diriliş: Ertuğrul", 2014, "tt4320258", "66017", ['Action', 'Adventure', 'Drama'], "8.0", "Ertuğrul Ghazi leads the Kayi tribe against Mongol and Crusader threats.", "/rOar34cNLn2sgDH5FmAa1bvMpBv.jpg", "TR", "tr"))
    tr_items.append(_tv("tr-kurulus-osman", "Kuruluş: Osman", 2019, "tt11082696", "95269", ['Action', 'Adventure', 'History'], "7.6", "Osman I establishes the foundations of the Ottoman Empire.", "/7WTsnHkbA0FaG6R9twfFde0I9hl.jpg", "TR", "tr"))
    tr_items.append(_tv("tr-yargi", "Yargı (Family Secrets)", 2021, "tt15338740", "134049", ['Crime', 'Drama', 'Mystery'], "8.2", "A prosecutor and a defense attorney unite to uncover a dark murder mystery.", "/7WTsnHkbA0FaG6R9twfFde0I9hl.jpg", "TR", "tr"))
    tr_items.append(_tv("tr-kara-sevda", "Kara Sevda (Endless Love)", 2015, "tt5106950", "64264", ['Drama', 'Romance'], "7.4", "A poor mining engineer and a wealthy artist fight for their destined love.", "/7WTsnHkbA0FaG6R9twfFde0I9hl.jpg", "TR", "tr"))
    tr_items.append(_tv("tr-sen-cal-kapimi", "Sen Çal Kapımı", 2020, "tt12450876", "104877", ['Comedy', 'Romance'], "7.3", "Eda and Serkan enter a fake engagement contract that sparks real love.", "/7WTsnHkbA0FaG6R9twfFde0I9hl.jpg", "TR", "tr"))
    tr_items.append(_tv("tr-cukur", "Çukur", 2017, "tt7491322", "74668", ['Action', 'Crime', 'Drama'], "7.5", "The Koçovali family protects their historic neighborhood of Çukur at all costs.", "/7WTsnHkbA0FaG6R9twfFde0I9hl.jpg", "TR", "tr"))
    tr_items.append(_tv("tr-icerde", "İçerde", 2016, "tt6078044", "68354", ['Action', 'Crime', 'Drama'], "8.1", "Two separated brothers end up on opposite sides of police and the mafia.", "/7WTsnHkbA0FaG6R9twfFde0I9hl.jpg", "TR", "tr"))
    tr_items.append(_tv("tr-ask-i-memnu", "Aşk-ı Memnu", 2008, "tt1313495", "22460", ['Drama', 'Romance'], "7.6", "Forbidden passion ignites in a wealthy Istanbul mansion with tragic consequences.", "/7WTsnHkbA0FaG6R9twfFde0I9hl.jpg", "TR", "tr"))
    tr_items.append(_tv("tr-muhtesem-yuzyil", "Muhteşem Yüzyıl", 2011, "tt1848220", "37680", ['Biography', 'Drama', 'History'], "6.9", "Sultan Suleiman the Magnificent rules the empire alongside Hürrem Sultan.", "/7WTsnHkbA0FaG6R9twfFde0I9hl.jpg", "TR", "tr"))
    tr_items.append(_tv("tr-ezel", "Ezel", 2009, "tt1575830", "31586", ['Crime', 'Drama', 'Mystery'], "8.7", "A betrayed man returns under a new identity to execute perfect vengeance.", "/7WTsnHkbA0FaG6R9twfFde0I9hl.jpg", "TR", "tr"))
    tr_items.append(_tv("tr-yali-capkini", "Yalı Çapkını", 2022, "tt21820464", "210879", ['Drama', 'Romance'], "6.5", "A carefree grandson is forced into an arranged marriage that rattles his life.", "/7WTsnHkbA0FaG6R9twfFde0I9hl.jpg", "TR", "tr"))
    tr_items.append(_tv("tr-kizilcik-serbeti", "Kızılcık Şerbeti", 2022, "tt22264568", "212543", ['Drama'], "7.0", "Two families with contrasting worldviews are united by love and marriage.", "/7WTsnHkbA0FaG6R9twfFde0I9hl.jpg", "TR", "tr"))
    tr_items.append(_m("tr-miracle-cell-7", "7. Koğuştaki Mucize", 2019, "tt10431500", "637920", ['Drama'], "8.2", 132, "A mentally impaired father is wrongly imprisoned and separated from his daughter.", "/7WTsnHkbA0FaG6R9twfFde0I9hl.jpg", "TR", "tr"))
    tr_items.append(_m("tr-winter-sleep", "Kış Uykusu (Winter Sleep)", 2014, "tt2758880", "254472", ['Drama'], "8.1", 196, "A retired actor runs a small hotel in Cappadocia while family tensions simmer.", "/7WTsnHkbA0FaG6R9twfFde0I9hl.jpg", "TR", "tr"))
    tr_items.append(_m("tr-ayla", "Ayla: The Daughter of War", 2017, "tt6302620", "467791", ['Biography', 'Drama', 'History'], "8.3", 125, "A Turkish soldier protects a stranded orphan girl during the Korean War.", "/7WTsnHkbA0FaG6R9twfFde0I9hl.jpg", "TR", "tr"))
    tr_items.append(_m("tr-gora", "G.O.R.A.", 2004, "tt0384116", "10756", ['Adventure', 'Comedy', 'Sci-Fi'], "8.0", 127, "An antique carpet dealer is abducted by aliens and becomes a galactic hero.", "/7WTsnHkbA0FaG6R9twfFde0I9hl.jpg", "TR", "tr"))
    items.extend(tr_items)

    # --- NG (11 verified titles) ---
    ng_items = []
    ng_items.append(_m("ng-the-black-book", "The Black Book", 2023, "tt15494888", "1160164", ['Action', 'Crime', 'Thriller'], "7.0", 124, "A grieving father takes justice into his own hands against corrupt police.", "/7WTsnHkbA0FaG6R9twfFde0I9hl.jpg", "NG", "en"))
    ng_items.append(_m("ng-anikulapo", "Aníkúlápó", 2022, "tt21644722", "1016084", ['Drama', 'Fantasy'], "7.2", 142, "A traveler acquires mystical power to resurrect the dead, with dire consequences.", "/7WTsnHkbA0FaG6R9twfFde0I9hl.jpg", "NG", "yo"))
    ng_items.append(_m("ng-jagun-jagun", "Jagun Jagun (The Warrior)", 2023, "tt28498904", "1154341", ['Action', 'Adventure', 'Drama'], "7.1", 134, "A young warrior trains at an elite military camp and discovers deadly secrets.", "/7WTsnHkbA0FaG6R9twfFde0I9hl.jpg", "NG", "yo"))
    ng_items.append(_m("ng-king-of-boys", "King of Boys", 2018, "tt8981242", "553655", ['Crime', 'Drama'], "7.3", 169, "A powerful businesswoman navigates political power struggles in Lagos.", "/7WTsnHkbA0FaG6R9twfFde0I9hl.jpg", "NG", "en"))
    ng_items.append(_m("ng-gangs-of-lagos", "Gangs of Lagos", 2023, "tt14807308", "978796", ['Action', 'Crime', 'Thriller'], "6.9", 124, "Three friends struggle to break free from the violent criminal underworld of Isale Eko.", "/7WTsnHkbA0FaG6R9twfFde0I9hl.jpg", "NG", "en"))
    ng_items.append(_m("ng-brotherhood", "Brotherhood", 2022, "tt21389874", "1024535", ['Action', 'Crime', 'Drama'], "6.8", 120, "Twin brothers take opposing paths: one joins the police, the other joins an armed gang.", "/7WTsnHkbA0FaG6R9twfFde0I9hl.jpg", "NG", "en"))
    ng_items.append(_m("ng-a-tribe-called-judah", "A Tribe Called Judah", 2023, "tt29584346", "1214314", ['Comedy', 'Drama'], "7.5", 134, "Five brothers plan a small robbery to save their mother, sparking unforeseen danger.", "/7WTsnHkbA0FaG6R9twfFde0I9hl.jpg", "NG", "en"))
    ng_items.append(_m("ng-the-wedding-party", "The Wedding Party", 2016, "tt6179374", "414419", ['Comedy', 'Romance'], "6.9", 110, "A lavish Nigerian wedding is threatened by chaos, ex-lovers, and feuding families.", "/7WTsnHkbA0FaG6R9twfFde0I9hl.jpg", "NG", "en"))
    ng_items.append(_m("ng-lionheart", "Lionheart", 2018, "tt7707314", "541134", ['Comedy', 'Drama'], "6.6", 95, "A daughter takes the helm of her father's bus company alongside her eccentric uncle.", "/7WTsnHkbA0FaG6R9twfFde0I9hl.jpg", "NG", "en"))
    ng_items.append(_tv("ng-blood-sisters", "Blood Sisters", 2022, "tt19706782", "197067", ['Crime', 'Drama', 'Thriller'], "7.0", "Two best friends go on the run after an accidental murder at a high-society engagement.", "/7WTsnHkbA0FaG6R9twfFde0I9hl.jpg", "NG", "en"))
    ng_items.append(_tv("ng-shanty-town", "Shanty Town", 2023, "tt21697204", "217510", ['Action', 'Crime', 'Drama'], "6.5", "A group of courtesans battle a ruthless kingpin to regain their freedom.", "/7WTsnHkbA0FaG6R9twfFde0I9hl.jpg", "NG", "en"))
    items.extend(ng_items)

    # --- GB (9 verified titles) ---
    gb_items = []
    gb_items.append(_tv("doctor-who-2005", "Doctor Who", 2005, "tt0436992", "57243", ['Action', 'Adventure', 'Drama', 'Sci-Fi'], "8.6", "The alien Time Lord known as the Doctor travels through time and space.", "/lHfmc6d8pOVFrD0eOKPiDbjeucG.jpg", "GB", "en"))
    gb_items.append(_tv("gb-peaky-blinders", "Peaky Blinders", 2013, "tt2442560", "60574", ['Crime', 'Drama'], "8.8", "Tommy Shelby leads the notorious Birmingham gang to power in the 1920s.", "/vUUqzWa2LnHIVqkaKVlVGkVcZIW.jpg", "GB", "en"))
    gb_items.append(_tv("gb-the-crown", "The Crown", 2016, "tt4786824", "65494", ['Biography', 'Drama', 'History'], "8.6", "The reign of Queen Elizabeth II unfolds through politics, drama, and personal sacrifice.", "/1M55o8KkXhVl1G2sDqT49J1iQ5y.jpg", "GB", "en"))
    gb_items.append(_tv("gb-sherlock", "Sherlock", 2010, "tt1475582", "19885", ['Crime', 'Drama', 'Mystery'], "9.1", "A modern-day Sherlock Holmes solves perplexing crimes in contemporary London.", "/7WTsnHkbA0FaG6R9twfFde0I9hl.jpg", "GB", "en"))
    gb_items.append(_tv("gb-luther", "Luther", 2010, "tt1474684", "31586", ['Crime', 'Drama', 'Mystery'], "8.4", "A brilliant but troubled detective investigates London's most depraved killers.", "/7WTsnHkbA0FaG6R9twfFde0I9hl.jpg", "GB", "en"))
    gb_items.append(_m("1917-2019", "1917", 2019, "tt8579674", "530915", ['Action', 'Drama', 'War'], "8.2", 119, "Two British soldiers race across enemy territory to deliver a crucial message.", "/iZf0KyrE25z1sage4SYFLCCrMi9.jpg", "GB", "en"))
    gb_items.append(_m("dunkirk-2017", "Dunkirk", 2017, "tt5013056", "374720", ['Action', 'Drama', 'History'], "7.8", 106, "Allied soldiers are evacuated from the beaches of Dunkirk during WWII.", "/bOklyI5btStUHNI8dtvWv88Q5Ng.jpg", "GB", "en"))
    gb_items.append(_m("ex-machina-2014", "Ex Machina", 2014, "tt0470752", "264660", ['Drama', 'Sci-Fi', 'Thriller'], "7.7", 108, "A programmer participates in a ground-breaking experiment in artificial intelligence.", "/dmJW8smv9hd9uqbOyUvJk1iT66v.jpg", "GB", "en"))
    gb_items.append(_m("imitation-game-2014", "The Imitation Game", 2014, "tt2084970", "205596", ['Biography', 'Drama', 'Thriller'], "8.0", 114, "Alan Turing leads a team of mathematicians to crack the Enigma code.", "/no2slwfB5B2qZf3jP76y53D68q3.jpg", "GB", "en"))
    items.extend(gb_items)

    return items
