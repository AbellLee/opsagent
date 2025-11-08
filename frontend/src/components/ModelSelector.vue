<template>
  <div class="model-selector">
    <n-select
      v-model:value="selectedModelId"
      :options="modelOptions"
      :loading="loading"
      placeholder="选择模型"
      filterable
      clearable
      @update:value="handleModelChange"
    >
      <template #empty>
        <n-empty description="暂无可用模型">
          <template #extra>
            <n-button size="small" @click="loadModels">
              刷新
            </n-button>
          </template>
        </n-empty>
      </template>
    </n-select>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, h } from 'vue'
import { NTag, NSpace, NIcon } from 'naive-ui'
import { Star, CheckmarkCircle } from '@vicons/ionicons5'
import { llmConfigAPI } from '../api'

const props = defineProps({
  modelValue: {
    type: String,
    default: null
  },
  isEmbedding: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

const loading = ref(false)
const models = ref([])
const selectedModelId = ref(props.modelValue)

// 模型选项
const modelOptions = computed(() => {
  return models.value.map(model => ({
    label: model.name,
    value: model.id,
    disabled: !model.is_active,
    // 自定义渲染
    render: () => {
      return h('div', { class: 'model-option' }, [
        h('div', { class: 'model-option-main' }, [
          h('span', { class: 'model-name' }, model.name),
          h(NSpace, { size: 4, style: { marginLeft: '8px' } }, {
            default: () => [
              model.is_default ? h(NIcon, { 
                size: 14, 
                color: '#f0a020' 
              }, { default: () => h(Star) }) : null,
              model.is_active ? h(NIcon, { 
                size: 14, 
                color: '#18a058' 
              }, { default: () => h(CheckmarkCircle) }) : null,
              h(NTag, { 
                size: 'small',
                type: getProviderTagType(model.provider)
              }, { default: () => model.provider.toUpperCase() })
            ]
          })
        ]),
        h('div', { class: 'model-option-sub' }, [
          h('span', { class: 'model-model-name' }, model.model_name),
          model.description ? h('span', { 
            class: 'model-description' 
          }, ` - ${model.description}`) : null
        ])
      ])
    }
  }))
})

// 获取提供商标签类型
const getProviderTagType = (provider) => {
  const types = {
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
  return types[provider] || 'default'
}

// 加载模型列表
const loadModels = async () => {
  loading.value = true
  try {
    const params = {
      is_active: true,
      is_embedding: props.isEmbedding
    }
    models.value = await llmConfigAPI.list(params)
    
    // 如果没有选中的模型，自动选择默认模型
    if (!selectedModelId.value && models.value.length > 0) {
      const defaultModel = models.value.find(m => m.is_default)
      if (defaultModel) {
        selectedModelId.value = defaultModel.id
        emit('update:modelValue', defaultModel.id)
        emit('change', defaultModel)
      }
    }
  } catch (error) {
    console.error('加载模型列表失败:', error)
  } finally {
    loading.value = false
  }
}

// 处理模型变化
const handleModelChange = (modelId) => {
  emit('update:modelValue', modelId)
  const selectedModel = models.value.find(m => m.id === modelId)
  emit('change', selectedModel)
}

// 监听 modelValue 变化
watch(() => props.modelValue, (newValue) => {
  selectedModelId.value = newValue
})

// 监听 isEmbedding 变化
watch(() => props.isEmbedding, () => {
  loadModels()
})

// 初始化
onMounted(() => {
  loadModels()
})

// 暴露方法
defineExpose({
  loadModels
})
</script>

<style scoped>
.model-selector {
  width: 100%;
}

:deep(.model-option) {
  padding: 4px 0;
}

:deep(.model-option-main) {
  display: flex;
  align-items: center;
  margin-bottom: 2px;
}

:deep(.model-name) {
  font-weight: 500;
  font-size: 14px;
}

:deep(.model-option-sub) {
  font-size: 12px;
  color: #999;
  padding-left: 2px;
}

:deep(.model-model-name) {
  font-family: monospace;
}

:deep(.model-description) {
  color: #666;
}
</style>

