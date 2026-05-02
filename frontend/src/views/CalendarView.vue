<template>
  <div>
    <h2>{{ zhCN.calendar.title }}</h2>
    <el-calendar v-model="currentDate">
      <template #date-cell="{ data }">
        <div class="calendar-cell">
          <div class="calendar-day">{{ data.day.split('-')[2] }}</div>
          <div v-if="getPayments(data.day).length" class="calendar-payments">
            <div v-for="p in getPayments(data.day)" :key="p.subscription_name" class="calendar-payment">
              <el-tag size="small" :type="p.remaining_days !== undefined && p.remaining_days <= 7 ? 'danger' : 'primary'">
                {{ p.subscription_name }}
              </el-tag>
            </div>
          </div>
        </div>
      </template>
    </el-calendar>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getDashboardCalendar } from '../api/dashboard'
import { zhCN } from '../locales/zh-CN'

const currentDate = ref(new Date())
const payments = ref<any[]>([])

onMounted(async () => {
  try {
    const res = await getDashboardCalendar()
    payments.value = res.data
  } catch {}
})

function getPayments(day: string) {
  return payments.value.filter((p: any) => p.date === day)
}
</script>

<style scoped>
.calendar-cell {
  height: 100%;
  min-height: 60px;
}
.calendar-day {
  font-size: 14px;
  text-align: center;
}
.calendar-payments {
  margin-top: 2px;
}
.calendar-payment {
  margin-top: 2px;
}
</style>