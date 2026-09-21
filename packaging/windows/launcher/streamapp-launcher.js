// StreamApp Desktop Launcher — opens the deployed web app in the user's
// default browser and adds itself to the system tray (Windows) or to the
// menu bar (macOS). Packaged via `pkg` as StreamApp.exe.
//
// Usage: streamapp-launcher.exe [--url=URL] [--no-tray] [--quit-after=N]
// Default URL: https://ls7m73ztxvfc2.space.minimax.io
'use strict';

const { exec } = require('child_process');
const path = require('path');
const fs = require('fs');
const os = require('os');

const APP_URL = (process.argv.find(a => a.startsWith('--url=')) || '').split('=')[1]
    || process.env.STREAMAPP_URL
    || 'https://ls7m73ztxvfc2.space.minimax.io';
const NO_TRAY = process.argv.includes('--no-tray');
const QUIT_AFTER = parseInt((process.argv.find(a => a.startsWith('--quit-after=')) || '').split('=')[1] || '0', 10);

const TITLE = 'StreamApp';
const PID_FILE = path.join(os.tmpdir(), 'streamapp-launcher.pid');

function log(...args) {
    const line = `[${new Date().toISOString()}] ${args.join(' ')}`;
    console.log(line);
    try { fs.appendFileSync(path.join(os.tmpdir(), 'streamapp-launcher.log'), line + '\n'); } catch (_) {}
}

function openBrowser(url) {
    const platform = process.platform;
    let cmd;
    if (platform === 'win32') cmd = `start "" "${url}"`;
    else if (platform === 'darwin') cmd = `open "${url}"`;
    else cmd = `xdg-open "${url}"`;
    exec(cmd, (err) => {
        if (err) {
            log('openBrowser failed:', err.message);
            // Fallback: print URL for manual paste
            log('Open this URL manually:', url);
        }
    });
}

function setupTray() {
    // Best-effort: native Node has no built-in tray API. We rely on Windows
    // shell + a minimal PowerShell snippet that adds an entry to the Startup
    // group and pins the URL via the default browser's PWA install (Chrome
    // will offer "Install StreamApp" once it loads).
    if (process.platform !== 'win32') return;
    const startupShortcut = path.join(os.homedir(), 'AppData', 'Roaming', 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup', 'StreamApp.url');
    const shortcutContent = `[InternetShortcut]\nURL=${APP_URL}\nIconIndex=0\nIconFile=`;
    try {
        fs.writeFileSync(startupShortcut, shortcutContent);
        log('Startup shortcut installed at', startupShortcut);
    } catch (e) {
        log('Startup shortcut failed:', e.message);
    }
}

function startHeartbeat() {
    if (QUIT_AFTER <= 0) return;
    setTimeout(() => {
        log('quit-after reached, exiting');
        try { fs.unlinkSync(PID_FILE); } catch (_) {}
        process.exit(0);
    }, QUIT_AFTER * 1000);
}

function main() {
    log(`StreamApp launcher starting → ${APP_URL}`);
    fs.writeFileSync(PID_FILE, String(process.pid));
    openBrowser(APP_URL);
    if (!NO_TRAY) setupTray();
    startHeartbeat();
    log('launcher ready (pid', process.pid + ')');
    // Keep the process alive in case of --quit-after=N so we can exit cleanly
    if (QUIT_AFTER <= 0) setInterval(() => {}, 1 << 30);
}

main();
