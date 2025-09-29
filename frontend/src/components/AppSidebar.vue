<template>
  <n-layout-sider
    width="240"
    collapse-mode="width"
    :collapsed-width="64"
    :collapsed="collapsed"
    show-trigger
    @collapse="handleCollapse"
    @expand="handleExpand"
  >
    <SessionList :collapsed="collapsed" />
  </n-layout-sider>
</template>

<script setup>
import { ref } from 'vue'
import { NLayoutSider } from 'naive-ui'
import SessionList from './SessionList.vue'

const collapsed = ref(false)

// 处理侧边栏折叠和展开事件
const handleCollapse = () => {
  collapsed.value = true
}

const handleExpand = () => {
  collapsed.value = false
}
</script>

<style scoped>
/* Sidebar 美化 - 修复布局和展开按钮，移除白线 */
.n-layout-sider {
  background: rgba(255, 255, 255, 0.9) !important;
  backdrop-filter: blur(20px);
  border: none !important;
  border-right: none !important;
  border-left: none !important;
  border-top: none !important;
  border-bottom: none !important;
  border-radius: 20px !important;
  margin: 0 8px 12px 12px !important;
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.12);
  overflow: visible !important; /* 允许展开按钮显示 */
  height: calc(100vh - 92px) !important;
  max-height: calc(100vh - 92px) !important;
  flex-shrink: 0;
  display: flex !important;
  flex-direction: column !important;
  position: relative !important;
}

/* 修复侧边栏内容区域，移除所有边框 */
.n-layout-sider :deep(.n-layout-sider-scroll-container) {
  border-radius: 20px !important;
  overflow: hidden !important;
  border: none !important;
  border-right: none !important;
  border-left: none !important;
  border-top: none !important;
  border-bottom: none !important;
}

/* 确保侧边栏内部所有元素无边框 */
.n-layout-sider :deep(*) {
  border-right: none !important;
}

.n-layout-sider::before,
.n-layout-sider::after {
  display: none !important;
}

/* 移除可能的分割线 */
.n-layout-sider :deep(.n-layout-sider__border) {
  display: none !important;
}

.n-layout-sider :deep(.n-divider) {
  display: none !important;
}

/* 美化展开/收起按钮 */
.n-layout-sider :deep(.n-layout-toggle-button) {
  background: rgba(255, 255, 255, 0.9) !important;
  backdrop-filter: blur(10px) !important;
  border: 1px solid rgba(102, 126, 234, 0.2) !important;
  border-radius: 50% !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1) !important;
  width: 32px !important;
  height: 32px !important;
  right: -16px !important;
  top: 50% !important;
  transform: translateY(-50%) !important;
  z-index: 100 !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

.n-layout-sider :deep(.n-layout-toggle-button:hover) {
  background: rgba(102, 126, 234, 0.1) !important;
  border-color: rgba(102, 126, 234, 0.4) !important;
  transform: translateY(-50%) scale(1.1) !important;
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.2) !important;
}

.n-layout-sider :deep(.n-layout-toggle-button .n-icon) {
  color: #667eea !important;
  transition: all 0.3s ease !important;
}

.n-layout-sider :deep(.n-layout-toggle-button:hover .n-icon) {
  color: #5a6fd8 !important;
}

/* 暗色模式下的侧边栏 */
html.dark .n-layout-sider {
  background: rgba(30, 30, 30, 0.9) !important;
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.3);
}

/* 暗色模式下的展开按钮 */
html.dark .n-layout-sider :deep(.n-layout-toggle-button) {
  background: rgba(30, 30, 30, 0.9) !important;
  border-color: rgba(102, 126, 234, 0.3) !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3) !important;
}

html.dark .n-layout-sider :deep(.n-layout-toggle-button:hover) {
  background: rgba(102, 126, 234, 0.2) !important;
  border-color: rgba(102, 126, 234, 0.5) !important;
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.3) !important;
}

html.dark .n-layout-sider :deep(.n-layout-toggle-button .n-icon) {
  color: #667eea !important;
}

html.dark .n-layout-sider :deep(.n-layout-toggle-button:hover .n-icon) {
  color: #7c8aed !important;
}

/* 全面移除侧边栏白线的样式 */
.n-layout-sider,
.n-layout-sider :deep(*),
.n-layout-sider::before,
.n-layout-sider::after,
.n-layout-sider :deep(.n-scrollbar),
.n-layout-sider :deep(.n-scrollbar *),
.n-layout-sider :deep(.n-list),
.n-layout-sider :deep(.n-list *) {
  border-right: none !important;
  box-shadow: none !important;
}

/* 特别针对可能的边框元素 */
.n-layout-sider :deep(.n-layout-sider__border),
.n-layout-sider :deep(.n-layout-sider-trigger),
.n-layout-sider :deep(.n-divider),
.n-layout-sider :deep(.n-border) {
  display: none !important;
  border: none !important;
  box-shadow: none !important;
}

/* 暗色模式下也移除白线 */
html.dark .n-layout-sider,
html.dark .n-layout-sider :deep(*),
html.dark .n-layout-sider::before,
html.dark .n-layout-sider::after {
  border-right: none !important;
  box-shadow: none !important;
}
</style>
