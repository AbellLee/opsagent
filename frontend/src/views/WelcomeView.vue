<template>
  <div class="welcome-container">
    <!-- 主要内容区域 -->
    <div class="welcome-main">
      <!-- 头部区域 -->
      <div class="welcome-header">
        <div class="logo-container">
          <div class="logo-background">
            <n-icon size="64" class="logo-icon">
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M12,2A10,10 0 0,1 22,12A10,10 0 0,1 12,22A10,10 0 0,1 2,12A10,10 0 0,1 12,2M12,4A8,8 0 0,0 4,12A8,8 0 0,0 12,20A8,8 0 0,0 20,12A8,8 0 0,0 12,4M11,16.5L6.5,12L7.91,10.59L11,13.67L16.59,8.09L18,9.5L11,16.5Z"/>
              </svg>
            </n-icon>
          </div>
        </div>

        <h1 class="welcome-title">
          <span class="title-main">欢迎使用</span>
          <span class="title-brand">OpsAgent</span>
        </h1>

        <p class="welcome-subtitle">
          智能AI运维助手，让复杂的运维工作变得简单高效
        </p>

        <div class="welcome-stats">
          <div class="stat-item">
            <div class="stat-number">24/7</div>
            <div class="stat-label">全天候服务</div>
          </div>
          <div class="stat-item">
            <div class="stat-number">99.9%</div>
            <div class="stat-label">准确率</div>
          </div>
          <div class="stat-item">
            <div class="stat-number">10s</div>
            <div class="stat-label">响应时间</div>
          </div>
        </div>
      </div>

      <!-- 操作按钮区域 -->
      <div class="welcome-actions">
        <n-button
          type="primary"
          size="large"
          @click="createNewSession"
          class="primary-action-btn"
          :loading="creating"
        >
          <template #icon>
            <n-icon>
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M20,2H4A2,2 0 0,0 2,4V22L6,18H20A2,2 0 0,0 22,16V4C22,2.89 21.1,2 20,2M6,9V7H18V9H6M14,11V13H6V11H14M16,15V17H6V15H16Z"/>
              </svg>
            </n-icon>
          </template>
          开始新对话
        </n-button>

        <n-button
          quaternary
          size="large"
          @click="showQuickStart = true"
          class="secondary-action-btn"
        >
          <template #icon>
            <n-icon>
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M9.5,3A6.5,6.5 0 0,1 16,9.5C16,11.11 15.41,12.59 14.44,13.73L14.71,14H15.5L20.5,19L19,20.5L14,15.5V14.71L13.73,14.44C12.59,15.41 11.11,16 9.5,16A6.5,6.5 0 0,1 3,9.5A6.5,6.5 0 0,1 9.5,3M9.5,5C7,5 5,7 5,9.5C5,12 7,14 9.5,14C12,14 14,12 14,9.5C14,7 12,5 9.5,5Z"/>
              </svg>
            </n-icon>
          </template>
          快速入门
        </n-button>
      </div>

      <!-- 功能特性区域 -->
      <div class="welcome-features">
        <h3 class="features-title">核心功能</h3>
        <div class="features-grid">
          <div class="feature-card" v-for="feature in features" :key="feature.id">
            <div class="feature-icon">
              <n-icon size="32" :color="feature.color">
                <component :is="feature.icon" />
              </n-icon>
            </div>
            <h4 class="feature-title">{{ feature.title }}</h4>
            <p class="feature-description">{{ feature.description }}</p>
            <div class="feature-tags">
              <n-tag
                v-for="tag in feature.tags"
                :key="tag"
                size="small"
                :bordered="false"
                class="feature-tag"
              >
                {{ tag }}
              </n-tag>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 快速入门弹窗 -->
    <n-modal v-model:show="showQuickStart" preset="card" title="快速入门" style="width: 600px;">
      <div class="quick-start-content">
        <div class="quick-start-step" v-for="(step, index) in quickStartSteps" :key="index">
          <div class="step-number">{{ index + 1 }}</div>
          <div class="step-content">
            <h4>{{ step.title }}</h4>
            <p>{{ step.description }}</p>
          </div>
        </div>
      </div>
      <template #action>
        <n-button @click="showQuickStart = false">知道了</n-button>
        <n-button type="primary" @click="startQuickDemo">开始体验</n-button>
      </template>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, h } from 'vue'
import { useSessionStore } from '../stores/session'
import { sessionAPI } from '../api'
import { useUserStore } from '../stores/user'
import { createDiscreteApi } from 'naive-ui'

const { message } = createDiscreteApi(['message'])
const sessionStore = useSessionStore()
const userStore = useUserStore()

// 响应式数据
const creating = ref(false)
const showQuickStart = ref(false)

// 功能特性数据
const features = ref([
  {
    id: 1,
    title: '智能日志分析',
    description: '自动分析系统日志，快速定位问题根源，支持多种日志格式',
    color: '#667eea',
    tags: ['日志解析', '异常检测', '趋势分析'],
    icon: () => h('svg', { viewBox: '0 0 24 24', fill: 'currentColor' }, [
      h('path', { d: 'M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z' })
    ])
  },
  {
    id: 2,
    title: '实时系统监控',
    description: '24/7监控系统状态，智能预警潜在风险，保障系统稳定运行',
    color: '#f093fb',
    tags: ['性能监控', '资源管理', '告警通知'],
    icon: () => h('svg', { viewBox: '0 0 24 24', fill: 'currentColor' }, [
      h('path', { d: 'M3,3H21A2,2 0 0,1 23,5V19A2,2 0 0,1 21,21H3A2,2 0 0,1 1,19V5A2,2 0 0,1 3,3M3,5V19H21V5H3M5,7H19V9H5V7M5,11H19V13H5V11M5,15H19V17H5V15Z' })
    ])
  },
  {
    id: 3,
    title: '故障智能诊断',
    description: '基于AI算法的故障诊断，提供详细的解决方案和修复建议',
    color: '#f6d365',
    tags: ['故障定位', '根因分析', '修复建议'],
    icon: () => h('svg', { viewBox: '0 0 24 24', fill: 'currentColor' }, [
      h('path', { d: 'M12,2A10,10 0 0,1 22,12A10,10 0 0,1 12,22A10,10 0 0,1 2,12A10,10 0 0,1 12,2M12,4A8,8 0 0,0 4,12A8,8 0 0,0 12,20A8,8 0 0,0 20,12A8,8 0 0,0 12,4M11,16.5L6.5,12L7.91,10.59L11,13.67L16.59,8.09L18,9.5L11,16.5Z' })
    ])
  },
  {
    id: 4,
    title: '自动化运维',
    description: '自动执行重复性运维任务，提高工作效率，减少人为错误',
    color: '#fa709a',
    tags: ['任务自动化', '脚本执行', '流程优化'],
    icon: () => h('svg', { viewBox: '0 0 24 24', fill: 'currentColor' }, [
      h('path', { d: 'M12,15.5A3.5,3.5 0 0,1 8.5,12A3.5,3.5 0 0,1 12,8.5A3.5,3.5 0 0,1 15.5,12A3.5,3.5 0 0,1 12,15.5M19.43,12.97C19.47,12.65 19.5,12.33 19.5,12C19.5,11.67 19.47,11.34 19.43,11L21.54,9.37C21.73,9.22 21.78,8.95 21.66,8.73L19.66,5.27C19.54,5.05 19.27,4.96 19.05,5.05L16.56,6.05C16.04,5.66 15.5,5.32 14.87,5.07L14.5,2.42C14.46,2.18 14.25,2 14,2H10C9.75,2 9.54,2.18 9.5,2.42L9.13,5.07C8.5,5.32 7.96,5.66 7.44,6.05L4.95,5.05C4.73,4.96 4.46,5.05 4.34,5.27L2.34,8.73C2.22,8.95 2.27,9.22 2.46,9.37L4.57,11C4.53,11.34 4.5,11.67 4.5,12C4.5,12.33 4.53,12.65 4.57,12.97L2.46,14.63C2.27,14.78 2.22,15.05 2.34,15.27L4.34,18.73C4.46,18.95 4.73,19.03 4.95,18.95L7.44,17.94C7.96,18.34 8.5,18.68 9.13,18.93L9.5,21.58C9.54,21.82 9.75,22 10,22H14C14.25,22 14.46,21.82 14.5,21.58L14.87,18.93C15.5,18.68 16.04,18.34 16.56,17.94L19.05,18.95C19.27,19.03 19.54,18.95 19.66,18.73L21.66,15.27C21.78,15.05 21.73,14.78 21.54,14.63L19.43,12.97Z' })
    ])
  }
])

// 快速入门步骤
const quickStartSteps = ref([
  {
    title: '创建新对话',
    description: '点击"开始新对话"按钮，创建您的第一个AI助手会话'
  },
  {
    title: '描述问题',
    description: '详细描述您遇到的运维问题或需要帮助的任务'
  },
  {
    title: '获取建议',
    description: 'AI助手会分析您的问题并提供专业的解决方案'
  },
  {
    title: '执行操作',
    description: '根据建议执行相应操作，AI助手会持续协助您'
  }
])

// 创建新会话
const createNewSession = async () => {
  if (creating.value) return

  creating.value = true
  try {
    const response = await sessionAPI.create({
      user_id: userStore.user?.user_id || 'default_user'
    })

    sessionStore.addSession(response)
    sessionStore.setSessionId(response.session_id)
    sessionStore.setMessages([])

    message.success('新会话创建成功！开始您的AI运维之旅吧 🚀')
  } catch (error) {
    console.error('创建新会话失败:', error)
    message.error('创建新会话失败，请重试')
  } finally {
    creating.value = false
  }
}

// 开始快速演示
const startQuickDemo = async () => {
  showQuickStart.value = false
  await createNewSession()

  // 添加演示消息
  setTimeout(() => {
    sessionStore.addMessage({
      role: 'assistant',
      content: '👋 欢迎使用OpsAgent！我是您的AI运维助手。\n\n您可以向我咨询：\n• 系统性能问题诊断\n• 日志分析和错误排查\n• 运维最佳实践建议\n• 自动化脚本编写\n\n请告诉我您需要什么帮助？',
      timestamp: new Date().toISOString()
    })
  }, 500)
}
</script>

<style scoped>
.welcome-container {
  height: 100%;
  width: 100%;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 40px 20px;
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
}

.welcome-main {
  max-width: 1200px;
  width: 100%;
  text-align: center;
  animation: fadeInUp 0.8s ease-out;
}

/* 头部区域 */
.welcome-header {
  margin-bottom: 60px;
}

.logo-container {
  margin-bottom: 32px;
  display: flex;
  justify-content: center;
}

.logo-background {
  width: 120px;
  height: 120px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 20px 60px rgba(102, 126, 234, 0.3);
  animation: float 3s ease-in-out infinite;
  position: relative;
}

.logo-background::before {
  content: '';
  position: absolute;
  top: -4px;
  left: -4px;
  right: -4px;
  bottom: -4px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 50%;
  opacity: 0.3;
  z-index: -1;
  animation: pulse 2s ease-in-out infinite;
}

.logo-icon {
  color: white;
  filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.2));
}

.welcome-title {
  margin: 0 0 24px 0;
  font-size: 48px;
  font-weight: 700;
  line-height: 1.2;
}

.title-main {
  color: #2c3e50;
  display: block;
  font-size: 32px;
  font-weight: 400;
  margin-bottom: 8px;
}

.title-brand {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  display: block;
  font-size: 56px;
  font-weight: 800;
  letter-spacing: -2px;
}

.welcome-subtitle {
  color: #64748b;
  font-size: 20px;
  line-height: 1.6;
  margin: 0 0 40px 0;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
}

/* 统计数据 */
.welcome-stats {
  display: flex;
  justify-content: center;
  gap: 60px;
  margin-bottom: 40px;
  flex-wrap: wrap;
}

.stat-item {
  text-align: center;
  animation: slideInUp 0.6s ease-out;
}

.stat-number {
  font-size: 36px;
  font-weight: 800;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 8px;
}

.stat-label {
  color: #64748b;
  font-size: 14px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 1px;
}

/* 操作按钮 */
.welcome-actions {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-bottom: 80px;
  flex-wrap: wrap;
}

.primary-action-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
  border: none !important;
  box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3) !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
  font-size: 16px !important;
  font-weight: 600 !important;
  padding: 0 32px !important;
  height: 48px !important;
}

.primary-action-btn:hover {
  transform: translateY(-3px) !important;
  box-shadow: 0 12px 40px rgba(102, 126, 234, 0.4) !important;
}

.secondary-action-btn {
  border: 2px solid #667eea !important;
  color: #667eea !important;
  font-size: 16px !important;
  font-weight: 600 !important;
  padding: 0 32px !important;
  height: 48px !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

.secondary-action-btn:hover {
  background: rgba(102, 126, 234, 0.1) !important;
  transform: translateY(-3px) !important;
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.2) !important;
}

/* 功能特性区域 */
.welcome-features {
  text-align: left;
}

.features-title {
  text-align: center;
  font-size: 32px;
  font-weight: 700;
  color: #2c3e50;
  margin: 0 0 48px 0;
  position: relative;
}

.features-title::after {
  content: '';
  position: absolute;
  bottom: -12px;
  left: 50%;
  transform: translateX(-50%);
  width: 80px;
  height: 4px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 2px;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 32px;
  margin-bottom: 40px;
}

.feature-card {
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  padding: 32px 24px;
  text-align: center;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  position: relative;
  overflow: hidden;
}

.feature-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.feature-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
  background: rgba(255, 255, 255, 0.95);
}

.feature-icon {
  margin-bottom: 20px;
  display: flex;
  justify-content: center;
}

.feature-title {
  font-size: 20px;
  font-weight: 600;
  color: #2c3e50;
  margin: 0 0 12px 0;
}

.feature-description {
  color: #64748b;
  font-size: 14px;
  line-height: 1.6;
  margin: 0 0 20px 0;
}

.feature-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
}

.feature-tag {
  background: rgba(102, 126, 234, 0.1) !important;
  color: #667eea !important;
  border: none !important;
  font-size: 12px !important;
  padding: 4px 12px !important;
  border-radius: 12px !important;
}

/* 快速入门弹窗 */
.quick-start-content {
  padding: 20px 0;
}

.quick-start-step {
  display: flex;
  align-items: flex-start;
  margin-bottom: 24px;
  padding: 16px;
  border-radius: 12px;
  background: rgba(102, 126, 234, 0.05);
  transition: all 0.3s ease;
}

.quick-start-step:hover {
  background: rgba(102, 126, 234, 0.1);
  transform: translateX(4px);
}

.step-number {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 14px;
  margin-right: 16px;
  flex-shrink: 0;
}

.step-content h4 {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
}

.step-content p {
  margin: 0;
  color: #64748b;
  font-size: 14px;
  line-height: 1.5;
}

/* 动画 */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes slideInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes float {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-10px);
  }
}

@keyframes pulse {
  0%, 100% {
    opacity: 0.3;
    transform: scale(1);
  }
  50% {
    opacity: 0.1;
    transform: scale(1.05);
  }
}

/* 暗色模式 */
html.dark .title-main {
  color: #e2e8f0;
}

html.dark .welcome-subtitle {
  color: #94a3b8;
}

html.dark .stat-label {
  color: #94a3b8;
}

html.dark .features-title {
  color: #e2e8f0;
}

html.dark .feature-card {
  background: rgba(30, 30, 30, 0.8);
  border-color: rgba(255, 255, 255, 0.1);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

html.dark .feature-card:hover {
  background: rgba(30, 30, 30, 0.95);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
}

html.dark .feature-title {
  color: #e2e8f0;
}

html.dark .feature-description {
  color: #94a3b8;
}

html.dark .feature-tag {
  background: rgba(102, 126, 234, 0.2) !important;
  color: #a5b4fc !important;
}

html.dark .quick-start-step {
  background: rgba(102, 126, 234, 0.1);
}

html.dark .quick-start-step:hover {
  background: rgba(102, 126, 234, 0.15);
}

html.dark .step-content h4 {
  color: #e2e8f0;
}

html.dark .step-content p {
  color: #94a3b8;
}

html.dark .secondary-action-btn {
  border-color: #667eea !important;
  color: #667eea !important;
}

html.dark .secondary-action-btn:hover {
  background: rgba(102, 126, 234, 0.2) !important;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .welcome-stats {
    gap: 40px;
  }

  .features-grid {
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 24px;
  }
}

@media (max-width: 768px) {
  .welcome-container {
    padding: 20px 16px;
  }

  .welcome-main {
    max-width: 100%;
  }

  .logo-background {
    width: 100px;
    height: 100px;
  }

  .logo-icon {
    font-size: 48px !important;
  }

  .welcome-title {
    font-size: 36px;
  }

  .title-main {
    font-size: 24px;
  }

  .title-brand {
    font-size: 42px;
  }

  .welcome-subtitle {
    font-size: 18px;
    padding: 0 16px;
  }

  .welcome-stats {
    gap: 30px;
    margin-bottom: 30px;
  }

  .stat-number {
    font-size: 28px;
  }

  .welcome-actions {
    flex-direction: column;
    align-items: center;
    gap: 16px;
    margin-bottom: 60px;
  }

  .primary-action-btn,
  .secondary-action-btn {
    width: 100%;
    max-width: 280px;
  }

  .features-title {
    font-size: 28px;
    margin-bottom: 32px;
  }

  .features-grid {
    grid-template-columns: 1fr;
    gap: 20px;
  }

  .feature-card {
    padding: 24px 20px;
  }
}

@media (max-width: 480px) {
  .welcome-container {
    padding: 16px 12px;
  }

  .logo-background {
    width: 80px;
    height: 80px;
  }

  .logo-icon {
    font-size: 40px !important;
  }

  .welcome-title {
    font-size: 28px;
  }

  .title-main {
    font-size: 20px;
  }

  .title-brand {
    font-size: 32px;
  }

  .welcome-subtitle {
    font-size: 16px;
  }

  .welcome-stats {
    flex-direction: column;
    gap: 20px;
  }

  .stat-number {
    font-size: 24px;
  }

  .features-title {
    font-size: 24px;
  }

  .feature-card {
    padding: 20px 16px;
  }

  .quick-start-step {
    flex-direction: column;
    text-align: center;
  }

  .step-number {
    margin-right: 0;
    margin-bottom: 12px;
  }
}
</style>