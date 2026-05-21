import { chatStream } from '../../utils/ws';
import { audioUrl } from '../../utils/api';

const audioCtx = wx.createInnerAudioContext();
let currentPlayIdx = -1;

Page({
  data: {
    messages: [],
    inputText: '',
    sending: false,
    thinking: '',
    playingIndex: -1,
  },

  onInput(e) { this.setData({ inputText: e.detail.value }); },

  send() {
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

    chatStream(text, history, (event) => {
      const allMsgs = this.data.messages;
      const idx = allMsgs.findIndex(m => m.id === placeholderId);

      if (event.type === 'thinking') {
        this.setData({ thinking: event.content });
      } else if (event.type === 'token') {
        if (idx !== -1) {
          allMsgs[idx].content += event.content;
          this.setData({ messages: allMsgs });
        }
      } else if (event.type === 'voice') {
        if (idx !== -1) {
          allMsgs[idx].voiceUrl = event.content;
          this.setData({ messages: allMsgs }, () => this.playAtIndex(idx));
        }
      } else if (event.type === 'done' || event.type === 'closed') {
        this.setData({ sending: false, thinking: '' });
      } else if (event.type === 'error') {
        wx.showToast({ title: event.content, icon: 'none' });
        this.setData({ sending: false, thinking: '' });
      }
    });
  },

  playVoice(e) {
    this.playAtIndex(e.currentTarget.dataset.index);
  },

  playAtIndex(idx) {
    const msg = this.data.messages[idx];
    if (!msg?.voiceUrl) return;

    if (currentPlayIdx === idx && !audioCtx.paused) {
      audioCtx.pause();
      this.setData({ playingIndex: -1 });
      return;
    }

    this.setData({ playingIndex: idx });
    currentPlayIdx = idx;
    audioCtx.src = audioUrl(msg.voiceUrl);
    audioCtx.play();
  },
});
