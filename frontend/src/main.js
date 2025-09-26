import { createApp } from 'vue'
import { createPinia } from 'pinia'
import naive from 'naive-ui'

import App from './App.vue'
import router from './router'

// 更全面的ResizeObserver错误处理
const isResizeObserverErr = (err) => {
  if (!err) return false
  const msg = typeof err === 'string' ? err : err.message || ''
  return msg.includes('ResizeObserver loop') || msg.includes('ResizeObserver') || msg.includes('resize')
}

// 全局错误处理
const errorHandler = (err, instance, info) => {
  // 忽略ResizeObserver相关错误
  if (isResizeObserverErr(err)) {
    return
  }
  console.error('Error:', err, instance, info)
}

// 捕获未处理的Promise拒绝
const unhandledrejectionHandler = (event) => {
  if (isResizeObserverErr(event.reason)) {
    event.preventDefault()
    event.stopPropagation()
    return
  }
  console.error('Unhandled promise rejection:', event.reason)
}

// 添加事件监听器
window.addEventListener('error', (event) => {
  if (isResizeObserverErr(event.error)) {
    event.preventDefault()
    event.stopPropagation()
    return
  }
})

window.addEventListener('unhandledrejection', unhandledrejectionHandler)

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(naive)

// 设置全局错误处理
app.config.errorHandler = errorHandler

app.mount('#app')