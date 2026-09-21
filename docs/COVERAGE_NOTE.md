# StreamApp: Global Audiovisual Inventory & Coverage Note

## 1. Executive Summary

This document formalizes the typological classification, national production volumes, and structural blind spots of informal streaming aggregators, calibrated directly against the **Global Audiovisual Inventory Census** (27+ million records across statutory registries, IMDb, TMDb, and UIS).

StreamApp integrates a hybrid architecture combining:
1. **Parallel Scrapling + Patchright Live Micro-Service (`:7800`)** crawling 10 high-velocity web portals (BeeTV, MovieBoxHD, OnStream, HDO Box, 123moviesweb, YTS, YIFY, TMovies, Donkey.to, Uflix).
2. **Dedicated National Slate Ingestion Engine** covering high-output regional cinema and serialized television slates identified in the census.
3. **Multi-Mirror Public Iframe Resolvers** (VidSrc, SuperEmbed, MultiEmbed) routing playback without Cloudflare lockouts.

---

## 2. National Production Slates vs. Scraper Coverage

| Country / Region | Annual Feature Films | Annual Scripted TV / Serials | Primary Domestic Characteristic | Informational Blind Spot in Western Indexers | StreamApp Resolution Strategy |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **India (`IN`)** | 1,800 – 2,500 | High (Multilingual) | 90% Domestic Box Office; Hindi, Telugu, Tamil, Kannada, Malayalam | Regional linguistic releases fragmented across distinct non-Western networks | MovieBoxHD `sa-drama` category + curated multi-linguistic catalogue |
| **Turkey (`TR`)** | 350 – 450 | 50 – 70 prime-time *diziler* | World's 2nd largest scripted TV exporter ($600M+ revenue; 120–150 min weekly eps) | Severely under-represented in torrent repositories; primarily linear & YouTube | Pre-seeded prime-time diziler (*Diriliş*, *Kuruluş*, *Yargı*, *Kara Sevda*) with VidSrc/SuperEmbed resolvers |
| **Pakistan (`PK`)** | 25 – 45 | 150 – 250 finite drama serials | High-prestige PEMRA-regulated serials (20–35 eps per season); South Asian diaspora reach | Almost completely absent from P2P torrent portals; hosted on broadcast YouTube / OTT | Pre-seeded PEMRA serials (*Parizaad*, *Humsafar*, *Zindagi Gulzar Hai*, *Mere Paas Tum Ho*) + cinema revival (*Maula Jatt*) |
| **Nigeria (`NG`)** | 1,200 – 2,500 | Growing SVOD | High-velocity direct-to-digital Nollywood video commerce; >95% domestic capture | Omitted from torrent repositories unless acquired by global streamers | MovieBoxHD `black-drama` category + top Nollywood originals (*The Black Book*, *Aníkúlápó*, *Jagun Jagun*) |
| **South Korea (`KR`)**| 200 – 260 | 600 – 900 East Asian series | Global K-Drama phenomenon; theatrical box-office capture 50–60% | Rapid title rotation on pirate portals | MovieBoxHD `k-drama` crawler + comprehensive K-Drama registry |
| **China (`CN`)** | 700 – 1,050 | Major C-Drama & Donghua | 74% Domestic Box Office; *Ne Zha 2* (€1.8B global receipts) | Regional CDN firewalls & distinct hosting cyberlockers | MovieBoxHD `c-drama` crawler + domestic tentpoles |
| **Japan (`JP`)** | 500 – 650 | 12k–14k TV Anime; 24.9k MAL | Anime production committees; Studio Ghibli, Shinkai, global simulcast | Fragmented releases; torrent indexers focus strictly on mainstream episodes | MovieBoxHD `anime` crawler + high-yield MAL catalogue |
| **Egypt (`EG`)** | 35 – 55 | 40 – 60 *musalsalat* | Historical pan-Arab library (>4,000 features); Ramadan television | Concentrated during holy month; non-indexed by Western scrapers | Pre-seeded Ramadan musalsalat (*El Hashashin*, *Gaafar El Omda*, *Kira & El Gin*) |
| **Indonesia (`ID`)** | 180 – 240 | 80+ *sinetron* serials | Commercial terrestrial dominance (thousands of sinetron eps); horror cinema | Daily high-episode runs omit metadata indexing | Top theatrical action & horror (*The Raid*, *Pengabdi Setan*, *Gadis Kretek*) |
| **Philippines (`PH`)**| 120 – 180 | 80 – 120 *teleseryes* | Prolific commercial studio sector (multi-hundred episode runs) | Long-running daily broadcast ledgers non-standardized | Flagship teleseryes (*Maria Clara at Ibarra*, *Dirty Linen*) + cinema |
| **Mexico (`MX`)** | 100 – 140 | 100+ serials & telenovelas| TelevisaUnivision broadcast hub; auteur cinema (*Roma*, *Amores Perros*) | High-volume daily telenovela pipelines | Top telenovelas & classic auteur cinema |
| **Brazil (`BR`)** | 130 – 170 | 80+ telenovelas & streaming| TV Globo internationally syndicated telenovela production | Telenovela syndicated ledger formats | Flagship telenovelas (*Avenida Brasil*) + cinema (*Cidade de Deus*) |
| **Iran (`IR`)** | 90 – 130 | 30 – 50 broadcast/web series| State-regulated cinema via Farabi Cinema Foundation; auteur festival circuit | Strict national distribution windows | Award-winning auteur cinema (*A Separation*, *Children of Heaven*) + web series |

---

## 3. Structural Trajectories and Archival Preservation Gaps

1. **Celluloid & Pre-1990 Degradation**: Of the 2.13 million feature films produced globally, hundreds of thousands of pre-1990 titles, educational documentaries, and regional cinematic works lack digital encoding, placing them beyond the reach of standard scrapers.
2. **Episodic Predominance**: Serialized TV episodes represent 71.2% (~23.26M) of the global audiovisual inventory, whereas standalone movies comprise only 7.7% (~2.13M).
3. **Informal Aggregator Distortions**: Web indexers disproportionately represent commercial Hollywood releases and SVOD originals from the past 15 years, while regional daily television (diziler, sinetron, telenovelas, PEMRA serials) requires specialized native ingestion.
