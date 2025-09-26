import axios from 'axios'

// 创建axios实例
const apiClient = axios.create({
  baseURL: 'http://localhost:8000/api',
  // 移除timeout配置，避免10秒超时限制
})

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    // 添加认证头
    const token = localStorage.getItem('authToken') || localStorage.getItem('token')
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
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
    return response
  },
  (error) => {
    // 处理错误响应
    if (error.response?.status === 401) {
      // 未授权，清空本地存储的认证信息
      localStorage.removeItem('authToken')
      localStorage.removeItem('token')
      localStorage.removeItem('userProfile')
      // 如果在浏览器环境中，重定向到登录页
      if (typeof window !== 'undefined') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

/**
 * 用户相关API
 */
export const userAPI = {
  // 用户登录
  login: async (data) => {
    const response = await apiClient.post('/users/login', data)
    return response.data
  },

  // 用户注册
  register: async (data) => {
    const response = await apiClient.post('/users', data)
    return response.data
  },

  // 获取用户信息
  getUserInfo: async (userId) => {
    const response = await apiClient.get(`/users/${userId}`)
    return response.data
  }
}

/**
 * 会话相关API
 */
export const sessionAPI = {
  // 创建会话
  create: async (data) => {
    const response = await apiClient.post('/sessions', data)
    return response.data
  },

  // 获取会话列表
  list: async () => {
    const response = await apiClient.get('/sessions')
    return response.data
  },

  // 删除会话
  delete: async (sessionId) => {
    const response = await apiClient.delete(`/sessions/${sessionId}`)
    return response.data
  },

  // 发送消息
  sendMessage: async (sessionId, data) => {
    const response = await apiClient.post(`/sessions/${sessionId}/chat`, data)
    return response.data
  }
}

/**
 * 工具相关API
 */
export const toolAPI = {
  // 获取工具列表
  list: async () => {
    const response = await apiClient.get('/tools')
    return response.data
  },

  // 获取工具详情
  get: async (toolId) => {
    const response = await apiClient.get(`/tools/${toolId}`)
    return response.data
  }
}

/**
 * 审批相关API
 */
export const approvalAPI = {
  // 获取审批列表
  list: async () => {
    const response = await apiClient.get('/approvals')
    return response.data
  },

  // 批准工具执行
  approve: async (approvalId) => {
    const response = await apiClient.post(`/approvals/${approvalId}/approve`)
    return response.data
  },

  // 拒绝工具执行
  reject: async (approvalId) => {
    const response = await apiClient.post(`/approvals/${approvalId}/reject`)
    return response.data
  }
}

// 默认导出apiClient以供直接使用
export default apiClient