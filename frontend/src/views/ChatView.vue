<template>
  <div class="chat-view-container">
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
        :isStreaming="isLastMessageStreaming && index === sessionStore.messages.length - 1"
        class="chat-message"
      />
    </div>

    <!-- 输入区域 -->
    <div class="input-container">
      <MessageInput
        @send="scrollToBottom"
        @streaming-start="isLastMessageStreaming = true"
        @streaming-end="isLastMessageStreaming = false"
        class="message-input"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useSessionStore } from '../stores/session'
import { useUserStore } from '../stores/user'
import { createDiscreteApi } from 'naive-ui'
import { messageAPI } from '../api'
import ChatMessage from '../components/ChatMessage.vue'
import MessageInput from '../components/MessageInput.vue'

const { message } = createDiscreteApi(['message'])
const router = useRouter()
const sessionStore = useSessionStore()
const userStore = useUserStore()

// 组件状态
const messagesContainer = ref(null)
const isLastMessageStreaming = ref(false)

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
watch(() => sessionStore.messages.map(m => m?.content || '').join(''), () => {
  scrollToBottom()
})

// 创建消息的辅助函数
const createMessage = (role, content) => ({
  role,
  content,
  timestamp: new Date().toISOString()
})

// 发送消息并获取AI回复
const sendMessageAndGetReply = async (messageContent) => {
  try {
    // 检查是否有会话ID
    if (!sessionStore.sessionId) {
      message.error('请先选择或创建一个会话')
      return
    }

    // 添加用户消息
    const userMessage = createMessage('user', messageContent)
    sessionStore.addMessage(userMessage)
    scrollToBottom()

    // 发送消息到后端获取AI回复
    const response = await messageAPI.send(sessionStore.sessionId, {
      message: messageContent
    })

    // 添加AI回复
    if (response && response.response) {
      const assistantMessage = createMessage('assistant', response.response)
      sessionStore.addMessage(assistantMessage)
      scrollToBottom()
    }
  } catch (error) {
    console.error('发送消息失败:', error)
    message.error('发送消息失败，请重试')
  }
}

// 发送问候消息
const sendGreeting = async () => {
  await sendMessageAndGetReply('你好！很高兴认识你 👋')
}

// 发送示例问题
const sendExample = async () => {
  const examples = [
    '请帮我解释一下什么是人工智能？',
    '能给我推荐一些学习编程的资源吗？',
    '如何提高工作效率？',
    '请介绍一下最新的科技趋势',
    '能帮我制定一个学习计划吗？'
  ]

  const randomExample = examples[Math.floor(Math.random() * examples.length)]
  await sendMessageAndGetReply(randomExample)
}
</script>

<style scoped>
.chat-view-container {
  height: 100%;
  width: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 20px;
  height: calc(100% - 120px); /* 减去输入区域高度 */
  min-height: 0; /* 允许flex子项收缩 */
}

/* 美化滚动条 */
.messages-container::-webkit-scrollbar {
  width: 6px;
}

.messages-container::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.05);
  border-radius: 3px;
}

.messages-container::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 3px;
  transition: all 0.3s ease;
}

.messages-container::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(135deg, #5a6fd8 0%, #6a4c93 100%);
}

.empty-messages {
  text-align: center;
  padding: 60px 20px;
  color: #999;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
}

.empty-messages-extra {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  margin-top: 20px;
}

.input-container {
  flex-shrink: 0;
  border-top: 1px solid rgba(0, 0, 0, 0.08);
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  padding: 0;
  position: relative;
  z-index: 10;
}

.chat-message {
  margin-bottom: 16px;
}

.chat-message:last-child {
  margin-bottom: 0;
}

/* 暗色模式 */
html.dark .messages-container::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.05);
}

html.dark .messages-container::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, #4a5568 0%, #2d3748 100%);
}

html.dark .messages-container::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

html.dark .input-container {
  background: rgba(30, 30, 30, 0.95);
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

html.dark .empty-messages {
  color: #9ca3af;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .messages-container {
    padding: 16px;
    height: calc(100% - 100px);
  }

  .empty-messages {
    padding: 40px 16px;
  }
}
</style>