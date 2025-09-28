<template>
  <div class="login-container">
    <n-card title="用户登录" style="width: 400px; max-width: 90vw;">
      <n-form ref="formRef" :model="formValue" :rules="rules" label-placement="left">
        <n-form-item label="邮箱" path="email">
          <n-input 
            v-model:value="formValue.email" 
            placeholder="请输入邮箱"
            @keydown.enter="handleLogin"
          />
        </n-form-item>
        <n-form-item label="密码" path="password">
          <n-input 
            v-model:value="formValue.password" 
            type="password"
            placeholder="请输入密码"
            @keydown.enter="handleLogin"
          />
        </n-form-item>
        <div class="form-footer">
          <n-button 
            type="primary" 
            @click="handleLogin" 
            :loading="loading"
            block
          >
            登录
          </n-button>
          <n-button 
            @click="router.push('/register')" 
            block 
            style="margin-top: 16px"
          >
            注册账号
          </n-button>
        </div>
      </n-form>
    </n-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { createDiscreteApi } from 'naive-ui'
import { 
  NCard, 
  NForm, 
  NFormItem, 
  NInput, 
  NButton 
} from 'naive-ui'

const router = useRouter()
const userStore = useUserStore()
const { message } = createDiscreteApi(['message'])

const formRef = ref(null)
const loading = ref(false)

const formValue = ref({
  email: '',
  password: ''
})

const rules = {
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
  password: [
    {
      required: true,
      message: '请输入密码',
      trigger: 'blur'
    },
    {
      min: 6,
      message: '密码至少6位',
      trigger: 'blur'
    }
  ]
}

const handleLogin = (e) => {
  e.preventDefault()
  
  formRef.value?.validate(async (errors) => {
    if (!errors) {
      loading.value = true
      try {
        const result = await userStore.login(formValue.value)
        if (result.success) {
          message.success('登录成功')

          // 登录成功后，等待一小段时间让状态更新，然后跳转
          setTimeout(() => {
            router.push('/chat')

            // 跳转后再次尝试刷新会话列表
            setTimeout(() => {
              if (window.refreshSessions) {
                console.log('登录成功后刷新会话列表')
                window.refreshSessions()
              }
            }, 100)
          }, 100)
        } else {
          message.error(result.error || '登录失败')
        }
      } catch (error) {
        message.error('登录过程中发生错误')
      } finally {
        loading.value = false
      }
    } else {
      message.error('请检查输入信息')
    }
  })
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  min-height: 400px;
}

.form-footer {
  margin-top: 24px;
}
</style>