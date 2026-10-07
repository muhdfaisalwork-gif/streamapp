/**
 * Scraper Adapters - Unified Source Adapter Framework
 * 
 * This module exports all source adapters and the registry.
 * 
 * Architecture:
 * - ScraperAdapter (abstract base)
 * - LegalCatalogAdapter (priority 1, legal)
 * - CuratedCatalogAdapter (priority 1, legal)
 * - TMDBWatchProviderAdapter (priority 2, legal, metadata-only)
 * - AggregatorAdapter (priority 3, non-legal)
 * - AdapterRegistry (manages all adapters, health monitoring)
 */

export { ScraperAdapter, AdapterRegistry, adapterRegistry } from './ScraperAdapter.js';
export { LegalCatalogAdapter, CuratedCatalogAdapter } from './LegalCatalogAdapter.js';
export { TMDBWatchProviderAdapter } from './TMDBWatchProviderAdapter.js';
export { AggregatorAdapter } from './AggregatorAdapter.js';

/**
 * Initialize all adapters and register with the global registry
 * @returns {Promise<AdapterRegistry>}
 */
export async function initializeAdapters() {
    const { adapterRegistry } = await import('./ScraperAdapter.js');
    
    // Legal sources (priority 1)
    const { LegalCatalogAdapter } = await import('./LegalCatalogAdapter.js');
    const { CuratedCatalogAdapter } = await import('./LegalCatalogAdapter.js');
    adapterRegistry.register(new LegalCatalogAdapter());
    adapterRegistry.register(new CuratedCatalogAdapter());
    
    // TMDB Watch Providers (priority 2, metadata-only)
    const { TMDBWatchProviderAdapter } = await import('./TMDBWatchProviderAdapter.js');
    adapterRegistry.register(new TMDBWatchProviderAdapter());
    
    // Aggregator sources (priority 3)
    const { AggregatorAdapter } = await import('./AggregatorAdapter.js');
    adapterRegistry.register(new AggregatorAdapter());
    
    // Start health monitoring
    adapterRegistry.startHealthChecks(300000); // 5 minutes
    
    console.log('[Adapters] All adapters initialized and registered');
    console.log('[Adapters] Health monitoring started (5min interval)');
    
    return adapterRegistry;
}

/**
 * Get adapters by priority for availability resolution
 * @param {AdapterRegistry} registry
 * @returns {Array<ScraperAdapter>}
 */
export function getAdaptersByPriority(registry) {
    return registry.getByPriority();
}

/**
 * Get all legal sources
 * @param {AdapterRegistry} registry
 * @returns {Array<ScraperAdapter>}
 */
export function getLegalSources(registry) {
    return registry.getLegalSources();
}

/**
 * Get all aggregator sources
 * @param {AdapterRegistry} registry
 * @returns {Array<ScraperAdapter>}
 */
export function getAggregatorSources(registry) {
    return registry.getAggregatorSources();
}