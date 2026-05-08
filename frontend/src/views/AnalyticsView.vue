<template>
  <div v-loading="loading">
    <h2>{{ zhCN.analytics.title }}</h2>

    <!-- Monthly comparison -->
    <el-row :gutter="16">
      <el-col :span="8" :xs="24">
        <el-card shadow="hover" class="comp-card">
          <div class="comp-label">{{ zhCN.analytics.currentMonth }}</div>
          <div class="comp-value">{{ comparison.currency }} {{ comparison.current_month?.toFixed(2) || '0.00' }}</div>
        </el-card>
      </el-col>
      <el-col :span="8" :xs="24">
        <el-card shadow="hover" class="comp-card">
          <div class="comp-label">{{ zhCN.analytics.lastMonth }}</div>
          <div class="comp-value">{{ comparison.currency }} {{ comparison.last_month?.toFixed(2) || '0.00' }}</div>
        </el-card>
      </el-col>
      <el-col :span="8" :xs="24">
        <el-card shadow="hover" class="comp-card" :class="comparison.change >= 0 ? 'comp-up' : 'comp-down'">
          <div class="comp-label">{{ zhCN.analytics.monthlyComparison }}</div>
          <div class="comp-value">{{ comparison.change >= 0 ? '+' : '' }}{{ comparison.change?.toFixed(2) || '0.00' }}</div>
          <div class="comp-hint">{{ comparison.change >= 0 ? '↑' : '↓' }}</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Category trend chart -->
    <el-card shadow="hover" style="margin-top: 16px">
      <template #header>{{ zhCN.analytics.categoryTrend }}</template>
      <div ref="trendRef" style="height: 320px"></div>
    </el-card>

    <!-- Top subscriptions + Currency breakdown -->
    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :span="14" :xs="24">
        <el-card shadow="hover">
          <template #header>{{ zhCN.analytics.topSubscriptions }}</template>
          <el-table :data="topSubs" stripe size="small" style="width: 100%">
            <el-table-column prop="name" :label="zhCN.subscription.name" />
            <el-table-column prop="category_name" :label="zhCN.subscription.category" width="100">
              <template #default="{ row }">
                <el-tag v-if="row.category_name" :color="row.category_color" size="small" style="color: #fff; border: none">{{ row.category_name }}</el-tag>
                <span v-else>--</span>
              </template>
            </el-table-column>
            <el-table-column :label="zhCN.analytics.yearlyCost" width="140" prop="converted_amount">
              <template #default="{ row }">{{ row.currency }} {{ row.amount.toFixed(2) }} (≈{{ row.converted_amount.toFixed(2) }})</template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="10" :xs="24">
        <el-card shadow="hover">
          <template #header>{{ zhCN.analytics.currencyBreakdown }}</template>
          <div ref="currencyRef" style="height: 260px"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import * as echarts from 'echarts'
import { getMonthlyComparison, getCategoryTrend, getTopSubscriptions, getCurrencyBreakdown } from '../api/analytics'
import { zhCN } from '../locales/zh-CN'

const loading = ref(true)
const comparison = ref<Record<string, any>>({ current_month: 0, last_month: 0, change: 0, currency: 'CNY' })
const trend = ref<any[]>([])
const topSubs = ref<any[]>([])
const currencyData = ref<any[]>([])

const trendRef = ref<HTMLElement>()
const currencyRef = ref<HTMLElement>()
let trendChart: echarts.ECharts | null = null
let currencyChart: echarts.ECharts | null = null
const isDark = ref(document.documentElement.classList.contains('dark'))

const palette = ['#4f46e5','#7c3aed','#06b6d4','#059669','#d97706','#dc2626','#ec4899','#6366f1','#0ea5e9','#10b981']

const resizeHandler = () => { trendChart?.resize(); currencyChart?.resize() }

onMounted(async () => {
  const [compRes, trendRes, topRes, curRes] = await Promise.all([
    getMonthlyComparison().catch(() => ({ data: {} })),
    getCategoryTrend().catch(() => ({ data: [] })),
    getTopSubscriptions().catch(() => ({ data: [] })),
    getCurrencyBreakdown().catch(() => ({ data: [] })),
  ])
  comparison.value = compRes.data
  trend.value = trendRes.data
  topSubs.value = topRes.data
  currencyData.value = curRes.data

  await nextTick()
  renderTrend()
  renderCurrency()
  loading.value = false
  window.addEventListener('resize', resizeHandler)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeHandler)
  trendChart?.dispose()
  currencyChart?.dispose()
})

function renderTrend() {
  if (!trendRef.value || !trend.value.length) return
  trendChart = echarts.init(trendRef.value)
  const textColor = isDark.value ? '#94a3b8' : '#64748b'
  const allCats = new Set<string>()
  trend.value.forEach((m: any) => Object.keys(m.categories).forEach(c => allCats.add(c)))
  const catList = Array.from(allCats)

  trendChart.setOption({
    tooltip: { trigger: 'axis', confine: true },
    legend: { bottom: 0, type: 'scroll', textStyle: { fontSize: 12, color: textColor } },
    xAxis: {
      type: 'category',
      data: trend.value.map((m: any) => m.month.slice(5)),
      axisLabel: { fontSize: 12, color: textColor },
    },
    yAxis: {
      type: 'value',
      axisLabel: { fontSize: 12, color: textColor },
      splitLine: { lineStyle: { color: isDark.value ? '#1e293b' : '#f1f5f9' } },
    },
    series: catList.map((cat, i) => ({
      name: cat,
      type: 'bar',
      stack: 'total',
      data: trend.value.map((m: any) => m.categories[cat] || 0),
      itemStyle: { color: palette[i % palette.length], borderRadius: i === catList.length - 1 ? [4, 4, 0, 0] : [0, 0, 0, 0] },
      barWidth: '50%',
    })),
    grid: { left: 60, right: 20, top: 20, bottom: 50 },
  })
}

function renderCurrency() {
  if (!currencyRef.value || !currencyData.value.length) return
  currencyChart = echarts.init(currencyRef.value)
  const textColor = isDark.value ? '#e2e8f0' : '#334155'

  currencyChart.setOption({
    tooltip: { trigger: 'item', confine: true },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['50%', '45%'],
      itemStyle: { borderRadius: 6, borderColor: isDark.value ? '#1e293b' : '#fff', borderWidth: 2 },
      data: currencyData.value.map((c: any, i: number) => ({
        name: `${c.currency} (${c.count})`,
        value: c.converted_amount,
        itemStyle: { color: palette[i % palette.length] },
      })),
      label: { fontSize: 12, color: textColor },
    }],
    legend: { bottom: 0, type: 'scroll', textStyle: { fontSize: 12, color: textColor } },
  })
}
</script>

<style scoped>
.comp-card { text-align: center; margin-bottom: 16px; }
.comp-label { font-size: 13px; color: #94a3b8; margin-bottom: 6px; }
.comp-value { font-size: 24px; font-weight: 700; color: #1e293b; }
.comp-up .comp-value { color: #ef4444; }
.comp-down .comp-value { color: #059669; }
.comp-hint { font-size: 18px; font-weight: 700; }
.comp-up .comp-hint { color: #ef4444; }
.comp-down .comp-hint { color: #059669; }
html.dark .comp-value { color: #e2e8f0; }
</style>