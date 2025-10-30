<template>
  <div class="dify-agent-panel">
    <!-- 工具栏 -->
    <div class="dify-toolbar">
      <n-space>
        <n-button type="primary" @click="showCreateModal = true">
          <template #icon>
            <n-icon><Add /></n-icon>
          </template>
          新增 Agent
        </n-button>
        <n-button @click="loadAgents">
          <template #icon>
            <n-icon><Refresh /></n-icon>
          </template>
          刷新列表
        </n-button>
        <n-button @click="handleRefreshCache" :loading="refreshing" type="success">
          <template #icon>
            <n-icon><Refresh /></n-icon>
          </template>
          刷新缓存
        </n-button>
        <n-switch v-model:value="showEnabledOnly" @update:value="loadAgents">
          <template #checked>只显示启用的</template>
          <template #unchecked>显示全部</template>
        </n-switch>
      </n-space>
    </div>

    <!-- Agent 列表 -->
    <div class="dify-agent-list">
      <n-data-table
        :columns="columns"
        :data="agents"
        :loading="loading"
        :pagination="false"
        size="small"
        striped
      />
    </div>

    <!-- 新增/编辑 Agent 弹窗 -->
    <n-modal
      v-model:show="showCreateModal"
      preset="card"
      :title="editingAgent ? '编辑 Agent' : '新增 Agent'"
      style="width: 600px;"
    >
      <n-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-placement="left"
        label-width="100px"
      >
        <n-form-item label="名称" path="name">
          <n-input v-model:value="formData.name" placeholder="Agent 名称" />
        </n-form-item>

        <n-form-item label="描述" path="description">
          <n-input
            v-model:value="formData.description"
            type="textarea"
            placeholder="Agent 描述（可选）"
            :rows="2"
          />
        </n-form-item>

        <n-form-item label="类型" path="agent_type">
          <n-select
            v-model:value="formData.agent_type"
            :options="agentTypeOptions"
            placeholder="选择 Agent 类型"
          />
        </n-form-item>

        <n-form-item label="Dify App ID" path="dify_app_id">
          <n-input v-model:value="formData.dify_app_id" placeholder="app-xxx" />
        </n-form-item>

        <n-form-item label="API Key" path="api_key">
          <n-input
            v-model:value="formData.api_key"
            type="password"
            show-password-on="click"
            placeholder="Dify API Key"
          />
        </n-form-item>

        <n-form-item label="Base URL" path="base_url">
          <n-input
            v-model:value="formData.base_url"
            placeholder="https://api.dify.ai/v1"
          />
        </n-form-item>

        <n-form-item label="能力标签" path="capabilities">
          <n-dynamic-tags v-model:value="formData.capabilities" />
        </n-form-item>

        <n-form-item label="关键词" path="keywords">
          <n-dynamic-tags v-model:value="formData.keywords" />
        </n-form-item>

        <n-form-item label="优先级" path="priority">
          <n-input-number
            v-model:value="formData.priority"
            :min="0"
            :max="100"
            placeholder="0-100"
            style="width: 100%"
          />
        </n-form-item>

        <n-form-item label="启用" path="enabled">
          <n-switch v-model:value="formData.enabled" />
        </n-form-item>
      </n-form>

      <template #action>
        <n-space justify="end">
          <n-button @click="handleCancel">取消</n-button>
          <n-button type="primary" @click="handleSubmit" :loading="submitting">
            {{ editingAgent ? '更新' : '创建' }}
          </n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- 测试 Agent 弹窗 -->
    <n-modal
      v-model:show="showTestModal"
      preset="card"
      title="测试 Agent"
      style="width: 500px;"
    >
      <n-form>
        <n-form-item label="测试消息">
          <n-input
            v-model:value="testMessage"
            type="textarea"
            placeholder="输入测试消息"
            :rows="3"
          />
        </n-form-item>
      </n-form>

      <template #action>
        <n-space justify="end">
          <n-button @click="showTestModal = false">取消</n-button>
          <n-button type="primary" @click="handleTest" :loading="testing">
            测试
          </n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, h } from 'vue'
import {
  NButton,
  NSpace,
  NSwitch,
  NDataTable,
  NModal,
  NForm,
  NFormItem,
  NInput,
  NInputNumber,
  NSelect,
  NDynamicTags,
  NIcon,
  NTag,
  NPopconfirm
} from 'naive-ui'
import { createDiscreteApi } from 'naive-ui'
import { Add, Refresh, Edit, Trash, Play } from '@vicons/ionicons5'
import { difyAgentAPI } from '../api'

const { message } = createDiscreteApi(['message'])

// 响应式数据
const agents = ref([])
const loading = ref(false)
const refreshing = ref(false)
const showEnabledOnly = ref(false)
const showCreateModal = ref(false)
const showTestModal = ref(false)
const submitting = ref(false)
const testing = ref(false)
const editingAgent = ref(null)
const testingAgent = ref(null)
const formRef = ref(null)
const testMessage = ref('你好')

// 表单数据
const formData = reactive({
  name: '',
  description: '',
  agent_type: 'chatbot',
  dify_app_id: '',
  api_key: '',
  base_url: 'https://api.dify.ai/v1',
  capabilities: [],
  keywords: [],
  priority: 0,
  enabled: true
})

// Agent 类型选项
const agentTypeOptions = [
  { label: 'Chatbot', value: 'chatbot' },
  { label: 'Workflow', value: 'workflow' },
  { label: 'Agent', value: 'agent' }
]

// 表单验证规则
const formRules = {
  name: [
    { required: true, message: '请输入 Agent 名称', trigger: 'blur' }
  ],
  agent_type: [
    { required: true, message: '请选择 Agent 类型', trigger: 'change' }
  ],
  dify_app_id: [
    { required: true, message: '请输入 Dify App ID', trigger: 'blur' }
  ],
  api_key: [
    { required: true, message: '请输入 API Key', trigger: 'blur' }
  ],
  base_url: [
    { required: true, message: '请输入 Base URL', trigger: 'blur' }
  ]
}

// 表格列定义
const columns = [
  {
    title: '名称',
    key: 'name',
    width: 120
  },
  {
    title: '描述',
    key: 'description',
    ellipsis: {
      tooltip: true
    }
  },
  {
    title: '类型',
    key: 'agent_type',
    width: 100,
    render: (row) => {
      const typeMap = {
        chatbot: { type: 'info', text: 'Chatbot' },
        workflow: { type: 'success', text: 'Workflow' },
        agent: { type: 'warning', text: 'Agent' }
      }
      const config = typeMap[row.agent_type] || { type: 'default', text: row.agent_type }
      return h(NTag, { type: config.type, size: 'small' }, { default: () => config.text })
    }
  },
  {
    title: '优先级',
    key: 'priority',
    width: 70
  },
  {
    title: '状态',
    key: 'enabled',
    width: 70,
    render: (row) => {
      return h(NSwitch, {
        value: row.enabled,
        size: 'small',
        onUpdateValue: () => toggleAgent(row)
      })
    }
  },
  {
    title: '操作',
    key: 'actions',
    width: 150,
    render: (row) => {
      return h(NSpace, { size: 'small' }, {
        default: () => [
          h(NButton, {
            size: 'small',
            type: 'primary',
            ghost: true,
            onClick: () => editAgent(row)
          }, { default: () => '编辑' }),
          h(NButton, {
            size: 'small',
            type: 'info',
            ghost: true,
            onClick: () => testAgent(row)
          }, { default: () => '测试' }),
          h(NPopconfirm, {
            onPositiveClick: () => deleteAgent(row.id)
          }, {
            trigger: () => h(NButton, {
              size: 'small',
              type: 'error',
              ghost: true
            }, { default: () => '删除' }),
            default: () => '确定删除这个 Agent 吗？'
          })
        ]
      })
    }
  }
]

// 加载 Agent 列表
const loadAgents = async () => {
  loading.value = true
  try {
    agents.value = await difyAgentAPI.list(showEnabledOnly.value)
    console.log('加载 Agent 列表成功:', agents.value.length)
  } catch (error) {
    console.error('加载 Agent 列表失败:', error)
    message.error('加载失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}

// 刷新缓存
const handleRefreshCache = async () => {
  refreshing.value = true
  try {
    await difyAgentAPI.refreshCache()
    message.success('缓存刷新成功')
    await loadAgents()
  } catch (error) {
    console.error('刷新缓存失败:', error)
    message.error('刷新失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    refreshing.value = false
  }
}

// 编辑 Agent
const editAgent = (agent) => {
  editingAgent.value = agent
  Object.assign(formData, {
    name: agent.name,
    description: agent.description || '',
    agent_type: agent.agent_type,
    dify_app_id: agent.dify_app_id,
    api_key: agent.api_key,
    base_url: agent.base_url,
    capabilities: agent.capabilities || [],
    keywords: agent.keywords || [],
    priority: agent.priority,
    enabled: agent.enabled
  })
  showCreateModal.value = true
}

// 取消
const handleCancel = () => {
  showCreateModal.value = false
  editingAgent.value = null
  Object.assign(formData, {
    name: '',
    description: '',
    agent_type: 'chatbot',
    dify_app_id: '',
    api_key: '',
    base_url: 'https://api.dify.ai/v1',
    capabilities: [],
    keywords: [],
    priority: 0,
    enabled: true
  })
}

// 提交表单
const handleSubmit = async () => {
  try {
    await formRef.value?.validate()
    submitting.value = true

    if (editingAgent.value) {
      await difyAgentAPI.update(editingAgent.value.id, formData)
      message.success('更新成功')
    } else {
      await difyAgentAPI.create(formData)
      message.success('创建成功')
    }

    showCreateModal.value = false
    handleCancel()
    await loadAgents()
  } catch (error) {
    if (error?.errors) {
      return
    }
    console.error('提交失败:', error)
    message.error('操作失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    submitting.value = false
  }
}

// 切换 Agent 状态
const toggleAgent = async (agent) => {
  try {
    await difyAgentAPI.update(agent.id, { enabled: !agent.enabled })
    message.success('状态更新成功')
    await loadAgents()
  } catch (error) {
    console.error('切换状态失败:', error)
    message.error('操作失败: ' + (error.response?.data?.detail || error.message))
  }
}

// 删除 Agent
const deleteAgent = async (agentId) => {
  try {
    await difyAgentAPI.delete(agentId)
    message.success('删除成功')
    await loadAgents()
  } catch (error) {
    console.error('删除失败:', error)
    message.error('删除失败: ' + (error.response?.data?.detail || error.message))
  }
}

// 测试 Agent
const testAgent = (agent) => {
  testingAgent.value = agent
  testMessage.value = '你好'
  showTestModal.value = true
}

const handleTest = async () => {
  if (!testMessage.value.trim()) {
    message.warning('请输入测试消息')
    return
  }

  testing.value = true
  try {
    const result = await difyAgentAPI.test(testingAgent.value.id, {
      message: testMessage.value
    })

    if (result.success) {
      message.success(`测试成功! 延迟: ${result.latency_ms}ms`)
    } else {
      message.error(`测试失败: ${result.error}`)
    }
  } catch (error) {
    console.error('测试失败:', error)
    message.error('测试失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    testing.value = false
  }
}

// 初始化
onMounted(() => {
  loadAgents()
})
</script>

<style scoped>
.dify-agent-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 16px;
}

.dify-toolbar {
  margin-bottom: 16px;
}

.dify-agent-list {
  flex: 1;
  overflow: auto;
}
</style>

