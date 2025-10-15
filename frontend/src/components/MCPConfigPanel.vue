<template>
  <div class="mcp-config-panel">
    <!-- 工具栏 -->
    <div class="mcp-toolbar">
      <n-space>
        <n-button type="primary" @click="showCreateModal = true">
          <template #icon>
            <n-icon><Add /></n-icon>
          </template>
          新增配置
        </n-button>
        <n-button @click="loadConfigs">
          <template #icon>
            <n-icon><Refresh /></n-icon>
          </template>
          刷新
        </n-button>
        <n-switch v-model:value="showEnabledOnly" @update:value="loadConfigs">
          <template #checked>只显示启用的</template>
          <template #unchecked>显示全部</template>
        </n-switch>
      </n-space>
    </div>

    <!-- 配置列表 -->
    <div class="mcp-config-list">
      <n-data-table
        :columns="columns"
        :data="configs"
        :loading="loading"
        :pagination="false"
        size="small"
        striped
      />
    </div>

    <!-- 新增/编辑配置弹窗 -->
    <n-modal v-model:show="showCreateModal" preset="card" title="MCP配置" style="width: 600px;">
      <n-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-placement="left"
        label-width="auto"
      >
        <n-form-item label="名称" path="name">
          <n-input v-model:value="formData.name" placeholder="输入配置名称" />
        </n-form-item>
        
        <n-form-item label="描述" path="description">
          <n-input v-model:value="formData.description" placeholder="输入配置描述（可选）" />
        </n-form-item>

        <n-form-item label="配置JSON" path="config">
          <n-space vertical>
            <n-space>
              <n-button size="small" @click="fillExample('stdio')">填入stdio示例</n-button>
              <n-button size="small" @click="fillExample('http')">填入HTTP示例</n-button>
            </n-space>
            <n-input
              v-model:value="formData.configJson"
              type="textarea"
              :rows="8"
              placeholder='请输入JSON配置，例如:
{
  "command": "python",
  "args": ["/path/to/script.py"],
  "transport": "stdio"
}

或者:

{
  "url": "http://localhost:8000/mcp/",
  "transport": "streamable_http"
}'
            />
          </n-space>
        </n-form-item>
        
        <n-form-item label="启用" path="enabled">
          <n-switch v-model:value="formData.enabled" />
        </n-form-item>
      </n-form>
      
      <template #footer>
        <n-space justify="end">
          <n-button @click="showCreateModal = false">取消</n-button>
          <n-button type="primary" @click="handleSubmit" :loading="submitting">
            {{ editingConfig ? '更新' : '创建' }}
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
  NSelect, 
  NDynamicInput,
  NIcon,
  NTag,
  NPopconfirm
} from 'naive-ui'
import { createDiscreteApi } from 'naive-ui'
import { Add, Refresh, Edit, Trash, Settings } from '@vicons/ionicons5'
import { mcpConfigAPI } from '../api'

const { message } = createDiscreteApi(['message'])

// 响应式数据
const configs = ref([])
const loading = ref(false)
const showEnabledOnly = ref(false)
const showCreateModal = ref(false)
const submitting = ref(false)
const editingConfig = ref(null)
const formRef = ref(null)

// 表单数据
const formData = reactive({
  name: '',
  description: '',
  configJson: '',
  enabled: true
})

// 配置示例
const configExamples = {
  stdio: {
    command: "python",
    args: ["/path/to/your/script.py"],
    transport: "stdio"
  },
  http: {
    url: "http://localhost:8000/mcp/",
    transport: "streamable_http"
  }
}

// 表单验证规则
const formRules = {
  name: [
    { required: true, message: '请输入配置名称', trigger: 'blur' },
    { min: 1, max: 100, message: '名称长度应在1-100字符之间', trigger: 'blur' }
  ],
  config: [
    { required: true, message: '请输入配置JSON', trigger: 'blur', validator: validateConfigJson }
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
    ellipsis: true
  },
  {
    title: '协议',
    key: 'transport',
    width: 100,
    render: (row) => {
      const type = row.config.transport === 'stdio' ? 'info' : 'success'
      const text = row.config.transport === 'stdio' ? 'stdio' : 'HTTP'
      return h(NTag, { type, size: 'small' }, { default: () => text })
    }
  },
  {
    title: '状态',
    key: 'enabled',
    width: 80,
    render: (row) => {
      return h(NSwitch, {
        value: row.enabled,
        onUpdateValue: () => toggleConfig(row.id)
      })
    }
  },
  {
    title: '操作',
    key: 'actions',
    width: 120,
    render: (row) => {
      return h(NSpace, { size: 'small' }, {
        default: () => [
          h(NButton, {
            size: 'small',
            type: 'primary',
            ghost: true,
            onClick: () => editConfig(row)
          }, { default: () => h(NIcon, null, { default: () => h(Edit) }) }),
          h(NPopconfirm, {
            onPositiveClick: () => deleteConfig(row.id)
          }, {
            trigger: () => h(NButton, {
              size: 'small',
              type: 'error',
              ghost: true
            }, { default: () => h(NIcon, null, { default: () => h(Trash) }) }),
            default: () => '确定删除这个配置吗？'
          })
        ]
      })
    }
  }
]

// 验证函数
function validateConfigJson(rule, value) {
  if (!value || value.trim() === '') {
    return new Error('请输入配置JSON')
  }

  try {
    const config = JSON.parse(value)

    // 验证必需字段
    if (!config.transport) {
      return new Error('配置中缺少 transport 字段')
    }

    if (!['stdio', 'streamable_http'].includes(config.transport)) {
      return new Error('transport 必须是 "stdio" 或 "streamable_http"')
    }

    if (config.transport === 'stdio') {
      if (!config.command) {
        return new Error('stdio 协议需要 command 字段')
      }
      if (!config.args || !Array.isArray(config.args)) {
        return new Error('stdio 协议需要 args 字段（数组类型）')
      }
    }

    if (config.transport === 'streamable_http') {
      if (!config.url) {
        return new Error('streamable_http 协议需要 url 字段')
      }
    }

    return true
  } catch (e) {
    return new Error('JSON格式错误: ' + e.message)
  }
}

// 方法
const loadConfigs = async () => {
  try {
    loading.value = true
    configs.value = await mcpConfigAPI.list(showEnabledOnly.value)
  } catch (error) {
    console.error('加载配置失败:', error)
    const errorMsg = error.response?.data?.detail || error.message || '未知错误'
    message.error('加载配置失败: ' + errorMsg)
  } finally {
    loading.value = false
  }
}

const resetForm = () => {
  Object.assign(formData, {
    name: '',
    description: '',
    configJson: '',
    enabled: true
  })
  editingConfig.value = null
}

const fillExample = (type) => {
  formData.configJson = JSON.stringify(configExamples[type], null, 2)
}

const editConfig = (config) => {
  editingConfig.value = config
  Object.assign(formData, {
    name: config.name,
    description: config.description || '',
    configJson: JSON.stringify(config.config, null, 2),
    enabled: config.enabled
  })
  showCreateModal.value = true
}

const handleSubmit = async () => {
  try {
    await formRef.value?.validate()

    submitting.value = true

    const configData = {
      name: formData.name,
      description: formData.description,
      enabled: formData.enabled,
      config: JSON.parse(formData.configJson)
    }
    
    if (editingConfig.value) {
      await mcpConfigAPI.update(editingConfig.value.id, configData)
      message.success('配置更新成功')
    } else {
      await mcpConfigAPI.create(configData)
      message.success('配置创建成功')
    }
    
    showCreateModal.value = false
    resetForm()
    await loadConfigs()
  } catch (error) {
    console.error('创建/更新配置失败:', error)
    const errorMsg = error.response?.data?.detail || error.message || '未知错误'
    message.error('操作失败: ' + errorMsg)
  } finally {
    submitting.value = false
  }
}

const toggleConfig = async (configId) => {
  try {
    await mcpConfigAPI.toggle(configId)
    message.success('状态切换成功')
    await loadConfigs()
  } catch (error) {
    console.error('状态切换失败:', error)
    const errorMsg = error.response?.data?.detail || error.message || '未知错误'
    message.error('状态切换失败: ' + errorMsg)
  }
}

const deleteConfig = async (configId) => {
  try {
    await mcpConfigAPI.delete(configId)
    message.success('配置删除成功')
    await loadConfigs()
  } catch (error) {
    console.error('删除失败:', error)
    const errorMsg = error.response?.data?.detail || error.message || '未知错误'
    message.error('删除失败: ' + errorMsg)
  }
}

// 生命周期
onMounted(() => {
  loadConfigs()
})
</script>

<style scoped>
.mcp-config-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.mcp-toolbar {
  padding: 16px;
  border-bottom: 1px solid var(--border-color);
}

.mcp-config-list {
  flex: 1;
  padding: 0 16px;
  overflow: auto;
}
</style>
