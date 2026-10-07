import { BaseScraper } from '../BaseScraper.js';

/**
 * ScraperAdapter - Abstract base class for all source adapters
 * 
 * This framework separates concerns:
 * - LegalCatalogAdapter: Public domain / CC-licensed content (always legal)
 * - TMDBWatchProviderAdapter: Legal streaming provider links from TMDB (metadata only)
 * - AggregatorAdapter: Third-party aggregator sites (opt-in, may be unstable)
 * 
 * Each adapter implements:
 * - search(query): Find titles by query
 * - getAvailability(titleId): Get playback availability for a known title
 * - healthCheck(): Return source health metrics
 */

export class ScraperAdapter extends BaseScraper {
    constructor(sourceName, baseUrl, options = {}) {
        super(sourceName, baseUrl);
        this.type = options.type || 'scraper'; // 'scraper', 'aggregator', 'embed', 'metadata'
        this.enabled = options.enabled !== false;
        this.isLegal = options.isLegal || false;
        this.priority = options.priority || 3; // 1=legal, 2=tmdb_watch, 3=aggregator
        this.health = {
            successRate: 1.0,
            avgLatencyMs: 0,
            lastSuccess: null,
            lastFailure: null,
            consecutiveFailures: 0,
            totalRequests: 0,
            totalSuccesses: 0
        };
    }

    /**
     * Search for titles matching query
     * @param {string} query - Search query
     * @returns {Promise<Array<{titleId, externalId, title, year, type, poster, url}>>}
     */
    async search(query) {
        throw new Error('search() must be implemented by subclass');
    }

    /**
     * Get playback availability for a known title
     * @param {string} titleId - Internal catalog title ID
     * @param {Object} metadata - TMDB/IMDb metadata for matching
     * @returns {Promise<Array<{sourceId, status, externalId, externalUrl, qualityOptions, formatOptions, playbackUrl}>>}
     */
    async getAvailability(titleId, metadata) {
        throw new Error('getAvailability() must be implemented by subclass');
    }

    /**
     * Health check for circuit breaker pattern
     * @returns {Promise<{healthy: boolean, metrics: Object}>}
     */
    async healthCheck() {
        return { healthy: this.health.consecutiveFailures < 5, metrics: this.health };
    }

    /**
     * Record successful request
     * @param {number} latencyMs
     */
    recordSuccess(latencyMs) {
        this.health.totalRequests++;
        this.health.totalSuccesses++;
        this.health.successRate = this.health.totalSuccesses / this.health.totalRequests;
        this.health.avgLatencyMs = (this.health.avgLatencyMs * (this.health.totalRequests - 1) + latencyMs) / this.health.totalRequests;
        this.health.lastSuccess = Date.now();
        this.health.consecutiveFailures = 0;
    }

    /**
     * Record failed request
     * @param {Error} error
     */
    recordFailure(error) {
        this.health.totalRequests++;
        this.health.successRate = this.health.totalSuccesses / this.health.totalRequests;
        this.health.lastFailure = Date.now();
        this.health.consecutiveFailures++;
        console.warn(`[${this.sourceName}] Failure #${this.health.consecutiveFailures}: ${error.message}`);
    }

    /**
     * Get source priority for availability ordering
     * @returns {number}
     */
    getPriority() {
        return this.priority;
    }

    /**
     * Check if source is legal
     * @returns {boolean}
     */
    isLegalSource() {
        return this.isLegal;
    }
}

/**
 * Adapter Registry - Manages all source adapters with health monitoring
 */
export class AdapterRegistry {
    constructor() {
        this.adapters = new Map();
        this.healthCheckInterval = null;
    }

    register(adapter) {
        this.adapters.set(adapter.sourceName, adapter);
    }

    unregister(sourceName) {
        this.adapters.delete(sourceName);
    }

    get(sourceName) {
        return this.adapters.get(sourceName);
    }

    getAll() {
        return Array.from(this.adapters.values());
    }

    getEnabled() {
        return this.getAll().filter(a => a.enabled);
    }

    getByPriority() {
        return this.getEnabled().sort((a, b) => a.getPriority() - b.getPriority());
    }

    getLegalSources() {
        return this.getEnabled().filter(a => a.isLegalSource());
    }

    getAggregatorSources() {
        return this.getEnabled().filter(a => !a.isLegalSource() && a.type !== 'metadata');
    }

    /**
     * Start periodic health checks
     * @param {number} intervalMs - Check interval in milliseconds
     */
    startHealthChecks(intervalMs = 300000) { // 5 minutes default
        if (this.healthCheckInterval) return;
        this.healthCheckInterval = setInterval(async () => {
            for (const adapter of this.getEnabled()) {
                try {
                    await adapter.healthCheck();
                } catch (e) {
                    adapter.recordFailure(e);
                }
            }
        }, intervalMs);
    }

    stopHealthChecks() {
        if (this.healthCheckInterval) {
            clearInterval(this.healthCheckInterval);
            this.healthCheckInterval = null;
        }
    }

    /**
     * Get aggregated health status for all sources
     * @returns {Object}
     */
    getHealthStatus() {
        const status = {};
        for (const [name, adapter] of this.adapters) {
            status[name] = {
                enabled: adapter.enabled,
                type: adapter.type,
                priority: adapter.priority,
                isLegal: adapter.isLegal,
                health: adapter.health
            };
        }
        return status;
    }
}

// Singleton instance
export const adapterRegistry = new AdapterRegistry();