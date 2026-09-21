# PHASE 5 — DELIVERABLE 2: DESKTOP PACKAGING & DISTRIBUTION SPECIFICATIONS

**Document Version**: 1.0.0  
**Phase**: Phase 5 (Windows & Linux Desktop)  
**Primary Owners**: Agent 5 — Desktop Agent & Agent 8 — DevOps / Infrastructure Agent  
**Status**: Submitted for Verification  

---

## 1. WINDOWS PACKAGING SPECIFICATIONS

1. **NSIS Setup Executable (`StreamingApp-Setup-x64.exe`)**:
   - Built via `packaging/windows/installer.nsi`.
   - Provisions `$PROGRAMFILES64\StreamApp`, installs desktop and Start Menu shortcuts, and configures uninstaller registry keys.
2. **Portable ZIP Archive (`streaming_app_win_x64.zip`)**:
   - Zero-install standalone folder containing `streaming_app.exe` and dependent DLLs (`flutter_windows.dll`, libmpv).

---

## 2. LINUX PACKAGING SPECIFICATIONS

1. **Debian / Ubuntu / Mint Package (`.deb`)**:
   - Built via `packaging/linux/debian/control`.
   - Installs binaries into `/usr/bin/streaming_app` and system `.desktop` file into `/usr/share/applications/`.
2. **Fedora / RHEL Package (`.rpm`)**:
   - Built via `packaging/linux/rpm/streaming_app.spec`.
   - Requires `gtk3` and `mpv-libs`.
3. **Universal AppImage (`StreamApp-x86_64.AppImage`)**:
   - Built with `appimagetool` and `packaging/linux/appimage/AppRun`.
   - Runs out-of-the-box across any modern Linux distribution without package manager installation.
