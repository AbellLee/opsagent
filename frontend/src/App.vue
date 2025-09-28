<template>
  <n-config-provider :locale="zhCN" :date-locale="dateZhCN">
    <n-message-provider>
      <n-layout style="height: 100vh; overflow: hidden;">
        <n-layout-header bordered style="padding: 16px; display: flex; align-items: center; justify-content: space-between;">
          <div>
            <h3 style="margin: 0">{{ currentSession?.session_name || '请选择或新建对话' }}</h3>
            <div style="font-size: 12px; color: #666;">ID: {{ currentSession?.session_id }}</div>
          </div>
          <n-button v-if="userStore.isAuthenticated" @click="handleLogout" size="small">退出登录</n-button>
        </n-layout-header>
        
        <n-layout has-sider style="height: calc(100vh - 64px); overflow: hidden;">
          <n-layout-sider
            v-if="userStore.isAuthenticated"
            bordered
            width="240"
            collapse-mode="width"
            :collapsed-width="64"
            :collapsed="collapsed"
            show-trigger
            @collapse="handleCollapse"
            @expand="handleExpand"
          >
            <div class="session-list-header">
              <h3 v-show="!collapsed" style="margin: 0; padding: 16px;">会话列表</h3>
              <n-button v-show="!collapsed" text @click="createNewSession" style="padding: 16px;">
                <n-icon size="18">
                  <Add />
                </n-icon>
              </n-button>
              <!-- 收起时只显示图标 -->
              <n-button v-show="collapsed" text @click="createNewSession" style="padding: 16px;" title="新建会话">
                <n-icon size="18">
                  <Add />
                </n-icon>
              </n-button>
            </div>
            <n-scrollbar style="height: calc(100% - 64px);">
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
                      <n-ellipsis>{{ session.session_name || '新建对话' }}</n-ellipsis>
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
                      <n-button v-show="!collapsed" text>
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
          </n-layout-sider>
          
          <n-layout-content style="overflow: hidden;">
            <!-- 当没有选择会话时显示欢迎页面 -->
            <WelcomeView v-if="!sessionStore.sessionId || sessionStore.sessionId === ''" />
            <router-view v-else />
          </n-layout-content>
        </n-layout>
        
        <!-- 修改会话名称的模态框 -->
        <n-modal v-model:show="showRenameModal" preset="dialog" title="修改会话名称">
          <n-input v-model:value="newSessionName" placeholder="请输入会话名称" />
          <template #action>
            <n-button @click="showRenameModal = false" size="small">取消</n-button>
            <n-button @click="confirmRenameSession" size="small" type="primary">确定</n-button>
          </template>
        </n-modal>
      </n-layout>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from './stores/user'
import { useSessionStore } from './stores/session'
import { sessionAPI } from './api'
import WelcomeView from './views/WelcomeView.vue'
import { 
  NLayout, 
  NLayoutHeader, 
  NLayoutSider, 
  NLayoutContent, 
  NList,
  NListItem,
  NButton,
  NScrollbar,
  NIcon,
  NConfigProvider,
  NModal,
  NInput,
  NEllipsis,
  NDropdown
} from 'naive-ui'
import { zhCN, dateZhCN } from 'naive-ui'
import { createDiscreteApi } from 'naive-ui'
import { Add, Trash, MoreHorizontal, ChatboxEllipses, EllipsisVertical } from '@vicons/ionicons5'

const router = useRouter()
const userStore = useUserStore()
const sessionStore = useSessionStore()
const { message } = createDiscreteApi(['message'])

// 计算属性：获取当前会话信息
const currentSession = computed(() => {
  return sessionStore.sessions.find(s => s.session_id === sessionStore.sessionId) || {}
})

const collapsed = ref(false)

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

// 初始化用户状态
onMounted(async () => {
  userStore.initializeFromStorage()
  if (userStore.isAuthenticated) {
    await loadSessions()
  }
})

// 加载会话列表
const loadSessions = async () => {
  try {
    // 传递用户ID以获取用户的会话列表
    const userId = userStore.user?.user_id
    if (userId) {
      const sessions = await sessionAPI.list(userId)
      sessionStore.setSessions(sessions)
    }
  } catch (error) {
    console.error('加载会话列表失败:', error)
    message.error('加载会话列表失败: ' + (error.response?.data?.detail || error.message))
  }
}

// 创建新会话
const createNewSession = async () => {
  try {
    const response = await sessionAPI.create({
      user_id: userStore.user?.user_id || 'default_user'
    })
    
    sessionStore.addSession(response)
    sessionStore.setSessionId(response.session_id)
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

// 登出处理
const handleLogout = () => {
  userStore.logout()
  sessionStore.resetSession()
  router.push('/login')
}

// 处理侧边栏折叠和展开事件
const handleCollapse = () => {
  collapsed.value = true
}

const handleExpand = () => {
  collapsed.value = false
}
</script>

<style>
#app {
  height: 100%;
}

.session-list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #eee;
}

.active {
  background-color: #e6f4ff;
}

/* 全局隐藏滚动条但仍保持滚动功能 */
::-webkit-scrollbar {
  width: 0 !important;
  height: 0 !important;
  display: none;
  background: transparent;
}

* {
  scrollbar-width: none;
  -ms-overflow-style: none;
}
</style>