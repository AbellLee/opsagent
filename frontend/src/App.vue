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
            @collapse="handleCollapse"
            @expand="handleExpand"
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
import { ref, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from './stores/user'
import { debounce } from './utils'
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

// 监听路由变化以更新活动菜单项
watch(
  () => route.name,
  (newName) => {
    // 只有在认证路由中才更新活动菜单项
    if (['chat', 'tools', 'approvals', 'users'].includes(newName)) {
      activeKey.value = newName
    }
  },
  { immediate: true }
)

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

// 使用防抖处理菜单选择
const handleMenuSelect = debounce((key) => {
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
}, 300)

// 登出处理
const handleLogout = debounce(() => {
  userStore.logout()
  router.push('/login')
}, 300)

// 处理侧边栏折叠和展开事件
const handleCollapse = debounce(() => {
  collapsed.value = true
}, 100)

const handleExpand = debounce(() => {
  collapsed.value = false
}, 100)
</script>

<style>
#app {
  height: 100%;
}

/* 禁用过渡动画以减少ResizeObserver错误 */
*, *::before, *::after {
  transition: none !important;
  animation: none !important;
}

/* 特别针对Naive UI组件 */
.n-layout, .n-layout-sider, .n-layout-content, .n-card, .n-menu {
  transition: none !important;
}
</style>