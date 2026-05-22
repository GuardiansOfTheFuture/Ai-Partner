const app = getApp();

function getBase() {
  return app ? app.globalData.apiBase : 'http://localhost:8000';
}

function request(method, path, data) {
  return new Promise((resolve, reject) => {
    wx.request({
      method,
      url: getBase() + path,
      header: { 'Content-Type': 'application/json' },
      data,
      success(res) {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data);
        } else {
          reject(new Error(res.data?.detail || `HTTP ${res.statusCode}`));
        }
      },
      fail(err) { reject(new Error(err.errMsg || '网络请求失败')); },
    });
  });
}

export function healthCheck() { return request('GET', '/api/v1/health'); }
export function getCharacters() { return request('GET', '/api/v1/gf/characters'); }
export function sendMessage(message, chatHistory = []) {
  return request('POST', '/api/v1/gf/chat', { message, chat_history: chatHistory });
}

/** 对话历史 */
export function getConversations(token) {
  return request('GET', '/api/v1/gf/conversations?token=' + encodeURIComponent(token));
}
export function getConvMessages(convId, token) {
  return request('GET', '/api/v1/gf/conversations/' + convId + '/messages?token=' + encodeURIComponent(token));
}

/** 拼接完整音频地址 */
export function audioUrl(path) {
  return getBase() + path;
}
