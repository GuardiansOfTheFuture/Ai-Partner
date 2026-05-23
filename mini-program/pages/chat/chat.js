// ── callContainer 版本（HTTP，无流式）──
import { sendMessage, getCharacters, getConversations, getConvMessages } from '../../utils/api';

const audioCtx = wx.createInnerAudioContext();
let currentPlayIdx = -1;

Page({
  data: {
    messages: [],
    inputText: '',
    sending: false,
    thinking: '',
    playingIndex: -1,
    aiAvatar: 'tianmei.png',
    aiName: '小糖',
    convId: '',
    showHistory: false,
    conversations: [],
  },

  onShow() { this.loadCharacter(); },

  async loadCharacter() {
    const cid = wx.getStorageSync('character_id') || 'sweet';
    try {
      const data = await getCharacters();
      const chars = data.characters || [];
      const found = chars.find(c => c.id === cid) || chars[0] || {};
      this.setData({ aiAvatar: found.avatar || 'tianmei.png', aiName: found.name || '小糖' });
    } catch {
      const map = { sweet:'tianmei.png', mature:'yujie.png', pure:'qingchun.png', spicy:'lamei.png', mentor:'mentor.jpg' };
      const names = { sweet:'小糖', mature:'若琳', pure:'清禾', spicy:'辣辣', mentor:'亮亮导师' };
      this.setData({ aiAvatar: map[cid] || 'tianmei.png', aiName: names[cid] || '小糖' });
    }
  },

  async loadHistory() {
    const app = getApp();
    if (!app.globalData.token) return;
    try {
      const data = await getConversations(app.globalData.token);
      this.setData({ conversations: data.conversations || [], showHistory: true });
    } catch { wx.showToast({ title: '加载失败', icon: 'none' }); }
  },

  async selectConv(e) {
    const convId = e.currentTarget.dataset.id;
    const name = e.currentTarget.dataset.name || this.data.aiName;
    const avatar = e.currentTarget.dataset.avatar || this.data.aiAvatar;
    this.setData({ showHistory: false, messages: [], convId, aiName: name, aiAvatar: avatar });
    try {
      const data = await getConvMessages(convId, getApp().globalData.token);
      const msgs = data.messages.map(m => ({
        id: Date.now() + Math.random(), role: m.role === 'user' ? 'user' : 'assistant',
        content: m.content, voiceUrl: m.voice_url || '',
      }));
      this.setData({ messages: msgs });
    } catch { wx.showToast({ title: '加载失败', icon: 'none' }); }
  },

  newConv() { this.setData({ messages: [], convId: '', showHistory: false }); },

  onInput(e) { this.setData({ inputText: e.detail.value }); },

  async send() {
    const app = getApp();
    if (!app.globalData.token) {
      wx.showToast({ title: '登录中...', icon: 'none' });
      app.globalData.loginPromise?.then(() => this.send());
      return;
    }
    const text = this.data.inputText.trim();
    if (!text || this.data.sending) return;

    const cid = wx.getStorageSync('character_id') || 'sweet';
    const userMsg = { id: Date.now(), role: 'user', content: text };
    const msgs = [...this.data.messages, userMsg];
    this.setData({ messages: msgs, inputText: '', sending: true, thinking: '' });

    const history = msgs.slice(0, -1).map(m => ({ role: m.role, content: m.content }));

    const placeholderId = Date.now() + 1;
    this.setData({ messages: [...this.data.messages, { id: placeholderId, role: 'assistant', content: '', voiceUrl: '' }] });

    try {
      const result = await sendMessage(text, history, cid);
      const idx = this.data.messages.findIndex(m => m.id === placeholderId);
      if (idx !== -1) {
        const allMsgs = this.data.messages;
        allMsgs[idx].content = result.response;
        allMsgs[idx].voiceUrl = result.voice_url || '';
        this.setData({ messages: allMsgs, sending: false, thinking: result.thinking });
      }
    } catch (e) {
      const idx = this.data.messages.findIndex(m => m.id === placeholderId);
      if (idx !== -1) {
        const allMsgs = this.data.messages;
        allMsgs[idx].content = '小暖走神了...';
        this.setData({ messages: allMsgs, sending: false });
      }
    }
  },
});
