<template>
  <n-layout content-style="padding: 0;" class="chat-layout">
    <n-card class="chat-card" content-style="padding: 0; display: flex; flex-direction: column;">
      <!-- 头部工具栏 -->
      <div class="chat-header">
        <div class="agent-info">
          <n-avatar round>
            <n-icon>
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2C13.1 2 14 2.9 14 4C14 5.1 13.1 6 12 6C10.9 6 10 5.1 10 4C10 2.9 10.9 2 12 2ZM21 9V7L15 1H5C3.9 1 3 1.9 3 3V7C3 7 3 7 3 7L1 7V9C1 9 1 9 1 9H3V15C3 16.1 3.9 17 5 17H11V19H9C8.4 19 8 19.4 8 20C8 20.6 8.4 21 9 21H15C15.6 21 16 20.6 16 20C16 19.4 15.6 19 15 19H13V17H19C20.1 17 21 16.1 21 15V9H21ZM5 15V8H19V15H5Z"/>
              </svg>
            </n-icon>
          </n-avatar>
          <div class="agent-details">
            <h3>OpsAgent</h3>
            <div class="agent-description">
              智能AI助手
            </div>
          </div>
        </div>
        
        <div class="header-actions">
          <n-tooltip trigger="hover">
            <template #trigger>
              <n-button size="small" tertiary @click="exportChat">
                <n-icon size="16">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 16L16 11H13V4H11V11H8L12 16ZM18 18H6C5.45 18 5 18.45 5 19C5 19.55 5.45 20 6 20H18C18.55 20 19 19.55 19 19C19 18.45 18.55 18 18 18Z"/>
                  </svg>
                </n-icon>
              </n-button>
            </template>
            导出聊天记录
          </n-tooltip>
          
          <n-tooltip trigger="hover">
            <template #trigger>
              <n-button size="small" tertiary @click="clearChat">
                <n-icon size="16">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M7 21Q5.8 21 4.9 20.1Q4 19.2 4 18V6Q4 4.8 4.9 3.9Q5.8 3 7 3H17Q18.2 3 19.1 3.9Q20 4.8 20 6V18Q20 19.2 19.1 20.1Q18.2 21 17 21ZM17 18L18.5 6H16V5Q16 4.58 15.71 4.29Q15.42 4 15 4H9Q8.58 4 8.29 4.29Q8 4.58 8 5V6H5.5L7 18ZM9 16H15L14 9H10Z"/>
                  </svg>
                </n-icon>
              </n-button>
            </template>
            清空聊天记录
          </n-tooltip>
          
          <n-button size="small" type="primary" @click="showAgentInfo = true">
            Agent信息
          </n-button>
        </div>
      </div>
      
      <!-- 消息统计 -->
      <div class="message-stats">
        <div class="stats-info">
          消息: {{ messageStats.total }} (用户: {{ messageStats.user }}, AI: {{ messageStats.assistant }})
        </div>
        <div class="thread-info">
          线程ID: {{ sessionStore.sessionId }}
        </div>
      </div>
      
      <!-- 消息容器 -->
      <div ref="messagesContainer" class="messages-container">
        <div v-if="sessionStore.messages.length === 0" class="empty-messages">
          <n-empty description="暂无消息，开始与AI助手对话吧">
            <template #extra>
              <div class="empty-messages-extra">
                <n-button size="small" @click="sendGreeting">发送问候</n-button>
              </div>
            </template>
          </n-empty>
        </div>
        <ChatMessage 
          v-for="(message, index) in sessionStore.messages" 
          :key="index"
          :message="message"
          class="chat-message"
        />
      </div>
      
      <!-- 输入区域 -->
      <div class="input-container">
        <MessageInput @send="scrollToBottom" class="message-input" />
      </div>
    </n-card>
    
    <!-- Agent信息抽屉 -->
    <n-drawer v-model:show="showAgentInfo" :width="320" placement="right">
      <n-drawer-content title="Agent信息" closable>
        <div class="agent-drawer-content">
          <n-descriptions label-placement="left" :column="1">
            <n-descriptions-item label="名称">
              OpsAgent
            </n-descriptions-item>
            <n-descriptions-item label="版本">
              v1.0.0
            </n-descriptions-item>
            <n-descriptions-item label="描述">
              智能AI助手，能够帮助您处理各种运维任务
            </n-descriptions-item>
            <n-descriptions-item label="功能">
              <n-space>
                <n-tag>日志分析</n-tag>
                <n-tag>系统监控</n-tag>
                <n-tag>故障诊断</n-tag>
                <n-tag>自动化运维</n-tag>
              </n-space>
            </n-descriptions-item>
          </n-descriptions>
        </div>
      </n-drawer-content>
    </n-drawer>
  </n-layout>
</template>

<script setup>
import { ref, onMounted, watch, nextTick, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useSessionStore } from '../stores/session'
import { useUserStore } from '../stores/user'
import { createDiscreteApi } from 'naive-ui'
import ChatMessage from '../components/ChatMessage.vue'
import MessageInput from '../components/MessageInput.vue'

const { message } = createDiscreteApi(['message'])
const router = useRouter()
const sessionStore = useSessionStore()
const userStore = useUserStore()

// 组件状态
const messagesContainer = ref(null)
const showAgentInfo = ref(false)

// 滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

// 组件挂载时的操作
onMounted(() => {
  // 检查用户是否已登录
  if (!userStore.isAuthenticated) {
    message.warning('请先登录')
    router.push('/login')
    return
  }
  
  scrollToBottom()
})

// 监听消息变化，自动滚动到底部
watch(() => sessionStore.messages, () => {
  scrollToBottom()
}, { deep: true })

// 监听消息内容变化，特别是流式输出时
watch(() => sessionStore.messages.map(m => m.content).join(''), () => {
  scrollToBottom()
})

// 计算消息统计
const messageStats = computed(() => {
  const userMessages = sessionStore.messages.filter(m => m.role === 'user').length
  const assistantMessages = sessionStore.messages.filter(m => m.role === 'assistant').length
  return {
    total: sessionStore.messages.length,
    user: userMessages,
    assistant: assistantMessages
  }
})

// 清空聊天记录
const clearChat = () => {
  sessionStore.clearMessages()
  message.success('聊天记录已清空')
}

// 导出聊天记录
const exportChat = () => {
  const chatData = {
    sessionId: sessionStore.sessionId,
    messages: sessionStore.messages,
    timestamp: new Date().toISOString()
  }
  
  const blob = new Blob([JSON.stringify(chatData, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `chat-export-${new Date().getTime()}.json`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
  
  message.success('聊天记录已导出')
}

// 发送问候消息
const sendGreeting = () => {
  sessionStore.addMessage({
    role: 'user',
    content: '你好',
    timestamp: new Date().toISOString()
  })
}
</script>

<style scoped>
.chat-layout {
  height: 100%;
}

.chat-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #eee;
  flex-shrink: 0;
}

.agent-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.agent-details h3 {
  margin: 0;
}

.agent-description {
  font-size: 12px;
  color: #999;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.message-stats {
  padding: 8px 16px;
  background-color: #f8f9fa;
  border-bottom: 1px solid #eee;
  font-size: 12px;
  color: #666;
  display: flex;
  justify-content: space-between;
  flex-shrink: 0;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.empty-messages {
  text-align: center;
  padding: 40px 0;
  color: #999;
}

.empty-messages-extra {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.input-container {
  flex-shrink: 0;
  border-top: 1px solid #eee;
}

/* 滚动条样式 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: transparent;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 4px;
  transition: background 0.3s;
}

::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.2);
}

/* 暗色主题滚动条 */
html.dark ::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
}

html.dark ::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.3);
}
</style>