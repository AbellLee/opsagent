import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../views/LoginView.vue'
import RegisterView from '../views/RegisterView.vue'
import ChatView from '../views/ChatView.vue'

const routes = [
  {
    path: '/',
    redirect: '/chat'
  },
  {
    path: '/login',
    name: 'Login',
    component: LoginView,
    meta: { skipAuth: true }  // 跳过认证检查
  },
  {
    path: '/register',
    name: 'Register',
    component: RegisterView,
    meta: { skipAuth: true }  // 跳过认证检查
  },
  {
    path: '/chat',
    name: 'Chat',
    component: ChatView,
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  try {
    console.log('路由守卫:', {
      to: to.path,
      from: from.path,
      meta: to.meta
    })

    // 如果路由标记为跳过认证检查，直接通过
    if (to.meta.skipAuth) {
      console.log('跳过认证检查，直接访问')
      next()
      return
    }

    // 导入用户store（延迟导入避免循环依赖）
    const { useUserStore } = require('../stores/user')
    const userStore = useUserStore()

    // 确保用户状态已初始化
    userStore.initializeFromStorage()
    const isAuthenticated = userStore.isAuthenticated

    console.log('认证状态:', isAuthenticated)

    if (to.meta.requiresAuth && !isAuthenticated) {
      console.log('需要认证但未登录，重定向到登录页')
      next('/login')
    } else if ((to.path === '/login' || to.path === '/register') && isAuthenticated) {
      console.log('已登录用户访问登录/注册页，重定向到聊天页')
      next('/chat')
    } else {
      console.log('正常访问')
      next()
    }
  } catch (error) {
    console.error('路由守卫错误:', error)
    // 发生错误时，允许访问登录页面
    if (to.path === '/login' || to.path === '/register') {
      next()
    } else {
      next('/login')
    }
  }
})

export default router