<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-logo">S</div>
      <h2>SubLedger</h2>
      <p class="login-subtitle">{{ zhCN.auth.title }}</p>
      <el-form @submit.prevent="handleLogin">
        <el-form-item>
          <el-input
            v-model="username"
            size="large"
            :placeholder="zhCN.auth.usernameRequired"
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="password"
            type="password"
            size="large"
            :placeholder="zhCN.auth.passwordRequired"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" size="large" class="login-btn" @click="handleLogin">
            {{ zhCN.auth.login }}
          </el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../composables/useApi'
import { zhCN } from '../locales/zh-CN'

const username = ref('')
const password = ref('')
const loading = ref(false)

onMounted(async () => {
  try {
    const res = await api.get('/auth/setup-status')
    if (res.data.needs_setup) {
      window.location.href = '/setup'
    }
  } catch {}
})

async function handleLogin() {
  if (!username.value || !password.value) return
  loading.value = true
  try {
    await api.post('/auth/login', { username: username.value, password: password.value }).then((res) => {
      localStorage.setItem('subledger_token', res.data.token)
    })
    ElMessage.success(zhCN.auth.loginSuccess)
    window.location.href = '/dashboard'
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || zhCN.auth.loginFailed)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: #eef2ff;
  position: relative;
  overflow: hidden;
}
.login-container::before {
  content: '';
  position: absolute;
  width: 600px;
  height: 600px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(99,102,241,.15), transparent 70%);
  top: -200px;
  left: -100px;
  animation: float1 8s ease-in-out infinite;
}
.login-container::after {
  content: '';
  position: absolute;
  width: 500px;
  height: 500px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(139,92,246,.1), transparent 70%);
  bottom: -150px;
  right: -100px;
  animation: float2 10s ease-in-out infinite;
}
@keyframes float1 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(40px, 30px) scale(1.1); }
}
@keyframes float2 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(-30px, -20px) scale(1.05); }
}
.login-card {
  position: relative;
  z-index: 1;
  width: 420px;
  padding: 48px 40px 36px;
  background: rgba(255,255,255,.92);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(255,255,255,.5);
  border-radius: 24px;
  box-shadow: 0 16px 40px rgba(99,102,241,.1);
  text-align: center;
}
html.dark .login-card {
  background: rgba(21,28,44,.85);
  border-color: rgba(255,255,255,.08);
}
.login-logo {
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
.login-card h2 {
  margin: 0 0 4px;
  font-size: 26px;
  color: #1e293b;
  text-align: center;
  font-weight: 800;
  letter-spacing: -.5px;
}
.login-subtitle {
  color: #94a3b8;
  font-size: 14px;
  margin: 0 0 28px;
}
.login-btn {
  width: 100%;
  height: 46px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 12px !important;
  background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
  border: none !important;
  transition: all .2s ease;
}
.login-btn:hover {
  background: linear-gradient(135deg, #818cf8, #a78bfa) !important;
  transform: translateY(-1px);
  box-shadow: 0 8px 20px rgba(99,102,241,.35);
}
</style>