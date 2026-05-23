// ── AI 女友 · callContainer 版本 ──
App({
  globalData: {
    token: '',
    loginReady: false,
    loginPromise: null,
  },

  onLaunch() {
    // 初始化云开发（连接云托管）
    wx.cloud.init({
      env: 'python-fastapi-d7gdpr87480d51954',  // 云托管控制台 → 环境信息 → 环境ID
    });
    this.doLogin();
  },

  doLogin() {
    this.globalData.loginPromise = new Promise((resolve) => {
      wx.cloud.callContainer({
        config: { env: 'python-fastapi-d7gdpr87480d51954' },
        service: 'ai-backend',
        path: '/api/v1/auth/dev-login',
        method: 'POST',
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
