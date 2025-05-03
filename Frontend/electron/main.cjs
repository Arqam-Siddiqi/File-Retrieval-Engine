const { app, BrowserWindow, ipcMain, shell } = require('electron');
const path = require('path');
const url = require('url');
const fs = require('fs');
const { spawn } = require('child_process');

// Keep a global reference of the window object
let mainWindow;
// Track any child processes
let childProcesses = [];

// Suppress Electron warnings
process.env.ELECTRON_DISABLE_SECURITY_WARNINGS = 'true';

function createWindow() {
  // Create the browser window
  mainWindow = new BrowserWindow({
    width: 800,
    height: 700,
    title: "File Retrieval Engine",
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
    // mainWindow.webContents.openDevTools();
    
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

// Function to resolve relative paths
function resolveFilePath(filePath) {
  // Check if it's a relative path (starts with ../ or ./)
  if (filePath.startsWith('../') || filePath.startsWith('./')) {
    // Resolve relative to the project root directory
    // Assuming Backend and Frontend are sibling directories
    const projectRoot = path.resolve(__dirname, '../');
    return path.resolve(projectRoot, filePath);
  }
  return filePath;
}

// Function to kill all child processes
function cleanupProcesses() {
  childProcesses.forEach(process => {
    if (!process.killed) {
      try {
        // Force kill on Windows
        if (process.platform === 'win32') {
          spawn('taskkill', ['/pid', process.pid, '/f', '/t']);
        } else {
          process.kill('SIGTERM');
        }
      } catch (e) {
        console.error('Error killing process:', e);
      }
    }
  });
  // Clear the array
  childProcesses = [];
}

app.whenReady().then(() => {
  createWindow();
  
  // Set up IPC handler for opening files
  ipcMain.handle('open-file', async (event, filePath) => {
    
    // Resolve the file path
    const resolvedPath = resolveFilePath(filePath);
    
    // Check if file exists before trying to open it
    if (!fs.existsSync(resolvedPath)) {
      console.error('File does not exist:', resolvedPath);
      return { 
        success: false, 
        error: `File does not exist: ${resolvedPath}` 
      };
    }
    
    try {
      await shell.openPath(resolvedPath);
      return { success: true };
    } catch (err) {
      console.error('Failed to open file:', err);
      return { success: false, error: err.message };
    }
  });
});

// Ensure we properly clean up
app.on('will-quit', () => {
  cleanupProcesses();
});

// Force cleanup when window is closed
app.on('window-all-closed', function () {
  cleanupProcesses();
  app.quit();
});

app.on('activate', function () {
  if (mainWindow === null) createWindow();
});