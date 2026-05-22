<template>
  <el-container class="app-layout" :class="{ dark: isDark, 'is-mobile': isMobile }">
    <!-- Mobile overlay -->
    <div v-if="isMobile && mobileMenuOpen" class="mobile-overlay" @click="mobileMenuOpen = false" />

    <el-aside
      :width="asideWidth"
      class="app-aside"
      :class="{ 'mobile-open': isMobile && mobileMenuOpen }"
    >
      <div class="logo">
        <div class="logo-icon">S</div>
        <span v-if="!asideCollapsed" class="logo-text">SubLedger</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        :collapse="asideCollapsed && !isMobile"
        background-color="transparent"
        text-color="rgba(255,255,255,.65)"
        active-text-color="#fff"
        router
        @select="onMenuSelect"
      >
        <el-menu-item index="/dashboard">
          <el-icon><Monitor /></el-icon>
          <span>{{ zhCN.nav.dashboard }}</span>
        </el-menu-item>
        <el-menu-item index="/subscriptions">
          <el-icon><List /></el-icon>
          <span>{{ zhCN.nav.subscriptions }}</span>
        </el-menu-item>
        <el-menu-item index="/payments">
          <el-icon><Wallet /></el-icon>
          <span>{{ zhCN.nav.payments }}</span>
        </el-menu-item>
        <el-menu-item index="/analytics">
          <el-icon><TrendCharts /></el-icon>
          <span>{{ zhCN.nav.analytics }}</span>
        </el-menu-item>
        <el-menu-item index="/annual-report">
          <el-icon><DataLine /></el-icon>
          <span>{{ zhCN.nav.annualReport }}</span>
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
        <el-button
          :icon="isMobile ? (mobileMenuOpen ? Fold : Expand) : (isCollapsed ? Expand : Fold)"
          text
          @click="toggleSidebar"
        />
        <div class="header-right">
          <el-button :icon="Search" text @click="showSearch = true" />
          <el-button :icon="isDark ? Sunny : Moon" text @click="toggleTheme" />
          <span v-if="!isMobile" class="username">{{ authStore.username }}</span>
          <el-button text @click="handleLogout">{{ zhCN.auth.logout }}</el-button>
        </div>
      </el-header>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
    <GlobalSearch v-model:visible="showSearch" />
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Monitor, List, Bell, Setting, Calendar, Expand, Fold, Sunny, Moon, Wallet, TrendCharts, Search, DataLine } from '@element-plus/icons-vue'
import { useAuthStore } from '../../stores/auth'
import { zhCN } from '../../locales/zh-CN'
import api from '../../composables/useApi'
import { getUnreadCount } from '../../api/notifications'
import { initBrowserNotifications } from '../../composables/useBrowserNotify'
import GlobalSearch from '../GlobalSearch.vue'

const isCollapsed = ref(false)
const isDark = ref(false)
const isMobile = ref(false)
const mobileMenuOpen = ref(false)
const unreadCount = ref(0)
const showSearch = ref(false)
const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const activeMenu = computed(() => route.path)
const asideCollapsed = computed(() => isMobile.value ? false : isCollapsed.value)
const asideWidth = computed(() => {
  if (isMobile.value) return mobileMenuOpen.value ? '220px' : '0px'
  return isCollapsed.value ? '64px' : '220px'
})

function toggleSidebar() {
  if (isMobile.value) {
    mobileMenuOpen.value = !mobileMenuOpen.value
  } else {
    isCollapsed.value = !isCollapsed.value
  }
}

function onMenuSelect() {
  if (isMobile.value) mobileMenuOpen.value = false
}

function checkMobile() {
  isMobile.value = window.innerWidth < 768
  if (!isMobile.value) mobileMenuOpen.value = false
}

let pollTimer: ReturnType<typeof setInterval> | null = null

async function fetchUnreadCount() {
  try {
    const res = await getUnreadCount()
    unreadCount.value = res.data.count
  } catch {}
}

onMounted(async () => {
  authStore.checkAuth()
  checkMobile()
  const saved = localStorage.getItem('subledger_theme')
  if (saved === 'dark') {
    isDark.value = true
    document.documentElement.classList.add('dark')
  }
  fetchUnreadCount()
  pollTimer = setInterval(fetchUnreadCount, 60000)
  initBrowserNotifications()
  window.addEventListener('resize', checkMobile)
})

function handleKeydown(e: KeyboardEvent) {
  if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
    e.preventDefault()
    showSearch.value = true
  }
}

onMounted(() => window.addEventListener('keydown', handleKeydown))
onBeforeUnmount(() => {
  if (pollTimer) clearInterval(pollTimer)
  window.removeEventListener('keydown', handleKeydown)
  window.removeEventListener('resize', checkMobile)
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
  background: linear-gradient(180deg, #2e1065 0%, #3730a3 50%, #4338ca 100%);
  transition: width .3s ease;
  overflow: hidden;
  box-shadow: 2px 0 12px rgba(0,0,0,.12);
}
.logo {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 0 16px;
  position: relative;
}
.logo-icon {
  width: 38px;
  height: 38px;
  background: linear-gradient(135deg, #818cf8, #6366f1);
  color: #fff;
  font-size: 18px;
  font-weight: 800;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 0 16px rgba(99,102,241,.4);
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
  border-bottom: 1px solid rgba(0,0,0,.06);
  box-shadow: 0 1px 3px rgba(0,0,0,.03);
  background: var(--surface, #fff);
  transition: background-color .3s, border-color .3s;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}
.username {
  color: var(--text-secondary, #64748b);
  font-size: 14px;
  font-weight: 500;
}
.el-menu {
  border-right: none;
}
.el-menu-item {
  margin: 2px 8px;
  border-radius: 10px;
  border-left: 3px solid transparent;
  transition: all .2s ease;
}
.el-menu-item:hover {
  background: rgba(255,255,255,.06) !important;
  border-left-color: rgba(129,140,248,.3);
}
.el-menu-item.is-active {
  background: rgba(99,102,241,.15) !important;
  border-radius: 10px;
  margin: 2px 8px;
  border-left: 3px solid #818cf8;
}
.notification-badge :deep(.el-badge__content) {
  top: -2px;
  right: -8px;
}
.el-main {
  padding: 24px;
  background: var(--bg, #f8fafc);
  transition: background-color .3s;
}

/* Mobile */
.mobile-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,.45);
  z-index: 99;
  transition: opacity .3s;
}
.is-mobile .app-aside {
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  z-index: 100;
  width: 0;
  overflow: hidden;
}
.is-mobile .app-aside.mobile-open {
  width: 220px;
}
.is-mobile .el-main {
  padding: 16px;
}

/* Dark */
.dark .app-header {
  border-bottom-color: rgba(255,255,255,.06);
  background: var(--surface, #151c2c);
}
.dark .username { color: #cbd5e1; }
.dark .el-main { background: var(--bg, #0a0e1a); color: #e2e8f0; }
</style>
