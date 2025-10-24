<template>
  <div class="message-row" :style="messageRowStyle">
    <div class="message-bubble" :style="bubbleStyle">
      <!-- 消息头部 -->
      <div v-if="showHeader" class="message-header">
        <div class="sender-info">
          <span class="sender-icon">{{ messageConfig.icon }}</span>
          <span class="sender-name">{{ senderName }}</span>
        </div>
        <div class="message-actions">
          <n-button text size="tiny" @click="copyToClipboard">
            <n-icon>
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                <path d="M7 4V2C7 1.45 7.45 1 8 1H20C20.55 1 21 1.45 21 2V16C21 16.55 20.55 17 20 17H18V19C18 20.1 17.1 21 16 21H4C2.9 21 2 20.1 2 19V7C2 5.9 2.9 5 4 5H6V4H7ZM4 7V19H16V17H14C12.9 17 12 16.1 12 15V7C12 5.9 12.9 5 14 5H16V3H8V5H10C11.1 5 12 5.9 12 7V15C12 16.1 11.1 17 10 17H4V7ZM6 5V4H4V5H6Z"/>
              </svg>
            </n-icon>
          </n-button>
        </div>
      </div>

      <!-- Augment风格的序列化AI回复 -->
      <div class="ai-message-container">
        <!-- 按时间顺序展示内容序列 -->
        <div v-if="hasContentSequence" class="content-sequence">
          <div v-for="(item, index) in message.content" :key="index" class="sequence-item">
            <!-- 工具调用项 -->
            <div v-if="item.type === 'tool_call'" class="tool-call-item">
              <div class="step-indicator" @click="toggleSequenceItem(index)">
                <span class="step-icon">{{ getToolIcon(item?.name || 'default') }}</span>
                <span class="step-name">{{ item?.name || '未知工具' }}</span>
                <span class="step-status" :class="getToolStatusClass(item?.status || 'unknown')">
                  {{ getToolStatusText(item?.status || 'unknown') }}
                </span>
                <n-button text size="tiny" class="expand-btn">
                  {{ (item?.expanded) ? '收起' : '展开' }}
                </n-button>
              </div>

              <!-- 工具调用详情 -->
              <div v-if="item?.expanded" class="step-details">
                <div v-if="item?.args" class="step-args">
                  <div class="detail-label">参数:</div>
                  <pre class="detail-content">{{ JSON.stringify(item.args, null, 2) }}</pre>
                </div>
                <div v-if="item?.result" class="step-result">
                  <div class="detail-label">结果:</div>
                  <div class="detail-content">
                    <pre v-if="isJsonContent(item.result)">{{ formatJsonContent(item.result) }}</pre>
                    <div v-else v-html="parseMarkdown(String(item.result))"></div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 文本回复项 -->
            <div v-else-if="item.type === 'text'" class="text-response-item">
              <div class="text-content" v-html="parseMarkdown(item.content)"></div>
            </div>
          </div>
        </div>

        <!-- 兼容旧格式：如果是字符串内容 -->
        <div v-else-if="typeof message.content === 'string' && message.content" class="legacy-content">
          <div ref="contentRef" class="message-content" v-html="formattedContent"></div>
        </div>
      </div>

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
import { NButton, NIcon, createDiscreteApi } from 'naive-ui'
import { parseMarkdown } from '../utils/markdown'
import {
  MESSAGE_TYPES,
  getMessageConfig,
  getToolIcon,
  isJsonContent,
  formatJsonContent,
  getToolStatusText
} from '../constants/messageTypes'

const { message: notification } = createDiscreteApi(['message'])

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
    default: return MESSAGE_TYPES.ASSISTANT
  }
})

const messageConfig = computed(() => getMessageConfig(messageType.value))
const showHeader = computed(() => messageConfig.value.showHeader)

const senderName = computed(() => {
  return props.message.sender || messageConfig.value.defaultSender || '未知'
})

// 检查是否有内容序列
const hasContentSequence = computed(() => {
  return Array.isArray(props.message?.content) && props.message.content.length > 0
})

// 兼容性：检查是否有工具调用（旧格式）
// const hasToolCallsComputed = computed(() => hasToolCalls(props.message))

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

// 流式显示内容
const streamingContent = ref('')
const isStreamingActive = ref(false)

// 处理消息内容，支持Markdown格式
const formattedContent = computed(() => {
  const content = isStreamingActive.value ? streamingContent.value : props.message.content
  if (!content) return ''
  return parseMarkdown(content)
})

// 序列项切换方法
const toggleSequenceItem = (index) => {
  if (Array.isArray(props.message?.content) && props.message.content[index]) {
    const item = props.message.content[index]
    if (item.type === 'tool_call') {
      // 确保expanded属性存在，如果不存在则初始化为false
      if (typeof item.expanded === 'undefined') {
        item.expanded = false
      }

      // 记录当前滚动位置
      const container = document.querySelector('.messages-container')
      const scrollTop = container?.scrollTop || 0

      // 切换展开状态
      item.expanded = !item.expanded

      // 保持滚动位置（使用PRESERVE场景）
      nextTick(() => {
        if (container && scrollTop > 0) {
          const threshold = 50
          const isNearBottom = scrollTop + container.clientHeight >= container.scrollHeight - threshold

          // 如果用户不在底部，恢复原位置
          if (!isNearBottom) {
            container.scrollTop = scrollTop
          }
        }
      })
    }
  }
}

// 兼容性：工具调用相关方法（旧格式）
// const toggleToolCall = (index) => {
//   if (props.message?.tool_calls && props.message.tool_calls[index]) {
//     // 确保expanded属性存在，如果不存在则初始化为false
//     const toolCall = props.message.tool_calls[index]
//     if (typeof toolCall.expanded === 'undefined') {
//       toolCall.expanded = false
//     }
//     // 切换展开状态
//     toolCall.expanded = !toolCall.expanded
//   }
// }

const getToolStatusClass = (status) => {
  switch (status) {
    case 'calling':
      return 'status-calling'
    case 'completed':
      return 'status-completed'
    case 'failed':
      return 'status-failed'
    default:
      return 'status-unknown'
  }
}

const copyToClipboard = async () => {
  try {
    let textToCopy = ''

    // 根据消息内容类型处理要复制的文本
    if (typeof props.message.content === 'string') {
      // 旧格式：纯文本内容
      textToCopy = props.message.content
    } else if (Array.isArray(props.message.content)) {
      // 新格式：内容序列
      textToCopy = props.message.content
        .map(item => {
          if (item.type === 'text') {
            return item.content
          } else if (item.type === 'tool_call') {
            return `工具: ${item.name}\n参数: ${JSON.stringify(item.args, null, 2)}\n结果: ${item.result || '无结果'}`
          }
          return ''
        })
        .filter(text => text.length > 0)
        .join('\n\n')
    } else {
      // 其他情况，尝试转换为字符串
      textToCopy = String(props.message.content)
    }

    // 如果有工具调用（旧格式兼容），也包含工具调用信息
    if (props.message.tool_calls && props.message.tool_calls.length > 0) {
      const toolInfo = props.message.tool_calls.map(call =>
        `工具: ${call.name}\n参数: ${JSON.stringify(call.args, null, 2)}\n结果: ${call.result || '无结果'}`
      ).join('\n\n')
      textToCopy = `${textToCopy}\n\n工具调用信息:\n${toolInfo}`
    }

    await navigator.clipboard.writeText(textToCopy)

    // 使用 Naive UI 的消息提示
    notification.success('已复制到剪贴板')
  } catch (error) {
    console.error('复制失败:', error)
    notification.error('复制失败')
  }
}

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
  // 使用nextTick确保DOM更新完成后再执行高亮
  await nextTick()

  // 查找所有可能包含代码的容器
  const containers = []
  if (contentRef.value) {
    containers.push(contentRef.value)
  }

  // 查找序列化内容中的容器
  const sequenceContainers = document.querySelectorAll('.content-sequence .text-content, .legacy-content .message-content')
  sequenceContainers.forEach(container => containers.push(container))

  // 对每个容器执行代码高亮
  for (const container of containers) {
    if (container && window.Prism) {
      try {
        window.Prism.highlightAllUnder(container)
      } catch (error) {
        // 静默处理高亮失败
      }
    }

    // 处理Mermaid图表
    if (container) {
      const mermaidElements = container.querySelectorAll('.mermaid')
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

        // 渲染Mermaid图表
        await window.mermaid.run({
          nodes: mermaidElements,
          suppressErrors: false
        })
      } catch (error) {
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

/* 代码块样式 - GitHub Light 主题 */
.message-content :deep(pre),
.text-content :deep(pre),
.detail-content :deep(pre) {
  background-color: #f6f8fa;
  color: #24292f;
  padding: 16px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 16px 0;
  border: 1px solid #d0d7de;
  box-shadow: none;
  font-family: 'SFMono-Regular', 'Consolas', 'Liberation Mono', 'Menlo', monospace;
  line-height: 1.45;
  position: relative;
}

.message-content :deep(code),
.text-content :deep(code),
.detail-content :deep(code) {
  background-color: #f8f9fa;
  color: #495057;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Fira Code', 'Courier New', monospace;
  font-size: 0.9em;
  border: 1px solid #e9ecef;
}

.message-content :deep(pre code),
.text-content :deep(pre code),
.detail-content :deep(pre code) {
  background-color: transparent;
  color: inherit;
  padding: 0;
  border: none;
  font-size: 14px;
}

/* Prism.js 语法高亮样式覆盖 - GitHub Light 主题 */
.message-content :deep(.token.comment),
.text-content :deep(.token.comment) {
  color: #6a737d;
  font-style: italic;
}

.message-content :deep(.token.keyword),
.text-content :deep(.token.keyword) {
  color: #d73a49;
  font-weight: 600;
}

.message-content :deep(.token.string),
.text-content :deep(.token.string) {
  color: #032f62;
}

.message-content :deep(.token.function),
.text-content :deep(.token.function) {
  color: #6f42c1;
}

.message-content :deep(.token.number),
.text-content :deep(.token.number) {
  color: #005cc5;
}

.message-content :deep(.token.operator),
.text-content :deep(.token.operator) {
  color: #d73a49;
}

.message-content :deep(.token.punctuation),
.text-content :deep(.token.punctuation) {
  color: #24292f;
}

.message-content :deep(.token.builtin),
.text-content :deep(.token.builtin) {
  color: #005cc5;
}

.message-content :deep(.token.class-name),
.text-content :deep(.token.class-name) {
  color: #6f42c1;
}

.message-content :deep(.token.boolean),
.text-content :deep(.token.boolean) {
  color: #005cc5;
}

.message-content :deep(.token.variable),
.text-content :deep(.token.variable) {
  color: #e36209;
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

/* Augment风格的完整AI消息样式 */
.ai-message-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.content-sequence {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.sequence-item {
  position: relative;
}

.tool-call-item {
  background: rgba(24, 144, 255, 0.03);
  border: 1px solid rgba(24, 144, 255, 0.12);
  border-radius: 6px;
  padding: 12px 16px;
  margin: 3px 0;
  position: relative;
  transition: all 0.2s ease;
}

.tool-call-item:hover {
  border-color: rgba(24, 144, 255, 0.2);
  background: rgba(24, 144, 255, 0.05);
}

.tool-call-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: #1890ff;
  border-radius: 3px 0 0 3px;
}

.text-response-item {
  padding: 3px 0;
}

.text-content {
  font-size: 14px;
  line-height: 1.6;
  color: #333;
}

/* 兼容性样式保留 */
.legacy-content {
  padding: 8px 0;
}

.legacy-content .message-content {
  font-size: 14px;
  line-height: 1.6;
  color: #333;
}

.step-indicator {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0;
  cursor: pointer;
  transition: all var(--transition-fast);
  border-radius: var(--border-radius-sm);
  min-height: 32px;
}

.step-indicator:hover {
  background: rgba(168, 216, 234, 0.15);
  padding: 4px 8px;
  margin: -4px -8px;
}

.step-icon {
  font-size: 16px;
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(168, 216, 234, 0.1);
  border-radius: var(--border-radius-sm);
  color: var(--primary-color-1);
  flex-shrink: 0;
}

.step-name {
  flex: 1;
  font-size: 14px;
  color: #333;
  font-weight: 500;
}

.step-status {
  font-size: 11px;
  padding: 3px 8px;
  border-radius: var(--border-radius-full);
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.3px;
  flex-shrink: 0;
}

.status-calling {
  background: #fff7e6;
  color: #fa8c16;
  border: 1px solid #ffd591;
}

.status-calling::before {
  content: '●';
  animation: pulse 1.5s infinite;
  margin-right: 4px;
}

.status-completed {
  background: #f6ffed;
  color: #52c41a;
  border: 1px solid #b7eb8f;
}

.status-completed::before {
  content: '✓';
  margin-right: 4px;
}

.status-failed {
  background: #fff2f0;
  color: #ff4d4f;
  border: 1px solid #ffccc7;
}

.status-failed::before {
  content: '✗';
  margin-right: 4px;
}

.status-unknown {
  background: #f0f0f0;
  color: #999;
  border: 1px solid #d9d9d9;
}

.expand-btn {
  opacity: 0.7;
  transition: all var(--transition-fast);
  font-size: 12px;
  color: #666;
  flex-shrink: 0;
}

.step-indicator:hover .expand-btn {
  opacity: 1;
  color: var(--primary-color-1);
}

.step-details {
  margin-top: 12px;
  padding: var(--spacing-4);
  background: var(--bg-secondary);
  border-radius: var(--border-radius-md);
  border: 1px solid var(--border-color-light);
  margin-left: 28px;
}

.step-args,
.step-result,
.step-error {
  margin-bottom: 12px;
}

.step-args:last-child,
.step-result:last-child,
.step-error:last-child {
  margin-bottom: 0;
}

.ai-response-content {
  padding-top: 8px;
}

.ai-response-content .message-content {
  font-size: 14px;
  line-height: 1.6;
  color: #333;
}

.detail-label {
  font-size: 12px;
  font-weight: 600;
  color: #666;
  margin-bottom: 4px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.detail-content {
  font-size: 13px;
  line-height: 1.5;
}

.detail-content pre {
  background: var(--bg-tertiary);
  padding: var(--spacing-2);
  border-radius: var(--border-radius-sm);
  font-family: 'Courier New', monospace;
  font-size: 12px;
  overflow-x: auto;
  margin: 0;
  white-space: pre-wrap;
  border: 1px solid var(--border-color-light);
}

.error-text {
  color: #ff4d4f;
  background: #fff2f0;
  padding: 8px;
  border-radius: 4px;
  border-left: 3px solid #ff4d4f;
}

/* 移除旧的ai-response样式，已被ai-response-content替代 */

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

/* 暗色模式下的代码块样式 - GitHub Dark */
html.dark .message-content :deep(pre),
html.dark .text-content :deep(pre),
html.dark .detail-content :deep(pre) {
  background-color: #0d1117;
  color: #e6edf3;
  border-color: #30363d;
}

html.dark .message-content :deep(code),
html.dark .text-content :deep(code),
html.dark .detail-content :deep(code) {
  background-color: rgba(110, 118, 129, 0.4);
  color: #e6edf3;
  border-color: #30363d;
}

/* 暗色模式下的语法高亮 */
html.dark .message-content :deep(.token.comment),
html.dark .text-content :deep(.token.comment) {
  color: #8b949e;
}

html.dark .message-content :deep(.token.keyword),
html.dark .text-content :deep(.token.keyword) {
  color: #ff7b72;
}

html.dark .message-content :deep(.token.string),
html.dark .text-content :deep(.token.string) {
  color: #a5d6ff;
}

html.dark .message-content :deep(.token.function),
html.dark .text-content :deep(.token.function) {
  color: #d2a8ff;
}

html.dark .message-content :deep(.token.number),
html.dark .text-content :deep(.token.number) {
  color: #79c0ff;
}

html.dark .message-content :deep(.token.operator),
html.dark .text-content :deep(.token.operator) {
  color: #ff7b72;
}

html.dark .message-content :deep(.token.builtin),
html.dark .text-content :deep(.token.builtin) {
  color: #79c0ff;
}

html.dark .message-content :deep(.token.class-name),
html.dark .text-content :deep(.token.class-name) {
  color: #ffa657;
}

html.dark .message-content :deep(.token.variable),
html.dark .text-content :deep(.token.variable) {
  color: #ffa657;
}
</style>