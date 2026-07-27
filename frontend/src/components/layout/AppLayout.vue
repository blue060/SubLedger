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
        <div class="logo-icon">SL</div>
        <div v-if="!asideCollapsed" class="logo-copy">
          <span class="logo-text">SubLedger</span>
          <span class="logo-caption">订阅账本</span>
        </div>
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
        <div v-if="!asideCollapsed" class="nav-section-label">概览</div>
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
        <div v-if="!asideCollapsed" class="nav-section-label">洞察</div>
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
        <div v-if="!asideCollapsed" class="nav-section-label">系统</div>
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
      <div v-if="!asideCollapsed" class="aside-footer">
        <span class="status-dot"></span>
        <span>服务运行中</span>
      </div>
    </el-aside>
    <el-container>
      <el-header class="app-header">
        <div class="header-left">
          <el-button
            class="sidebar-trigger"
            :icon="isMobile ? (mobileMenuOpen ? Fold : Expand) : (isCollapsed ? Expand : Fold)"
            text
            @click="toggleSidebar"
          />
          <div class="page-context">
            <strong>{{ pageTitle }}</strong>
            <span v-if="!isMobile">{{ pageDescription }}</span>
          </div>
        </div>
        <div class="header-right">
          <el-tooltip content="全局搜索 Ctrl/⌘ K" placement="bottom">
            <el-button class="header-action" :icon="Search" circle @click="showSearch = true" />
          </el-tooltip>
          <el-tooltip :content="isDark ? '切换浅色模式' : '切换深色模式'" placement="bottom">
            <el-button class="header-action" :icon="isDark ? Sunny : Moon" circle @click="toggleTheme" />
          </el-tooltip>
          <el-dropdown trigger="click">
            <button class="account-button">
              <span class="account-avatar">{{ authStore.username?.slice(0, 1).toUpperCase() || 'A' }}</span>
              <span v-if="!isMobile" class="username">{{ authStore.username }}</span>
              <el-icon v-if="!isMobile" class="account-arrow"><ArrowDown /></el-icon>
            </button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="router.push('/settings')">账户与设置</el-dropdown-item>
                <el-dropdown-item divided @click="handleLogout">{{ zhCN.auth.logout }}</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      <el-main class="page-stage">
        <router-view v-slot="{ Component }">
          <transition name="page-fade" mode="out-in">
            <keep-alive :max="8">
              <component :is="Component" :key="String(route.name)" />
            </keep-alive>
          </transition>
        </router-view>
      </el-main>
    </el-container>
    <GlobalSearch v-model:visible="showSearch" />
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Monitor, List, Bell, Setting, Calendar, Expand, Fold, Sunny, Moon, Wallet, TrendCharts, Search, DataLine, ArrowDown } from '@element-plus/icons-vue'
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
const pageTitle = computed(() => String(route.meta.title || 'SubLedger'))
const pageDescription = computed(() => String(route.meta.description || ''))
const asideCollapsed = computed(() => isMobile.value ? false : isCollapsed.value)
const asideWidth = computed(() => {
  if (isMobile.value) return mobileMenuOpen.value ? '248px' : '0px'
  return isCollapsed.value ? '72px' : '248px'
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
.app-layout {
  min-height: 100vh;
  background: var(--bg);
}
.app-aside {
  position: relative;
  display: flex;
  flex-direction: column;
  background:
    radial-gradient(circle at 20% 0%, rgba(99, 102, 241, .24), transparent 30%),
    linear-gradient(180deg, #111827 0%, #0f172a 100%);
  transition: width .24s ease;
  overflow: hidden;
  box-shadow: 8px 0 32px rgba(15, 23, 42, .08);
}
.logo {
  height: 76px;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 12px;
  padding: 0 17px;
  flex-shrink: 0;
}
.logo-icon {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #818cf8, #4f46e5);
  color: #fff;
  font-size: 13px;
  font-weight: 900;
  letter-spacing: -.5px;
  border-radius: 13px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 8px 24px rgba(79, 70, 229, .35), inset 0 1px 0 rgba(255, 255, 255, .25);
}
.logo-copy {
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.logo-text {
  font-size: 18px;
  line-height: 1.2;
  font-weight: 800;
  color: #fff;
  letter-spacing: -.4px;
}
.logo-caption {
  margin-top: 3px;
  color: #64748b;
  font-size: 11px;
  letter-spacing: 1.5px;
}
.el-menu {
  flex: 1;
  border-right: none;
  padding-bottom: 12px;
  overflow-y: auto;
  overflow-x: hidden;
}
.nav-section-label {
  padding: 18px 24px 7px;
  color: #64748b;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 1.5px;
}
.el-menu-item {
  height: 44px;
  line-height: 44px;
  margin: 3px 10px;
  padding: 0 14px !important;
  border-radius: 11px;
  transition: color .16s ease, background-color .16s ease, transform .16s ease;
}
.el-menu--collapse .el-menu-item {
  justify-content: center;
  margin-left: 9px;
  margin-right: 9px;
  padding: 0 !important;
}
.el-menu-item:hover {
  color: #e2e8f0 !important;
  background: rgba(255, 255, 255, .055) !important;
}
.el-menu-item.is-active {
  color: #fff !important;
  background: linear-gradient(135deg, rgba(99, 102, 241, .95), rgba(79, 70, 229, .9)) !important;
  box-shadow: 0 7px 20px rgba(79, 70, 229, .24);
}
.notification-badge :deep(.el-badge__content) {
  top: -2px;
  right: -8px;
}
.aside-footer {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 12px 16px 18px;
  padding: 11px 12px;
  color: #94a3b8;
  font-size: 12px;
  background: rgba(255, 255, 255, .035);
  border: 1px solid rgba(255, 255, 255, .05);
  border-radius: 10px;
}
.status-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #34d399;
  box-shadow: 0 0 0 4px rgba(52, 211, 153, .1);
}
.app-header {
  height: 72px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  border-bottom: 1px solid var(--border);
  background: color-mix(in srgb, var(--surface) 92%, transparent);
  backdrop-filter: blur(16px);
  transition: background-color .2s, border-color .2s;
}
.header-left {
  display: flex;
  align-items: center;
  min-width: 0;
  gap: 12px;
}
.sidebar-trigger {
  width: 38px;
  height: 38px;
  color: var(--text-secondary);
}
.page-context {
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.page-context strong {
  color: var(--text-primary);
  font-size: 16px;
  line-height: 1.3;
}
.page-context span {
  margin-top: 2px;
  color: var(--text-muted);
  font-size: 12px;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 9px;
}
.header-action {
  width: 38px;
  height: 38px;
  color: var(--text-secondary);
  background: var(--surface-secondary);
  border-color: transparent;
}
.account-button {
  height: 42px;
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 3px 10px 3px 4px;
  color: var(--text-primary);
  background: transparent;
  border: 1px solid transparent;
  border-radius: 13px;
  cursor: pointer;
  transition: background .16s, border-color .16s;
}
.account-button:hover {
  background: var(--surface-secondary);
  border-color: var(--border);
}
.account-avatar {
  width: 34px;
  height: 34px;
  display: grid;
  place-items: center;
  color: #fff;
  font-size: 13px;
  font-weight: 800;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border-radius: 11px;
}
.username {
  max-width: 110px;
  overflow: hidden;
  color: var(--text-primary);
  font-size: 13px;
  font-weight: 650;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.account-arrow {
  color: var(--text-muted);
  font-size: 11px;
}
.page-stage {
  min-width: 0;
  padding: 26px;
  background: var(--bg);
  transition: background-color .2s;
}
.page-fade-enter-active,
.page-fade-leave-active {
  transition: opacity .14s ease, transform .14s ease;
}
.page-fade-enter-from {
  opacity: 0;
  transform: translateY(5px);
}
.page-fade-leave-to {
  opacity: 0;
}

.mobile-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, .55);
  backdrop-filter: blur(2px);
  z-index: 99;
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
  width: 248px;
}
.is-mobile .page-stage {
  padding: 16px;
}
.is-mobile .app-header {
  height: 64px;
  padding: 0 12px;
}
.is-mobile .header-right {
  gap: 5px;
}
.is-mobile .header-action {
  width: 34px;
  height: 34px;
}
.is-mobile .account-button {
  padding: 2px;
}

@media (max-width: 420px) {
  .page-context strong { font-size: 15px; }
  .header-right > :first-child { display: none; }
}
</style>
