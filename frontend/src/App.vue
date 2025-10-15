<template>
  <n-config-provider :locale="zhCN" :date-locale="dateZhCN">
    <n-message-provider>
      <n-layout style="height: 100vh; overflow: hidden;">
        <!-- 只在用户已登录时显示 header -->
        <AppHeader v-if="userStore.isAuthenticated" />

        <n-layout has-sider class="main-content-layout">
          <!-- 侧边栏 -->
          <AppSidebar v-if="userStore.isAuthenticated" />

          <n-layout-content class="main-content-area">
            <!-- 只有在已登录且没有选择会话时显示欢迎页面 -->
            <WelcomeView v-if="userStore.isAuthenticated && (!sessionStore.sessionId || sessionStore.sessionId === '')" />
            <!-- 已登录且有会话时显示聊天视图 -->
            <ChatView v-else-if="userStore.isAuthenticated && sessionStore.sessionId" />
            <!-- 未登录时显示路由视图（登录/注册页面） -->
            <router-view v-else />
          </n-layout-content>
        </n-layout>
      </n-layout>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup>
import { onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from './stores/user'
import { useSessionStore } from './stores/session'
import { sessionAPI } from './api'
import WelcomeView from './views/WelcomeView.vue'
import ChatView from './views/ChatView.vue'
import AppHeader from './components/AppHeader.vue'
import AppSidebar from './components/AppSidebar.vue'
import {
  NLayout,
  NLayoutContent,
  NConfigProvider
} from 'naive-ui'
import { zhCN, dateZhCN } from 'naive-ui'
import { createDiscreteApi } from 'naive-ui'

const router = useRouter()
const userStore = useUserStore()
const sessionStore = useSessionStore()
const { message } = createDiscreteApi(['message'])



// 监听用户认证状态变化
watch(() => userStore.isAuthenticated, async (isAuthenticated, wasAuthenticated) => {
  console.log('用户认证状态变化:', { isAuthenticated, wasAuthenticated })

  if (isAuthenticated && !wasAuthenticated) {
    // 用户刚刚登录，加载会话列表
    console.log('用户刚刚登录，开始加载会话数据')
    try {
      await loadSessions()
      console.log('登录后会话数据加载完成')
    } catch (error) {
      console.error('登录后加载会话数据失败:', error)
    }
  } else if (!isAuthenticated && wasAuthenticated) {
    // 用户刚刚退出登录，清空会话数据
    console.log('用户退出登录，清空会话数据')
    sessionStore.resetSession()
  }
}, { immediate: false })

// 监听路由变化，确保在访问聊天页面时加载会话列表
watch(() => router.currentRoute.value.path, async (newPath, oldPath) => {
  if (newPath === '/chat' && userStore.isAuthenticated) {
    // 如果会话列表为空，则加载
    if (!sessionStore.sessions || sessionStore.sessions.length === 0) {
      try {
        await loadSessions()
      } catch (error) {
        console.error('路由变化后加载会话数据失败:', error)
      }
    }
  }
}, { immediate: true })

// 初始化用户状态
onMounted(async () => {
  try {
    console.log('应用初始化开始')

    // 初始化用户状态
    userStore.initializeFromStorage()
    console.log('用户状态初始化完成:', userStore.isAuthenticated)

    // 确保 sessionStore 有默认值
    if (!sessionStore.sessions) {
      sessionStore.setSessions([])
    }

    // 如果用户已登录，加载会话数据
    if (userStore.isAuthenticated) {
      console.log('用户已登录，开始加载会话数据')
      await loadSessions()
    } else {
      console.log('用户未登录，跳过会话数据加载')
    }

    console.log('应用初始化完成')
  } catch (error) {
    console.error('应用初始化失败:', error)
  }
})

// 加载会话列表
const loadSessions = async () => {
  try {
    const userId = userStore.user?.user_id
    if (userId) {
      const sessions = await sessionAPI.list(userId)
      sessionStore.setSessions(sessions)
    }
  } catch (error) {
    console.error('加载会话列表失败:', error)
    message.error('加载会话列表失败: ' + (error.response?.data?.detail || error.message))
  }
}

// 强制刷新会话列表（供外部调用）
const refreshSessions = async () => {
  if (userStore.isAuthenticated) {
    await loadSessions()
  }
}

// 暴露给全局使用
window.refreshSessions = refreshSessions




</script>

<style>
@import './styles/global.css';
</style>