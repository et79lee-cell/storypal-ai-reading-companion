const { baseUrl } = require('../../utils/config')

Page({
  data: { stories: [], error: '' },
  onLoad() {
    wx.request({
      url: `${baseUrl()}/api/stories`,
      success: ({ data }) => this.setData({ stories: data }),
      fail: () => this.setData({
        stories: [{ id: 'lost-starlight', title: '迷路的星光', emoji: '🌟', age_range: '6–10 岁', summary: '跟随一颗落进森林的小星星，练习观察与表达。' }],
        error: '未连接本地服务，当前显示内置目录。请按 README 启动 backend。'
      })
    })
  },
  openStory(e) { wx.navigateTo({ url: `/pages/player/player?id=${e.currentTarget.dataset.id}` }) }
})
