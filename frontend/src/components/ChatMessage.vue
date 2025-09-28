<template>
  <div :class="messageClass">
    <div class="message-content">
      <div class="message-text">
        <n-ellipsis 
          v-if="message.role === 'user'" 
          :line-clamp="100" 
          :tooltip="false"
        >
          {{ message.content }}
        </n-ellipsis>
        <div v-else>
          <div v-html="renderedContent" ref="contentRef"></div>
        </div>
      </div>
      <div class="message-time">
        {{ formattedTime }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, onUpdated } from 'vue'
import { NEllipsis } from 'naive-ui'
import { parseMarkdown, initializeMermaid } from '../utils/markdown'

const props = defineProps({
  message: {
    type: Object,
    required: true
  }
})

const contentRef = ref(null)

const messageClass = computed(() => ({
  'message': true,
  'user-message': props.message.role === 'user',
  'assistant-message': props.message.role === 'assistant'
}))

// 检测是否为JSON格式
const isJSON = (content) => {
  if (typeof content !== 'string') return false
  try {
    const parsed = JSON.parse(content)
    return typeof parsed === 'object' && parsed !== null
  } catch (e) {
    return false
  }
}

// 格式化JSON显示
const formatJSON = (content) => {
  try {
    const obj = JSON.parse(content)
    return JSON.stringify(obj, null, 2)
  } catch (e) {
    return content
  }
}

// 转义HTML特殊字符
const escapeHtml = (unsafe) => {
  return unsafe
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;")
}

const renderedContent = computed(() => {
  const content = props.message.content || ''
  
  // 如果是JSON格式，特殊处理
  if (isJSON(content)) {
    const formatted = formatJSON(content)
    return `<pre class="code-block json"><code>${escapeHtml(formatted)}</code></pre>`
  }
  
  // 检查是否包含HTML标签
  if (/<[^>]+>/.test(content)) {
    // 简单判断是否为纯HTML片段（以标签开始和结束）
    if (/^<[^>]+>.*<\/[^>]+>$/.test(content.trim()) || /^<[^>]+\/?>$/.test(content.trim())) {
      // 直接返回HTML内容（注意：实际项目中需要更严格的XSS防护）
      return content
    }
  }
  
  // 使用统一的Markdown解析器
  return parseMarkdown(content)
})

const formattedTime = computed(() => {
  const date = new Date(props.message.timestamp)
  return date.toLocaleTimeString('zh-CN', { 
    hour: '2-digit', 
    minute: '2-digit' 
  })
})

// 渲染 Mermaid 图表
const renderMermaid = async () => {
  if (contentRef.value && window.mermaid) {
    const mermaidElements = contentRef.value.querySelectorAll('.mermaid')
    if (mermaidElements.length > 0) {
      try {
        await initializeMermaid()
        mermaidElements.forEach(element => {
          // 检查是否已经渲染过
          if (!element.hasAttribute('data-processed')) {
            window.mermaid.render(
              'mermaid-' + element.id,
              element.textContent,
              (svgCode) => {
                element.innerHTML = svgCode
                element.setAttribute('data-processed', 'true')
              }
            )
          }
        })
      } catch (error) {
        console.error('Mermaid渲染失败:', error)
      }
    }
  }
}

onMounted(async () => {
  // 动态加载 mermaid
  if (!window.mermaid) {
    try {
      window.mermaid = await import('mermaid')
    } catch (error) {
      console.error('加载Mermaid失败:', error)
    }
  }
  renderMermaid()
})

onUpdated(() => {
  renderMermaid()
})
</script>

<style scoped>
.message {
  margin-bottom: 20px;
  display: flex;
}

.user-message {
  justify-content: flex-end;
}

.assistant-message {
  justify-content: flex-start;
}

.message-content {
  max-width: 80%;
  position: relative;
  border-radius: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  transition: all 0.2s ease;
}

.message-content:hover {
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
}

.user-message .message-content {
  background-color: #18a058;
  color: white;
  border-radius: 16px 0 16px 16px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}

.user-message .message-content:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.assistant-message .message-content {
  background-color: #f5f5f5;
  color: #333;
  border-radius: 0 16px 16px 16px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}

.assistant-message .message-content:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.message-text {
  padding: 16px 20px;
  line-height: 1.6;
  font-size: 14px;
}

.message-time {
  font-size: 12px;
  color: #999;
  text-align: right;
  padding: 4px 20px 0 20px;
  margin-top: 4px;
}

.code-block {
  background-color: #2d2d2d;
  color: #f8f8f2;
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 12px 0;
  font-family: 'Courier New', monospace;
  font-size: 14px;
  white-space: pre-wrap;
  border: 1px solid #3a3a3a;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.inline-code {
  background-color: #f0f0f0;
  color: #333;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 14px;
  border: 1px solid #ddd;
}

.user-message .code-block {
  background-color: #0f7b47;
  color: #e0e0e0;
  border-color: #1a8c50;
}

.user-message .inline-code {
  background-color: #128a49;
  color: #e0e0e0;
  border-color: #1a8c50;
}

.md-table {
  border-collapse: collapse;
  width: 100%;
  margin: 12px 0;
  font-size: 14px;
  border: 1px solid #ddd;
}

.md-table th,
.md-table td {
  border: 1px solid #ddd;
  padding: 10px 14px;
  text-align: left;
}

.md-table th {
  background-color: #f2f2f2;
  font-weight: bold;
}

a {
  color: #1890ff;
  text-decoration: none;
}

a:hover {
  text-decoration: underline;
}

/* Mermaid 图表容器样式 */
.mermaid {
  text-align: center;
  margin: 16px 0;
  padding: 12px;
  border-radius: 8px;
  background-color: #fff;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}

.user-message .mermaid {
  background-color: rgba(255, 255, 255, 0.1);
}
</style>