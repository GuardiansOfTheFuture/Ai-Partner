// ── callContainer 版本 ──

const ENV = 'python-fastapi-d7gdpr87480d51954';

function request(method, path, data) {
  return new Promise((resolve, reject) => {
    wx.cloud.callContainer({
      config: { env: ENV },
      service: 'ai-backend',
      path,
      method,
      header: { 'Content-Type': 'application/json' },
      data,
      success(res) {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data);
        } else {
          reject(new Error(res.data?.detail || `HTTP ${res.statusCode}`));
        }
      },
      fail(err) { reject(new Error(err.errMsg || '请求失败')); },
    });
  });
}

export function healthCheck() { return request('GET', '/api/v1/health'); }
export function getCharacters() { return request('GET', '/api/v1/gf/characters'); }
export function sendMessage(message, chatHistory = [], characterId = 'sweet') {
  return request('POST', '/api/v1/gf/chat', { message, character_id: characterId, chat_history: chatHistory });
}
export function getConversations(token) {
  return request('GET', '/api/v1/gf/conversations?token=' + encodeURIComponent(token));
}
export function getConvMessages(convId, token) {
  return request('GET', '/api/v1/gf/conversations/' + convId + '/messages?token=' + encodeURIComponent(token));
}
export function audioUrl(path) { return ''; } // callContainer 不支持音频文件直链
