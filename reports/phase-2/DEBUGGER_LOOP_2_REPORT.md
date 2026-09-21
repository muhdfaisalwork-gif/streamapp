PROJECT: Cross-Platform Streaming App
PHASE: Phase 2 — Backend Core
LOOP: Loop 2 — Regression Verification
DEBUGGER: Agent 14 — Debugger Agent

DEFECT: DEF-P2-03 (Stream resolution endpoint returns HTTP 400 instead of HTTP 404 for missing media)
REPRODUCED: YES
ROOT CAUSE:
- In `src/server.ts` line 167:
  ```typescript
  if (pathname.startsWith('/api/v1/playback/resolve/') && method === 'GET') {
    const id = pathname.replace('/api/v1/playback/resolve/', '');
    const format = (parsedUrl.searchParams.get('format') || 'hls') as any;
    const result = this.playbackService.resolveStream(id, format);
    return this.sendJson(res, 200, { success: true, data: result });
  }
  ```
  `playbackService.resolveStream` throws an `Error('Media not found: ...')` when the media is missing. Because there is no explicit check or caught error mapping, the outer catch block catches the error and defaults to `sendJson(res, 400, ...)`. Semantic REST guidelines dictate HTTP 404 for missing resources.
AFFECTED COMPONENT:
- backend/src/server.ts
SEVERITY:
- Minor
RECOMMENDED FIX:
- Check if `this.catalogService.getItemById(id)` exists, or catch the not-found error and return `sendJson(res, 404, { success: false, error: 'Media not found' })`.
REGRESSION RISK:
- None.
READY FOR RETEST:
- YES (Pending developer update)
