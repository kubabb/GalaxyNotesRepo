const { contextBridge, ipcRenderer } = require('electron');
const fs = require('fs');
const path = require('path');

// Expose safe API to renderer process
contextBridge.exposeInMainWorld('electronAPI', {
  // Python backend logs
  onPythonLog: (callback) => ipcRenderer.on('python-log', (event, data) => callback(data)),
  onPythonError: (callback) => ipcRenderer.on('python-error', (event, data) => callback(data)),

  // Main-process navigation (View menu)
  onNavigate: (callback) => ipcRenderer.on('navigate', (event, target) => callback(target)),

  // File operations
  uploadFiles: (files, projectName) => ipcRenderer.invoke('upload-files', files, projectName),
  selectFolder: () => ipcRenderer.invoke('select-folder'),

  // Project management
  createProject: (name) => ipcRenderer.invoke('create-project', name),
  getProjects: () => ipcRenderer.invoke('get-projects'),

  // Read JSON file directly (for galaxy_data.json, metadata.json)
  readJSON: (relativePath) => {
    const fullPath = path.join(__dirname, '..', relativePath);
    try {
      const data = fs.readFileSync(fullPath, 'utf-8');
      return JSON.parse(data);
    } catch (e) {
      return null;
    }
  },

  // Check if running in Electron
  isElectron: true,

  // App info
  getVersion: () => ipcRenderer.invoke('get-version'),

  // Platform
  platform: process.platform
});
