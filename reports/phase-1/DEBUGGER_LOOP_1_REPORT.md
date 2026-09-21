PROJECT: Cross-Platform Streaming App
PHASE: Phase 1 — UX & Design System
LOOP: Loop 1 — Initial Verification
DEBUGGER: Agent 14 — Debugger Agent

DEFECT: DEF-P1-01 (Underspecified responsive modal presentation for audio/subtitle track selector)
REPRODUCED: YES
ROOT CAUSE:
- In 03_COMPONENT_LIBRARY.md CMP-04, the track selector is designated as "opens modal sheet to select tracks". While BottomSheets are native on mobile smartphones, on Android TV and Desktop a bottom sheet disrupts full-screen video context and causes focus traps with D-pad navigation. A right-side slide-over panel allows the user to preview changes while keeping the video running and provides natural vertical D-pad navigation.
AFFECTED COMPONENT:
- docs/phases/phase-1-ux-design/03_COMPONENT_LIBRARY.md (CMP-04)
SEVERITY:
- Major
RECOMMENDED FIX:
- Explicitly define the responsive track selector presentation:
  - Phone (<600dp): `ModalBottomSheet` anchored to bottom viewport.
  - TV / Desktop / Tablet (>=600dp): Right-anchored `SlideOverDrawer` (360dp width) with vertical radio list maintaining immediate video visibility.
REGRESSION RISK:
- None; improves UX clarity for frontend developers.
READY FOR RETEST:
- YES (Pending developer update)

---

DEFECT: DEF-P1-02 (Missing formal token definition for color-focus-high-contrast)
REPRODUCED: YES
ROOT CAUSE:
- In 05_TV_FOCUS_AND_A11Y_DESIGN.md Section 4.B, `#FFE500` is referenced as the high contrast focus indicator, but was omitted from the master semantic tokens table in 02_DESIGN_TOKENS.md Section 1.
AFFECTED COMPONENT:
- docs/phases/phase-1-ux-design/02_DESIGN_TOKENS.md Section 1
SEVERITY:
- Minor
RECOMMENDED FIX:
- Add `color-focus-high-contrast` (`#FFE500`, RGB: `255, 229, 0`) to the Semantic Color Tokens table in 02_DESIGN_TOKENS.md.
REGRESSION RISK:
- None.
READY FOR RETEST:
- YES (Pending developer update)
