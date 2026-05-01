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
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'
import { zhCN } from '../locales/zh-CN'

const password = ref('')
const loading = ref(false)
const router = useRouter()
const authStore = useAuthStore()

async function handleLogin() {
  if (!password.value) return
  loading.value = true
  try {
    await authStore.login(password.value)
    ElMessage.success(zhCN.auth.loginSuccess)
    router.push('/dashboard')
  } catch {
    ElMessage.error(zhCN.auth.loginFailed)
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