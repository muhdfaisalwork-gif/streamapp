# PHASE 1 — DELIVERABLE 4: MULTI-PLATFORM RESPONSIVE LAYOUTS & WIREFRAMES

**Document Version**: 1.0.0  
**Phase**: Phase 1 (UX & Design System)  
**Primary Owners**: Agent 2 — UI/UX Design Agent, Agent 4 — Android / TV Agent, Agent 5 — Desktop Agent  
**Status**: Submitted for Verification  

---

## 1. RESPONSIVE BREAKPOINT SPECIFICATIONS

| Breakpoint Tier | Window Width ($w$) | Primary Target Devices | Navigation Architecture | Grid Columns |
| :--- | :--- | :--- | :--- | :--- |
| **Compact** | $w < 600\text{dp}$ | Android Smartphones (Portrait/Landscape) | `BottomNavigationBar` (4 tabs) | 2 columns (Poster), 1 column (Landscape) |
| **Medium** | $600\text{dp} \le w < 1024\text{dp}$ | Android Tablets, Foldables | Left `NavigationRail` (Icons only) | 3-4 columns (Poster), 2 columns (Landscape) |
| **Expanded** | $w \ge 1024\text{dp}$ | Windows & Linux Desktop | Left `NavigationRail` (Icons + Labels) | 5-6 columns (Poster), 3-4 columns (Landscape) |
| **TV Leanback** | Fixed $1920\times 1080$ / $3840\times 2160$ | Android TV / Google TV | Left Collapsible TV Drawer | Horizontal Carousels with Snap Focus |

---

## 2. WIREFRAMES & LAYOUT SCHEMATICS

### A. Android Smartphone Layout (Portrait)
```text
+-------------------------------------------------------+
|  [Logo: StreamApp]             [Search]  [User Avatar]| <- Top AppBar
+-------------------------------------------------------+
|                                                       |
|  +-------------------------------------------------+  |
|  | HERO BANNER                                     |  | <- 45vh Hero
|  | "SINTEL" (4K • 15m • CC-BY)                     |  |
|  | [▶ Play Now]    [+ Watchlist]                   |  |
|  +-------------------------------------------------+  |
|                                                       |
|  CONTINUE WATCHING                                    |
|  +-------------+  +-------------+  +-------------+    |
|  | Card 1 (65%)|  | Card 2 (20%)|  | Card 3 (90%)|    | <- Horizontal Tray
|  +-------------+  +-------------+  +-------------+    |
|                                                       |
|  BLENDER OPEN MOVIES                                  |
|  +-------------+  +-------------+  +-------------+    |
|  | Card A      |  | Card B      |  | Card C      |    |
|  +-------------+  +-------------+  +-------------+    |
|                                                       |
+-------------------------------------------------------+
|  [Home]       [Search]       [Watchlist]    [Settings]| <- BottomNavBar
+-------------------------------------------------------+
```

---

### B. Android Tablet Layout (Landscape Split-Pane)
```text
+----+------------------------------------------------------------------+
|    | [🔍 Search Movies, Series, Creators...]             [Guest / Profile]|
| N  +-----------------------------------+------------------------------+
| A  | FEATURED HERO                     | SELECTED TITLE DETAILS       |
| V  |                                   |                              |
|    | "Tears of Steel"                  | "Tears of Steel" (2012)      |
| R  | Sci-Fi • 12m • 4K • CC-BY         | In a dystopian future...     |
| A  | [▶ Play]  [+ Watchlist]           | Rating: PG • Dur: 12 mins    |
| I  +-----------------------------------+ License: CC-BY 3.0           |
| L  | TRENDING NOW (Horizontal Tray)    |                              |
|    | [Card 1]  [Card 2]  [Card 3]      | [▶ Play Fullscreen]          |
|    +-----------------------------------+ [⬇ Add to Watchlist]         |
|    | PUBLIC DOMAIN CINEMA (Tray)       |                              |
|    | [Card A]  [Card B]  [Card C]      | Related Titles...            |
+----+-----------------------------------+------------------------------+
```

---

### C. Android TV 10-Foot Leanback Layout
```text
+-------------------------------------------------------------------------+
|                                                                         |
|  HERO SPOTLIGHT: "NIGHT OF THE LIVING DEAD" (Restored 4K)               |
|  1968 • Horror/Classic • 96m • Public Domain                            |
|  A disparate group of individuals seeks refuge in an abandoned house... |
|                                                                         |
|  [▶ Play Now]      [ℹ More Info]      [+ Watchlist]                     |
|                                                                         |
|  ---------------------------------------------------------------------  |
|                                                                         |
|  POPULAR ON STREAMAPP                                                   |
|  +--------------+  +--------------+  +--------------+  +--------------+ |
|  | FOCUS RING   |  | Standard     |  | Standard     |  | Standard     | |
|  | [Sintel 4K]  |  | [Big Buck B] |  | [Tears Steel]|  | [Metropolis] | |
|  | Scale 1.08x  |  |              |  |              |  |              | |
|  | #00E5FF Glow |  |              |  |              |  |              | |
|  +--------------+  +--------------+  +--------------+  +--------------+ |
|                                                                         |
|  ARCHIVE.ORG CLASSICS                                                   |
|  +--------------+  +--------------+  +--------------+  +--------------+ |
|  | [The General]|  | [The Kid]    |  | [A Trip Moon]|  | [Nosferatu]  | |
|  +--------------+  +--------------+  +--------------+  +--------------+ |
|                                                                         |
+-------------------------------------------------------------------------+
*(Overscan Safe Padding: 48dp on all sides. Clamped boundary navigation)*
```

---

### D. Desktop Layout (Windows 11 & Linux)
```text
+-----------------------------------------------------------------------------+
| StreamApp Desktop                   [-][口][X] (Custom Window Title Bar)     |
+----+------------------------------------------------------------------------+
|    |  [Search Titles, Genres, Years (Ctrl+F)]           [Sync] [Settings]   |
| N  +------------------------------------------------------------------------+
| A  | HERO CAROUSEL: "COSMOS LAUNDROMAT" (Blender Studio)                    |
| V  | Animated Fantasy • 12m • 4K UHD • CC-BY 4.0                            |
|    | [▶ Play (Space)]    [+ Watchlist]    [Legal License: CC-BY 4.0]        |
| R  +------------------------------------------------------------------------+
| A  | CONTINUE WATCHING                                                      |
| I  | [Card 1: Sintel (10:45 / 15:00)]    [Card 2: Tears of Steel (04:12)]   |
| L  +------------------------------------------------------------------------+
|    | ALL TITLES (Responsive Grid: 5 Columns)                                |
|    | [Card A]   [Card B]   [Card C]   [Card D]   [Card E]                   |
|    | [Card F]   [Card G]   [Card H]   [Card I]   [Card J]                   |
+----+------------------------------------------------------------------------+
| Keyboard Shortcuts: Space (Play/Pause) • F (Fullscreen) • M (Mute) • J/L (-/+10s) |
+-----------------------------------------------------------------------------+
```
