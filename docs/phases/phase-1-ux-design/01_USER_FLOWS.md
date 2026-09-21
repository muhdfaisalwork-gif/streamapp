# PHASE 1 — DELIVERABLE 1: USER FLOWS & INTERACTION ARCHITECTURE

**Document Version**: 1.0.0  
**Phase**: Phase 1 (UX & Design System)  
**Primary Owners**: Agent 2 — UI/UX Design Agent & Agent 1 — Product Manager / Requirements Agent  
**Status**: Submitted for Verification  

---

## 1. USER FLOW TAXONOMY & ARCHITECTURAL PRINCIPLES

The user experience is engineered around three foundational tenets:
1. **Instant Gratification (Zero-Friction Guest Mode)**: Users can browse the entire catalog and begin streaming within 2 clicks from cold start without registering or entering personal data.
2. **Deterministic Resumption**: Watch history and bookmarks are saved immediately at the millisecond level and automatically promoted from local guest storage to cloud storage upon user sign-in.
3. **Form-Factor Native Interaction**: 
   - Android Mobile: One-handed thumb reachability, edge gestures.
   - Android Tablet: Responsive multi-column grid with split-pane title inspection.
   - Android TV: 10-foot D-pad navigation, high-visibility focus indicators, zero pointer traps.
   - Desktop: Keyboard shortcuts, hover states, multi-window responsiveness.

---

## 2. CORE USER JOURNEYS & STATE FLOWCHARTS

### FLOW 1: Cold Start, Guest Mode & Discovery
```mermaid
graph TD
    AppLaunch["App Launch (Cold Start)"] --> CheckSession{"Auth Token Cached?"}
    CheckSession -- "Yes" --> HydrateUser["Hydrate Cloud User Profile & Bookmarks"]
    CheckSession -- "No" --> InitGuest["Initialize Local Guest Session in SQLite"]
    
    HydrateUser --> LoadFeed["Load Home Feed from API (Cached ETag)"]
    InitGuest --> LoadFeed
    
    LoadFeed --> RenderHome["Render Home Screen: Hero Carousel + Trays"]
    RenderHome --> UserChoice{"User Action"}
    UserChoice -- "Select Hero Play" --> InstantPlay["Launch Video Player with Master Stream"]
    UserChoice -- "Browse Trays" --> ScrollFeed["Navigate Trays (Touch/D-pad/Mouse)"]
    UserChoice -- "Click Title Card" --> OpenDetails["Open Title Details Modal / Page"]
    UserChoice -- "Click Search" --> SearchScreen["Open Search View"]
    UserChoice -- "Click Sign In" --> AuthModal["Open Auth / Registration Modal"]
```

---

### FLOW 2: Search, Query Filtering & Discovery
```mermaid
graph TD
    SearchScreen["Search Input Focused"] --> EnterQuery["User Enters Query Term"]
    EnterQuery --> Debounce{"300ms Idle Delay?"}
    Debounce -- "Typing..." --> EnterQuery
    Debounce -- "Idle" --> QueryAPI["Dispatch GET /api/v1/search?q=..."]
    
    QueryAPI --> APIResponse{"Results Found?"}
    APIResponse -- "Yes (Matches > 0)" --> RenderResults["Display Grid: Grouped by Titles, Creators, Genres"]
    APIResponse -- "No (Matches == 0)" --> EmptyState["Render Friendly Empty State + Curated Classics Tray"]
    
    RenderResults --> SelectItem["User Selects Media Card"]
    EmptyState --> SelectItem
    SelectItem --> OpenDetails["Open Title Details Modal"]
```

---

### FLOW 3: Video Player Lifecycle & Error Recovery
```mermaid
graph TD
    TriggerPlay["Trigger Playback (from Card / Details)"] --> ProbeCache["Check Local/Cloud Bookmark for Resume Position"]
    ProbeCache --> MountPlayer["Initialize Player Surface (Media3 / libmpv)"]
    MountPlayer --> LoadManifest["Fetch Primary HLS Manifest (.m3u8)"]
    
    LoadManifest --> CheckStream{"Manifest Load Success?"}
    CheckStream -- "Success" --> SeekResume["Seek to Resume Timestamp (if > 10s)"]
    SeekResume --> BufferFirst["Buffer Initial Segment (Sub-second TTFF)"]
    BufferFirst --> PlayingState["State: PLAYING"]
    
    CheckStream -- "Failure / 404 / CORS" --> RetryPrimary{"Retry Count < 2?"}
    RetryPrimary -- "Yes" --> BackoffWait["Wait Exponential Backoff (1s, 2s)"] --> LoadManifest
    RetryPrimary -- "No" --> CheckBackup{"Backup Stream Available?"}
    CheckBackup -- "Yes" --> LoadBackup["Switch Source to backupUrl"] --> SeekResume
    CheckBackup -- "No" --> RenderPlayerError["Display Graceful Error Modal + Retry & Report Buttons"]
    
    PlayingState --> UserInput{"Player Controls Action"}
    UserInput -- "Pause / Play" --> TogglePlayback["Toggle Play/Pause State"]
    UserInput -- "Seek (+/-10s)" --> Scrub["Seek Target Time + Persist Bookmark"]
    UserInput -- "Change Subtitle" --> SwitchSub["Mount WebVTT Subtitle Track"]
    UserInput -- "Quality Select" --> ForceABR["Override ABR Track (e.g. 1080p, 720p, Auto)"]
    UserInput -- "Back / Close" --> SaveBookmark["Save Exact Position to SQLite & API"] --> DisposePlayer["Dispose Surface & Return"]
```

---

### FLOW 4: Watchlist & Guest-to-Account Migration
```mermaid
graph TD
    GuestAction["Guest Adds Title to Watchlist / Watches 5 mins"] --> StoreLocal["Save to Local SQLite (is_guest=true)"]
    StoreLocal --> LaterRegister["Guest Chooses 'Sign In / Register'"]
    LaterRegister --> SubmitCredentials["Submit Auth API Request"]
    SubmitCredentials --> AuthSuccess{"Credentials Valid?"}
    AuthSuccess -- "Yes" --> ReceiveJWT["Store Access JWT & Refresh Token"]
    
    ReceiveJWT --> TriggerSync["Trigger POST /api/v1/user/sync with Local Bookmarks"]
    TriggerSync --> ConflictMerge{"Merge Local vs Server Data"}
    ConflictMerge --> MergeRules["Rules: Max timestamp wins; Union of watchlists"]
    MergeRules --> PersistMerged["Update Local SQLite & Cloud Database"]
    PersistMerged --> UpdateUI["Refresh UI with Merged Watchlist & Continue Watching Trays"]
```

---

### FLOW 5: Android TV D-Pad Remote Traversal
```mermaid
graph TD
    TVAppStart["Android TV App Mounted"] --> FocusHome["Default Focus: First Item in Hero Carousel"]
    FocusHome --> TVInput{"D-Pad Remote Input"}
    
    TVInput -- "DPAD_RIGHT" --> RightCheck{"At End of Carousel Row?"}
    RightCheck -- "No" --> MoveRight["Focus Advances to Next Card (scale 1.08x)"]
    RightCheck -- "Yes" --> ClampRight["Hard Clamp: Elastic Bump Animation, Zero Focus Loss"]
    
    TVInput -- "DPAD_LEFT" --> LeftCheck{"At Beginning of Row?"}
    LeftCheck -- "No" --> MoveLeft["Focus Moves to Previous Card"]
    LeftCheck -- "Yes" --> ClampLeft["Hard Clamp: Focus Retained on First Card"]
    
    TVInput -- "DPAD_DOWN" --> DownMove["Focus Moves to First Visible Card of Next Tray"]
    TVInput -- "DPAD_UP" --> UpCheck{"In Top Tray?"}
    UpCheck -- "No" --> MoveUpTray["Focus Moves to Upper Tray Card"]
    UpCheck -- "Yes" --> FocusHero["Focus Moves to Hero Action Buttons (Play/Details)"]
    
    TVInput -- "DPAD_CENTER / ENTER" --> Activate["Open Title Details or Start Stream"]
    TVInput -- "BACK" --> HandleBack{"Current Screen?"}
    HandleBack -- "In Player" --> ExitPlayer["Stop Playback, Save Bookmark, Return to Tray"]
    HandleBack -- "In Details Modal" --> CloseModal["Dismiss Modal, Return Focus to Trigger Card"]
    HandleBack -- "In Home Feed" --> PromptExit["Show 'Exit App?' Confirmation Dialog"]
```
