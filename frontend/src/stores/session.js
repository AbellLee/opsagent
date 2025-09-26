import { defineStore } from 'pinia'

export const useSessionStore = defineStore('session', {
  state: () => ({
    sessionId: null,
    messages: []
  }),
  
  actions: {
    setSessionId(sessionId) {
      this.sessionId = sessionId
    },
    
    addMessage(message) {
      this.messages.push(message)
    },
    
    clearMessages() {
      this.messages = []
    },
    
    resetSession() {
      this.sessionId = null
      this.messages = []
    }
  }
})