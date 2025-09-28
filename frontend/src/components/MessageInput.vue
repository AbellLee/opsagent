<template>
  <div class="message-input-wrapper">
    <div class="input-container">
      <!-- 输入框 -->
      <div class="textarea-wrapper">
        <n-input
          ref="inputRef"
          v-model:value="inputValue"
          type="textarea"
          :autosize="{ minRows: 1, maxRows: 6 }"
          :placeholder="placeholder"
          :maxlength="maxLength"
          :show-count="false"
          class="message-textarea"
          @keydown="handleKeyDown"
        />

        <!-- 发送按钮 -->
        <div class="send-button-wrapper">
          <n-button
            type="primary"
            circle
            size="medium"
            @click="sendMessage"
            :disabled="isSendDisabled"
            :loading="sending"
            class="send-button"
          >
            <template #icon>
              <n-icon size="18">
                <svg viewBox="0 0 24 24" fill="currentColor">
                  <path d="M2,21L23,12L2,3V10L17,12L2,14V21Z"/>
                </svg>
              </n-icon>
            </template>
          </n-button>
        </div>
      </div>

      <!-- 字数统计 -->
      <div class="char-count-wrapper">
        <span class="char-count" :class="{ warning: isNearLimit, error: isOverLimit }">
          {{ inputValue.length }}/{{ maxLength }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useSessionStore } from '../stores/session'
import { messageAPI } from '../api'
import { createDiscreteApi } from 'naive-ui'

// Constants
const MESSAGE_ROLE = {
  USER: 'user',
  ASSISTANT: 'assistant'
}

// Emits
const emit = defineEmits(['send'])

// Store and API
const { message: notification } = createDiscreteApi(['message'])
const sessionStore = useSessionStore()

// Reactive data
const inputValue = ref('')
const sending = ref(false)
const inputRef = ref(null)

// Configuration
const maxLength = ref(2000)
const placeholder = ref('有什么我能帮您的吗？')

// Computed properties
const isSendDisabled = computed(() => {
  return !inputValue.value?.trim() || sending.value || isOverLimit.value
})

const isNearLimit = computed(() => {
  return inputValue.value.length > maxLength.value * 0.8
})

const isOverLimit = computed(() => {
  return inputValue.value.length > maxLength.value
})

// Event handlers
const handleKeyDown = (event) => {
  // Enter 发送消息（不按 Shift）
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    sendMessage()
  }
}

// Methods
const createMessage = (role, content) => ({
  role,
  content,
  timestamp: new Date().toISOString()
})

const sendMessage = async () => {
  if (isSendDisabled.value) return

  const messageContent = inputValue.value.trim()
  if (!messageContent) return

  try {
    sending.value = true

    // 创建并添加用户消息
    const userMessage = createMessage(MESSAGE_ROLE.USER, messageContent)
    sessionStore.addMessage(userMessage)

    // 清空输入框
    inputValue.value = ''

    // 通知父组件滚动到底部
    emit('send')

    // 发送消息到后端
    const response = await messageAPI.send(sessionStore.sessionId, {
      message: messageContent
    })

    // 创建并添加助手消息
    const assistantMessage = createMessage(MESSAGE_ROLE.ASSISTANT, response.response)
    sessionStore.addMessage(assistantMessage)

    // 再次通知父组件滚动到底部
    emit('send')

  } catch (error) {
    console.error('发送消息失败:', error)
    notification.error('发送消息失败')

    // 错误时恢复输入内容
    if (!inputValue.value.trim()) {
      inputValue.value = messageContent
    }
  } finally {
    sending.value = false
  }
}

// Lifecycle hooks
onMounted(() => {
  inputRef.value?.focus()
})
</script>

<style scoped>
.message-input-wrapper {
  padding: 16px;
  background: #ffffff;
  border-top: 1px solid #e5e7eb;
}

.input-container {
  max-width: 95%;
  margin: 0 auto;
  position: relative;
}

/* 输入框容器 */
.textarea-wrapper {
  position: relative;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  /* 预设阴影空间，避免聚焦时跳动 */
  box-shadow: 0 0 0 3px transparent;
  transition: all 0.2s ease;
}

.textarea-wrapper:focus-within {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.message-textarea {
  width: 100%;
  padding: 16px 60px 16px 16px;
  border: none;
  background: transparent;
  resize: none;
  font-size: 14px;
  line-height: 1.5;
  box-sizing: border-box;
}

:deep(.message-textarea .n-input__textarea-el) {
  border: none !important;
  box-shadow: none !important;
  outline: none !important;
  background: transparent !important;
  padding: 0 !important;
  margin: 0 !important;
  box-sizing: border-box !important;
}

:deep(.message-textarea .n-input__border),
:deep(.message-textarea .n-input__state-border) {
  display: none !important;
}

:deep(.message-textarea .n-input) {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
}

/* 发送按钮 */
.send-button-wrapper {
  position: absolute;
  right: 12px;
  bottom: 12px;
  z-index: 10;
}

.send-button {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.2s ease;
}

.send-button:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

/* 字数统计 */
.char-count-wrapper {
  display: flex;
  justify-content: flex-end;
  padding: 8px 12px 0;
}

.char-count {
  font-size: 12px;
  color: #64748b;
  font-weight: 500;
  transition: color 0.2s ease;
}

.char-count.warning {
  color: #f59e0b;
}

.char-count.error {
  color: #ef4444;
}

/* 暗色模式 */
html.dark .message-input-wrapper {
  background: #1f2937;
  border-top-color: #374151;
}

html.dark .textarea-wrapper {
  background: #1f2937;
  border-color: #4b5563;
  box-shadow: 0 0 0 3px transparent;
}

html.dark .textarea-wrapper:focus-within {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

html.dark .message-textarea {
  color: #f9fafb;
}

html.dark .char-count {
  color: #9ca3af;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .message-input-wrapper {
    padding: 12px;
  }

  .message-textarea {
    padding: 12px 50px 12px 12px;
  }

  .send-button-wrapper {
    right: 8px;
    bottom: 8px;
  }

  .send-button {
    width: 36px;
    height: 36px;
  }

  .char-count-wrapper {
    padding: 6px 8px 0;
  }
}
</style>