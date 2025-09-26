<template>
  <div style="padding: 20px; display: flex; justify-content: center; align-items: center; height: 100%;">
    <n-card style="width: 400px; max-width: 90vw;">
      <n-tabs type="line" animated>
        <n-tab-pane name="register" tab="用户注册">
          <n-form
            :model="registerForm"
            :rules="registerRules"
            ref="registerFormRef"
          >
            <n-form-item label="用户名" path="username">
              <n-input 
                v-model:value="registerForm.username" 
                placeholder="请输入用户名"
              />
            </n-form-item>
            <n-form-item label="邮箱" path="email">
              <n-input 
                v-model:value="registerForm.email" 
                placeholder="请输入邮箱"
              />
            </n-form-item>
            <n-form-item label="密码" path="password">
              <n-input 
                v-model:value="registerForm.password" 
                type="password"
                placeholder="请输入密码"
                show-password-on="click"
              />
            </n-form-item>
            <n-form-item label="确认密码" path="confirmPassword">
              <n-input 
                v-model:value="registerForm.confirmPassword" 
                type="password"
                placeholder="请再次输入密码"
                show-password-on="click"
              />
            </n-form-item>
            <n-form-item>
              <n-button 
                type="primary" 
                @click="handleRegister"
                :loading="registerLoading"
                style="width: 100%"
              >
                注册
              </n-button>
            </n-form-item>
          </n-form>
          
          <div style="text-align: center; margin-top: 20px;">
            <n-text>已有账户？</n-text>
            <n-button text type="primary" @click="router.push('/login')">立即登录</n-button>
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
import axios from 'axios'

const message = useMessage()
const router = useRouter()
const userStore = useUserStore()

// 注册表单
const registerFormRef = ref()
const registerForm = ref({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})

const registerRules = {
  username: {
    required: true,
    message: '请输入用户名',
    trigger: 'blur'
  },
  email: [
    {
      required: true,
      message: '请输入邮箱',
      trigger: 'blur'
    },
    {
      type: 'email',
      message: '请输入正确的邮箱格式',
      trigger: 'blur'
    }
  ],
  password: {
    required: true,
    message: '请输入密码',
    trigger: 'blur'
  },
  confirmPassword: {
    required: true,
    message: '请再次输入密码',
    trigger: 'blur',
    validator: (rule, value) => {
      if (value !== registerForm.value.password) {
        return new Error('两次输入的密码不一致')
      }
      return true
    }
  }
}

// 状态管理
const registerLoading = ref(false)

// 处理注册
const handleRegister = async (e) => {
  e.preventDefault()
  registerLoading.value = true
  
  try {
    await registerFormRef.value.validate()
    
    // 调用后端注册API
    const response = await axios.post('http://localhost:8000/api/users', {
      username: registerForm.value.username,
      email: registerForm.value.email,
      password: registerForm.value.password
    })
    
    userStore.login(response.data, 'placeholder_token_' + Date.now())
    message.success('注册成功')
    router.push('/')
  } catch (error) {
    console.error('注册失败:', error)
    message.error('注册失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    registerLoading.value = false
  }
}
</script>