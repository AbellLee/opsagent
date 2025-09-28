<template>
  <n-config-provider :locale="zhCN" :date-locale="dateZhCN">
    <n-message-provider>
      <n-layout style="height: 100vh">
        <n-layout-header bordered style="padding: 16px; display: flex; align-items: center; justify-content: space-between;">
          <h2 style="margin: 0">OpsAgent 管理平台</h2>
          <n-button v-if="userStore.isAuthenticated" @click="handleLogout" size="small">退出登录</n-button>
        </n-layout-header>
        
        <n-layout has-sider style="height: calc(100vh - 64px)">
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
              <h3 style="margin: 0; padding: 16px;">会话列表</h3>
              <n-button text @click="createNewSession" style="padding: 16px;">
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
                    <div style="flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                      <n-ellipsis>{{ session.session_name || '新建对话' }}</n-ellipsis>
                    </div>
                    <n-dropdown 
                      :options="sessionOptions" 
                      @select="(key) => handleSessionAction(key, session)"
                      trigger="click"
                      placement="bottom-end"
                    >
                      <n-button text>
                        <n-icon size="16">
                          <MoreHorizontal />
                        </n-icon>
                      </n-button>
                    </n-dropdown>
                  </div>
                  <div style="font-size: 12px; color: #999; margin-top: 4px;">
                    {{ formatTime(session.created_at) }}
                  </div>
                </n-list-item>
              </n-list>
            </n-scrollbar>
          </n-layout-sider>
          
          <n-layout-content>
            <router-view />
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
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from './stores/user'
import { useSessionStore } from './stores/session'
import { sessionAPI } from './api'
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
import { Add, Trash, MoreHorizontal } from '@vicons/ionicons5'

const router = useRouter()
const userStore = useUserStore()
const sessionStore = useSessionStore()
const { message } = createDiscreteApi(['message'])

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
const selectSession = (session) => {
  sessionStore.setSessionId(session.session_id)
  // 这里应该加载会话的详细内容
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
</style>