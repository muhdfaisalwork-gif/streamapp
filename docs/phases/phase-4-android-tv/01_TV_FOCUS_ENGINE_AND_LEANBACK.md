# PHASE 4 — DELIVERABLE 1: ANDROID TV FOCUS ENGINE & LEANBACK ARCHITECTURE

**Document Version**: 1.0.0  
**Phase**: Phase 4 (Android TV)  
**Primary Owners**: Agent 4 — Android / TV Agent & Agent 10 — Accessibility Agent  
**Status**: Submitted for Verification  

---

## 1. 10-FOOT LEANBACK DESIGN ARCHITECTURE

Android TV demands a dedicated interaction paradigm free of touch or mouse assumptions:
1. **Overscan Margins**: Minimum 48dp margins on left/right and 24dp on top/bottom to prevent clipping on television edge bezels.
2. **Expandable TV Navigation Drawer**:
   - Resting State: 72dp collapsed icon rail.
   - Expanded State: Expands smoothly to 220dp width when focus transitions to the navigation scope via `DPAD_LEFT`.
   - Auto-Collapse: Automatically shrinks back to 72dp when focus enters any content tray.
3. **Spatial Focus Engine**:
   - `TvFocusableCard`: Encapsulates cards in a dedicated `FocusNode` responding to `LogicalKeyboardKey.select`, `enter`, and `space`.
   - Visual Focus Ring: `2.5dp solid #00E5FF` (cyan glow with 20dp blur radius) and `scale(1.08)` transform.
   - Z-index Elevation: Elevates focused cards above siblings, eliminating edge-clipping.
4. **Focus History Restoration (`TvFocusNodeHistory`)**:
   - When a user selects a card to enter Title Details or Video Player, the card's ID is saved on `_historyStack`.
   - When pressing `KEYCODE_BACK` to return to the catalog, the system restores focus to that exact card node instead of resetting to the top.
5. **Horizontal Boundary Clamping**:
   - Prevents focus from wrapping around within a carousel or jumping unintended rows upon reaching the edge.
