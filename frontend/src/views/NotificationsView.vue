<template>
  <div>
    <div class="page-header">
      <h2>{{ zhCN.notification.title }}</h2>
      <el-button @click="handleMarkAllRead">{{ zhCN.notification.markAllRead }}</el-button>
    </div>

    <el-empty v-if="!notifications.length" :description="zhCN.common.noData" />

    <el-card v-for="n in notifications" :key="n.id" class="notification-card" :class="{ unread: !n.is_read }">
      <div style="display: flex; justify-content: space-between; align-items: center">
        <span>{{ n.message }}</span>
        <el-button v-if="!n.is_read" size="small" text @click="handleMarkRead(n.id)">{{ zhCN.notification.markRead }}</el-button>
      </div>
      <div style="color: #909399; font-size: 12px; margin-top: 4px">{{ n.notify_date }}</div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { listNotifications, markRead, markAllRead } from '../api/notifications'
import { zhCN } from '../locales/zh-CN'

const notifications = ref<any[]>([])

onMounted(async () => {
  const res = await listNotifications()
  notifications.value = res.data
})

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
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.notification-card {
  margin-bottom: 8px;
}
.unread {
  border-left: 3px solid #f56c6c;
}
</style>