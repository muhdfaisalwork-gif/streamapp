# PHASE 1 — DELIVERABLE 3: COMPONENT LIBRARY SPECIFICATIONS

**Document Version**: 1.0.0  
**Phase**: Phase 1 (UX & Design System)  
**Primary Owners**: Agent 2 — UI/UX Design Agent & Agent 3 — Frontend / Flutter Agent  
**Status**: Submitted for Verification  

---

## 1. COMPONENT ARCHITECTURE & STATE MODEL

Every component is defined with five standard interaction states:
1. **Default (Resting)**: Base theme styling.
2. **Hover (Desktop)**: Pointer proximity feedback (subtle elevation increase + border highlight).
3. **Focused (TV D-Pad & Keyboard)**: Unmistakable focus ring, 1.08x scale, high-contrast cyan border, drop glow.
4. **Active (Pressed)**: Visual compression feedback (0.96x scale).
5. **Disabled**: 40% opacity, non-interactive pointer events.

---

## 2. CORE COMPONENTS SPECIFICATION

### CMP-01: HeroBanner
- **Purpose**: Showcases featured public-domain or open-creator spotlight title.
- **Dimensions**:
  - TV / Desktop: 60vh height, full container width, 16:9 ratio backdrop.
  - Mobile: 45vh height, full viewport width.
- **Elements**:
  - High-resolution backdrop image with multi-stage linear gradient overlay (fading to `#0B0F19` at bottom and left).
  - Title typography (`font-display-hero`).
  - Metadata badges row: Release Year, Duration, Content Rating, Legal Badge ("Creative Commons" / "Public Domain").
  - Description synopsis (clamped to 3 lines on mobile, 4 lines on desktop/TV).
  - Primary Action Button: "Play Now" (`color-brand-primary` background, dark text, play icon).
  - Secondary Action Button: "+ Watchlist" (Translucent dark surface, white border, bookmark icon).
  - Tertiary Action Button: "More Info" (Opens detail dialog).

---

### CMP-02: MediaCard
- **Purpose**: Standard interactive card for catalog media representations in rows and grids.
- **Aspect Ratios Supported**:
  - Landscape (`16:9`): Standard for modern streams, episodes, and trailers (`280x158dp` on Desktop/TV; `180x101dp` on Mobile).
  - Portrait Poster (`2:3`): Classic cinema catalog representation (`160x240dp` on Desktop/TV; `120x180dp` on Mobile).
- **Sub-elements**:
  - Cached network image with smooth shimmer placeholder (animated gradient `#111827` to `#1F2937`).
  - Graceful Error Fallback Layout: If network image fails to load or device is offline, renders `#1F2937` surface with subtle radial gradient, centered `Icons.movie_outlined` (32dp, `#6B7280`), and title text at bottom in `font-caption` (`#9CA3AF`) guaranteeing title legibility.
  - Top-Right Badge: Resolution indicator (`4K UHD`, `1080p HD`).
  - Bottom Progress Bar (for Continue Watching): Height 4dp, background `#374151`, fill `#00E5FF` representing percentage watched.
  - Hover / Focus Overlay: Displays title, year, and quick "Play" button.
- **TV Focus Styling**:
  - Border: `2.5dp solid #00E5FF`.
  - Transform: `scale(1.08)` with `Curves.easeOutCubic`.
  - Box Shadow: `0px 8px 24px rgba(0, 229, 255, 0.40)`.

---

### CMP-03: TrayCarousel (Horizontal Media Row)
- **Purpose**: Container for horizontal collections (e.g. "Trending Now", "Blender Open Movies", "Public Domain Classics", "Continue Watching").
- **Properties**:
  - Header: Section Title (`font-h2`) + Optional "See All" action.
  - Scroll Behavior: Smooth physical scrolling with momentum on touch; programmatic snap-to-card on TV D-pad navigation.
  - Boundary Behavior: Strictly clamped at index `0` and index `N-1`. Zero wrapping to next row.
  - Edge Masking: Left/Right 32dp gradient fade on desktop/mobile indicating overflow.

---

### CMP-04: VideoPlayerOverlay
- **Purpose**: On-screen display (OSD) controls for media playback.
- **Behavior**: Auto-dismisses after 3.5 seconds of user inactivity; re-appears on any touch, mouse movement, or remote keypress.
- **Header Bar (Top)**:
  - Back Navigation Button (`Icons.arrow_back` / `Esc` / TV `Back`).
  - Title & Subtitle/Episode metadata.
  - Audio & Subtitle Selector Button:
    - *Phone (<600dp)*: Launches `ModalBottomSheet` anchored to bottom viewport.
    - *TV / Desktop / Tablet (>=600dp)*: Launches right-anchored `SlideOverDrawer` (360dp width) with vertical radio list, maintaining video visibility and direct vertical D-pad navigation.
  - Quality Selector Button (Auto, 1080p, 720p, 480p).
- **Center Canvas**:
  - Large Play / Pause toggle with pulse animation.
  - Dual Seek Buttons (-10s / +10s).
- **Footer Bar (Bottom)**:
  - Elapsed Time Counter (`00:04:12`).
  - Custom Seekbar Scrubber:
    - Track: 4dp height (expands to 8dp on hover/focus).
    - Buffered Range: Translucent white bar (`rgba(255,255,255,0.4)`).
    - Played Range: Cyan bar (`#00E5FF`).
    - Scrubber Thumb: 16dp circular draggable thumb with glow.
  - Remaining Time Counter (`-00:10:48`).
  - Volume Slider with Mute Toggle (Desktop/Tablet).
  - Fullscreen Toggle Button.

---

### CMP-05: Adaptive Navigation Framework
- **Phone (Width < 600dp)**: `BottomNavigationBar` (Home, Search, Watchlist, Settings).
- **Tablet / Desktop (Width >= 600dp)**: Compact or Extended `NavigationRail` pinned to the left edge, maximizing vertical viewing area.
- **Android TV**: Left-side expandable `TvNavigationDrawer` that expands from icon-only (64dp) to icon+label (240dp) when focused, collapsing automatically when focus enters the content grid.

---

### CMP-06: LegalAttributionBadge
- **Purpose**: Displays the license provenance and copyright status of the media item.
- **Attributes**:
  - Pill chip format (`radius-full`, border `1dp solid #6366F1`, background `rgba(99, 102, 241, 0.15)`).
  - Label: e.g. "License: CC-BY 3.0 (Blender Foundation)" or "Public Domain (Pre-1929 Classic)".
  - Click action: Launches browser to the official license declaration or source repository.
