// ── AI 女友 · 生产环境 ──
App({
  globalData: {
    apiBase: 'https://ai-backend-261153-4-1436055608.sh.run.tcloudbase.com',
    wsBase: 'wss://ai-backend-261153-4-1436055608.sh.run.tcloudbase.com',
    token: '',
    loginReady: false,
    loginPromise: null,
  },

  onLaunch() {
    this.doLogin();
  },

  doLogin() {
    this.globalData.loginPromise = new Promise((resolve) => {
      wx.request({
        method: 'POST',
        url: this.globalData.apiBase + '/api/v1/auth/dev-login',
        data: { device_id: 'dev-' + Date.now() },
        success: (res) => {
          if (res.statusCode === 200 && res.data.token) {
            this.globalData.token = res.data.token;
            this.globalData.loginReady = true;
            wx.setStorageSync('auth_token', res.data.token);
          } else {
            setTimeout(() => this.doLogin(), 3000);
          }
          resolve();
        },
        fail: () => {
          setTimeout(() => this.doLogin(), 3000);
          resolve();
        },
      });
    });
  },
});
