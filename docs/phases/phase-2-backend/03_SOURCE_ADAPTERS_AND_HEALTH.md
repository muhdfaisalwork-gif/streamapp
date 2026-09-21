# PHASE 2 — DELIVERABLE 3: SOURCE ADAPTERS & HEALTH MONITORING

**Document Version**: 1.0.0  
**Phase**: Phase 2 (Backend Core)  
**Primary Owners**: Agent 11 — Data / Content Agent & Agent 7 — Streaming / Player Agent  
**Status**: Submitted for Verification  

---

## 1. LEGAL SOURCE ADAPTER SPECIFICATIONS

All catalog streams are ingested exclusively through legal origin adapters:
1. **Blender Studio Open Movie Adapter**: Direct multi-bitrate HLS and MP4 mirrors for Sintel, Tears of Steel, Big Buck Bunny, Cosmos Laundromat.
2. **Internet Archive Public Domain Cinema Adapter**: MP4 progressive streams for Night of the Living Dead, Metropolis, Buster Keaton.
3. **NASA Deep Space Media Adapter**: NASA JPL mission archives and rover footage.

Every ingested item must possess:
- Verified legal license tag (`CC-BY-3.0`, `CC-BY-4.0`, `Public Domain`, `CC0`).
- Immutable attribution link to original author or foundation repository.
- Secondary fallback mirror (`backupUrl`) to ensure uninterrupted user playback.

---

## 2. STREAM HEALTH MONITORING ENGINE

The `HealthService` executes periodic automated probes:
- Sends HTTP HEAD/GET range requests to check availability and latency.
- If primary stream URL fails or returns 5xx/404, automatically updates item status to `degraded`.
- When client requests `/api/v1/playback/resolve/:id`, the API returns both primary source and verified `fallbackSource`.
