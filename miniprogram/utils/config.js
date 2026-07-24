const DEFAULT_BASE_URL = 'http://127.0.0.1:8000'

function baseUrl() {
  return wx.getStorageSync('storypalBaseUrl') || DEFAULT_BASE_URL
}

function wsUrl() {
  return baseUrl().replace(/^http/, 'ws') + '/ws/miniapp'
}

module.exports = { baseUrl, wsUrl }
