# PHASE 0 — DELIVERABLE 5: MASTER RISK REGISTER & MITIGATION STRATEGY

**Document Version**: 1.0.0  
**Phase**: Phase 0 (Foundation & Legal Scope)  
**Primary Owners**: Agent 9 — Security Agent & Project Manager (PM)  
**Status**: Submitted for Verification  

---

## 1. RISK ASSESSMENT METHODOLOGY

Risks are evaluated using a standard 5x5 Likelihood and Impact matrix:
- **Likelihood (L)**: 1 (Rare) to 5 (Almost Certain)
- **Impact (I)**: 1 (Insignificant) to 5 (Catastrophic)
- **Risk Score**: $L \times I$ (1-6: Low, 7-14: Medium, 15-25: High / Critical)

---

## 2. MASTER RISK REGISTER

| Risk ID | Category | Description | L | I | Score | Mitigation Strategy | Contingency Plan | Owner |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **RSK-01** | Legal / Content | Ingestion of unauthorized or disputed copyrighted media. | 1 | 5 | 5 (Med) | Whitelist-only source adapters; mandatory legal license attestation; automated DMCA instant takedown engine. | Immediate quarantine of title within <60s; permanent audit log. | Agent 11 (Data) & Agent 9 (Sec) |
| **RSK-02** | Streaming | External legal CDN link rot or sudden manifest 404. | 4 | 3 | 12 (Med) | Automated background health checker every 15m; secondary backup mirror URLs for each catalog title. | Automatic fallback to secondary mirror; graceful error message to user if all mirrors fail. | Agent 7 (Player) & Agent 6 (Backend) |
| **RSK-03** | Android TV | Focus trapping or lost focus node during D-pad navigation. | 3 | 4 | 12 (Med) | Dedicated TV Focus Engine with boundary traps, spatial navigation tree, and visual focus glow assertions in automated tests. | Global TV focus recovery listener resets focus to first active row if focus lost. | Agent 4 (Android TV) & Agent 10 (A11y) |
| **RSK-04** | Hardware / TV | Out-of-memory (OOM) crash on 1.5GB RAM Android TV devices. | 3 | 4 | 12 (Med) | Aggressive image memory caching limits (100MB cap); virtualized list rendering; automatic texture cleanup on player exit. | Low-memory callback (`onTrimMemory`) releases inactive poster textures. | Agent 4 (Android) & Agent 8 (DevOps) |
| **RSK-05** | Desktop | Video playback hardware decoding failures across Linux drivers. | 3 | 3 | 9 (Med) | `media_kit` libmpv binding with fallback chain: VA-API -> VDPAU -> Software OpenGL/CPU rendering. | Automatic fallback to software decoding if hardware initialization fails. | Agent 5 (Desktop) & Agent 7 (Player) |
| **RSK-06** | Security | Brute force credential stuffing against auth endpoints. | 3 | 3 | 9 (Med) | IP and account-level rate limiting (5 attempts / min); Argon2id password hashing; CAPTCHA on consecutive failures. | Temporary account lockout for 15 minutes; security email alert to user. | Agent 9 (Security) |
| **RSK-07** | Network / ABR | High buffering and stalls on fluctuating mobile cellular networks. | 4 | 3 | 12 (Med) | HLS multi-bitrate streams with low-bitrate start (480p); aggressive buffer pre-fetching (30s forward buffer). | Immediate step-down to lowest bitrate ladder upon first buffer stall event. | Agent 7 (Streaming) |
| **RSK-08** | Governance | Silently combining agent roles or skipping verification loops. | 2 | 5 | 10 (Med) | Rigid 3-loop verification protocol enforced by PM; automated reporting templates; binary PM sign-off gate. | Immediate phase rejection and rollback to development agent if loops skipped. | Project Manager (PM) |

---

## 3. RISK MONITORING & REVIEW CADENCE

1. **Weekly PM Risk Audit**: Review active mitigation effectiveness during each phase gate.
2. **Automated Alerts**: Real-time alerts configured for RSK-02 (source health failures > 5%) and RSK-06 (failed login rate > threshold).
3. **Phase Gate Risk Check**: No phase can be approved if any risk in the Critical/High quadrant has an unverified mitigation strategy.
