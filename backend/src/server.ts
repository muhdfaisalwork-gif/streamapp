import http from 'node:http';
import { URL } from 'node:url';
import { Database } from './db/database.ts';
import { CatalogService } from './services/catalog.service.ts';
import { AuthService } from './services/auth.service.ts';
import { PlaybackService } from './services/playback.service.ts';
import { WatchlistService } from './services/watchlist.service.ts';
import { SearchService } from './services/search.service.ts';
import { HealthService } from './services/health.service.ts';
import { LegalService } from './services/legal.service.ts';
import { AnalyticsService } from './services/analytics.service.ts';

export class StreamingServer {
  private server: http.Server;
  private db: Database;
  public catalogService: CatalogService;
  public authService: AuthService;
  public playbackService: PlaybackService;
  public watchlistService: WatchlistService;
  public searchService: SearchService;
  public healthService: HealthService;
  public legalService: LegalService;
  public analyticsService: AnalyticsService;

  constructor(dbPath?: string) {
    this.db = new Database(dbPath);
    this.catalogService = new CatalogService(this.db);
    this.authService = new AuthService(this.db);
    this.playbackService = new PlaybackService(this.db);
    this.watchlistService = new WatchlistService(this.db);
    this.searchService = new SearchService(this.db);
    this.healthService = new HealthService(this.db);
    this.legalService = new LegalService(this.db);
    this.analyticsService = new AnalyticsService(this.db);

    this.server = http.createServer(this.handleRequest.bind(this));
  }

  private async parseBody(req: http.IncomingMessage): Promise<any> {
    return new Promise((resolve, reject) => {
      let body = '';
      req.on('data', chunk => {
        body += chunk;
        if (body.length > 1e6) {
          req.destroy();
          reject(new Error('Payload too large'));
        }
      });
      req.on('end', () => {
        if (!body) return resolve({});
        try {
          resolve(JSON.parse(body));
        } catch (e) {
          reject(new Error('Invalid JSON payload'));
        }
      });
      req.on('error', reject);
    });
  }

  private sendJson(res: http.ServerResponse, status: number, data: any) {
    res.writeHead(status, {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization'
    });
    res.end(JSON.stringify(data));
  }

  private sendHtml(res: http.ServerResponse, html: string) {
    res.writeHead(200, {
      'Content-Type': 'text/html; charset=utf-8',
      'Access-Control-Allow-Origin': '*'
    });
    res.end(html);
  }

  private getAuthUser(req: http.IncomingMessage) {
    const authHeader = req.headers['authorization'];
    if (!authHeader || !authHeader.startsWith('Bearer ')) return null;
    const token = authHeader.substring(7);
    return this.authService.getUserFromToken(token);
  }

  private async handleRequest(req: http.IncomingMessage, res: http.ServerResponse) {
    const parsedUrl = new URL(req.url || '/', `http://${req.headers.host || 'localhost'}`);
    const pathname = parsedUrl.pathname;
    const method = req.method?.toUpperCase();

    // Handle CORS preflight
    if (method === 'OPTIONS') {
      res.writeHead(204, {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization'
      });
      res.end();
      return;
    }

    try {
      // Root: Built-in Web Streaming & Direct Download Portal
      if ((pathname === '/' || pathname === '/index.html') && method === 'GET') {
        return this.sendHtml(res, this.renderWebPortal());
      }

      // PWA Manifest for Android TV, Mobile, Tablet, and Desktop Installation
      if (pathname === '/manifest.json' && method === 'GET') {
        return this.sendJson(res, 200, {
          name: 'MovieBox HD',
          short_name: 'MovieBox',
          start_url: '/',
          display: 'standalone',
          background_color: '#090D16',
          theme_color: '#090D16',
          description: 'MovieBox HD Cross-Platform Streaming & Direct Download Aggregator',
          icons: [
            {
              src: 'https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=192&q=80',
              sizes: '192x192',
              type: 'image/jpeg'
            },
            {
              src: 'https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=512&q=80',
              sizes: '512x512',
              type: 'image/jpeg'
            }
          ]
        });
      }

      // 1. Health Endpoints
      if ((pathname === '/health' || pathname === '/api/v1/health') && method === 'GET') {
        const report = this.healthService.getSystemStatus();
        return this.sendJson(res, 200, report);
      }

      // 2. Catalog Endpoints
      if (pathname === '/api/v1/catalog/home' && method === 'GET') {
        const feed = this.catalogService.getHomeFeed();
        return this.sendJson(res, 200, { success: true, data: feed });
      }

      if (pathname.startsWith('/api/v1/catalog/media/') && method === 'GET') {
        const id = pathname.replace('/api/v1/catalog/media/', '');
        const item = this.catalogService.getItemById(id);
        if (!item) {
          return this.sendJson(res, 404, { success: false, error: 'Media item not found' });
        }
        return this.sendJson(res, 200, { success: true, data: item });
      }

      if (pathname === '/api/v1/catalog/genres' && method === 'GET') {
        const genres = this.catalogService.getGenres();
        return this.sendJson(res, 200, { success: true, data: genres });
      }

      // 3. Search Endpoints
      if (pathname === '/api/v1/search' && method === 'GET') {
        const query = parsedUrl.searchParams.get('q') || undefined;
        const genre = parsedUrl.searchParams.get('genre') || undefined;
        const category = parsedUrl.searchParams.get('category') || undefined;
        const yearParam = parsedUrl.searchParams.get('year');
        const year = yearParam ? parseInt(yearParam, 10) : undefined;

        const results = this.searchService.search({ query, genre, category, year });
        return this.sendJson(res, 200, { success: true, data: results });
      }

      // 4. Auth Endpoints
      if (pathname === '/api/v1/auth/register' && method === 'POST') {
        const body = await this.parseBody(req);
        const result = this.authService.register(body.email, body.password, body.displayName);
        return this.sendJson(res, 201, { success: true, data: result });
      }

      if (pathname === '/api/v1/auth/login' && method === 'POST') {
        const body = await this.parseBody(req);
        const result = this.authService.login(body.email, body.password);
        return this.sendJson(res, 200, { success: true, data: result });
      }

      if (pathname === '/api/v1/auth/me' && method === 'GET') {
        const user = this.getAuthUser(req);
        if (!user) {
          return this.sendJson(res, 401, { success: false, error: 'Unauthorized' });
        }
        return this.sendJson(res, 200, { success: true, data: user });
      }

      if (pathname === '/api/v1/auth/sync' && method === 'POST') {
        const user = this.getAuthUser(req);
        if (!user) {
          return this.sendJson(res, 401, { success: false, error: 'Unauthorized' });
        }
        const body = await this.parseBody(req);
        const bookmarks = Array.isArray(body.bookmarks) ? body.bookmarks : [];
        const watchlist = Array.isArray(body.watchlist) ? body.watchlist : [];
        const syncResult = this.authService.syncGuestData(user.id, bookmarks, watchlist);
        return this.sendJson(res, 200, { success: true, data: syncResult });
      }

      // 5. Playback Endpoints
      if (pathname.startsWith('/api/v1/playback/resolve/') && method === 'GET') {
        const id = pathname.replace('/api/v1/playback/resolve/', '');
        const item = this.catalogService.getItemById(id);
        if (!item) {
          return this.sendJson(res, 404, { success: false, error: 'Media not found' });
        }
        const format = (parsedUrl.searchParams.get('format') || 'hls') as any;
        const result = this.playbackService.resolveStream(id, format);
        return this.sendJson(res, 200, { success: true, data: result });
      }

      if (pathname === '/api/v1/playback/bookmark' && method === 'POST') {
        const user = this.getAuthUser(req);
        const userId = user ? user.id : 'guest';
        const body = await this.parseBody(req);
        if (!body.mediaId || typeof body.mediaId !== 'string') {
          return this.sendJson(res, 400, { success: false, error: "Missing or invalid 'mediaId'" });
        }
        const bookmark = this.playbackService.saveBookmark(
          userId,
          body.mediaId,
          Number(body.positionSeconds || 0),
          Number(body.durationSeconds || 0)
        );
        return this.sendJson(res, 200, { success: true, data: bookmark });
      }

      if (pathname.startsWith('/api/v1/playback/bookmark/') && method === 'GET') {
        const id = pathname.replace('/api/v1/playback/bookmark/', '');
        const user = this.getAuthUser(req);
        const userId = user ? user.id : 'guest';
        const bookmark = this.playbackService.getBookmark(userId, id);
        return this.sendJson(res, 200, { success: true, data: bookmark });
      }

      if (pathname === '/api/v1/playback/continue-watching' && method === 'GET') {
        const user = this.getAuthUser(req);
        const userId = user ? user.id : 'guest';
        const items = this.playbackService.getContinueWatching(userId);
        return this.sendJson(res, 200, { success: true, data: items });
      }

      // 6. Watchlist Endpoints
      if (pathname === '/api/v1/watchlist/add' && method === 'POST') {
        const user = this.getAuthUser(req);
        const userId = user ? user.id : 'guest';
        const body = await this.parseBody(req);
        if (!body.mediaId || typeof body.mediaId !== 'string') {
          return this.sendJson(res, 400, { success: false, error: "Missing or invalid 'mediaId'" });
        }
        this.watchlistService.addToWatchlist(userId, body.mediaId);
        return this.sendJson(res, 200, { success: true, message: 'Added to watchlist' });
      }

      if (pathname === '/api/v1/watchlist/remove' && method === 'POST') {
        const user = this.getAuthUser(req);
        const userId = user ? user.id : 'guest';
        const body = await this.parseBody(req);
        this.watchlistService.removeFromWatchlist(userId, body.mediaId);
        return this.sendJson(res, 200, { success: true, message: 'Removed from watchlist' });
      }

      if (pathname === '/api/v1/watchlist' && method === 'GET') {
        const user = this.getAuthUser(req);
        const userId = user ? user.id : 'guest';
        const items = this.watchlistService.getWatchlist(userId);
        return this.sendJson(res, 200, { success: true, data: items });
      }

      // 7. Legal & DMCA Endpoints
      if (pathname === '/api/v1/legal/takedown' && method === 'POST') {
        const body = await this.parseBody(req);
        const result = this.legalService.submitTakedownNotice(body);
        return this.sendJson(res, 201, { success: true, data: result });
      }

      if (pathname === '/api/v1/legal/audit' && method === 'GET') {
        const notices = this.legalService.getAuditLog();
        return this.sendJson(res, 200, { success: true, data: notices });
      }

      // 8. Analytics Endpoints
      if (pathname === '/api/v1/analytics/qoe' && method === 'POST') {
        const isOptedOut = req.headers['dnt'] === '1' || req.headers['sec-gpc'] === '1' || req.headers['x-consent-telemetry'] === 'false';
        const body = await this.parseBody(req);
        const optOut = isOptedOut || Boolean(body.optOut);
        const result = this.analyticsService.recordEvent(body, optOut);
        return this.sendJson(res, 201, { success: true, data: result });
      }

      if (pathname === '/api/v1/analytics/events' && method === 'POST') {
        const isOptedOut = req.headers['dnt'] === '1' || req.headers['sec-gpc'] === '1' || req.headers['x-consent-telemetry'] === 'false';
        const body = await this.parseBody(req);
        const optOut = isOptedOut || Boolean(body.optOut);
        const events = Array.isArray(body.events) ? body.events : [];
        const result = this.analyticsService.recordBatchEvents(events, optOut);
        return this.sendJson(res, 200, { success: true, data: result });
      }

      if (pathname === '/api/v1/analytics/dashboard' && method === 'GET') {
        const metrics = this.analyticsService.getDashboardMetrics();
        return this.sendJson(res, 200, { success: true, data: metrics });
      }

      // 9. Ethical Sponsor & Creator Support Endpoints
      if (pathname === '/api/v1/sponsors/active' && method === 'GET') {
        const mediaId = parsedUrl.searchParams.get('mediaId') || undefined;
        const sponsors = this.analyticsService.getActiveSponsors(mediaId);
        return this.sendJson(res, 200, { success: true, data: sponsors });
      }

      if (pathname === '/api/v1/sponsors/impression' && method === 'POST') {
        const body = await this.parseBody(req);
        if (!body.campaignId || typeof body.campaignId !== 'string') {
          return this.sendJson(res, 400, { success: false, error: "Missing or invalid 'campaignId'" });
        }
        const updated = this.analyticsService.recordSponsorImpression(body.campaignId);
        if (!updated) {
          return this.sendJson(res, 404, { success: false, error: 'Campaign not found' });
        }
        return this.sendJson(res, 200, { success: true, message: 'Impression recorded' });
      }

      if (pathname === '/api/v1/sponsors/click' && method === 'POST') {
        const body = await this.parseBody(req);
        if (!body.campaignId || typeof body.campaignId !== 'string') {
          return this.sendJson(res, 400, { success: false, error: "Missing or invalid 'campaignId'" });
        }
        const updated = this.analyticsService.recordSponsorClick(body.campaignId);
        if (!updated) {
          return this.sendJson(res, 404, { success: false, error: 'Campaign not found' });
        }
        return this.sendJson(res, 200, { success: true, message: 'Click recorded' });
      }

      // Not Found
      return this.sendJson(res, 404, { success: false, error: `Route not found: ${method} ${pathname}` });
    } catch (err: any) {
      return this.sendJson(res, 400, { success: false, error: err.message || 'Server error' });
    }
  }

  private renderWebPortal(): string {
    const feed = this.catalogService.getHomeFeed();
    const allItems: any[] = [];
    for (const tray of feed.trays) {
      for (const item of tray.items) {
        if (!allItems.some(i => i.id === item.id)) {
          allItems.push(item);
        }
      }
    }
    const heroItem = allItems[0] || feed.featured[0];

    return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link rel="manifest" href="/manifest.json">
  <meta name="theme-color" content="#090D16">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <meta name="mobile-web-app-capable" content="yes">
  <title>MovieBox HD — Legal Streaming & Multi-Server Aggregator</title>
  <style>
    :root {
      --bg-canvas: #090D16;
      --bg-surface1: #101626;
      --bg-surface2: #182238;
      --bg-surface3: #23314E;
      --text-primary: #F0F4FC;
      --text-secondary: #94A3B8;
      --text-muted: #64748B;
      --brand-red: #E50914;
      --brand-cyan: #00E5FF;
      --brand-amber: #FFB300;
      --brand-green: #10B981;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif; }
    body { background: var(--bg-canvas); color: var(--text-primary); overflow-x: hidden; padding-bottom: 50px; }

    /* Focus styling for PC Keyboard & Android TV D-pad Navigation */
    :focus-visible, .tv-focus {
      outline: 3px solid var(--brand-cyan) !important;
      transform: scale(1.05) !important;
      box-shadow: 0 0 25px rgba(0, 229, 255, 0.7) !important;
      z-index: 50;
    }

    /* Top Navigation Bar */
    .navbar {
      position: sticky; top: 0; z-index: 100;
      display: flex; align-items: center; justify-content: space-between;
      padding: 12px 32px; background: rgba(9, 13, 22, 0.95);
      backdrop-filter: blur(12px); border-bottom: 1px solid rgba(255,255,255,0.08);
    }
    .nav-left { display: flex; align-items: center; gap: 28px; }
    .logo {
      display: flex; align-items: center; gap: 8px; font-size: 22px; font-weight: 900;
      letter-spacing: -0.5px; text-decoration: none; color: #fff; outline: none;
    }
    .logo-badge {
      background: linear-gradient(135deg, var(--brand-red), #FF4D4D);
      padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: 800; color: #fff;
    }
    .nav-links { display: flex; gap: 20px; list-style: none; }
    .nav-link {
      color: var(--text-secondary); text-decoration: none; font-size: 14px; font-weight: 600;
      cursor: pointer; transition: color 0.15s; outline: none; border-radius: 4px; padding: 4px 8px;
    }
    .nav-link:hover, .nav-link.active, .nav-link:focus-visible { color: var(--brand-cyan); }
    .search-box {
      position: relative; width: 320px;
    }
    .search-input {
      width: 100%; background: var(--bg-surface1); border: 1px solid var(--bg-surface3);
      padding: 8px 14px 8px 36px; border-radius: 20px; color: #fff; font-size: 13px; outline: none;
      transition: border-color 0.2s, box-shadow 0.2s;
    }
    .search-input:focus { border-color: var(--brand-cyan); box-shadow: 0 0 10px rgba(0,229,255,0.25); }
    .search-icon { position: absolute; left: 12px; top: 9px; font-size: 14px; color: var(--text-muted); }

    /* Category Filter Chips */
    .genre-bar {
      display: flex; gap: 10px; padding: 14px 32px; overflow-x: auto;
      background: var(--bg-surface1); border-bottom: 1px solid var(--bg-surface2);
    }
    .genre-chip {
      background: var(--bg-surface2); color: var(--text-secondary);
      padding: 6px 14px; border-radius: 16px; font-size: 12px; font-weight: 600;
      cursor: pointer; white-space: nowrap; border: 1px solid transparent; transition: all 0.15s; outline: none;
    }
    .genre-chip:hover, .genre-chip.active, .genre-chip:focus-visible {
      background: rgba(0,229,255,0.15); color: var(--brand-cyan); border-color: var(--brand-cyan);
    }

    /* Cinematic Hero Billboard */
    .hero {
      position: relative; width: 100%; height: 520px;
      display: flex; align-items: flex-end; padding: 48px 32px;
      background-size: cover; background-position: center;
    }
    .hero-gradient {
      position: absolute; inset: 0;
      background: linear-gradient(0deg, var(--bg-canvas) 0%, rgba(9,13,22,0.6) 50%, rgba(9,13,22,0.2) 100%),
                  linear-gradient(90deg, var(--bg-canvas) 0%, rgba(9,13,22,0.8) 35%, transparent 70%);
    }
    .hero-content { position: relative; z-index: 2; max-width: 650px; }
    .hero-badges { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; flex-wrap: wrap; }
    .badge-pill {
      background: rgba(255,255,255,0.15); backdrop-filter: blur(4px);
      padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: 700;
    }
    .badge-rating { background: var(--brand-amber); color: #000; font-weight: 800; }
    .badge-legal { background: rgba(16,185,129,0.2); color: var(--brand-green); border: 1px solid var(--brand-green); }
    .hero-title { font-size: 42px; font-weight: 900; line-height: 1.1; margin-bottom: 12px; }
    .hero-desc { font-size: 15px; color: var(--text-secondary); line-height: 1.5; margin-bottom: 22px; max-height: 70px; overflow: hidden; }
    .hero-actions { display: flex; gap: 14px; align-items: center; flex-wrap: wrap; }
    .btn-play {
      display: inline-flex; align-items: center; gap: 8px;
      background: var(--brand-cyan); color: #000; font-weight: 800; font-size: 14px;
      padding: 12px 26px; border-radius: 6px; cursor: pointer; border: none; transition: transform 0.15s, background 0.15s; outline: none;
    }
    .btn-play:hover, .btn-play:focus-visible { transform: scale(1.04); background: #33EBFF; }
    .btn-secondary {
      display: inline-flex; align-items: center; gap: 8px;
      background: rgba(255,255,255,0.15); color: #fff; font-weight: 700; font-size: 14px;
      padding: 12px 20px; border-radius: 6px; cursor: pointer; border: none; backdrop-filter: blur(8px);
      transition: background 0.15s; outline: none;
    }
    .btn-secondary:hover, .btn-secondary:focus-visible { background: rgba(255,255,255,0.25); }

    /* Netflix / MovieBox Trays */
    .section-tray { padding: 28px 32px 10px; }
    .tray-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
    .tray-title { font-size: 20px; font-weight: 800; display: flex; align-items: center; gap: 10px; }
    .tray-title span { color: var(--brand-cyan); font-size: 14px; font-weight: 600; }
    .tray-grid {
      display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 18px;
    }

    /* 2:3 Movie Poster Cards */
    .movie-card {
      position: relative; background: var(--bg-surface1); border-radius: 8px; overflow: hidden;
      cursor: pointer; transition: transform 0.2s, box-shadow 0.2s, border-color 0.2s;
      border: 1px solid rgba(255,255,255,0.06); outline: none;
    }
    .movie-card:hover, .movie-card:focus-visible {
      transform: translateY(-6px) scale(1.03);
      box-shadow: 0 12px 28px rgba(0, 229, 255, 0.25);
      border-color: var(--brand-cyan);
    }
    .poster-wrap { position: relative; width: 100%; padding-top: 148%; background: #161D2F; overflow: hidden; }
    .poster-img {
      position: absolute; top: 0; left: 0; width: 100%; height: 100%; object-fit: cover;
    }
    .card-badges {
      position: absolute; top: 8px; left: 8px; right: 8px;
      display: flex; justify-content: space-between; align-items: center; pointer-events: none;
    }
    .quality-tag {
      background: rgba(0,0,0,0.75); color: var(--brand-cyan); font-size: 10px; font-weight: 800;
      padding: 2px 6px; border-radius: 3px; border: 1px solid var(--brand-cyan);
    }
    .rating-tag {
      background: rgba(0,0,0,0.8); color: var(--brand-amber); font-size: 10px; font-weight: 800;
      padding: 2px 6px; border-radius: 3px;
    }
    .card-info { padding: 10px 12px 14px; }
    .card-title { font-size: 14px; font-weight: 700; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-bottom: 4px; }
    .card-meta { font-size: 11px; color: var(--text-secondary); display: flex; justify-content: space-between; }
    .card-genre { color: var(--brand-cyan); font-size: 10px; font-weight: 600; margin-top: 4px; }

    /* MovieBox Multi-Server Player Modal */
    .modal-overlay {
      position: fixed; inset: 0; z-index: 999; background: rgba(4, 7, 13, 0.92);
      backdrop-filter: blur(14px); display: none; align-items: center; justify-content: center;
      padding: 20px; overflow-y: auto;
    }
    .modal-overlay.active { display: flex; }
    .modal-content {
      background: var(--bg-surface1); border: 1px solid var(--bg-surface3);
      border-radius: 14px; width: 100%; max-width: 1060px; overflow: hidden;
      box-shadow: 0 25px 60px rgba(0,0,0,0.8); animation: modalIn 0.2s ease-out;
    }
    @keyframes modalIn { from { opacity: 0; transform: scale(0.96); } to { opacity: 1; transform: scale(1); } }
    .modal-header {
      display: flex; justify-content: space-between; align-items: center;
      padding: 14px 24px; background: var(--bg-surface2); border-bottom: 1px solid var(--bg-surface3);
    }
    .modal-title { font-size: 18px; font-weight: 800; display: flex; align-items: center; gap: 10px; }
    .btn-close {
      background: rgba(255,255,255,0.1); border: none; color: #fff; font-size: 18px;
      width: 32px; height: 32px; border-radius: 50%; cursor: pointer; display: flex;
      align-items: center; justify-content: center; transition: background 0.15s; outline: none;
    }
    .btn-close:hover, .btn-close:focus-visible { background: var(--brand-red); }
    .player-section { background: #000; width: 100%; position: relative; }
    video { width: 100%; max-height: 520px; outline: none; display: block; }

    /* Resume Playback Banner Overlay */
    .resume-banner {
      position: absolute; bottom: 40px; left: 20px; right: 20px;
      background: rgba(16, 22, 38, 0.94); backdrop-filter: blur(8px);
      border: 1px solid var(--brand-amber); padding: 12px 18px; border-radius: 8px;
      display: none; align-items: center; justify-content: space-between; z-index: 15;
    }
    .resume-text { font-size: 13px; font-weight: 700; color: #fff; }
    .resume-actions { display: flex; gap: 10px; }
    .btn-resume {
      background: var(--brand-amber); color: #000; font-weight: 800; font-size: 12px;
      padding: 6px 14px; border-radius: 4px; border: none; cursor: pointer; outline: none;
    }
    .btn-restart {
      background: rgba(255,255,255,0.15); color: #fff; font-weight: 600; font-size: 12px;
      padding: 6px 12px; border-radius: 4px; border: none; cursor: pointer; outline: none;
    }

    /* Player Action Bar (PiP, Speed, Fullscreen) */
    .player-actions-bar {
      display: flex; justify-content: space-between; align-items: center;
      padding: 8px 24px; background: #070B14; border-bottom: 1px solid rgba(255,255,255,0.06);
      flex-wrap: wrap; gap: 8px;
    }
    .player-actions-left, .player-actions-right { display: flex; align-items: center; gap: 8px; }
    .btn-action-sm {
      background: var(--bg-surface2); color: var(--text-secondary); border: 1px solid var(--bg-surface3);
      padding: 5px 10px; border-radius: 4px; font-size: 11px; font-weight: 700; cursor: pointer;
      display: inline-flex; align-items: center; gap: 5px; outline: none; transition: all 0.15s;
    }
    .btn-action-sm:hover, .btn-action-sm:focus-visible { background: var(--brand-cyan); color: #000; }

    /* Multi-Server Aggregator Bar */
    .server-bar {
      padding: 14px 24px; background: var(--bg-surface2); border-bottom: 1px solid var(--bg-surface3);
      display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px;
    }
    .server-label { font-size: 13px; font-weight: 700; color: var(--text-secondary); display: flex; align-items: center; gap: 6px; }
    .server-tabs { display: flex; gap: 8px; flex-wrap: wrap; }
    .server-btn {
      background: var(--bg-surface3); color: var(--text-secondary); border: 1px solid transparent;
      padding: 7px 14px; border-radius: 6px; font-size: 12px; font-weight: 700; cursor: pointer;
      display: flex; align-items: center; gap: 6px; transition: all 0.15s; outline: none;
    }
    .server-btn.active, .server-btn:focus-visible {
      background: rgba(0,229,255,0.15); color: var(--brand-cyan); border-color: var(--brand-cyan);
    }
    .server-health {
      font-size: 11px; color: var(--brand-green); font-weight: 700;
      display: flex; align-items: center; gap: 6px;
    }

    /* Modal Details Body */
    .modal-body { padding: 24px; display: grid; grid-template-columns: 1fr 300px; gap: 24px; }
    @media (max-width: 800px) { .modal-body { grid-template-columns: 1fr; } }
    .details-title { font-size: 24px; font-weight: 800; margin-bottom: 8px; }
    .details-meta { color: var(--text-secondary); font-size: 13px; margin-bottom: 14px; display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
    .details-desc { font-size: 14px; line-height: 1.6; color: var(--text-secondary); margin-bottom: 18px; }
    .download-panel {
      background: var(--bg-surface2); border: 1px solid var(--bg-surface3);
      border-radius: 8px; padding: 16px;
    }
    .download-panel h4 { font-size: 14px; font-weight: 800; margin-bottom: 12px; display: flex; align-items: center; gap: 8px; }
    .download-link-btn {
      display: flex; align-items: center; justify-content: space-between;
      background: rgba(0,229,255,0.1); border: 1px solid rgba(0,229,255,0.3);
      padding: 10px 14px; border-radius: 6px; color: var(--brand-cyan); text-decoration: none;
      font-size: 13px; font-weight: 700; margin-bottom: 8px; transition: all 0.15s; outline: none;
    }
    .download-link-btn:hover, .download-link-btn:focus-visible { background: var(--brand-cyan); color: #000; }
    .creator-fund-box {
      background: rgba(255,179,0,0.08); border: 1px solid rgba(255,179,0,0.3);
      border-radius: 8px; padding: 14px; margin-top: 14px; font-size: 12px; line-height: 1.4;
    }

    /* Floating Toast Notification */
    .toast-msg {
      position: fixed; top: 20px; right: 20px; z-index: 10000;
      background: rgba(16, 22, 38, 0.96); border: 1px solid var(--brand-cyan);
      color: #fff; padding: 10px 18px; border-radius: 8px; font-size: 13px; font-weight: 700;
      box-shadow: 0 10px 25px rgba(0,0,0,0.8); display: none; align-items: center; gap: 8px;
    }

    /* Bottom Status Bar for Shortcuts & Android TV */
    .status-bar {
      position: fixed; bottom: 0; left: 0; right: 0; z-index: 90;
      background: rgba(9, 13, 22, 0.94); backdrop-filter: blur(10px);
      border-top: 1px solid rgba(255,255,255,0.06); padding: 8px 24px;
      font-size: 11px; color: var(--text-muted); display: flex; justify-content: space-between; align-items: center;
    }
    .key-badge {
      background: var(--bg-surface2); border: 1px solid var(--bg-surface3);
      padding: 2px 6px; border-radius: 3px; color: var(--brand-cyan); font-family: monospace; font-weight: bold;
    }

    /* Shortcuts Cheat Sheet Modal */
    .shortcuts-modal {
      position: fixed; inset: 0; z-index: 10001; background: rgba(0,0,0,0.85);
      display: none; align-items: center; justify-content: center; padding: 20px;
    }
    .shortcuts-modal.active { display: flex; }
    .shortcuts-card {
      background: var(--bg-surface1); border: 1px solid var(--bg-surface3);
      border-radius: 12px; padding: 24px; max-width: 520px; width: 100%;
    }
    .shortcuts-table { width: 100%; border-collapse: collapse; margin-top: 14px; }
    .shortcuts-table td { padding: 8px 4px; border-bottom: 1px solid var(--bg-surface2); font-size: 13px; }
  </style>
</head>
<body>

  <!-- Floating Notification Toast -->
  <div class="toast-msg" id="toastBox">
    <span id="toastIcon">⚡</span>
    <span id="toastText">Notification</span>
  </div>

  <!-- Top Navbar -->
  <nav class="navbar">
    <div class="nav-left">
      <a href="#" class="logo" onclick="switchNav('home')" tabindex="0">
        🎬 MOVIEBOX <span class="logo-badge">HD</span>
      </a>
      <ul class="nav-links">
        <li><a class="nav-link active" id="nav-home" onclick="switchNav('home')" tabindex="0">Home</a></li>
        <li><a class="nav-link" id="nav-movies" onclick="switchNav('movies')" tabindex="0">Movies</a></li>
        <li><a class="nav-link" id="nav-series" onclick="switchNav('series')" tabindex="0">Series & Shorts</a></li>
        <li><a class="nav-link" id="nav-watchlist" onclick="switchNav('watchlist')" tabindex="0">Watchlist (<span id="wlCount">0</span>)</a></li>
      </ul>
    </div>
    <div class="search-box">
      <span class="search-icon">🔍</span>
      <input type="text" class="search-input" id="searchInput" placeholder="Search movies, genres, stars... (Press / to focus)" oninput="handleSearch(this.value)" tabindex="0">
    </div>
  </nav>

  <!-- Genre Filter Bar -->
  <div class="genre-bar">
    <div class="genre-chip active" onclick="filterGenre('All')" tabindex="0">All Genres</div>
    <div class="genre-chip" onclick="filterGenre('Animation')" tabindex="0">Animation</div>
    <div class="genre-chip" onclick="filterGenre('Sci-Fi')" tabindex="0">Sci-Fi & Cyberpunk</div>
    <div class="genre-chip" onclick="filterGenre('Action')" tabindex="0">Action & Adventure</div>
    <div class="genre-chip" onclick="filterGenre('Horror')" tabindex="0">Horror & Mystery</div>
    <div class="genre-chip" onclick="filterGenre('Classic')" tabindex="0">Classics & Golden Age</div>
    <div class="genre-chip" onclick="filterGenre('Documentary')" tabindex="0">NASA & Documentary</div>
  </div>

  <!-- Main View Container -->
  <div id="mainView">

    <!-- Hero Spotlight Billboard -->
    <div class="hero" id="heroBillboard" style="background-image: url('${heroItem.backdropUrl}');">
      <div class="hero-gradient"></div>
      <div class="hero-content">
        <div class="hero-badges">
          <span class="badge-pill badge-rating">★ 8.8</span>
          <span class="badge-pill">4K UHD</span>
          <span class="badge-pill">${heroItem.releaseYear}</span>
          <span class="badge-pill badge-legal">✔ 100% Legal / ${heroItem.attribution.licenseType}</span>
        </div>
        <h1 class="hero-title">${heroItem.title}</h1>
        <p class="hero-desc">${heroItem.description}</p>
        <div class="hero-actions">
          <button class="btn-play" onclick="openPlayerModal('${heroItem.id}')" tabindex="0">▶ Watch Now</button>
          <button class="btn-secondary" onclick="toggleWatchlist('${heroItem.id}')" id="heroWlBtn" tabindex="0">＋ Watchlist</button>
          <a class="btn-secondary" style="text-decoration:none;" href="${heroItem.sources[0]?.url || '#'}" download target="_blank" tabindex="0">⬇ Direct Download</a>
        </div>
      </div>
    </div>

    <!-- Movie Trays Container -->
    <div id="traysContainer">
      <!-- Trays populated dynamically -->
    </div>

  </div>

  <!-- Search & Filter Results Container -->
  <div id="searchResultsView" style="display:none; padding: 24px 32px;">
    <h2 style="font-size: 22px; font-weight: 800; margin-bottom: 18px;" id="searchHeader">Search Results</h2>
    <div class="tray-grid" id="searchGrid"></div>
  </div>

  <!-- MovieBox Multi-Server Streaming & Download Modal -->
  <div class="modal-overlay" id="playerModal" onclick="closeModalOnBg(event)">
    <div class="modal-content" onclick="event.stopPropagation()">
      <div class="modal-header">
        <div class="modal-title">
          <span id="modalHeaderTitle">MovieBox Player</span>
          <span class="badge-pill badge-legal" id="modalLicenseBadge">Verified Legal Stream</span>
        </div>
        <button class="btn-close" onclick="closePlayerModal()" tabindex="0" title="Close (Esc)">✕</button>
      </div>

      <!-- Cinema Video Player -->
      <div class="player-section">
        <video id="activeVideoPlayer" controls autoplay playsinline preload="metadata">
          Your browser does not support HTML5 video.
        </video>

        <!-- Resume Banner Overlay -->
        <div class="resume-banner" id="resumeBanner">
          <span class="resume-text" id="resumeText">Resume playback at 00:00?</span>
          <div class="resume-actions">
            <button class="btn-resume" onclick="confirmResume(true)" tabindex="0">▶ Resume</button>
            <button class="btn-restart" onclick="confirmResume(false)" tabindex="0">↺ Start Over</button>
          </div>
        </div>
      </div>

      <!-- Player Action Bar (PiP, Speed, Fullscreen, Share) -->
      <div class="player-actions-bar">
        <div class="player-actions-left">
          <button class="btn-action-sm" onclick="cycleSpeed()" id="speedBtn" tabindex="0" title="Change Playback Speed">⚡ Speed: 1x</button>
          <button class="btn-action-sm" onclick="togglePip()" id="pipBtn" tabindex="0" title="Picture-in-Picture (P)">📺 PiP</button>
          <button class="btn-action-sm" onclick="toggleFullscreen()" tabindex="0" title="Toggle Fullscreen (F)">⛶ Fullscreen</button>
        </div>
        <div class="player-actions-right">
          <button class="btn-action-sm" onclick="copyCurrentStreamUrl()" tabindex="0">🔗 Copy Stream URL</button>
        </div>
      </div>

      <!-- Multi-Server Selector Bar (MovieBox / BeeTV Aggregator) -->
      <div class="server-bar">
        <div class="server-label">
          <span>⚡ Streaming Servers:</span>
        </div>
        <div class="server-tabs" id="serverTabsContainer">
          <!-- Populated dynamically with Server 1, Server 2, Server 3 -->
        </div>
        <div class="server-health">
          <span>🟢 100% Online & Fast</span>
        </div>
      </div>

      <!-- Movie Details & Download Links -->
      <div class="modal-body">
        <div>
          <h2 class="details-title" id="mDetailsTitle">Movie Title</h2>
          <div class="details-meta">
            <span id="mDetailsYear">2026</span> •
            <span id="mDetailsDuration">120 min</span> •
            <span id="mDetailsRating" class="badge-pill badge-rating">★ 8.5</span> •
            <span id="mDetailsCreator">Creator</span>
          </div>
          <p class="details-desc" id="mDetailsDesc">Synopsis</p>
          <div style="font-size: 12px; color: var(--text-muted); margin-top: 8px;">
            License: <strong id="mDetailsLicense" style="color: var(--brand-cyan);">CC-BY</strong> • Source: <a id="mDetailsSourceUrl" href="#" target="_blank" style="color: var(--brand-cyan);">Official Creator Archive</a>
          </div>
        </div>

        <div class="download-panel">
          <h4>📥 Direct Download Center</h4>
          <div id="downloadButtonsContainer">
            <!-- Download buttons -->
          </div>
          <div class="creator-fund-box">
            <strong>Support the Creators:</strong>
            <p style="margin-top: 4px; color: var(--text-secondary);">
              This title is free and open to the public. You can support the creators directly through their official donation funds.
            </p>
            <a id="creatorFundLink" href="https://fund.blender.org" target="_blank" style="display:inline-block; margin-top:8px; color: var(--brand-amber); font-weight: bold; text-decoration: none;" tabindex="0">
              ❤ Support Creator Fund →
            </a>
          </div>
        </div>
      </div>

    </div>
  </div>

  <!-- Keyboard & TV Remote Shortcuts Help Modal -->
  <div class="shortcuts-modal" id="shortcutsModal" onclick="toggleShortcutsModal(false)">
    <div class="shortcuts-card" onclick="event.stopPropagation()">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
        <h3 style="font-size:18px; font-weight:800; color:var(--brand-cyan);">⌨ Controls & Navigation Guide</h3>
        <button class="btn-close" onclick="toggleShortcutsModal(false)">✕</button>
      </div>
      <table class="shortcuts-table">
        <tr><td><span class="key-badge">Space</span> or <span class="key-badge">K</span></td><td>Play / Pause Video</td></tr>
        <tr><td><span class="key-badge">F</span></td><td>Toggle Fullscreen</td></tr>
        <tr><td><span class="key-badge">M</span></td><td>Mute / Unmute Audio</td></tr>
        <tr><td><span class="key-badge">←</span> / <span class="key-badge">→</span></td><td>Seek backward / forward 10 seconds</td></tr>
        <tr><td><span class="key-badge">↑</span> / <span class="key-badge">↓</span></td><td>Volume Up / Down (10%)</td></tr>
        <tr><td><span class="key-badge">P</span></td><td>Picture-in-Picture (PiP) Mode</td></tr>
        <tr><td><span class="key-badge">/</span></td><td>Quick Search</td></tr>
        <tr><td><span class="key-badge">Esc</span></td><td>Close Modal / Exit Fullscreen</td></tr>
        <tr><td><span class="key-badge">Android TV D-Pad</span></td><td>Navigate rows & cards; Press <strong>OK</strong> to play</td></tr>
      </table>
    </div>
  </div>

  <!-- Bottom Helper Bar for PC & TV -->
  <div class="status-bar">
    <div>
      <span>🎮 <strong>Android TV & PC</strong>: Use <span class="key-badge">Arrow Keys</span> + <span class="key-badge">Enter</span> to browse • <span class="key-badge">Space</span> Play • <span class="key-badge">F</span> Fullscreen • <span class="key-badge">M</span> Mute</span>
    </div>
    <div>
      <a href="javascript:void(0)" onclick="toggleShortcutsModal(true)" style="color:var(--brand-cyan); text-decoration:none; font-weight:bold;">[?] Shortcuts Guide</a>
    </div>
  </div>

  <script>
    // Master Catalog Data
    const CATALOG = ${JSON.stringify(allItems)};
    let activeMovie = CATALOG[0];
    let activeServerIndex = 0;
    let watchlist = JSON.parse(localStorage.getItem('moviebox_watchlist') || '[]');
    let currentSpeed = 1.0;
    let pendingResumeTime = 0;

    function showToast(msg, icon = '⚡') {
      const toast = document.getElementById('toastBox');
      document.getElementById('toastText').innerText = msg;
      document.getElementById('toastIcon').innerText = icon;
      toast.style.display = 'flex';
      clearTimeout(window._toastTimeout);
      window._toastTimeout = setTimeout(() => {
        toast.style.display = 'none';
      }, 1800);
    }

    function updateWatchlistCount() {
      document.getElementById('wlCount').innerText = watchlist.length;
    }
    updateWatchlistCount();

    function toggleWatchlist(id) {
      if (watchlist.includes(id)) {
        watchlist = watchlist.filter(item => item !== id);
        showToast('Removed from Watchlist', '🗑');
      } else {
        watchlist.push(id);
        showToast('Added to Watchlist', '⭐');
      }
      localStorage.setItem('moviebox_watchlist', JSON.stringify(watchlist));
      updateWatchlistCount();
      renderTrays();
      if (document.getElementById('nav-watchlist').classList.contains('active')) {
        renderWatchlistView();
      }
    }

    function renderMovieCard(item) {
      return \`
        <div class="movie-card" onclick="openPlayerModal('\${item.id}')" tabindex="0" data-id="\${item.id}">
          <div class="poster-wrap">
            <img class="poster-img" src="\${item.posterUrl}" alt="\${item.title}" loading="lazy" onerror="this.src='\${item.backdropUrl}'">
            <div class="card-badges">
              <span class="quality-tag">\${item.sources[0]?.resolution || '1080p'}</span>
              <span class="rating-tag">★ \${item.rating}</span>
            </div>
          </div>
          <div class="card-info">
            <div class="card-title">\${item.title}</div>
            <div class="card-meta">
              <span>\${item.releaseYear}</span>
              <span>\${Math.round(item.durationSeconds / 60)} min</span>
            </div>
            <div class="card-genre">\${(item.genres || []).slice(0, 2).join(' • ')}</div>
          </div>
        </div>
      \`;
    }

    function renderTrays() {
      const container = document.getElementById('traysContainer');
      const trendingItems = CATALOG.slice(0, 6);
      const openCinema = CATALOG.filter(m => m.category === 'Blender Open Movies');
      const classics = CATALOG.filter(m => m.category === 'Public Domain Classics');
      const science = CATALOG.filter(m => m.category === 'NASA & Science');

      container.innerHTML = \`
        <div class="section-tray">
          <div class="tray-header">
            <h2 class="tray-title">🔥 Trending Now on MovieBox <span>High Speed HD</span></h2>
          </div>
          <div class="tray-grid">
            \${trendingItems.map(renderMovieCard).join('')}
          </div>
        </div>

        <div class="section-tray">
          <div class="tray-header">
            <h2 class="tray-title">🎬 Featured Open Cinema & Independent Masterpieces <span>100% Free & Legal</span></h2>
          </div>
          <div class="tray-grid">
            \${openCinema.map(renderMovieCard).join('')}
          </div>
        </div>

        <div class="section-tray">
          <div class="tray-header">
            <h2 class="tray-title">🍿 Legendary Classics & Public Domain Cinema <span>Classic Vault</span></h2>
          </div>
          <div class="tray-grid">
            \${classics.map(renderMovieCard).join('')}
          </div>
        </div>

        \${science.length ? \`
        <div class="section-tray">
          <div class="tray-header">
            <h2 class="tray-title">🌌 NASA & Space Exploration Documentaries <span>4K Science</span></h2>
          </div>
          <div class="tray-grid">
            \${science.map(renderMovieCard).join('')}
          </div>
        </div>\` : ''}
      \`;
    }
    renderTrays();

    function formatTime(secs) {
      const m = Math.floor(secs / 60);
      const s = Math.floor(secs % 60);
      return (m < 10 ? '0' : '') + m + ':' + (s < 10 ? '0' : '') + s;
    }

    function openPlayerModal(id) {
      const item = CATALOG.find(m => m.id === id);
      if (!item) return;
      activeMovie = item;
      activeServerIndex = 0;

      document.getElementById('modalHeaderTitle').innerText = item.title;
      document.getElementById('modalLicenseBadge').innerText = item.attribution.licenseType;
      document.getElementById('mDetailsTitle').innerText = item.title;
      document.getElementById('mDetailsYear').innerText = item.releaseYear;
      document.getElementById('mDetailsDuration').innerText = Math.round(item.durationSeconds / 60) + ' min';
      document.getElementById('mDetailsRating').innerText = '★ ' + item.rating;
      document.getElementById('mDetailsCreator').innerText = item.attribution.creator;
      document.getElementById('mDetailsDesc').innerText = item.description;
      document.getElementById('mDetailsLicense').innerText = item.attribution.licenseType;
      document.getElementById('mDetailsSourceUrl').href = item.attribution.sourceUrl || '#';
      document.getElementById('mDetailsSourceUrl').innerText = item.attribution.sourceUrl || 'Public Archive';

      if (item.attribution.sourceUrl && item.attribution.sourceUrl.includes('blender')) {
        document.getElementById('creatorFundLink').href = 'https://fund.blender.org';
        document.getElementById('creatorFundLink').innerText = '❤ Support Blender Studio Fund →';
      } else {
        document.getElementById('creatorFundLink').href = 'https://archive.org/donate';
        document.getElementById('creatorFundLink').innerText = '❤ Donate to Internet Archive →';
      }

      // Build Multi-Server Selector Tabs (MovieBox Aggregator)
      const serverTabs = document.getElementById('serverTabsContainer');
      const sources = item.sources || [];
      serverTabs.innerHTML = sources.map((src, idx) => \`
        <button class="server-btn \${idx === 0 ? 'active' : ''}" onclick="switchServer(\${idx})" tabindex="0">
          ⚡ Server \${idx + 1} (\${src.format.toUpperCase()} \${src.resolution})
        </button>
      \`).join('');

      // Build Direct Download Buttons
      const dlContainer = document.getElementById('downloadButtonsContainer');
      dlContainer.innerHTML = sources.map((src, idx) => \`
        <a class="download-link-btn" href="\${src.url}" download target="_blank" tabindex="0">
          <span>⬇ Server \${idx + 1} (\${src.resolution})</span>
          <span style="font-size:11px; opacity:0.8;">Direct MP4</span>
        </a>
      \`).join('');

      // Play on initial server
      const video = document.getElementById('activeVideoPlayer');
      video.poster = item.backdropUrl || item.posterUrl;
      video.src = sources[0]?.url || '';
      video.playbackRate = currentSpeed;
      video.load();

      // Check Saved Playback Position for Resume Feature
      const savedPos = parseFloat(localStorage.getItem('mb_pos_' + item.id) || '0');
      const resumeBanner = document.getElementById('resumeBanner');
      if (savedPos > 15) {
        pendingResumeTime = savedPos;
        document.getElementById('resumeText').innerText = 'Resume "' + item.title + '" from ' + formatTime(savedPos) + '?';
        resumeBanner.style.display = 'flex';
      } else {
        resumeBanner.style.display = 'none';
        video.play().catch(() => {});
      }

      document.getElementById('playerModal').classList.add('active');
    }

    function confirmResume(shouldResume) {
      const video = document.getElementById('activeVideoPlayer');
      const banner = document.getElementById('resumeBanner');
      banner.style.display = 'none';
      if (shouldResume && pendingResumeTime > 0) {
        video.currentTime = pendingResumeTime;
        showToast('Resumed at ' + formatTime(pendingResumeTime), '⏩');
      } else {
        video.currentTime = 0;
        showToast('Playing from beginning', '▶');
      }
      video.play().catch(() => {});
    }

    // Save playback position periodically
    const videoElem = document.getElementById('activeVideoPlayer');
    videoElem.addEventListener('timeupdate', () => {
      if (activeMovie && videoElem.currentTime > 5) {
        localStorage.setItem('mb_pos_' + activeMovie.id, videoElem.currentTime);
      }
    });

    function switchServer(index) {
      if (!activeMovie || !activeMovie.sources[index]) return;
      activeServerIndex = index;
      const video = document.getElementById('activeVideoPlayer');
      const currentTime = video.currentTime;
      const newSource = activeMovie.sources[index];

      document.querySelectorAll('.server-btn').forEach((btn, idx) => {
        if (idx === index) btn.classList.add('active');
        else btn.classList.remove('active');
      });

      video.src = newSource.url;
      video.currentTime = currentTime;
      video.play().catch(() => {});
      showToast('Switched to Server ' + (index + 1) + ' (' + newSource.resolution + ')', '⚡');
    }

    function cycleSpeed() {
      const video = document.getElementById('activeVideoPlayer');
      const speeds = [1.0, 1.25, 1.5, 2.0];
      let nextIndex = (speeds.indexOf(currentSpeed) + 1) % speeds.length;
      currentSpeed = speeds[nextIndex];
      video.playbackRate = currentSpeed;
      document.getElementById('speedBtn').innerText = '⚡ Speed: ' + currentSpeed + 'x';
      showToast('Speed: ' + currentSpeed + 'x', '⚡');
    }

    async function togglePip() {
      const video = document.getElementById('activeVideoPlayer');
      try {
        if (document.pictureInPictureElement) {
          await document.exitPictureInPicture();
          showToast('Exited Picture-in-Picture', '📺');
        } else if (document.pictureInPictureEnabled) {
          await video.requestPictureInPicture();
          showToast('Picture-in-Picture active', '📺');
        }
      } catch (err) {
        showToast('PiP not supported', '⚠');
      }
    }

    function toggleFullscreen() {
      const modalContent = document.querySelector('.modal-content');
      if (!document.fullscreenElement) {
        modalContent.requestFullscreen().catch(() => {});
        showToast('Fullscreen Mode', '⛶');
      } else {
        document.exitFullscreen().catch(() => {});
        showToast('Exited Fullscreen', '⛶');
      }
    }

    function copyCurrentStreamUrl() {
      const url = activeMovie?.sources[activeServerIndex]?.url;
      if (url) {
        navigator.clipboard.writeText(url).then(() => {
          showToast('Stream URL copied to clipboard!', '📋');
        }).catch(() => {
          showToast(url, '🔗');
        });
      }
    }

    function closePlayerModal() {
      const video = document.getElementById('activeVideoPlayer');
      video.pause();
      video.src = '';
      document.getElementById('playerModal').classList.remove('active');
    }

    function closeModalOnBg(e) {
      if (e.target.id === 'playerModal') closePlayerModal();
    }

    function toggleShortcutsModal(show) {
      const modal = document.getElementById('shortcutsModal');
      if (show) modal.classList.add('active');
      else modal.classList.remove('active');
    }

    function handleSearch(query) {
      const q = query.toLowerCase().trim();
      const mainView = document.getElementById('mainView');
      const searchView = document.getElementById('searchResultsView');
      const searchGrid = document.getElementById('searchGrid');

      if (!q) {
        mainView.style.display = 'block';
        searchView.style.display = 'none';
        return;
      }

      mainView.style.display = 'none';
      searchView.style.display = 'block';
      document.getElementById('searchHeader').innerText = 'Search Results for "' + query + '"';

      const filtered = CATALOG.filter(m => 
        m.title.toLowerCase().includes(q) ||
        m.description.toLowerCase().includes(q) ||
        m.attribution.creator.toLowerCase().includes(q) ||
        (m.genres || []).some(g => g.toLowerCase().includes(q))
      );

      if (filtered.length === 0) {
        searchGrid.innerHTML = '<p style="color:var(--text-muted); padding:20px;">No movies found matching "' + query + '".</p>';
      } else {
        searchGrid.innerHTML = filtered.map(renderMovieCard).join('');
      }
    }

    function filterGenre(genre) {
      document.querySelectorAll('.genre-chip').forEach(c => c.classList.remove('active'));
      event.target.classList.add('active');

      if (genre === 'All') {
        document.getElementById('mainView').style.display = 'block';
        document.getElementById('searchResultsView').style.display = 'none';
        renderTrays();
        return;
      }

      document.getElementById('mainView').style.display = 'none';
      document.getElementById('searchResultsView').style.display = 'block';
      document.getElementById('searchHeader').innerText = genre + ' Movies & Shows';

      const filtered = CATALOG.filter(m => 
        (m.genres || []).some(g => g.toLowerCase().includes(genre.toLowerCase())) ||
        m.category.toLowerCase().includes(genre.toLowerCase())
      );

      const searchGrid = document.getElementById('searchGrid');
      searchGrid.innerHTML = filtered.map(renderMovieCard).join('');
    }

    function switchNav(tab) {
      document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
      const activeLink = document.getElementById('nav-' + tab);
      if (activeLink) activeLink.classList.add('active');

      const mainView = document.getElementById('mainView');
      const searchView = document.getElementById('searchResultsView');
      const searchGrid = document.getElementById('searchGrid');

      if (tab === 'home') {
        mainView.style.display = 'block';
        searchView.style.display = 'none';
        renderTrays();
      } else if (tab === 'movies') {
        mainView.style.display = 'none';
        searchView.style.display = 'block';
        document.getElementById('searchHeader').innerText = 'All Movies (' + CATALOG.length + ')';
        searchGrid.innerHTML = CATALOG.map(renderMovieCard).join('');
      } else if (tab === 'series') {
        mainView.style.display = 'none';
        searchView.style.display = 'block';
        document.getElementById('searchHeader').innerText = 'Animated Series & Open Cinema Shorts';
        const filtered = CATALOG.filter(m => m.category === 'Blender Open Movies');
        searchGrid.innerHTML = filtered.map(renderMovieCard).join('');
      } else if (tab === 'watchlist') {
        mainView.style.display = 'none';
        searchView.style.display = 'block';
        renderWatchlistView();
      }
    }

    function renderWatchlistView() {
      const searchGrid = document.getElementById('searchGrid');
      const savedItems = CATALOG.filter(m => watchlist.includes(m.id));
      document.getElementById('searchHeader').innerText = 'My Watchlist (' + savedItems.length + ')';

      if (savedItems.length === 0) {
        searchGrid.innerHTML = '<p style="color:var(--text-muted); padding:20px;">Your watchlist is empty. Click "+ Watchlist" on any movie to bookmark it here!</p>';
      } else {
        searchGrid.innerHTML = savedItems.map(renderMovieCard).join('');
      }
    }

    // =========================================================================
    // KEYBOARD SHORTCUTS & ANDROID TV D-PAD SPATIAL NAVIGATION ENGINE
    // =========================================================================
    document.addEventListener('keydown', (e) => {
      const video = document.getElementById('activeVideoPlayer');
      const isModalOpen = document.getElementById('playerModal').classList.contains('active');
      const isShortcutsOpen = document.getElementById('shortcutsModal').classList.contains('active');
      const isSearchFocused = document.activeElement === document.getElementById('searchInput');

      if (e.key === 'Escape') {
        if (isShortcutsOpen) { toggleShortcutsModal(false); return; }
        if (isModalOpen) { closePlayerModal(); return; }
        if (isSearchFocused) { document.getElementById('searchInput').blur(); return; }
      }

      if (e.key === '?' && !isSearchFocused) {
        toggleShortcutsModal(!isShortcutsOpen);
        return;
      }

      if (e.key === '/' && !isSearchFocused && !isModalOpen) {
        e.preventDefault();
        document.getElementById('searchInput').focus();
        return;
      }

      // Hotkeys when video modal is active
      if (isModalOpen && !isSearchFocused) {
        if (e.key === ' ' || e.key === 'k' || e.key === 'K') {
          e.preventDefault();
          if (video.paused) { video.play(); showToast('Play', '▶'); }
          else { video.pause(); showToast('Pause', '⏸'); }
          return;
        }

        if (e.key === 'f' || e.key === 'F') {
          e.preventDefault();
          toggleFullscreen();
          return;
        }

        if (e.key === 'm' || e.key === 'M') {
          e.preventDefault();
          video.muted = !video.muted;
          showToast(video.muted ? 'Muted' : 'Unmuted', video.muted ? '🔇' : '🔊');
          return;
        }

        if (e.key === 'p' || e.key === 'P') {
          e.preventDefault();
          togglePip();
          return;
        }

        if (e.key === 'ArrowLeft') {
          e.preventDefault();
          video.currentTime = Math.max(0, video.currentTime - 10);
          showToast('-10s (' + formatTime(video.currentTime) + ')', '⏪');
          return;
        }

        if (e.key === 'ArrowRight') {
          e.preventDefault();
          video.currentTime = Math.min(video.duration || 9999, video.currentTime + 10);
          showToast('+10s (' + formatTime(video.currentTime) + ')', '⏩');
          return;
        }

        if (e.key === 'ArrowUp') {
          e.preventDefault();
          video.volume = Math.min(1, Math.round((video.volume + 0.1) * 10) / 10);
          showToast('Volume: ' + Math.round(video.volume * 100) + '%', '🔊');
          return;
        }

        if (e.key === 'ArrowDown') {
          e.preventDefault();
          video.volume = Math.max(0, Math.round((video.volume - 0.1) * 10) / 10);
          showToast('Volume: ' + Math.round(video.volume * 100) + '%', '🔉');
          return;
        }
      }

      // Android TV / Spatial Remote Navigation outside modal
      if (!isModalOpen && !isSearchFocused) {
        const focusable = Array.from(document.querySelectorAll('.movie-card, .genre-chip, .nav-link, .btn-play, .btn-secondary, .search-input'));
        const currentIndex = focusable.indexOf(document.activeElement);

        if (['ArrowDown', 'ArrowUp', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
          if (currentIndex === -1) {
            focusable[0]?.focus();
            return;
          }
          if (e.key === 'ArrowRight' && currentIndex < focusable.length - 1) {
            focusable[currentIndex + 1]?.focus();
            e.preventDefault();
          } else if (e.key === 'ArrowLeft' && currentIndex > 0) {
            focusable[currentIndex - 1]?.focus();
            e.preventDefault();
          } else if (e.key === 'ArrowDown') {
            // Find vertically lower element
            const currRect = document.activeElement.getBoundingClientRect();
            let bestMatch = null;
            let minDistance = Infinity;
            focusable.forEach(el => {
              const r = el.getBoundingClientRect();
              if (r.top > currRect.top + 20) {
                const dist = Math.hypot(r.left - currRect.left, r.top - currRect.top);
                if (dist < minDistance) { minDistance = dist; bestMatch = el; }
              }
            });
            if (bestMatch) { bestMatch.focus(); e.preventDefault(); bestMatch.scrollIntoView({ behavior: 'smooth', block: 'center' }); }
          } else if (e.key === 'ArrowUp') {
            const currRect = document.activeElement.getBoundingClientRect();
            let bestMatch = null;
            let minDistance = Infinity;
            focusable.forEach(el => {
              const r = el.getBoundingClientRect();
              if (r.bottom < currRect.bottom - 20) {
                const dist = Math.hypot(r.left - currRect.left, r.top - currRect.top);
                if (dist < minDistance) { minDistance = dist; bestMatch = el; }
              }
            });
            if (bestMatch) { bestMatch.focus(); e.preventDefault(); bestMatch.scrollIntoView({ behavior: 'smooth', block: 'center' }); }
          }
        }
      }
    });
  </script>
</body>
</html>`;
  }
  }

  listen(port = 4000, host = '0.0.0.0'): Promise<void> {
    return new Promise(resolve => {
      this.server.listen(port, host, () => {
        resolve();
      });
    });
  }

  close(): Promise<void> {
    return new Promise(resolve => {
      this.db.close();
      this.server.close(() => resolve());
    });
  }
}
