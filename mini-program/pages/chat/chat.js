import { chatStream } from '../../utils/ws';
import { audioUrl, getCharacters, getConversations, getConvMessages } from '../../utils/api';

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
    convId: '',              // 当前会话 ID
    showHistory: false,       // 历史面板
    conversations: [],        // 历史对话列表
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

  // ── 历史 ──
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

    const app = getApp();
    try {
      const data = await getConvMessages(convId, app.globalData.token);
      const msgs = data.messages.map(m => ({
        id: Date.now() + Math.random(),
        role: m.role === 'user' ? 'user' : 'assistant',
        content: m.content,
        voiceUrl: m.voice_url || '',
      }));
      this.setData({ messages: msgs });
    } catch { wx.showToast({ title: '加载消息失败', icon: 'none' }); }
  },

  newConv() {
    this.setData({ messages: [], convId: '', showHistory: false });
  },

  // ── 发送 ──
  onInput(e) { this.setData({ inputText: e.detail.value }); },

  send() {
    const app = getApp();
    if (!app.globalData.token) {
      wx.showToast({ title: '登录中...', icon: 'none' });
      app.globalData.loginPromise?.then(() => this.send());
      return;
    }

    const text = this.data.inputText.trim();
    if (!text || this.data.sending) return;

    const userMsg = { id: Date.now(), role: 'user', content: text };
    const msgs = [...this.data.messages, userMsg];
    this.setData({ messages: msgs, inputText: '', sending: true, thinking: '' });

    const history = msgs.slice(0, -1).map(m => ({ role: m.role, content: m.content }));

    const placeholderId = Date.now() + 1;
    this.setData({
      messages: [...this.data.messages, { id: placeholderId, role: 'assistant', content: '', voiceUrl: '' }],
    });

    const cleanup = chatStream(text, history, (event) => {
      const allMsgs = this.data.messages;
      const idx = allMsgs.findIndex(m => m.id === placeholderId);

      if (event.type === 'conv' && !this.data.convId) {
        this.setData({ convId: event.content });
      } else if (event.type === 'thinking') {
        this.setData({ thinking: event.content });
      } else if (event.type === 'token') {
        if (idx !== -1) { allMsgs[idx].content += event.content; this.setData({ messages: allMsgs }); }
      } else if (event.type === 'voice') {
        if (idx !== -1) { allMsgs[idx].voiceUrl = event.content; this.setData({ messages: allMsgs }, () => this.playAtIndex(idx)); }
      } else if (event.type === 'done' || event.type === 'closed') {
        this.setData({ sending: false, thinking: '' });
        cleanup();
      } else if (event.type === 'error') {
        wx.showToast({ title: event.content, icon: 'none' });
        this.setData({ sending: false, thinking: '' });
        cleanup();
      }
    }, this.data.convId);
  },

  playVoice(e) { this.playAtIndex(e.currentTarget.dataset.index); },

  playAtIndex(idx) {
    const msg = this.data.messages[idx];
    if (!msg?.voiceUrl) return;
    if (currentPlayIdx === idx && !audioCtx.paused) { audioCtx.pause(); this.setData({ playingIndex: -1 }); return; }
    this.setData({ playingIndex: idx }); currentPlayIdx = idx;
    audioCtx.src = audioUrl(msg.voiceUrl);
    audioCtx.play();
  },
});
