// ── 小暖 AI 女友 ──
// 前后端分离，MVP 版本
App({
  globalData: {
    apiBase: 'http://localhost:8000',
    wsBase: 'ws://localhost:8000',
  },

  onLaunch() {
    const info = wx.getSystemInfoSync();
    this.globalData.statusBarHeight = info.statusBarHeight;
  },
});
