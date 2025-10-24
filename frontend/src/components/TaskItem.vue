<template>
  <div class="task-item" :class="`task-status-${task.status.toLowerCase()}`">
    <div class="task-header" @click="toggleExpanded">
      <div class="task-header-main">
        <n-icon v-if="hasChildren" class="expand-icon" size="16">
          <svg v-if="expanded" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
            <path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6-1.41-1.41z"/>
          </svg>
          <svg v-else xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
            <path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41z"/>
          </svg>
        </n-icon>
        <div class="task-id">#{{ task.id }}</div>
      </div>
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
    </div>
    
    <!-- 子任务 -->
    <div v-if="expanded && hasChildren" class="sub-tasks">
      <div v-for="child in childTasks" :key="child.id" class="sub-task-item">
        <!-- 子任务使用简化版显示，避免递归组件引用 -->
        <div class="task-item" :class="`task-status-${child.status.toLowerCase()}`">
          <div class="task-header">
            <div class="task-header-main">
              <div class="task-id">#{{ child.id }}</div>
            </div>
            <n-tag 
              :type="getTaskStatusType(child.status)"
              size="small"
              class="task-status-tag"
            >
              {{ getTaskStatusText(child.status) }}
            </n-tag>
          </div>
          
          <div class="task-content">
            {{ child.content }}
          </div>
          
          <div class="task-meta">
            <div class="task-time">
              <n-icon size="12">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8z"/>
                  <path d="M12.5 7H11v6l5.25 3.15.75-1.23-4.5-2.67z"/>
                </svg>
              </n-icon>
              <span>{{ formatTime(child.created_at) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { NIcon, NTag } from 'naive-ui'

const props = defineProps({
  task: {
    type: Object,
    required: true
  },
  allTasks: {
    type: Array,
    required: true
  },
  getTaskStatusText: {
    type: Function,
    required: true
  },
  getTaskStatusType: {
    type: Function,
    required: true
  },
  formatTime: {
    type: Function,
    required: true
  }
})

// 展开状态
const expanded = ref(false)

// 计算是否有子任务
const hasChildren = computed(() => {
  return props.allTasks.some(t => t.parent_task_id === props.task.id)
})

// 计算子任务
const childTasks = computed(() => {
  return props.allTasks.filter(t => t.parent_task_id === props.task.id)
})

// 切换展开状态
const toggleExpanded = () => {
  if (hasChildren.value) {
    expanded.value = !expanded.value
  }
}
</script>

<style scoped>
.task-item {
  padding: 12px;
  border-radius: 12px;
  background-color: #ffffff;
  border: 1px solid #e8e8e8;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  transition: all 0.2s ease;
}

.task-item:hover {
  box-shadow: 0 2px 8px rgba(168, 216, 234, 0.1);
  border-color: #d9d9d9;
}

.task-item.task-status-complete {
  border-left: 3px solid #52c41a;
}

.task-item.task-status-in_progress {
  border-left: 3px solid #fa8c16;
}

.task-item.task-status-pending {
  border-left: 3px solid #a8d8ea;
}

.task-item.task-status-cancelled {
  border-left: 3px solid #fcbad3;
}

.task-item.task-status-error {
  border-left: 3px solid #ff4d4f;
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  cursor: pointer;
}

.task-header-main {
  display: flex;
  align-items: center;
  gap: 6px;
}

.expand-icon {
  transition: transform 0.2s ease;
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

.task-time {
  display: flex;
  align-items: center;
  gap: 4px;
}

.sub-tasks {
  margin-top: 12px;
  padding-left: 16px;
  border-left: 2px solid #f0f0f0;
}

.sub-task-item {
  margin-bottom: 8px;
}

.sub-task-item:last-child {
  margin-bottom: 0;
}

/* 暗色主题适配 */
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

html.dark .sub-tasks {
  border-left: 2px solid #333;
}
</style>