<template>
  <div class="task-list-container">
    <div class="task-list-header">
      <span class="header-title">任务列表</span>
      <div class="header-actions">
        <n-button 
          text 
          @click="refreshTasks"
          :loading="loading"
          title="刷新任务列表"
        >
          <n-icon size="16">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
              <path d="M17.65 6.35C16.2 4.9 14.21 4 12 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08c-.82 2.33-3.04 4-5.65 4-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"/>
            </svg>
          </n-icon>
        </n-button>
      </div>
    </div>
    
    <n-scrollbar class="task-list-content">
      <div v-if="tasks.length === 0" class="empty-state">
        <n-empty description="暂无任务" size="small">
          <template #extra>
            <span class="empty-hint">Agent执行任务时会在这里显示</span>
          </template>
        </n-empty>
      </div>
      
      <div v-else class="task-items">
        <div 
          v-for="task in rootTasks" 
          :key="task.id" 
          class="task-item-wrapper"
        >
          <TaskItem 
            :task="task"
            :all-tasks="tasks"
            :get-task-status-text="getTaskStatusText"
            :get-task-status-type="getTaskStatusType"
            :format-time="formatTime"
          />
        </div>
      </div>
    </n-scrollbar>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import { NButton, NIcon, NScrollbar, NEmpty, NTag } from 'naive-ui'
import { taskAPI } from '../api'
import TaskItem from './TaskItem.vue'

const props = defineProps({
  sessionId: {
    type: String,
    required: true
  }
})

// 任务状态映射
const TASK_STATUS_MAP = {
  'PENDING': '待处理',
  'IN_PROGRESS': '进行中',
  'COMPLETE': '已完成',
  'CANCELLED': '已取消',
  'ERROR': '错误'
}

const TASK_STATUS_TYPE = {
  'PENDING': 'info',
  'IN_PROGRESS': 'warning',
  'COMPLETE': 'success',
  'CANCELLED': 'default',
  'ERROR': 'error'
}

// 响应式数据
const tasks = ref([])
const loading = ref(false)
const websocket = ref(null)
const reconnectAttempts = ref(0)
const maxReconnectAttempts = ref(5)
const reconnectDelay = ref(1000)
const heartbeatInterval = ref(null)

// 计算根任务（没有父任务的任务）
const rootTasks = computed(() => {
  return tasks.value.filter(task => !task.parent_task_id)
})

// 获取任务状态显示文本
const getTaskStatusText = (status) => {
  return TASK_STATUS_MAP[status] || status
}

// 获取任务状态标签类型
const getTaskStatusType = (status) => {
  return TASK_STATUS_TYPE[status] || 'default'
}

// 格式化时间
const formatTime = (timeString) => {
  if (!timeString) return ''
  const date = new Date(timeString)
  return date.toLocaleString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 刷新任务列表
const refreshTasks = async () => {
  if (!props.sessionId) return
  
  loading.value = true
  try {
    const response = await taskAPI.list(props.sessionId)
    tasks.value = response.tasks || []
    console.log('任务列表已刷新:', tasks.value)
  } catch (error) {
    console.error('获取任务列表失败:', error)
  } finally {
    loading.value = false
  }
}

// 发送心跳包
const sendHeartbeat = () => {
  if (websocket.value && websocket.value.readyState === WebSocket.OPEN) {
    websocket.value.send(JSON.stringify({ type: 'heartbeat' }))
  }
}

// 初始化WebSocket连接
const initWebSocket = () => {
  if (!props.sessionId) return

  // 关闭现有的连接和心跳
  if (websocket.value) {
    websocket.value.close()
  }
  
  if (heartbeatInterval.value) {
    clearInterval(heartbeatInterval.value)
    heartbeatInterval.value = null
  }

  // 创建新的WebSocket连接
  const protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://'
  const wsUrl = `${protocol}${window.location.host}/api/tasks/ws/${props.sessionId}`
  websocket.value = new WebSocket(wsUrl)

  websocket.value.onopen = () => {
    console.log('任务WebSocket连接已建立')
    // 重置重连尝试次数
    reconnectAttempts.value = 0
    
    // 启动心跳机制
    heartbeatInterval.value = setInterval(sendHeartbeat, 30000) // 每30秒发送一次心跳
  }

  websocket.value.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      console.log('收到WebSocket消息:', data)
      if (data.type === 'task_update') {
        // 更新任务列表
        console.log('收到任务更新通知，正在刷新任务列表...')
        refreshTasks()
      }
    } catch (error) {
      console.error('解析WebSocket消息失败:', error)
    }
  }

  websocket.value.onerror = (error) => {
    console.error('任务WebSocket连接错误:', error)
  }

  websocket.value.onclose = (event) => {
    console.log('任务WebSocket连接已关闭:', event.code, event.reason)
    
    // 清理心跳机制
    if (heartbeatInterval.value) {
      clearInterval(heartbeatInterval.value)
      heartbeatInterval.value = null
    }
    
    // 实现重连机制
    if (reconnectAttempts.value < maxReconnectAttempts.value) {
      reconnectAttempts.value++
      console.log(`尝试重新连接 (${reconnectAttempts.value}/${maxReconnectAttempts.value})...`)
      setTimeout(() => {
        initWebSocket()
      }, reconnectDelay.value * reconnectAttempts.value) // 逐渐增加延迟
    } else {
      console.log('达到最大重连次数，停止重连')
    }
  }
}

// 关闭WebSocket连接
const closeWebSocket = () => {
  if (websocket.value) {
    websocket.value.close()
    websocket.value = null
  }
  
  if (heartbeatInterval.value) {
    clearInterval(heartbeatInterval.value)
    heartbeatInterval.value = null
  }
}

// 监听会话ID变化
watch(() => props.sessionId, (newSessionId) => {
  if (newSessionId) {
    refreshTasks()
    initWebSocket()
  } else {
    closeWebSocket()
  }
})

onMounted(() => {
  if (props.sessionId) {
    refreshTasks()
    initWebSocket()
  }
})

onUnmounted(() => {
  closeWebSocket()
})
</script>

<style scoped>
.task-list-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  background-color: #fafafa;
  border-left: 1px solid #e0e0e0;
}

.task-list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #e0e0e0;
  background-color: #ffffff;
}

.header-title {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.task-list-content {
  flex: 1;
  padding: 12px;
}

.empty-state {
  padding: 24px 0;
}

.empty-hint {
  font-size: 12px;
  color: #999;
}

.task-items {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* 暗色主题适配 */
html.dark .task-list-container {
  background-color: #1e1e1e;
  border-left: 1px solid #333;
}

html.dark .task-list-header {
  background-color: #2d2d2d;
  border-bottom: 1px solid #333;
}

html.dark .header-title {
  color: #e0e0e0;
}
</style>