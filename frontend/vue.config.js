module.exports = {
  devServer: {
    client: {
      overlay: false
    }
  },
  
  // 其他配置...
  configureWebpack: {
    // 忽略特定的警告或错误
    stats: {
      warningsFilter: [
        'ResizeObserver loop limit exceeded',
        'ResizeObserver loop completed with undelivered notifications'
      ]
    }
  }
}