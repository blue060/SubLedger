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
  background: #eef2ff;
  position: relative;
  overflow: hidden;
}
.setup-container::before {
  content: '';
  position: absolute;
  width: 600px;
  height: 600px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(99,102,241,.15), transparent 70%);
  top: -200px;
  left: -100px;
  animation: sfloat 8s ease-in-out infinite;
}
.setup-container::after {
  content: '';
  position: absolute;
  width: 500px;
  height: 500px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(139,92,246,.2), transparent 70%);
  bottom: -150px;
  right: -100px;
  animation: sfloat2 10s ease-in-out infinite;
}
@keyframes sfloat {
  0%, 100% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(40px, 30px) scale(1.1); }
}
@keyframes sfloat2 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(-30px, -20px) scale(1.05); }
}
.setup-card {
  position: relative;
  z-index: 1;
  width: 420px;
  padding: 48px 40px 36px;
  background: rgba(255,255,255,.85);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(255,255,255,.3);
  border-radius: 24px;
  box-shadow: 0 24px 48px rgba(0,0,0,.2);
  text-align: center;
}
html.dark .setup-card {
  background: rgba(21,28,44,.85);
  border-color: rgba(255,255,255,.08);
}
.setup-logo {
  width: 56px;
  height: 56px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: #fff;
  font-size: 28px;
  font-weight: 800;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16px;
  box-shadow: 0 8px 24px rgba(99,102,241,.4);
}
.setup-card h2 {
  margin: 0 0 4px;
  font-size: 26px;
  color: #1e293b;
  text-align: center;
  font-weight: 800;
  letter-spacing: -.5px;
}
.setup-desc {
  color: #94a3b8;
  font-size: 14px;
  margin: 0 0 28px;
}
.setup-btn {
  width: 100%;
  height: 46px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 12px !important;
  background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
  border: none !important;
  transition: all .2s ease;
}
.setup-btn:hover {
  background: linear-gradient(135deg, #818cf8, #a78bfa) !important;
  transform: translateY(-1px);
  box-shadow: 0 8px 20px rgba(99,102,241,.35);
}
</style>