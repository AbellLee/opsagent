import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import naive from 'naive-ui'
import './styles/global.css'

// 确保Prism.js在全局可用
import Prism from 'prismjs'
window.Prism = Prism

// 全局错误处理
const errorHandler = (err, instance, info) => {
  console.error('Error:', err, instance, info)
}

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(naive)

// 设置全局错误处理
app.config.errorHandler = errorHandler

app.mount('#app')