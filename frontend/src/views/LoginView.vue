<template>
  <div class="login-container">
    <el-card class="login-card">
      <h2>{{ zhCN.auth.title }}</h2>
      <el-form @submit.prevent="handleLogin">
        <el-form-item>
          <el-input
            v-model="password"
            type="password"
            :placeholder="zhCN.auth.passwordRequired"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" style="width: 100%" @click="handleLogin">
            {{ zhCN.auth.login }}
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../composables/useApi'
import { zhCN } from '../locales/zh-CN'

const password = ref('')
const loading = ref(false)

async function handleLogin() {
  if (!password.value) return
  loading.value = true
  try {
    await api.post('/auth/login', { password: password.value }).then((res) => {
      localStorage.setItem('subledger_token', res.data.token)
    })
    ElMessage.success(zhCN.auth.loginSuccess)
    // Use direct window.location to ensure full page reload with cookies
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
  background: #f0f2f5;
}
.login-card {
  width: 380px;
}
.login-card h2 {
  text-align: center;
  margin-bottom: 24px;
  color: #303133;
}
</style>