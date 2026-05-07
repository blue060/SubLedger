<template>
  <div>
    <h2>{{ zhCN.calendar.title }}</h2>

    <!-- Monthly total summary -->
    <el-card v-if="monthlyTotal > 0" shadow="hover" class="calendar-summary">
      <span class="calendar-summary-label">{{ zhCN.calendar.monthlyTotal }}</span>
      <span class="calendar-summary-value">{{ preferredCurrency }} {{ monthlyTotal.toFixed(2) }}</span>
    </el-card>

    <el-calendar v-model="currentDate">
      <template #date-cell="{ data }">
        <div class="calendar-cell">
          <div class="calendar-day">{{ data.day.split('-')[2] }}</div>
          <div v-if="getPayments(data.day).length" class="calendar-payments">
            <div v-for="p in getPayments(data.day)" :key="p.subscription_name" class="calendar-payment">
              <el-tag size="small" :color="p.category_color || '#4f46e5'" style="color: #fff; border: none" @mouseenter="hoveredPayment = p" @mouseleave="hoveredPayment = null">
                {{ p.subscription_name.length > 6 ? p.subscription_name.slice(0, 6) + '…' : p.subscription_name }}
              </el-tag>
              <div v-if="hoveredPayment && hoveredPayment.subscription_name === p.subscription_name" class="calendar-tooltip">
                <div class="calendar-tooltip-name">{{ p.subscription_name }}</div>
                <div class="calendar-tooltip-amount">{{ p.currency }} {{ p.amount.toFixed(2) }} <span v-if="Math.abs(p.converted_amount - p.amount) > 0.005">(≈ {{ preferredCurrency }} {{ p.converted_amount.toFixed(2) }})</span></div>
              </div>
            </div>
          </div>
        </div>
      </template>
    </el-calendar>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { getDashboardCalendar, getDashboardSummary } from '../api/dashboard'
import { zhCN } from '../locales/zh-CN'

const currentDate = ref(new Date())
const payments = ref<any[]>([])
const hoveredPayment = ref<any>(null)
const monthlyTotal = ref(0)
const preferredCurrency = ref('CNY')

async function fetchCalendarData() {
  try {
    const d = currentDate.value
    const year = d.getFullYear()
    const month = d.getMonth() + 1

    const calRes = await getDashboardCalendar(year, month)
    payments.value = calRes.data

    // Compute monthly total from calendar data (using converted amounts)
    monthlyTotal.value = calRes.data.reduce((sum: number, p: any) => sum + p.converted_amount, 0)

    // Fetch preferred currency once
    if (preferredCurrency.value === 'CNY') {
      const summaryRes = await getDashboardSummary()
      preferredCurrency.value = summaryRes.data.monthly_total_currency ?? 'CNY'
    }
  } catch {}
}

onMounted(fetchCalendarData)

watch(currentDate, (newDate, oldDate) => {
  if (newDate.getMonth() !== oldDate.getMonth() || newDate.getFullYear() !== oldDate.getFullYear()) {
    fetchCalendarData()
  }
})

function getPayments(day: string) {
  return payments.value.filter((p: any) => p.date === day)
}
</script>

<style scoped>
.calendar-summary {
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
}
.calendar-summary-label {
  font-size: 14px;
  color: #64748b;
  font-weight: 500;
}
.calendar-summary-value {
  font-size: 22px;
  font-weight: 700;
  color: #4f46e5;
}

.calendar-cell {
  height: 100%;
  min-height: 60px;
  position: relative;
}
.calendar-day {
  font-size: 14px;
  text-align: center;
}
.calendar-payments {
  margin-top: 2px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.calendar-payment {
  margin-top: 2px;
  position: relative;
}
.calendar-tooltip {
  position: absolute;
  z-index: 100;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  background: #1e293b;
  color: #fff;
  border-radius: 8px;
  padding: 8px 12px;
  font-size: 12px;
  white-space: nowrap;
  box-shadow: 0 4px 12px rgba(0,0,0,.2);
  pointer-events: none;
}
.calendar-tooltip-name {
  font-weight: 600;
  margin-bottom: 2px;
}
.calendar-tooltip-amount {
  color: #a5b4fc;
}
html.dark .calendar-summary {
  background: #1e293b;
}
</style>
