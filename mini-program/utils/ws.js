/**
 * WebSocket — 复用连接，遵循微信并发限制
 */

const app = getApp();
let ws = null;
let pendingCallbacks = [];

function ensureConnection() {
  if (ws && ws.readyState === 1) return;  // 已连接

  ws = wx.connectSocket({
    url: (app ? app.globalData.wsBase : 'ws://localhost:8000') + '/ws/v1/gf/chat',
  });

  ws.onMessage((res) => {
    try { pendingCallbacks.forEach(cb => cb(JSON.parse(res.data))); }
    catch {}
  });

  ws.onClose(() => { ws = null; });
}

export function chatStream(message, chatHistory, onEvent, convId) {
  // 注册回调（支持多个消息排队）
  pendingCallbacks.push(onEvent);

  ensureConnection();

  // 等连接就绪后发消息
  const send = () => {
    if (ws && ws.readyState === 1) {
      ws.send({ data: JSON.stringify({
        token: app ? app.globalData.token : '',
        message,
        chat_history: chatHistory,
        character_id: wx.getStorageSync('character_id') || 'sweet',
        conversation_id: convId || '',
      })});
    } else {
      // 还在连接中，等 open 事件
      const check = setInterval(() => {
        if (ws && ws.readyState === 1) {
          clearInterval(check);
          ws.send({ data: JSON.stringify({
            token: app ? app.globalData.token : '',
            message,
            chat_history: chatHistory,
            character_id: wx.getStorageSync('character_id') || 'sweet',
            conversation_id: convId || '',
          })});
        }
      }, 100);
      // 超时保护
      setTimeout(() => clearInterval(check), 5000);
    }
  };

  if (ws && ws.readyState === 1) { send(); }
  else { ws.onOpen(() => send()); }

  // 返回清理函数
  return () => {
    pendingCallbacks = pendingCallbacks.filter(cb => cb !== onEvent);
  };
}
