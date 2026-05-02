<template>
  <div class="setup-container">
    <div class="setup-card">
      <div class="setup-logo">S</div>
      <h2>{{ zhCN.auth.setupTitle }}</h2>
      <p class="setup-desc">{{ zhCN.auth.setupDesc }}</p>
      <el-form @submit.prevent="handleSetup">
        <el-form-item>
          <el-input v-model="username" size="large" :placeholder="zhCN.auth.usernameRequired" />
        </el-form-item>
        <el-form-item>
          <el-input v-model="password" type="password" size="large" :placeholder="zhCN.auth.passwordRequired" show-password />
        </el-form-item>
        <el-form-item>
          <el-input v-model="confirmPassword" type="password" size="large" :placeholder="zhCN.auth.passwordRequired" show-password @keyup.enter="handleSetup" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" size="large" class="setup-btn" @click="handleSetup">
            {{ zhCN.common.confirm }}
          </el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../composables/useApi'
import { zhCN } from '../locales/zh-CN'

const username = ref('')
const password = ref('')
const confirmPassword = ref('')
const loading = ref(false)

async function handleSetup() {
  if (!username.value || !password.value) return
  if (password.value !== confirmPassword.value) {
    ElMessage.error(zhCN.auth.passwordMismatch)
    return
  }
  loading.value = true
  try {
    await api.post('/auth/setup', { username: username.value, password: password.value })
    ElMessage.success(zhCN.auth.setupSuccess)
    setTimeout(() => { window.location.href = '/login' }, 500)
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || zhCN.auth.setupFailed)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.setup-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
.setup-card {
  width: 420px;
  padding: 48px 40px 32px;
  background: rgba(255,255,255,.97);
  border-radius: 20px;
  box-shadow: 0 20px 60px rgba(0,0,0,.15);
  text-align: center;
}
.setup-logo {
  width: 56px;
  height: 56px;
  background: linear-gradient(135deg, #4f46e5, #7c3aed);
  color: #fff;
  font-size: 28px;
  font-weight: 800;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16px;
}
.setup-card h2 {
  margin: 0 0 4px;
  font-size: 24px;
  color: #1e293b;
  text-align: center;
}
.setup-desc {
  color: #94a3b8;
  font-size: 14px;
  margin: 0 0 28px;
}
.setup-btn {
  width: 100%;
  height: 44px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 10px !important;
  background: linear-gradient(135deg, #4f46e5, #7c3aed) !important;
  border: none !important;
}
.setup-btn:hover {
  background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
}
</style>