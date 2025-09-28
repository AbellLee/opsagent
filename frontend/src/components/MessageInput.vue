<template>
  <div class="message-input-container">
    <n-input
      ref="inputRef"
      v-model:value="inputValue"
      type="textarea"
      :autosize="{ minRows: 3, maxRows: 6 }"
      placeholder="输入消息..."
      @keydown="handleKeydown"
    />
    <div class="input-actions">
      <div class="quick-prompts">
        <n-button 
          v-for="prompt in quickPrompts" 
          :key="prompt.text"
          text 
          size="tiny"
          @click="useQuickPrompt(prompt)"
        >
          {{ prompt.label }}
        </n-button>
      </div>
      <n-button 
        type="primary" 
        @click="sendMessage"
        :disabled="!inputValue || !inputValue.trim() || sending"
        :loading="sending"
      >
        发送
      </n-button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useSessionStore } from '../stores/session'
import { messageAPI } from '../api'
import { createDiscreteApi } from 'naive-ui'
import { NInput, NButton } from 'naive-ui'

const { message } = createDiscreteApi(['message'])

const emit = defineEmits(['send'])

const sessionStore = useSessionStore()

const inputValue = ref('')
const sending = ref(false)
const inputRef = ref(null)

const quickPrompts = [
  { label: '你好', text: '你好' },
  { label: '系统状态', text: '请检查系统状态' },
  { label: '帮助', text: '你能帮我做什么？' }
]

const handleKeydown = (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

const sendMessage = async () => {
  if (!inputValue.value || !inputValue.value.trim() || sending.value) return

  try {
    sending.value = true
    
    // 添加用户消息到状态
    const userMessage = {
      role: 'user',
      content: inputValue.value,
      timestamp: new Date().toISOString()
    }
    
    sessionStore.addMessage(userMessage)
    
    // 清空输入框
    inputValue.value = ''
    
    // 触发父组件滚动到底部
    emit('send')
    
    // 发送消息到后端
    const response = await messageAPI.send(sessionStore.sessionId, {
      message: userMessage.content
    })
    
    // 添加助手消息到状态
    const assistantMessage = {
      role: 'assistant',
      content: response.response,
      timestamp: new Date().toISOString()
    }
    
    sessionStore.addMessage(assistantMessage)
    
    // 触发父组件滚动到底部
    emit('send')
  } catch (error) {
    console.error('发送消息失败:', error)
    message.error('发送消息失败')
  } finally {
    sending.value = false
  }
}

const useQuickPrompt = (prompt) => {
  inputValue.value = prompt.text
  inputRef.value?.focus()
}

onMounted(() => {
  inputRef.value?.focus()
})
</script>

<style scoped>
.message-input-container {
  padding: 16px;
}

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
}

.quick-prompts {
  display: flex;
  gap: 8px;
}
</style>