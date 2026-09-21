/**
 * LiveClient - Node.js HTTP client to the Python Scrapling FastAPI micro-service (:7800).
 * Handles health probing with backoff, resilient fallbacks, and response caching.
 */

const DEFAULT_BASE_URL = process.env.LIVE_SCRAPER_URL || 'http://127.0.0.1:7800';
const PROBE_INTERVAL_MS = 30000; // 30s probe cache

export class LiveClient {
    constructor(baseUrl = DEFAULT_BASE_URL) {
        this.baseUrl = baseUrl;
        this.liveAvailable = false;
        this.liveTitlesCached = 0;
        this.tmdbEnabled = false;
        this.lastProbeTs = 0;
        this.cache = new Map(); // key -> { ts, data }
        this.cacheTtlMs = 5 * 60 * 1000; // 5 minutes
    }

    /**
     * Probes the Python live service.
     */
    async probe() {
        const now = Date.now();
        if (now - this.lastProbeTs < PROBE_INTERVAL_MS) {
            return this.liveAvailable;
        }
        this.lastProbeTs = now;

        try {
            const res = await fetch(`${this.baseUrl}/health`, {
                signal: AbortSignal.timeout(3000)
            });
            if (res.ok) {
                const data = await res.json();
                this.liveAvailable = data.ok === true;
                this.liveTitlesCached = data.liveTitlesCached || 0;
                this.tmdbEnabled = !!data.tmdbEnabled;
                return true;
            }
        } catch (e) {
            this.liveAvailable = false;
        }
        return false;
    }

    /**
     * Startup probe with 5-retry exponential backoff.
     */
    async init() {
        let delay = 500;
        for (let attempt = 1; attempt <= 5; attempt++) {
            const ok = await this.probe();
            if (ok) {
                console.log(`[LiveClient] Connected to Python live-scraper at ${this.baseUrl} (${this.liveTitlesCached} titles cached)`);
                return true;
            }
            if (attempt < 5) {
                await new Promise(r => setTimeout(r, delay));
                delay *= 2;
            }
        }
        console.warn(`[LiveClient] Python live service at ${this.baseUrl} is currently offline. Curated catalog will be used as fallback.`);
        return false;
    }

    async byId(id) {
        if (!id) return null;
        const cacheKey = `byId:${id}`;
        const cached = this.cache.get(cacheKey);
        if (cached && Date.now() - cached.ts < this.cacheTtlMs) return cached.data;
        const isUp = await this.probe();
        if (!isUp) return null;
        const controller = new AbortController();
        const t = setTimeout(() => controller.abort(), 3500);
        try {
            const res = await fetch(`${this.baseUrl}/title/${encodeURIComponent(id)}`, { signal: controller.signal });
            if (!res.ok) return null;
            const data = await res.json();
            const result = (data && (data.title || data.results)) ? (data.title || (Array.isArray(data.results) ? data.results[0] : null)) : null;
            if (result) this.cache.set(cacheKey, { ts: Date.now(), data: result });
            return result;
        } catch (_) {
            return null;
        } finally {
            clearTimeout(t);
        }
    }

    async search({ q = '', genre = '', country = '', language = '', page = 1, pageSize = 50 } = {}) {
        const cacheKey = `search:${q}:${genre}:${country}:${language}:${page}:${pageSize}`;
        const cached = this.cache.get(cacheKey);
        if (cached && Date.now() - cached.ts < this.cacheTtlMs) {
            return cached.data;
        }

        // Fast probe check
        const isUp = await this.probe();
        if (!isUp) {
            return {
                query: q,
                genre,
                country,
                language,
                page,
                pageSize,
                count: 0,
                total: this.liveTitlesCached,
                live: false,
                sources: [],
                results: []
            };
        }

        try {
            const params = new URLSearchParams({
                q: q || '',
                genre: genre || '',
                country: country || '',
                language: language || '',
                page: String(page),
                pageSize: String(pageSize)
            });

            const res = await fetch(`${this.baseUrl}/search?${params}`, {
                signal: AbortSignal.timeout(15000)
            });

            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            if (data.results && data.results.length > 0) {
                this.cache.set(cacheKey, { ts: Date.now(), data });
            }
            if (data.total) this.liveTitlesCached = data.total;
            return data;
        } catch (e) {
            console.warn(`[LiveClient] search failed: ${e.message}`);
            return {
                query: q,
                genre,
                country,
                page,
                pageSize,
                count: 0,
                total: this.liveTitlesCached,
                live: false,
                sources: [],
                results: []
            };
        }
    }

    async getByCountry(countryKey, page = 1, pageSize = 50) {
        const cacheKey = `country:${countryKey}:${page}:${pageSize}`;
        const cached = this.cache.get(cacheKey);
        if (cached && Date.now() - cached.ts < this.cacheTtlMs) {
            return cached.data;
        }

        const isUp = await this.probe();
        if (!isUp) return { count: 0, results: [], live: false };

        try {
            const res = await fetch(`${this.baseUrl}/country/${encodeURIComponent(countryKey)}?page=${page}&pageSize=${pageSize}`, {
                signal: AbortSignal.timeout(10000)
            });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            if (data.results && data.results.length > 0) {
                this.cache.set(cacheKey, { ts: Date.now(), data });
            }
            return data;
        } catch (e) {
            return { count: 0, results: [], live: false };
        }
    }

    async getByGenre(genre, page = 1, pageSize = 50) {
        const cacheKey = `genre:${genre}:${page}:${pageSize}`;
        const cached = this.cache.get(cacheKey);
        if (cached && Date.now() - cached.ts < this.cacheTtlMs) {
            return cached.data;
        }

        const isUp = await this.probe();
        if (!isUp) return { count: 0, results: [], live: false };

        try {
            const res = await fetch(`${this.baseUrl}/genre/${encodeURIComponent(genre)}?page=${page}&pageSize=${pageSize}`, {
                signal: AbortSignal.timeout(10000)
            });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            if (data.results && data.results.length > 0) {
                this.cache.set(cacheKey, { ts: Date.now(), data });
            }
            return data;
        } catch (e) {
            return { count: 0, results: [], live: false };
        }
    }

    async resolve(site, url, season = null, episode = null) {
        const isUp = await this.probe();
        if (!isUp) return null;

        try {
            const res = await fetch(`${this.baseUrl}/resolve`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ site, url, season, episode }),
                signal: AbortSignal.timeout(8000)
            });
            if (!res.ok) return null;
            const data = await res.json();
            return data.streamUrl || null;
        } catch (e) {
            return null;
        }
    }

    async getStats() {
        const isUp = await this.probe();
        if (!isUp) return { total: 0, liveAvailable: false };

        try {
            const res = await fetch(`${this.baseUrl}/stats`, {
                signal: AbortSignal.timeout(5000)
            });
            if (!res.ok) return { total: 0, liveAvailable: false };
            const data = await res.json();
            return { ...data, liveAvailable: true };
        } catch (e) {
            return { total: 0, liveAvailable: false };
        }
    }

    async getCountryCounts() {
        const isUp = await this.probe();
        if (!isUp) return {};

        try {
            const res = await fetch(`${this.baseUrl}/country-counts`, {
                signal: AbortSignal.timeout(5000)
            });
            if (!res.ok) return {};
            return await res.json();
        } catch (e) {
            return {};
        }
    }

    async getTvEpisodes(id, season = 1) {
        const isUp = await this.probe();
        if (!isUp) return null;

        try {
            const res = await fetch(`${this.baseUrl}/tv/${encodeURIComponent(id)}/episodes?season=${season}`, {
                signal: AbortSignal.timeout(6000)
            });
            if (!res.ok) return null;
            return await res.json();
        } catch (e) {
            return null;
        }
    }

    async getTitleById(id) {
        const isUp = await this.probe();
        if (!isUp) return null;

        try {
            const res = await fetch(`${this.baseUrl}/title/${encodeURIComponent(id)}`, {
                signal: AbortSignal.timeout(5000)
            });
            if (!res.ok) return null;
            return await res.json();
        } catch (e) {
            return null;
        }
    }

    async warm(target = 100000) {
        try {
            await fetch(`${this.baseUrl}/warm?target=${target}`, {
                method: 'POST',
                signal: AbortSignal.timeout(5000)
            });
            return true;
        } catch (e) {
            return false;
        }
    }
}

export const liveClient = new LiveClient();
// Kick off non-blocking background probe
setImmediate(() => liveClient.init());
