import { defineStore } from 'pinia'

export const useAgentStore = defineStore('agent', {
  state: () => ({
    agentInfo: {
      name: '',
      description: '',
      tools: []
    },
    loading: false
  }),
  
  actions: {
    setAgentInfo(info) {
      this.agentInfo = {
        name: info.name || '',
        description: info.description || '',
        tools: info.tools || []
      }
    },
    
    setLoading(loading) {
      this.loading = loading
    },
    
    async fetchAgentInfo() {
      // 模拟获取Agent信息
      this.setLoading(true)
      try {
        // 这里应该调用实际的API获取Agent信息
        // 暂时使用模拟数据
        this.setAgentInfo({
          name: 'OpsAgent',
          description: '智能运维助手',
          tools: [
            { 
              name: '服务器监控', 
              description: '监控服务器状态和性能指标',
              examples: ['查看服务器CPU使用率', '监控内存使用情况']
            },
            { 
              name: '日志分析', 
              description: '分析系统日志以发现问题',
              examples: ['分析最近的错误日志', '查找登录失败的记录']
            },
            { 
              name: '自动化部署', 
              description: '自动部署应用程序',
              examples: ['部署最新版本的应用', '回滚到上一个版本']
            }
          ]
        })
      } catch (error) {
        console.error('获取Agent信息失败:', error)
      } finally {
        this.setLoading(false)
      }
    }
  }
})