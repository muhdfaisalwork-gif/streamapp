/**
 * watchlist.routes.js — Server-side persistence for user watchlist and history.
 *
 * Storage: catalog.db `user_watchlist` and `user_history` tables.
 * Anonymous auth via X-User-Id header or `user_id` query/body param (generated
 * client-side and stored in localStorage). No PII stored.
 *
 * Endpoints:
 *   GET    /api/v1/watchlist?user_id=...
 *   POST   /api/v1/watchlist       { user_id, title: { id, slug, title, type, year, poster, ... } }
 *   DELETE /api/v1/watchlist?user_id=...&title_id=...
 *   GET    /api/v1/history?user_id=...&limit=50
 *   POST   /api/v1/history         { user_id, title_id, position_sec, duration_sec, pct, episode_id, completed }
 *
 * All endpoints are write-or-read with simple INSERT OR REPLACE / DELETE semantics.
 * Failure returns 4xx with a JSON error — never silently drops writes.
 */
import express from 'express';
import sqlite3 from 'node:sqlite';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const router = express.Router();
const CATALOG_DB = process.env.CATALOG_DB
    || path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..', '..', 'scraper', 'catalog.db');
let db;
try {
    db = new sqlite3.DatabaseSync(CATALOG_DB);
    db.exec('PRAGMA journal_mode = WAL');
    console.log('[watchlist] catalog.db at', CATALOG_DB);
} catch (e) {
    console.error('[watchlist] cannot open catalog.db at', CATALOG_DB, e.message);
}

function getDb() {
    if (!db) throw new Error('catalog.db unavailable');
    return db;
}

function getUserId(req) {
    return req.query.user_id || req.body?.user_id || req.headers['x-user-id'] || 'anonymous';
}

router.get('/watchlist', (req, res) => {
    try {
        const uid = getUserId(req);
        const rows = getDb().prepare(`
            SELECT t.id, t.slug, t.title, t.type, t.year, t.poster, t.rating, w.added_at
            FROM user_watchlist w
            JOIN titles t ON t.id = w.title_id
            WHERE w.user_id = ?
            ORDER BY w.added_at DESC
        `).all(uid);
        res.json({ user_id: uid, items: rows });
    } catch (e) {
        res.status(500).json({ error: 'watchlist_read_failed', detail: e.message });
    }
});

router.post('/watchlist', (req, res) => {
    try {
        const uid = getUserId(req);
        const title = req.body?.title;
        if (!title || !title.id) {
            return res.status(400).json({ error: 'missing_title_id' });
        }
        // Upsert the title record first (best-effort — may not have all fields).
        const t = title;
        getDb().prepare(`
            INSERT INTO titles (id, slug, title, type, year, poster, rating, popularity, is_anime, is_short_drama, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, strftime('%s','now'))
            ON CONFLICT(id) DO UPDATE SET updated_at = strftime('%s','now')
        `).run(
            Number(t.id), t.slug || `t-${t.id}`, t.title || 'Untitled',
            t.type || 'movie', t.year || null, t.poster || null, t.rating || null,
            0, t.type === 'anime' ? 1 : 0, t.type === 'short_drama' ? 1 : 0
        );
        getDb().prepare(`
            INSERT OR REPLACE INTO user_watchlist (user_id, title_id, added_at)
            VALUES (?, ?, strftime('%s','now'))
        `).run(uid, Number(t.id));
        res.json({ ok: true, user_id: uid, title_id: t.id });
    } catch (e) {
        res.status(500).json({ error: 'watchlist_add_failed', detail: e.message });
    }
});

router.delete('/watchlist', (req, res) => {
    try {
        const uid = getUserId(req);
        const tid = req.query.title_id;
        if (!tid) return res.status(400).json({ error: 'missing_title_id' });
        getDb().prepare('DELETE FROM user_watchlist WHERE user_id = ? AND title_id = ?')
            .run(uid, Number(tid));
        res.json({ ok: true, user_id: uid, title_id: tid });
    } catch (e) {
        res.status(500).json({ error: 'watchlist_remove_failed', detail: e.message });
    }
});

router.get('/history', (req, res) => {
    try {
        const uid = getUserId(req);
        const limit = Math.max(1, Math.min(200, Number(req.query.limit) || 50));
        const rows = getDb().prepare(`
            SELECT h.id, h.title_id, h.episode_id, h.position_sec, h.duration_sec, h.pct, h.completed, h.ts,
                   t.slug, t.title, t.type, t.year, t.poster, t.backdrop
            FROM user_history h
            JOIN titles t ON t.id = h.title_id
            WHERE h.user_id = ?
            ORDER BY h.ts DESC
            LIMIT ?
        `).all(uid, limit);
        res.json({ user_id: uid, items: rows });
    } catch (e) {
        res.status(500).json({ error: 'history_read_failed', detail: e.message });
    }
});

router.post('/history', (req, res) => {
    try {
        const uid = getUserId(req);
        const { title_id, episode_id, position_sec, duration_sec, pct, completed } = req.body || {};
        if (!title_id) return res.status(400).json({ error: 'missing_title_id' });
        getDb().prepare(`
            INSERT INTO user_history
              (user_id, title_id, episode_id, position_sec, duration_sec, pct, completed, ts)
            VALUES (?, ?, ?, ?, ?, ?, ?, strftime('%s','now'))
        `).run(uid, Number(title_id), episode_id ? Number(episode_id) : null,
               Number(position_sec) || 0, Number(duration_sec) || 0,
               Number(pct) || 0, completed ? 1 : 0);
        res.json({ ok: true });
    } catch (e) {
        res.status(500).json({ error: 'history_write_failed', detail: e.message });
    }
});

router.delete('/history', (req, res) => {
    try {
        const uid = getUserId(req);
        if (req.query.all === 'true') {
            getDb().prepare('DELETE FROM user_history WHERE user_id = ?').run(uid);
            return res.json({ ok: true, cleared: 'all' });
        }
        if (req.query.id) {
            getDb().prepare('DELETE FROM user_history WHERE user_id = ? AND id = ?')
                .run(uid, Number(req.query.id));
            return res.json({ ok: true, removed: req.query.id });
        }
        res.status(400).json({ error: 'specify ?all=true or ?id=N' });
    } catch (e) {
        res.status(500).json({ error: 'history_delete_failed', detail: e.message });
    }
});

export default router;