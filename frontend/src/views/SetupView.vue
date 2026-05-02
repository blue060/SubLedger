<template>
  <div class="setup-container">
    <el-card class="setup-card">
      <h2>{{ zhCN.auth.setupTitle }}</h2>
      <p class="setup-desc">{{ zhCN.auth.setupDesc }}</p>
      <el-form @submit.prevent="handleSetup">
        <el-form-item>
          <el-input
            v-model="username"
            :placeholder="zhCN.auth.usernameRequired"
          />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="password"
            type="password"
            :placeholder="zhCN.auth.passwordRequired"
            show-password
          />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="confirmPassword"
            type="password"
            :placeholder="zhCN.auth.passwordRequired"
            show-password
            @keyup.enter="handleSetup"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" style="width: 100%" @click="handleSetup">
            {{ zhCN.common.confirm }}
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
  background: #f0f2f5;
}
.setup-card {
  width: 400px;
}
.setup-card h2 {
  text-align: center;
  margin-bottom: 8px;
  color: #303133;
}
.setup-desc {
  text-align: center;
  color: #909399;
  margin-bottom: 24px;
  font-size: 14px;
}
</style>
