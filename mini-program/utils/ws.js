/**
 * WebSocket 客户端 — 小暖流式对话
 */

const app = getApp();

export function chatStream(message, chatHistory, onEvent) {
  const ws = wx.connectSocket({
    url: (app ? app.globalData.wsBase : 'ws://localhost:8000') + '/ws/v1/gf/chat',
  });

  ws.onOpen(() => {
    ws.send({
      data: JSON.stringify({ message, chat_history: chatHistory }),
    });
  });

  ws.onMessage((res) => {
    try {
      onEvent(JSON.parse(res.data));
    } catch {}
  });

  ws.onError((err) => {
    onEvent({ type: 'error', content: err.errMsg || 'WebSocket 连接失败' });
    ws.close();
  });

  ws.onClose(() => {
    onEvent({ type: 'closed' });
  });
}
