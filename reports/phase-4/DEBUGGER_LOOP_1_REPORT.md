PROJECT: Cross-Platform Streaming App
PHASE: Phase 4 — Android TV
LOOP: Loop 1 — Initial Verification
DEBUGGER: Agent 14 — Debugger Agent

DEFECT: DEF-P4-01 (Missing auto-centering scroll listener for vertical tray alignment during D-pad navigation)
REPRODUCED: YES
ROOT CAUSE:
- In `client/lib/tv/tv_home_screen.dart`, trays are rendered inside a `SingleChildScrollView(controller: _verticalScroll, ...)`. While individual cards inside each row manage their focus, the parent vertical scroll controller is not programmatically notified when a card in a lower row gains focus, relying on Flutter's default `Scrollable.ensureVisible` which only scrolls until the edge is just barely visible rather than centering the active tray in prime television sightlines.
AFFECTED COMPONENT:
- client/lib/tv/tv_home_screen.dart
SEVERITY:
- Major
RECOMMENDED FIX:
- In `TvHomeScreen`, wrap each tray in a callback `onFocusChanged: (focused) { if (focused) Scrollable.ensureVisible(context, alignment: 0.35, duration: Duration(milliseconds: 250)); }` ensuring active trays are smoothly centered at 35%-40% from top of the screen.
REGRESSION RISK:
- None.
READY FOR RETEST:
- YES (Pending developer update)

---

DEFECT: DEF-P4-02 (TvFocusableCard lacks RepaintBoundary for raster caching during D-pad repeat)
REPRODUCED: YES
ROOT CAUSE:
- In `client/lib/tv/tv_focus_engine.dart`, `AnimatedScale` and `AnimatedContainer` repaint their render objects and children on every animation tick. On lower-end Quad-Core Amlogic TV chipsets (1.5GB RAM), holding down a D-pad arrow causes layout repaints across all visible cards in the row.
AFFECTED COMPONENT:
- client/lib/tv/tv_focus_engine.dart
SEVERITY:
- Minor
RECOMMENDED FIX:
- Wrap `TvFocusableCard.child` inside a `RepaintBoundary` to isolate the card texture to its own GPU raster layer.
REGRESSION RISK:
- None.
READY FOR RETEST:
- YES (Pending developer update)
