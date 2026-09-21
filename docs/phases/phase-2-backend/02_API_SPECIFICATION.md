# PHASE 2 — DELIVERABLE 2: REST API ENDPOINT SPECIFICATIONS

**Document Version**: 1.0.0  
**Phase**: Phase 2 (Backend Core)  
**Primary Owners**: Agent 6 — Backend Agent & Agent 9 — Security Agent  
**Status**: Submitted for Verification  

---

## 1. GLOBAL CONVENTIONS

- Base URL: `http://localhost:4000` (or configured host/port).
- Request & Response Body: `Content-Type: application/json`.
- Authentication: `Authorization: Bearer <jwt-token>` on protected routes.
- CORS: All origins permitted (`*`) with preflight options.

---

## 2. ENDPOINT DIRECTORY

### A. System & Health
- `GET /health`
  - Response: `{ status: "healthy" | "degraded", mediaCount: number, activeCount: number, degradedCount: number, quarantinedCount: number, timestamp: string }`

### B. Catalog & Media Discovery
- `GET /api/v1/catalog/home`
  - Response: `{ success: true, data: { featured: MediaItem[], trays: [{ title: string, category: string, items: MediaItem[] }] } }`
- `GET /api/v1/catalog/media/:id`
  - Response: `{ success: true, data: MediaItem }`
  - 404: `{ success: false, error: "Media item not found" }`
- `GET /api/v1/catalog/genres`
  - Response: `{ success: true, data: string[] }`

### C. Search & Filtering
- `GET /api/v1/search?q=query&genre=genre&category=cat&year=2010`
  - Response: `{ success: true, data: { total: number, results: MediaItem[], genresMatched: string[] } }`

### D. Authentication & Session
- `POST /api/v1/auth/register`
  - Payload: `{ email: string, password: string, displayName: string }`
  - Response (201): `{ success: true, data: { user: User, token: string } }`
- `POST /api/v1/auth/login`
  - Payload: `{ email: string, password: string }`
  - Response (200): `{ success: true, data: { user: User, token: string } }`
- `GET /api/v1/auth/me` [Protected]
  - Response (200): `{ success: true, data: User }`
  - 401: `{ success: false, error: "Unauthorized" }`
- `POST /api/v1/auth/sync` [Protected]
  - Payload: `{ bookmarks: [{ mediaId: string, positionSeconds: number, durationSeconds: number }], watchlist: string[] }`
  - Response (200): `{ success: true, data: { syncedBookmarks: number, syncedWatchlist: number } }`

### E. Playback & State Sync
- `GET /api/v1/playback/resolve/:id?format=hls`
  - Response: `{ success: true, data: { mediaId: string, title: string, activeSource: StreamSource, fallbackSource?: StreamSource, availableSources: StreamSource[], subtitles: SubtitleTrack[], attribution: LicenseAttribution } }`
- `POST /api/v1/playback/bookmark`
  - Payload: `{ mediaId: string, positionSeconds: number, durationSeconds: number }`
  - Response: `{ success: true, data: PlaybackBookmark }`
- `GET /api/v1/playback/bookmark/:id`
  - Response: `{ success: true, data: PlaybackBookmark | null }`
- `GET /api/v1/playback/continue-watching`
  - Response: `{ success: true, data: [{ media: MediaItem, bookmark: PlaybackBookmark }] }`

### F. Watchlist
- `POST /api/v1/watchlist/add`
  - Payload: `{ mediaId: string }`
- `POST /api/v1/watchlist/remove`
  - Payload: `{ mediaId: string }`
- `GET /api/v1/watchlist`
  - Response: `{ success: true, data: MediaItem[] }`

### G. Legal & DMCA Compliance
- `POST /api/v1/legal/takedown`
  - Payload: `{ mediaId: string, claimantName: string, claimantEmail: string, copyrightWorkDescription: string, statementOfGoodFaith: boolean, digitalSignature: string }`
  - Response (201): `{ success: true, data: { notice: DmcaTakedownNotice, actionTaken: string } }`
- `GET /api/v1/legal/audit`
  - Response: `{ success: true, data: DmcaTakedownNotice[] }`

### H. Telemetry & Analytics
- `POST /api/v1/analytics/qoe`
  - Payload: `{ sessionId: string, mediaId: string, platform: string, eventType: string, startupTimeMs?: number, bufferDurationMs?: number, targetBitrateBps?: number, errorCode?: string }`
- `GET /api/v1/analytics/dashboard`
  - Response: `{ success: true, data: { totalEvents: number, averageStartupMs: number, totalBufferStalls: number, healthStatus: string } }`
