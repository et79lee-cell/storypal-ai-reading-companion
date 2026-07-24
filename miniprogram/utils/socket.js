const { wsUrl } = require('./config')

class StorySocket {
  connect(onMessage, onState) {
    this.socket = wx.connectSocket({ url: wsUrl() })
    this.socket.onOpen(() => onState && onState(true))
    this.socket.onClose(() => onState && onState(false))
    this.socket.onMessage(({ data }) => onMessage(JSON.parse(data)))
    this.socket.onError(() => onState && onState(false))
  }
  send(type, payload = {}) {
    this.socket.send({ data: JSON.stringify({ type, ...payload }) })
  }
  close() { if (this.socket) this.socket.close() }
}

module.exports = StorySocket
