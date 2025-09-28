<template>
  <div :class="messageClass">
    <div class="message-content">
      <div class="message-text">
        <n-ellipsis v-if="message.role === 'user'" :line-clamp="100" :tooltip="false">
          {{ message.content }}
        </n-ellipsis>
        <div v-else v-html="renderedContent"></div>
      </div>
      <div class="message-time">
        {{ formatTime(message.timestamp) }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { NEllipsis } from 'naive-ui'

const props = defineProps({
  message: {
    type: Object,
    required: true
  }
})

const messageClass = computed(() => {
  return {
    'message': true,
    'user-message': props.message.role === 'user',
    'assistant-message': props.message.role === 'assistant'
  }
})

const renderedContent = computed(() => {
  // 简单的 Markdown 解析，支持代码块和换行
  let content = props.message.content || ''
  
  // 处理代码块
  content = content.replace(/```([\s\S]*?)```/g, '<pre class="code-block"><code>$1</code></pre>')
  
  // 处理行内代码
  content = content.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>')
  
  // 处理换行
  content = content.replace(/\n/g, '<br>')
  
  return content
})

const formatTime = (time) => {
  return new Date(time).toLocaleTimeString('zh-CN', { 
    hour: '2-digit', 
    minute: '2-digit' 
  })
}
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
}

.user-message .message-content {
  background-color: #18a058;
  color: white;
  border-radius: 8px 0 8px 8px;
}

.assistant-message .message-content {
  background-color: #f5f5f5;
  color: #333;
  border-radius: 0 8px 8px 8px;
}

.message-text {
  padding: 12px 16px;
  line-height: 1.5;
}

.message-time {
  font-size: 12px;
  color: #999;
  text-align: right;
  padding: 4px 16px 0 16px;
}

.code-block {
  background-color: #2d2d2d;
  color: #f8f8f2;
  padding: 12px;
  border-radius: 4px;
  overflow-x: auto;
  margin: 8px 0;
  font-family: 'Courier New', monospace;
  font-size: 14px;
}

.inline-code {
  background-color: #f0f0f0;
  color: #333;
  padding: 2px 4px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 14px;
}

.user-message .code-block {
  background-color: #0f7b47;
  color: #e0e0e0;
}

.user-message .inline-code {
  background-color: #128a49;
  color: #e0e0e0;
}
</style>