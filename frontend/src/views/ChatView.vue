<template>
  <div style="padding: 20px; height: calc(100vh - 100px)">
    <n-card title="Agent聊天" style="height: 100%; display: flex; flex-direction: column;">
      <div style="flex: 1; overflow-y: auto; margin-bottom: 20px; padding: 10px;" ref="messageContainer">
        <div v-for="(message, index) in sessionStore.messages" :key="index" style="margin-bottom: 15px;">
          <div :style="{ 
            textAlign: message.role === 'user' ? 'right' : 'left',
            display: 'flex',
            justifyContent: message.role === 'user' ? 'flex-end' : 'flex-start'
          }">
            <n-avatar 
              :size="36" 
              style="margin-right: 10px;"
              :style="{ 
                order: message.role === 'user' ? 2 : 1,
                marginRight: message.role === 'user' ? '0' : '10px',
                marginLeft: message.role === 'user' ? '10px' : '0'
              }"
            >
              {{ message.role === 'user' ? 'U' : 'A' }}
            </n-avatar>
            <n-card 
              :style="{ 
                maxWidth: '70%',
                order: message.role === 'user' ? 1 : 2
              }"
              :type="message.role === 'user' ? 'primary' : 'default'"
            >
              <template #header>
                {{ message.role === 'user' ? '你' : 'Agent' }}
              </template>
              <div style="word-break: break-word; white-space: pre-wrap;">
                {{ message.content }}
              </div>
            </n-card>
          </div>
        </div>
      </div>
      
      <div style="display: flex; gap: 10px;">
        <n-input 
          v-model:value="inputMessage" 
          type="textarea" 
          placeholder="输入消息..." 
          :autosize="{ minRows: 2, maxRows: 4 }"
          @keyup.enter="sendMessage"
        />
        <n-button 
          type="primary" 
          @click="sendMessage" 
          :disabled="!inputMessage.trim() || sending"
          style="height: fit-content;"
        >
          发送
        </n-button>
      </div>
    </n-card>
    
    <!-- 工具审批弹窗 -->
    <n-modal v-model:show="showApprovalModal" preset="dialog" title="工具审批">
      <div style="padding: 20px;">
        <n-h3>工具执行需要审批</n-h3>
        <n-p><b>工具名称:</b> {{ pendingApproval.tool_name }}</n-p>
        <n-p><b>请求时间:</b> {{ pendingApproval.created_at }}</n-p>
        <n-p><b>会话ID:</b> {{ pendingApproval.session_id }}</n-p>
        
        <n-space style="margin-top: 20px; display: flex; justify-content: flex-end;">
          <n-button @click="rejectToolExecution">拒绝</n-button>
          <n-button type="primary" @click="approveToolExecution">批准</n-button>
        </n-space>
      </div>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { useSessionStore } from '../stores/session'
import { debounce } from '../utils'
import { 
  NCard, 
  NInput, 
  NButton, 
  NAvatar,
  NModal,
  NH3,
  NP,
  NSpace,
  useMessage
} from 'naive-ui'
import axios from 'axios'

const message = useMessage()
const router = useRouter()
const userStore = useUserStore()
const sessionStore = useSessionStore()

const inputMessage = ref('')
const sending = ref(false)
const showApprovalModal = ref(false)
const pendingApproval = ref({})
const messageContainer = ref(null)

// 检查用户是否已登录
onMounted(() => {
  if (!userStore.isAuthenticated) {
    message.warning('请先登录')
    router.push('/login')
  }
})

// 创建会话
const createSession = async () => {
  try {
    if (!userStore.isAuthenticated) {
      message.error('请先登录')
      throw new Error('用户未登录')
    }
    
    // 使用真实的用户ID创建会话
    const response = await axios.post('http://localhost:8000/api/sessions', {
      user_id: userStore.userProfile.user_id
    })
    
    sessionStore.setSessionId(response.data.session_id)
    message.success('会话创建成功')
  } catch (error) {
    console.error('创建会话失败:', error)
    message.error('创建会话失败: ' + (error.response?.data?.detail || error.message))
  }
}

// 发送消息（使用防抖）
const sendMessage = debounce(async () => {
  if (!inputMessage.value.trim() || sending.value) return
  
  // 添加用户消息到显示
  sessionStore.addMessage({
    role: 'user',
    content: inputMessage.value
  })
  
  // 滚动到底部
  scrollToBottom()
  
  const userMessage = inputMessage.value
  inputMessage.value = ''
  sending.value = true
  
  try {
    // 检查用户是否已登录
    if (!userStore.isAuthenticated) {
      message.error('请先登录')
      router.push('/login')
      return
    }
    
    // 检查是否有会话ID
    if (!sessionStore.sessionId) {
      await createSession()
      if (!sessionStore.sessionId) {
        throw new Error('无法创建会话')
      }
    }
    
    // 调用聊天API
    const response = await axios.post(
      `http://localhost:8000/api/sessions/${sessionStore.sessionId}/chat`,
      {
        message: userMessage
      }
    )
    
    // 检查是否需要工具审批
    const agentResponse = response.data.response
    if (agentResponse.includes('需要审批')) {
      // 模拟获取审批信息
      pendingApproval.value = {
        tool_name: '示例工具',
        created_at: new Date().toLocaleString(),
        session_id: sessionStore.sessionId,
        approval_id: 'approval_' + Date.now()
      }
      showApprovalModal.value = true
    }
    
    // 添加Agent回复到显示
    sessionStore.addMessage({
      role: 'assistant',
      content: response.data.response
    })
    
    // 滚动到底部
    scrollToBottom()
  } catch (error) {
    console.error('发送消息失败:', error)
    message.error('发送消息失败: ' + (error.response?.data?.detail || error.message))
    sessionStore.addMessage({
      role: 'assistant',
      content: '抱歉，我无法处理您的请求。'
    })
    
    // 滚动到底部
    scrollToBottom()
  } finally {
    sending.value = false
  }
}, 300)

// 批准工具执行（使用防抖）
const approveToolExecution = debounce(async () => {
  try {
    // 在实际应用中，这里应该调用后端API批准工具执行
    sessionStore.addMessage({
      role: 'assistant',
      content: `工具 ${pendingApproval.value.tool_name} 已批准执行`
    })
    showApprovalModal.value = false
    message.success('工具执行已批准')
    
    // 滚动到底部
    scrollToBottom()
  } catch (error) {
    console.error('批准失败:', error)
    message.error('批准失败: ' + (error.response?.data?.detail || error.message))
  }
}, 300)

// 拒绝工具执行（使用防抖）
const rejectToolExecution = debounce(async () => {
  try {
    // 在实际应用中，这里应该调用后端API拒绝工具执行
    sessionStore.addMessage({
      role: 'assistant',
      content: `工具 ${pendingApproval.value.tool_name} 已拒绝执行`
    })
    showApprovalModal.value = false
    message.success('工具执行已拒绝')
    
    // 滚动到底部
    scrollToBottom()
  } catch (error) {
    console.error('拒绝失败:', error)
    message.error('拒绝失败: ' + (error.response?.data?.detail || error.message))
  }
}, 300)

// 滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    if (messageContainer.value) {
      messageContainer.value.scrollTop = messageContainer.value.scrollHeight
    }
  })
}
</script>

<style>
/* 禁用过渡动画以减少ResizeObserver错误 */
*, *::before, *::after {
  transition: none !important;
  animation: none !important;
}
</style>