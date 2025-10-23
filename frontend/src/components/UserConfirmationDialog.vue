<template>
  <n-modal
    v-model:show="showModal"
    :title="actualTitle"
    preset="dialog"
    :type="dialogType"
    positive-text="确认"
    negative-text="取消"
    @positive-click="handleConfirm"
    @negative-click="handleCancel"
    @close="handleCancel"
  >
    <div class="confirmation-content">
      <div ref="messageContent" class="message-content" :class="{ 'markdown-body': actualIsMarkdown }"></div>
      <n-checkbox-group
        v-if="hasOptions"
        v-model:value="selectedValue"
        class="options-checkbox-group"
      >
        <n-space vertical>
          <n-checkbox
            v-for="option in actualOptions"
            :key="option"
            :value="option"
            :label="option"
          />
        </n-space>
      </n-checkbox-group>
    </div>
  </n-modal>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { marked } from 'marked'
import { NModal, NSelect, NCheckboxGroup, NCheckbox, NSpace } from 'naive-ui'

// Props
const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  data: {
    type: Object,
    default: () => ({})
  }
})

// Emits
const emit = defineEmits(['confirm', 'cancel', 'update:show'])

// Reactive data
const showModal = computed({
  get: () => props.show,
  set: (value) => emit('update:show', value)
})

const selectedValue = ref([])
const messageContent = ref(null)

// Computed properties
const actualTitle = computed(() => props.data.title || '请确认')
const actualMessage = computed(() => props.data.message || '请确认操作')
const actualOptions = computed(() => props.data.options || [])
const actualIsMarkdown = computed(() => props.data.is_markdown !== undefined ? props.data.is_markdown : false)

const hasOptions = computed(() => actualOptions.value && Array.isArray(actualOptions.value) && actualOptions.value.length > 0)

const selectOptions = computed(() => {
  if (!hasOptions.value) return []
  return actualOptions.value.map(option => ({
    label: option,
    value: option
  }))
})

const selectPlaceholder = computed(() => {
  return '请选择一个或多个选项'
})

const dialogType = computed(() => {
  return hasOptions.value ? 'info' : 'warning'
})

// Methods
const handleConfirm = () => {
  emit('confirm', {
    status: 'confirmed',
    value: selectedValue.value
  })
  reset()
}

const handleCancel = () => {
  emit('cancel', {
    status: 'cancelled',
    value: null
  })
  reset()
}

const reset = () => {
  selectedValue.value = []
}

// Process message content
const processMessageContent = async () => {
  if (!messageContent.value) return
  
  if (actualIsMarkdown.value) {
    try {
      messageContent.value.innerHTML = marked(actualMessage.value || '请确认操作')
    } catch (e) {
      console.error('Markdown解析失败:', e)
      messageContent.value.innerHTML = actualMessage.value || '请确认操作'
    }
  } else {
    messageContent.value.innerHTML = actualMessage.value || '请确认操作'
  }
}

// Watch for changes
onMounted(() => {
  nextTick(() => {
    processMessageContent()
  })
})

// Watch for message changes
watch([actualMessage, actualIsMarkdown], () => {
  nextTick(() => {
    processMessageContent()
  })
})

</script>

<style scoped>
.confirmation-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.message-content {
  line-height: 1.5;
}

.options-select {
  min-width: 200px;
}

.options-checkbox-group {
  padding: 8px 0;
}

/* 引入markdown样式 */
@import 'github-markdown-css/github-markdown.css';

.markdown-body {
  background-color: transparent !important;
  color: inherit !important;
  font-size: 14px;
  line-height: 1.5;
  margin: 0;
}

.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3) {
  margin-top: 1em;
  margin-bottom: 0.5em;
}

.markdown-body :deep(p) {
  margin-top: 0.5em;
  margin-bottom: 0.5em;
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  margin-top: 0.5em;
  margin-bottom: 0.5em;
  padding-left: 1.5em;
}

.markdown-body :deep(li) {
  margin-bottom: 0.25em;
}

.markdown-body :deep(code) {
  background-color: rgba(175, 184, 193, 0.2);
  padding: 0.2em 0.4em;
  border-radius: 6px;
  font-size: 0.85em;
}

.markdown-body :deep(pre) {
  background-color: rgba(175, 184, 193, 0.2);
  padding: 1em;
  border-radius: 6px;
  overflow: auto;
}

.markdown-body :deep(pre code) {
  background-color: transparent;
  padding: 0;
}

.markdown-body :deep(blockquote) {
  margin: 0;
  padding: 0 1em;
  color: #6a737d;
  border-left: 0.25em solid #dfe2e5;
}
</style>