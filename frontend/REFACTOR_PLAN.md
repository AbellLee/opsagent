# 前端重构设计方案

## 1. 现状分析

### 1.1 当前问题
1. 用户认证系统不完善，没有正确的路由保护机制
2. 页面间跳转逻辑不清晰，未登录用户无法自动跳转到登录页
3. 组件间存在重复代码和错误处理不一致
4. 消息提示系统存在问题，部分组件无法正常使用
5. 状态管理分散，缺乏统一的用户状态管理机制

### 1.2 技术栈
- Vue 3 (Composition API)
- Vue Router 4
- Naive UI 组件库
- Pinia 状态管理

## 2. 重构目标

### 2.1 功能目标
1. 实现完整的用户认证流程（注册、登录、登出）
2. 添加路由保护，未登录用户访问受保护页面时自动跳转到登录页
3. 统一状态管理，使用 Pinia 管理用户状态
4. 完善错误处理和用户提示机制
5. 优化组件结构和代码复用

### 2.2 技术目标
1. 修复现有的编译和运行时错误
2. 建立统一的用户状态管理机制
3. 实现路由守卫保护需要认证的页面
4. 优化组件间通信和数据流

## 3. 详细设计方案

### 3.1 用户状态管理
创建统一的用户状态管理模块：

```javascript
// stores/user.js
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
```

### 3.2 路由保护机制
实现路由守卫来保护需要认证的路由：

```javascript
// router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '../stores/user'

const routes = [
  {
    path: '/',
    name: 'chat',
    component: () => import('../views/ChatView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/tools',
    name: 'tools',
    component: () => import('../views/ToolsView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/approvals',
    name: 'approvals',
    component: () => import('../views/ApprovalsView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/users',
    name: 'users',
    component: () => import('../views/UsersView.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 全局前置守卫
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  
  // 如果路由需要认证但用户未登录，则跳转到登录页
  if (to.meta.requiresAuth && !userStore.isAuthenticated) {
    next('/users')
  } else {
    next()
  }
})

export default router
```

### 3.3 应用入口优化
修改主应用文件以支持状态管理和消息系统：

```javascript
// main.js
import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'

// 创建 Pinia 实例
const pinia = createPinia()

const app = createApp(App)

app.use(pinia)
app.use(router)

app.mount('#app')
```

### 3.4 根组件优化
在根组件中提供全局消息服务和初始化用户状态：

```vue
<!-- App.vue -->
<template>
  <n-config-provider :locale="zhCN" :date-locale="dateZhCN">
    <n-message-provider>
      <n-layout style="height: 100vh">
        <n-layout-header bordered style="padding: 16px; display: flex; align-items: center; justify-content: space-between;">
          <h2 style="margin: 0">OpsAgent 管理平台</h2>
          <n-button v-if="userStore.isAuthenticated" @click="handleLogout" size="small">退出登录</n-button>
        </n-layout-header>
        
        <n-layout has-sider style="height: calc(100vh - 64px)">
          <n-layout-sider
            v-if="userStore.isAuthenticated"
            bordered
            width="240"
            collapse-mode="width"
            :collapsed-width="64"
            :collapsed="collapsed"
            show-trigger
            @collapse="collapsed = true"
            @expand="collapsed = false"
          >
            <n-menu
              v-model:value="activeKey"
              :collapsed="collapsed"
              :collapsed-width="64"
              :collapsed-icon-size="22"
              :options="menuOptions"
              @update:value="handleMenuSelect"
            />
          </n-layout-sider>
          
          <n-layout-content>
            <router-view />
          </n-layout-content>
        </n-layout>
      </n-layout>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from './stores/user'
import { 
  NLayout, 
  NLayoutHeader, 
  NLayoutSider, 
  NLayoutContent, 
  NMenu, 
  NButton,
  NConfigProvider,
  NMessageProvider
} from 'naive-ui'
import { zhCN, dateZhCN } from 'naive-ui'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const activeKey = ref('chat')
const collapsed = ref(false)

// 初始化用户状态
onMounted(() => {
  userStore.initializeFromStorage()
})

// 菜单选项
const menuOptions = [
  {
    label: 'Agent聊天',
    key: 'chat'
  },
  {
    label: '工具管理',
    key: 'tools'
  },
  {
    label: '审批管理',
    key: 'approvals'
  },
  {
    label: '用户管理',
    key: 'users'
  }
]

// 菜单选择处理
const handleMenuSelect = (key) => {
  switch (key) {
    case 'chat':
      router.push('/')
      break
    case 'tools':
      router.push('/tools')
      break
    case 'approvals':
      router.push('/approvals')
      break
    case 'users':
      router.push('/users')
      break
  }
}

// 登出处理
const handleLogout = () => {
  userStore.logout()
  router.push('/users')
}
</script>
```

### 3.5 用户认证组件优化
优化用户管理组件，使用状态管理：

```vue
<!-- views/UsersView.vue -->
<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { useMessage } from 'naive-ui'

const message = useMessage()
const router = useRouter()
const userStore = useUserStore()

// 登录表单
const loginFormRef = ref()
const loginForm = ref({
  username: '',
  password: ''
})

// 注册表单
const registerFormRef = ref()
const registerForm = ref({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})

// 处理登录
const handleLogin = async (e) => {
  e.preventDefault()
  try {
    await loginFormRef.value.validate()
    
    // 调用后端登录API
    const response = await axios.post('http://localhost:8000/api/users/login', {
      username: loginForm.value.username,
      password: loginForm.value.password
    })
    
    // 更新用户状态
    userStore.login(response.data.user, response.data.token)
    message.success('登录成功')
    router.push('/')
  } catch (error) {
    message.error('登录失败: ' + (error.response?.data?.detail || error.message))
  }
}

// 处理注册
const handleRegister = async (e) => {
  e.preventDefault()
  try {
    await registerFormRef.value.validate()
    
    // 调用后端注册API
    const response = await axios.post('http://localhost:8000/api/users', {
      username: registerForm.value.username,
      email: registerForm.value.email,
      password: registerForm.value.password
    })
    
    // 自动登录
    userStore.login(response.data, 'placeholder_token_' + Date.now())
    message.success('注册成功')
    router.push('/')
  } catch (error) {
    message.error('注册失败: ' + (error.response?.data?.detail || error.message))
  }
}
</script>
```

### 3.6 聊天组件优化
优化聊天组件，添加认证检查：

```vue
<!-- views/ChatView.vue -->
<script setup>
import { ref, onMounted } from 'vue'
import { useUserStore } from '../stores/user'
import { useMessage } from 'naive-ui'

const message = useMessage()
const userStore = useUserStore()

// 检查用户是否已登录
onMounted(() => {
  if (!userStore.isAuthenticated) {
    message.warning('请先登录')
    router.push('/users')
  }
})

// 创建会话
const createSession = async () => {
  try {
    if (!userStore.isAuthenticated) {
      message.error('请先登录')
      throw new Error('用户未登录')
    }
    
    // 使用真实的用户ID创建会话
    const response = await axios.post('http://localhost:8000/api/sessions', {
      user_id: userStore.userProfile.user_id
    })
    
    sessionId.value = response.data.session_id
    message.success('会话创建成功')
  } catch (error) {
    message.error('创建会话失败: ' + (error.response?.data?.detail || error.message))
  }
}
</script>
```

## 4. 实施步骤

### 4.1 第一阶段：基础架构搭建
1. 创建用户状态管理模块 (Pinia store)
2. 设置路由守卫和权限控制
3. 修复现有的编译和运行时错误

### 4.2 第二阶段：组件优化
1. 重构根组件 App.vue
2. 优化用户管理组件 UsersView.vue
3. 优化聊天组件 ChatView.vue

### 4.3 第三阶段：集成测试
1. 测试完整的用户认证流程
2. 验证路由保护机制
3. 测试页面间跳转逻辑

## 5. 预期效果

1. **完整的用户认证流程**：用户可以注册、登录和登出
2. **自动路由保护**：未登录用户访问受保护页面时自动跳转到登录页
3. **统一状态管理**：使用 Pinia 统一管理用户状态
4. **错误处理完善**：提供友好的错误提示和处理机制
5. **代码结构优化**：组件间职责清晰，代码复用率提高

## 6. 风险与应对

### 6.1 技术风险
- 现有功能可能受到影响：通过充分测试来降低风险
- 状态管理引入新的复杂性：采用渐进式重构策略

### 6.2 应对措施
- 逐步重构，每次修改后进行测试
- 保留原有功能的备份
- 增加错误处理和边界情况检查