import { defineStore } from 'pinia'

export const useUserStore = defineStore('user', {
  state: () => ({
    userProfile: null,
    authToken: null,
    isLoggedIn: false
  }),
  
  getters: {
    isAuthenticated: (state) => state.isLoggedIn && state.userProfile && state.authToken
  },
  
  actions: {
    setUserProfile(profile) {
      this.userProfile = profile
      this.isLoggedIn = !!profile
    },
    
    setAuthToken(token) {
      this.authToken = token
    },
    
    login(profile, token) {
      this.setUserProfile(profile)
      this.setAuthToken(token)
      // 保存到本地存储
      localStorage.setItem('userProfile', JSON.stringify(profile))
      localStorage.setItem('authToken', token)
    },
    
    logout() {
      this.setUserProfile(null)
      this.setAuthToken(null)
      // 清除本地存储
      localStorage.removeItem('userProfile')
      localStorage.removeItem('authToken')
    },
    
    initializeFromStorage() {
      const profileStr = localStorage.getItem('userProfile')
      const token = localStorage.getItem('authToken')
      
      if (profileStr && token) {
        try {
          this.login(JSON.parse(profileStr), token)
        } catch (e) {
          console.error('Failed to initialize user from storage:', e)
          this.logout()
        }
      }
    }
  }
})