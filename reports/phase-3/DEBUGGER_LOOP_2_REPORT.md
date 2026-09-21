PROJECT: Cross-Platform Streaming App
PHASE: Phase 3 — Android Phone & Tablet
LOOP: Loop 2 — Regression Verification
DEBUGGER: Agent 14 — Debugger Agent

DEFECT: DEF-P3-03 (MediaDetailsScreen play button lacks dynamic "Resume" label when bookmark exists)
REPRODUCED: YES
ROOT CAUSE:
- In `client/lib/screens/media_details_screen.dart`, the CTA button is hardcoded to `label: const Text('Play Fullscreen', ...)`. `MediaDetailsScreen` does not accept a `resumePositionSeconds` parameter, preventing the button from displaying "Resume (04:12)" when a bookmark is stored.
AFFECTED COMPONENT:
- client/lib/screens/media_details_screen.dart & client/lib/main.dart
SEVERITY:
- Minor
RECOMMENDED FIX:
- Pass `resumePositionSeconds` (or `progressPercentage`) to `MediaDetailsScreen` and format the play button label dynamically:
  `final playLabel = (resumeSeconds != null && resumeSeconds > 10) ? 'Resume (${formatTime(resumeSeconds)})' : 'Play Fullscreen';`
REGRESSION RISK:
- None.
READY FOR RETEST:
- YES (Pending developer update)
