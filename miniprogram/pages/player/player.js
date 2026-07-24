const StorySocket = require('../../utils/socket')

Page({
  data: { storyId: 'lost-starlight', started: false, state: '准备故事', text: '点击开始进入《迷路的星光》。', progress: 0, showInput: false, allowSkip: false, canInterrupt: false, message: '', sessionId: '' },
  onLoad(options) {
    this.setData({ storyId: options.id || 'lost-starlight' })
    this.storySocket = new StorySocket()
    this.storySocket.connect(event => this.handleEvent(event), connected => this.setData({ state: connected ? '本地演示已连接' : '服务未连接' }))
  },
  onUnload() { this.storySocket.close() },
  start() { this.setData({ started: true }); this.storySocket.send('start_story', { story_id: this.data.storyId }) },
  interrupt() { this.storySocket.send('interrupt_intent') },
  skipQuestion() { this.storySocket.send('skip_proactive_question'); this.setData({ showInput: false, allowSkip: false }) },
  onInput(e) { this.setData({ message: e.detail.value }) },
  sendMessage() { const text = this.data.message.trim(); if (text) { this.storySocket.send('user_message', { text }); this.setData({ message: '', showInput: false }) } },
  completeAfterReading(type, delay = 2600) { clearTimeout(this.timer); this.timer = setTimeout(() => this.storySocket.send(type), delay) },
  handleEvent(event) {
    if (event.progress !== undefined) this.setData({ progress: event.progress })
    if (event.type === 'session_started') this.setData({ sessionId: event.session_id })
    if (event.type === 'story_sentence') { this.setData({ state: '故事正在讲述 · 可以随时打断', text: event.text, canInterrupt: true, showInput: false, allowSkip: false }); this.completeAfterReading('sentence_complete') }
    if (event.type === 'proactive_question') { clearTimeout(this.timer); this.setData({ state: `AI 主动提问 · ${(event.dimension_labels || []).join(' × ')}`, text: event.text, showInput: true, allowSkip: event.skip_allowed, canInterrupt: false }) }
    if (event.type === 'story_paused') { clearTimeout(this.timer); this.setData({ state: '用户打断提问 · 故事已暂停', text: event.text, showInput: true, allowSkip: false, canInterrupt: false }) }
    if (event.type === 'assistant_answer') { const moduleName = event.interaction_module === 'ai_proactive_question' ? '主动提问回应' : '打断问题回应'; this.setData({ state: `AI 伙伴回答 · ${moduleName}`, text: event.text, showInput: false, allowSkip: false }); this.completeAfterReading('answer_complete') }
    if (event.type === 'story_end') { getApp().globalData.sessionId = this.data.sessionId; wx.redirectTo({ url: `/pages/report/report?session=${this.data.sessionId}` }) }
    if (event.type === 'error') this.setData({ state: '操作提示', text: event.message })
  }
})
