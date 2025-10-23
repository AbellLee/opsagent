import { defineStore } from 'pinia'

export const useSessionStore = defineStore('session', {
  state: () => ({
    sessions: [],
    sessionId: null,
    messages: [],
    websocket: null // 添加WebSocket引用
  }),
  
  actions: {
    setSessions(sessions) {
      this.sessions = sessions
    },
    
    addSession(session) {
      this.sessions.unshift(session)
    },
    
    removeSession(sessionId) {
      this.sessions = this.sessions.filter(s => s.session_id !== sessionId)
    },
    
    setSessionId(sessionId) {
      this.sessionId = sessionId
    },
    
    setMessages(messages) {
      this.messages = messages
    },
    
    addMessage(message) {
      this.messages.push(message)
      return this.messages.length - 1 // 返回消息索引
    },

    updateMessage(messageIndex, content) {
      if (messageIndex >= 0 && messageIndex < this.messages.length) {
        // 确保Vue能检测到变化，使用响应式更新
        this.messages[messageIndex] = {
          ...this.messages[messageIndex],
          content: content,
          timestamp: new Date().toISOString() // 添加时间戳确保变化
        }
      }
    },
    
    clearMessages() {
      this.messages = []
    },
    
    updateMessageContent(messageId, content) {
      const message = this.messages.find(m => m.id === messageId)
      if (message) {
        message.content = content
      }
    },
    
    // 设置WebSocket连接
    setWebsocket(websocket) {
      this.websocket = websocket
    },
    
    // 移除WebSocket连接
    clearWebsocket() {
      this.websocket = null
    },
    
    resetSession() {
      this.sessions = []
      this.sessionId = null
      this.messages = []
      this.websocket = null
    }
  }
})