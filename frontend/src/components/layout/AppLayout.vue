<template>
  <el-container class="app-layout" :class="{ dark: isDark }">
    <el-aside :width="isCollapsed ? '64px' : '220px'" class="app-aside">
      <div class="logo">
        <div class="logo-icon">S</div>
        <span v-if="!isCollapsed" class="logo-text">SubLedger</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapsed"
        background-color="transparent"
        text-color="rgba(255,255,255,.65)"
        active-text-color="#fff"
        router
      >
        <el-menu-item index="/dashboard">
          <el-icon><Monitor /></el-icon>
          <span>{{ zhCN.nav.dashboard }}</span>
        </el-menu-item>
        <el-menu-item index="/subscriptions">
          <el-icon><List /></el-icon>
          <span>{{ zhCN.nav.subscriptions }}</span>
        </el-menu-item>
        <el-menu-item index="/calendar">
          <el-icon><Calendar /></el-icon>
          <span>{{ zhCN.nav.calendar }}</span>
        </el-menu-item>
        <el-menu-item index="/notifications">
          <el-icon>
            <el-badge :value="unreadCount" :hidden="unreadCount === 0" :max="99" class="notification-badge">
              <Bell />
            </el-badge>
          </el-icon>
          <span>{{ zhCN.nav.notifications }}</span>
        </el-menu-item>
        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <span>{{ zhCN.nav.settings }}</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="app-header">
        <el-button :icon="isCollapsed ? Expand : Fold" text @click="isCollapsed = !isCollapsed" />
        <div class="header-right">
          <el-button :icon="isDark ? Sunny : Moon" text @click="toggleTheme" />
          <span class="username">{{ authStore.username }}</span>
          <el-button text @click="handleLogout">{{ zhCN.auth.logout }}</el-button>
        </div>
      </el-header>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Monitor, List, Bell, Setting, Calendar, Expand, Fold, Sunny, Moon } from '@element-plus/icons-vue'
import { useAuthStore } from '../../stores/auth'
import { zhCN } from '../../locales/zh-CN'
import api from '../../composables/useApi'
import { getUnreadCount } from '../../api/notifications'

const isCollapsed = ref(false)
const isDark = ref(false)
const unreadCount = ref(0)
const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const activeMenu = computed(() => route.path)

let pollTimer: ReturnType<typeof setInterval> | null = null

async function fetchUnreadCount() {
  try {
    const res = await getUnreadCount()
    unreadCount.value = res.data.count
  } catch {}
}

onMounted(async () => {
  authStore.checkAuth()
  const saved = localStorage.getItem('subledger_theme')
  if (saved === 'dark') {
    isDark.value = true
    document.documentElement.classList.add('dark')
  }
  fetchUnreadCount()
  pollTimer = setInterval(fetchUnreadCount, 60000)
})

onBeforeUnmount(() => {
  if (pollTimer) clearInterval(pollTimer)
})

function toggleTheme() {
  isDark.value = !isDark.value
  document.documentElement.classList.toggle('dark', isDark.value)
  localStorage.setItem('subledger_theme', isDark.value ? 'dark' : 'light')
  api.put('/settings', { theme: isDark.value ? 'dark' : 'light' }).catch(() => {})
}

async function handleLogout() {
  await authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.app-layout { min-height: 100vh; }
.app-aside {
  background: linear-gradient(180deg, #1e1b4b 0%, #312e81 50%, #3730a3 100%);
  transition: width .3s ease;
  overflow: hidden;
  box-shadow: 2px 0 12px rgba(0,0,0,.15);
}
.logo {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 0 16px;
}
.logo-icon {
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, #818cf8, #a78bfa);
  color: #fff;
  font-size: 18px;
  font-weight: 800;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.logo-text {
  font-size: 20px;
  font-weight: 700;
  color: #fff;
  letter-spacing: -.5px;
}
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #f1f5f9;
  box-shadow: 0 1px 3px rgba(0,0,0,.04);
  background: #fff;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}
.username {
  color: #475569;
  font-size: 14px;
  font-weight: 500;
}
.el-menu {
  border-right: none;
}
.el-menu-item.is-active {
  background: rgba(255,255,255,.12) !important;
  border-radius: 8px;
  margin: 2px 8px;
}
.el-menu-item {
  margin: 2px 8px;
  border-radius: 8px;
}
.notification-badge :deep(.el-badge__content) {
  top: -2px;
  right: -8px;
}
.el-main {
  padding: 24px;
  background: var(--bg, #f8fafc);
}

/* Dark */
.dark .app-header {
  border-bottom-color: #1e293b;
  background: #1e293b;
}
.dark .username { color: #cbd5e1; }
.dark .el-main { background: #0f172a; color: #e2e8f0; }
</style>