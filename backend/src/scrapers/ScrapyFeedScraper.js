import { BaseScraper } from './BaseScraper.js';
import fs from 'node:fs';
import path from 'node:path';

/**
 * ScrapyFeedScraper
 *
 * Reads catalog JSON produced by the Python Scrapy service (Phase 1b).
 * If the JSON file is missing, stale, or unparseable, this scraper
 * returns empty results without raising — the rest of the catalog
 * stays usable.
 *
 * Expected JSON shape (one of):
 *   { items: [...]}           // from pipelines.py
 *   [{...}, {...}, ...]        // raw JSON array
 *
 * Each item has:
 *   { title, year, imdb_id, type, tmdb_id, genres, overview, poster_path, backdrop_path, ... }
 *
 * Re-mapped to the frontend's catalog shape:
 *   { id, title, year, type, url, sourceName, poster, backdrop, genres, rating,
 *     duration, durationMinutes, description, imdbId, tmdbId, seasons, streams }
 */
export class ScrapyFeedScraper extends BaseScraper {
    constructor({ feedPath } = {}) {
        super('ScrapyFeed', 'scrapy-feed');
        // Default to ../scraper/output/scraped_catalog.json relative to this file
        this.feedPath = feedPath
            || path.resolve(process.cwd(), '..', 'scraper', 'output', 'scraped_catalog.json');
    }

    async loadFeed() {
        try {
            if (!fs.existsSync(this.feedPath)) return null;
            const stat = fs.statSync(this.feedPath);
            // Treat >24h as stale
            const ageMs = Date.now() - stat.mtimeMs;
            if (ageMs > 24 * 60 * 60 * 1000) {
                console.warn(`[ScrapyFeed] feed is ${(ageMs / 3600000).toFixed(1)}h old, treating as stale`);
                return null;
            }
            const raw = await fs.promises.readFile(this.feedPath, 'utf8');
            const parsed = JSON.parse(raw);
            if (Array.isArray(parsed)) return parsed;
            if (parsed && Array.isArray(parsed.items)) return parsed.items;
            return null;
        } catch (err) {
            console.warn(`[ScrapyFeed] failed to read feed: ${err.message}`);
            return null;
        }
    }

    async search(query) {
        const items = await this.loadFeed();
        if (!items) return [];
        const q = (query || '').toLowerCase().trim();
        const matches = q
            ? items.filter(item =>
                (item.title || '').toLowerCase().includes(q) ||
                (item.imdb_id || '').toLowerCase() === q.toLowerCase() ||
                (item.genres || []).some(g => (g || '').toLowerCase().includes(q))
            )
            : items;
        return matches.map(item => this.toFrontendItem(item)).filter(Boolean);
    }

    async extractStream(movieUrl) {
        // Scrapy items may carry a direct embed URL or a torrent magnet
        const items = await this.loadFeed();
        if (!items) return null;
        const item = items.find(i =>
            i.id === movieUrl ||
            i.imdb_id === movieUrl ||
            (i.title || '').toLowerCase().replace(/\s+/g, '-') === movieUrl.toLowerCase()
        );
        if (!item) return null;
        return item.embed_url || item.torrent_magnet || item.url || null;
    }

    /**
     * Normalize a Scrapy item into the frontend catalog shape.
     * Scrapy spiders may emit fields under various names — we accept both
     * snake_case (from Python) and camelCase (legacy).
     */
    toFrontendItem(item) {
        if (!item || !item.title) return null;

        const id = item.id
            || (item.title || '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')
            || `scrapy-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;

        const tmdbId = item.tmdb_id || item.tmdbId;
        const imdbId = item.imdb_id || item.imdbId;
        const type = item.type || 'movie';
        const year = item.year || parseInt((item.release_date || '').substring(0, 4), 10) || 0;
        const posterPath = item.poster_path || item.posterPath || '';
        const backdropPath = item.backdrop_path || item.backdropPath || posterPath;
        const overview = item.overview || item.description || '';
        const rating = item.rating || item.vote_average?.toFixed?.(1) || 'NR';
        const runtime = item.runtime || item.durationMinutes || 0;
        const genres = item.genres || [];

        const streams = [];
        if (item.embed_url) {
            streams.push({
                label: 'Embed',
                provider: 'scrapy-embed',
                url: item.embed_url,
                quality: item.quality || '720p',
                format: 'embed'
            });
        }
        if (item.torrent_magnet) {
            streams.push({
                label: 'Torrent',
                provider: 'scrapy-torrent',
                url: item.torrent_magnet,
                quality: item.quality || '1080p',
                format: 'torrent'
            });
        }
        // Always fall back to VidSrc by TMDB/IMDb id so users have a clickable source
        if (tmdbId && type === 'movie') {
            streams.push({
                label: 'VidSrc',
                provider: 'vidsrc',
                url: `https://vidsrc.to/embed/movie/${tmdbId}`,
                quality: '1080p',
                format: 'embed'
            });
        } else if (imdbId && type === 'movie') {
            streams.push({
                label: 'VidSrc',
                provider: 'vidsrc',
                url: `https://vidsrc.to/embed/movie/${tmdbId || ''}`,
                quality: '1080p',
                format: 'embed'
            });
        }

        return {
            id,
            title: item.title,
            year,
            type,
            url: id,
            sourceName: this.sourceName,
            poster: posterPath.startsWith('/')
                ? `https://image.tmdb.org/t/p/w500${posterPath}`
                : (posterPath || ''),
            backdrop: backdropPath.startsWith('/')
                ? `https://image.tmdb.org/t/p/w1280${backdropPath}`
                : (backdropPath || posterPath || ''),
            genres,
            rating: typeof rating === 'number' ? rating.toFixed(1) : rating,
            duration: runtime * 60,
            durationMinutes: runtime,
            description: overview,
            imdbId,
            tmdbId,
            seasons: item.seasons,
            streams
        };
    }
}
