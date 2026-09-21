import { BaseScraper } from './BaseScraper.js';

/**
 * UflixHtmlScraper - HTTP-only scraper for uflix.cc movie listings
 *
 * uflix.cc serves server-rendered HTML (no SPA, no Cloudflare challenge from
 * clean IPs) with a consistent movie card structure:
 *   <a href="/movie/<slug>" class="card card-movie">
 *     <img src="/images/posters/<hash>.jpg" />
 *     <span>rating</span>
 *     <li>genre</li>
 *     <li>year</li>
 *     <h3 class="title">title</h3>
 *   </a>
 *
 * Pagination: /movies/page/2/, /movies/page/3/, ...
 *
 * Each uflix movie has its own detail page at /movie/<slug> with more
 * metadata (description, IMDB code, genres). We do a single detail-page
 * fetch per title on first access to enrich it with an IMDb ID, which
 * the streaming layer can use to resolve the actual embed via VidSrc.
 */

const PAGES_TO_SCRAPE = 4;       // /movies, /movies/page/2, page/3, page/4
const ITEMS_PER_PAGE = 18;       // uflix serves ~18 per page
const CACHE_TTL_MS = 1000 * 60 * 60; // 1 hour

export class UflixHtmlScraper extends BaseScraper {
    constructor() {
        super('uflix', 'https://uflix.cc');
        this.cache = new Map();   // url → { ts, data }
        this.detailCache = new Map();
    }

    async _fetchHtml(url, useCache = true) {
        if (useCache) {
            const c = this.cache.get(url);
            if (c && Date.now() - c.ts < CACHE_TTL_MS) return c.data;
        }
        try {
            const res = await fetch(url, {
                headers: {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml'
                },
                signal: AbortSignal.timeout(15000)
            });
            if (!res.ok) return null;
            const text = await res.text();
            this.cache.set(url, { ts: Date.now(), data: text });
            return text;
        } catch (e) {
            console.error(`[uflix] fetch ${url} failed: ${e.message}`);
            return null;
        }
    }

    _extractSlugFromUrl(href) {
        // /movie/in-the-grey-2026 -> in-the-grey-2026
        const m = href.match(/\/movie\/([^/?#]+)/);
        return m ? m[1] : null;
    }

    _parseTitleAndYear(slug) {
        // slug "in-the-grey-2026" -> { title: "In the Grey", year: 2026 }
        const m = slug.match(/^(.+)-(\d{4})$/);
        if (m) {
            return {
                title: m[1].split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' '),
                year: parseInt(m[2], 10)
            };
        }
        return { title: slug.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase()), year: 0 };
    }

    _parseCardsFromHtml(html) {
        const cards = [];
        // Match each <a href="/movie/..." class="card card-movie">...</a>
        const cardRe = /<a\s+href="(\/movie\/[^"]+)"\s+class="card\s+card-movie"[\s\S]*?<\/a>/g;
        let m;
        while ((m = cardRe.exec(html)) !== null) {
            const block = m[0];
            const slug = this._extractSlugFromUrl(m[1]);
            if (!slug) continue;
            const { title: slugTitle, year } = this._parseTitleAndYear(slug);
            const posterMatch = block.match(/<img[^>]*src="(\/images\/posters\/[^"]+)"/);
            const poster = posterMatch ? posterMatch[1] : '';
            const ratingMatch = block.match(/<span>([0-9.]+)<\/span>/);
            const rating = ratingMatch ? parseFloat(ratingMatch[1]) : null;
            const genreMatch = block.match(/<li class="list-inline-item"\s+title="([^"]+)">([^<]+)<\/li>/);
            const genre = genreMatch ? genreMatch[1] : '';
            const titleMatch = block.match(/<h3 class="title"[^>]*>([^<]+)<\/h3>/);
            const title = titleMatch ? titleMatch[1].trim() : slugTitle;
            cards.push({ slug, title, year, poster, rating, genre });
        }
        return cards;
    }

    async fetchListings(pages = PAGES_TO_SCRAPE) {
        const all = [];
        const urls = [`${this.baseUrl}/movies`];
        for (let p = 2; p <= pages; p++) urls.push(`${this.baseUrl}/movies/page/${p}/`);
        for (const url of urls) {
            const html = await this._fetchHtml(url);
            if (!html) continue;
            const cards = this._parseCardsFromHtml(html);
            for (const c of cards) all.push(c);
        }
        return all;
    }

    async fetchDetail(slug) {
        if (this.detailCache.has(slug)) return this.detailCache.get(slug);
        const html = await this._fetchHtml(`${this.baseUrl}/movie/${slug}`);
        if (!html) return null;
        const imdbMatch = html.match(/imdb\.com\/title\/(tt\d+)/);
        const imdbId = imdbMatch ? imdbMatch[1] : '';
        // Description: look for first <p> after a known header
        const descMatch = html.match(/<div class="description[^"]*"[^>]*>([\s\S]*?)<\/div>/);
        const description = descMatch ? descMatch[1].replace(/<[^>]+>/g, '').trim() : '';
        // Genre list (uflix shows them as comma-separated list in card-imdb/etc)
        const genres = [];
        const genreList = html.match(/<li class="list-inline-item"\s+title="([^"]+)">([^<]+)<\/li>/g);
        if (genreList) {
            for (const g of genreList) {
                const mm = g.match(/title="([^"]+)"/);
                if (mm) genres.push(mm[1]);
            }
        }
        const detail = { imdbId, description, genres };
        this.detailCache.set(slug, detail);
        return detail;
    }

    /** Build a normalized frontend item from a card + detail (if available). */
    _toItem(card, detail = null) {
        const imdbId = detail?.imdbId || '';
        // Use uflix slug as ID (stable across reloads)
        const id = `uflix-${card.slug}`;
        const streams = [];
        if (imdbId) {
            streams.push({ label: 'VidSrc.me', provider: 'vidsrc', url: `https://vidsrc.me/embed/movie?imdb=${imdbId}`, quality: '1080p', format: 'embed' });
            streams.push({ label: 'SuperEmbed', provider: 'superembed', url: `https://multiembed.mov/?video_id=${imdbId}`, quality: '1080p', format: 'embed' });
            streams.push({ label: 'VidSrc.to', provider: 'vidsrc', url: `https://vidsrc.to/embed/movie/${imdbId}`, quality: '1080p', format: 'embed' });
            streams.push({ label: '2Embed', provider: '2embed', url: `https://www.2embed.cc/embed/${imdbId}`, quality: '720p', format: 'embed' });
        } else {
            // Fall back to slug-based URL — uflix itself hosts the player
            streams.push({ label: 'Uflix', provider: 'uflix', url: `${this.baseUrl}/movie/${card.slug}`, quality: '720p', format: 'page' });
        }
        return {
            id,
            title: card.title,
            year: card.year,
            type: 'movie',
            imdbId,
            tmdbId: '',
            genres: detail?.genres?.length ? detail.genres : (card.genre ? [card.genre] : []),
            rating: card.rating != null ? String(card.rating) : 'NR',
            runtime: 0,
            durationMinutes: 0,
            overview: detail?.description || '',
            poster: card.poster?.startsWith('http') ? card.poster : `${this.baseUrl}${card.poster}`,
            backdrop: '',
            posterPath: '',
            backdropPath: '',
            sourceName: this.sourceName,
            sourceOrigin: 'uflix-html',
            streams
        };
    }

    getCatalog() { return []; }

    async search(query) {
        // uflix search uses ?s= parameter (no separate search page reliably,
        // so we fall back to listings). If we get a query, also try a real search page.
        if (query) {
            const searchHtml = await this._fetchHtml(`${this.baseUrl}/search/${encodeURIComponent(query)}`);
            if (searchHtml) {
                const cards = this._parseCardsFromHtml(searchHtml);
                if (cards.length > 0) {
                    const items = [];
                    for (const c of cards) {
                        const detail = await this.fetchDetail(c.slug).catch(() => null);
                        items.push(this._toItem(c, detail));
                    }
                    return items;
                }
            }
        }
        // Fallback: list recent movies and filter by title match
        const cards = await this.fetchListings(1);
        const lc = (query || '').toLowerCase();
        const filtered = lc ? cards.filter(c => c.title.toLowerCase().includes(lc)) : cards;
        const items = [];
        for (const c of filtered.slice(0, 30)) {
            const detail = await this.fetchDetail(c.slug).catch(() => null);
            items.push(this._toItem(c, detail));
        }
        return items;
    }

    async browseByGenre(genre) {
        const cards = await this.fetchListings(PAGES_TO_SCRAPE);
        const lc = (genre || '').toLowerCase();
        const filtered = cards.filter(c => (c.genre || '').toLowerCase().includes(lc));
        const items = [];
        for (const c of filtered.slice(0, 30)) {
            const detail = await this.fetchDetail(c.slug).catch(() => null);
            items.push(this._toItem(c, detail));
        }
        return items;
    }

    async extractStream(movieUrl) {
        // movieUrl is "uflix-<slug>"
        const slug = String(movieUrl).replace(/^uflix-/, '');
        const detail = await this.fetchDetail(slug);
        if (detail?.imdbId) return `https://vidsrc.to/embed/movie/${detail.imdbId}`;
        return `${this.baseUrl}/movie/${slug}`;
    }
}
