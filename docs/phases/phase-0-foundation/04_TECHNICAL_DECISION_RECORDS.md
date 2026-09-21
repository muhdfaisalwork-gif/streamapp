# PHASE 0 — DELIVERABLE 4: TECHNICAL DECISION RECORDS (TDRs / ADRs)

**Document Version**: 1.0.0  
**Phase**: Phase 0 (Foundation & Legal Scope)  
**Primary Owners**: Agent 6 — Backend Agent & Agent 7 — Streaming / Player Agent  
**Status**: Submitted for Verification  

---

## TDR-001: CROSS-PLATFORM CLIENT FRAMEWORK SELECTION

- **Status**: APPROVED
- **Context**: The product requires native-like performance, high-fidelity custom design systems, and responsive layout across 5 distinct target environments: Android Phones, Android Tablets, Android TV, Windows, and Linux.
- **Alternatives Evaluated**:
  1. *React Native*: Strong on mobile, but TV focus management and Linux desktop support are fragmented with third-party, out-of-tree maintainers.
  2. *Electron / Web*: High memory footprint, poor performance on low-end Android TV hardware (Amlogic Quad-Core with 1.5GB RAM).
  3. *Flutter (Dart 3)*: Single unified codebase, direct Skia/Impeller canvas rendering, first-class Android & Android TV support, native compilation on Windows and Linux, rich accessibility hooks.
- **Decision**: Adopt **Flutter** as the core cross-platform client technology.
- **Consequences**:
  - Positive: 90%+ code sharing across all 5 form factors; uniform 60fps animations; native compilation.
  - Negative: Requires careful handling of D-pad focus nodes on TV and platform-specific video texture plugins.

---

## TDR-002: BACKEND SERVICE ARCHITECTURE & RUNTIME

- **Status**: APPROVED
- **Context**: The backend must serve catalog discovery, metadata search, user auth/sessions, watchlist synchronization, stream health monitoring, and analytics. It must be lightweight, fast, easy to test, and deployable via Docker or bare-metal.
- **Alternatives Evaluated**:
  1. *Spring Boot (Java)*: High memory overhead, slower cold starts.
  2. *Go (Golang)*: Extremely fast, but slower developer velocity for complex schema validation and rapid prototyping.
  3. *Node.js with TypeScript (Fastify / Express)*: High throughput (event-driven asynchronous I/O), end-to-end type safety, vast ecosystem for video stream inspection (FFprobe / HLS parsing), low idle memory footprint (<80MB).
- **Decision**: Adopt **Node.js (v22 LTS) with TypeScript** structured as a **Modular Monolith**.
- **Module Decomposition**:
  - `auth`: JWT issuance, password hashing (Argon2id), session refresh.
  - `catalog`: Categories, hero carousels, titles, tags, and pagination.
  - `playback`: Stream URL resolution, multi-bitrate manifest proxying, legal verification checks.
  - `watchlist`: Continue watching bookmarks and user saved titles.
  - `search`: Debounced search engine with fuzzy matching and indexing.
  - `health`: Background scheduler verifying external stream endpoints every 15m.
- **Data Persistence**:
  - Portable SQLite via Knex/Kysely with foreign key constraints, WAL mode (Write-Ahead Logging), and automated migrations.
  - Architected for drop-in migration to PostgreSQL for distributed cloud deployments.
- **Canonical Data Contracts (Core Schemas)**:
  ```typescript
  export interface LicenseAttribution {
    licenseType: 'Public Domain' | 'CC-BY-3.0' | 'CC-BY-4.0' | 'CC-BY-SA-4.0' | 'CC0';
    creator: string;
    sourceUrl: string;
    licenseUrl: string;
    verificationDate: string; // ISO 8601
  }

  export interface SubtitleTrack {
    id: string;
    language: string; // ISO 639-1 ('en', 'es', 'fr', etc.)
    label: string;
    src: string; // WebVTT URL
    isDefault: boolean;
  }

  export interface StreamSource {
    id: string;
    format: 'hls' | 'dash' | 'mp4';
    url: string;
    backupUrl?: string;
    resolution: '4K' | '1080p' | '720p' | '480p' | 'auto';
    bitrateBps?: number;
    fps?: number;
  }

  export interface MediaItem {
    id: string;
    title: string;
    slug: string;
    description: string;
    releaseYear: number;
    durationSeconds: number;
    genres: string[];
    posterUrl: string;
    backdropUrl: string;
    rating: string;
    attribution: LicenseAttribution;
    sources: StreamSource[];
    subtitles: SubtitleTrack[];
    isFeatured: boolean;
    createdAt: string;
    updatedAt: string;
  }
  ```

---

## TDR-003: VIDEO PLAYER ENGINE & STREAMING PROTOCOL

- **Status**: APPROVED
- **Context**: Seamless playback of high-resolution video (1080p, 4K) across mobile, TV, and desktop devices with adaptive bitrate (ABR) switching, audio track selection, and subtitle rendering.
- **Protocols Supported**:
  1. **HLS (HTTP Live Streaming / RFC 8216)**: Primary streaming protocol. Adaptive multi-bitrate manifests (`.m3u8`) with TS or fMP4 segments.
  2. **DASH (Dynamic Adaptive Streaming over HTTP / ISO/IEC 23009-1)**: Supported for multi-period content.
  3. **Progressive MP4**: Direct fallback stream for legacy or high-speed direct downloads.
- **Player Implementations by Platform**:
  - **Android & Android TV**: Google Media3 / ExoPlayer. Provides hardware decoding via MediaCodec, smooth ABR switching algorithms (DefaultTrackSelector), and D-pad media control integration.
  - **Windows & Linux**: `media_kit` (backed by libmpv) and Flutter's official `video_player` platform channels. Direct hardware acceleration via DXVA2/D3D11VA (Windows) and VA-API (Linux).
- **Adaptive Bitrate Strategy**:
  - Initial segment starts at medium resolution (720p or 480p) to ensure sub-second Time-To-First-Frame (TTFF).
  - Bandwidth estimation continuously adjusts up to 1080p/4K based on download throughput and frame drop rate.
- **Player Resilience & Fallback State Machine**:
  ```text
  [Active Playback]
          ↓ (Encounter fatal segment error, HTTP 4xx/5xx, or stall > 8s)
  [Primary Retry Phase]
          ↓ (Attempt 2 retries with exponential backoff: 1s, 2s)
     Successful? ──► YES ──► [Resume Playback]
          │ NO
          ▼
  [Fallback Source Switch]
          ↓ (Check if `backupUrl` exists in active StreamSource)
     Exists? ─────► YES ──► [Mount backupUrl at current timestamp currentTimeMs]
          │ NO
          ▼
  [Graceful Error State]
          ↓ (Render non-blocking overlay: friendly error message, Retry button, Report Stream button)
  ```
  - Playback position bookmark (`currentTimeMs`) is preserved in local cache prior to fallback switch to eliminate user progress loss.

---

## TDR-004: STATE MANAGEMENT & OFFLINE-FIRST CACHE

- **Status**: APPROVED
- **Context**: State management must support reactive UI updates, synchronized continue-watching bookmarks, and seamless transition between Guest and Authenticated modes.
- **Decision**:
  - **Frontend State**: Riverpod (`flutter_riverpod` or structured BLoC) for compile-time safe, testable dependency injection and state management.
  - **Local Persistence**: SQLite (`sqflite` / `sqlite3`) combined with encrypted key-value storage (`flutter_secure_storage`) for tokens.
  - **Guest Mode State Machine**:
    - Unauthenticated guest actions (watchlist, playback progress) save to local SQLite.
    - Upon user authentication, a sync worker pushes local changes to the remote `/api/v1/user/sync` endpoint, merging lists deterministically without data loss.

---

## TDR-005: SECURITY, AUTHENTICATION & DEFENSE-IN-DEPTH

- **Status**: APPROVED
- **Context**: Protection of API endpoints, user credentials, prevention of stream hotlinking abuse, and strict isolation against unauthorized content.
- **Architecture**:
  - Passwords hashed using Argon2id with salt.
  - Access tokens: Short-lived HMAC-SHA256 JWTs (15 minutes).
  - Refresh tokens: Long-lived opaque cryptographically random tokens (30 days) stored with device fingerprinting and automatic reuse detection revocation.
  - Rate Limiting: 100 requests / min for general API; 5 requests / min for `/auth/login` to thwart brute force attacks.
  - Strict Content Security: Stream URLs must pass through the domain whitelist before dispatch.

---

## TDR-006: PRIVACY-FIRST TELEMETRY & QUALITY OF EXPERIENCE (QoE)

- **Status**: APPROVED
- **Context**: Measure player health, stream buffering ratios, and application stability without collecting user personal information.
- **Decision**:
  - Minimal QoE metrics: `startup_time_ms`, `buffer_count`, `buffer_duration_ms`, `bitrate_switches`, `playback_error_code`.
  - Zero PII (Personally Identifiable Information): IP addresses are masked to country/city level; device IDs are pseudo-anonymously generated and rotatable by user in Settings.
  - Global user toggle: "Send anonymous diagnostic & playback performance reports" (Enabled by default, can be toggled off at any time).
