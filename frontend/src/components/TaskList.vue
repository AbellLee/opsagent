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
          v-for="task in tasks" 
          :key="task.id" 
          class="task-item"
          :class="`task-status-${task.status.toLowerCase()}`"
        >
          <div class="task-header">
            <div class="task-id">#{{ task.id }}</div>
            <n-tag 
              :type="getTaskStatusType(task.status)"
              size="small"
              class="task-status-tag"
            >
              {{ getTaskStatusText(task.status) }}
            </n-tag>
          </div>
          
          <div class="task-content">
            {{ task.content }}
          </div>
          
          <div class="task-meta">
            <div class="task-time">
              <n-icon size="12">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8z"/>
                  <path d="M12.5 7H11v6l5.25 3.15.75-1.23-4.5-2.67z"/>
                </svg>
              </n-icon>
              <span>{{ formatTime(task.created_at) }}</span>
            </div>
            
            <div v-if="task.parent_task_id" class="task-parent">
              <n-icon size="12">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 12l8-8H4l8 8zm0 2l-8 8h16l-8-8z"/>
                </svg>
              </n-icon>
              <span>父任务: #{{ task.parent_task_id }}</span>
            </div>
          </div>
        </div>
      </div>
    </n-scrollbar>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { NButton, NIcon, NScrollbar, NEmpty, NTag } from 'naive-ui'
import { taskAPI } from '../api'

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
const refreshInterval = ref(null)

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
  } catch (error) {
    console.error('获取任务列表失败:', error)
  } finally {
    loading.value = false
  }
}

// 设置定时刷新
const startAutoRefresh = () => {
  refreshInterval.value = setInterval(() => {
    refreshTasks()
  }, 10000) // 每10秒刷新一次
}

// 停止定时刷新
const stopAutoRefresh = () => {
  if (refreshInterval.value) {
    clearInterval(refreshInterval.value)
    refreshInterval.value = null
  }
}

// 监听会话ID变化
watch(() => props.sessionId, (newSessionId) => {
  if (newSessionId) {
    refreshTasks()
  }
})

onMounted(() => {
  if (props.sessionId) {
    refreshTasks()
  }
  startAutoRefresh()
})

onUnmounted(() => {
  stopAutoRefresh()
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

.task-item {
  padding: 12px;
  border-radius: 8px;
  background-color: #ffffff;
  border: 1px solid #e8e8e8;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  transition: all 0.2s ease;
}

.task-item:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border-color: #d9d9d9;
}

.task-item.task-status-complete {
  border-left: 3px solid #52c41a;
}

.task-item.task-status-in_progress {
  border-left: 3px solid #fa8c16;
}

.task-item.task-status-pending {
  border-left: 3px solid #1890ff;
}

.task-item.task-status-cancelled {
  border-left: 3px solid #999;
}

.task-item.task-status-error {
  border-left: 3px solid #ff4d4f;
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.task-id {
  font-size: 12px;
  font-weight: 600;
  color: #666;
}

.task-status-tag {
  font-size: 10px;
}

.task-content {
  font-size: 13px;
  color: #333;
  line-height: 1.4;
  margin-bottom: 10px;
  word-break: break-word;
}

.task-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 11px;
  color: #999;
}

.task-time,
.task-parent {
  display: flex;
  align-items: center;
  gap: 4px;
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

html.dark .task-item {
  background-color: #2d2d2d;
  border: 1px solid #333;
}

html.dark .task-content {
  color: #e0e0e0;
}

html.dark .task-id,
html.dark .task-meta {
  color: #aaa;
}
</style>