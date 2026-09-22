/**
 * catalog.routes.js — Proxy endpoints to the Python catalog service (port 7801).
 * The frontend keeps hitting :3000/api/v1/* without knowing about the split.
 */
import express from 'express';
import http from 'http';
import https from 'https';
import { URL } from 'url';

const router = express.Router();
const CATALOG_UPSTREAM = process.env.CATALOG_UPSTREAM || 'http://127.0.0.1:7801';

function proxy(path) {
    return (req, res) => {
        const url = new URL(CATALOG_UPSTREAM + path + (req.url.includes('?') ? req.url.slice(req.url.indexOf('?')) : ''));
        const transport = url.protocol === 'https:' ? https : http;
        const opts = {
            method: req.method,
            headers: { ...req.headers, host: url.host },
        };
        const upstream = transport.request(url, opts, (upRes) => {
            res.status(upRes.statusCode || 502);
            for (const [k, v] of Object.entries(upRes.headers)) {
                if (typeof v === 'string') res.setHeader(k, v);
            }
            upRes.pipe(res);
        });
        upstream.on('error', (e) => {
            res.status(502).json({ error: 'catalog_upstream_error', detail: e.message, upstream: CATALOG_UPSTREAM });
        });
        req.pipe(upstream);
    };
}

// Catalog endpoints — only the NEW multi-facet discovery endpoints go through
// the proxy. Existing /api/v1/genres, /api/v1/countries, /api/v1/languages
// continue to serve legacy shapes from the Node backend (so the existing
// frontend screens don't break).
const PATHS = [
    '/api/v1/stats',
    '/api/v1/collections',
    '/api/v1/years',
    '/api/v1/sources',
    '/api/v1/titles',
    '/api/v1/titles/movies',
    '/api/v1/titles/tv',
    '/api/v1/titles/anime',
    '/api/v1/titles/short-dramas',
    '/api/v1/titles/trending',
    '/api/v1/titles/top-rated',
    '/api/v1/titles/latest',
    '/api/v1/titles/coming-soon',
    '/api/v1/search',
    '/api/v1/genres-catalog',
    '/api/v1/countries-catalog',
    '/api/v1/languages-catalog',
    '/health',
];
for (const p of PATHS) {
    router.get(p, proxy(p));
}
// Detail routes with sub-paths need wildcard matching
router.get(/^\/api\/v1\/title\/[^/]+(\/(availability|seasons))?$/, (req, res) => {
    const upstreamUrl = CATALOG_UPSTREAM + req.originalUrl;
    console.log(`[catalog-proxy] ${req.method} ${req.originalUrl} -> ${upstreamUrl}`);
    const url = new URL(upstreamUrl);
    const transport = url.protocol === 'https:' ? https : http;
    const upstream = transport.request(url, { method: req.method }, (upRes) => {
        res.status(upRes.statusCode || 502);
        for (const [k, v] of Object.entries(upRes.headers)) {
            if (typeof v === 'string') res.setHeader(k, v);
        }
        upRes.pipe(res);
    });
    upstream.on('error', (e) => {
        console.error(`[catalog-proxy] error: ${e.message}`);
        res.status(502).json({ error: 'catalog_upstream_error', detail: e.message });
    });
    upstream.on('timeout', () => {
        upstream.destroy(new Error('upstream timeout'));
    });
    upstream.end();
});

export default router;