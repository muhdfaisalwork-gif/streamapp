# PHASE 0 — DELIVERABLE 3: TARGET PLATFORM MATRIX & HARDWARE SPECIFICATIONS

**Document Version**: 1.0.0  
**Phase**: Phase 0 (Foundation & Legal Scope)  
**Primary Owners**: Agent 4 — Android / Android TV Agent & Agent 5 — Desktop Agent  
**Status**: Submitted for Verification  

---

## 1. COMPREHENSIVE PLATFORM SUPPORT MATRIX

| Platform Target | Supported OS Versions | Form Factors / Dimensions | Primary Input Method | Minimum Hardware Specs |
| :--- | :--- | :--- | :--- | :--- |
| **Android Phone** | Android 7.0 (API 24) to Android 15 (API 35) | 5.0" to 6.9" (Portrait / Landscape) | Multi-touch, Swipes, Edge gestures | 2GB RAM, Quad-Core 1.8GHz, OpenGL ES 3.0 |
| **Android Tablet** | Android 7.0 (API 24) to Android 15 (API 35) | 8.0" to 13.0" (Landscape default, Foldables) | Multi-touch, Stylus, External keyboard | 3GB RAM, Octa-Core 2.0GHz, Full HD Panel |
| **Android TV** | Android TV 9.0 (API 28) to Android TV 14 (Google TV) | 1080p (FHD) & 2160p (4K UHD) Displays | 5-way D-pad Remote, Back, Home, Play/Pause | 1.5GB RAM, Quad-Core Amlogic/MediaTek, H.264/HEVC decode |
| **Windows Desktop**| Windows 10 (Build 19041+) & Windows 11 | 1366x768 to 4K multi-monitor | Keyboard shortcuts, Mouse, Touchpad | 4GB RAM, Intel Core i3 / AMD Ryzen 3, DirectX 11 |
| **Linux Desktop**  | Ubuntu 20.04/22.04/24.04 LTS, Fedora 38+, Debian 11/12 | 1366x768 to 4K displays (X11 & Wayland) | Keyboard shortcuts, Mouse, Trackpad | 4GB RAM, Dual-Core 2.0GHz, OpenGL 3.3 / Mesa |

---

## 2. INPUT MAPPING & INTERACTION SPECIFICATIONS

### A. Android TV Remote (10-Foot Experience)
Android TV requires dedicated focus handling without any pointer cursor assumptions:
- **D-Pad Directional Keys** (`KEYCODE_DPAD_UP`, `DOWN`, `LEFT`, `RIGHT`): Moves focus to adjacent actionable widget.
- **Select / Center** (`KEYCODE_DPAD_CENTER`, `KEYCODE_ENTER`): Activates current focused item (e.g. opens details or starts stream).
- **Back Button** (`KEYCODE_BACK`): Closes drawer/modal, navigates up the hierarchy, or exits player back to browse screen.
- **Media Keys** (`KEYCODE_MEDIA_PLAY`, `PAUSE`, `PLAY_PAUSE`, `FAST_FORWARD`, `REWIND`): Direct media playback control.
- **Visual Focus Requirement**: The active item must have an unmistakable focus ring: `scale(1.08)` transform, `2.5dp` illuminated accent border (`#00E5FF`), and `elevation: 8dp` drop shadow.
- **Horizontal Boundary Clamping Rule**: Horizontal carousels strictly clamp focus at the first (leftmost) and last (rightmost) items. Pressing `LEFT` at the beginning or `RIGHT` at the end produces a gentle elastic bump animation with no focus loss or unintended vertical row skipping. Inter-row navigation is exclusively initiated via `UP` or `DOWN` directional inputs.

### B. Desktop Keyboard Navigation (Windows & Linux)
Desktop users expect power-user shortcuts during browsing and playback:
- `Space` / `K`: Toggle Play / Pause.
- `F` / `F11`: Toggle Fullscreen mode.
- `Left Arrow` / `J`: Seek backward 10 seconds.
- `Right Arrow` / `L`: Seek forward 10 seconds.
- `Up Arrow` / `Down Arrow`: Volume increment / decrement (5% steps).
- `M`: Mute / Unmute audio.
- `C`: Cycle Subtitle track (Off, English, Spanish, etc.).
- `Esc`: Exit Fullscreen or dismiss overlay modals.
- `/` or `Ctrl + F`: Focus search bar immediately.

### C. Touch & Gesture Interactions (Mobile & Tablet)
- **Double tap left/right third**: Seek -10s / +10s with ripple animation.
- **Vertical swipe right side**: Brightness adjustment.
- **Vertical swipe left side**: Volume adjustment.
- **Pinch to zoom**: Toggle between "Fit to Screen" and "Fill / Crop".

---

## 3. GRAPHICS, CODECS & HARDWARE ACCELERATION

### Video Decoders per Target:
- **Android Phone/Tablet/TV**: 
  - Engine: Google Media3 / ExoPlayer 1.x pipeline.
  - Hardware Decoders: MediaCodec API supporting AVC (H.264 High Profile up to Level 5.2), HEVC (H.265 Main/Main10 Profile), VP9, and AV1 (where hardware supports it).
  - Software Fallback: libgav1 and ffmpeg software decoder extensions.
- **Windows Desktop**:
  - Engine: Flutter video_player with Media Foundation / DirectX Video Acceleration (DXVA2 / D3D11VA) and `media_kit` (libmpv).
  - Codecs: H.264, H.265, VP9, AV1 with Direct3D texture sharing.
- **Linux Desktop**:
  - Engine: `media_kit` (libmpv) with VA-API / VDPAU hardware acceleration.
  - Display Servers: Full support for both X11 and Wayland without tearing.

---

## 4. PACKAGING & DISTRIBUTION ARTIFACTS

### Android:
- Universal APK (`app-release.apk`) for sideloading and rapid device testing.
- Android App Bundle (`app-release.aab`) with split architectures (arm64-v8a, armeabi-v7a, x86_64).
- Android TV Leanback Banner (`320x180` xhdpi) and TV Launcher intent category (`CATEGORY_LEANBACK_LAUNCHER`).

### Windows:
- Standalone Portable ZIP (`streaming_app_win_x64.zip`).
- Nullsoft Scriptable Install System (NSIS) Installer (`StreamingApp-Setup-x64.exe`).
- MSIX package with self-signed test certificate for enterprise/store deployment.

### Linux:
- Debian/Ubuntu Package: `.deb` package with system desktop file, high-res icon, and MIME associations.
- Red Hat/Fedora Package: `.rpm` package built with `rpmbuild`.
- Standalone Universal: Portable `.AppImage` bundle executable across any modern Linux distro.
