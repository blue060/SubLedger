<template>
  <div>
    <h2>{{ zhCN.dashboard.title }}</h2>

    <el-row :gutter="16" class="summary-row">
      <el-col :span="12" :xs="24">
        <el-card shadow="hover">
          <template #header>{{ zhCN.dashboard.monthlySpend }}</template>
          <div class="amount">{{ summary.monthly_total_currency }} {{ (summary.monthly_total ?? 0).toFixed(2) }}</div>
        </el-card>
      </el-col>
      <el-col :span="12" :xs="24">
        <el-card shadow="hover">
          <template #header>{{ zhCN.dashboard.nextMonthProjected }}</template>
          <div class="amount">{{ summary.next_month_projected_currency }} {{ (summary.next_month_projected ?? 0).toFixed(2) }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row v-if="expiring.length" :gutter="16" style="margin-top: 16px">
      <el-col :span="24">
        <el-card shadow="hover" class="expiring-card">
          <template #header>
            <span style="color: #f56c6c; font-weight: 600">{{ zhCN.dashboard.expiringSoon }}</span>
          </template>
          <div class="expiring-list">
            <div v-for="item in expiring" :key="item.id" class="expiring-item">
              <span class="expiring-name">{{ item.name }}</span>
              <el-tag :type="item.remaining_days <= 0 ? 'danger' : item.remaining_days <= 7 ? 'danger' : 'warning'" size="small">
                {{ item.remaining_days <= 0 ? zhCN.subscription.expired : zhCN.subscription.daysLeft.replace('{days}', String(item.remaining_days)) }}
              </el-tag>
              <span class="expiring-date">{{ item.expiry_date }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :span="12" :xs="24">
        <el-card shadow="hover">
          <template #header>{{ zhCN.dashboard.categoryBreakdown }}</template>
          <div ref="chartRef" style="height: 300px"></div>
        </el-card>
      </el-col>
      <el-col :span="12" :xs="24">
        <el-card shadow="hover">
          <template #header>{{ zhCN.dashboard.upcomingPayments }}</template>
          <el-timeline v-if="calendar.length">
            <el-timeline-item
              v-for="entry in calendar"
              :key="entry.date + entry.subscription_name"
              :timestamp="entry.date"
            >
              {{ entry.subscription_name }} - {{ entry.currency }} {{ Number(entry.amount).toFixed(2) }}
              <span v-if="entry.converted_amount !== entry.amount">
                (≈ {{ Number(entry.converted_amount).toFixed(2) }})
              </span>
            </el-timeline-item>
          </el-timeline>
          <el-empty v-else :description="zhCN.common.noData" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import * as echarts from 'echarts'
import { getDashboardSummary, getDashboardStats, getDashboardCalendar, getDashboardExpiring } from '../api/dashboard'
import { zhCN } from '../locales/zh-CN'

const summary = ref<Record<string, any>>({})
const stats = ref<any[]>([])
const calendar = ref<any[]>([])
const expiring = ref<any[]>([])
const chartRef = ref<HTMLElement>()
let chartInstance: echarts.ECharts | null = null

const resizeHandler = () => chartInstance?.resize()

onMounted(async () => {
  const [summaryRes, statsRes, calendarRes, expiringRes] = await Promise.all([
    getDashboardSummary().catch(() => ({ data: {} })),
    getDashboardStats().catch(() => ({ data: [] })),
    getDashboardCalendar().catch(() => ({ data: [] })),
    getDashboardExpiring().catch(() => ({ data: [] })),
  ])
  summary.value = summaryRes.data
  stats.value = statsRes.data
  calendar.value = calendarRes.data
  expiring.value = expiringRes.data

  await nextTick()
  renderChart()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeHandler)
  chartInstance?.dispose()
})

function renderChart() {
  if (!chartRef.value || !stats.value.length) return
  chartInstance = echarts.init(chartRef.value)
  chartInstance.setOption({
    tooltip: { trigger: 'item' },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      data: stats.value.map((s: any) => ({
        name: s.category_name,
        value: s.total_amount,
        itemStyle: { color: s.color },
      })),
    }],
  })
  window.addEventListener('resize', resizeHandler)
}
</script>

<style scoped>
.amount {
  font-size: 28px;
  font-weight: 600;
  color: #409eff;
}
.summary-row .el-col {
  margin-bottom: 16px;
}
.expiring-card {
  border: 1px solid #fde2e2;
}
.expiring-list {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}
.expiring-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: #fef0f0;
  border-radius: 4px;
}
.expiring-name {
  font-weight: 500;
}
.expiring-date {
  color: #909399;
  font-size: 12px;
}
</style>