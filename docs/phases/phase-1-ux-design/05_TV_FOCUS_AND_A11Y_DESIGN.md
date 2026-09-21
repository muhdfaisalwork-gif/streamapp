# PHASE 1 — DELIVERABLE 5: ANDROID TV FOCUS ENGINE & ACCESSIBILITY SPECIFICATIONS

**Document Version**: 1.0.0  
**Phase**: Phase 1 (UX & Design System)  
**Primary Owners**: Agent 2 — UI/UX Design Agent, Agent 4 — Android / TV Agent, Agent 10 — Accessibility Agent  
**Status**: Submitted for Verification  

---

## 1. ANDROID TV SPATIAL NAVIGATION & FOCUS ENGINE

The Android TV experience is governed by a deterministic **Spatial Focus Engine** built to eradicate focus traps, phantom selections, and accidental navigation off-screen.

### Spatial Navigation Tree
```text
                  [TV Navigation Drawer (Collapsible)]
                                  ↕ (Left / Right)
                             [Hero Banner]
                                  ↕ (Down / Up)
                       [Tray 1: Continue Watching]
                        [Card 0] ↔ [Card 1] ↔ [Card 2] (Clamped)
                                  ↕ (Down / Up)
                       [Tray 2: Blender Open Movies]
                        [Card 0] ↔ [Card 1] ↔ [Card 2] (Clamped)
                                  ↕ (Down / Up)
                       [Tray 3: Public Domain Classics]
                        [Card 0] ↔ [Card 1] ↔ [Card 2] (Clamped)
```

---

## 2. DETERMINISTIC FOCUS RULES & BOUNDARY CLAMPING

1. **Horizontal Row Clamping**:
   - When focus resides on `Card[0]` (leftmost item) and user presses `DPAD_LEFT`, the focus remains locked on `Card[0]`. If navigation drawer is available, `DPAD_LEFT` opens the navigation drawer.
   - When focus resides on `Card[N-1]` (rightmost item) and user presses `DPAD_RIGHT`, the focus stays locked on `Card[N-1]` with a subtle elastic bump animation. It **never** wraps to the next row.
2. **Vertical Inter-Row Traversal**:
   - Pressing `DPAD_DOWN` moves focus from the current card directly to the geographically closest card in the row below.
   - The scroll container automatically scrolls vertically to keep the active row centered at 40% from the top of the viewport.
3. **Focus Restoration on Back Navigation**:
   - When a user opens a Title Detail Modal or enters the Video Player, the ID of the origin card node is pushed to the `FocusHistoryStack`.
   - Upon pressing `KEYCODE_BACK` to return to the catalog, the application restores focus precisely to the originating card node rather than resetting to the top of the screen.

---

## 3. TV FOCUS VISUAL INDICATORS

To guarantee clear visibility across low-cost LCD panels and bright living rooms:
- **Outline**: `2.5dp` solid neon cyan (`#00E5FF`).
- **Scale Transformation**: `scale(1.08)` applied with `Curves.easeOutCubic` over `180ms`.
- **Drop Glow**: Elevation shadow with radius `16dp`, color `rgba(0, 229, 255, 0.40)`.
- **Z-Index Layering**: The focused card automatically elevates its z-index above adjacent sibling cards to avoid being clipped by neighboring posters.

---

## 4. ACCESSIBILITY (A11Y) SPECIFICATIONS

### A. Screen Reader & TalkBack Semantics
- Every interactive element (MediaCard, PlayButton, DrawerItem) is wrapped with Flutter's `Semantics` node:
  - `label`: Full title, release year, duration, and legal status (e.g. "Sintel, 2010, 15 minutes, Creative Commons Attribution 3.0, button").
  - `hint`: "Double tap to view details or play".
  - `value`: Completion progress (e.g. "65 percent watched").

### B. High Contrast Theme Mode
- User can toggle "High Contrast Mode" in Settings:
  - Replaces `#111827` surface with pure black `#000000`.
  - Replaces cyan focus border with high-visibility pure yellow `#FFE500` (Contrast ratio **19.5:1** against black).
  - All text badges rendered with solid background fills rather than semi-transparent pills.

### C. Dynamic Font Scaling & Text Reflow
- Supports system font scaling up to **200%**:
  - All labels use auto-wrapping or responsive expansion rather than fixed height containers.
  - Text truncation with ellipsis is prohibited on actionable buttons and titles.

### D. Subtitle Customization Engine
- Complies with FCC Closed Captioning & Section 508 standards:
  - Font Size: Small (14sp), Medium (18sp, Default), Large (24sp), Extra-Large (32sp).
  - Font Color: White, Yellow, Cyan, Green.
  - Background Opacity: 0% (None), 50% (Semi-transparent black), 100% (Solid black).
  - Window Edge Style: Raised, Depressed, Uniform Drop Shadow.
