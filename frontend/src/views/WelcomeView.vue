<template>
  <n-layout content-style="padding: 0;" class="welcome-layout">
    <n-card class="welcome-card" content-style="display: flex; flex-direction: column; height: 100%; align-items: center; justify-content: center;">
      <div class="welcome-container">
        <n-avatar :size="80" round>
          <n-icon :size="48">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2C13.1 2 14 2.9 14 4C14 5.1 13.1 6 12 6C10.9 6 10 5.1 10 4C10 2.9 10.9 2 12 2ZM21 9V7L15 1H5C3.9 1 3 1.9 3 3V7C3 7 3 7 3 7L1 7V9C1 9 1 9 1 9H3V15C3 16.1 3.9 17 5 17H11V19H9C8.4 19 8 19.4 8 20C8 20.6 8.4 21 9 21H15C15.6 21 16 20.6 16 20C16 19.4 15.6 19 15 19H13V17H19C20.1 17 21 16.1 21 15V9H21ZM5 15V8H19V15H5Z"/>
            </svg>
          </n-icon>
        </n-avatar>
        <h1 class="welcome-title">欢迎使用 OpsAgent</h1>
        <p class="welcome-description">智能AI助手，帮助您处理各种运维任务</p>
        <div class="welcome-actions">
          <n-button type="primary" size="large" @click="createNewSession">
            <template #icon>
              <n-icon>
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M11 11V5H13V11H19V13H13V19H11V13H5V11H11Z"/>
                </svg>
              </n-icon>
            </template>
            新建对话
          </n-button>
        </div>
        <div class="welcome-features">
          <n-grid :cols="2" :x-gap="20" :y-gap="20">
            <n-grid-item>
              <n-card title="日志分析" size="small">
                <p>快速分析系统日志，定位问题根源</p>
              </n-card>
            </n-grid-item>
            <n-grid-item>
              <n-card title="系统监控" size="small">
                <p>实时监控系统状态，预警潜在风险</p>
              </n-card>
            </n-grid-item>
            <n-grid-item>
              <n-card title="故障诊断" size="small">
                <p>智能诊断系统故障，提供解决方案</p>
              </n-card>
            </n-grid-item>
            <n-grid-item>
              <n-card title="自动化运维" size="small">
                <p>自动执行重复性运维任务，提高效率</p>
              </n-card>
            </n-grid-item>
          </n-grid>
        </div>
      </div>
    </n-card>
  </n-layout>
</template>

<script setup>
import { useSessionStore } from '../stores/session'
import { sessionAPI } from '../api'
import { useUserStore } from '../stores/user'
import { createDiscreteApi } from 'naive-ui'
import { useRouter } from 'vue-router'

const { message } = createDiscreteApi(['message'])
const sessionStore = useSessionStore()
const userStore = useUserStore()
const router = useRouter()

const createNewSession = async () => {
  try {
    const response = await sessionAPI.create({
      user_id: userStore.user?.user_id || 'default_user'
    })
    
    sessionStore.addSession(response)
    sessionStore.setSessionId(response.session_id)
    message.success('新会话创建成功')
  } catch (error) {
    console.error('创建新会话失败:', error)
    message.error('创建新会话失败')
  }
}
</script>

<style scoped>
.welcome-layout {
  height: 100%;
  overflow: hidden;
}

.welcome-card {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.welcome-container {
  max-width: 800px;
  width: 100%;
  text-align: center;
}

.welcome-title {
  margin-top: 20px;
  margin-bottom: 10px;
  font-size: 28px;
  font-weight: 600;
}

.welcome-description {
  color: #666;
  font-size: 16px;
  margin-bottom: 30px;
}

.welcome-actions {
  margin-bottom: 40px;
}

.welcome-features {
  margin-top: 30px;
}

.welcome-features :deep(.n-card__content) {
  padding: 12px !important;
}

.welcome-features :deep(.n-card__content p) {
  margin: 0;
  font-size: 13px;
  color: #666;
}

html.dark .welcome-title {
  color: #fff;
}

html.dark .welcome-description {
  color: #aaa;
}
</style>