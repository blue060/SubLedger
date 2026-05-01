<template>
  <el-container class="app-layout">
    <el-aside :width="isCollapsed ? '64px' : '200px'" class="app-aside">
      <div class="logo">
        <h1 v-if="!isCollapsed">SubLedger</h1>
        <h1 v-else>S</h1>
      </div>
      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapsed"
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409eff"
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
        <el-menu-item index="/notifications">
          <el-icon><Bell /></el-icon>
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
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Monitor, List, Bell, Setting, Expand, Fold } from '@element-plus/icons-vue'
import { useAuthStore } from '../../stores/auth'
import { zhCN } from '../../locales/zh-CN'

const isCollapsed = ref(false)
const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const activeMenu = computed(() => route.path)

onMounted(() => {
  authStore.checkAuth()
})

async function handleLogout() {
  await authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.app-layout {
  min-height: 100vh;
}
.app-aside {
  background: #304156;
  transition: width 0.3s;
  overflow: hidden;
}
.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}
.logo h1 {
  margin: 0;
  font-size: 18px;
}
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #e6e6e6;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}
.username {
  color: #606266;
  font-size: 14px;
}
.el-menu {
  border-right: none;
}
</style>