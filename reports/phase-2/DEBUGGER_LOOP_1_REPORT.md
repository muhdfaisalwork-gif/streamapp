PROJECT: Cross-Platform Streaming App
PHASE: Phase 2 — Backend Core
LOOP: Loop 1 — Initial Verification
DEBUGGER: Agent 14 — Debugger Agent

DEFECT: DEF-P2-01 (Missing request body validation for mediaId on watchlist and bookmark routes)
REPRODUCED: YES
ROOT CAUSE:
- In `src/server.ts`, handlers for `/api/v1/watchlist/add` and `/api/v1/playback/bookmark` extract `body.mediaId` without asserting that `mediaId` is a non-empty string. If a malformed or empty client payload arrives, the database query receives an invalid key.
AFFECTED COMPONENT:
- backend/src/server.ts
SEVERITY:
- Major
RECOMMENDED FIX:
- In `src/server.ts`, validate that `body.mediaId` is present, of type string, and not empty. If invalid, immediately throw an Error: `Missing or invalid 'mediaId'`.
REGRESSION RISK:
- None; hardens endpoint boundary validation.
READY FOR RETEST:
- YES (Pending developer update)

---

DEFECT: DEF-P2-02 (Playback bookmark position not clamped to non-negative range)
REPRODUCED: YES
ROOT CAUSE:
- In `src/services/playback.service.ts` line 52 (`saveBookmark`), `positionSeconds` is stored as provided by client without asserting `Math.max(0, positionSeconds)` or ensuring `positionSeconds <= durationSeconds`.
AFFECTED COMPONENT:
- backend/src/services/playback.service.ts
SEVERITY:
- Minor
RECOMMENDED FIX:
- In `saveBookmark`, clamp `positionSeconds`:
  `const clampedPos = Math.max(0, Math.min(positionSeconds, durationSeconds > 0 ? durationSeconds : positionSeconds));`
REGRESSION RISK:
- None.
READY FOR RETEST:
- YES (Pending developer update)
