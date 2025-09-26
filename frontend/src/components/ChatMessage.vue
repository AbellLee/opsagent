<template>
  <div class="message-row" :style="messageStyle">
    <div class="message-bubble" :style="bubbleStyle">
      <div 
        v-if="message.role !== 'user'" 
        class="message-header"
      >
        <div class="message-sender">
          {{ message.role === 'assistant' ? 'AI助手' : '系统消息' }}
        </div>
        <n-button 
          text 
          size="tiny" 
          @click="copyToClipboard"
          class="copy-button"
        >
          <n-icon size="16">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
              <path d="M7 4V2C7 1.45 7.45 1 8 1H20C20.55 1 21 1.45 21 2V16C21 16.55 20.55 17 20 17H18V19C18 20.1 17.1 21 16 21H4C2.9 21 2 20.1 2 19V7C2 5.9 2.9 5 4 5H6V4H7ZM4 7V19H16V17H14C12.9 17 12 16.1 12 15V7C12 5.9 12.9 5 14 5H16V3H8V5H10C11.1 5 12 5.9 12 7V15C12 16.1 11.1 17 10 17H4V7ZM6 5V4H4V5H6Z"/>
            </svg>
          </n-icon>
        </n-button>
      </div>
      <div 
        ref="contentRef"
        class="message-content" 
        v-html="formattedContent"
      ></div>
      <div class="message-time">
        {{ formatTime(message.timestamp) }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, watch, nextTick } from 'vue'
import { useMessage } from 'naive-ui'

const props = defineProps({
  message: {
    type: Object,
    required: true
  }
})

const message = useMessage()
const contentRef = ref(null)

// 计算消息样式
const messageStyle = computed(() => {
  return {
    justifyContent: props.message.role === 'user' ? 'flex-end' : 'flex-start'
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

// 处理消息内容，支持简单格式化
const formattedContent = computed(() => {
  if (!props.message.content) return ''
  // 简单的格式化处理，将换行符转换为<br>
  return props.message.content.replace(/\n/g, '<br>')
})

// 格式化时间
const formatTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', { 
    hour: '2-digit', 
    minute: '2-digit' 
  })
}

// 复制消息内容到剪贴板
const copyToClipboard = async () => {
  try {
    await navigator.clipboard.writeText(props.message.content)
    message.success('消息已复制到剪贴板')
  } catch (err) {
    console.error('复制失败:', err)
    message.error('复制失败')
  }
}

// 模拟代码高亮函数（简化版）
const highlightCode = async () => {
  // 在实际应用中，这里可以集成 Prism.js 或其他代码高亮库
  // 暂时留空，作为占位符
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

.message-bubble {
  position: relative;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.message-sender {
  font-weight: bold;
  font-size: 12px;
  color: #409eff;
}

.copy-button {
  opacity: 0;
  transition: opacity 0.2s;
}

.message-bubble:hover .copy-button {
  opacity: 1;
}

.message-content {
  line-height: 1.6;
}

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

.message-time {
  font-size: 10px;
  margin-top: 6px;
  opacity: 0.7;
  text-align: right;
}
</style>