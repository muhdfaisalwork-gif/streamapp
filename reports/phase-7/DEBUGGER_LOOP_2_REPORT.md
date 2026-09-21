PROJECT: Cross-Platform Streaming App
PHASE: Phase 7 — Accessibility, Performance & Full QA
LOOP: Loop 2 — Regression Verification
DEBUGGER: Agent 14 — Debugger Agent

DEFECT: DEF-P7-02 (Playback error overlay lacks `Semantics(liveRegion: true)` status announcement, violating WCAG 2.1 AA 4.1.3)
REPRODUCED: YES
ROOT CAUSE:
- In `client/lib/widgets/video_player_view.dart`, line 273 renders the error overlay:
  `if (_hasError) Container(...)`
- The error container contains visual text and icons, but Flutter does not expose this dynamic UI transition as an assertive accessibility alert without explicit semantic live region tagging. Screen-readers require `Semantics(liveRegion: true)` so that the OS accessibility framework announces incoming error messages immediately without requiring the user to blindly search the screen.
AFFECTED COMPONENT:
- client/lib/widgets/video_player_view.dart
SEVERITY:
- Major
RECOMMENDED FIX:
- In `client/lib/widgets/video_player_view.dart`, wrap the `_hasError` overlay container in:
  `Semantics(liveRegion: true, label: 'Playback alert: ${_errorMessage ?? "Playback error encountered"}. Retry available.', child: ...)`
REGRESSION RISK:
- None.
READY FOR RETEST:
- YES (Pending developer update)
