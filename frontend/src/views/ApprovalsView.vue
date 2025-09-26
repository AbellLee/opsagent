<template>
  <div style="padding: 20px">
    <n-card title="审批管理">
      <n-space vertical>
        <n-button @click="loadApprovals" type="primary">刷新审批列表</n-button>
        
        <n-data-table
          :columns="columns"
          :data="approvals"
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
import axios from 'axios'

const message = useMessage()
const loading = ref(false)
const approvals = ref([])

const columns = [
  {
    title: '工具名称',
    key: 'tool_name'
  },
  {
    title: '用户',
    key: 'user_id'
  },
  {
    title: '会话ID',
    key: 'session_id'
  },
  {
    title: '创建时间',
    key: 'created_at'
  },
  {
    title: '操作',
    key: 'actions',
    render(row) {
      return h(NSpace, {}, () => [
        h(NButton, {
          size: 'small',
          type: 'success',
          onClick: () => approveRequest(row)
        }, { default: () => '批准' }),
        h(NButton, {
          size: 'small',
          type: 'error',
          onClick: () => rejectRequest(row)
        }, { default: () => '拒绝' })
      ])
    }
  }
]

// 加载审批列表
const loadApprovals = async () => {
  loading.value = true
  try {
    const response = await axios.get('http://localhost:8000/api/approvals')
    approvals.value = response.data
  } catch (error) {
    message.error('加载审批列表失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

// 批准请求
const approveRequest = async (approval) => {
  try {
    await axios.post(`http://localhost:8000/api/approvals/${approval.id}/approve`)
    message.success('已批准工具执行')
    loadApprovals() // 刷新列表
  } catch (error) {
    message.error('批准失败: ' + error.message)
  }
}

// 拒绝请求
const rejectRequest = async (approval) => {
  try {
    await axios.post(`http://localhost:8000/api/approvals/${approval.id}/reject`)
    message.success('已拒绝工具执行')
    loadApprovals() // 刷新列表
  } catch (error) {
    message.error('拒绝失败: ' + error.message)
  }
}

onMounted(() => {
  loadApprovals()
})
</script>