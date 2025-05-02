const { app, BrowserWindow, ipcMain, shell } = require('electron');
const path = require('path');
const url = require('url');

// Keep a global reference of the window object
let mainWindow;

// Suppress Electron warnings
process.env.ELECTRON_DISABLE_SECURITY_WARNINGS = 'true';

function createWindow() {
  // Create the browser window
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    }
  });

  // Determine the correct URL to load
  const startUrl = process.env.ELECTRON_START_URL || url.format({
    pathname: path.join(__dirname, '../dist/index.html'),
    protocol: 'file:',
    slashes: true
  });
  
  console.log("Loading URL:", startUrl);
  
  // Load the app
  mainWindow.loadURL(startUrl);

  // Open DevTools in development mode but suppress console noise
  if (process.env.ELECTRON_START_URL) {
    mainWindow.webContents.openDevTools();
    
    // Optional: Filter out specific DevTools warnings
    mainWindow.webContents.on('console-message', (event, level, message) => {
      if (message.includes('Autofill.') && message.includes('wasn\'t found')) {
        event.preventDefault();
      }
    });
  }

  mainWindow.on('closed', function () {
    mainWindow = null;
  });
}

app.whenReady().then(() => {
  createWindow();
  
  // Set up IPC handler for opening files
  ipcMain.handle('open-file', async (event, filePath) => {
    console.log('Opening file:', filePath);
    try {
      await shell.openPath(filePath);
      return { success: true };
    } catch (err) {
      console.error('Failed to open file:', err);
      return { success: false, error: err.message };
    }
  });
});

app.on('window-all-closed', function () {
  if (process.platform !== 'darwin') app.quit();
});

app.on('activate', function () {
  if (mainWindow === null) createWindow();
});