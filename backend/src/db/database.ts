import { DatabaseSync } from 'node:sqlite';
import path from 'node:path';
import fs from 'node:fs';
import { SEED_CATALOG } from './seeds.ts';
import type { MediaItem, User, PlaybackBookmark, WatchlistEntry, DmcaTakedownNotice, QoEEvent, SponsorCampaign } from '../types/index.ts';

export class Database {
  private db: DatabaseSync;

  constructor(dbPath?: string) {
    const finalPath = dbPath || path.resolve(process.cwd(), 'streaming_app.db');
    const dir = path.dirname(finalPath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
    this.db = new DatabaseSync(finalPath);
    this.init();
  }

  private init() {
    this.db.exec(`
      PRAGMA journal_mode = WAL;
      PRAGMA foreign_keys = ON;

      CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        display_name TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'user',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
      );

      CREATE TABLE IF NOT EXISTS media_items (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        slug TEXT UNIQUE NOT NULL,
        description TEXT NOT NULL,
        release_year INTEGER NOT NULL,
        duration_seconds INTEGER NOT NULL,
        genres TEXT NOT NULL, -- JSON array
        poster_url TEXT NOT NULL,
        backdrop_url TEXT NOT NULL,
        rating TEXT NOT NULL,
        attribution TEXT NOT NULL, -- JSON object
        sources TEXT NOT NULL, -- JSON array
        subtitles TEXT NOT NULL, -- JSON array
        is_featured INTEGER NOT NULL DEFAULT 0,
        category TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'active',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
      );

      CREATE TABLE IF NOT EXISTS bookmarks (
        user_id TEXT NOT NULL,
        media_id TEXT NOT NULL,
        position_seconds REAL NOT NULL,
        duration_seconds REAL NOT NULL,
        completed_percentage REAL NOT NULL,
        updated_at TEXT NOT NULL,
        PRIMARY KEY (user_id, media_id)
      );

      CREATE TABLE IF NOT EXISTS watchlist (
        user_id TEXT NOT NULL,
        media_id TEXT NOT NULL,
        added_at TEXT NOT NULL,
        PRIMARY KEY (user_id, media_id)
      );

      CREATE TABLE IF NOT EXISTS dmca_notices (
        id TEXT PRIMARY KEY,
        media_id TEXT NOT NULL,
        claimant_name TEXT NOT NULL,
        claimant_email TEXT NOT NULL,
        copyright_work_description TEXT NOT NULL,
        statement_of_good_faith INTEGER NOT NULL,
        digital_signature TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'quarantined',
        submitted_at TEXT NOT NULL
      );

      CREATE TABLE IF NOT EXISTS qoe_events (
        id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL,
        media_id TEXT NOT NULL,
        platform TEXT NOT NULL,
        event_type TEXT NOT NULL,
        startup_time_ms REAL,
        buffer_duration_ms REAL,
        target_bitrate_bps INTEGER,
        error_code TEXT,
        timestamp TEXT NOT NULL
      );

      CREATE TABLE IF NOT EXISTS sponsor_campaigns (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        sponsor_name TEXT NOT NULL,
        message TEXT NOT NULL,
        cta_url TEXT NOT NULL,
        cta_label TEXT NOT NULL,
        badge_text TEXT NOT NULL,
        media_id TEXT,
        impressions INTEGER DEFAULT 0,
        clicks INTEGER DEFAULT 0,
        status TEXT NOT NULL DEFAULT 'active',
        created_at TEXT NOT NULL
      );
    `);

    this.seedCatalogIfEmpty();
  }

  private seedCatalogIfEmpty() {
    const insert = this.db.prepare(`
      INSERT OR REPLACE INTO media_items (
        id, title, slug, description, release_year, duration_seconds, genres,
        poster_url, backdrop_url, rating, attribution, sources, subtitles,
        is_featured, category, status, created_at, updated_at
      ) VALUES (
        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
      )
    `);

    for (const item of SEED_CATALOG) {
        insert.run(
          item.id,
          item.title,
          item.slug,
          item.description,
          item.releaseYear,
          item.durationSeconds,
          JSON.stringify(item.genres),
          item.posterUrl,
          item.backdropUrl,
          item.rating,
          JSON.stringify(item.attribution),
          JSON.stringify(item.sources),
          JSON.stringify(item.subtitles),
          item.isFeatured ? 1 : 0,
          item.category,
          item.status,
          item.createdAt,
          item.updatedAt
        );
      }

    const sponsorCount = this.db.prepare('SELECT COUNT(*) as count FROM sponsor_campaigns').get() as { count: number };
    if (sponsorCount.count === 0) {
      const insertSponsor = this.db.prepare(`
        INSERT INTO sponsor_campaigns (
          id, title, sponsor_name, message, cta_url, cta_label, badge_text, media_id, impressions, clicks, status, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 0, 'active', ?)
      `);
      insertSponsor.run(
        'sp-blender-01',
        'Blender Studio Open Movie Fund',
        'Blender Foundation',
        'Support open-source 3D animation and free creative tools at Blender Studio.',
        'https://fund.blender.org',
        'Support Blender Fund',
        'Creator Support',
        null,
        new Date().toISOString()
      );
      insertSponsor.run(
        'sp-archive-02',
        'Internet Archive Film Preservation',
        'Internet Archive',
        'Preserving classic cinema, cultural history, and public domain archives for the world.',
        'https://archive.org/donate',
        'Donate to Archive.org',
        'Public Domain Preservation',
        null,
        new Date().toISOString()
      );
    }
  }

  // --- Catalog Queries ---
  getAllMedia(includeQuarantined = false): MediaItem[] {
    const query = includeQuarantined 
      ? 'SELECT * FROM media_items ORDER BY release_year DESC'
      : "SELECT * FROM media_items WHERE status != 'suspended_pending_review' ORDER BY release_year DESC";
    const rows = this.db.prepare(query).all() as any[];
    return rows.map(this.mapMediaRow);
  }

  getMediaById(id: string): MediaItem | null {
    const row = this.db.prepare('SELECT * FROM media_items WHERE id = ?').get(id) as any;
    return row ? this.mapMediaRow(row) : null;
  }

  updateMediaStatus(id: string, status: 'active' | 'degraded' | 'suspended_pending_review'): boolean {
    const result = this.db.prepare('UPDATE media_items SET status = ?, updated_at = ? WHERE id = ?')
      .run(status, new Date().toISOString(), id);
    return result.changes > 0;
  }

  // --- User Queries ---
  createUser(user: User): boolean {
    const stmt = this.db.prepare(`
      INSERT INTO users (id, email, password_hash, display_name, role, created_at, updated_at)
      VALUES (?, ?, ?, ?, ?, ?, ?)
    `);
    stmt.run(user.id, user.email, user.passwordHash, user.displayName, user.role, user.createdAt, user.updatedAt);
    return true;
  }

  getUserByEmail(email: string): User | null {
    const row = this.db.prepare('SELECT * FROM users WHERE email = ?').get(email) as any;
    if (!row) return null;
    return {
      id: row.id,
      email: row.email,
      passwordHash: row.password_hash,
      displayName: row.display_name,
      role: row.role,
      createdAt: row.created_at,
      updatedAt: row.updated_at
    };
  }

  getUserById(id: string): User | null {
    const row = this.db.prepare('SELECT * FROM users WHERE id = ?').get(id) as any;
    if (!row) return null;
    return {
      id: row.id,
      email: row.email,
      passwordHash: row.password_hash,
      displayName: row.display_name,
      role: row.role,
      createdAt: row.created_at,
      updatedAt: row.updated_at
    };
  }

  // --- Bookmark / Continue Watching Queries ---
  saveBookmark(bookmark: PlaybackBookmark): void {
    const stmt = this.db.prepare(`
      INSERT INTO bookmarks (user_id, media_id, position_seconds, duration_seconds, completed_percentage, updated_at)
      VALUES (?, ?, ?, ?, ?, ?)
      ON CONFLICT(user_id, media_id) DO UPDATE SET
        position_seconds = excluded.position_seconds,
        duration_seconds = excluded.duration_seconds,
        completed_percentage = excluded.completed_percentage,
        updated_at = excluded.updated_at
    `);
    stmt.run(
      bookmark.userId,
      bookmark.mediaId,
      bookmark.positionSeconds,
      bookmark.durationSeconds,
      bookmark.completedPercentage,
      bookmark.updatedAt
    );
  }

  getBookmarksByUser(userId: string): PlaybackBookmark[] {
    const rows = this.db.prepare(`
      SELECT * FROM bookmarks WHERE user_id = ? ORDER BY updated_at DESC
    `).all(userId) as any[];
    return rows.map(r => ({
      userId: r.user_id,
      mediaId: r.media_id,
      positionSeconds: r.position_seconds,
      durationSeconds: r.duration_seconds,
      completedPercentage: r.completed_percentage,
      updatedAt: r.updated_at
    }));
  }

  getBookmark(userId: string, mediaId: string): PlaybackBookmark | null {
    const row = this.db.prepare(`
      SELECT * FROM bookmarks WHERE user_id = ? AND media_id = ?
    `).get(userId, mediaId) as any;
    if (!row) return null;
    return {
      userId: row.user_id,
      mediaId: row.media_id,
      positionSeconds: row.position_seconds,
      durationSeconds: row.duration_seconds,
      completedPercentage: row.completed_percentage,
      updatedAt: row.updated_at
    };
  }

  // --- Watchlist Queries ---
  addToWatchlist(userId: string, mediaId: string): void {
    const stmt = this.db.prepare(`
      INSERT OR IGNORE INTO watchlist (user_id, media_id, added_at)
      VALUES (?, ?, ?)
    `);
    stmt.run(userId, mediaId, new Date().toISOString());
  }

  removeFromWatchlist(userId: string, mediaId: string): void {
    this.db.prepare('DELETE FROM watchlist WHERE user_id = ? AND media_id = ?').run(userId, mediaId);
  }

  getWatchlist(userId: string): string[] {
    const rows = this.db.prepare('SELECT media_id FROM watchlist WHERE user_id = ? ORDER BY added_at DESC').all(userId) as any[];
    return rows.map(r => r.media_id);
  }

  // --- DMCA Takedown Notices ---
  createDmcaNotice(notice: DmcaTakedownNotice): void {
    const stmt = this.db.prepare(`
      INSERT INTO dmca_notices (
        id, media_id, claimant_name, claimant_email, copyright_work_description,
        statement_of_good_faith, digital_signature, status, submitted_at
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    `);
    stmt.run(
      notice.id,
      notice.mediaId,
      notice.claimantName,
      notice.claimantEmail,
      notice.copyrightWorkDescription,
      notice.statementOfGoodFaith ? 1 : 0,
      notice.digitalSignature,
      notice.status,
      notice.submittedAt
    );
  }

  getDmcaNotices(): DmcaTakedownNotice[] {
    const rows = this.db.prepare('SELECT * FROM dmca_notices ORDER BY submitted_at DESC').all() as any[];
    return rows.map(r => ({
      id: r.id,
      mediaId: r.media_id,
      claimantName: r.claimant_name,
      claimantEmail: r.claimant_email,
      copyrightWorkDescription: r.copyright_work_description,
      statementOfGoodFaith: Boolean(r.statement_of_good_faith),
      digitalSignature: r.digital_signature,
      status: r.status,
      submittedAt: r.submitted_at
    }));
  }

  // --- QoE Analytics ---
  recordQoEEvent(event: QoEEvent): void {
    const stmt = this.db.prepare(`
      INSERT INTO qoe_events (
        id, session_id, media_id, platform, event_type, startup_time_ms,
        buffer_duration_ms, target_bitrate_bps, error_code, timestamp
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `);
    stmt.run(
      event.id,
      event.sessionId,
      event.mediaId,
      event.platform,
      event.eventType,
      event.startupTimeMs ?? null,
      event.bufferDurationMs ?? null,
      event.targetBitrateBps ?? null,
      event.errorCode ?? null,
      event.timestamp
    );
  }

  recordQoEEvents(events: QoEEvent[]): void {
    const stmt = this.db.prepare(`
      INSERT INTO qoe_events (
        id, session_id, media_id, platform, event_type, startup_time_ms,
        buffer_duration_ms, target_bitrate_bps, error_code, timestamp
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `);
    this.db.exec('BEGIN TRANSACTION;');
    try {
      for (const event of events) {
        stmt.run(
          event.id,
          event.sessionId,
          event.mediaId,
          event.platform,
          event.eventType,
          event.startupTimeMs ?? null,
          event.bufferDurationMs ?? null,
          event.targetBitrateBps ?? null,
          event.errorCode ?? null,
          event.timestamp
        );
      }
      this.db.exec('COMMIT;');
    } catch (err) {
      this.db.exec('ROLLBACK;');
      throw err;
    }
  }

  getQoEStats(): { totalEvents: number; averageStartupMs: number; totalBufferStalls: number } {
    const total = this.db.prepare('SELECT COUNT(*) as count FROM qoe_events').get() as { count: number };
    const avgStartup = this.db.prepare(`
      SELECT AVG(startup_time_ms) as avg_ms FROM qoe_events WHERE startup_time_ms IS NOT NULL
    `).get() as { avg_ms: number | null };
    const stalls = this.db.prepare(`
      SELECT COUNT(*) as stalls FROM qoe_events WHERE event_type = 'buffer_stall'
    `).get() as { stalls: number };

    return {
      totalEvents: total.count,
      averageStartupMs: Math.round(avgStartup.avg_ms || 0),
      totalBufferStalls: stalls.stalls
    };
  }

  // --- Sponsor Campaigns ---
  getActiveSponsors(mediaId?: string): SponsorCampaign[] {
    let query = "SELECT * FROM sponsor_campaigns WHERE status = 'active'";
    let rows: any[];
    if (mediaId) {
      query += " AND (media_id IS NULL OR media_id = ?)";
      rows = this.db.prepare(query).all(mediaId) as any[];
    } else {
      rows = this.db.prepare(query).all() as any[];
    }
    return rows.map(this.mapSponsorRow);
  }

  recordSponsorImpression(id: string): boolean {
    const res = this.db.prepare('UPDATE sponsor_campaigns SET impressions = impressions + 1 WHERE id = ?').run(id);
    return res.changes > 0;
  }

  recordSponsorClick(id: string): boolean {
    const res = this.db.prepare('UPDATE sponsor_campaigns SET clicks = clicks + 1 WHERE id = ?').run(id);
    return res.changes > 0;
  }

  private mapSponsorRow(row: any): SponsorCampaign {
    return {
      id: row.id,
      title: row.title,
      sponsorName: row.sponsor_name,
      message: row.message,
      ctaUrl: row.cta_url,
      ctaLabel: row.cta_label,
      badgeText: row.badge_text,
      mediaId: row.media_id,
      impressions: row.impressions,
      clicks: row.clicks,
      status: row.status,
      createdAt: row.created_at
    };
  }

  close(): void {
    this.db.close();
  }

  private mapMediaRow(row: any): MediaItem {
    return {
      id: row.id,
      title: row.title,
      slug: row.slug,
      description: row.description,
      releaseYear: row.release_year,
      durationSeconds: row.duration_seconds,
      genres: JSON.parse(row.genres),
      posterUrl: row.poster_url,
      backdropUrl: row.backdrop_url,
      rating: row.rating,
      attribution: JSON.parse(row.attribution),
      sources: JSON.parse(row.sources),
      subtitles: JSON.parse(row.subtitles),
      isFeatured: Boolean(row.is_featured),
      category: row.category,
      status: row.status,
      createdAt: row.created_at,
      updatedAt: row.updated_at
    };
  }
}
