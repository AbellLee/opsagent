<template>
  <div class="message-row" :style="messageStyle">
    <div class="message-bubble" :style="bubbleStyle">
      <!-- 消息头部（非用户消息显示） -->
      <div
        class="message-header"
        v-if="message.role !== 'user'"
        style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;"
      >
        <div style="font-weight: bold; font-size: 12px;" :style="{ color: headerColor }">
          {{ senderName }}
        </div>
        <n-button text size="tiny" @click="copyToClipboard">
          <n-icon>
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
              <path d="M7 4V2C7 1.45 7.45 1 8 1H20C20.55 1 21 1.45 21 2V16C21 16.55 20.55 17 20 17H18V19C18 20.1 17.1 21 16 21H4C2.9 21 2 20.1 2 19V7C2 5.9 2.9 5 4 5H6V4H7ZM4 7V19H16V17H14C12.9 17 12 16.1 12 15V7C12 5.9 12.9 5 14 5H16V3H8V5H10C11.1 5 12 5.9 12 7V15C12 16.1 11.1 17 10 17H4V7ZM6 5V4H4V5H6Z"/>
            </svg>
          </n-icon>
        </n-button>
      </div>

      <!-- 消息内容 -->
      <div
        ref="contentRef"
        class="message-content"
        v-html="formattedContent"
      ></div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch, nextTick } from 'vue'
import { NButton, NIcon } from 'naive-ui'
import { parseMarkdown } from '../utils/markdown'

const props = defineProps({
  message: {
    type: Object,
    required: true,
    default: () => ({
      role: 'assistant',
      content: '',
      timestamp: ''
    }),
    validator: (value) => {
      if (!value || typeof value !== 'object') return false
      if (!value.role || typeof value.role !== 'string') return false
      return ['user', 'assistant', 'system'].includes(value.role)
    }
  }
})

// 计算消息样式
const messageStyle = computed(() => {
  return {
    justifyContent: props.message.role === 'user' ? 'flex-end' :
                   props.message.role === 'system' ? 'center' : 'flex-start'
  }
})

// 计算消息气泡样式
const bubbleStyle = computed(() => {
  const baseStyle = {
    borderRadius: '12px',
    padding: '12px 16px',
    maxWidth: '80%',
    wordWrap: 'break-word',
    position: 'relative',
    boxShadow: '0 1px 2px rgba(0,0,0,0.1)'
  }

  if (props.message.role === 'user') {
    return {
      ...baseStyle,
      backgroundColor: '#409eff',
      color: '#fff',
      marginLeft: 'auto',
      marginRight: '0'
    }
  } else if (props.message.role === 'assistant') {
    return {
      ...baseStyle,
      backgroundColor: '#f0f5ff',
      color: '#333',
      marginRight: 'auto',
      marginLeft: '0'
    }
  } else {
    return {
      ...baseStyle,
      backgroundColor: '#fff7e6',
      color: '#333',
      margin: '0 auto',
      maxWidth: '90%'
    }
  }
})

// 计算发送者名称
const senderName = computed(() => {
  switch (props.message.role) {
    case 'user': return '你'
    case 'assistant': return 'AI助手'
    case 'system': return '系统消息'
    default: return '未知'
  }
})

// 计算头部颜色
const headerColor = computed(() => {
  switch (props.message.role) {
    case 'assistant': return '#409eff'
    case 'system': return '#e6a23c'
    default: return '#409eff'
  }
})

// 处理消息内容，支持Markdown格式
const formattedContent = computed(() => {
  if (!props.message.content) return ''
  return parseMarkdown(props.message.content)
})

// 用于触发代码高亮的引用
const contentRef = ref(null)

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



// 复制消息内容到剪贴板
const copyToClipboard = async () => {
  try {
    await navigator.clipboard.writeText(props.message.content)
    // 可以添加一个提示，比如notification
  } catch (err) {
    console.error('复制失败:', err)
  }
}

// 在组件挂载后触发代码高亮
onMounted(() => {
  highlightCode()
})

// 监听内容变化，重新高亮代码
watch(() => props.message.content, () => {
  highlightCode()
})
</script>

<style scoped>
.message-row {
  display: flex;
  margin-bottom: 16px;
  animation: fadeIn 0.3s ease-out;
}

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




</style>