import { defineStore } from 'pinia'
import { userAPI } from '../api'

export const useUserStore = defineStore('user', {
  state: () => ({
    user: null,
    token: localStorage.getItem('token') || null
  }),
  
  getters: {
    isAuthenticated: (state) => !!state.token
  },
  
  actions: {
    initializeFromStorage() {
      const token = localStorage.getItem('token')
      const user = localStorage.getItem('user')
      
      if (token && user) {
        this.token = token
        this.user = JSON.parse(user)
      }
    },
    
    async login(credentials) {
      try {
        const response = await userAPI.login(credentials)
        const { token, user } = response
        
        this.token = token
        this.user = user
        
        localStorage.setItem('token', token)
        localStorage.setItem('user', JSON.stringify(user))
        
        return { success: true }
      } catch (error) {
        return { success: false, error: error.message }
      }
    },
    
    async register(userData) {
      try {
        const response = await userAPI.register(userData)
        return { success: true, data: response }
      } catch (error) {
        return { success: false, error: error.message }
      }
    },
    
    logout() {
      this.user = null
      this.token = null
      
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    }
  }
})