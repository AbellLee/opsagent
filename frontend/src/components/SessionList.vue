<template>
  <div class="session-list-container">
    <div class="session-list-header">
      <!-- 展开状态 -->
      <template v-if="!collapsed">
        <h4 style="margin: 0; font-size: 18px; font-weight: 600;">会话列表</h4>
        <n-button text @click="createNewSession" class="new-session-btn">
          <n-icon size="18">
            <Add />
          </n-icon>
        </n-button>
      </template>
      <!-- 收起状态 -->
      <template v-else>
        <div style="width: 100%; display: flex; justify-content: center;">
          <n-button text @click="createNewSession" title="新建会话" class="new-session-btn-collapsed">
            <n-icon size="20">
              <Add />
            </n-icon>
          </n-button>
        </div>
      </template>
    </div>
    
    <n-scrollbar class="session-list-scroll">
      <n-list hoverable clickable>
        <n-list-item 
          v-for="session in sessionStore.sessions" 
          :key="session.session_id"
          @click="selectSession(session)"
          :class="{ active: session.session_id === sessionStore.sessionId }"
        >
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <!-- 收起时只显示图标 -->
            <div v-show="!collapsed" style="flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
              <n-ellipsis :tooltip="false">{{ session.session_name || '新建对话' }}</n-ellipsis>
            </div>
            <div v-show="collapsed" style="flex: 1; text-align: center; padding: 8px 0;" :title="session.session_name || '新建对话'">
              <n-icon size="18">
                <ChatboxEllipses />
              </n-icon>
            </div>
            
            <n-dropdown 
              :options="sessionOptions" 
              @select="(key) => handleSessionAction(key, session)"
              trigger="click"
              placement="bottom-end"
            >
              <n-button v-show="!collapsed" text :tooltip="false">
                <n-icon size="16">
                  <EllipsisVertical />
                </n-icon>
              </n-button>
            </n-dropdown>
          </div>
          <div v-show="!collapsed" style="font-size: 12px; color: #999; margin-top: 4px;">
            {{ formatTime(session.created_at) }}
          </div>
        </n-list-item>
      </n-list>
    </n-scrollbar>

    <!-- 修改会话名称的模态框 -->
    <n-modal v-model:show="showRenameModal" preset="dialog" title="修改会话名称">
      <n-input v-model:value="newSessionName" placeholder="请输入会话名称" />
      <template #action>
        <n-button @click="showRenameModal = false" size="small">取消</n-button>
        <n-button @click="confirmRenameSession" size="small" type="primary">确定</n-button>
      </template>
    </n-modal>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useUserStore } from '../stores/user'
import { useSessionStore } from '../stores/session'
import { sessionAPI } from '../api'
import {
  NList,
  NListItem,
  NButton,
  NScrollbar,
  NIcon,
  NModal,
  NInput,
  NEllipsis,
  NDropdown
} from 'naive-ui'
import { createDiscreteApi } from 'naive-ui'
import {
  Add,
  ChatboxEllipses,
  EllipsisVertical
} from '@vicons/ionicons5'

// Props
const props = defineProps({
  collapsed: {
    type: Boolean,
    default: false
  }
})

const userStore = useUserStore()
const sessionStore = useSessionStore()
const { message } = createDiscreteApi(['message'])

// 会话操作相关状态
const showRenameModal = ref(false)
const sessionToRename = ref(null)
const newSessionName = ref('')

// 会话操作选项
const sessionOptions = [
  {
    label: '修改名称',
    key: 'rename'
  },
  {
    label: '删除会话',
    key: 'delete'
  }
]

// 创建新会话
const createNewSession = async () => {
  try {
    const response = await sessionAPI.create({
      user_id: userStore.user?.user_id || 'default_user'
    })
    
    sessionStore.addSession(response)
    sessionStore.setSessionId(response.session_id)
    
    // 加载新创建的会话消息（初始为空）
    sessionStore.setMessages([])
    
    message.success('新会话创建成功')
  } catch (error) {
    console.error('创建新会话失败:', error)
    message.error('创建新会话失败')
  }
}

// 选择会话
const selectSession = async (session) => {
  sessionStore.setSessionId(session.session_id)
  // 加载会话的详细内容（消息）
  try {
    const response = await sessionAPI.getMessages(session.session_id)
    sessionStore.setMessages(response.messages || [])
  } catch (error) {
    console.error('加载会话消息失败:', error)
    message.error('加载会话消息失败: ' + (error.response?.data?.detail || error.message))
    sessionStore.setMessages([]) // 出错时清空消息
  }
}

// 处理会话操作
const handleSessionAction = (key, session) => {
  switch (key) {
    case 'rename':
      renameSession(session)
      break
    case 'delete':
      deleteSession(session.session_id)
      break
  }
}

// 重命名会话
const renameSession = (session) => {
  sessionToRename.value = session
  newSessionName.value = session.session_name || '新建对话'
  showRenameModal.value = true
}

// 确认重命名会话
const confirmRenameSession = async () => {
  if (!sessionToRename.value || !newSessionName.value.trim()) {
    message.warning('请输入有效的会话名称')
    return
  }

  try {
    await sessionAPI.updateName(sessionToRename.value.session_id, newSessionName.value.trim())
    
    // 更新本地状态
    const sessionIndex = sessionStore.sessions.findIndex(s => s.session_id === sessionToRename.value.session_id)
    if (sessionIndex !== -1) {
      sessionStore.sessions[sessionIndex].session_name = newSessionName.value.trim()
    }
    
    showRenameModal.value = false
    message.success('会话名称更新成功')
  } catch (error) {
    console.error('更新会话名称失败:', error)
    message.error('更新会话名称失败')
  }
}

// 删除会话
const deleteSession = async (sessionId) => {
  try {
    await sessionAPI.delete(sessionId)
    sessionStore.removeSession(sessionId)
    
    // 如果删除的是当前会话，清除当前会话ID
    if (sessionStore.sessionId === sessionId) {
      sessionStore.setSessionId(null)
    }
    
    message.success('会话删除成功')
  } catch (error) {
    console.error('删除会话失败:', error)
    message.error('删除会话失败')
  }
}

// 格式化时间
const formatTime = (time) => {
  return new Date(time).toLocaleString('zh-CN')
}
</script>

<style scoped>
.session-list-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

/* 会话列表头部美化 */
.session-list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  background: linear-gradient(135deg, var(--primary-color-1) 0%, var(--primary-color-2) 100%);
  color: white;
  border: none;
  position: relative;
  overflow: hidden;
  flex-shrink: 0;
  height: 80px;
  min-height: 80px;
  max-height: 80px;
  box-sizing: border-box;
  border-radius: var(--border-radius-lg) var(--border-radius-lg) 0 0;
}

.session-list-header::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grain" width="100" height="100" patternUnits="userSpaceOnUse"><circle cx="25" cy="25" r="1" fill="white" opacity="0.1"/><circle cx="75" cy="75" r="1" fill="white" opacity="0.1"/><circle cx="50" cy="10" r="0.5" fill="white" opacity="0.1"/></pattern></defs><rect width="100" height="100" fill="url(%23grain)"/></svg>');
  opacity: 0.3;
  border-radius: var(--border-radius-lg) var(--border-radius-lg) 0 0;
}

.session-list-header > * {
  position: relative;
  z-index: 1;
}

.session-list-header h4 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  letter-spacing: 0.5px;
}

/* 会话列表滚动区域 */
.session-list-scroll {
  flex: 1 !important;
  height: calc(100% - 80px) !important;
  max-height: calc(100% - 80px) !important;
  overflow-y: auto !important;
  overflow-x: hidden !important;
}

/* 新建会话按钮美化 */
.new-session-btn {
  background: rgba(255, 255, 255, 0.2) !important;
  border: 1px solid rgba(255, 255, 255, 0.3) !important;
  color: white !important;
  backdrop-filter: blur(10px);
  transition: all var(--transition-normal);
  border-radius: var(--border-radius-md) !important;
  font-weight: 500;
  padding: var(--spacing-2) var(--spacing-3) !important;
  display: flex;
  align-items: center;
  gap: var(--spacing-1);
}

.new-session-btn:hover {
  background: rgba(255, 255, 255, 0.3) !important;
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

/* 收起状态的新建会话按钮 */
.new-session-btn-collapsed {
  background: rgba(255, 255, 255, 0.2) !important;
  border: 1px solid rgba(255, 255, 255, 0.3) !important;
  color: white !important;
  backdrop-filter: blur(10px);
  transition: all var(--transition-normal);
  border-radius: 50% !important;
  width: 40px !important;
  height: 40px !important;
  padding: 0 !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
}

.new-session-btn-collapsed:hover {
  background: rgba(255, 255, 255, 0.3) !important;
  transform: scale(1.1);
  box-shadow: var(--shadow-md);
}

/* 会话项美化 */
.n-list-item {
  padding: var(--spacing-4) var(--spacing-5) !important;
  cursor: pointer;
  border: none !important;
  transition: all var(--transition-normal);
  position: relative;
  overflow: hidden;
  margin: 0 var(--spacing-2);
  border-radius: var(--border-radius-md) !important;
  margin-bottom: var(--spacing-1);
  backdrop-filter: blur(10px);
}

.n-list-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, var(--primary-color-1) 0%, var(--primary-color-2) 100%);
  opacity: 0;
  transition: opacity var(--transition-normal);
  z-index: 0;
  border-radius: var(--border-radius-md);
}

.n-list-item:hover::before {
  opacity: 0.08;
}

.n-list-item.active::before {
  opacity: 0.12;
}

.n-list-item > * {
  position: relative;
  z-index: 1;
}

.n-list-item:hover {
  transform: translateX(4px);
  box-shadow: 4px 0 12px rgba(168, 216, 234, 0.1);
}

.n-list-item.active {
  background: linear-gradient(135deg, rgba(168, 216, 234, 0.1) 0%, rgba(170, 150, 218, 0.1) 100%) !important;
  border-right: 4px solid var(--primary-color-1) !important;
  transform: translateX(4px);
  box-shadow: var(--shadow-md);
}

/* 会话名称和时间美化 */
.n-list-item .n-ellipsis {
  font-size: 15px !important;
  font-weight: 500 !important;
  color: #2c3e50 !important;
  margin-bottom: 4px !important;
}

.n-list-item div[style*="font-size: 12px"] {
  color: #7f8c8d !important;
  font-weight: 400 !important;
}

/* 会话操作按钮美化 */
.n-list-item .n-button {
  opacity: 0 !important;
  transition: all var(--transition-normal) !important;
  transform: translateX(var(--spacing-2)) !important;
  border-radius: var(--border-radius-sm) !important;
}

.n-list-item:hover .n-button {
  opacity: 0.7 !important;
  transform: translateX(0) !important;
}

.n-list-item .n-button:hover {
  opacity: 1 !important;
  background: rgba(102, 126, 234, 0.1) !important;
}

/* 暗色模式下的会话列表 */
html.dark .session-list-header {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
}

html.dark .n-list-item {
  background: rgba(255, 255, 255, 0.05);
}

html.dark .n-list-item:hover {
  background: rgba(255, 255, 255, 0.1);
}

html.dark .n-list-item .n-ellipsis {
  color: #e2e8f0 !important;
}

html.dark .n-list-item div[style*="font-size: 12px"] {
  color: #94a3b8 !important;
}

html.dark .n-list-item .n-button:hover {
  background: rgba(102, 126, 234, 0.2) !important;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .session-list-header {
    padding: var(--spacing-4) var(--spacing-3);
    height: 60px;
    min-height: 60px;
    max-height: 60px;
  }
  
  .session-list-header h4 {
    font-size: var(--font-size-lg);
  }
  
  .n-list-item {
    padding: var(--spacing-3) var(--spacing-4) !important;
    margin: 0 var(--spacing-1);
  }
}
</style>
