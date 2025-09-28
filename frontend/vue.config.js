module.exports = {
  devServer: {
    client: {
      overlay: false
    },
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      }
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