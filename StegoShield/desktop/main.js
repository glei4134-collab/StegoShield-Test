const { app, BrowserWindow, ipcMain, shell } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const log = require('electron-log');

log.transports.file.level = 'info';
log.transports.console.level = 'debug';

let mainWindow = null;
let flaskProcess = null;

function getAssetPath(...paths) {
  if (app.isPackaged) {
    return path.join(process.resourcesPath, ...paths);
  }
  return path.join(__dirname, ...paths);
}

function getBackendPath() {
  if (app.isPackaged) {
    return path.join(process.resourcesPath, 'backend');
  }
  return path.join(__dirname, 'backend');
}

function startFlaskBackend() {
  return new Promise((resolve, reject) => {
    const backendPath = getBackendPath();
    const pythonScript = path.join(backendPath, 'run.py');
    
    log.info('Starting Flask backend...');
    log.info('Backend path:', backendPath);
    
    const pythonCmd = process.platform === 'win32' ? 'python' : 'python3';
    
    flaskProcess = spawn(pythonCmd, [pythonScript], {
      cwd: backendPath,
      stdio: ['pipe', 'pipe', 'pipe'],
      shell: true,
      env: { 
        ...process.env, 
        FLASK_DEBUG: 'False',
        FLASK_ENV: 'development'
      }
    });

    let startupComplete = false;

    flaskProcess.stdout.on('data', (data) => {
      const output = data.toString();
      log.info('Flask:', output);
      
      if (!startupComplete && (output.includes('Running on') || output.includes('localhost:5001'))) {
        startupComplete = true;
        log.info('Flask backend started successfully');
        resolve();
      }
    });

    flaskProcess.stderr.on('data', (data) => {
      log.error('Flask error:', data.toString());
    });

    flaskProcess.on('error', (error) => {
      log.error('Failed to start Flask:', error);
      reject(error);
    });

    flaskProcess.on('exit', (code) => {
      log.info('Flask process exited with code:', code);
    });

    setTimeout(() => {
      if (!startupComplete) {
        log.warn('Flask startup timeout, but continuing...');
        resolve();
      }
    }, 10000);
  });
}

async function createWindow() {
  log.info('Creating main window...');

  try {
    await startFlaskBackend();
  } catch (error) {
    log.error('Failed to start Flask backend:', error);
  }

  mainWindow = new BrowserWindow({
    width: 380,
    height: 540,
    minWidth: 380,
    minHeight: 540,
    frame: false,
    transparent: false,
    resizable: false,
    maximizable: false,
    minimizable: true,
    center: true,
    show: false,
    backgroundColor: '#f5f5f5',
    titleBarStyle: 'hidden',
    icon: path.join(__dirname, 'assets', 'icon.png'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
      webSecurity: true,
      allowRunningInsecureContent: false,
      experimentalFeatures: false,
      preload: path.join(__dirname, 'preload.js'),
      sandbox: true
    },
    autoHideMenuBar: true
  });

  await new Promise(resolve => setTimeout(resolve, 2000));
  
  const flaskUrl = 'http://127.0.0.1:5001/';
  log.info('Loading frontend from Flask:', flaskUrl);
  
  mainWindow.loadURL(flaskUrl);

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    log.info('Window shown');
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  mainWindow.on('maximize', () => {
    if (mainWindow) {
      mainWindow.unmaximize();
    }
  });

  mainWindow.webContents.on('will-navigate', (event, url) => {
    const parsedUrl = new URL(url);
    if (parsedUrl.origin !== 'http://127.0.0.1:5001' && parsedUrl.origin !== 'http://localhost:5001') {
      event.preventDefault();
      log.warn('Blocked navigation to:', url);
    }
  });

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    try {
      const parsedUrl = new URL(url);
      if (parsedUrl.protocol === 'https:' || parsedUrl.protocol === 'http:') {
        shell.openExternal(url);
      }
    } catch (e) {
      log.error('Invalid URL:', url);
    }
    return { action: 'deny' };
  });

  app.on('web-contents-created', (event, contents) => {
    contents.on('will-attach-webview', (event, webPreferences) => {
      webPreferences.nodeIntegration = false;
      webPreferences.contextIsolation = true;
      log.info('Webview security settings applied');
    });
  });
}

app.whenReady().then(() => {
  log.info('App ready, creating window...');
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  log.info('All windows closed');
  if (flaskProcess) {
    flaskProcess.kill();
  }
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  log.info('App quitting...');
  if (flaskProcess) {
    flaskProcess.kill();
  }
});

process.on('uncaughtException', (error) => {
  log.error('Uncaught Exception:', error);
  app.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
  log.error('Unhandled Rejection at:', promise, 'reason:', reason);
});

log.info('Main process started');
