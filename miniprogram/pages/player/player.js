const StorySocket = require('../../utils/socket')

Page({
  data: { storyId: 'lost-starlight', started: false, state: '准备故事', text: '点击开始进入《迷路的星光》。', progress: 0, showInput: false, canInterrupt: false, message: '', sessionId: '' },
  onLoad(options) {
    this.setData({ storyId: options.id || 'lost-starlight' })
    this.storySocket = new StorySocket()
    this.storySocket.connect(event => this.handleEvent(event), connected => this.setData({ state: connected ? '本地演示已连接' : '服务未连接' }))
  },
  onUnload() { this.storySocket.close() },
  start() { this.setData({ started: true }); this.storySocket.send('start_story', { story_id: this.data.storyId }) },
  interrupt() { this.storySocket.send('interrupt_intent') },
  onInput(e) { this.setData({ message: e.detail.value }) },
  sendMessage() { const text = this.data.message.trim(); if (text) { this.storySocket.send('user_message', { text }); this.setData({ message: '', showInput: false }) } },
  completeAfterReading(type, delay = 2600) { clearTimeout(this.timer); this.timer = setTimeout(() => this.storySocket.send(type), delay) },
  handleEvent(event) {
    if (event.progress !== undefined) this.setData({ progress: event.progress })
    if (event.type === 'session_started') this.setData({ sessionId: event.session_id })
    if (event.type === 'story_sentence') { this.setData({ state: '故事正在讲述', text: event.text, canInterrupt: true, showInput: false }); this.completeAfterReading('sentence_complete') }
    if (event.type === 'interaction_prompt') { clearTimeout(this.timer); this.setData({ state: '轮到你表达', text: event.text, showInput: true, canInterrupt: false }) }
    if (event.type === 'story_paused') { clearTimeout(this.timer); this.setData({ state: '故事已暂停', text: event.text, showInput: true, canInterrupt: false }) }
    if (event.type === 'assistant_answer') { this.setData({ state: 'AI 伙伴回答', text: event.text, showInput: false }); this.completeAfterReading('answer_complete') }
    if (event.type === 'story_end') { getApp().globalData.sessionId = this.data.sessionId; wx.redirectTo({ url: `/pages/report/report?session=${this.data.sessionId}` }) }
    if (event.type === 'error') this.setData({ state: '操作提示', text: event.message })
  }
})
