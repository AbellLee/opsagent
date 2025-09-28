import { defineStore } from 'pinia'

export const useSessionStore = defineStore('session', {
  state: () => ({
    sessions: [],
    sessionId: null,
    messages: []
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
    
    resetSession() {
      this.sessions = []
      this.sessionId = null
      this.messages = []
    }
  }
})