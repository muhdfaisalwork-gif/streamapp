PROJECT: Cross-Platform Streaming App
PHASE: Phase 0 — Foundation & Legal Scope
LOOP: Loop 2 — Regression Verification
DEBUGGER: Agent 14 — Debugger Agent

DEFECT: DEF-P0-03 (Player stream fallback state machine unformalized)
REPRODUCED: YES
ROOT CAUSE:
- In TDR-003 (04_TECHNICAL_DECISION_RECORDS.md) and 02_LEGAL_CONTENT_STRATEGY.md Section 4, the existence of `backupUrl` is established in the schema, but the runtime player transition logic is left implicit. If an external legal CDN suffers transient failure or segment 404, an unguided player implementation might freeze indefinitely or immediately crash to an error screen without attempting the available fallback stream source.
AFFECTED COMPONENT:
- docs/phases/phase-0-foundation/04_TECHNICAL_DECISION_RECORDS.md (TDR-003)
SEVERITY:
- Major
RECOMMENDED FIX:
- Formalize the exact Player Fallback State Machine within TDR-003:
  1. Detect playback error (HTTP 4xx/5xx, CORS violation, or stalled buffer > 8s).
  2. Attempt 2 automatic retries on current stream with exponential backoff (1s, 2s).
  3. If primary stream fails, switch player source to `backupUrl` preserving current playback position (`currentTimeMs`).
  4. If `backupUrl` also fails or does not exist, transition player to Graceful Error State displaying user-friendly error message, retry button, and "Report Issue" action.
REGRESSION RISK:
- None; clarifies and hardens player resilience specifications.
READY FOR RETEST:
- YES (Pending developer update)
