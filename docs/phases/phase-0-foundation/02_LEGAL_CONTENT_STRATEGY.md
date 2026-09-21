# PHASE 0 — DELIVERABLE 2: LEGAL CONTENT STRATEGY & SOURCE ADAPTER FRAMEWORK

**Document Version**: 1.0.0  
**Phase**: Phase 0 (Foundation & Legal Scope)  
**Primary Owners**: Agent 11 — Data / Content Agent & Agent 9 — Security Agent  
**Status**: Submitted for Verification  

---

## 1. LEGAL COMPLIANCE CHARTER & CORE POLICY

The application is explicitly architected and maintained as a **100% legal, open-access streaming platform**. 

### The Golden Rule of Content
> **Under no circumstances shall unauthorized copyrighted, pirated, scraped, or illicit commercial stream sources be integrated, indexed, proxied, cached, or surfaced by this platform.**

Every item in the catalog must possess an immutable legal pedigree originating from one of five permitted categories:
1. **Public Domain**: Works whose copyright term has expired or which have been dedicated to the public domain globally (e.g., CC0, Pre-1929 works, government works).
2. **Creative Commons Open Licenses**: Works licensed under CC-BY, CC-BY-SA, or CC0 allowing non-commercial or commercial redistribution with attribution.
3. **Open Creator / Foundation Projects**: Official open-source creative initiatives (e.g., Blender Studio Open Movie projects).
4. **Official Institutional Media**: Scientific, educational, and governmental media archives (e.g., NASA, European Southern Observatory).
5. **User-Owned / Authorized Private Sources**: Self-hosted or user-provided local media libraries via explicit client configuration.

---

## 2. CONTENT SOURCE WHITELIST & SEED CATALOG

The initial MVP catalog is curated from verified, high-availability legal sources providing direct multi-bitrate HLS and MP4 streams:

### A. Blender Studio Open Movies (Creative Commons Attribution)
- **Titles**:
  - *Sintel* (Dur: 15m, 4K/1080p HLS + MP4, multi-language subtitles) — License: CC-BY 3.0
  - *Tears of Steel* (Dur: 12m, Sci-Fi VFX, 4K HLS + DASH) — License: CC-BY 3.0
  - *Big Buck Bunny* (Dur: 10m, Animation, 1080p 60fps ABR HLS) — License: CC-BY 3.0
  - *Cosmos Laundromat* (Dur: 12m, Stylized animation, HLS) — License: CC-BY 3.0
  - *Charge* (Dur: 3m, Next-gen real-time rendered action) — License: CC-BY 3.0
  - *Caminandes: Llama Drama & Gran Dillama* (Animation series) — License: CC-BY 3.0
- **Attributes**: Full metadata, posters, studio credits, lossless audio streams, WebVTT captions.

### B. Public Domain Cinema & Historical Archive (Archive.org Verified PD)
- **Titles**:
  - *Night of the Living Dead* (1968, George A. Romero) — Status: Public Domain (lack of copyright notice upon release).
  - *Metropolis* (1927, Fritz Lang) — Status: Public Domain worldwide.
  - *The General* (1926, Buster Keaton) — Status: Public Domain.
  - *The Kid* / *The Gold Rush* (Charlie Chaplin Public Domain collections).
  - *A Trip to the Moon* (1902, Georges Méliès).
- **Attributes**: Historical metadata, restored MP4 and HLS progressive manifests, archival posters.

### C. NASA & Scientific Media (Public Domain / US Government Works)
- **Titles**:
  - *Mars Perseverance: Seven Minutes of Terror & Landing* (Documentary 4K).
  - *Artemis: Humanity’s Return to the Moon* (HD/4K Series).
  - *Hubble & James Webb Deep Universe Ultra HD Tours*.
- **Attributes**: Scientifically accurate descriptions, multi-audio narration tracks, technical specifications.

---

## 3. SOURCE ADAPTER ARCHITECTURE

Content ingestion is isolated behind a strict **Source Adapter Interface**. Direct raw URLs are never entered into the database without passing through automated legal and health validation:

```text
External Legal Source (Blender / Archive / NASA)
                     ↓
         Source Adapter Worker
                     ↓
     1. Legal Attestation Verification (License Type Check)
     2. HTTPS & Domain Whitelist Check
     3. Stream Integrity Check (FFprobe / HLS Parser)
     4. Content Safety & CORS Availability Check
                     ↓
       Sanitized Catalog Database Record
```

### Ingestion Validation Pipeline:
1. **Domain Whitelisting**: Only approved origins (e.g., `commondatastorage.googleapis.com`, `archive.org`, `blender.org`, `nasa.gov`, `test-streams.mux.dev`) are permissible.
2. **License Metadata Check**: Every record must have `license_type`, `attribution_text`, and `license_url` populated.
3. **Codec and Container Validation**: Stream headers are probed with FFmpeg/FFprobe to verify valid H.264/H.265 video and AAC/Opus audio without DRM corruption.

---

## 4. SOURCE HEALTH MONITORING ENGINE

Public media CDNs can experience downtime or changed manifest links. The backend includes an automated **Health Monitor Service**:
- Runs every 15 minutes as a background scheduled task.
- Sends an HTTP `HEAD` / Range `GET` request to verify HTTP 200/206 status and latency < 1500ms.
- Automatically marks unhealthy streams as `status: degraded` or `status: offline` and switches to the registered fallback source URL.
- Triggers alert events in the system log if an entire title has no functional mirrors.

---

## 5. DMCA / COPYRIGHT TAKEDOWN & COMPLIANCE PROTOCOL

Although only legal sources are accepted, an enterprise-grade takedown process is mandatory for legal risk mitigation:

1. **Designated DMCA Agent & Intake Endpoint**:
   - Public endpoint: `GET /api/v1/legal/takedown` (Guidelines & Form)
   - API intake: `POST /api/v1/legal/takedown`
   - Dedicated intake mailbox: `legal@streaming-app.local`
2. **Automated Takedown SLA**:
   - Upon receiving a valid copyright dispute ticket, the disputed title ID is immediately moved to `status: suspended_pending_review`.
   - The title is instantly hidden from all user feeds, search indices, and playback endpoints within **< 60 seconds** via Redis/memory cache invalidation.
3. **Audit Log & Archival**:
   - Every takedown submission, investigation, resolution, or restoration is permanently logged in an append-only audit table.
