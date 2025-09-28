const { defineConfig } = require('@vue/cli-service')

module.exports = defineConfig({
  devServer: {
    port: 8080,
    host: 'localhost',
    client: {
      overlay: false
    },
    // 配置 History API fallback 支持 Vue Router
    historyApiFallback: {
      index: '/index.html',
      rewrites: [
        { from: /^\/login$/, to: '/index.html' },
        { from: /^\/register$/, to: '/index.html' },
        { from: /^\/chat$/, to: '/index.html' },
        { from: /./, to: '/index.html' }
      ]
    },
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        logLevel: 'debug'
      }
    }
  },

  // 确保生产环境也支持 History 模式
  publicPath: '/',

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
})