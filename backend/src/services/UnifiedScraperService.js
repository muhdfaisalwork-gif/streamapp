import { adapterRegistry, initializeAdapters, getAdaptersByPriority } from './adapters/index.js';

/**
 * UnifiedScraperService - Main entry point for all scraping operations
 * 
 * This service coordinates between different source adapters based on priority:
 * 1. Legal sources (Curated, LegalCatalog) - Always tried first
 * 2. TMDB Watch Providers - Legal streaming links (metadata only)
 * 3. Aggregator sources - Fallback for hard-to-find content
 * 
 * Features:
 * - Priority-based source selection
 * - Circuit breaker pattern via health monitoring
 * - Graceful degradation when sources fail
 * - Unified search and availability APIs
 */
export class UnifiedScraperService {
    constructor() {
        this.initialized = false;
        this.searchCache = new Map();
        this.availabilityCache = new Map();
        this.cacheTTL = 5 * 60 * 1000; // 5 minutes
    }

    /**
     * Initialize all adapters
     */
    async initialize() {
        if (this.initialized) return;
        await initializeAdapters();
        this.initialized = true;
    }

    /**
     * Search across all enabled sources by priority
     * @param {string} query - Search query
     * @param {Object} options - Search options
     * @returns {Promise<Array>} Combined search results
     */
    async search(query, options = {}) {
        if (!this.initialized) await this.initialize();
        
        const cacheKey = `search:${query}:${JSON.stringify(options)}`;
        const cached = this.searchCache.get(cacheKey);
        if (cached && Date.now() - cached.timestamp < this.cacheTTL) {
            return cached.data;
        }

        const adapters = getAdaptersByPriority(adapterRegistry);
        const allResults = [];
        const errors = [];

        for (const adapter of adapters) {
            try {
                const results = await adapter.search(query);
                // Tag results with source info
                const tagged = results.map(r => ({
                    ...r,
                    sourceName: adapter.sourceName,
                    sourcePriority: adapter.getPriority(),
                    isLegal: adapter.isLegalSource()
                }));
                allResults.push(...tagged);
            } catch (e) {
                errors.push({ source: adapter.sourceName, error: e.message });
                adapter.recordFailure(e);
            }
        }

        // Deduplicate by title similarity
        const deduplicated = this._deduplicateResults(allResults);
        
        const result = {
            results: deduplicated,
            sourcesQueried: adapters.map(a => a.sourceName),
            errors,
            timestamp: Date.now()
        };

        this.searchCache.set(cacheKey, { data: result, timestamp: Date.now() });
        return result;
    }

    /**
     * Get playback availability for a title across all sources
     * @param {string} titleId - Internal catalog title ID
     * @param {Object} metadata - TMDB/IMDb metadata for matching
     * @returns {Promise<Array>} Availability records sorted by priority
     */
    async getAvailability(titleId, metadata = {}) {
        if (!this.initialized) await this.initialize();
        
        const cacheKey = `avail:${titleId}`;
        const cached = this.availabilityCache.get(cacheKey);
        if (cached && Date.now() - cached.timestamp < this.cacheTTL) {
            return cached.data;
        }

        const adapters = getAdaptersByPriority(adapterRegistry);
        const allAvailability = [];

        for (const adapter of adapters) {
            try {
                const availability = await adapter.getAvailability(titleId, metadata);
                const tagged = availability.map(a => ({
                    ...a,
                    sourceName: adapter.sourceName,
                    sourcePriority: adapter.getPriority(),
                    isLegal: adapter.isLegalSource()
                }));
                allAvailability.push(...tagged);
            } catch (e) {
                console.warn(`[UnifiedScraper] ${adapter.sourceName} availability failed: ${e.message}`);
                adapter.recordFailure(e);
            }
        }

        // Sort by priority (legal first), then by quality
        const sorted = allAvailability.sort((a, b) => {
            if (a.sourcePriority !== b.sourcePriority) {
                return a.sourcePriority - b.sourcePriority;
            }
            // Within same priority, prefer higher quality
            const aHas1080p = a.qualityOptions?.includes('1080p') || a.qualityOptions?.includes('4K');
            const bHas1080p = b.qualityOptions?.includes('1080p') || b.qualityOptions?.includes('4K');
            if (aHas1080p !== bHas1080p) return aHas1080p ? -1 : 1;
            return 0;
        });

        const result = {
            availability: sorted,
            sourcesQueried: adapters.map(a => a.sourceName),
            timestamp: Date.now()
        };

        this.availabilityCache.set(cacheKey, { data: result, timestamp: Date.now() });
        return result;
    }

    /**
     * Get health status of all sources
     * @returns {Promise<Object>}
     */
    async getHealthStatus() {
        if (!this.initialized) await this.initialize();
        return adapterRegistry.getHealthStatus();
    }

    /**
     * Enable/disable a specific source
     * @param {string} sourceName
     * @param {boolean} enabled
     */
    setSourceEnabled(sourceName, enabled) {
        const adapter = adapterRegistry.get(sourceName);
        if (adapter) {
            adapter.enabled = enabled;
            console.log(`[UnifiedScraper] ${sourceName} ${enabled ? 'enabled' : 'disabled'}`);
        }
    }

    /**
     * Get source by name
     * @param {string} sourceName
     * @returns {ScraperAdapter|null}
     */
    getSource(sourceName) {
        return adapterRegistry.get(sourceName);
    }

    /**
     * Clear caches
     */
    clearCache() {
        this.searchCache.clear();
        this.availabilityCache.clear();
    }

    /**
     * Deduplicate search results by title similarity
     * @private
     */
    _deduplicateResults(results) {
        const seen = new Map();
        const unique = [];

        for (const result of results) {
            const key = this._normalizeTitle(result.title);
            if (!seen.has(key)) {
                seen.set(key, result);
                unique.push(result);
            } else {
                // Keep the higher priority (legal) source
                const existing = seen.get(key);
                if (result.sourcePriority < existing.sourcePriority) {
                    seen.set(key, result);
                    // Replace in unique array
                    const idx = unique.indexOf(existing);
                    if (idx !== -1) unique[idx] = result;
                }
            }
        }

        return unique;
    }

    /**
     * Normalize title for deduplication
     * @private
     */
    _normalizeTitle(title) {
        return (title || '')
            .toLowerCase()
            .replace(/[^a-z0-9]/g, '')
            .trim();
    }
}

// Singleton instance
export const unifiedScraper = new UnifiedScraperService();

/**
 * Convenience function for search
 */
export async function searchAllSources(query, options) {
    return unifiedScraper.search(query, options);
}

/**
 * Convenience function for availability
 */
export async function getAvailabilityForTitle(titleId, metadata) {
    return unifiedScraper.getAvailability(titleId, metadata);
}