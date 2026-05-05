const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');

// Ścieżki
const PROJECT_ROOT = path.join(__dirname, '..');
const PYTHON_SCRIPT = path.join(PROJECT_ROOT, 'src', 'main.py');
const DATA_DIR = path.join(PROJECT_ROOT, 'data');
const PROJECTS_DIR = path.join(DATA_DIR, 'projects');

let mainWindow;
let pythonProcess = null;

// ─── AUTO-START PYTHON BACKEND ───
function startPythonBackend(projectPath = path.join(PROJECTS_DIR, 'default')) {
  if (pythonProcess) {
    pythonProcess.kill();
    pythonProcess = null;
  }

  console.log('[ELECTRON] Starting Python backend:', PYTHON_SCRIPT);
  
  pythonProcess = spawn('python', [PYTHON_SCRIPT, '--brain', projectPath], {
    cwd: PROJECT_ROOT,
    env: { ...process.env, PYTHONUNBUFFERED: '1' }
  });

  pythonProcess.stdout.on('data', (data) => {
    const msg = data.toString().trim();
    console.log('[PYTHON]', msg);
    if (mainWindow) {
      mainWindow.webContents.send('python-log', msg);
    }
  });

  pythonProcess.stderr.on('data', (data) => {
    const msg = data.toString().trim();
    console.error('[PYTHON-ERR]', msg);
    if (mainWindow) {
      mainWindow.webContents.send('python-error', msg);
    }
  });

  pythonProcess.on('close', (code) => {
    console.log(`[ELECTRON] Python exited with code ${code}`);
    pythonProcess = null;
  });

  return pythonProcess;
}

// ─── CREATE WINDOW ───
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1024,
    minHeight: 768,
    title: 'Galaxy-Pilot v5.1',
    icon: path.join(PROJECT_ROOT, 'design', 'screen.png'),
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true
    },
    show: false,
    backgroundColor: '#000000'
  });

  // Load renderer
  const rendererPath = path.join(PROJECT_ROOT, 'renderer', 'index.html');
  mainWindow.loadFile(rendererPath);

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    // Start Python after window is ready
    startPythonBackend();
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
    if (pythonProcess) {
      pythonProcess.kill();
      pythonProcess = null;
    }
  });
}

// ─── IPC HANDLERS ───

// Upload files to project
ipcMain.handle('upload-files', async (event, files, projectName) => {
  const targetDir = path.join(PROJECTS_DIR, projectName, 'inbox');
  fs.mkdirSync(targetDir, { recursive: true });

  const results = [];
  for (const file of files) {
    const targetPath = path.join(targetDir, file.name);
    fs.writeFileSync(targetPath, Buffer.from(file.data));
    results.push({ name: file.name, path: targetPath });
  }

  // Re-run pipeline
  startPythonBackend(targetDir);

  return { imported: results.length, files: results };
});

// Create new project
ipcMain.handle('create-project', async (event, name) => {
  const projectDir = path.join(PROJECTS_DIR, name);
  fs.mkdirSync(projectDir, { recursive: true });
  fs.mkdirSync(path.join(projectDir, 'inbox'), { recursive: true });
  
  // Create empty galaxy_data.json and metadata.json
  fs.writeFileSync(
    path.join(projectDir, 'galaxy_data.json'),
    JSON.stringify({ nodes: {}, edges: [], meta: { node_count: 0, edge_count: 0 } })
  );
  fs.writeFileSync(
    path.join(projectDir, 'metadata.json'),
    JSON.stringify({})
  );

  return { path: projectDir, name };
});

// Get project list
ipcMain.handle('get-projects', async () => {
  fs.mkdirSync(PROJECTS_DIR, { recursive: true });
  const entries = fs.readdirSync(PROJECTS_DIR, { withFileTypes: true });
  return entries
    .filter(e => e.isDirectory())
    .map(e => ({ name: e.name, path: path.join(PROJECTS_DIR, e.name) }));
});

// Select folder dialog
ipcMain.handle('select-folder', async () => {
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openDirectory']
  });
  return result.canceled ? null : result.filePaths[0];
});

// Get app version
ipcMain.handle('get-version', () => {
  return '5.1.0';
});

// ─── APP EVENTS ───
app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (pythonProcess) {
    pythonProcess.kill();
    pythonProcess = null;
  }
  if (process.platform !== 'darwin') app.quit();
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow();
});

// Prevent multiple instances
const gotTheLock = app.requestSingleInstanceLock();
if (!gotTheLock) {
  app.quit();
} else {
  app.on('second-instance', () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.focus();
    }
  });
}
