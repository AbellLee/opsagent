import axios from 'axios'

// 创建 axios 实例
const apiClient = axios.create({
  baseURL: '/api',
  timeout: 60000
})

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    if (error.response?.status === 401) {
      // token 过期或无效，清除本地存储并跳转到登录页
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// 用户相关 API
export const userAPI = {
  login: (credentials) => apiClient.post('/users/login', credentials),
  register: (userData) => apiClient.post('/users', userData),
  getProfile: (userId) => apiClient.get(`/users/${userId}`),
  updateProfile: (userId, userData) => apiClient.put(`/users/profile`, userData),
  listUsers: () => apiClient.get('/users/list')  // 调试用接口
}

// 会话相关 API
export const sessionAPI = {
  list: (userId) => apiClient.get(`/sessions/?user_id=${userId}`),
  create: (sessionData) => apiClient.post('/sessions', sessionData),
  get: (sessionId) => apiClient.get(`/sessions/${sessionId}`),
  getMessages: (sessionId) => apiClient.get(`/sessions/${sessionId}/messages`),
  updateName: (sessionId, sessionName) => apiClient.put(`/sessions/${sessionId}/name?session_name=${encodeURIComponent(sessionName)}`),
  'delete': (sessionId) => apiClient.delete(`/sessions/${sessionId}`)
}

// 消息相关 API
export const messageAPI = {
  send: (sessionId, messageData) => apiClient.post(`/sessions/${sessionId}/chat`, messageData),
  execute: (sessionId, messageData) => apiClient.post(`/sessions/${sessionId}/execute`, messageData),

  // 流式聊天API
  sendStreaming: async (sessionId, messageData, onChunk, onComplete, onError) => {
    try {
      const response = await fetch(`/api/sessions/${sessionId}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...messageData,
          response_mode: 'streaming'
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let fullContent = ''

      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value, { stream: true })
        buffer += chunk

        // 处理完整的行
        const lines = buffer.split('\n')
        // 保留最后一行（可能不完整）
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.slice(6).trim()
            if (dataStr === '[DONE]') {
              onComplete && onComplete(fullContent)
              return fullContent
            }

            if (dataStr) {
              try {
                const chunkData = JSON.parse(dataStr)
                if (chunkData.chunk) {
                  fullContent += chunkData.chunk
                  onChunk && onChunk(chunkData.chunk, fullContent, chunkData.is_final)
                }

                if (chunkData.is_final) {
                  onComplete && onComplete(fullContent)
                  return fullContent
                }
              } catch (e) {
                console.error('解析JSON失败:', dataStr, e)
              }
            }
          }
        }
      }
    } catch (error) {
      onError && onError(error)
      throw error
    }
  }
}

// 工具相关 API
export const toolAPI = {
  list: () => apiClient.get('/tools'),
  get: (toolId) => apiClient.get(`/tools/${toolId}`),
  updateApprovalConfig: (toolId, configData) => apiClient.put(`/tools/${toolId}/approval`, configData)
}

// 审批相关 API
export const approvalAPI = {
  list: () => apiClient.get('/approvals'),
  request: (approvalData) => apiClient.post('/approvals', approvalData),
  approve: (approvalId) => apiClient.post(`/approvals/${approvalId}/approve`),
  reject: (approvalId) => apiClient.post(`/approvals/${approvalId}/reject`)
}

// MCP配置相关 API
export const mcpConfigAPI = {
  list: (enabledOnly = false) => apiClient.get(`/mcp-configs${enabledOnly ? '?enabled_only=true' : ''}`),
  create: (configData) => apiClient.post('/mcp-configs', configData),
  get: (configId) => apiClient.get(`/mcp-configs/${configId}`),
  update: (configId, configData) => apiClient.put(`/mcp-configs/${configId}`, configData),
  delete: (configId) => apiClient.delete(`/mcp-configs/${configId}`),
  toggle: (configId) => apiClient.post(`/mcp-configs/${configId}/toggle`),
  validate: (configData) => apiClient.post('/mcp-configs/validate', configData),
  reload: () => apiClient.post('/mcp-configs/reload')
}

// 任务相关 API
export const taskAPI = {
  list: (sessionId) => apiClient.get(`/sessions/${sessionId}/tasks`),
  add: (taskData) => apiClient.post('/tasks', taskData),
  update: (taskId, taskData) => apiClient.put(`/tasks/${taskId}`, taskData),
  get: (taskId) => apiClient.get(`/tasks/${taskId}`)
}

// 中断相关 API
export const interruptAPI = {
  interrupt: (sessionId, reason = "User requested interrupt") =>
    apiClient.post(`/sessions/${sessionId}/interrupt`, { reason })
}

// Dify Agent 相关 API
export const difyAgentAPI = {
  list: (enabledOnly = false) => apiClient.get(`/dify-agents${enabledOnly ? '?enabled_only=true' : ''}`),
  create: (agentData) => apiClient.post('/dify-agents', agentData),
  get: (agentId) => apiClient.get(`/dify-agents/${agentId}`),
  update: (agentId, agentData) => apiClient.put(`/dify-agents/${agentId}`, agentData),
  delete: (agentId) => apiClient.delete(`/dify-agents/${agentId}`),
  test: (agentId, testData) => apiClient.post(`/dify-agents/${agentId}/test`, testData),
  refreshCache: () => apiClient.post('/dify-agents/refresh-cache')
}
