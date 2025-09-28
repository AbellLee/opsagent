<template>
  <n-config-provider :locale="zhCN" :date-locale="dateZhCN">
    <n-message-provider>
      <n-layout style="height: 100vh; overflow: hidden;">
        <!-- 只在用户已登录时显示 header -->
        <n-layout-header
          v-if="userStore.isAuthenticated"
          bordered
          style="padding: 16px; display: flex; align-items: center; justify-content: space-between;"
        >
          <div>
            <h3 style="margin: 0">{{ currentSession?.session_name || '请选择或新建对话' }}</h3>
            <div style="font-size: 12px; color: #666;">ID: {{ currentSession?.session_id || '无' }}</div>
          </div>

          <!-- 用户菜单 -->
          <div class="user-menu">
            <n-dropdown
              :options="userMenuOptions"
              @select="handleUserMenuAction"
              trigger="click"
              placement="bottom-end"
            >
              <div class="user-avatar-wrapper">
                <n-avatar
                  :size="36"
                  :src="userStore.user?.avatar"
                  :fallback-src="defaultAvatar"
                  class="user-avatar"
                >
                  <n-icon size="20" v-if="!userStore.user?.avatar">
                    <Person />
                  </n-icon>
                </n-avatar>
                <n-icon size="12" class="dropdown-icon">
                  <ChevronDown />
                </n-icon>
              </div>
            </n-dropdown>
          </div>
        </n-layout-header>

        <n-layout has-sider :style="{ height: userStore.isAuthenticated ? 'calc(100vh - 64px)' : '100vh', overflow: 'hidden' }">
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
          </n-layout-sider>
          
          <n-layout-content style="overflow: hidden; height: 100%;">
            <!-- 只有在已登录且没有选择会话时显示欢迎页面 -->
            <WelcomeView v-if="userStore.isAuthenticated && (!sessionStore.sessionId || sessionStore.sessionId === '')" />
            <!-- 已登录且有会话时显示聊天视图 -->
            <ChatView v-else-if="userStore.isAuthenticated && sessionStore.sessionId" style="height: 100%;" />
            <!-- 未登录时显示路由视图（登录/注册页面） -->
            <router-view v-else style="height: 100%;" />
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

        <!-- 用户信息弹窗 -->
        <n-modal v-model:show="showUserProfileModal" preset="card" title="用户信息" style="width: 500px;">
          <div v-if="userProfileLoading" class="profile-loading">
            <n-spin size="medium">
              <template #description>
                加载用户信息中...
              </template>
            </n-spin>
          </div>

          <div v-else-if="userProfileData" class="user-profile-content">
            <!-- 用户头像 -->
            <div class="profile-avatar-section">
              <n-avatar
                :size="80"
                :src="userProfileData.avatar"
                :fallback-src="defaultAvatar"
                class="profile-avatar"
              >
                <n-icon size="40" v-if="!userProfileData.avatar">
                  <Person />
                </n-icon>
              </n-avatar>
            </div>

            <!-- 用户基本信息 -->
            <div class="profile-info-section">
              <n-descriptions :column="1" bordered>
                <n-descriptions-item label="用户ID">
                  <n-text code>{{ userProfileData.user_id }}</n-text>
                </n-descriptions-item>
                <n-descriptions-item label="用户名">
                  <n-text strong>{{ userProfileData.username }}</n-text>
                </n-descriptions-item>
                <n-descriptions-item label="邮箱">
                  <n-text>{{ userProfileData.email }}</n-text>
                </n-descriptions-item>
                <n-descriptions-item label="注册时间">
                  <n-text>{{ formatTime(userProfileData.created_at) }}</n-text>
                </n-descriptions-item>
                <n-descriptions-item label="最后更新">
                  <n-text>{{ formatTime(userProfileData.updated_at) }}</n-text>
                </n-descriptions-item>
              </n-descriptions>
            </div>
          </div>

          <div v-else class="profile-error">
            <n-result status="error" title="加载失败" description="无法获取用户信息，请稍后重试">
              <template #footer>
                <n-button @click="loadUserProfile" type="primary">重新加载</n-button>
              </template>
            </n-result>
          </div>

          <template #footer>
            <div class="profile-footer">
              <n-button @click="showUserProfileModal = false">关闭</n-button>
              <n-button type="primary" @click="editUserProfile" disabled>编辑资料</n-button>
            </div>
          </template>
        </n-modal>
      </n-layout>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup>
import { ref, onMounted, computed, h, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from './stores/user'
import { useSessionStore } from './stores/session'
import { sessionAPI, userAPI } from './api'
import WelcomeView from './views/WelcomeView.vue'
import ChatView from './views/ChatView.vue'
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
  NDropdown,
  NAvatar,
  NSpin,
  NDescriptions,
  NDescriptionsItem,
  NText,
  NResult
} from 'naive-ui'
import { zhCN, dateZhCN } from 'naive-ui'
import { createDiscreteApi } from 'naive-ui'
import {
  Add,
  ChatboxEllipses,
  EllipsisVertical,
  Person,
  ChevronDown,
  LogOut,
  Settings,
  InformationCircle
} from '@vicons/ionicons5'

const router = useRouter()
const userStore = useUserStore()
const sessionStore = useSessionStore()
const { message } = createDiscreteApi(['message'])

// 计算属性：获取当前会话信息
const currentSession = computed(() => {
  try {
    if (!sessionStore.sessions || !sessionStore.sessionId) {
      return { session_name: '请选择或新建对话', session_id: null }
    }
    return sessionStore.sessions.find(s => s.session_id === sessionStore.sessionId) || { session_name: '请选择或新建对话', session_id: null }
  } catch (error) {
    console.warn('获取当前会话信息失败:', error)
    return { session_name: '请选择或新建对话', session_id: null }
  }
})

const collapsed = ref(false)

// 会话操作相关状态
const showRenameModal = ref(false)
const sessionToRename = ref(null)
const newSessionName = ref('')

// 用户信息相关状态
const showUserProfileModal = ref(false)
const userProfileData = ref(null)
const userProfileLoading = ref(false)

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

// 用户菜单选项
const userMenuOptions = [
  {
    label: '用户信息',
    key: 'profile',
    icon: () => h(NIcon, null, { default: () => h(InformationCircle) })
  },
  {
    label: '设置',
    key: 'settings',
    icon: () => h(NIcon, null, { default: () => h(Settings) })
  },
  {
    type: 'divider'
  },
  {
    label: '退出登录',
    key: 'logout',
    icon: () => h(NIcon, null, { default: () => h(LogOut) })
  }
]

// 默认头像
const defaultAvatar = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHZpZXdCb3g9IjAgMCA0MCA0MCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPGNpcmNsZSBjeD0iMjAiIGN5PSIyMCIgcj0iMjAiIGZpbGw9IiNGNUY1RjUiLz4KPHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIiB4PSI4IiB5PSI4Ij4KPHBhdGggZD0iTTEyIDEyQzE0LjIwOTEgMTIgMTYgMTAuMjA5MSAxNiA4QzE2IDUuNzkwODYgMTQuMjA5MSA0IDEyIDRDOS43OTA4NiA0IDggNS43OTA4NiA4IDhDOCAxMC4yMDkxIDkuNzkwODYgMTIgMTIgMTJaIiBmaWxsPSIjOTk5OTk5Ii8+CjxwYXRoIGQ9Ik0xMiAxNEM5LjMzIDEzLjk5IDcuMDEgMTUuNjIgNiAxOEMxMC4wMSAyMCAxMy45OSAyMCAxOCAxOEMxNi45OSAxNS42MiAxNC42NyAxMy45OSAxMiAxNFoiIGZpbGw9IiM5OTk5OTkiLz4KPC9zdmc+Cjwvc3ZnPgo='

// 监听用户认证状态变化
watch(() => userStore.isAuthenticated, async (isAuthenticated, wasAuthenticated) => {
  console.log('用户认证状态变化:', { isAuthenticated, wasAuthenticated })

  if (isAuthenticated && !wasAuthenticated) {
    // 用户刚刚登录，加载会话列表
    console.log('用户刚刚登录，开始加载会话数据')
    try {
      await loadSessions()
      console.log('登录后会话数据加载完成')
    } catch (error) {
      console.error('登录后加载会话数据失败:', error)
    }
  } else if (!isAuthenticated && wasAuthenticated) {
    // 用户刚刚退出登录，清空会话数据
    console.log('用户退出登录，清空会话数据')
    sessionStore.resetSession()
  }
}, { immediate: false })

// 监听路由变化，确保在访问聊天页面时加载会话列表
watch(() => router.currentRoute.value.path, async (newPath, oldPath) => {
  console.log('路由变化:', { newPath, oldPath })

  if (newPath === '/chat' && userStore.isAuthenticated) {
    console.log('访问聊天页面且用户已登录，检查会话列表')

    // 如果会话列表为空，则加载
    if (!sessionStore.sessions || sessionStore.sessions.length === 0) {
      console.log('会话列表为空，开始加载')
      try {
        await loadSessions()
        console.log('路由变化后会话数据加载完成')
      } catch (error) {
        console.error('路由变化后加载会话数据失败:', error)
      }
    } else {
      console.log('会话列表已存在，跳过加载')
    }
  }
}, { immediate: true })

// 初始化用户状态
onMounted(async () => {
  try {
    console.log('应用初始化开始')

    // 初始化用户状态
    userStore.initializeFromStorage()
    console.log('用户状态初始化完成:', userStore.isAuthenticated)

    // 确保 sessionStore 有默认值
    if (!sessionStore.sessions) {
      sessionStore.setSessions([])
    }

    // 如果用户已登录，加载会话数据
    if (userStore.isAuthenticated) {
      console.log('用户已登录，开始加载会话数据')
      await loadSessions()
    } else {
      console.log('用户未登录，跳过会话数据加载')
    }

    console.log('应用初始化完成')
  } catch (error) {
    console.error('应用初始化失败:', error)
  }
})

// 加载会话列表
const loadSessions = async () => {
  try {
    console.log('开始加载会话列表...')
    // 传递用户ID以获取用户的会话列表
    const userId = userStore.user?.user_id
    console.log('当前用户ID:', userId)

    if (userId) {
      const sessions = await sessionAPI.list(userId)
      console.log('获取到的会话列表:', sessions)
      sessionStore.setSessions(sessions)
      console.log('会话列表已设置到store')
    } else {
      console.warn('用户ID为空，无法加载会话列表')
    }
  } catch (error) {
    console.error('加载会话列表失败:', error)
    message.error('加载会话列表失败: ' + (error.response?.data?.detail || error.message))
  }
}

// 强制刷新会话列表（供外部调用）
const refreshSessions = async () => {
  console.log('强制刷新会话列表')
  if (userStore.isAuthenticated) {
    await loadSessions()
  }
}

// 暴露给全局使用
window.refreshSessions = refreshSessions

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

// 处理用户菜单操作
const handleUserMenuAction = (key) => {
  switch (key) {
    case 'profile':
      showUserProfile()
      break
    case 'settings':
      showSettings()
      break
    case 'logout':
      handleLogout()
      break
  }
}

// 显示用户信息
const showUserProfile = () => {
  console.log('当前用户信息:', userStore.user)
  showUserProfileModal.value = true
  loadUserProfile()
}

// 加载用户信息
const loadUserProfile = async () => {
  if (!userStore.user?.user_id) {
    message.error('用户信息不完整')
    return
  }

  try {
    userProfileLoading.value = true
    userProfileData.value = null

    console.log('尝试获取用户信息，用户ID:', userStore.user.user_id)

    // 先尝试获取用户列表进行调试
    try {
      const userList = await userAPI.listUsers()
      console.log('数据库中的用户列表:', userList)
    } catch (listError) {
      console.warn('获取用户列表失败:', listError)
    }

    // 获取特定用户信息
    const profile = await userAPI.getProfile(userStore.user.user_id)
    userProfileData.value = profile
    console.log('获取用户信息成功:', profile)
  } catch (error) {
    console.error('获取用户信息失败:', error)
    console.error('错误详情:', error.response?.data)

    // 如果从后端获取失败，使用本地存储的用户信息作为备选
    if (userStore.user) {
      console.log('使用本地存储的用户信息作为备选')
      userProfileData.value = {
        user_id: userStore.user.user_id,
        username: userStore.user.username,
        email: userStore.user.email,
        created_at: userStore.user.created_at,
        updated_at: userStore.user.updated_at
      }
      message.warning('从本地缓存加载用户信息')
    } else {
      message.error('获取用户信息失败: ' + (error.response?.data?.detail || error.message))
    }
  } finally {
    userProfileLoading.value = false
  }
}

// 编辑用户资料
const editUserProfile = () => {
  message.info('编辑功能开发中...')
}

// 显示设置
const showSettings = () => {
  message.info('设置功能开发中...')
  // 这里可以打开设置模态框或跳转到设置页面
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
  overflow: hidden;
}

html, body {
  height: 100%;
  margin: 0;
  padding: 0;
  overflow: hidden;
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

/* 用户菜单样式 */
.user-menu {
  position: relative;
}

.user-avatar-wrapper {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.2s ease;
  background: transparent;
}

.user-avatar-wrapper:hover {
  background: rgba(0, 0, 0, 0.05);
}

.user-avatar {
  border: 2px solid #e5e7eb;
  transition: all 0.2s ease;
}

.user-avatar-wrapper:hover .user-avatar {
  border-color: #3b82f6;
}

.dropdown-icon {
  color: #6b7280;
  transition: all 0.2s ease;
}

.user-avatar-wrapper:hover .dropdown-icon {
  color: #3b82f6;
}

/* 暗色模式支持 */
html.dark .user-avatar-wrapper:hover {
  background: rgba(255, 255, 255, 0.1);
}

html.dark .user-avatar {
  border-color: #4b5563;
}

html.dark .user-avatar-wrapper:hover .user-avatar {
  border-color: #3b82f6;
}

html.dark .dropdown-icon {
  color: #9ca3af;
}

html.dark .user-avatar-wrapper:hover .dropdown-icon {
  color: #3b82f6;
}

/* 用户信息弹窗样式 */
.profile-loading {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 40px 0;
}

.user-profile-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.profile-avatar-section {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px 0;
}

.profile-avatar {
  border: 3px solid #e5e7eb;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.profile-info-section {
  flex: 1;
}

.profile-error {
  padding: 20px 0;
}

.profile-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* 暗色模式下的用户信息弹窗 */
html.dark .profile-avatar {
  border-color: #4b5563;
}
</style>