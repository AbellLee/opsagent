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

      <!-- 响应模式选择和字数统计 -->
      <div class="bottom-controls">
        <div class="response-mode-wrapper">
          <n-radio-group v-model:value="responseMode" size="small">
            <n-radio-button value="blocking">
              <n-icon size="14" style="margin-right: 4px;">
                <svg viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M12,4A8,8 0 0,1 20,12A8,8 0 0,1 12,20A8,8 0 0,1 4,12A8,8 0 0,1 12,4M12,6A6,6 0 0,0 6,12A6,6 0 0,0 12,18A6,6 0 0,0 18,12A6,6 0 0,0 12,6Z"/>
                </svg>
              </n-icon>
              阻塞
            </n-radio-button>
            <n-radio-button value="streaming">
              <n-icon size="14" style="margin-right: 4px;">
                <svg viewBox="0 0 24 24" fill="currentColor">
                  <path d="M5,13L9,17L7.5,18.5L1,12L7.5,5.5L9,7L5,11H21V13H5M21,6V8H11V6H21M21,16V18H11V16H21Z"/>
                </svg>
              </n-icon>
              流式
            </n-radio-button>
          </n-radio-group>
        </div>

        <div class="char-count-wrapper">
          <span class="char-count" :class="{ warning: isNearLimit, error: isOverLimit }">
            {{ inputValue.length }}/{{ maxLength }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useSessionStore } from '../stores/session'
import { messageAPI } from '../api'
import { createDiscreteApi } from 'naive-ui'

// Constants
import { MESSAGE_TYPES } from '../constants/messageTypes'

// Emits
const emit = defineEmits(['send', 'streaming-start', 'streaming-end'])

// Store and API
const { message: notification } = createDiscreteApi(['message'])
const sessionStore = useSessionStore()

// Reactive data
const inputValue = ref('')
const sending = ref(false)
const inputRef = ref(null)
const responseMode = ref('streaming') // 默认使用流式模式

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
const createMessage = (type, content, extraProps = {}) => ({
  id: Date.now() + Math.random(), // 生成唯一ID
  type,
  role: type === MESSAGE_TYPES.USER ? 'user' : 'assistant', // 保持向后兼容
  content,
  timestamp: new Date().toISOString(),
  sender: type === MESSAGE_TYPES.USER ? '用户' : 'AI助手',
  ...extraProps // 合并额外属性
})

const sendMessage = async () => {
  if (isSendDisabled.value) return

  const messageContent = inputValue.value.trim()
  if (!messageContent) return

  try {
    sending.value = true

    // 创建并添加用户消息
    const userMessage = createMessage(MESSAGE_TYPES.USER, messageContent)
    sessionStore.addMessage(userMessage)

    // 清空输入框
    inputValue.value = ''

    // 通知父组件滚动到底部
    emit('send')

    if (responseMode.value === 'streaming') {
      // 流式模式
      await sendStreamingMessage(messageContent)
    } else {
      // 阻塞模式
      await sendBlockingMessage(messageContent)
    }

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

// 阻塞模式发送消息
const sendBlockingMessage = async (messageContent) => {
  const response = await messageAPI.send(sessionStore.sessionId, {
    message: messageContent,
    response_mode: 'blocking'
  })

  // 处理结构化消息数据
  if (response.response && typeof response.response === 'object') {
    // 新格式：response是完整的消息对象
    sessionStore.addMessage(response.response)
  } else {
    // 兼容旧格式：创建并添加助手消息
    const assistantMessage = createMessage(MESSAGE_TYPES.ASSISTANT, response.response)
    sessionStore.addMessage(assistantMessage)
  }

  // 通知父组件滚动到底部
  emit('send')
}

// 流式模式发送消息
const sendStreamingMessage = async (messageContent) => {
  // 不再预先创建消息，而是根据流式数据动态创建

  // 通知开始流式输入
  emit('streaming-start')

  try {
    // 先发送POST请求启动流式响应
    const response = await fetch(`/api/sessions/${sessionStore.sessionId}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: messageContent,
        response_mode: 'streaming'
      })
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    // 使用EventSource处理SSE（更好的流式支持）
    let currentMessageIndex = null
    let currentAIMessage = null  // 当前的AI消息（可能包含工具调用）

    // 创建一个Promise来处理EventSource
    await new Promise((resolve, reject) => {
      // 注意：EventSource不能直接使用POST，所以我们需要用Fetch的方式
      // 但是我们可以优化Fetch的处理方式

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      const processStream = async () => {
        try {
          while (true) {
            const { done, value } = await reader.read()
            if (done) {
              resolve()
              break
            }

            const chunk = decoder.decode(value, { stream: true })
            buffer += chunk

            // 立即处理每个字符块，不等待完整行
            const lines = buffer.split('\n')
            buffer = lines.pop() || ''

            for (const line of lines) {
              // 处理SSE事件格式
              if (line.startsWith('event: ')) {
                const eventType = line.slice(7).trim()
                console.log('SSE Event:', eventType)
                continue
              }

              if (line.startsWith('data: ')) {
                const dataStr = line.slice(6).trim()

                if (dataStr === '[DONE]') {
                  resolve()
                  return
                }

                // 跳过非JSON数据（如连接事件）
                if (dataStr === 'connected' || !dataStr.startsWith('{')) {
                  continue
                }

                if (dataStr) {
                  try {
                    const chunkData = JSON.parse(dataStr)

                    // 跳过连接测试消息
                    if (chunkData.type === 'connection_established' || chunkData.type === 'test') {
                      continue
                    }

                    // 根据消息类型处理不同的消息 - Augment风格简化处理
                    const messageType = chunkData.message_type || 'assistant'

                    if (messageType === 'tool_call') {
                      // 创建新的AI消息，使用序列化内容结构
                      if (!currentAIMessage) {
                        currentAIMessage = createMessage(MESSAGE_TYPES.ASSISTANT, [])
                        currentMessageIndex = sessionStore.addMessage(currentAIMessage)
                      }

                      // 添加工具调用到内容序列中
                      if (chunkData.tool_calls) {
                        chunkData.tool_calls.forEach(toolCall => {
                          const toolCallEntry = {
                            type: 'tool_call',
                            id: toolCall.id || '',
                            name: toolCall.name || '',
                            args: toolCall.args || {},
                            result: null,
                            status: 'calling',
                            expanded: false
                          }
                          currentAIMessage.content.push(toolCallEntry)
                        })
                        // 更新消息
                        sessionStore.messages[currentMessageIndex] = { ...currentAIMessage }
                      }
                    } else if (messageType === 'tool_result') {
                      // 更新对应工具调用的结果
                      if (currentAIMessage && Array.isArray(currentAIMessage.content)) {
                        const toolCallId = chunkData.tool_call_id || ''
                        const toolResult = chunkData.chunk || ''

                        // 查找对应的工具调用并更新结果
                        for (const item of currentAIMessage.content) {
                          if (item.type === 'tool_call' && item.id === toolCallId) {
                            item.status = 'completed'
                            item.result = toolResult
                            break
                          }
                        }

                        // 更新消息
                        sessionStore.messages[currentMessageIndex] = { ...currentAIMessage }
                      }
                    } else {
                      // 处理AI回复内容
                      if (currentAIMessage) {
                        // 添加内容到现有的AI消息
                        if (chunkData.chunk) {
                          // 如果content是数组（新格式），处理序列化内容
                          if (Array.isArray(currentAIMessage.content)) {
                            const lastItem = currentAIMessage.content[currentAIMessage.content.length - 1]
                            if (lastItem && lastItem.type === 'text') {
                              lastItem.content += chunkData.chunk
                            } else {
                              const textEntry = {
                                type: 'text',
                                content: chunkData.chunk,
                                status: 'completed'
                              }
                              currentAIMessage.content.push(textEntry)
                            }
                          } else {
                            // 兼容旧格式：字符串内容
                            currentAIMessage.content += chunkData.chunk
                          }
                          sessionStore.messages[currentMessageIndex] = { ...currentAIMessage }
                        }
                      } else {
                        // 创建新的AI消息（没有工具调用的情况）
                        const textEntry = {
                          type: 'text',
                          content: chunkData.chunk || '',
                          status: 'completed'
                        }
                        currentAIMessage = createMessage(MESSAGE_TYPES.ASSISTANT, [textEntry])
                        currentMessageIndex = sessionStore.addMessage(currentAIMessage)
                      }
                    }

                    // 通知界面更新
                    emit('send')

                    // 强制DOM更新
                    await nextTick()

                    if (chunkData.is_final) {
                      // 流结束时重置状态
                      currentAIMessage = null
                      resolve()
                      return
                    }
                  } catch (e) {
                    console.error('解析JSON失败:', dataStr, e)
                  }
                }
              }
            }
          }
        } catch (error) {
          reject(error)
        }
      }

      processStream()
    })

  } catch (error) {
    console.error('流式消息发送失败:', error)
    sessionStore.updateMessage(messageIndex, '抱歉，消息发送失败，请重试。')
  } finally {
    emit('streaming-end')
    emit('send')
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

/* 底部控件 */
.bottom-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px 0;
  gap: 12px;
}

.response-mode-wrapper {
  flex-shrink: 0;
}

.char-count-wrapper {
  flex-shrink: 0;
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

  .bottom-controls {
    padding: 6px 8px 0;
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }

  .response-mode-wrapper {
    display: flex;
    justify-content: center;
  }

  .char-count-wrapper {
    display: flex;
    justify-content: flex-end;
  }
}
</style>