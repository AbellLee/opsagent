<template>
  <div style="padding: 20px; display: flex; justify-content: center; align-items: center; height: 100%;">
    <n-card style="width: 400px; max-width: 90vw;">
      <n-tabs type="line" animated>
        <n-tab-pane name="login" tab="用户登录">
          <n-form
            :model="loginForm"
            :rules="loginRules"
            ref="loginFormRef"
          >
            <n-form-item label="用户名/邮箱" path="username">
              <n-input 
                v-model:value="loginForm.username" 
                placeholder="请输入用户名或邮箱"
              />
            </n-form-item>
            <n-form-item label="密码" path="password">
              <n-input 
                v-model:value="loginForm.password" 
                type="password"
                placeholder="请输入密码"
                show-password-on="click"
              />
            </n-form-item>
            <n-form-item>
              <n-button 
                type="primary" 
                @click="handleLogin"
                :loading="loginLoading"
                style="width: 100%"
              >
                登录
              </n-button>
            </n-form-item>
          </n-form>
          
          <div style="text-align: center; margin-top: 20px;">
            <n-text>还没有账户？</n-text>
            <n-button text type="primary" @click="router.push('/register')">立即注册</n-button>
          </div>
        </n-tab-pane>
      </n-tabs>
    </n-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { 
  NCard, 
  NTabs, 
  NTabPane, 
  NForm, 
  NFormItem, 
  NInput, 
  NButton, 
  NText,
  useMessage
} from 'naive-ui'
import { userAPI } from '../api'

const message = useMessage()
const router = useRouter()
const userStore = useUserStore()

// 登录表单
const loginFormRef = ref()
const loginForm = ref({
  username: '',
  password: ''
})

const loginRules = {
  username: {
    required: true,
    message: '请输入用户名或邮箱',
    trigger: 'blur'
  },
  password: {
    required: true,
    message: '请输入密码',
    trigger: 'blur'
  }
}

// 状态管理
const loginLoading = ref(false)

// 处理登录
const handleLogin = async (e) => {
  e.preventDefault()
  loginLoading.value = true
  
  try {
    await loginFormRef.value.validate()
    
    // 调用后端登录API
    const response = await userAPI.login({
      username: loginForm.value.username,
      email: loginForm.value.username, // 同时传递用户名和邮箱字段
      password: loginForm.value.password
    })
    
    userStore.login(response.user || response, response.token)
    message.success('登录成功')
    router.push('/')
  } catch (error) {
    console.error('登录失败:', error)
    message.error('登录失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    loginLoading.value = false
  }
}
</script>