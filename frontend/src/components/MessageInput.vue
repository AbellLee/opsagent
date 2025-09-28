<template>
  <div class="message-input-container">
    <n-input
      ref="inputRef"
      v-model:value="inputValue"
      type="textarea"
      :autosize="{ minRows: 1, maxRows: 6 }"
      :placeholder="PLACEHOLDER_TEXT"
      class="message-textarea"
      @keydown="handleKeyDown"
    />
    <div class="send-button-container">
      <n-button 
        type="primary" 
        circle
        size="small"
        @click="sendMessage"
        :disabled="isSendDisabled"
        :loading="sending"
        class="send-button"
        :aria-label="SEND_BUTTON_LABEL"
      >
        <template #icon>
          <n-icon>
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
              <path d="M3 20V4L17 11L10 13L3 20ZM5 16.05L11.5 13.5L15.5 15.5L5 19.05V16.05ZM11.5 10.5L5 7.95V10.95L15.5 14.5L11.5 10.5Z"/>
            </svg>
          </n-icon>
        </template>
      </n-button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useSessionStore } from '../stores/session'
import { messageAPI } from '../api'
import { createDiscreteApi } from 'naive-ui'

// Constants
const PLACEHOLDER_TEXT = '有什么我能帮您的吗？'
const SEND_BUTTON_LABEL = '发送消息'
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

// Computed properties
const isSendDisabled = computed(() => {
  return !inputValue.value?.trim() || sending.value
})

// Event handlers
const handleKeyDown = (event) => {
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

  try {
    sending.value = true
    
    // Prepare and add user message
    const userMessage = createMessage(MESSAGE_ROLE.USER, inputValue.value.trim())
    sessionStore.addMessage(userMessage)
    
    // Save message content and clear input
    const messageContent = inputValue.value
    inputValue.value = ''
    
    // Notify parent to scroll to bottom
    emit('send')
    
    // Send message to backend
    const response = await messageAPI.send(sessionStore.sessionId, {
      message: messageContent
    })
    
    // Prepare and add assistant message
    const assistantMessage = createMessage(MESSAGE_ROLE.ASSISTANT, response.response)
    sessionStore.addMessage(assistantMessage)
    
    // Notify parent to scroll to bottom again
    emit('send')
  } catch (error) {
    console.error('发送消息失败:', error)
    notification.error('发送消息失败')
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
.message-input-container {
  padding: 16px;
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 8px;
  box-sizing: border-box;
}

.message-textarea {
  flex: 1;
  border: none;
  box-shadow: none;
  resize: none;
  padding: 6px 0;
  outline: none;
  width: 100%;
  /* Add rounded corners for better appearance */
  border-radius: 8px;
  /* Add a subtle shadow for depth */
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  box-sizing: border-box;
}

:deep(.message-textarea .n-input__textarea-el),
:deep(.message-textarea .n-input__border),
:deep(.message-textarea .n-input__state-border) {
  border: none;
  box-shadow: none;
  outline: none;
}

.send-button-container {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  padding: 8px 0;
  /* Ensure the container takes up the full width */
  width: 100%;
  /* Add a small margin to ensure it doesn't touch the edge */
  margin-top: 4px;
  box-sizing: border-box;
}

.send-button {
  width: 32px;
  height: 32px;
  min-width: 32px;
  padding: 0;
  margin-left: 8px;
  flex-shrink: 0;
  /* Position the button in the bottom right corner */
  position: relative;
  right: 0;
  /* Add a small margin to ensure it doesn't touch the edge */
  margin-right: 4px;
  /* Add a subtle shadow for depth */
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.send-button:disabled {
  background-color: #f5f5f5;
  border-color: #d9d9d9;
  color: rgba(0, 0, 0, 0.25);
}

html.dark .message-input-container {
  background-color: #1e1e20;
}

html.dark .message-textarea {
  background-color: #2a2a2a;
  color: #fff;
}

html.dark .send-button-container {
  background-color: #1e1e20;
}

html.dark .send-button {
  background-color: #2a2a2a;
  border-color: #444;
  color: #fff;
}

html.dark .send-button:disabled {
  background-color: #2a2a2a;
  border-color: #444;
  color: rgba(255, 255, 255, 0.3);
}

/* Remove hover border */
.message-input-container:hover {
  border-color: inherit;
}

html.dark .message-input-container:hover {
  border-color: inherit;
}
</style>