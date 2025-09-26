<template>
  <div class="message-input-container">
    <!-- 快速提示 -->
    <div v-if="showQuickPrompts && !inputMessage" class="quick-prompts">
      <div class="quick-prompts-title">快速开始:</div>
      <div class="quick-prompts-list">
        <n-button 
          v-for="(prompt, index) in quickPrompts" 
          :key="index"
          size="small" 
          secondary 
          @click="sendQuickPrompt(prompt)"
          class="quick-prompt-button"
        >
          {{ prompt }}
        </n-button>
      </div>
    </div>
    
    <!-- 输入区域 -->
    <div class="input-area">
      <n-input 
        v-model:value="inputMessage"
        type="textarea"
        placeholder="输入消息... (按Enter发送，Shift+Enter换行)"
        :autosize="{ minRows: 2, maxRows: 6 }"
        :disabled="loading"
        @keydown="handleKeyDown"
        class="message-textarea"
      />
      
      <div class="input-actions">
        <div class="input-actions-left">
          <n-button 
            text 
            size="small" 
            @click="showAdvancedOptions = !showAdvancedOptions"
            class="advanced-options-button"
          >
            <n-icon size="16">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 15.5C13.93 15.5 15.5 13.93 15.5 12C15.5 10.07 13.93 8.5 12 8.5C10.07 8.5 8.5 10.07 8.5 12C8.5 13.93 10.07 15.5 12 15.5ZM12 17C9.24 17 7 14.76 7 12C7 9.24 9.24 7 12 7C14.76 7 17 9.24 17 12C17 14.76 14.76 17 12 17ZM12 4C9.29 4 6.84 5.09 5 6.84L6.41 8.25C7.87 6.97 9.83 6.25 12 6.25C14.17 6.25 16.13 6.97 17.59 8.25L19 6.84C17.16 5.09 14.71 4 12 4ZM12 19.75C9.83 19.75 7.87 19.03 6.41 17.75L5 19.16C6.84 20.91 9.29 22 12 22C14.71 22 17.16 20.91 19 19.16L17.59 17.75C16.13 19.03 14.17 19.75 12 19.75Z"/>
              </svg>
            </n-icon>
            高级选项
          </n-button>
          
          <n-tag v-if="toolCount > 0" size="small" type="info">
            {{ toolCount }} 个可用工具
          </n-tag>
        </div>
        
        <div class="input-actions-right">
          <n-checkbox 
            v-if="showAdvancedOptions" 
            v-model:checked="useStreaming" 
            :disabled="loading"
            size="small"
            class="streaming-checkbox"
          >
            流式输出
          </n-checkbox>
          
          <n-button 
            type="primary" 
            :loading="loading"
            @click="sendMessage"
            :disabled="!canSendMessage"
            class="send-button"
          >
            <template #icon>
              <n-icon size="16">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M3 20V4L22 12L3 20ZM5 17L16.85 12L5 7V10.5L11 12L5 13.5V17Z"/>
                </svg>
              </n-icon>
            </template>
            发送
          </n-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useSessionStore } from '../stores/session'
import { useToolStore } from '../stores/tool'
import { useUserStore } from '../stores/user'
import { sessionAPI } from '../api'

const emit = defineEmits(['send'])

const sessionStore = useSessionStore()
const toolStore = useToolStore()
const userStore = useUserStore()

// 输入的消息
const inputMessage = ref('')
const loading = ref(false)
const useStreaming = ref(true) // 默认使用流式输出
const showAdvancedOptions = ref(false)
const showQuickPrompts = ref(true)

// 计算是否可以发送消息
const canSendMessage = computed(() => {
  return inputMessage.value.trim() && !loading.value
})

// 计算工具数量
const toolCount = computed(() => {
  return toolStore.tools.length
})

// 发送消息
const sendMessage = async () => {
  if (!canSendMessage.value) return
  
  const message = inputMessage.value.trim()
  inputMessage.value = ''
  loading.value = true
  
  try {
    // 添加用户消息到显示
    sessionStore.addMessage({
      role: 'user',
      content: message,
      timestamp: new Date().toISOString()
    })
    
    // 触发父组件的send事件
    emit('send')
    
    // 检查是否有会话ID
    if (!sessionStore.sessionId) {
      // 创建新会话
      const response = await sessionAPI.create({
        user_id: userStore.userProfile?.user_id || 'default_user'
      })
      sessionStore.setSessionId(response.session_id)
    }
    
    // 调用聊天API
    const response = await sessionAPI.sendMessage(sessionStore.sessionId, {
      message: message
    })
    
    // 添加AI回复到显示
    sessionStore.addMessage({
      role: 'assistant',
      content: response.response,
      timestamp: new Date().toISOString()
    })
    
    loading.value = false
  } catch (error) {
    console.error('发送消息失败:', error)
    sessionStore.addMessage({
      role: 'assistant',
      content: '抱歉，发送消息时出现错误: ' + (error.response?.data?.detail || error.message || JSON.stringify(error)),
      timestamp: new Date().toISOString()
    })
    loading.value = false
  }
}

// 按回车发送消息
const handleKeyDown = (event) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    sendMessage()
  }
}

// 快速提示
const quickPrompts = [
  "你好，介绍一下你自己",
  "你能帮我做什么？",
  "给我展示一个代码示例"
]

// 发送快速提示
const sendQuickPrompt = (prompt) => {
  inputMessage.value = prompt
  sendMessage()
}
</script>

<style scoped>
.message-input-container {
  padding: 12px;
}

.quick-prompts {
  margin-bottom: 12px;
}

.quick-prompts-title {
  font-size: 12px;
  color: #999;
  margin-bottom: 8px;
}

.quick-prompts-list {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.quick-prompt-button {
  font-size: 12px;
}

.input-area {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.message-textarea {
  flex: 1;
}

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.input-actions-left {
  display: flex;
  gap: 8px;
  align-items: center;
}

.input-actions-right {
  display: flex;
  gap: 8px;
  align-items: center;
}

.advanced-options-button {
  font-size: 12px;
}

.streaming-checkbox {
  font-size: 12px;
}

.send-button {
  border-radius: 6px;
}
</style>