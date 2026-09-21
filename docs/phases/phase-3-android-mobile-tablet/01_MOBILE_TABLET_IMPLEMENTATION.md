# PHASE 3 — DELIVERABLE 1: ANDROID PHONE & TABLET IMPLEMENTATION ARCHITECTURE

**Document Version**: 1.0.0  
**Phase**: Phase 3 (Android Phone & Tablet)  
**Primary Owners**: Agent 3 — Frontend / Flutter Agent & Agent 4 — Android Agent  
**Status**: Submitted for Verification  

---

## 1. CODEBASE STRUCTURE & ARCHITECTURE

The Flutter client (`g:/streaming app/client/lib/`) implements a unified, reactive architecture:
- `theme/app_theme.dart`: Midnight Dark and High Contrast themes.
- `models/models.dart`: Strongly typed client models (`MediaItem`, `StreamSource`, `SubtitleTrack`, `Bookmark`, `User`).
- `services/api_service.dart`: REST API consumer with local offline fallback.
- `widgets/`:
  - `hero_banner.dart`: Responsive hero banner with multi-stage gradient scrim (CMP-01).
  - `media_card.dart`: 16:9 and 2:3 cards, hover/focus states, continue watching progress bar, and resilient fallback container (CMP-02).
  - `tray_carousel.dart`: Horizontal collection rows (CMP-03).
  - `video_player_view.dart`: Video surface, custom seekbar scrubber, responsive track selector (`ModalBottomSheet` on phone vs `SlideOverDrawer` on tablet/desktop), and stream fallback recovery (CMP-04).
  - `responsive_layout.dart`: Breakpoint router (Compact <600dp, Medium 600-1024dp, Expanded >1024dp).
- `screens/`:
  - `home_screen.dart`: Home discovery feed with Hero, Continue Watching, and Category Trays.
  - `search_screen.dart`: Instant debounced search with genre filters.
  - `media_details_screen.dart`: Title synopsis, legal attribution pill, technical stream specs.
  - `watchlist_screen.dart`: Bookmarked titles grid.
  - `settings_screen.dart`: High Contrast toggle, Telemetry opt-out, legal statement.

---

## 2. FORM FACTOR RESPONSIVENESS

1. **Android Smartphone (Compact < 600dp)**:
   - Navigation: Bottom navigation bar (`BottomNavigationBar`) optimized for one-handed thumb reach.
   - Layout: Portrait single-column feed with horizontal trays; landscape auto-fullscreen player.
   - Track Selector: Bottom sheet (`ModalBottomSheet`).
2. **Android Tablet (Medium 600dp - 1024dp)**:
   - Navigation: Left-pinned `NavigationRail` maximizing vertical screen estate.
   - Layout: 3-4 column grid, horizontal trays with expanded visible cards.
   - Track Selector: Right-side `SlideOverDrawer` (360dp width) preserving video visibility.
