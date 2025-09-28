<template>
  <n-layout content-style="padding: 0;" class="chat-layout">
    <n-card class="chat-card" content-style="padding: 0; display: flex; flex-direction: column; height: 100%;">
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
  
  // 检查是否选择了会话
  if (!sessionStore.sessionId) {
    // 如果没有选择会话，不执行任何操作，让父组件显示欢迎页面
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
  overflow: hidden;
}

.chat-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  /* 隐藏滚动条但仍可滚动 */
  scrollbar-width: none; /* Firefox */
  -ms-overflow-style: none; /* IE/Edge */
}

/* 隐藏 Webkit 浏览器的滚动条 */
.messages-container::-webkit-scrollbar {
  width: 0 !important;
  height: 0 !important;
  display: none;
  background: transparent;
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
  position: sticky;
  bottom: 0;
  background: white;
  padding: 0;
}

html.dark .input-container {
  background: #1e1e20;
  border-top: 1px solid #333;
}
</style>