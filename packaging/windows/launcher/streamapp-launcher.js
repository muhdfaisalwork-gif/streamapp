// StreamApp Desktop Launcher — opens the deployed web app in the user's
// default browser.
//
// Usage: streamapp-launcher.exe [--url=URL] [--no-tray] [--quit-after=N]
// Default URL: https://ssmoviestvs.site
//
// This was the workers.dev developer link, which still resolves but is the
// wrong place to send users: it is the raw Cloudflare hostname, not the brand
// domain, so bookmarks and screenshots show an internal URL.
//
// NOTE: this used to write a StreamApp.url shortcut into the Windows Startup
// folder on every launch. That is silent boot persistence with no user consent
// and the file was never removed. It is gone. If auto-launch is wanted later it
// belongs behind an explicit opt-in inside the app.
'use strict';

const { exec } = require('child_process');
const path = require('path');
const fs = require('fs');
const os = require('os');

const APP_URL = (process.argv.find(a => a.startsWith('--url=')) || '').split('=')[1]
    || process.env.STREAMAPP_URL
    || 'https://ssmoviestvs.site';
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

// Auto-launch on boot was removed. See the note at the top of this file.
// Launching a desktop app should not silently write to the Startup folder.
function setupTray() {
    log('no tray integration (not supported for this build)');
    return;
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
