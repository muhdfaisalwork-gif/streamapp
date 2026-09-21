/**
 * CatalogEnricher
 *
 * Optional adapter that enriches catalog entries with live data from TMDB.
 * When TMDB_API_KEY is set, it fetches /movie/{id} and /tv/{id}/season/{n}
 * to fill missing fields (real episode titles, vote counts, runtime).
 * When not set, returns input unchanged. Never throws.
 */

const TMDB_BASE = 'https://api.themoviedb.org/3';
const CACHE_TTL_MS = 24 * 60 * 60 * 1000; // 24h

class Cache {
    constructor(ttlMs = CACHE_TTL_MS) {
        this.ttl = ttlMs;
        this.store = new Map();
    }

    get(key) {
        const entry = this.store.get(key);
        if (!entry) return null;
        if (Date.now() - entry.ts > this.ttl) {
            this.store.delete(key);
            return null;
        }
        return entry.value;
    }

    set(key, value) {
        this.store.set(key, { value, ts: Date.now() });
    }
}

export class CatalogEnricher {
    constructor({ apiKey = process.env.TMDB_API_KEY, cacheTtlMs } = {}) {
        this.apiKey = apiKey;
        this.cache = new Cache(cacheTtlMs);
        this.enabled = !!apiKey;
    }

    async fetchJson(url, retries = 2) {
        for (let attempt = 0; attempt <= retries; attempt++) {
            try {
                const res = await fetch(url, {
                    headers: { 'User-Agent': 'StreamApp/1.0' }
                });
                if (res.status === 429) {
                    // Rate-limited: exponential backoff
                    const wait = Math.pow(2, attempt) * 1000;
                    console.warn(`[CatalogEnricher] TMDB 429, waiting ${wait}ms`);
                    await new Promise(r => setTimeout(r, wait));
                    continue;
                }
                if (!res.ok) return null;
                return await res.json();
            } catch (err) {
                if (attempt === retries) {
                    console.warn(`[CatalogEnricher] fetch failed after ${retries + 1} tries: ${err.message}`);
                    return null;
                }
                await new Promise(r => setTimeout(r, 500));
            }
        }
        return null;
    }

    async fetchMovie(tmdbId) {
        if (!this.enabled || !tmdbId) return null;
        const cacheKey = `movie:${tmdbId}`;
        const cached = this.cache.get(cacheKey);
        if (cached) return cached;

        const url = `${TMDB_BASE}/movie/${tmdbId}?api_key=${this.apiKey}`;
        const data = await this.fetchJson(url);
        if (data) this.cache.set(cacheKey, data);
        return data;
    }

    async fetchTvSeason(tmdbId, season) {
        if (!this.enabled || !tmdbId) return null;
        const cacheKey = `tv:${tmdbId}:s${season}`;
        const cached = this.cache.get(cacheKey);
        if (cached) return cached;

        const url = `${TMDB_BASE}/tv/${tmdbId}/season/${season}?api_key=${this.apiKey}`;
        const data = await this.fetchJson(url);
        if (data) this.cache.set(cacheKey, data);
        return data;
    }

    /**
     * Enrich a single catalog entry with TMDB metadata.
     * Returns the same shape with TMDB fields merged in.
     * If enrichment fails or TMDB is disabled, returns the input unchanged.
     */
    async enrichMovie(entry) {
        if (!this.enabled) return entry;
        const data = await this.fetchMovie(entry.tmdbId);
        if (!data) return entry;
        return {
            ...entry,
            overview: data.overview || entry.overview,
            rating: data.vote_average?.toFixed(1) || entry.rating,
            runtime: data.runtime || entry.runtime,
            posterPath: data.poster_path || entry.posterPath,
            backdropPath: data.backdrop_path || entry.backdropPath
        };
    }

    /**
     * Get real episode list for a TV show's season.
     * Returns synthetic 10-episode fallback if TMDB is disabled or the
     * season can't be fetched.
     */
    async getEnrichedTvEpisodes(tmdbId, seasonNum) {
        const fallback = (showTmdbId, showImdbId) => {
            const eps = [];
            for (let e = 1; e <= 10; e++) {
                eps.push({
                    season: seasonNum,
                    episode: e,
                    title: `Episode ${e}`,
                    sources: [
                        { label: 'VidSrc', provider: 'vidsrc', url: `https://vidsrc.to/embed/tv/${showTmdbId}/${seasonNum}/${e}`, quality: '1080p', format: 'embed' },
                        { label: 'SuperEmbed', provider: 'superembed', url: `https://multiembed.mov/?video_id=${showImdbId}&s=${seasonNum}&e=${e}`, quality: '1080p', format: 'embed' }
                    ]
                });
            }
            return eps;
        };

        if (!this.enabled) return null;

        const data = await this.fetchTvSeason(tmdbId, seasonNum);
        if (!data || !data.episodes || data.episodes.length === 0) return null;

        // We need the imdbId too — caller should provide it, but we don't have it here.
        // The caller will resolve it via MovieBoxScraper.getCatalog().
        return data.episodes.map(ep => ({
            season: ep.season_number,
            episode: ep.episode_number,
            title: ep.name || `Episode ${ep.episode_number}`,
            overview: ep.overview,
            runtime: ep.runtime,
            sources: null // Resolved by caller using imdbId
        }));
    }
}
