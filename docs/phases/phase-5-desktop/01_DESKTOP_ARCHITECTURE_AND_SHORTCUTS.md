# PHASE 5 — DELIVERABLE 1: WINDOWS & LINUX DESKTOP ARCHITECTURE & SHORTCUTS

**Document Version**: 1.0.0  
**Phase**: Phase 5 (Windows & Linux Desktop)  
**Primary Owners**: Agent 5 — Desktop Agent & Agent 7 — Streaming / Player Agent  
**Status**: Submitted for Verification  

---

## 1. DESKTOP ARCHITECTURE & HARDWARE ACCELERATION

The desktop application targets both Windows (10/11) and Linux distributions (Ubuntu, Debian, Fedora, Mint):
- **Windows Runtime Engine**: Flutter Windows x64 with DirectX Video Acceleration (DXVA2 / D3D11VA) for hardware-accelerated H.264/HEVC/VP9 decoding.
- **Linux Runtime Engine**: Flutter Linux GTK3 with `media_kit` (libmpv) utilizing VA-API / VDPAU hardware acceleration across both X11 and Wayland display servers.
- **Window Management**:
  - Minimum window constraints: `960x600dp`.
  - Default window dimensions: `1280x800dp`.
  - Custom dark title bar (`DesktopCustomTitleBar`) featuring window title, minimize, maximize/restore, and close buttons.

---

## 2. DESKTOP KEYBOARD SHORTCUT MATRIX

| Shortcut Key | Scope | Action Executed |
| :--- | :--- | :--- |
| `Space` / `K` | Video Player | Toggle Play / Pause |
| `F` / `F11` | Video Player | Toggle Fullscreen Mode |
| `Left Arrow` / `J` | Video Player | Seek backward 10 seconds |
| `Right Arrow` / `L` | Video Player | Seek forward 10 seconds |
| `M` | Video Player | Toggle Audio Mute / Unmute |
| `C` | Video Player | Cycle Subtitle Track |
| `Esc` | Global | Exit Fullscreen or dismiss open modal dialog |
| `Ctrl + F` | Global | Focus Search Bar immediately |
