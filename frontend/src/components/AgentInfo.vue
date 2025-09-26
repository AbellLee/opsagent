<template>
  <n-drawer :show="show" @update:show="handleUpdateShow" :width="500" placement="right">
    <n-drawer-content :native-scrollbar="false" closable>
      <template #header>
        <div class="agent-header">
          <n-avatar round size="small">
            <n-icon>
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2C13.1 2 14 2.9 14 4C14 5.1 13.1 6 12 6C10.9 6 10 5.1 10 4C10 2.9 10.9 2 12 2ZM21 9V7L15 1H5C3.9 1 3 1.9 3 3V7C3 7 3 7 3 7L1 7V9C1 9 1 9 1 9H3V15C3 16.1 3.9 17 5 17H11V19H9C8.4 19 8 19.4 8 20C8 20.6 8.4 21 9 21H15C15.6 21 16 20.6 16 20C16 19.4 15.6 19 15 19H13V17H19C20.1 17 21 16.1 21 15V9H21ZM5 15V8H19V15H5Z"/>
              </svg>
            </n-icon>
          </n-avatar>
          <div class="agent-header-text">
            <h3>{{ agentStore.agentInfo.name || 'Agent信息' }}</h3>
            <div class="agent-header-description">智能代理配置</div>
          </div>
        </div>
      </template>
      
      <n-spin :show="agentStore.loading">
        <div class="agent-content">
          <!-- 基本信息卡片 -->
          <n-card title="基本信息" size="small" embedded :bordered="false">
            <n-descriptions label-placement="left" :column="1" size="small">
              <n-descriptions-item label="名称">
                <n-tag type="primary">{{ agentStore.agentInfo.name || '未设置' }}</n-tag>
              </n-descriptions-item>
              <n-descriptions-item label="描述">
                {{ agentStore.agentInfo.description || '暂无描述' }}
              </n-descriptions-item>
              <n-descriptions-item label="工具数量">
                <n-tag type="success">{{ agentStore.agentInfo.tools?.length || 0 }} 个</n-tag>
              </n-descriptions-item>
            </n-descriptions>
          </n-card>
          
          <!-- 可用工具卡片 -->
          <n-card title="可用工具" size="small" embedded :bordered="false" class="tools-card">
            <div v-if="agentStore.agentInfo.tools && agentStore.agentInfo.tools.length > 0">
              <n-collapse :default-expanded-names="[]">
                <n-collapse-item 
                  v-for="(tool, index) in categorizedTools" 
                  :key="index"
                  :title="tool.name"
                  :name="index"
                >
                  <template #header>
                    <div class="tool-header">
                      <div>{{ tool.name }}</div>
                      <n-tag size="small" type="info">
                        工具
                      </n-tag>
                    </div>
                  </template>
                  <div class="tool-content">
                    <div class="tool-description">{{ tool.description }}</div>
                    <n-alert 
                      v-if="tool.examples && tool.examples.length > 0" 
                      type="info" 
                      :show-icon="false" 
                      class="tool-examples"
                    >
                      <template #header>
                        <strong>使用示例</strong>
                      </template>
                      <div 
                        v-for="(example, exIndex) in tool.examples" 
                        :key="exIndex" 
                        class="tool-example"
                      >
                        <n-text code>{{ example }}</n-text>
                      </div>
                    </n-alert>
                  </div>
                </n-collapse-item>
              </n-collapse>
            </div>
            
            <div v-else>
              <n-empty description="暂无可用工具" size="small">
                <template #extra>
                  <n-button size="small" @click="agentStore.fetchAgentInfo">刷新</n-button>
                </template>
              </n-empty>
            </div>
          </n-card>
          
          <!-- 系统信息卡片 -->
          <n-card title="系统信息" size="small" embedded :bordered="false" class="system-card">
            <n-descriptions label-placement="left" :column="1" size="small">
              <n-descriptions-item label="状态">
                <n-tag type="success">在线</n-tag>
              </n-descriptions-item>
              <n-descriptions-item label="版本">
                <n-tag>1.0.0</n-tag>
              </n-descriptions-item>
            </n-descriptions>
          </n-card>
        </div>
      </n-spin>
      
      <template #footer>
        <div class="agent-footer">
          <n-button @click="agentStore.fetchAgentInfo" size="small">
            <template #icon>
              <n-icon size="16">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M17.65 6.35C16.2 4.9 14.21 4 12 4C9.79 4 7.8 4.9 6.35 6.35C4.9 7.8 4 9.79 4 12C4 14.21 4.9 16.2 6.35 17.65C7.8 19.1 9.79 20 12 20C14.21 20 16.2 19.1 17.65 17.65C19.1 16.2 20 14.21 20 12C20 9.79 19.1 7.8 17.65 6.35ZM12 22C6.47 22 2 17.5 2 12S6.47 2 12 2C17.53 2 22 6.5 22 12S17.53 22 12 22ZM13 12H16L12 16L8 12H11V8H13V12Z"/>
                </svg>
              </n-icon>
            </template>
            刷新
          </n-button>
          <n-button @click="closeDrawer" size="small" type="primary">
            关闭
          </n-button>
        </div>
      </template>
    </n-drawer-content>
  </n-drawer>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useAgentStore } from '../stores/agent'

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:show'])

const agentStore = useAgentStore()

// 关闭抽屉
const closeDrawer = () => {
  emit('update:show', false)
}

// 处理抽屉显示状态变化
const handleUpdateShow = (value) => {
  emit('update:show', value)
}

// 计算工具分类
const categorizedTools = computed(() => {
  if (!agentStore.agentInfo.tools || agentStore.agentInfo.tools.length === 0) {
    return []
  }
  
  // 这里可以按类别分组工具，暂时按字母顺序排序
  return [...agentStore.agentInfo.tools].sort((a, b) => a.name.localeCompare(b.name))
})
</script>

<style scoped>
.agent-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.agent-header-text h3 {
  margin: 0;
}

.agent-header-description {
  font-size: 12px;
  color: #999;
}

.agent-content {
  padding: 16px;
}

.tools-card {
  margin-top: 16px;
}

.system-card {
  margin-top: 16px;
}

.tool-header {
  display: flex;
  justify-content: space-between;
  width: 100%;
  align-items: center;
}

.tool-content {
  padding: 8px 0;
}

.tool-description {
  margin-bottom: 8px;
}

.tool-examples {
  margin-top: 8px;
}

.tool-example {
  margin-top: 4px;
}

.agent-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

:deep(.n-collapse-item__header) {
  border-radius: 4px;
  margin-bottom: 4px;
}

:deep(.n-collapse-item) {
  margin-bottom: 8px;
  border-radius: 4px;
}
</style>