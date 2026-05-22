import { healthCheck, getCharacters } from '../../utils/api';

Page({
  data: {
    backendOnline: false,
    characters: [],
    activeId: wx.getStorageSync('character_id') || 'sweet',
  },

  onShow() {
    this.checkHealth();
    this.loadCharacters();
  },

  async checkHealth() {
    try { await healthCheck(); this.setData({ backendOnline: true }); }
    catch { this.setData({ backendOnline: false }); }
  },

  async loadCharacters() {
    try {
      const data = await getCharacters();
      this.setData({ characters: data.characters || [] });
    } catch {}
  },

  selectChar(e) {
    const id = e.currentTarget.dataset.id;
    wx.setStorageSync('character_id', id);
    this.setData({ activeId: id });
  },

  goChat() {
    wx.switchTab({ url: '/pages/chat/chat' });
  },
});
