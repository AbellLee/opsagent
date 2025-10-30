<template>
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

    <!-- 设置弹窗 -->
    <n-modal v-model:show="showSettingsModal" preset="card" title="设置" style="width: 900px; height: 600px;">
      <div class="settings-container">
        <!-- 左侧导航 -->
        <div class="settings-sidebar">
          <div
            class="settings-nav-item"
            :class="{ active: activeSettingsTab === 'mcp' }"
            @click="activeSettingsTab = 'mcp'"
          >
            MCP配置
          </div>
          <div
            class="settings-nav-item"
            :class="{ active: activeSettingsTab === 'dify' }"
            @click="activeSettingsTab = 'dify'"
          >
            Dify Agent
          </div>
          <div
            class="settings-nav-item"
            :class="{ active: activeSettingsTab === 'other' }"
            @click="activeSettingsTab = 'other'"
          >
            其他配置
          </div>
        </div>

        <!-- 右侧内容 -->
        <div class="settings-content">
          <MCPConfigPanel v-if="activeSettingsTab === 'mcp'" />
          <DifyAgentPanel v-else-if="activeSettingsTab === 'dify'" />
          <div v-else-if="activeSettingsTab === 'other'" class="other-settings">
            <n-result status="info" title="其他设置" description="功能开发中...">
            </n-result>
          </div>
        </div>
      </div>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, h } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { useSessionStore } from '../stores/session'
import { userAPI } from '../api'
import {
  NDropdown,
  NAvatar,
  NIcon,
  NModal,
  NSpin,
  NDescriptions,
  NDescriptionsItem,
  NText,
  NResult,
  NButton
} from 'naive-ui'
import MCPConfigPanel from './MCPConfigPanel.vue'
import DifyAgentPanel from './DifyAgentPanel.vue'
import { createDiscreteApi } from 'naive-ui'
import {
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

// 用户信息相关状态
const showUserProfileModal = ref(false)
const userProfileData = ref(null)
const userProfileLoading = ref(false)

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

// 设置相关状态
const showSettingsModal = ref(false)
const activeSettingsTab = ref('mcp')

// 显示设置
const showSettings = () => {
  showSettingsModal.value = true
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
</script>

<style scoped>
/* 用户菜单样式美化 */
.user-menu {
  position: relative;
}

.user-avatar-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: 25px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.user-avatar-wrapper:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: translateY(-1px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.user-avatar {
  border: 3px solid rgba(255, 255, 255, 0.3);
  transition: all 0.3s ease;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.user-avatar-wrapper:hover .user-avatar {
  border-color: rgba(255, 255, 255, 0.6);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15);
}

.dropdown-icon {
  color: rgba(255, 255, 255, 0.7);
  transition: all 0.3s ease;
}

.user-avatar-wrapper:hover .dropdown-icon {
  color: rgba(255, 255, 255, 0.9);
  transform: rotate(180deg);
}

/* 用户信息弹窗样式美化 */
.profile-loading {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 60px 0;
}

.user-profile-content {
  display: flex;
  flex-direction: column;
  gap: 32px;
  padding: 20px;
}

.profile-avatar-section {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 30px 0;
  position: relative;
}

.profile-avatar-section::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 120px;
  height: 120px;
  background: linear-gradient(135deg, #a8d8ea 0%, #aa96da 100%);
  border-radius: 50%;
  opacity: 0.1;
  z-index: 0;
}

.profile-avatar {
  border: 4px solid #a8d8ea;
  box-shadow: 0 8px 32px rgba(168, 216, 234, 0.3);
  position: relative;
  z-index: 1;
  transition: all 0.3s ease;
}

.profile-avatar:hover {
  transform: scale(1.05);
  box-shadow: 0 12px 40px rgba(168, 216, 234, 0.4);
}

.profile-info-section {
  flex: 1;
}

.profile-error {
  padding: 40px 0;
  text-align: center;
}

.profile-footer {
  display: flex;
  justify-content: flex-end;
  gap: 16px;
  padding-top: 20px;
  border-top: 1px solid rgba(0, 0, 0, 0.1);
}

/* 暗色模式美化 */
html.dark .user-avatar-wrapper {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.1);
}

html.dark .user-avatar-wrapper:hover {
  background: rgba(255, 255, 255, 0.1);
}

html.dark .user-avatar {
  border-color: rgba(255, 255, 255, 0.2);
}

html.dark .user-avatar-wrapper:hover .user-avatar {
  border-color: rgba(255, 255, 255, 0.4);
}

html.dark .profile-avatar {
  border-color: #a8d8ea;
}

html.dark .profile-footer {
  border-top-color: rgba(255, 255, 255, 0.1);
}

/* 设置弹窗样式 */
.settings-container {
  display: flex;
  height: 500px;
}

.settings-sidebar {
  width: 150px;
  border-right: 1px solid var(--border-color);
  padding: 16px 0;
}

.settings-nav-item {
  padding: 12px 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  border-radius: 8px;
  margin: 0 8px 4px 8px;
  color: var(--text-color-2);
}

.settings-nav-item:hover {
  background-color: var(--hover-color);
  color: var(--text-color-1);
}

.settings-nav-item.active {
  background: linear-gradient(135deg, #a8d8ea 0%, #aa96da 100%);
  color: white;
}

.settings-content {
  flex: 1;
  overflow: hidden;
}

.other-settings {
  padding: 40px;
  text-align: center;
}

/* 暗色模式 */
html.dark .settings-sidebar {
  border-right-color: rgba(255, 255, 255, 0.1);
}
</style>
