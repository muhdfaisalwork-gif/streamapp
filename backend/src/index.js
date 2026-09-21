import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import router from './api/routes.js';
import { liveClient } from './services/LiveClient.js';

dotenv.config();

const app = express();
const PORT = process.env.PORT || 3000;
const CORS_ORIGIN = process.env.CORS_ORIGIN || '*';

app.use(cors({ origin: CORS_ORIGIN }));
app.use(express.json({ limit: '1mb' }));

// API Routes (search, stream extraction, etc.)
app.use('/api/v1', router);

// Health check
app.get('/health', async (req, res) => {
    await liveClient.probe();
    res.status(200).json({
        status: 'healthy',
        message: 'Streaming Aggregator Backend is running',
        port: PORT,
        liveAvailable: liveClient.liveAvailable,
        liveTitlesCached: liveClient.liveTitlesCached,
        totalUniqueTitles: liveClient.liveTitlesCached + 683,
        tmdbEnrichment: liveClient.tmdbEnabled,
        uptime: process.uptime(),
    });
});

// Root index - small landing page so opening http://localhost:3000 in a browser
// doesn't show "Cannot GET /". The Flutter client and Expo frontend hit /api/v1/*.
app.get('/', (req, res) => {
    res.status(200).json({
        name: 'StreamApp Aggregator Backend',
        endpoints: {
            health: '/health',
            search: '/api/v1/search?q=<query>',
            stream: '/api/v1/stream  (POST {url, sourceName})',
        },
    });
});

// 404 handler
app.use((req, res) => {
    res.status(404).json({ error: 'Not Found', path: req.originalUrl });
});

// Error handler
app.use((err, req, res, _next) => {
    console.error('[backend] Unhandled error:', err);
    res.status(500).json({ error: 'Internal server error', detail: err.message });
});

app.listen(PORT, () => {
    console.log(`🚀 Streaming Aggregator Backend running on http://localhost:${PORT}`);
    console.log(`   Health:  http://localhost:${PORT}/health`);
    console.log(`   API:     http://localhost:${PORT}/api/v1`);
});