/**
 * Galaxy-Pilot Renderer Helper
 * Automatycznie wykrywa Electron i używa IPC zamiast fetch
 */

window.GP = window.GP || {};

// Detect Electron
GP.isElectron = () => {
  return typeof window !== 'undefined' && 
         typeof window.electronAPI !== 'undefined' && 
         window.electronAPI.isElectron === true;
};

// Load JSON (galaxy_data.json, metadata.json)
GP.loadJSON = async (path) => {
  if (GP.isElectron()) {
    // Use IPC (direct file read)
    return window.electronAPI.readJSON(path);
  } else {
    // Use fetch (web server mode)
    const res = await fetch(path);
    return res.json();
  }
};

// Upload files (Electron: IPC, Web: manual)
GP.uploadFiles = async (files, projectName) => {
  if (GP.isElectron()) {
    // Convert File objects to serializable format
    const serializable = await Promise.all(files.map(async (f) => ({
      name: f.name,
      data: Array.from(new Uint8Array(await f.arrayBuffer()))
    })));
    return window.electronAPI.uploadFiles(serializable, projectName);
  } else {
    // Web fallback: show CLI instruction
    return { error: 'WEB_MODE', message: 'Use python main.py --brain data/inbox' };
  }
};

// Select folder (Electron only)
GP.selectFolder = async () => {
  if (GP.isElectron()) {
    return window.electronAPI.selectFolder();
  }
  return null;
};

// Get projects list
GP.getProjects = async () => {
  if (GP.isElectron()) {
    return window.electronAPI.getProjects();
  }
  return [];
};

// Create project
GP.createProject = async (name) => {
  if (GP.isElectron()) {
    return window.electronAPI.createProject(name);
  }
  return { error: 'WEB_MODE' };
};

// App version
GP.getVersion = async () => {
  if (GP.isElectron()) {
    return window.electronAPI.getVersion();
  }
  return '5.1.0-web';
};

// Listen for main-process navigation (View menu / tray)
if (GP.isElectron() && window.electronAPI.onNavigate) {
  window.electronAPI.onNavigate((target) => {
    const targetUrl = `./${target}.html`;
    if (window.location.href.endsWith(targetUrl)) return;
    window.location.href = targetUrl;
  });
}

console.log('[GP] Renderer helper loaded. Electron:', GP.isElectron());
