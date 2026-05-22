// ── AI 女友 ──
App({
  globalData: {
    apiBase: 'http://localhost:8000',
    wsBase: 'ws://localhost:8000',
    token: '',
    loginReady: false,
    loginPromise: null,
  },

  onLaunch() {
    this.detectEnv();
    this.doLogin();
  },

  detectEnv() {
    const info = wx.getSystemInfoSync();
    // 真机用局域网 IP，模拟器用 localhost
    if (info.platform !== 'devtools') {
      this.globalData.apiBase = 'http://192.168.2.8:8000';
      this.globalData.wsBase = 'ws://192.168.2.8:8000';
    }
    this.globalData.statusBarHeight = info.statusBarHeight;
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
            console.log('登录成功');
          } else {
            console.error('登录失败, 3s后重试');
            setTimeout(() => this.doLogin(), 3000);
          }
          resolve();
        },
        fail: (err) => {
          console.error('登录请求失败, 3s后重试', err);
          setTimeout(() => this.doLogin(), 3000);
          resolve();
        },
      });
    });
  },
});
