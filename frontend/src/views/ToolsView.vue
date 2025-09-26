<template>
  <div style="padding: 20px">
    <n-card title="工具管理">
      <n-space vertical>
        <n-button @click="loadTools" type="primary">刷新工具列表</n-button>
        
        <n-data-table
          :columns="columns"
          :data="tools"
          :loading="loading"
          striped
        />
      </n-space>
    </n-card>
  </div>
</template>

<script setup>
import { ref, onMounted, h } from 'vue'
import { 
  NCard, 
  NButton, 
  NSpace, 
  NDataTable,
  useMessage
} from 'naive-ui'
import { toolAPI } from '../api'

const message = useMessage()
const loading = ref(false)
const tools = ref([])

const columns = [
  {
    title: '工具名称',
    key: 'name'
  },
  {
    title: '描述',
    key: 'description'
  },
  {
    title: '类型',
    key: 'type'
  },
  {
    title: '操作',
    key: 'actions',
    render(row) {
      return h(NSpace, {}, () => [
        h(NButton, {
          size: 'small',
          onClick: () => configureApproval(row)
        }, { default: () => '配置审批' })
      ])
    }
  }
]

// 加载工具列表
const loadTools = async () => {
  loading.value = true
  try {
    const response = await toolAPI.list()
    tools.value = response.map(tool => ({
      ...tool,
      type: tool.type || 'Custom'
    }))
  } catch (error) {
    message.error('加载工具列表失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

// 配置工具审批
const configureApproval = (tool) => {
  message.info(`配置工具 ${tool.name} 的审批规则`)
  // 在实际应用中，这里应该打开一个模态框来配置审批规则
}

onMounted(() => {
  loadTools()
})
</script>