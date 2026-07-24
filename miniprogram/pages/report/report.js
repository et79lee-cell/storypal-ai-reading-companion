const { baseUrl } = require('../../utils/config')
Page({ data: { report: {} }, onLoad(options) { wx.request({ url: `${baseUrl()}/api/reports/${options.session}`, success: ({ data }) => this.setData({ report: data }) }) } })
