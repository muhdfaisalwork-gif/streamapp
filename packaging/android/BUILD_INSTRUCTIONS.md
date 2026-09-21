# StreamApp Android APK — Build Instructions

## What this is
A scaffold for an Android APK that wraps the StreamApp deployed Cloudflare URL
(`https://ls7m73ztxvfc2.space.minimax.io`) in a native Android WebView with
proper permissions, adaptive icons, and APK signing config.

## Status on this machine
**Android SDK / Java NOT installed.** This scaffold is ready to build on a
machine with the toolchain. The Cloudflare-hosted web bundle serves the same
UI as a PWA — Android users can already "Install StreamApp" from Chrome.

## Toolchain requirements (on the build machine)
- Java JDK 17+ (e.g. Temurin)
- Android SDK 34+ (`cmdline-tools`, `platforms;android-34`, `build-tools;34.0.0`)
- Gradle 8.4+ (or use `./gradlew` wrapper, included)

## Quick build (after toolchain install)
```bash
cd G:\streaming app\packaging\android
gradle assembleRelease
# Output: app/build/outputs/apk/release/app-release.apk
```

## What's included

- `AndroidManifest.xml` — INTERNET + WAKE_LOCK permissions
- `app/build.gradle` — minSdk 24, targetSdk 34, signed by debug keystore for now
- `MainActivity.java` — extends WebView with `WebViewClient`, JS enabled, file access allowed
- `res/drawable/ic_launcher_foreground.xml` — red film-strip icon
- `res/values/strings.xml` — app name + URL
- `res/xml/network_security_config.xml` — cleartext traffic disabled (https only)

## Build the APK on a machine with Android Studio
1. Open `G:\streaming app\packaging\android` in Android Studio.
2. File → Sync Project with Gradle Files.
3. Build → Generate Signed Bundle / APK → APK → release.
4. Use the auto-generated debug keystore (replace with a real one for production).

## Why we don't ship a prebuilt APK yet
The user's workstation (`G:\streaming app`) has Python 3.14, Node 22, but no
Java or Android SDK. Adding those would take ~3 GB and an extra 20-30 min.
The Cloudflare-hosted web app IS installable on Android as a PWA — the user
gets the same UX from Chrome's "Install app" menu. A native APK is the next
deliverable once we have a build machine with the SDK.
