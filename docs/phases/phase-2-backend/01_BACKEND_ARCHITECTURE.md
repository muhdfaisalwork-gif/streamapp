# PHASE 2 — DELIVERABLE 1: BACKEND CORE ARCHITECTURE & SERVICES

**Document Version**: 1.0.0  
**Phase**: Phase 2 (Backend Core)  
**Primary Owners**: Agent 6 — Backend Agent & Agent 8 — DevOps Agent  
**Status**: Submitted for Verification  

---

## 1. ARCHITECTURAL TOPOLOGY

The backend core is structured as a high-throughput, zero-external-dependency **Modular Monolith** running natively on Node.js v22 LTS:

```text
                               +-----------------------------+
                               |     Client Applications     |
                               | (Mobile, TV, Desktop, Web)  |
                               +--------------+--------------+
                                              | HTTPS / JSON
                                              ▼
                               +-----------------------------+
                               |   Streaming HTTP Server     |
                               |   (CORS, Auth, Router)      |
                               +--------------+--------------+
                                              |
        +------------------+------------------+------------------+------------------+
        |                  |                  |                  |                  |
        ▼                  ▼                  ▼                  ▼                  ▼
+---------------+  +---------------+  +---------------+  +---------------+  +---------------+
|  Auth Service |  |Catalog Service|  |Playback Service| |Watchlist Svc  |  | Health & DMCA |
+---------------+  +---------------+  +---------------+  +---------------+  +---------------+
        |                  |                  |                  |                  |
        +------------------+------------------+------------------+------------------+
                                              |
                                              ▼
                               +-----------------------------+
                               |   Embedded SQLite (WAL)     |
                               |   `streaming_app.db`        |
                               +-----------------------------+
```

---

## 2. MODULAR SERVICE CATALOG

1. **`AuthService`** (`src/services/auth.service.ts`):
   - User registration and login.
   - Salted `scryptSync` password hashing (64-byte key).
   - HMAC-SHA256 JWT generation with 24-hour expiration.
   - Deterministic guest data reconciliation (`syncGuestData`).

2. **`CatalogService`** (`src/services/catalog.service.ts`):
   - Computes Home feed with featured Hero carousel items and category-grouped media trays.
   - Media details retrieval with rich license attributions and multi-bitrate sources.
   - Genre aggregation.

3. **`PlaybackService`** (`src/services/playback.service.ts`):
   - Resolves stream manifests (`hls`, `dash`, `mp4`) with automatic fallback mapping (`backupUrl`).
   - Millisecond-level playback bookmark persistence.
   - Continue Watching collection aggregation (filters completed >95% or <10s).

4. **`WatchlistService`** (`src/services/watchlist.service.ts`):
   - Manages user-specific and guest-specific watchlists.

5. **`SearchService`** (`src/services/search.service.ts`):
   - Multi-criteria fuzzy search over title, synopsis, creator, genres, and release year.

6. **`HealthService`** (`src/services/health.service.ts`):
   - Automated HTTP HEAD/GET stream reachability prober.
   - Automatic `status: degraded` transition on primary CDN failure.

7. **`LegalService`** (`src/services/legal.service.ts`):
   - DMCA takedown intake with mandatory good-faith attestation.
   - Automated instant quarantine (<60s SLA) removing disputed items from public feeds and playback.
   - Immutable audit logging.

8. **`AnalyticsService`** (`src/services/analytics.service.ts`):
   - Privacy-preserving QoE telemetry collection (startup latency, buffer stalls, bitrate shifts).
   - Dashboard summary metrics.

---

## 3. DATABASE SCHEMA & PERSISTENCE ENGINE

The database runs on embedded `node:sqlite` in Write-Ahead Logging (`WAL`) mode with foreign key enforcement:
- `users`: User credentials, roles, and profiles.
- `media_items`: Master catalog records with serialized JSON attributes for sources, subtitles, and legal attribution.
- `bookmarks`: User continue-watching positions and completion percentages.
- `watchlist`: Saved user titles.
- `dmca_notices`: Legal takedown filings with claimant credentials and status.
- `qoe_events`: Anonymous playback telemetry events.
