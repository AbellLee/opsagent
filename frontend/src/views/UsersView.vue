<template>
  <div style="padding: 20px">
    <n-card title="用户管理">
      <n-descriptions label-placement="left" bordered>
        <n-descriptions-item label="用户ID">
          {{ userStore.userProfile.user_id }}
        </n-descriptions-item>
        <n-descriptions-item label="用户名">
          {{ userStore.userProfile.username }}
        </n-descriptions-item>
        <n-descriptions-item label="邮箱">
          {{ userStore.userProfile.email }}
        </n-descriptions-item>
        <n-descriptions-item label="创建时间">
          {{ formatDate(userStore.userProfile.created_at) }}
        </n-descriptions-item>
        <n-descriptions-item label="更新时间">
          {{ formatDate(userStore.userProfile.updated_at) }}
        </n-descriptions-item>
      </n-descriptions>
      
      <n-space style="margin-top: 20px">
        <n-button @click="logout">退出登录</n-button>
      </n-space>
    </n-card>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { 
  NCard, 
  NSpace,
  NButton,
  NDescriptions,
  NDescriptionsItem
} from 'naive-ui'

const router = useRouter()
const userStore = useUserStore()

// 退出登录
const logout = () => {
  userStore.logout()
  router.push('/login')
}

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return ''
  return new Date(dateString).toLocaleString()
}
</script>