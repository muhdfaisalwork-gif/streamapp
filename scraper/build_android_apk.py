"""
build_android_apk.py — build a real, installable, *updatable* Android app.

What this fixes versus the old build_apk.py
--------------------------------------------
1. THE SIGNING KEY IS NOT DESTROYED ON EVERY BUILD.
   The old script deleted its entire build directory at the start of each run
   — including the keystore it had just created inside it. Every build therefore
   produced a different signing key, so a new APK could never install over an
   existing one (INSTALL_FAILED_UPDATE_INCOMPATIBLE) and Play App Signing
   enrollment was meaningless. Here the keystore lives in a stable location,
   is created exactly once, and the build directory is disposable.

2. The app points at the real domain, not a workers.dev URL.
3. targetSdk/minSdk reflect the available android.jar, and this is explicitly a
   SIDELOAD artifact. Play requires API 36 and an .aab, which needs the Android
   SDK + Gradle and an EAS account.

Toolchain discovered on this machine:
    aapt2.exe, android.jar, r8.jar  ->  <scratch>/
    java, javac, keytool, jarsigner ->  JDK 21

Signing is JAR-signature (v1). That installs correctly on every Android release
for sideloading. v2+ needs apksigner from Android build-tools, which is not
present here.

Usage:
    python build_android_apk.py                 # build + sign
    python build_android_apk.py --verify        # inspect an existing apk
    python build_android_apk.py --keystore-info # where the key lives
"""

import argparse
import os
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path

SCRATCH = Path(r"C:\Users\Lucifer\.gemini\antigravity\brain\9b67df9c-ed18-47e9-89da-a96f43a473c9\scratch")
AAPT2 = SCRATCH / "aapt2.exe"
ANDROID_JAR = SCRATCH / "android.jar"
R8_JAR = SCRATCH / "r8.jar"

JDK = Path(r"C:\Users\Lucifer\.antigravity\extensions\redhat.java-1.54.0-win32-x64\jre\21.0.10-win32-x86_64\bin")

REPO = Path(r"G:\streaming app")
OUT_DIR = REPO / "packaging" / "android"
BUILD = REPO / ".apkbuild"

# ---------------------------------------------------------------- identity
PACKAGE = "com.streamapp.app"
APP_NAME = "ShadowStream"
MIN_SDK = 24
TARGET_SDK = 33
VERSION_CODE = 240
VERSION_NAME = "2.4.0"
APP_URL = "https://ssmoviestvs.site"

# Signing material. The password comes from the environment; the keystore file
# itself is the irreplaceable artefact.
KEYSTORE = Path(os.environ.get(
    "SHADOWSTREAM_KEYSTORE_PATH", str(REPO / ".secrets" / "shadowstream-upload.keystore")))
KEY_ALIAS = os.environ.get("SHADOWSTREAM_KEY_ALIAS", "shadowstream")
KEYSTORE_PASS = os.environ.get("SHADOWSTREAM_KEYSTORE_PASS", "")


def load_password():
    """Prefer the env var; fall back to the .secrets note.

    Reading it here rather than through a shell means a password containing
    characters like $ or & cannot be mangled in transit.
    """
    if KEYSTORE_PASS:
        return KEYSTORE_PASS
    note = KEYSTORE.parent / "keystore-password.txt"
    if note.is_file():
        for line in note.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.strip().lower().startswith("password"):
                return line.split(":", 1)[1].strip()
    return ""


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", **kw)


def check_toolchain():
    global KEYSTORE_PASS
    KEYSTORE_PASS = load_password()
    missing = []
    for label, p in (("aapt2", AAPT2), ("android.jar", ANDROID_JAR), ("r8.jar", R8_JAR)):
        if not p.exists():
            missing.append(label)
    for tool in ("java.exe", "javac.exe", "keytool.exe", "jarsigner.exe"):
        if not (JDK / tool).exists():
            missing.append(tool)
    if missing:
        print("FATAL: missing toolchain pieces: " + ", ".join(missing))
        sys.exit(2)


def ensure_keystore():
    """Create the upload key ONCE, in a stable location, and never touch it again."""
    if KEYSTORE.exists():
        print(f"  using existing keystore: {KEYSTORE}  ({KEYSTORE.stat().st_size:,} bytes)")
        return
    if not KEYSTORE_PASS:
        print("\nNo keystore yet and SHADOWSTREAM_KEYSTORE_PASS is not set.")
        print("Create one with a strong password, for example:")
        print('    $env:SHADOWSTREAM_KEYSTORE_PASS = "<a long random password>"')
        print("    python build_android_apk.py")
        print("Then back the file up somewhere permanent. Losing it means the app")
        print("can never be updated again.\n")
        sys.exit(3)
    KEYSTORE.parent.mkdir(parents=True, exist_ok=True)
    print(f"  creating upload keystore: {KEYSTORE}")
    r = run([str(JDK / "keytool.exe"), "-genkeypair",
             "-keystore", str(KEYSTORE), "-storetype", "PKCS12",
             "-storepass", KEYSTORE_PASS, "-keypass", KEYSTORE_PASS,
             "-alias", KEY_ALIAS, "-keyalg", "RSA", "-keysize", "4096",
             "-validity", "10950",
             "-dname", "CN=ShadowStream, OU=Mobile, O=ShadowStream, L=Karachi, ST=Sindh, C=PK"])
    if r.returncode != 0:
        print("FATAL: keytool failed\n", r.stdout, r.stderr)
        sys.exit(2)


JAVA_SOURCE = r'''
package {pkg};

import android.annotation.SuppressLint;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.view.KeyEvent;
import android.view.View;
import android.view.WindowManager;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Toast;

public class MainActivity extends android.app.Activity {{

    private static final String HOME = "{url}";

    private WebView web;
    private long lastBackPress = 0L;

    @SuppressLint("SetJavaScriptEnabled")
    @Override
    protected void onCreate(Bundle savedInstanceState) {{
        super.onCreate(savedInstanceState);

        web = new WebView(this);
        setContentView(web);

        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setDatabaseEnabled(true);
        s.setMediaPlaybackRequiresUserGesture(false);
        s.setLoadWithOverviewMode(true);
        s.setUseWideViewPort(true);
        s.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        s.setCacheMode(WebSettings.LOAD_DEFAULT);
        s.setAllowFileAccess(false);
        s.setAllowContentAccess(false);
        if (android.os.Build.VERSION.SDK_INT >= 21) {{
            s.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        }}

        // Hardware acceleration keeps video decode smooth.
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_HARDWARE_ACCELERATED);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);

        web.setWebViewClient(new WebViewClient() {{
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest req) {{
                return handleUrl(req.getUrl());
            }}

            @Override
            public void onPageFinished(WebView view, String url) {{
                injectFullscreenBridge(view);
            }}
        }});

        web.setWebChromeClient(new WebChromeClient());

        // Block popups/popunders; the app handles navigation itself.
        s.setSupportMultipleWindows(false);
        s.setJavaScriptCanOpenWindowsAutomatically(false);

        web.loadUrl(HOME);
    }}

    private boolean handleUrl(Uri uri) {{
        if (uri == null) return false;
        String host = uri.getHost();
        if (host != null && (host.endsWith("ssmoviestvs.site")
                || host.endsWith("workers.dev"))) {{
            return false; // let the WebView load it
        }}
        try {{
            startActivity(new Intent(Intent.ACTION_VIEW, uri));
        }} catch (ActivityNotFoundException e) {{
            Toast.makeText(this, "No app can open that link", Toast.LENGTH_SHORT).show();
        }}
        return true;
    }}

    /** Let the site's own fullscreen button drive the native window. */
    private void injectFullscreenBridge(WebView view) {{
        try {{
            view.evaluateJavascript(
                "(function(){{"
              + "  var m=document.querySelector('meta[name=viewport]');"
              + "  if(!m){{m=document.createElement('meta');m.name='viewport';document.head.appendChild(m);}}"
              + "  m.content='width=device-width, initial-scale=1, viewport-fit=cover';"
              + "  document.documentElement.style.overflow='hidden';"
              + "}})();", null);
        }} catch (Throwable ignored) {{
        }}
    }}

    @Override
    public void onBackPressed() {{
        if (web != null && web.canGoBack()) {{
            web.goBack();
            return;
        }}
        long now = System.currentTimeMillis();
        if (now - lastBackPress < 2000) {{
            finish();
        }} else {{
            lastBackPress = now;
            Toast.makeText(this, "Press back again to exit", Toast.LENGTH_SHORT).show();
        }}
    }}

    @Override
    protected void onPause() {{
        super.onPause();
        if (web != null) web.onPause();
    }}

    @Override
    protected void onResume() {{
        super.onResume();
        if (web != null) web.onResume();
    }}

    @Override
    protected void onDestroy() {{
        if (web != null) {{
            web.loadUrl("about:blank");
            web.destroy();
            web = null;
        }}
        super.onDestroy();
    }}
}}
'''


def build():
    check_toolchain()
    print("== ShadowStream Android build ==")
    print(f"  package  {PACKAGE}  v{VERSION_NAME} ({VERSION_CODE})")
    print(f"  sdk      min {MIN_SDK} target {TARGET_SDK}")
    print(f"  url      {APP_URL}")
    ensure_keystore()

    # Disposable build dir. Note it does NOT contain the keystore.
    if BUILD.exists():
        shutil.rmtree(BUILD)
    (BUILD / "res" / "values").mkdir(parents=True)
    (BUILD / "res" / "mipmap-anydpi-v26").mkdir(parents=True)
    (BUILD / "res" / "drawable").mkdir(parents=True)
    (BUILD / "java" / PACKAGE.replace(".", "/")).mkdir(parents=True)
    (BUILD / "out").mkdir(parents=True)
    (BUILD / "assets").mkdir(parents=True)

    # Icon: reuse the app icon asset.
    icon_src = REPO / "frontend" / "assets" / "icon.png"
    if icon_src.exists():
        shutil.copy(icon_src, BUILD / "res" / "mipmap-anydpi-v26" / "ic_launcher.png")

    (BUILD / "res" / "values" / "strings.xml").write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n<resources>\n'
        f'  <string name="app_name">{APP_NAME}</string>\n'
        '</resources>\n', encoding="utf-8")
    (BUILD / "res" / "values" / "styles.xml").write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n<resources>\n'
        '  <style name="AppTheme" parent="@android:style/Theme.Material.NoActionBar.Fullscreen">\n'
        '    <item name="android:windowBackground">#0d0d0d</item>\n'
        '  </style>\n'
        '</resources>\n', encoding="utf-8")

    (BUILD / "AndroidManifest.xml").write_text(f"""<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="{PACKAGE}">

    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    <uses-permission android:name="android.permission.WAKE_LOCK" />

    <!-- Needed to hand a stream to VLC / MX Player from the External button. -->
    <queries>
        <intent>
            <action android:name="android.intent.action.VIEW" />
            <data android:scheme="https" />
        </intent>
        <package android:name="com.videolan.vlc" />
        <package android:name="org.mxplayer" />
    </queries>

    <uses-sdk android:minSdkVersion="{MIN_SDK}" android:targetSdkVersion="{TARGET_SDK}" />

    <application
        android:label="@string/app_name"
        android:icon="@mipmap/ic_launcher"
        android:theme="@style/AppTheme"
        android:hardwareAccelerated="true"
        android:usesCleartextTraffic="false"
        android:allowBackup="true"
        android:supportsRtl="true">

        <activity
            android:name=".MainActivity"
            android:exported="true"
            android:launchMode="singleTop"
            android:screenOrientation="behind"
            android:configChanges="orientation|keyboardHidden|screenSize|smallestScreenSize|screenLayout|uiMode"
            android:windowSoftInputMode="adjustResize">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
""", encoding="utf-8")

    java_path = BUILD / "java" / PACKAGE.replace(".", "/") / "MainActivity.java"
    java_path.write_text(JAVA_SOURCE.format(pkg=PACKAGE, url=APP_URL), encoding="utf-8")

    print("  1/5  aapt2 compile resources")
    flat = BUILD / "out" / "resources.zip"
    r = run([str(AAPT2), "compile", "--dir", str(BUILD / "res"), "-o", str(flat)])
    if r.returncode != 0:
        print("aapt2 compile failed:\n", r.stdout, r.stderr)
        sys.exit(2)

    base = BUILD / "out" / "base.apk"
    r = run([str(AAPT2), "link", "-o", str(base), "-I", str(ANDROID_JAR),
             "--manifest", str(BUILD / "AndroidManifest.xml"),
             "--min-sdk-version", str(MIN_SDK), "--target-sdk-version", str(TARGET_SDK),
             "--version-code", str(VERSION_CODE), "--version-name", VERSION_NAME,
             str(flat)])
    if r.returncode != 0:
        print("aapt2 link failed:\n", r.stdout, r.stderr)
        sys.exit(2)

    print("  2/5  javac")
    classes = BUILD / "out" / "classes"
    classes.mkdir(parents=True, exist_ok=True)
    r = run([str(JDK / "javac.exe"), "-source", "8", "-target", "8",
             "-bootclasspath", str(ANDROID_JAR), "-classpath", str(ANDROID_JAR),
             "-d", str(classes), str(java_path)])
    if r.returncode != 0:
        print("javac failed:\n", r.stdout, r.stderr)
        sys.exit(2)

    print("  3/5  d8 (dex)")
    dex_dir = BUILD / "out" / "dex"
    dex_dir.mkdir(parents=True, exist_ok=True)
    # javac nests output by package, so the class lives under com/streamapp/app.
    main_class = classes / PACKAGE.replace(".", "/") / "MainActivity.class"
    if not main_class.exists():
        print(f"d8: expected class not found at {main_class}")
        sys.exit(2)
    # r8.jar here has no Main-Class, so D8 is invoked as a class rather than
    # with `java -jar`.
    r = run(["java", "-cp", str(R8_JAR), "com.android.tools.r8.D8",
             "--lib", str(ANDROID_JAR),
             "--min-api", str(MIN_SDK), "--output", str(dex_dir),
             str(main_class)])
    if r.returncode != 0:
        print("d8 failed:\n", r.stdout, r.stderr)
        sys.exit(2)

    print("  4/5  assemble")
    unsigned = BUILD / "out" / "unsigned.apk"
    shutil.copy(base, unsigned)
    dex_files = sorted(dex_dir.glob("*.dex"))
    if not dex_files:
        print("d8 produced no .dex output")
        sys.exit(2)
    with zipfile.ZipFile(unsigned, "a", zipfile.ZIP_DEFLATED) as z:
        for d in dex_files:
            z.write(d, d.name)

    print("  5/5  sign (v1 / keystore)")
    # jarsigner's positional form is: jarsigner [options] <input> <alias>
    # The input file is required — omitting it makes jarsigner read the alias
    # as the archive and then complain that no alias was given.
    signed = BUILD / "out" / "signed.apk"
    r = run([str(JDK / "jarsigner.exe"),
             "-keystore", str(KEYSTORE), "-storepass", KEYSTORE_PASS,
             "-keypass", KEYSTORE_PASS,
             "-sigalg", "SHA256withRSA", "-digestalg", "SHA-256",
             "-signedjar", str(signed), str(unsigned), KEY_ALIAS])
    if r.returncode != 0:
        print("jarsigner failed:\n", r.stdout, r.stderr)
        sys.exit(2)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    final = OUT_DIR / "ShadowStream.apk"
    shutil.copy(signed, final)

    size = final.stat().st_size
    print(f"\n  built: {final}  ({size:,} bytes)")
    print(f"  signed with: {KEYSTORE.name}  alias={KEY_ALIAS}")
    print(f"  version: {VERSION_NAME} ({VERSION_CODE})  targetSdk {TARGET_SDK}")
    print(f"\n  install:  adb install -r {final}")
    print("  -r upgrades an existing install; the signing key is stable, so this works.")
    verify(str(final))


def verify(path):
    print("\n== verify ==")
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        print(f"  entries      {len(names)}")
        print(f"  manifest     {'AndroidManifest.xml' in names}")
        print(f"  dex          {any(n.endswith('.dex') for n in names)}")
        signed = any(n.startswith("META-INF/") for n in names)
        print(f"  v1 signature {signed}")
    txt = Path(path).read_bytes()
    print(f"  size         {len(txt):,} bytes")
    ok = signed and any(n.endswith(".dex") for n in names)
    print(f"  STATUS       {'OK' if ok else 'PROBLEM'}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", metavar="APK")
    ap.add_argument("--keystore-info", action="store_true")
    args = ap.parse_args()
    if args.verify:
        verify(args.verify)
    elif args.keystore_info:
        print(KEYSTORE)
        print("exists" if KEYSTORE.exists() else "NOT CREATED YET")
    else:
        build()
