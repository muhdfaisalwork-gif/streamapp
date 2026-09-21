# StreamApp: Scraper Adapter Probe Log (Verified Sep 20, 2026)

## 1. Network Probe & Cloudflare Bypass Summary

All 10 target sites were probed using Scrapling's stealth browser fingerprints and Fetcher engine on Python 3.14.

| Site | URL Probe | HTTP Status | Response Size | Extraction Architecture | Verified Yield / Page |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **MovieBoxHD** | `https://movieboxhd.net/ranking-list/...` | 200 | ~1.4 MB | Server-rendered Nuxt dataset & DOM cards | 20–24 cards / page |
| **123Movies** | `https://123moviesweb.org/movies` | 200 | 58 KB | SPA shell with embedded TMDB IDs in anchor hrefs | 40 items / page |
| **YifyPro** | `https://yify.pro/browse-movies/{page}/` | 200 | 45 KB | Server-rendered HTML with TMDB ID `/film/{id}/{slug}/` | 36 items / page (tested p1–p400) |
| **YTS** | `https://en.yts-official.biz/browse-movies` | 200 | 62 KB | Server-rendered HTML with `.browse-movie-wrap` | 40 items / page |
| **uflix.cc** | `https://uflix.cc/movies?page={page}` | 200 | 38 KB | Server-rendered HTML with card elements | 18 items / page |
| **HDO Box** | `https://hdobox.se` | 200 | ~468 KB | SSR HTML APK portal | 12 items / query |
| **BeeTV** | `https://beetv.me` | 200 | ~165 KB | SSR + Search endpoint | 15 items / query |
| **Donkey.to** | `https://donkey.to` | 200 | 27 KB | Adaptive Stealth Fetcher | 10 items / page |
| **TMovies** | `https://qmovies.co` | 200 | 11 KB | Adaptive Stealth Fetcher | 10 items / page |
| **OnStream** | `https://onstream.so` | 200 | 32 KB | Adaptive Stealth Fetcher | 12 items / page |

---

## 2. Stream Resolution Validation

All extracted items map to verified public embed mirrors:
1. **VidSrc**:
   - Movie: `https://vidsrc.to/embed/movie/{tmdbId}`
   - TV: `https://vidsrc.to/embed/tv/{tmdbId}/{season}/{episode}`
2. **SuperEmbed / MultiEmbed**:
   - Video: `https://multiembed.mov/?video_id={imdbId}` or `https://multiembed.mov/?video_id={tmdbId}&tmdb=1`
   - Direct: `https://multiembed.mov/directstream.php?video_id={imdbId}`
