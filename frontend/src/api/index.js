import axios from 'axios'

// 创建 axios 实例
const apiClient = axios.create({
  baseURL: '/api',
  timeout: 10000
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
  register: (userData) => apiClient.post('/users/register', userData)
}

// 会话相关 API
export const sessionAPI = {
  list: (userId) => apiClient.get(`/sessions/?user_id=${userId}`),
  create: (sessionData) => apiClient.post('/sessions', sessionData),
  get: (sessionId) => apiClient.get(`/sessions/${sessionId}`),
  getMessages: (sessionId) => apiClient.get(`/sessions/${sessionId}/messages`),
  updateName: (sessionId, sessionName) => apiClient.put(`/sessions/${sessionId}/name`, sessionName, {
    headers: {
      'Content-Type': 'application/json'
    }
  }),
  delete: (sessionId) => apiClient.delete(`/sessions/${sessionId}`)
}

// 消息相关 API
export const messageAPI = {
  send: (sessionId, messageData) => apiClient.post(`/sessions/${sessionId}/chat`, messageData),
  execute: (sessionId, messageData) => apiClient.post(`/sessions/${sessionId}/execute`, messageData)
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