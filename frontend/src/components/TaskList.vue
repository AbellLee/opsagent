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
import { ref, onMounted, onUnmounted, watch, computed, onBeforeUnmount } from 'vue'
import { NButton, NIcon, NScrollbar, NEmpty, NTag } from 'naive-ui'
import { taskAPI } from '../api'
import TaskItem from './TaskItem.vue'
import { useSessionStore } from '../stores/session'

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
const sessionStore = useSessionStore()
let taskUpdateHandler = null

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

// 通过全局事件监听任务更新
const initTaskUpdateListener = () => {
  // 定义任务更新处理函数
  taskUpdateHandler = (event) => {
    try {
      const data = JSON.parse(event.data)
      if (data.type === 'task_update' && data.session_id === props.sessionId) {
        // 更新任务列表
        console.log('收到任务更新通知，正在刷新任务列表...')
        refreshTasks()
      }
    } catch (error) {
      console.error('解析WebSocket消息失败:', error)
    }
  }
  
  // 添加事件监听器
  if (sessionStore.websocket) {
    sessionStore.websocket.addEventListener('message', taskUpdateHandler)
  }
}

// 移除任务更新监听器
const removeTaskUpdateListener = () => {
  if (taskUpdateHandler && sessionStore.websocket) {
    sessionStore.websocket.removeEventListener('message', taskUpdateHandler)
    taskUpdateHandler = null
  }
}

// 监听WebSocket连接事件
const handleWebsocketConnected = (event) => {
  // 确保是当前会话的连接
  if (event.detail.sessionId === props.sessionId) {
    // 移除旧的监听器
    removeTaskUpdateListener()
    // 初始化新的任务更新监听器
    initTaskUpdateListener()
  }
}

// 监听会话ID变化
watch(() => props.sessionId, (newSessionId) => {
  if (newSessionId) {
    refreshTasks()
    // 移除旧的监听器
    removeTaskUpdateListener()
    // 初始化新的任务更新监听器（如果WebSocket已存在）
    if (sessionStore.websocket) {
      initTaskUpdateListener()
    }
  } else {
    removeTaskUpdateListener()
  }
})

onMounted(() => {
  if (props.sessionId) {
    refreshTasks()
    // 初始化任务更新监听器（如果WebSocket已存在）
    if (sessionStore.websocket) {
      initTaskUpdateListener()
    }
    // 添加WebSocket连接事件监听器
    window.addEventListener('websocket-connected', handleWebsocketConnected)
  }
})

onUnmounted(() => {
  // 移除任务更新监听器
  removeTaskUpdateListener()
  // 移除WebSocket连接事件监听器
  window.removeEventListener('websocket-connected', handleWebsocketConnected)
})
</script>

<style scoped>
.task-list-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  background-color: #fafafa;
  border-left: 1px solid #e0e0e0;
  border-radius: 0 12px 12px 0;
}

.task-list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #e0e0e0;
  background: linear-gradient(135deg, #a8d8ea 0%, #aa96da 100%);
  border-radius: 0 12px 0 0;
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
  background: linear-gradient(135deg, #a8d8ea 0%, #aa96da 100%);
  border-bottom: 1px solid #333;
}

html.dark .header-title {
  color: #e0e0e0;
}
</style>