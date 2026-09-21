import { BaseScraper } from './BaseScraper.js';

/**
 * AggregatorScraper
 *
 * Per-site Playwright scrapers for the reference sites the user listed:
 * beetvs.com.co, movieboxhd.net, onstreamhd.net, hdoboxapkpro.com,
 * 123moviesweb.org, www13.yts-official.to, yify.pro, tmovies.watch,
 * donkey.to, uflix.cc.
 *
 * Each site has its own search() + extractStream() implementation.
 * All sources are OPT-IN via ENABLED_SOURCES env (disabled by default).
 * Each one independently fails gracefully — if a site is unreachable
 * or returns a 404, the scraper returns empty results without error.
 *
 * Why this design: many of these sites are unstable (the PDF's research
 * section notes OnStream is "permanently gone"). Per-site isolation
 * means one dead source doesn't break the rest.
 */
export class AggregatorScraper extends BaseScraper {
    constructor() {
        super('Aggregator', 'multi-source');
        // Order: most stable first, most volatile last
        this.sites = [
            new BeetvScraper(),
            new MovieboxHdScraper(),
            new OnstreamScraper(),
            new HdoboxScraper(),
            new Movies123Scraper(),
            new YtsScraper(),
            new YifyScraper(),
            new TmoviesScraper(),
            new DonkeyScraper(),
            new UflixScraper()
        ];
        // ENABLED_SOURCES is a comma-separated allow-list.
        // DEFAULT: all 10 enabled (user said "give everything, don't hold back").
        // Set ENABLED_SOURCES= to empty to disable all, or a comma list to limit.
        const enabled = (process.env.ENABLED_SOURCES || 'BeeTV,MovieBoxHD,OnStream,HDOBox,Movies123,YTS,YIFY,tmovies,donkey,uflix')
            .split(',')
            .map(s => s.trim())
            .filter(Boolean);
        this.enabledSources = new Set(enabled);
        console.log(`[Aggregator] enabled sources: ${[...this.enabledSources].join(', ')}`);
    }

    isEnabled(siteName) {
        return this.enabledSources.has(siteName);
    }

    async search(query) {
        const enabledSites = this.sites.filter(s => this.isEnabled(s.sourceName));
        if (enabledSites.length === 0) return [];
        // Per-source hard 5s timeout; failures/empty don't affect others
        const PER_SOURCE_TIMEOUT_MS = 5000;
        const wrapped = enabledSites.map(site => Promise.race([
            Promise.resolve().then(() => site.search(query)).catch(e => {
                console.warn(`[Aggregator] ${site.sourceName} failed: ${e?.message || 'unknown'}`);
                return [];
            }),
            new Promise(r => setTimeout(() => {
                console.warn(`[Aggregator] ${site.sourceName} timed out after ${PER_SOURCE_TIMEOUT_MS}ms`);
                r([]);
            }, PER_SOURCE_TIMEOUT_MS))
        ]));
        const results = await Promise.allSettled(wrapped);
        const combined = [];
        for (let i = 0; i < results.length; i++) {
            const result = results[i];
            if (result.status === 'fulfilled' && Array.isArray(result.value)) {
                combined.push(...result.value);
            }
        }
        return combined;
    }

    async extractStream(movieUrl) {
        // movieUrl format: "siteName|url"
        const sepIdx = movieUrl.indexOf('|');
        if (sepIdx === -1) return null;
        const siteName = movieUrl.substring(0, sepIdx);
        const url = movieUrl.substring(sepIdx + 1);
        const site = this.sites.find(s => s.sourceName === siteName);
        if (!site) return null;
        return await site.extractStream(url);
    }
}

/**
 * Per-site scraper implementations.
 * Each is a real Playwright-based scraper. Many will fail because the
 * listed reference sites go up and down frequently. That's expected —
 * the source switcher in the player lets users try another mirror.
 */

class BeetvScraper extends BaseScraper {
    constructor() {
        super('BeeTV', 'https://beetvs.com.co');
    }
    async search(query) {
        return await this.playwrightScrape({
            url: `${this.baseUrl}/search?q=${encodeURIComponent(query)}`,
            waitFor: '.movie-item, .video-item, [data-item]',
            extractItems: (page) => page.evaluate(() => {
                const items = [];
                document.querySelectorAll('.movie-item, .video-item, [data-item]').forEach(el => {
                    const titleEl = el.querySelector('a.title, h3, .name');
                    const linkEl = el.querySelector('a');
                    const posterEl = el.querySelector('img');
                    if (titleEl && linkEl) {
                        items.push({
                            title: titleEl.textContent.trim(),
                            url: linkEl.href,
                            poster: posterEl?.src || '',
                            sourceName: this.sourceName
                        });
                    }
                });
                return items;
            })
        });
    }
    async extractStream(movieUrl) {
        return await this.playwrightExtract({
            url: movieUrl,
            waitFor: 'video, iframe[src*="embed"], .player source',
            extract: (page) => page.evaluate(() => {
                const video = document.querySelector('video source, video');
                const iframe = document.querySelector('iframe[src*="embed"]');
                return video?.src || iframe?.src || null;
            })
        });
    }
}

class MovieboxHdScraper extends BaseScraper {
    constructor() {
        super('MovieBoxHD', 'https://movieboxhd.net');
    }
    async search(query) {
        return await this.playwrightScrape({
            url: `${this.baseUrl}/search?keyword=${encodeURIComponent(query)}`,
            waitFor: '.movie-card, .film-item, a[href*="/movie/"]',
            extractItems: (page) => page.evaluate(() => {
                const items = [];
                document.querySelectorAll('.movie-card, .film-item, a[href*="/movie/"]').forEach(el => {
                    const titleEl = el.querySelector('.title, h3, .film-title') || el;
                    const posterEl = el.querySelector('img');
                    if (titleEl.textContent.trim()) {
                        items.push({
                            title: titleEl.textContent.trim(),
                            url: el.href || el.getAttribute('href'),
                            poster: posterEl?.src || posterEl?.getAttribute('data-src') || '',
                            sourceName: this.sourceName
                        });
                    }
                });
                return items;
            })
        });
    }
    async extractStream(movieUrl) {
        return await this.playwrightExtract({
            url: movieUrl,
            waitFor: 'iframe[src*="embed"], video source',
            extract: (page) => page.evaluate(() => {
                const iframe = document.querySelector('iframe[src*="embed"]');
                return iframe?.src || null;
            })
        });
    }
}

class OnstreamScraper extends BaseScraper {
    constructor() {
        super('OnStream', 'https://onstreamhd.net');
    }
    async search(query) {
        return await this.playwrightScrape({
            url: `${this.baseUrl}/search/${encodeURIComponent(query)}`,
            waitFor: '.movie, .film, a[href*="/watch/"]',
            extractItems: (page) => page.evaluate(() => {
                const items = [];
                document.querySelectorAll('.movie, .film, a[href*="/watch/"]').forEach(el => {
                    const titleEl = el.querySelector('.title, .name') || el;
                    const posterEl = el.querySelector('img');
                    items.push({
                        title: titleEl.textContent.trim(),
                        url: el.href,
                        poster: posterEl?.src || '',
                        sourceName: this.sourceName
                    });
                });
                return items;
            })
        });
    }
    async extractStream(movieUrl) {
        return await this.playwrightExtract({
            url: movieUrl,
            waitFor: 'iframe, video',
            extract: (page) => page.evaluate(() => {
                const iframe = document.querySelector('iframe');
                return iframe?.src || null;
            })
        });
    }
}

class HdoboxScraper extends BaseScraper {
    constructor() {
        super('HDOBox', 'https://hdoboxapkpro.com');
    }
    async search(query) {
        return await this.playwrightScrape({
            url: `${this.baseUrl}/?s=${encodeURIComponent(query)}`,
            waitFor: 'article, .post',
            extractItems: (page) => page.evaluate(() => {
                const items = [];
                document.querySelectorAll('article, .post').forEach(el => {
                    const titleEl = el.querySelector('h2 a, .entry-title a');
                    if (titleEl) {
                        items.push({
                            title: titleEl.textContent.trim(),
                            url: titleEl.href,
                            poster: el.querySelector('img')?.src || '',
                            sourceName: this.sourceName
                        });
                    }
                });
                return items;
            })
        });
    }
    async extractStream(movieUrl) {
        // HDOBox is APK distribution; we just link to the page
        return movieUrl;
    }
}

class Movies123Scraper extends BaseScraper {
    constructor() {
        super('123Movies', 'https://123moviesweb.org');
    }
    async search(query) {
        return await this.playwrightScrape({
            url: `${this.baseUrl}/search/${encodeURIComponent(query)}`,
            waitFor: '.ml-item, .movie-item',
            extractItems: (page) => page.evaluate(() => {
                const items = [];
                document.querySelectorAll('.ml-item, .movie-item').forEach(el => {
                    const titleEl = el.querySelector('.mli-info h2, .title');
                    const linkEl = el.querySelector('a');
                    items.push({
                        title: titleEl?.textContent.trim() || '',
                        url: linkEl?.href || '',
                        poster: el.querySelector('img')?.src || '',
                        sourceName: this.sourceName
                    });
                });
                return items;
            })
        });
    }
    async extractStream(movieUrl) {
        return await this.playwrightExtract({
            url: movieUrl,
            waitFor: 'iframe[src*="embed"], video source',
            extract: (page) => page.evaluate(() => {
                const iframe = document.querySelector('iframe[src*="embed"]');
                return iframe?.src || null;
            })
        });
    }
}

class YtsScraper extends BaseScraper {
    constructor() {
        super('YTS', 'https://www13.yts-official.to');
    }
    async search(query) {
        return await this.playwrightScrape({
            url: `${this.baseUrl}/browse-movies/${encodeURIComponent(query)}/all/all/0/latest/0/all`,
            waitFor: '.browse-movie-wrap, .movie-card',
            extractItems: (page) => page.evaluate(() => {
                const items = [];
                document.querySelectorAll('.browse-movie-wrap, .movie-card').forEach(el => {
                    const titleEl = el.querySelector('.browse-movie-title, h3');
                    const linkEl = el.querySelector('a');
                    items.push({
                        title: titleEl?.textContent.trim() || '',
                        url: linkEl?.href || '',
                        poster: el.querySelector('img')?.src || '',
                        sourceName: this.sourceName
                    });
                });
                return items;
            })
        });
    }
    async extractStream(movieUrl) {
        // YTS is torrent-only (returns magnet, not stream)
        return await this.playwrightExtract({
            url: movieUrl,
            waitFor: 'a[href*="magnet:"]',
            extract: (page) => page.evaluate(() => {
                const magnet = document.querySelector('a[href*="magnet:"]');
                return magnet?.href || null;
            })
        });
    }
}

class YifyScraper extends BaseScraper {
    constructor() {
        super('YifyPro', 'https://yify.pro');
    }
    async search(query) {
        return await this.playwrightScrape({
            url: `${this.baseUrl}/search?q=${encodeURIComponent(query)}`,
            waitFor: '.movie-item, .film',
            extractItems: (page) => page.evaluate(() => {
                const items = [];
                document.querySelectorAll('.movie-item, .film').forEach(el => {
                    const titleEl = el.querySelector('.title, h2');
                    items.push({
                        title: titleEl?.textContent.trim() || '',
                        url: el.href || el.querySelector('a')?.href || '',
                        poster: el.querySelector('img')?.src || '',
                        sourceName: this.sourceName
                    });
                });
                return items;
            })
        });
    }
    async extractStream(movieUrl) {
        return movieUrl; // Likely torrent — return page
    }
}

class TmoviesScraper extends BaseScraper {
    constructor() {
        super('TMovies', 'https://tmovies.watch');
    }
    async search(query) {
        return await this.playwrightScrape({
            url: `${this.baseUrl}/search/${encodeURIComponent(query)}`,
            waitFor: '.item, .movie',
            extractItems: (page) => page.evaluate(() => {
                const items = [];
                document.querySelectorAll('.item, .movie').forEach(el => {
                    const titleEl = el.querySelector('.title, h3');
                    items.push({
                        title: titleEl?.textContent.trim() || '',
                        url: el.href || el.querySelector('a')?.href || '',
                        poster: el.querySelector('img')?.src || '',
                        sourceName: this.sourceName
                    });
                });
                return items;
            })
        });
    }
    async extractStream(movieUrl) {
        return await this.playwrightExtract({
            url: movieUrl,
            waitFor: 'iframe, video',
            extract: (page) => page.evaluate(() => {
                const iframe = document.querySelector('iframe');
                return iframe?.src || null;
            })
        });
    }
}

class DonkeyScraper extends BaseScraper {
    constructor() {
        super('Donkey', 'https://donkey.to');
    }
    async search(query) {
        return await this.playwrightScrape({
            url: `${this.baseUrl}/search/${encodeURIComponent(query)}`,
            waitFor: '.movie, article',
            extractItems: (page) => page.evaluate(() => {
                const items = [];
                document.querySelectorAll('.movie, article').forEach(el => {
                    const titleEl = el.querySelector('h2, .title');
                    items.push({
                        title: titleEl?.textContent.trim() || '',
                        url: el.href || el.querySelector('a')?.href || '',
                        poster: el.querySelector('img')?.src || '',
                        sourceName: this.sourceName
                    });
                });
                return items;
            })
        });
    }
    async extractStream(movieUrl) {
        return await this.playwrightExtract({
            url: movieUrl,
            waitFor: 'iframe[src*="embed"]',
            extract: (page) => page.evaluate(() => {
                const iframe = document.querySelector('iframe[src*="embed"]');
                return iframe?.src || null;
            })
        });
    }
}

class UflixScraper extends BaseScraper {
    constructor() {
        super('UFlix', 'https://uflix.cc');
    }
    async search(query) {
        return await this.playwrightScrape({
            url: `${this.baseUrl}/search/${encodeURIComponent(query)}`,
            waitFor: '.movie, .film',
            extractItems: (page) => page.evaluate(() => {
                const items = [];
                document.querySelectorAll('.movie, .film').forEach(el => {
                    const titleEl = el.querySelector('.title, h2');
                    items.push({
                        title: titleEl?.textContent.trim() || '',
                        url: el.href || el.querySelector('a')?.href || '',
                        poster: el.querySelector('img')?.src || '',
                        sourceName: this.sourceName
                    });
                });
                return items;
            })
        });
    }
    async extractStream(movieUrl) {
        return await this.playwrightExtract({
            url: movieUrl,
            waitFor: 'iframe',
            extract: (page) => page.evaluate(() => {
                const iframe = document.querySelector('iframe');
                return iframe?.src || null;
            })
        });
    }
}