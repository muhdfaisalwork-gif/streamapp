import { chromium } from 'playwright';

export class BaseScraper {
    constructor(sourceName, baseUrl) {
        this.sourceName = sourceName;
        this.baseUrl = baseUrl;
    }

    /**
     * Initialize the headless browser
     */
    async initBrowser() {
        const browser = await chromium.launch({
            headless: true, // Run in background
            args: ['--no-sandbox', '--disable-setuid-sandbox']
        });
        const context = await browser.newContext({
            userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        });
        const page = await context.newPage();
        return { browser, page };
    }

    /**
     * Method to search for a movie/show
     */
    async search(query) { throw new Error('Not implemented'); }

    /**
     * Method to extract the final .m3u8 or .mp4 stream URL
     */
    async extractStream(movieUrl) { throw new Error('Not implemented'); }

    /**
     * Link Validation Engine: Checks if the extracted stream URL is alive
     */
    async validateStream(streamUrl) {
        try {
            const response = await fetch(streamUrl, { method: 'HEAD' });
            // If the server returns a 2xx or 3xx status, the link is likely alive
            return response.status >= 200 && response.status < 400;
        } catch (error) {
            console.error(`[${this.sourceName}] Stream validation failed for ${streamUrl}`);
            return false;
        }
    }

    /**
     * Playwright-based scraper helper: navigate to a page, wait for items,
     * extract them via the provided closure. Used by AggregatorScraper.
     * Returns [] on any failure (timeout, navigation error, etc.)
     */
    async playwrightScrape({ url, waitFor = 'body', extractItems, timeoutMs = 15000 }) {
        if (!this._playwrightAvailable()) {
            console.warn(`[${this.sourceName}] Playwright not available; skipping scrape`);
            return [];
        }
        let browser;
        try {
            const { chromium } = await import('playwright');
            browser = await chromium.launch({ headless: true, args: ['--no-sandbox', '--disable-setuid-sandbox'] });
            const context = await browser.newContext({
                userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            });
            const page = await context.newPage();
            await page.goto(url, { waitUntil: 'domcontentloaded', timeout: timeoutMs });
            try {
                await page.waitForSelector(waitFor, { timeout: Math.min(timeoutMs, 8000) });
            } catch (e) {
                // selector not found — try to extract anyway
            }
            const items = await extractItems(page, this);
            await browser.close();
            return Array.isArray(items) ? items : [];
        } catch (err) {
            console.warn(`[${this.sourceName}] scrape failed for ${url}: ${err.message}`);
            if (browser) try { await browser.close(); } catch (_) {}
            return [];
        }
    }

    /**
     * Playwright-based extract helper: navigate to a page, wait for an
     * element, extract a single URL via the provided closure.
     */
    async playwrightExtract({ url, waitFor = 'body', extract, timeoutMs = 15000 }) {
        if (!this._playwrightAvailable()) return null;
        let browser;
        try {
            const { chromium } = await import('playwright');
            browser = await chromium.launch({ headless: true, args: ['--no-sandbox', '--disable-setuid-sandbox'] });
            const context = await browser.newContext({
                userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            });
            const page = await context.newPage();
            await page.goto(url, { waitUntil: 'domcontentloaded', timeout: timeoutMs });
            try {
                await page.waitForSelector(waitFor, { timeout: Math.min(timeoutMs, 8000) });
            } catch (e) {}
            const result = await extract(page);
            await browser.close();
            return result;
        } catch (err) {
            console.warn(`[${this.sourceName}] extract failed for ${url}: ${err.message}`);
            if (browser) try { await browser.close(); } catch (_) {}
            return null;
        }
    }

    _playwrightAvailable() {
        try {
            // ESM-safe probe: just attempt a dynamic import
            // and catch synchronously via createRequire would not work in ESM
            // Instead, check process.versions and the node_modules folder
            return true; // Let the dynamic import inside playwrightScrape decide; if it fails, we catch and return []
        } catch (_) {
            return false;
        }
    }
}
