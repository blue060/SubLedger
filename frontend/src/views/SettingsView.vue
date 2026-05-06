<template>
  <div>
    <h2>{{ zhCN.settings.title }}</h2>

    <el-card class="settings-card">
      <template #header>{{ zhCN.settings.changePassword }}</template>
      <el-form :model="passwordForm" label-width="120px" style="max-width: 400px">
        <el-form-item :label="zhCN.auth.oldPassword">
          <el-input v-model="passwordForm.old_password" type="password" show-password />
        </el-form-item>
        <el-form-item :label="zhCN.auth.newPassword">
          <el-input v-model="passwordForm.new_password" type="password" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleChangePassword">{{ zhCN.common.save }}</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="settings-card">
      <template #header>{{ zhCN.settings.preferences }}</template>
      <el-form :model="settingsForm" label-width="120px" style="max-width: 400px">
        <el-form-item :label="zhCN.settings.preferredCurrency">
          <el-select v-model="settingsForm.preferred_currency">
            <el-option label="CNY (¥)" value="CNY" />
            <el-option label="USD ($)" value="USD" />
            <el-option label="EUR (€)" value="EUR" />
            <el-option label="GBP (£)" value="GBP" />
            <el-option label="JPY (¥)" value="JPY" />
          </el-select>
        </el-form-item>
        <el-form-item :label="zhCN.settings.reminderDays">
          <el-input-number v-model="settingsForm.reminder_days" :min="1" :max="30" />
        </el-form-item>
        <el-form-item :label="zhCN.settings.monthlyBudget">
          <el-input-number v-model="settingsForm.monthly_budget" :min="0" :precision="2" :placeholder="zhCN.settings.monthlyBudgetPlaceholder" />
        </el-form-item>
        <el-form-item :label="zhCN.settings.theme">
          <el-radio-group v-model="settingsForm.theme">
            <el-radio value="light">{{ zhCN.settings.themeLight }}</el-radio>
            <el-radio value="dark">{{ zhCN.settings.themeDark }}</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSaveSettings">{{ zhCN.common.save }}</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="settings-card">
      <template #header>{{ zhCN.settings.smtpSection }}</template>
      <el-form :model="settingsForm" label-width="120px" style="max-width: 500px">
        <el-form-item :label="zhCN.settings.smtpHost">
          <el-input v-model="settingsForm.smtp_host" placeholder="smtp.gmail.com" />
        </el-form-item>
        <el-form-item :label="zhCN.settings.smtpPort">
          <el-input-number v-model="settingsForm.smtp_port" :min="1" :max="65535" />
        </el-form-item>
        <el-form-item :label="zhCN.settings.smtpUser">
          <el-input v-model="settingsForm.smtp_user" />
        </el-form-item>
        <el-form-item :label="zhCN.settings.smtpPassword">
          <el-input v-model="settingsForm.smtp_password" type="password" show-password />
        </el-form-item>
        <el-form-item :label="zhCN.settings.smtpTls">
          <el-switch v-model="settingsForm.smtp_tls" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSaveSettings">{{ zhCN.common.save }}</el-button>
          <el-button @click="handleTestEmail">{{ zhCN.settings.testEmail }}</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="settings-card">
      <template #header>{{ zhCN.settings.pushSection }}</template>
      <el-form :model="settingsForm" label-width="120px" style="max-width: 500px">
        <el-form-item :label="zhCN.settings.barkUrl">
          <el-input v-model="settingsForm.bark_url" placeholder="https://api.day.app/yourkey" />
        </el-form-item>
        <el-form-item :label="zhCN.settings.serverchanKey">
          <el-input v-model="settingsForm.serverchan_key" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSaveSettings">{{ zhCN.common.save }}</el-button>
          <el-button @click="handleTestPush">{{ zhCN.settings.testPush }}</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="settings-card">
      <template #header>{{ zhCN.settings.dataSection }}</template>
      <el-button @click="handleExport('csv')">{{ zhCN.settings.exportCsv }}</el-button>
      <el-button @click="handleExport('json')">{{ zhCN.settings.exportJson }}</el-button>
      <el-upload :before-upload="handleImport" :show-file-list="false" accept=".csv">
        <el-button type="primary" style="margin-left: 12px">{{ zhCN.settings.importData }}</el-button>
      </el-upload>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getSettings, updateSettings, changePassword, testEmail, testPush } from '../api/settings'
import { exportData, importData } from '../api/data'
import { zhCN } from '../locales/zh-CN'

const passwordForm = reactive({ old_password: '', new_password: '' })
const settingsForm = reactive({
  preferred_currency: 'CNY',
  reminder_days: 7,
  monthly_budget: null as number | null,
  theme: 'light',
  smtp_host: null as string | null,
  smtp_port: 465,
  smtp_user: null as string | null,
  smtp_password: null as string | null,
  smtp_tls: true,
  bark_url: null as string | null,
  serverchan_key: null as string | null,
})

onMounted(async () => {
  const res = await getSettings()
  Object.assign(settingsForm, res.data)
  settingsForm.smtp_password = null
})

async function handleSaveSettings() {
  await updateSettings(settingsForm)
  ElMessage.success(zhCN.common.success)
}

async function handleChangePassword() {
  await changePassword(passwordForm.old_password, passwordForm.new_password)
  ElMessage.success(zhCN.settings.passwordChanged)
  passwordForm.old_password = ''
  passwordForm.new_password = ''
}

async function handleTestEmail() {
  try {
    await testEmail()
    ElMessage.success(zhCN.settings.testEmailSent)
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || zhCN.settings.sendFailed)
  }
}

async function handleTestPush() {
  try {
    await testPush()
    ElMessage.success(zhCN.settings.testPushSent)
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || zhCN.settings.sendFailed)
  }
}

async function handleExport(format: string) {
  const res = await exportData(format)
  const url = window.URL.createObjectURL(new Blob([res.data]))
  const link = document.createElement('a')
  link.href = url
  link.download = `subscriptions.${format}`
  link.click()
  window.URL.revokeObjectURL(url)
}

async function handleImport(file: File) {
  try {
    const res = await importData(file)
    ElMessage.success(
      zhCN.settings.importResult
        .replace('{imported}', res.data.imported)
        .replace('{skipped}', res.data.skipped)
    )
  } catch {
    ElMessage.error(zhCN.common.error)
  }
  return false
}
</script>

<style scoped>
.settings-card {
  margin-bottom: 16px;
}
</style>