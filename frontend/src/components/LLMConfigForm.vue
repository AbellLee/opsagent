<template>
  <n-form
    ref="formRef"
    :model="formData"
    :rules="rules"
    label-placement="left"
    label-width="120"
    require-mark-placement="right-hanging"
  >
    <n-form-item label="配置名称" path="name">
      <n-input v-model:value="formData.name" placeholder="例如: OpenAI GPT-4" />
    </n-form-item>

    <n-form-item label="提供商" path="provider">
      <n-select
        v-model:value="formData.provider"
        :options="providerOptions"
        placeholder="选择提供商"
        @update:value="handleProviderChange"
      />
    </n-form-item>

    <n-form-item label="模型名称" path="model_name">
      <n-input
        v-model:value="formData.model_name"
        placeholder="例如: gpt-4o-mini"
      />
    </n-form-item>

    <n-form-item label="API Key" path="api_key">
      <n-input
        v-model:value="formData.api_key"
        type="password"
        show-password-on="click"
        placeholder="输入 API Key"
      />
    </n-form-item>

    <n-form-item label="Base URL" path="base_url">
      <n-input
        v-model:value="formData.base_url"
        placeholder="例如: https://api.openai.com/v1"
      />
    </n-form-item>

    <n-form-item label="模型类型" path="is_embedding">
      <n-radio-group v-model:value="formData.is_embedding">
        <n-radio :value="false">聊天模型</n-radio>
        <n-radio :value="true">嵌入模型</n-radio>
      </n-radio-group>
    </n-form-item>

    <n-divider>高级参数</n-divider>

    <n-form-item label="Max Tokens" path="max_tokens">
      <n-input-number
        v-model:value="formData.max_tokens"
        :min="1"
        :max="128000"
        placeholder="2048"
        style="width: 100%"
      />
    </n-form-item>

    <n-form-item label="Temperature" path="temperature">
      <n-slider
        v-model:value="formData.temperature"
        :min="0"
        :max="2"
        :step="0.1"
        :marks="{ 0: '0', 1: '1', 2: '2' }"
      />
    </n-form-item>

    <n-form-item label="Top P" path="top_p">
      <n-slider
        v-model:value="formData.top_p"
        :min="0"
        :max="1"
        :step="0.1"
        :marks="{ 0: '0', 0.5: '0.5', 1: '1' }"
      />
    </n-form-item>

    <n-form-item label="Frequency Penalty" path="frequency_penalty">
      <n-slider
        v-model:value="formData.frequency_penalty"
        :min="-2"
        :max="2"
        :step="0.1"
        :marks="{ '-2': '-2', 0: '0', 2: '2' }"
      />
    </n-form-item>

    <n-form-item label="Presence Penalty" path="presence_penalty">
      <n-slider
        v-model:value="formData.presence_penalty"
        :min="-2"
        :max="2"
        :step="0.1"
        :marks="{ '-2': '-2', 0: '0', 2: '2' }"
      />
    </n-form-item>

    <n-form-item label="描述" path="description">
      <n-input
        v-model:value="formData.description"
        type="textarea"
        placeholder="配置描述（可选）"
        :rows="3"
      />
    </n-form-item>

    <n-form-item label="激活状态" path="is_active">
      <n-switch v-model:value="formData.is_active" />
    </n-form-item>

    <n-form-item label="设为默认" path="is_default">
      <n-switch v-model:value="formData.is_default" />
    </n-form-item>

    <n-space justify="end">
      <n-button @click="handleCancel">取消</n-button>
      <n-button type="primary" @click="handleSubmit">
        {{ config ? '更新' : '创建' }}
      </n-button>
    </n-space>
  </n-form>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'

const props = defineProps({
  config: {
    type: Object,
    default: null
  },
  providers: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['submit', 'cancel'])

const formRef = ref(null)

// 表单数据
const formData = reactive({
  name: '',
  provider: null,
  model_name: '',
  api_key: '',
  base_url: '',
  max_tokens: 2048,
  temperature: 0.7,
  top_p: 1.0,
  frequency_penalty: 0.0,
  presence_penalty: 0.0,
  description: '',
  is_active: true,
  is_default: false,
  is_embedding: false
})

// 提供商选项
const providerOptions = ref([
  { label: 'OpenAI', value: 'openai' },
  { label: 'DeepSeek', value: 'deepseek' },
  { label: '通义千问', value: 'tongyi' },
  { label: 'Ollama', value: 'ollama' },
  { label: 'vLLM', value: 'vllm' },
  { label: '豆包', value: 'doubao' },
  { label: '智谱', value: 'zhipu' },
  { label: 'Moonshot', value: 'moonshot' },
  { label: '百度', value: 'baidu' }
])

// 默认 Base URL 映射
const defaultBaseUrls = {
  openai: 'https://api.openai.com/v1',
  deepseek: 'https://api.deepseek.com/v1',
  tongyi: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
  ollama: 'http://localhost:11434',
  vllm: 'http://localhost:8000/v1',
  doubao: 'https://ark.cn-beijing.volces.com/api/v3',
  zhipu: 'https://open.bigmodel.cn/api/paas/v4',
  moonshot: 'https://api.moonshot.cn/v1',
  baidu: 'https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop'
}

// 表单验证规则
const rules = {
  name: [
    { required: true, message: '请输入配置名称', trigger: 'blur' }
  ],
  provider: [
    { required: true, message: '请选择提供商', trigger: 'change' }
  ],
  model_name: [
    { required: true, message: '请输入模型名称', trigger: 'blur' }
  ],
  api_key: [
    { required: false, message: '请输入 API Key', trigger: 'blur' }
  ],
  base_url: [
    { required: false, message: '请输入 Base URL', trigger: 'blur' }
  ]
}

// 监听 config 变化
watch(() => props.config, (newConfig) => {
  if (newConfig) {
    Object.assign(formData, {
      name: newConfig.name || '',
      provider: newConfig.provider || null,
      model_name: newConfig.model_name || '',
      api_key: '', // 不回显密钥
      base_url: newConfig.base_url || '',
      max_tokens: newConfig.max_tokens || 2048,
      temperature: newConfig.temperature || 0.7,
      top_p: newConfig.top_p || 1.0,
      frequency_penalty: newConfig.frequency_penalty || 0.0,
      presence_penalty: newConfig.presence_penalty || 0.0,
      description: newConfig.description || '',
      is_active: newConfig.is_active !== undefined ? newConfig.is_active : true,
      is_default: newConfig.is_default || false,
      is_embedding: newConfig.is_embedding || false
    })
  } else {
    // 重置表单
    Object.assign(formData, {
      name: '',
      provider: null,
      model_name: '',
      api_key: '',
      base_url: '',
      max_tokens: 2048,
      temperature: 0.7,
      top_p: 1.0,
      frequency_penalty: 0.0,
      presence_penalty: 0.0,
      description: '',
      is_active: true,
      is_default: false,
      is_embedding: false
    })
  }
}, { immediate: true })

// 处理提供商变化
const handleProviderChange = (provider) => {
  if (provider && defaultBaseUrls[provider]) {
    formData.base_url = defaultBaseUrls[provider]
  }
}

// 处理提交
const handleSubmit = async () => {
  try {
    await formRef.value?.validate()
    
    // 准备提交数据
    const submitData = { ...formData }
    
    // 如果是编辑且没有输入新密钥，删除 api_key 字段
    if (props.config && !submitData.api_key) {
      delete submitData.api_key
    }
    
    emit('submit', submitData)
  } catch (error) {
    console.error('表单验证失败:', error)
  }
}

// 处理取消
const handleCancel = () => {
  emit('cancel')
}
</script>

<style scoped>
/* 样式可以根据需要添加 */
</style>

