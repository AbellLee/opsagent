<template>
  <n-layout-header
    bordered
    style="padding: 16px; display: flex; align-items: center; justify-content: space-between;"
  >
    <div>
      <h3 style="margin: 0">{{ currentSession?.session_name || '请选择或新建对话' }}</h3>
      <div style="font-size: 12px; color: #666;">ID: {{ currentSession?.session_id || '无' }}</div>
    </div>

    <!-- 用户菜单 -->
    <UserMenu />
  </n-layout-header>
</template>

<script setup>
import { computed } from 'vue'
import { useSessionStore } from '../stores/session'
import { NLayoutHeader } from 'naive-ui'
import UserMenu from './UserMenu.vue'

const sessionStore = useSessionStore()

// 计算属性：获取当前会话信息
const currentSession = computed(() => {
  try {
    if (!sessionStore.sessions || !sessionStore.sessionId) {
      return { session_name: '请选择或新建对话', session_id: null }
    }
    return sessionStore.sessions.find(s => s.session_id === sessionStore.sessionId) || { session_name: '请选择或新建对话', session_id: null }
  } catch (error) {
    console.warn('获取当前会话信息失败:', error)
    return { session_name: '请选择或新建对话', session_id: null }
  }
})
</script>

<style scoped>
/* Header 美化 */
.n-layout-header {
  background: rgba(255, 255, 255, 0.95) !important;
  backdrop-filter: blur(20px);
  border: none !important;
  box-shadow: 0 4px 32px rgba(0, 0, 0, 0.1);
  border-radius: 0 0 20px 20px !important;
  margin: 0 12px 8px 12px;
  height: 72px !important;
  min-height: 72px !important;
  max-height: 72px !important;
  flex-shrink: 0;
  z-index: 10;
  position: relative;
}

/* 暗色模式美化 */
html.dark .n-layout-header {
  background: rgba(30, 30, 30, 0.95) !important;
  box-shadow: 0 4px 32px rgba(0, 0, 0, 0.3);
}
</style>
