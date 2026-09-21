PROJECT: Cross-Platform Streaming App
PHASE: Phase 4 — Android TV
LOOP: Loop 2 — Regression Verification
DEBUGGER: Agent 14 — Debugger Agent

DEFECT: DEF-P4-03 (VideoPlayerView lacks hardware remote media key bindings for TV controllers)
REPRODUCED: YES
ROOT CAUSE:
- In `client/lib/widgets/video_player_view.dart`, `Scaffold` is wrapped with a `GestureDetector`, but lacks an overarching `Focus` widget configured with `autofocus: true` and an `onKeyEvent` handler. On Android TV devices without touchscreens, when OSD controls fade out after 3.5 seconds, pressing physical D-pad Left/Right or Play/Pause on the physical remote control is dropped by the window manager instead of driving player seeking or pausing.
AFFECTED COMPONENT:
- client/lib/widgets/video_player_view.dart
SEVERITY:
- Major
RECOMMENDED FIX:
- Wrap the playback scaffold in `Focus(autofocus: true, onKeyEvent: _handleRemoteKeyEvent, child: ...)`:
  - `LogicalKeyboardKey.select`, `enter`, `space`, `mediaPlayPause`, `mediaPlay`, `mediaPause` -> call `_togglePlayPause()`.
  - `LogicalKeyboardKey.arrowLeft`, `mediaRewind` -> call `_seekBy(-10)`.
  - `LogicalKeyboardKey.arrowRight`, `mediaFastForward` -> call `_seekBy(10)`.
  - `LogicalKeyboardKey.escape` -> call `widget.onBack()`.
REGRESSION RISK:
- None; simultaneously benefits Desktop keyboard navigation!
READY FOR RETEST:
- YES (Pending developer update)
