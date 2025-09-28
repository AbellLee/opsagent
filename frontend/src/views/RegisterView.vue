<template>
  <div class="register-container">
    <n-card title="用户注册" style="width: 400px; max-width: 90vw;">
      <n-form ref="formRef" :model="formValue" :rules="rules" label-placement="left">
        <n-form-item label="用户名" path="username">
          <n-input 
            v-model:value="formValue.username" 
            placeholder="请输入用户名"
            @keydown.enter="handleRegister"
          />
        </n-form-item>
        <n-form-item label="邮箱" path="email">
          <n-input 
            v-model:value="formValue.email" 
            placeholder="请输入邮箱"
            @keydown.enter="handleRegister"
          />
        </n-form-item>
        <n-form-item label="密码" path="password">
          <n-input 
            v-model:value="formValue.password" 
            type="password"
            placeholder="请输入密码"
            @keydown.enter="handleRegister"
          />
        </n-form-item>
        <n-form-item label="确认密码" path="confirmPassword">
          <n-input 
            v-model:value="formValue.confirmPassword" 
            type="password"
            placeholder="请再次输入密码"
            @keydown.enter="handleRegister"
          />
        </n-form-item>
        <div class="form-footer">
          <n-button 
            type="primary" 
            @click="handleRegister" 
            :loading="loading"
            block
          >
            注册
          </n-button>
          <n-button 
            @click="router.push('/login')" 
            block 
            style="margin-top: 16px"
          >
            已有账号？去登录
          </n-button>
        </div>
      </n-form>
    </n-card>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
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
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})

const rules = {
  username: [
    {
      required: true,
      message: '请输入用户名',
      trigger: 'blur'
    },
    {
      min: 3,
      message: '用户名至少3位',
      trigger: 'blur'
    }
  ],
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
  ],
  confirmPassword: [
    {
      required: true,
      message: '请确认密码',
      trigger: 'blur'
    },
    {
      validator: (rule, value) => value === formValue.value.password,
      message: '两次输入的密码不一致',
      trigger: 'blur'
    }
  ]
}

// 监听密码变化，重新验证确认密码
watch(() => formValue.value.password, () => {
  if (formValue.value.confirmPassword) {
    formRef.value?.validateField('confirmPassword')
  }
})

const handleRegister = (e) => {
  e.preventDefault()
  
  formRef.value?.validate(async (errors) => {
    if (!errors) {
      loading.value = true
      try {
        const userData = {
          username: formValue.value.username,
          email: formValue.value.email,
          password: formValue.value.password
        }
        
        const result = await userStore.register(userData)
        if (result.success) {
          message.success('注册成功')
          router.push('/login')
        } else {
          message.error(result.error || '注册失败')
        }
      } catch (error) {
        message.error('注册过程中发生错误')
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
.register-container {
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