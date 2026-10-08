import { ScraperAdapter } from './ScraperAdapter.js';

/**
 * LegalCatalogAdapter - Public domain / CC-licensed content sources
 * 
 * Sources: Internet Archive, Blender Open Movies, Pixabay, Pexels, 
 * Wikimedia Commons, Prelinger Archives
 * 
 * Priority: 1 (highest - always tried first)
 * Legal: true
 */
export class LegalCatalogAdapter extends ScraperAdapter {
    constructor() {
        super('LegalCatalog', '', {
            type: 'scraper',
            isLegal: true,
            priority: 1,
            enabled: true
        });
    }

    async search(query) {
        // Delegate to existing LegalCatalogScraper
        const { LegalCatalogScraper } = await import('../../scrapers/LegalCatalogScraper.js');
        const scraper = new LegalCatalogScraper();
        const results = await scraper.search(query);
        
        return results.map(r => ({
            titleId: r.id,
            externalId: r.id,
            title: r.title,
            year: r.releaseYear,
            type: r.category,
            poster: r.posterUrl,
            url: r.sources[0]?.url
        }));
    }

    async getAvailability(titleId, metadata) {
        const { LegalCatalogScraper } = await import('../../scrapers/LegalCatalogScraper.js');
        const scraper = new LegalCatalogScraper();
        const catalog = scraper.getCatalog();
        const item = catalog.find(m => m.id === titleId || m.url === titleId);
        
        if (!item || !item.sources) return [];
        
        return item.sources.map(src => ({
            sourceId: 'legal_catalog',
            status: 'available',
            externalId: titleId,
            externalUrl: src.url,
            qualityOptions: [src.resolution].filter(Boolean),
            formatOptions: [src.format].filter(Boolean),
            playbackUrl: src.url,
            priority: 1,
            isLegal: true
        }));
    }

    async healthCheck() {
        // Legal catalog is static - always healthy if data exists
        return { healthy: true, metrics: this.health };
    }
}

/**
 * CuratedCatalogAdapter - Hand-curated seed catalog
 * 
 * Priority: 1 (highest)
 * Legal: true
 */
export class CuratedCatalogAdapter extends ScraperAdapter {
    constructor() {
        super('CuratedCatalog', '', {
            type: 'curated',
            isLegal: true,
            priority: 1,
            enabled: true
        });
    }

    async search(query) {
        // Query the local seed catalog
        const { Database } = await import('../../db/database.ts');
        const database = new Database();
        const allMedia = database.getAllMedia(true);
        
        const lowerQuery = query.toLowerCase();
        const results = allMedia
            .filter(m => 
                m.title.toLowerCase().includes(lowerQuery) ||
                m.description.toLowerCase().includes(lowerQuery) ||
                m.genres.some(g => g.toLowerCase().includes(lowerQuery))
            )
            .slice(0, 20);
        
        return results.map(r => ({
            titleId: r.id,
            externalId: r.id,
            title: r.title,
            year: r.releaseYear,
            type: r.category,
            poster: r.posterUrl,
            url: r.sources[0]?.url
        }));
    }

    async getAvailability(titleId, metadata) {
        const { Database } = await import('../../db/database.ts');
        const database = new Database();
        const item = database.getMediaById(titleId);
        
        if (!item || !item.sources) return [];
        
        return item.sources.map(src => ({
            sourceId: 'curated_catalog',
            status: 'available',
            externalId: titleId,
            externalUrl: src.url,
            qualityOptions: [src.resolution].filter(Boolean),
            formatOptions: [src.format].filter(Boolean),
            playbackUrl: src.url,
            priority: 1,
            isLegal: true
        }));
    }
}