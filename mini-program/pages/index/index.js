import { healthCheck } from '../../utils/api';

Page({
  data: { backendOnline: false },

  onShow() { this.checkHealth(); },

  async checkHealth() {
    try {
      await healthCheck();
      this.setData({ backendOnline: true });
    } catch {
      this.setData({ backendOnline: false });
    }
  },

  goChat() {
    wx.switchTab({ url: '/pages/chat/chat' });
  },
});
