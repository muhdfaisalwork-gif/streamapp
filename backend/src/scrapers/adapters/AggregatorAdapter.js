import { ScraperAdapter } from './ScraperAdapter.js';

/**
 * AggregatorAdapter - Third-party aggregator site scrapers
 * 
 * Wraps the existing per-site Playwright scrapers (BeeTV, MovieBoxHD, 
 * OnStream, HDOBox, 123Movies, YTS, YIFY, TMovies, Donkey, UFlix).
 * 
 * Priority: 3 (fallback - may be unstable, legal gray area)
 * Legal: false (aggregator sites of varying legality)
 * Type: aggregator
 */
export class AggregatorAdapter extends ScraperAdapter {
    constructor() {
        super('Aggregator', '', {
            type: 'aggregator',
            isLegal: false,
            priority: 3,
            enabled: true
        });
        this.siteScrapers = new Map();
        this.enabledSiteNames = new Set();
        this._initSiteScrapers();
    }

    _initSiteScrapers() {
        // Import and instantiate all site scrapers
        // These are lazily loaded to avoid import overhead
        this.siteScraperClasses = {
            'BeeTV': '../scrapers/sites/BeetvScraper.js',
            'MovieBoxHD': '../scrapers/sites/MovieboxHdScraper.js',
            'OnStream': '../scrapers/sites/OnstreamScraper.js',
            'HDOBox': '../scrapers/sites/HdoboxScraper.js',
            '123Movies': '../scrapers/sites/Movies123Scraper.js',
            'YTS': '../scrapers/sites/YtsScraper.js',
            'YIFY': '../scrapers/sites/YifyScraper.js',
            'TMovies': '../scrapers/sites/TmoviesScraper.js',
            'Donkey': '../scrapers/sites/DonkeyScraper.js',
            'UFlix': '../scrapers/sites/UflixScraper.js'
        };

        // Parse ENABLED_SOURCES env var
        const enabled = (process.env.ENABLED_SOURCES || 
            'BeeTV,MovieBoxHD,OnStream,HDOBox,123Movies,YTS,YIFY,TMovies,Donkey,UFlix')
            .split(',')
            .map(s => s.trim())
            .filter(Boolean);
        
        this.enabledSiteNames = new Set(enabled);
        console.log(`[AggregatorAdapter] Enabled sites: ${[...this.enabledSiteNames].join(', ')}`);
    }

    async _getSiteScraper(siteName) {
        if (this.siteScrapers.has(siteName)) {
            return this.siteScrapers.get(siteName);
        }

        const path = this.siteScraperClasses[siteName];
        if (!path) return null;

        try {
            const module = await import(path);
            // Find the scraper class (named like BeetvScraper, MovieboxHdScraper, etc.)
            const className = Object.keys(module).find(k => k.endsWith('Scraper'));
            if (!className) return null;

            const ScraperClass = module[className];
            const instance = new ScraperClass();
            this.siteScrapers.set(siteName, instance);
            return instance;
        } catch (e) {
            console.warn(`[AggregatorAdapter] Failed to load ${siteName}: ${e.message}`);
            return null;
        }
    }

    async search(query) {
        const enabledSites = [...this.enabledSiteNames]
            .map(name => this._getSiteScraper(name))
            .filter(Boolean);

        if (enabledSites.length === 0) return [];

        const PER_SOURCE_TIMEOUT_MS = 8000;
        const wrapped = enabledSites.map(async (scraperPromise) => {
            try {
                const scraper = await scraperPromise;
                const results = await Promise.race([
                    scraper.search(query),
                    new Promise((_, reject) => 
                        setTimeout(() => reject(new Error('Timeout')), PER_SOURCE_TIMEOUT_MS)
                    )
                ]);
                return results.map(r => ({
                    ...r,
                    sourceName: scraper.sourceName,
                    sourcePriority: 3
                }));
            } catch (e) {
                console.warn(`[AggregatorAdapter] ${(await scraperPromise)?.sourceName || 'unknown'} search failed: ${e.message}`);
                return [];
            }
        });

        const results = await Promise.allSettled(wrapped);
        const combined = [];
        for (const result of results) {
            if (result.status === 'fulfilled' && Array.isArray(result.value)) {
                combined.push(...result.value);
            }
        }
        return combined;
    }

    async getAvailability(titleId, metadata) {
        // For aggregator sources, we need to search first to get the source-specific URL
        // Then extract the stream. This is a simplified version.
        if (!metadata?.title) return [];

        const searchResults = await this.search(metadata.title);
        const availability = [];

        for (const result of searchResults.slice(0, 3)) { // Top 3 matches
            const scraper = await this._getSiteScraper(result.sourceName);
            if (!scraper) continue;

            try {
                const stream = await Promise.race([
                    scraper.extractStream(`${result.sourceName}|${result.url}`),
                    new Promise((_, reject) => 
                        setTimeout(() => reject(new Error('Timeout')), 15000)
                    )
                ]);

                if (stream?.url) {
                    availability.push({
                        sourceId: `aggregator_${result.sourceName.toLowerCase()}`,
                        status: 'available',
                        externalId: result.externalId,
                        externalUrl: result.url,
                        qualityOptions: stream.qualityOptions || ['1080p', '720p'],
                        formatOptions: stream.formatOptions || ['hls', 'mp4'],
                        playbackUrl: stream.url,
                        backupUrl: stream.backupUrl,
                        sourceName: result.sourceName,
                        priority: 3,
                        isLegal: false,
                        requiresAuth: stream.requiresAuth || false
                    });
                }
            } catch (e) {
                console.warn(`[AggregatorAdapter] ${result.sourceName} extract failed: ${e.message}`);
            }
        }

        return availability;
    }

    /**
     * Get enabled site names
     * @returns {Array<string>}
     */
    getEnabledSites() {
        return [...this.enabledSiteNames];
    }

    /**
     * Enable/disable a specific site
     * @param {string} siteName 
     * @param {boolean} enabled
     */
    setSiteEnabled(siteName, enabled) {
        if (enabled) {
            this.enabledSiteNames.add(siteName);
        } else {
            this.enabledSiteNames.delete(siteName);
        }
    }

    async healthCheck() {
        // Check each enabled site
        const siteHealth = {};
        for (const siteName of this.enabledSiteNames) {
            const scraper = await this._getSiteScraper(siteName);
            if (scraper) {
                siteHealth[siteName] = scraper.health || { consecutiveFailures: 0 };
            }
        }

        const totalFailures = Object.values(siteHealth).reduce((sum, h) => sum + (h.consecutiveFailures || 0), 0);
        
        return { 
            healthy: totalFailures < 10, // Allow some failures across sites
            metrics: { 
                ...this.health,
                sites: siteHealth,
                enabledCount: this.enabledSiteNames.size
            } 
        };
    }
}