<template>
  <div v-loading="loading">
    <div class="report-header">
      <h2>{{ zhCN.annualReport.title }}</h2>
      <div class="year-nav">
        <el-button :icon="ArrowLeft" text @click="year--" />
        <span class="year-label">{{ year }}</span>
        <el-button :icon="ArrowRight" text :disabled="year >= currentYear" @click="year++" />
      </div>
    </div>

    <!-- Summary cards -->
    <div class="stat-row">
      <el-card shadow="hover" class="stat-card stat-color-blue" :body-style="{ padding: '18px' }">
        <div class="stat-label">{{ zhCN.annualReport.totalSpending }}</div>
        <div class="stat-value">{{ report.currency }} {{ report.total?.toFixed(2) || '0.00' }}</div>
      </el-card>
      <el-card shadow="hover" class="stat-card stat-color-green" :body-style="{ padding: '18px' }">
        <div class="stat-label">{{ zhCN.annualReport.avgMonthly }}</div>
        <div class="stat-value">{{ report.currency }} {{ avgMonthly }}</div>
      </el-card>
      <el-card shadow="hover" class="stat-card stat-color-purple" :body-style="{ padding: '18px' }">
        <div class="stat-label">{{ zhCN.annualReport.subCount }}</div>
        <div class="stat-value">{{ report.subscription_count || 0 }}</div>
      </el-card>
    </div>

    <!-- Charts row -->
    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :span="14" :xs="24">
        <el-card shadow="hover" class="chart-card">
          <template #header>{{ zhCN.annualReport.monthlyTrend }}</template>
          <div ref="trendRef" style="height: 300px"></div>
        </el-card>
      </el-col>
      <el-col :span="10" :xs="24">
        <el-card shadow="hover" class="chart-card">
          <template #header>{{ zhCN.annualReport.categoryBreakdown }}</template>
          <div ref="pieRef" style="height: 300px"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Top subscriptions -->
    <el-card shadow="hover" class="chart-card" style="margin-top: 16px">
      <template #header>{{ zhCN.annualReport.topSubscriptions }}</template>
      <div class="top-list">
        <div v-for="(sub, i) in report.top_subscriptions" :key="sub.id" class="top-item">
          <div class="top-rank">{{ Number(i) + 1 }}</div>
          <div class="top-info">
            <span class="top-name">{{ sub.name }}</span>
            <el-tag v-if="sub.category_name" :color="sub.category_color" size="small" effect="dark" style="color: #fff; border: none; border-radius: 6px">{{ sub.category_name }}</el-tag>
          </div>
          <div class="top-cost">
            <span class="top-amount">{{ sub.currency }} {{ sub.annual_cost?.toFixed(2) }}</span>
            <span class="top-period">/年</span>
          </div>
          <div class="top-bar">
            <div class="top-bar-fill" :style="{ width: barWidth(sub) + '%' }"></div>
          </div>
        </div>
        <el-empty v-if="!report.top_subscriptions?.length" :description="zhCN.common.noData" />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { ArrowLeft, ArrowRight } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { getAnnualReport } from '../api/analytics'
import { zhCN } from '../locales/zh-CN'

const loading = ref(true)
const currentYear = new Date().getFullYear()
const year = ref(currentYear)
const report = ref<Record<string, any>>({})

const trendRef = ref<HTMLElement>()
const pieRef = ref<HTMLElement>()
let trendChart: echarts.ECharts | null = null
let pieChart: echarts.ECharts | null = null
const isDark = ref(document.documentElement.classList.contains('dark'))

const avgMonthly = computed(() => {
  const total = report.value.total || 0
  return (total / 12).toFixed(2)
})

function barWidth(sub: any) {
  const max = Math.max(...(report.value.top_subscriptions || []).map((s: any) => s.annual_cost || 0))
  if (!max) return 0
  return Math.round(((sub.annual_cost || 0) / max) * 100)
}

const resizeHandler = () => { trendChart?.resize(); pieChart?.resize() }

async function fetchData() {
  loading.value = true
  try {
    const res = await getAnnualReport(year.value)
    report.value = res.data
    await nextTick()
    renderTrend()
    renderPie()
  } catch {}
  loading.value = false
}

onMounted(() => {
  fetchData()
  window.addEventListener('resize', resizeHandler)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeHandler)
  trendChart?.dispose()
  pieChart?.dispose()
})

watch(year, () => fetchData())

function renderTrend() {
  if (!trendRef.value || !report.value.monthly_totals?.length) return
  trendChart = echarts.init(trendRef.value)
  const textColor = isDark.value ? '#94a3b8' : '#64748b'
  const gridColor = isDark.value ? 'rgba(255,255,255,.06)' : 'rgba(0,0,0,.04)'
  const data = report.value.monthly_totals

  trendChart.setOption({
    tooltip: {
      trigger: 'axis',
      confine: true,
      backgroundColor: isDark.value ? '#1e293b' : '#fff',
      borderColor: isDark.value ? '#334155' : '#e2e8f0',
      textStyle: { color: isDark.value ? '#e2e8f0' : '#1e293b', fontSize: 13 },
    },
    xAxis: {
      type: 'category',
      data: data.map((m: any) => m.month.slice(5)),
      axisLabel: { fontSize: 12, color: textColor },
      axisLine: { show: false },
      axisTick: { show: false },
      boundaryGap: false,
    },
    yAxis: {
      type: 'value',
      axisLabel: { fontSize: 12, color: textColor },
      splitLine: { lineStyle: { color: gridColor, type: 'dashed' } },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    series: [{
      type: 'bar',
      data: data.map((m: any) => m.total),
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: '#6366f1' },
          { offset: 1, color: '#818cf8' },
        ]),
        borderRadius: [6, 6, 0, 0],
      },
      barWidth: '50%',
      emphasis: { itemStyle: { shadowBlur: 12, shadowColor: 'rgba(99,102,241,.3)' } },
    }],
    grid: { left: 56, right: 20, top: 16, bottom: 32 },
  })
}

function renderPie() {
  if (!pieRef.value || !report.value.category_totals?.length) return
  pieChart = echarts.init(pieRef.value)
  const textColor = isDark.value ? '#94a3b8' : '#64748b'

  pieChart.setOption({
    tooltip: {
      trigger: 'item',
      confine: true,
      backgroundColor: isDark.value ? '#1e293b' : '#fff',
      borderColor: isDark.value ? '#334155' : '#e2e8f0',
      textStyle: { color: isDark.value ? '#e2e8f0' : '#1e293b', fontSize: 13 },
      formatter: (p: any) => `<b>${p.name}</b><br/>${p.value.toFixed(2)} · ${p.percent}%`,
    },
    legend: { bottom: 0, type: 'scroll', textStyle: { fontSize: 12, color: textColor }, itemWidth: 12, itemHeight: 12 },
    series: [{
      type: 'pie',
      radius: ['42%', '72%'],
      center: ['50%', '44%'],
      itemStyle: { borderRadius: 8, borderColor: isDark.value ? 'rgba(255,255,255,.04)' : '#fff', borderWidth: 3 },
      data: report.value.category_totals.map((c: any) => ({
        name: c.name,
        value: c.total,
        itemStyle: { color: c.color },
      })),
      label: { show: false },
      emphasis: { scaleSize: 6, itemStyle: { shadowBlur: 16, shadowColor: 'rgba(99,102,241,.25)' } },
    }],
  })
}
</script>

<style scoped>
.report-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.year-nav {
  display: flex;
  align-items: center;
  gap: 8px;
}
.year-label {
  font-size: 18px;
  font-weight: 700;
  min-width: 50px;
  text-align: center;
}
.stat-row {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}
.stat-card {
  flex: 1;
  min-width: 180px;
  border: none !important;
  border-top: 4px solid transparent !important;
  transition: transform .2s, box-shadow .2s;
  background: var(--surface, #fff) !important;
}
.stat-card:hover { transform: translateY(-3px); }
.stat-color-blue { border-top-color: #6366f1 !important; }
.stat-color-green { border-top-color: #10b981 !important; }
.stat-color-purple { border-top-color: #8b5cf6 !important; }
.stat-card:hover.stat-color-blue { box-shadow: 0 8px 24px rgba(99,102,241,.18) !important; }
.stat-card:hover.stat-color-green { box-shadow: 0 8px 24px rgba(16,185,129,.18) !important; }
.stat-card:hover.stat-color-purple { box-shadow: 0 8px 24px rgba(139,92,246,.18) !important; }
.stat-label { font-size: 13px; color: var(--text-muted, #94a3b8); font-weight: 600; margin-bottom: 8px; text-transform: uppercase; letter-spacing: .5px; }
.stat-value { font-size: 28px; font-weight: 800; color: var(--text-primary, #0f172a); line-height: 1.1; letter-spacing: -.5px; }
.chart-card { border-radius: 16px !important; }

.top-list { display: flex; flex-direction: column; gap: 4px; }
.top-item {
  display: grid;
  grid-template-columns: 32px 1fr auto;
  grid-template-rows: auto auto;
  gap: 0 12px;
  padding: 12px 0;
  border-bottom: 1px solid rgba(0,0,0,.04);
  align-items: center;
}
.top-item:last-child { border-bottom: none; }
.top-rank {
  grid-row: 1 / 3;
  width: 28px; height: 28px;
  border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  font-size: 13px; font-weight: 700; color: #fff;
  background: var(--primary, #6366f1);
}
.top-item:nth-child(1) .top-rank { background: #6366f1; }
.top-item:nth-child(2) .top-rank { background: #8b5cf6; }
.top-item:nth-child(3) .top-rank { background: #06b6d4; }
.top-item:nth-child(n+4) .top-rank { background: var(--text-muted, #94a3b8); }
.top-info { display: flex; align-items: center; gap: 8px; min-width: 0; }
.top-name { font-weight: 600; font-size: 14px; color: var(--text-primary, #0f172a); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.top-cost { text-align: right; white-space: nowrap; }
.top-amount { font-size: 15px; font-weight: 700; color: var(--primary, #6366f1); }
.top-period { font-size: 12px; color: var(--text-muted, #94a3b8); margin-left: 2px; }
.top-bar {
  grid-column: 2 / 4;
  height: 4px; border-radius: 2px;
  background: rgba(99,102,241,.08); margin-top: 4px;
}
.top-bar-fill {
  height: 100%; border-radius: 2px;
  background: linear-gradient(90deg, #6366f1, #818cf8);
  transition: width .4s ease;
}

html.dark .top-item { border-bottom-color: rgba(255,255,255,.04); }
html.dark .top-name { color: #e2e8f0; }
html.dark .top-amount { color: #818cf8; }
html.dark .top-bar { background: rgba(129,140,248,.08); }
</style>
