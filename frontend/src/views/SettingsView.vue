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

    <!-- Category Management -->
    <el-card class="settings-card">
      <template #header>{{ zhCN.settings.categorySection }}</template>
      <div class="category-list">
        <div v-for="cat in categories" :key="cat.id" class="category-item">
          <span class="category-color-dot" :style="{ background: cat.color || '#909399' }"></span>
          <span class="category-name">{{ cat.name }}</span>
          <span class="category-actions">
            <el-button size="small" @click="editCategory(cat)">{{ zhCN.common.edit }}</el-button>
            <el-button size="small" type="danger" @click="handleDeleteCategory(cat)">{{ zhCN.common.delete }}</el-button>
          </span>
        </div>
        <el-button type="primary" size="small" @click="addCategory">{{ zhCN.settings.addCategory }}</el-button>
      </div>
    </el-card>

    <el-dialog v-model="categoryDialogVisible" :title="editingCategoryId ? zhCN.common.edit : zhCN.settings.addCategory" width="400px">
      <el-form label-width="80px">
        <el-form-item :label="zhCN.settings.categoryName">
          <el-input v-model="categoryForm.name" />
        </el-form-item>
        <el-form-item :label="zhCN.settings.categoryColor">
          <el-color-picker v-model="categoryForm.color" show-alpha :predefine="predefineColors" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="categoryDialogVisible = false">{{ zhCN.common.cancel }}</el-button>
        <el-button type="primary" @click="handleSaveCategory">{{ zhCN.common.save }}</el-button>
      </template>
    </el-dialog>

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
import { reactive, ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getSettings, updateSettings, changePassword, testEmail, testPush } from '../api/settings'
import { exportData, importData } from '../api/data'
import { useCategoryStore } from '../stores/category'
import { zhCN } from '../locales/zh-CN'

const categoryStore = useCategoryStore()
const categories = computed(() => categoryStore.categories)

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

const categoryDialogVisible = ref(false)
const editingCategoryId = ref<number | null>(null)
const categoryForm = reactive({ name: '', color: '#4f46e5' })
const predefineColors = [
  '#4f46e5', '#7c3aed', '#06b6d4', '#059669', '#d97706',
  '#dc2626', '#ec4899', '#6366f1', '#0ea5e9', '#10b981',
  '#f56c6c', '#e6a23c', '#909399',
]

onMounted(async () => {
  const res = await getSettings()
  Object.assign(settingsForm, res.data)
  settingsForm.smtp_password = null
  await categoryStore.fetchList()
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

// Category management
function addCategory() {
  editingCategoryId.value = null
  categoryForm.name = ''
  categoryForm.color = '#4f46e5'
  categoryDialogVisible.value = true
}

function editCategory(cat: any) {
  editingCategoryId.value = cat.id
  categoryForm.name = cat.name
  categoryForm.color = cat.color || '#4f46e5'
  categoryDialogVisible.value = true
}

async function handleSaveCategory() {
  if (!categoryForm.name.trim()) {
    ElMessage.warning(zhCN.settings.categoryName)
    return
  }
  try {
    if (editingCategoryId.value) {
      await categoryStore.update(editingCategoryId.value, { name: categoryForm.name, color: categoryForm.color })
    } else {
      await categoryStore.create({ name: categoryForm.name, color: categoryForm.color })
    }
    ElMessage.success(zhCN.common.success)
    categoryDialogVisible.value = false
  } catch {}
}

async function handleDeleteCategory(cat: any) {
  try {
    await ElMessageBox.confirm(zhCN.settings.deleteCategoryConfirm, zhCN.common.confirm, { type: 'warning' })
    await categoryStore.remove(cat.id)
    ElMessage.success(zhCN.common.success)
  } catch (e: any) {
    if (e?.response?.data?.detail) {
      ElMessage.error(e.response.data.detail)
    }
  }
}
</script>

<style scoped>
.settings-card {
  margin-bottom: 16px;
}
.category-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.category-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  border-radius: 8px;
  background: #f8fafc;
}
html.dark .category-item {
  background: #1e293b;
}
.category-color-dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  flex-shrink: 0;
}
.category-name {
  flex: 1;
  font-weight: 500;
  font-size: 14px;
}
.category-actions {
  display: flex;
  gap: 4px;
}
</style>