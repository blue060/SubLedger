<template>
  <div>
    <div class="page-header">
      <h2>{{ zhCN.notification.title }}</h2>
      <div style="display: flex; gap: 8px">
        <el-button size="small" @click="handleDeleteRead">{{ zhCN.notification.deleteRead }}</el-button>
        <el-button size="small" @click="handleMarkAllRead">{{ zhCN.notification.markAllRead }}</el-button>
      </div>
    </div>

    <div class="filter-bar">
      <el-radio-group v-model="filter" size="small" @change="handleFilterChange">
        <el-radio-button value="all">{{ zhCN.notification.filterAll }}</el-radio-button>
        <el-radio-button value="unread">{{ zhCN.notification.filterUnread }}</el-radio-button>
      </el-radio-group>
    </div>

    <el-empty v-if="!notifications.length" :description="zhCN.common.noData" />

    <el-card v-for="n in notifications" :key="n.id" class="notification-card" :class="{ unread: !n.is_read }">
      <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 12px">
        <div style="flex: 1; min-width: 0">
          <div class="notification-message" @click="goToSubscription(n.subscription_id)">
            {{ n.message }}
          </div>
          <div class="notification-meta">
            <span>{{ n.notify_date }}</span>
            <el-tag v-if="n.sent_email" size="small" type="info" class="status-tag">{{ zhCN.notification.emailSent }}</el-tag>
            <el-tag v-if="n.sent_push" size="small" type="info" class="status-tag">{{ zhCN.notification.pushSent }}</el-tag>
          </div>
        </div>
        <div class="notification-actions">
          <template v-if="n.message.includes('扣款')">
            <el-button size="small" type="primary" @click="handleKeepRenewal(n)">{{ zhCN.notification.keepRenewal }}</el-button>
            <el-button size="small" type="danger" plain @click="handleCancelRenewal(n)">{{ zhCN.notification.cancelRenewal }}</el-button>
          </template>
          <template v-else-if="n.message.includes('到期')">
            <el-button size="small" @click="goToSubscription(n.subscription_id)">{{ zhCN.notification.viewSubscription }}</el-button>
          </template>
          <el-button v-if="!n.is_read" size="small" text @click="handleMarkRead(n.id)">{{ zhCN.notification.markRead }}</el-button>
          <el-button size="small" text type="danger" @click="handleDelete(n.id)">{{ zhCN.common.delete }}</el-button>
        </div>
      </div>
    </el-card>

    <div v-if="total > pageSize" style="display: flex; justify-content: center; margin-top: 16px">
      <el-pagination
        v-model:current-page="currentPage"
        :page-size="pageSize"
        :total="total"
        layout="prev, pager, next"
        @current-change="fetchNotifications"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { listNotifications, markRead, markAllRead, deleteNotification, deleteReadNotifications } from '../api/notifications'
import { updateSubscription } from '../api/subscriptions'
import { zhCN } from '../locales/zh-CN'

const router = useRouter()
const notifications = ref<any[]>([])
const filter = ref('all')
const currentPage = ref(1)
const pageSize = 20
const total = ref(0)

async function fetchNotifications() {
  const res = await listNotifications(filter.value === 'unread', currentPage.value, pageSize)
  notifications.value = res.data.items
  total.value = res.data.total
}

function handleFilterChange() {
  currentPage.value = 1
  fetchNotifications()
}

onMounted(fetchNotifications)

async function handleMarkRead(id: number) {
  await markRead(id)
  const n = notifications.value.find((x) => x.id === id)
  if (n) n.is_read = true
}

async function handleMarkAllRead() {
  await markAllRead()
  notifications.value.forEach((n) => (n.is_read = true))
  ElMessage.success(zhCN.common.success)
}

async function handleDelete(id: number) {
  await ElMessageBox.confirm(zhCN.notification.deleteConfirm, zhCN.common.confirm, { type: 'warning' })
  await deleteNotification(id)
  await fetchNotifications()
  ElMessage.success(zhCN.common.success)
}

async function handleDeleteRead() {
  await ElMessageBox.confirm(zhCN.notification.deleteReadConfirm, zhCN.common.confirm, { type: 'warning' })
  await deleteReadNotifications()
  await fetchNotifications()
  ElMessage.success(zhCN.common.success)
}

async function handleKeepRenewal(n: any) {
  await handleMarkRead(n.id)
}

async function handleCancelRenewal(n: any) {
  try {
    await ElMessageBox.confirm(
      zhCN.dashboard.cancelRenewalConfirm.replace('{name}', n.message.split(' ')[0]),
      zhCN.common.confirm,
      { type: 'warning' }
    )
    await updateSubscription(n.subscription_id, { is_active: false })
    await handleMarkRead(n.id)
    ElMessage.success(zhCN.common.success)
  } catch {}
}

function goToSubscription(subscriptionId: number) {
  router.push({ path: '/subscriptions', query: { highlight: String(subscriptionId) } })
}
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.filter-bar {
  margin-bottom: 16px;
}
.notification-card {
  margin-bottom: 8px;
}
.unread {
  border-left: 3px solid #f56c6c;
}
.notification-message {
  cursor: pointer;
  color: #303133;
  line-height: 1.5;
}
.notification-message:hover {
  color: #409eff;
}
.notification-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #909399;
  font-size: 12px;
  margin-top: 4px;
}
.status-tag {
  font-size: 11px;
}
.notification-actions {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
  flex-wrap: wrap;
  justify-content: flex-end;
}
</style>
