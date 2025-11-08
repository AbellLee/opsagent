<template>
  <div class="llm-config-view">
    <div class="config-header">
      <h1>LLM 配置管理</h1>
      <n-button type="primary" @click="showCreateDialog = true">
        <template #icon>
          <n-icon><AddOutline /></n-icon>
        </template>
        新建配置
      </n-button>
    </div>

    <!-- 筛选器 -->
    <div class="config-filters">
      <n-space>
        <n-select
          v-model:value="filters.provider"
          placeholder="提供商"
          clearable
          style="width: 150px"
          :options="providerOptions"
          @update:value="loadConfigs"
        />
        <n-select
          v-model:value="filters.is_active"
          placeholder="状态"
          clearable
          style="width: 120px"
          :options="statusOptions"
          @update:value="loadConfigs"
        />
        <n-select
          v-model:value="filters.is_embedding"
          placeholder="类型"
          clearable
          style="width: 120px"
          :options="typeOptions"
          @update:value="loadConfigs"
        />
        <n-input
          v-model:value="filters.search"
          placeholder="搜索配置名称..."
          clearable
          style="width: 200px"
          @update:value="handleSearchDebounced"
        >
          <template #prefix>
            <n-icon><SearchOutline /></n-icon>
          </template>
        </n-input>
      </n-space>
    </div>

    <!-- 配置列表 -->
    <n-spin :show="loading">
      <n-data-table
        :columns="columns"
        :data="configs"
        :pagination="pagination"
        :bordered="false"
        :single-line="false"
      />
    </n-spin>

    <!-- 创建/编辑对话框 -->
    <n-modal
      v-model:show="showCreateDialog"
      preset="card"
      :title="editingConfig ? '编辑配置' : '新建配置'"
      style="width: 600px"
      :mask-closable="false"
    >
      <LLMConfigForm
        :config="editingConfig"
        :providers="providers"
        @submit="handleSubmit"
        @cancel="handleCancel"
      />
    </n-modal>

    <!-- 测试对话框 -->
    <n-modal
      v-model:show="showTestDialog"
      preset="card"
      title="测试配置"
      style="width: 500px"
    >
      <n-space vertical>
        <n-input
          v-model:value="testPrompt"
          type="textarea"
          placeholder="输入测试提示词..."
          :rows="3"
        />
        <n-space justify="end">
          <n-button @click="showTestDialog = false">取消</n-button>
          <n-button type="primary" :loading="testing" @click="handleTest">
            测试
          </n-button>
        </n-space>
        <n-alert v-if="testResult" :type="testResult.success ? 'success' : 'error'">
          {{ testResult.message }}
        </n-alert>
      </n-space>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, reactive, h, onMounted } from 'vue'
import { NButton, NIcon, NTag, NSpace, NPopconfirm, useMessage } from 'naive-ui'
import { AddOutline, SearchOutline, TrashOutline, CreateOutline, PlayOutline, CheckmarkCircleOutline, CloseCircleOutline, StarOutline, Star } from '@vicons/ionicons5'
import { llmConfigAPI } from '../api'
import LLMConfigForm from '../components/LLMConfigForm.vue'

const message = useMessage()

// 状态
const loading = ref(false)
const configs = ref([])
const providers = ref([])
const showCreateDialog = ref(false)
const showTestDialog = ref(false)
const editingConfig = ref(null)
const testingConfig = ref(null)
const testing = ref(false)
const testPrompt = ref('你好，请介绍一下你自己')
const testResult = ref(null)

// 筛选器
const filters = reactive({
  provider: null,
  is_active: null,
  is_embedding: null,
  search: ''
})

// 筛选选项
const providerOptions = ref([])
const statusOptions = [
  { label: '激活', value: true },
  { label: '未激活', value: false }
]
const typeOptions = [
  { label: '聊天模型', value: false },
  { label: '嵌入模型', value: true }
]

// 分页
const pagination = reactive({
  page: 1,
  pageSize: 10,
  showSizePicker: true,
  pageSizes: [10, 20, 50],
  onChange: (page) => {
    pagination.page = page
  },
  onUpdatePageSize: (pageSize) => {
    pagination.pageSize = pageSize
    pagination.page = 1
  }
})

// 表格列定义
const columns = [
  {
    title: '名称',
    key: 'name',
    width: 180,
    render: (row) => {
      return h('div', { class: 'config-name-cell' }, [
        h('span', { class: 'config-name' }, row.name),
        row.is_default ? h(NIcon, { 
          size: 16, 
          color: '#f0a020',
          style: { marginLeft: '8px' }
        }, { default: () => h(Star) }) : null
      ])
    }
  },
  {
    title: '提供商',
    key: 'provider',
    width: 100,
    render: (row) => {
      const providerColors = {
        openai: 'success',
        deepseek: 'info',
        tongyi: 'warning',
        ollama: 'default',
        vllm: 'error',
        doubao: 'info',
        zhipu: 'success',
        moonshot: 'warning',
        baidu: 'error'
      }
      return h(NTag, { 
        type: providerColors[row.provider] || 'default',
        size: 'small'
      }, { default: () => row.provider.toUpperCase() })
    }
  },
  {
    title: '模型',
    key: 'model_name',
    width: 150,
    ellipsis: { tooltip: true }
  },
  {
    title: '类型',
    key: 'is_embedding',
    width: 80,
    render: (row) => {
      return h(NTag, { 
        type: row.is_embedding ? 'info' : 'success',
        size: 'small'
      }, { default: () => row.is_embedding ? '嵌入' : '聊天' })
    }
  },
  {
    title: '状态',
    key: 'is_active',
    width: 80,
    render: (row) => {
      return h(NIcon, {
        size: 20,
        color: row.is_active ? '#18a058' : '#d03050'
      }, {
        default: () => h(row.is_active ? CheckmarkCircleOutline : CloseCircleOutline)
      })
    }
  },
  {
    title: '使用次数',
    key: 'usage_count',
    width: 90,
    align: 'right'
  },
  {
    title: '描述',
    key: 'description',
    ellipsis: { tooltip: true }
  },
  {
    title: '操作',
    key: 'actions',
    width: 220,
    render: (row) => {
      return h(NSpace, { size: 'small' }, {
        default: () => [
          h(NButton, {
            size: 'small',
            onClick: () => handleEdit(row)
          }, { default: () => '编辑', icon: () => h(NIcon, null, { default: () => h(CreateOutline) }) }),
          
          h(NButton, {
            size: 'small',
            type: row.is_active ? 'warning' : 'success',
            onClick: () => handleToggleStatus(row)
          }, { default: () => row.is_active ? '停用' : '激活' }),
          
          !row.is_default ? h(NButton, {
            size: 'small',
            onClick: () => handleSetDefault(row)
          }, { default: () => '设为默认', icon: () => h(NIcon, null, { default: () => h(StarOutline) }) }) : null,
          
          h(NButton, {
            size: 'small',
            onClick: () => handleTestConfig(row)
          }, { default: () => '测试', icon: () => h(NIcon, null, { default: () => h(PlayOutline) }) }),
          
          h(NPopconfirm, {
            onPositiveClick: () => handleDelete(row.id)
          }, {
            default: () => '确定删除此配置吗？',
            trigger: () => h(NButton, {
              size: 'small',
              type: 'error'
            }, { default: () => '删除', icon: () => h(NIcon, null, { default: () => h(TrashOutline) }) })
          })
        ]
      })
    }
  }
]

// 加载配置列表
const loadConfigs = async () => {
  loading.value = true
  try {
    const params = {}
    if (filters.provider) params.provider = filters.provider
    if (filters.is_active !== null) params.is_active = filters.is_active
    if (filters.is_embedding !== null) params.is_embedding = filters.is_embedding
    if (filters.search) params.search = filters.search
    
    configs.value = await llmConfigAPI.list(params)
  } catch (error) {
    message.error('加载配置失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

// 加载提供商列表
const loadProviders = async () => {
  try {
    providers.value = await llmConfigAPI.getProviders()
    providerOptions.value = providers.value.map(p => ({
      label: p.toUpperCase(),
      value: p
    }))
  } catch (error) {
    message.error('加载提供商列表失败: ' + error.message)
  }
}

// 搜索防抖
let searchTimeout = null
const handleSearchDebounced = () => {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    loadConfigs()
  }, 500)
}

// 处理编辑
const handleEdit = (config) => {
  editingConfig.value = { ...config }
  showCreateDialog.value = true
}

// 处理提交
const handleSubmit = async (configData) => {
  try {
    if (editingConfig.value) {
      await llmConfigAPI.update(editingConfig.value.id, configData)
      message.success('配置更新成功')
    } else {
      await llmConfigAPI.create(configData)
      message.success('配置创建成功')
    }
    showCreateDialog.value = false
    editingConfig.value = null
    await loadConfigs()
  } catch (error) {
    message.error('操作失败: ' + error.response?.data?.detail || error.message)
  }
}

// 处理取消
const handleCancel = () => {
  showCreateDialog.value = false
  editingConfig.value = null
}

// 处理删除
const handleDelete = async (configId) => {
  try {
    await llmConfigAPI.delete(configId)
    message.success('配置删除成功')
    await loadConfigs()
  } catch (error) {
    message.error('删除失败: ' + error.response?.data?.detail || error.message)
  }
}

// 处理切换状态
const handleToggleStatus = async (config) => {
  try {
    await llmConfigAPI.toggleStatus(config.id)
    message.success(`配置已${config.is_active ? '停用' : '激活'}`)
    await loadConfigs()
  } catch (error) {
    message.error('操作失败: ' + error.response?.data?.detail || error.message)
  }
}

// 处理设置默认
const handleSetDefault = async (config) => {
  try {
    await llmConfigAPI.setDefault(config.id)
    message.success('已设置为默认配置')
    await loadConfigs()
  } catch (error) {
    message.error('操作失败: ' + error.response?.data?.detail || error.message)
  }
}

// 处理测试配置
const handleTestConfig = (config) => {
  testingConfig.value = config
  testResult.value = null
  showTestDialog.value = true
}

// 执行测试
const handleTest = async () => {
  testing.value = true
  testResult.value = null
  try {
    const result = await llmConfigAPI.test(testingConfig.value.id, {
      prompt: testPrompt.value
    })
    testResult.value = {
      success: true,
      message: `测试成功！响应: ${result.response}`
    }
  } catch (error) {
    testResult.value = {
      success: false,
      message: '测试失败: ' + (error.response?.data?.detail || error.message)
    }
  } finally {
    testing.value = false
  }
}

// 初始化
onMounted(() => {
  loadConfigs()
  loadProviders()
})
</script>

<style scoped>
.llm-config-view {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
}

.config-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.config-header h1 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
}

.config-filters {
  margin-bottom: 16px;
}

.config-name-cell {
  display: flex;
  align-items: center;
}

.config-name {
  font-weight: 500;
}
</style>

