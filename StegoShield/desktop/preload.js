const { contextBridge, ipcRenderer } = require('electron');

// 暴露安全的API给渲染进程
contextBridge.exposeInMainWorld('electronAPI', {
  // 获取应用信息
  getAppInfo: () => {
    return {
      platform: process.platform,
      version: require('./package.json').version
    };
  },

  // 打开外部链接
  openExternal: (url) => {
    require('electron').shell.openExternal(url);
  },

  // 最小化窗口
  minimizeWindow: () => {
    ipcRenderer.send('minimize-window');
  },

  // 最大化窗口
  maximizeWindow: () => {
    ipcRenderer.send('maximize-window');
  },

  // 关闭应用
  quitApp: () => {
    ipcRenderer.send('quit-app');
  },

  // 监听窗口状态变化
  onWindowStateChange: (callback) => {
    ipcRenderer.on('window-state-changed', (event, state) => {
      callback(state);
    });
  }
});

console.log('Preload script loaded');
