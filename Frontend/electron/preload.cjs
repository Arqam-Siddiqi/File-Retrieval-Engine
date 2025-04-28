const { contextBridge, ipcRenderer, shell } = require('electron');
const fs = require('fs');
const path = require('path');

// Expose APIs for file handling
contextBridge.exposeInMainWorld('electronAPI', {
  // Open file in default application
  openFile: (filePath) => {
    shell.openPath(filePath);
  },
  
  // Read file contents for preview
  readFile: (filePath) => {
    return new Promise((resolve, reject) => {
      const ext = path.extname(filePath).toLowerCase();
      
      // For text files, read content
      if (ext === '.txt') {
        fs.readFile(filePath, 'utf-8', (err, data) => {
          if (err) reject(err);
          else resolve(data);
        });
      } 
      // For images, just indicate they can be previewed
      else if (['.jpg', '.jpeg', '.png', '.gif'].includes(ext)) {
        resolve(null); // Will render the image with src
      } 
      // For documents and PDFs, indicate no preview is available
      else {
        resolve(null); // Preview component will handle this case
      }
    });
  }
});