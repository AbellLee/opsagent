<template>
  <div class="message-row" :style="messageRowStyle">
    <div class="message-bubble" :style="bubbleStyle">
      <!-- 消息头部 -->
      <div v-if="showHeader" class="message-header">
        <div class="sender-info">
          <span class="sender-icon">{{ messageConfig.icon }}</span>
          <span class="sender-name" :style="{ color: headerColor }">
            {{ senderName }}
          </span>
          <span v-if="isToolMessage" class="tool-badge">
            {{ getToolDisplayName() }}
          </span>
        </div>
        <div class="message-actions">
          <n-button text size="tiny" @click="copyToClipboard">
            <n-icon>
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                <path d="M7 4V2C7 1.45 7.45 1 8 1H20C20.55 1 21 1.45 21 2V16C21 16.55 20.55 17 20 17H18V19C18 20.1 17.1 21 16 21H4C2.9 21 2 20.1 2 19V7C2 5.9 2.9 5 4 5H6V4H7ZM4 7V19H16V17H14C12.9 17 12 16.1 12 15V7C12 5.9 12.9 5 14 5H16V3H8V5H10C11.1 5 12 5.9 12 7V15C12 16.1 11.1 17 10 17H4V7ZM6 5V4H4V5H6Z"/>
              </svg>
            </n-icon>
          </n-button>
          <n-button v-if="canRetry" text size="tiny" @click="retryMessage">
            <n-icon>
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                <path d="M17.65,6.35C16.2,4.9 14.21,4 12,4A8,8 0 0,0 4,12A8,8 0 0,0 12,20C15.73,20 18.84,17.45 19.73,14H17.65C16.83,16.33 14.61,18 12,18A6,6 0 0,1 6,12A6,6 0 0,1 12,6C13.66,6 15.14,6.69 16.22,7.78L13,11H20V4L17.65,6.35Z"/>
              </svg>
            </n-icon>
          </n-button>
        </div>
      </div>

      <!-- 工具操作展示（合并的工具调用和结果） -->
      <div v-if="isToolOperationMessage" class="tool-operation-content">
        <!-- 第一行：标题和展开按钮 -->
        <div class="tool-operation-header">
          <span class="tool-operation-title">🔧 工具操作</span>
          <n-button text size="tiny" @click="toggleToolOperationDetails">
            {{ showToolOperationDetails ? '收起' : '展开' }}
          </n-button>
        </div>

        <!-- 第二行：简洁的工具信息 -->
        <div v-if="!showToolOperationDetails" class="tool-operation-summary">
          <span v-if="message.tool_calls && message.tool_calls.length > 0" class="tool-summary-item">
            调用了 {{ message.tool_calls.length }} 个工具
          </span>
          <span v-if="message.tool_results && message.tool_results.length > 0" class="tool-summary-item">
            {{ message.tool_results.length }} 个工具执行完成
          </span>
        </div>

        <!-- 展开的详细信息 -->
        <div v-if="showToolOperationDetails" class="tool-operation-details">
          <!-- 工具调用部分 -->
          <div v-if="message.tool_calls && message.tool_calls.length > 0" class="tool-calls-section">
            <div class="section-title">调用工具</div>
            <div class="tool-call-details">
              <div v-for="(call, index) in message.tool_calls" :key="index" class="tool-call-item">
                <div class="tool-name">{{ call.name }}</div>
                <div class="tool-args">
                  <pre>{{ JSON.stringify(call.args, null, 2) }}</pre>
                </div>
              </div>
            </div>
          </div>

          <!-- 工具结果部分 -->
          <div v-if="message.tool_results && message.tool_results.length > 0" class="tool-results-section">
            <div class="section-title">执行结果</div>
            <div class="tool-results-details">
              <div v-for="(result, index) in message.tool_results" :key="index" class="tool-result-item">
                <div class="tool-result-name">{{ result.tool_name }}</div>
                <div class="tool-result-content">
                  <pre v-if="checkIsJsonContent(result.content)">{{ formatJsonContent(result.content) }}</pre>
                  <div v-else v-html="parseMarkdown(result.content)"></div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- AI回复内容 -->
        <div v-if="message.content" class="tool-operation-message" v-html="formattedContent"></div>
      </div>

      <!-- 工具调用展示（独立显示，保持兼容性） -->
      <div v-else-if="isToolCallMessage" class="tool-call-content">
        <div class="tool-call-header">
          <span class="tool-call-title">🔧 调用工具</span>
          <n-button text size="tiny" @click="toggleToolDetails">
            {{ showToolDetails ? '收起' : '展开' }}
          </n-button>
        </div>
        <div v-if="showToolDetails" class="tool-call-details">
          <div v-for="(call, index) in message.tool_calls" :key="index" class="tool-call-item">
            <div class="tool-name">{{ call.name }}</div>
            <div class="tool-args">
              <pre>{{ JSON.stringify(call.args, null, 2) }}</pre>
            </div>
          </div>
        </div>
        <!-- 如果有内容，也显示 -->
        <div v-if="message.content" class="tool-call-message" v-html="formattedContent"></div>
      </div>

      <!-- 工具结果展示（独立显示，保持兼容性） -->
      <div v-else-if="isToolResultMessage" class="tool-result-content">
        <div class="tool-result-header">
          <span class="tool-result-title">📊 {{ message.tool_name }} 执行结果</span>
          <n-button text size="tiny" @click="toggleToolResultDetails">
            {{ showToolResultDetails ? '收起' : '展开' }}
          </n-button>
        </div>
        <div
          v-if="showToolResultDetails"
          class="tool-result-body"
          :class="{ 'tool-result-expanded': showToolResultDetails }"
        >
          <pre v-if="isJsonContent" class="tool-result-content-pre">{{ formattedJsonContent }}</pre>
          <div v-else class="tool-result-content-div" v-html="formattedContent"></div>
        </div>
        <div v-else class="tool-result-preview">
          <span class="tool-result-preview-text">
            {{ getToolResultPreview() }}
          </span>
        </div>
      </div>

      <!-- 普通消息内容 -->
      <div v-else ref="contentRef" class="message-content" v-html="formattedContent"></div>

      <!-- 流式输入指示器 -->
      <div v-if="isStreaming" class="streaming-indicator">
        <span class="typing-dots">
          <span></span>
          <span></span>
          <span></span>
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch, nextTick } from 'vue'
import { NButton, NIcon } from 'naive-ui'
import { parseMarkdown } from '../utils/markdown'
import {
  MESSAGE_TYPES,
  getMessageConfig,
  getToolIcon,
  isToolMessage as checkIsToolMessage,
  isJsonContent as checkIsJsonContent,
  formatJsonContent
} from '../constants/messageTypes'

const props = defineProps({
  message: {
    type: Object,
    required: true,
    default: () => ({
      type: 'assistant',
      role: 'assistant',
      content: '',
      timestamp: '',
      sender: 'AI助手'
    }),
    validator: (value) => {
      if (!value || typeof value !== 'object') return false
      // 兼容旧的 role 字段和新的 type 字段
      const messageType = value.type || value.role
      if (!messageType || typeof messageType !== 'string') return false
      return Object.values(MESSAGE_TYPES).includes(messageType) ||
             ['user', 'assistant', 'system', 'tool'].includes(messageType)
    }
  },
  isStreaming: {
    type: Boolean,
    default: false
  }
})

// 响应式数据
const showToolDetails = ref(false)
const showToolResultDetails = ref(false)
const showToolOperationDetails = ref(false)
const contentRef = ref(null)

// 计算属性
const messageType = computed(() => {
  // 优先使用新的 type 字段，如果没有则根据 role 映射
  if (props.message.type) {
    return props.message.type
  }

  // 兼容旧的 role 字段
  switch (props.message.role) {
    case 'user': return MESSAGE_TYPES.USER
    case 'assistant': return MESSAGE_TYPES.ASSISTANT
    case 'tool': return MESSAGE_TYPES.TOOL_RESULT
    case 'system': return MESSAGE_TYPES.ASSISTANT // 系统消息当作助手消息处理
    default: return MESSAGE_TYPES.ASSISTANT
  }
})
const messageConfig = computed(() => getMessageConfig(messageType.value))
const showHeader = computed(() => messageConfig.value.showHeader)
const isToolCallMessage = computed(() => messageType.value === MESSAGE_TYPES.TOOL_CALL)
const isToolResultMessage = computed(() => messageType.value === MESSAGE_TYPES.TOOL_RESULT)
const isToolOperationMessage = computed(() => messageType.value === MESSAGE_TYPES.TOOL_OPERATION)
const isToolMessage = computed(() => checkIsToolMessage(messageType.value))

const senderName = computed(() => {
  return props.message.sender || messageConfig.value.defaultSender || '未知'
})

const canRetry = computed(() => {
  return isToolResultMessage.value && props.message.content.includes('error')
})

// 样式计算
const messageRowStyle = computed(() => ({
  justifyContent: messageConfig.value.align === 'right' ? 'flex-end' : 'flex-start'
}))

const bubbleStyle = computed(() => ({
  backgroundColor: messageConfig.value.bgColor,
  color: messageConfig.value.textColor,
  borderRadius: '12px',
  padding: '12px 16px',
  maxWidth: '80%',
  wordWrap: 'break-word',
  position: 'relative',
  boxShadow: '0 1px 2px rgba(0,0,0,0.1)',
  marginLeft: messageConfig.value.align === 'right' ? 'auto' : '0',
  marginRight: messageConfig.value.align === 'right' ? '0' : 'auto'
}))

const headerColor = computed(() => {
  switch (messageType.value) {
    case MESSAGE_TYPES.ASSISTANT: return '#409eff'
    case MESSAGE_TYPES.TOOL_CALL: return '#fa8c16'
    case MESSAGE_TYPES.TOOL_RESULT: return '#52c41a'
    default: return '#409eff'
  }
})

// 内容处理
const isJsonContent = computed(() => {
  if (!isToolResultMessage.value) return false
  return checkIsJsonContent(props.message.content)
})

const formattedJsonContent = computed(() => {
  if (!isJsonContent.value) return ''
  return formatJsonContent(props.message.content)
})

// 流式显示内容
const streamingContent = ref('')
const isStreamingActive = ref(false)

// 处理消息内容，支持Markdown格式
const formattedContent = computed(() => {
  const content = isStreamingActive.value ? streamingContent.value : props.message.content
  if (!content) return ''
  return parseMarkdown(content)
})

// 方法
const getToolDisplayName = () => {
  if (isToolCallMessage.value && props.message.tool_calls?.length > 0) {
    return props.message.tool_calls[0].name
  }
  if (isToolResultMessage.value && props.message.tool_name) {
    return props.message.tool_name
  }
  return ''
}

const toggleToolDetails = () => {
  showToolDetails.value = !showToolDetails.value
}

const toggleToolResultDetails = () => {
  showToolResultDetails.value = !showToolResultDetails.value
}

const toggleToolOperationDetails = () => {
  showToolOperationDetails.value = !showToolOperationDetails.value
}

const getToolResultPreview = () => {
  const content = props.message.content || ''

  // 如果是JSON内容，显示简化的预览
  if (isJsonContent.value) {
    try {
      const parsed = JSON.parse(content)
      if (typeof parsed === 'object') {
        const keys = Object.keys(parsed)
        if (keys.length > 0) {
          return `{ ${keys.slice(0, 3).join(', ')}${keys.length > 3 ? '...' : ''} }`
        }
      }
      return 'JSON 数据'
    } catch {
      return '数据格式错误'
    }
  }

  // 对于普通文本，显示前100个字符
  if (content.length > 100) {
    return content.substring(0, 100) + '...'
  }

  return content || '无内容'
}

const copyToClipboard = async () => {
  try {
    let textToCopy = props.message.content

    // 如果是工具调用，复制工具调用信息
    if (isToolCallMessage.value && props.message.tool_calls) {
      textToCopy = JSON.stringify(props.message.tool_calls, null, 2)
    }
    // 如果是工具结果且是JSON，复制格式化的JSON
    else if (isToolResultMessage.value && isJsonContent.value) {
      textToCopy = formattedJsonContent.value
    }

    await navigator.clipboard.writeText(textToCopy)

    // 使用 Naive UI 的消息提示
    const { message } = await import('naive-ui')
    message.success('已复制到剪贴板')
  } catch (error) {
    console.error('复制失败:', error)
    const { message } = await import('naive-ui')
    message.error('复制失败')
  }
}

const retryMessage = () => {
  // 重试逻辑 - 通过事件向父组件发送重试请求
  emit('retry-message', props.message)
}

// 定义事件
const emit = defineEmits(['retry-message'])

// 打字机效果
const typewriterEffect = (targetText) => {
  if (!props.isStreaming) {
    streamingContent.value = targetText
    return
  }

  const currentLength = streamingContent.value.length
  const targetLength = targetText.length

  if (currentLength >= targetLength) {
    streamingContent.value = targetText
    return
  }

  // 逐字显示
  let index = currentLength
  const animate = () => {
    if (index < targetLength && props.isStreaming) {
      const charsToAdd = Math.min(2, targetLength - index)
      streamingContent.value = targetText.substring(0, index + charsToAdd)
      index += charsToAdd
      setTimeout(animate, 30) // 30ms间隔
    }
  }

  animate()
}

// 高亮代码的函数
const highlightCode = async () => {
  if (contentRef.value) {
    // 使用nextTick确保DOM更新完成后再执行高亮
    await nextTick()

    // 让Prism处理所有代码块
    if (window.Prism) {
      window.Prism.highlightAllUnder(contentRef.value)
    }

    // 处理Mermaid图表
    const mermaidElements = contentRef.value.querySelectorAll('.mermaid')
    if (mermaidElements.length > 0 && window.mermaid) {
      try {
        // 添加一个小延迟确保DOM完全渲染
        await new Promise(resolve => setTimeout(resolve, 100))

        // 为每个Mermaid元素生成唯一的ID
        mermaidElements.forEach((element, index) => {
          if (!element.getAttribute('data-processed')) {
            const id = `mermaid-${Date.now()}-${index}`
            element.id = id
            element.setAttribute('data-processed', 'true')
          }
        })

        console.log('准备渲染Mermaid图表，元素数量:', mermaidElements.length)

        // 渲染Mermaid图表
        const results = await window.mermaid.run({
          nodes: mermaidElements,
          suppressErrors: false
        })

        console.log('Mermaid渲染完成:', results)
      } catch (error) {
        console.warn('Mermaid渲染失败:', error)
        // 在元素中显示错误信息
        mermaidElements.forEach(element => {
          element.innerHTML = `<div style="color: red; font-style: italic;">
            图表渲染失败: ${error.message}
            <pre>${element.textContent}</pre>
          </div>`
        })
      }
    }
  }
}

// 在组件挂载后触发代码高亮
onMounted(() => {
  highlightCode()
})



// 监听内容变化
watch(() => props.message.content, (newContent, oldContent) => {
  if (props.isStreaming && newContent !== oldContent) {
    // 流式模式：使用打字机效果
    isStreamingActive.value = true
    typewriterEffect(newContent)
  } else {
    // 非流式模式：直接显示
    isStreamingActive.value = false
    streamingContent.value = newContent
  }
  highlightCode()
})

// 监听流式状态变化
watch(() => props.isStreaming, (isStreaming) => {
  if (!isStreaming) {
    // 流式结束，显示完整内容
    isStreamingActive.value = false
    streamingContent.value = props.message.content
    highlightCode()
  }
})

// 在组件挂载后初始化
onMounted(() => {
  streamingContent.value = props.message.content
  highlightCode()
})
</script>

<style scoped>
.message-row {
  display: flex;
  margin-bottom: 16px;
  animation: fadeIn 0.3s ease-out;
}

/* 消息头部样式 */
.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 12px;
}

.sender-info {
  display: flex;
  align-items: center;
  gap: 6px;
}

.sender-icon {
  font-size: 14px;
}

.sender-name {
  font-weight: bold;
}

.tool-badge {
  background: rgba(0,0,0,0.1);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 10px;
  color: #666;
}

.message-actions {
  display: flex;
  gap: 4px;
}

/* 工具调用样式 */
.tool-call-content {
  border-left: 3px solid #fa8c16;
  padding-left: 12px;
}

.tool-call-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-weight: bold;
  color: #fa8c16;
}

.tool-call-details {
  background: rgba(250, 140, 22, 0.05);
  border-radius: 6px;
  padding: 8px;
  margin-bottom: 8px;
  animation: slideDown 0.3s ease-out;
  max-height: 300px;
  overflow-y: auto;
}

.tool-call-item {
  margin-bottom: 8px;
}

.tool-call-item:last-child {
  margin-bottom: 0;
}

.tool-name {
  font-weight: bold;
  color: #fa8c16;
  margin-bottom: 4px;
  font-size: 13px;
}

.tool-args {
  font-family: 'Courier New', monospace;
  font-size: 12px;
  background: rgba(0,0,0,0.05);
  padding: 6px;
  border-radius: 4px;
  overflow-x: auto;
}

.tool-args pre {
  margin: 0;
  white-space: pre-wrap;
}

.tool-call-message {
  margin-top: 8px;
}

/* 工具操作样式（合并的工具调用和结果） */
.tool-operation-content {
  border-left: 3px solid #409eff;
  padding-left: 12px;
  background: rgba(64, 158, 255, 0.02);
  border-radius: 8px;
  padding: 12px;
  margin: 4px 0;
}

.tool-operation-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-weight: bold;
  color: #409eff;
}

.tool-operation-summary {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #666;
  margin-bottom: 8px;
}

.tool-summary-item {
  padding: 2px 8px;
  background: rgba(64, 158, 255, 0.1);
  border-radius: 4px;
  border: 1px dashed rgba(64, 158, 255, 0.3);
}

.tool-operation-details {
  border-top: 1px solid rgba(64, 158, 255, 0.2);
  padding-top: 8px;
  margin-top: 8px;
}

.tool-calls-section,
.tool-results-section {
  margin-bottom: 12px;
}

.section-title {
  font-size: 13px;
  font-weight: 600;
  color: #666;
  margin-bottom: 6px;
  padding: 4px 8px;
  background: rgba(0, 0, 0, 0.05);
  border-radius: 4px;
  display: inline-block;
}

.tool-calls-preview,
.tool-results-preview {
  font-size: 12px;
  color: #888;
  font-style: italic;
  padding: 6px 8px;
  background: rgba(250, 140, 22, 0.1);
  border-radius: 4px;
  border: 1px dashed #fa8c16;
}

.tool-result-item {
  margin-bottom: 8px;
  padding: 8px;
  background: rgba(82, 196, 26, 0.05);
  border-radius: 6px;
  border-left: 3px solid #52c41a;
}

.tool-result-name {
  font-weight: bold;
  color: #52c41a;
  margin-bottom: 4px;
  font-size: 12px;
}

.tool-result-content {
  font-size: 12px;
  max-height: 200px;
  overflow-y: auto;
}

.tool-result-content pre {
  margin: 0;
  font-family: 'Courier New', monospace;
  white-space: pre-wrap;
  overflow-x: auto;
}

.tool-operation-message {
  margin-top: 12px;
  padding-top: 8px;
  border-top: 1px solid rgba(250, 140, 22, 0.2);
}

/* 工具结果样式 */
.tool-result-content {
  border-left: 3px solid #52c41a;
  padding-left: 12px;
}

.tool-result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-weight: bold;
  color: #52c41a;
}

.tool-result-preview {
  background: rgba(82, 196, 26, 0.05);
  border-radius: 6px;
  padding: 8px;
  font-size: 12px;
  color: #666;
  font-style: italic;
  border: 1px dashed #52c41a;
}

.tool-result-preview-text {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tool-result-body {
  background: rgba(82, 196, 26, 0.05);
  border-radius: 6px;
  padding: 8px;
  animation: slideDown 0.3s ease-out;
  overflow: hidden;
}

.tool-result-expanded {
  max-height: 400px;
  overflow-y: auto;
}

.tool-result-content-pre {
  margin: 0;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  white-space: pre-wrap;
  overflow-x: auto;
  max-height: 350px;
  overflow-y: auto;
}

.tool-result-content-div {
  max-height: 350px;
  overflow-y: auto;
  font-size: 13px;
  line-height: 1.5;
}

/* 滚动条样式 */
.tool-result-content-pre::-webkit-scrollbar,
.tool-result-content-div::-webkit-scrollbar,
.tool-result-expanded::-webkit-scrollbar,
.tool-call-details::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.tool-result-content-pre::-webkit-scrollbar-track,
.tool-result-content-div::-webkit-scrollbar-track,
.tool-result-expanded::-webkit-scrollbar-track,
.tool-call-details::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 3px;
}

.tool-result-content-pre::-webkit-scrollbar-thumb,
.tool-result-content-div::-webkit-scrollbar-thumb,
.tool-result-expanded::-webkit-scrollbar-thumb {
  background: rgba(82, 196, 26, 0.5);
  border-radius: 3px;
}

.tool-call-details::-webkit-scrollbar-thumb {
  background: rgba(250, 140, 22, 0.5);
  border-radius: 3px;
}

.tool-result-content-pre::-webkit-scrollbar-thumb:hover,
.tool-result-content-div::-webkit-scrollbar-thumb:hover,
.tool-result-expanded::-webkit-scrollbar-thumb:hover {
  background: rgba(82, 196, 26, 0.7);
}

.tool-call-details::-webkit-scrollbar-thumb:hover {
  background: rgba(250, 140, 22, 0.7);
}

/* 动画效果 */
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(-10px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes slideDown {
  from {
    opacity: 0;
    max-height: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    max-height: 400px;
    transform: translateY(0);
  }
}

/* 工具消息特殊动画 */
.tool-call-content,
.tool-result-content {
  animation: slideIn 0.4s ease-out;
}

/* 悬停效果 */
.message-bubble:hover {
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
  transition: box-shadow 0.2s ease;
}

/* 工具调用详情展开动画 */
.tool-call-details {
  animation: fadeIn 0.3s ease-out;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .message-bubble {
    max-width: 90%;
    padding: 10px 12px;
  }

  .message-header {
    font-size: 11px;
  }

  .tool-args,
  .tool-result-body pre {
    font-size: 11px;
  }
}

/* 代码块样式 */
.message-content :deep(pre) {
  background-color: #f8f9fa;
  color: #212529;
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 12px 0;
  border: 1px solid #e9ecef;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
  font-family: 'Fira Code', 'Courier New', monospace;
  line-height: 1.5;
}

.message-content :deep(code) {
  background-color: #f8f9fa;
  color: #495057;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Fira Code', 'Courier New', monospace;
  font-size: 0.9em;
  border: 1px solid #e9ecef;
}

.message-content :deep(pre code) {
  background-color: transparent;
  color: inherit;
  padding: 0;
  border: none;
}

/* 标题样式 */
.message-content :deep(h1),
.message-content :deep(h2),
.message-content :deep(h3) {
  margin: 12px 0 8px 0;
  font-weight: bold;
}

.message-content :deep(h1) {
  font-size: 1.5em;
  border-bottom: 1px solid #ddd;
  padding-bottom: 0.3em;
}

.message-content :deep(h2) {
  font-size: 1.3em;
  border-bottom: 1px solid #ddd;
  padding-bottom: 0.3em;
}

.message-content :deep(h3) {
  font-size: 1.1em;
}

/* 段落和文本样式 */
.message-content :deep(p) {
  margin: 8px 0;
  line-height: 1.6;
}

.message-content :deep(strong) {
  font-weight: bold;
}

.message-content :deep(em) {
  font-style: italic;
}

/* 链接样式 */
.message-content :deep(a) {
  color: #409eff;
  text-decoration: underline;
}

/* 列表样式 */
.message-content :deep(ul),
.message-content :deep(ol) {
  padding-left: 20px;
  margin: 8px 0;
}

.message-content :deep(li) {
  margin: 4px 0;
}

/* 引用块样式 */
.message-content :deep(blockquote) {
  border-left: 4px solid #409eff;
  padding: 12px 20px;
  margin: 16px 0;
  color: #495057;
  background-color: rgba(64, 158, 255, 0.08);
  border-radius: 0 8px 8px 0;
}

/* 表格样式 */
.message-content :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 8px 0;
  border-radius: 4px;
  overflow: hidden;
}

.message-content :deep(th),
.message-content :deep(td) {
  border: 1px solid #ddd;
  padding: 8px 12px;
  text-align: left;
}

.message-content :deep(th) {
  background-color: #f0f5ff;
  font-weight: 600;
  color: #212529;
}

/* 图片样式 */
.message-content :deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: 4px;
  box-shadow: 0 2px 6px rgba(0,0,0,0.1);
}

/* Mermaid 图表样式 */
.message-content :deep(.mermaid) {
  background-color: white;
  border-radius: 8px;
  padding: 16px;
  margin: 12px 0;
  box-shadow: 0 2px 6px rgba(0,0,0,0.1);
  text-align: center;
  overflow: auto;
  border: 1px solid #e9ecef;
}

.message-content :deep(.mermaid svg) {
  max-width: 100%;
  height: auto;
}

/* 流式输入指示器 */
.streaming-indicator {
  margin-top: 8px;
  display: flex;
  align-items: center;
}

.typing-dots {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.typing-dots span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: #409eff;
  animation: typing 1.4s infinite ease-in-out;
}

.typing-dots span:nth-child(1) {
  animation-delay: -0.32s;
}

.typing-dots span:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes typing {
  0%, 80%, 100% {
    transform: scale(0.8);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}
</style>