import { ScraperAdapter } from './ScraperAdapter.js';

/**
 * TMDBWatchProviderAdapter - Legal streaming provider links from TMDB
 * 
 * This adapter reads from the title_streaming_providers table which is 
 * populated by the tmdb_watch_providers.py script. It provides "where to watch"
 * metadata but does NOT host or embed content.
 * 
 * Priority: 2 (second - legal streaming links)
 * Legal: true (references to licensed services)
 * Type: metadata
 */
export class TMDBWatchProviderAdapter extends ScraperAdapter {
    constructor() {
        super('TMDBWatchProviders', 'https://api.themoviedb.org/3', {
            type: 'metadata',
            isLegal: true,
            priority: 2,
            enabled: true
        });
        this.providerCache = new Map();
    }

    async search(query) {
        // This adapter doesn't do primary search - it enriches existing titles
        return [];
    }

    async getAvailability(titleId, metadata) {
        const { Database } = await import('../../db/database.ts');
        const database = new Database();
        
        // Query the title_streaming_providers table
        const providers = database.getStreamingProvidersForTitle ? 
            database.getStreamingProvidersForTitle(titleId) : 
            await this._queryStreamingProviders(titleId, database);
        
        return providers.map(p => ({
            sourceId: `tmdb_watch_${p.providerSlug}`,
            status: 'available',
            externalId: p.titleId,
            externalUrl: p.deepLink || p.baseUrl,
            qualityOptions: ['1080p', '720p', '4K'].filter(q => p.qualityOptions?.includes(q)),
            formatOptions: ['hls', 'dash'].filter(f => p.formatOptions?.includes(f)),
            playbackUrl: null, // We don't host playback - deep link to provider
            deepLink: p.deepLink,
            providerName: p.providerName,
            availabilityType: p.availabilityType, // subscription, rent, buy, free, ads_supported
            region: p.region || 'US',
            priority: 2,
            isLegal: true,
            isMetadataOnly: true // This source provides links, not direct streams
        }));
    }

    async _queryStreamingProviders(titleId, database) {
        // Direct SQL query to title_streaming_providers table
        const stmt = database.db.prepare(`
            SELECT 
                tsp.title_id,
                tsp.provider_id,
                tsp.availability_type,
                tsp.region,
                tsp.deep_link,
                tsp.free_access_ref,
                tsp.last_checked_at,
                sp.slug as provider_slug,
                sp.name as provider_name,
                sp.base_url,
                sp.logo_url
            FROM title_streaming_providers tsp
            JOIN streaming_providers sp ON tsp.provider_id = sp.id
            WHERE tsp.title_id = ?
        `);
        return stmt.all(titleId);
    }

    /**
     * Get all supported provider slugs for filtering
     * @returns {Array<string>}
     */
    getSupportedProviders() {
        return [
            'netflix', 'disney-plus', 'prime-video', 'apple-tv-plus', 'max',
            'hulu', 'paramount-plus', 'peacock', 'discovery-plus', 'crunchyroll'
        ];
    }

    async healthCheck() {
        // Check if we have recent watch provider data
        const { Database } = await import('../../db/database.ts');
        const database = new Database();
        
        const count = database.db.prepare(`
            SELECT COUNT(*) as count FROM title_streaming_providers 
            WHERE last_checked_at > ?
        `).get(Math.floor(Date.now() / 1000) - 86400 * 7); // Last 7 days
        
        return { 
            healthy: count && count.count > 0, 
            metrics: { 
                ...this.health,
                recentProviderLinks: count?.count || 0
            } 
        };
    }
}