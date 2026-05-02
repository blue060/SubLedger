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
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
.login-card {
  width: 400px;
  padding: 48px 40px 32px;
  background: rgba(255,255,255,.97);
  border-radius: 20px;
  box-shadow: 0 20px 60px rgba(0,0,0,.15);
  text-align: center;
}
.login-logo {
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
.login-card h2 {
  margin: 0 0 4px;
  font-size: 24px;
  color: #1e293b;
  text-align: center;
}
.login-subtitle {
  color: #94a3b8;
  font-size: 14px;
  margin: 0 0 28px;
}
.login-btn {
  width: 100%;
  height: 44px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 10px !important;
  background: linear-gradient(135deg, #4f46e5, #7c3aed) !important;
  border: none !important;
}
.login-btn:hover {
  background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
}
</style>