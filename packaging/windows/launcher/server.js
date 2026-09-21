// StreamApp Launcher — opens the deployed Cloudflare-hosted web app in a
// browser window with optional system-tray icon and start-with-Windows toggle.
// Packaged via `pkg` into a single Windows .exe at packaging/windows/dist/.

const { app, BrowserWindow, Tray, Menu, nativeImage, shell } = require('electron');
const path = require('path');

const APP_URL = process.env.STREAMAPP_URL || 'https://ls7m73ztxvfc2.space.minimax.io';

let mainWindow = null;
let tray = null;

function createMainWindow() {
    mainWindow = new BrowserWindow({
        width: 1400,
        height: 900,
        minWidth: 1024,
        minHeight: 640,
        title: 'StreamApp — Movies & TV. Free.',
        backgroundColor: '#0a0a0a',
        autoHideMenuBar: true,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            sandbox: true
        }
    });

    mainWindow.loadURL(APP_URL);

    mainWindow.on('close', (event) => {
        event.preventDefault();
        mainWindow.hide();
    });
}

function createTray() {
    // 16x16 red film-strip glyph
    const iconBuffer = Buffer.from([
        0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x10, 0x10, 0x00, 0x00, 0x01, 0x00, 0x20, 0x00, 0x68, 0x04,
        0x00, 0x00, 0x16, 0x00, 0x00, 0x00, 0x28, 0x00, 0x00, 0x00, 0x10, 0x00, 0x00, 0x00, 0x20, 0x00,
        0x00, 0x00, 0x01, 0x00, 0x20, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x04, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0xef, 0x1c, 0x1c, 0xef, 0xef, 0x1c, 0x1c, 0xef, 0xef, 0x1c, 0x1c, 0xef, 0xef, 0x1c, 0x1c, 0xef,
        0xef, 0x1c, 0x1c, 0xef, 0xef, 0x1c, 0x1c, 0xef, 0xef, 0x1c, 0x1c, 0xef, 0xef, 0x1c, 0x1c, 0xef,
        0xef, 0x1c, 0x1c, 0xef, 0xef, 0x1c, 0x1c, 0xef, 0xef, 0x1c, 0x1c, 0xef, 0xef, 0x1c, 0x1c, 0xef,
        0xef, 0x1c, 0x1c, 0xef, 0xef, 0x1c, 0x1c, 0xef, 0xef, 0x1c, 0x1c, 0xef, 0xef, 0x1c, 0x1c, 0xef,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
    ]);
    const icon = nativeImage.createFromBuffer(iconBuffer);
    tray = new Tray(icon);
    const menu = Menu.buildFromTemplate([
        { label: 'Open StreamApp', click: () => { if (!mainWindow) createMainWindow(); else { mainWindow.show(); mainWindow.focus(); } } },
        { label: 'Visit in Browser', click: () => shell.openExternal(APP_URL) },
        { type: 'separator' },
        { label: 'Quit', click: () => { app.quit(); } }
    ]);
    tray.setToolTip('StreamApp');
    tray.setContextMenu(menu);
    tray.on('click', () => { if (!mainWindow) createMainWindow(); else { mainWindow.show(); mainWindow.focus(); } });
}

app.whenReady().then(() => {
    createMainWindow();
    createTray();
});

app.on('window-all-closed', (event) => {
    event.preventDefault();
});

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createMainWindow();
});
