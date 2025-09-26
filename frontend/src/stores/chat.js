import { defineStore } from 'pinia'

export const useChatStore = defineStore('chat', {
  state: () => ({
    messages: [],
    threadId: null,
    loading: false
  }),
  
  actions: {
    addMessage(role, content, timestamp = new Date().toISOString()) {
      this.messages.push({
        role,
        content,
        timestamp
      })
    },
    
    setMessages(messages) {
      this.messages = messages
    },
    
    clearMessages() {
      this.messages = []
    },
    
    setThreadId(threadId) {
      this.threadId = threadId
    },
    
    setLoading(loading) {
      this.loading = loading
    }
  }
})