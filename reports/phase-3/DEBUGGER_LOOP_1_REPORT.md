PROJECT: Cross-Platform Streaming App
PHASE: Phase 3 — Android Phone & Tablet
LOOP: Loop 1 — Initial Verification
DEBUGGER: Agent 14 — Debugger Agent

DEFECT: DEF-P3-01 (Player overlay controls tap behavior lacks dedicated reveal gate)
REPRODUCED: YES
ROOT CAUSE:
- In `client/lib/widgets/video_player_view.dart`, `GestureDetector.onTap` toggles `_showControls = !_showControls`. If controls are currently hidden, tapping anywhere on the canvas reveals them, but if user double-taps or taps near actionable zones, the toggle state flips rapidly. When controls are hidden, any touch gesture should set `_showControls = true` and reset the timer without toggling off.
AFFECTED COMPONENT:
- client/lib/widgets/video_player_view.dart
SEVERITY:
- Major
RECOMMENDED FIX:
- Update canvas tap: if `!_showControls`, set `_showControls = true` and reset timer; only toggle off if user taps outside control zones while controls are already visible.
REGRESSION RISK:
- None.
READY FOR RETEST:
- YES (Pending developer update)

---

DEFECT: DEF-P3-02 (Missing DMCA Takedown guidance button in SettingsScreen)
REPRODUCED: YES
ROOT CAUSE:
- In `client/lib/screens/settings_screen.dart`, the legal statement informs the user about public domain content, but does not provide a button or modal dialog explaining how copyright holders can submit takedown notices to `/api/v1/legal/takedown`.
AFFECTED COMPONENT:
- client/lib/screens/settings_screen.dart
SEVERITY:
- Minor
RECOMMENDED FIX:
- Add a "Submit Copyright Inquiry / DMCA Notice" outlined button under the Legal section in `SettingsScreen` that opens an informational dialog with the designated agent contact and API guidance.
REGRESSION RISK:
- None.
READY FOR RETEST:
- YES (Pending developer update)
