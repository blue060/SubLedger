<template>
  <div v-loading="loading">
    <h2>{{ zhCN.analytics.title }}</h2>

    <!-- Monthly comparison -->
    <div class="comp-row">
      <div class="comp-card comp-card-current">
        <div class="comp-icon">📊</div>
        <div class="comp-text">
          <div class="comp-label">{{ zhCN.analytics.currentMonth }}</div>
          <div class="comp-value">{{ comparison.currency }} {{ comparison.current_month?.toFixed(2) || '0.00' }}</div>
        </div>
      </div>
      <div class="comp-card comp-card-last">
        <div class="comp-icon">📅</div>
        <div class="comp-text">
          <div class="comp-label">{{ zhCN.analytics.lastMonth }}</div>
          <div class="comp-value">{{ comparison.currency }} {{ comparison.last_month?.toFixed(2) || '0.00' }}</div>
        </div>
      </div>
      <div class="comp-card" :class="comparison.change >= 0 ? 'comp-card-up' : 'comp-card-down'">
        <div class="comp-icon">{{ comparison.change >= 0 ? '↑' : '↓' }}</div>
        <div class="comp-text">
          <div class="comp-label">{{ zhCN.analytics.monthlyComparison }}</div>
          <div class="comp-value">{{ comparison.change >= 0 ? '+' : '' }}{{ comparison.change?.toFixed(2) || '0.00' }}</div>
        </div>
      </div>
    </div>

    <!-- Category trend chart -->
    <el-card shadow="hover" class="chart-card">
      <template #header>{{ zhCN.analytics.categoryTrend }}</template>
      <div ref="trendRef" style="height: 320px"></div>
    </el-card>

    <!-- Top subscriptions + Currency breakdown -->
    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :span="14" :xs="24">
        <el-card shadow="hover" class="chart-card">
          <template #header>{{ zhCN.analytics.topSubscriptions }}</template>
          <div class="top-subs-list">
            <div v-for="(sub, i) in topSubs" :key="sub.id" class="top-sub-item">
              <div class="top-sub-rank">{{ i + 1 }}</div>
              <div class="top-sub-info">
                <span class="top-sub-name">{{ sub.name }}</span>
                <el-tag v-if="sub.category_name" :color="sub.category_color" size="small" effect="dark" style="color: #fff; border: none; border-radius: 6px">{{ sub.category_name }}</el-tag>
              </div>
              <div class="top-sub-cost">
                <span class="top-sub-original">{{ sub.currency }} {{ sub.amount.toFixed(2) }}</span>
                <span class="top-sub-converted">≈ {{ sub.converted_amount.toFixed(2) }}</span>
              </div>
              <div class="top-sub-bar">
                <div class="top-sub-bar-fill" :style="{ width: barWidth(sub) + '%' }"></div>
              </div>
            </div>
            <el-empty v-if="!topSubs.length" :description="zhCN.common.noData" />
          </div>
        </el-card>
      </el-col>
      <el-col :span="10" :xs="24">
        <el-card shadow="hover" class="chart-card">
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

const palette = ['#6366f1','#8b5cf6','#06b6d4','#10b981','#f59e0b','#ef4444','#ec4899','#a78bfa','#0ea5e9','#34d399']

function barWidth(sub: any) {
  const max = Math.max(...topSubs.value.map(s => s.converted_amount))
  if (!max) return 0
  return Math.round((sub.converted_amount / max) * 100)
}

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
  const gridColor = isDark.value ? 'rgba(255,255,255,.06)' : 'rgba(0,0,0,.04)'
  const allCats = new Set<string>()
  trend.value.forEach((m: any) => Object.keys(m.categories).forEach(c => allCats.add(c)))
  const catList = Array.from(allCats)

  trendChart.setOption({
    tooltip: {
      trigger: 'axis',
      confine: true,
      backgroundColor: isDark.value ? '#1e293b' : '#fff',
      borderColor: isDark.value ? '#334155' : '#e2e8f0',
      textStyle: { color: isDark.value ? '#e2e8f0' : '#1e293b', fontSize: 13 },
    },
    legend: { bottom: 0, type: 'scroll', textStyle: { fontSize: 12, color: textColor }, itemWidth: 12, itemHeight: 12, itemGap: 16 },
    xAxis: {
      type: 'category',
      data: trend.value.map((m: any) => m.month.slice(5)),
      axisLabel: { fontSize: 12, color: textColor },
      axisLine: { lineStyle: { color: gridColor } },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      axisLabel: { fontSize: 12, color: textColor },
      splitLine: { lineStyle: { color: gridColor, type: 'dashed' } },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    series: catList.map((cat, i) => ({
      name: cat,
      type: 'bar',
      stack: 'total',
      data: trend.value.map((m: any) => m.categories[cat] || 0),
      itemStyle: { color: palette[i % palette.length], borderRadius: i === catList.length - 1 ? [6, 6, 0, 0] : [0, 0, 0, 0] },
      barWidth: '45%',
      emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(99,102,241,.3)' } },
    })),
    grid: { left: 60, right: 20, top: 20, bottom: 50 },
  })
}

function renderCurrency() {
  if (!currencyRef.value || !currencyData.value.length) return
  currencyChart = echarts.init(currencyRef.value)
  const textColor = isDark.value ? '#e2e8f0' : '#334155'

  currencyChart.setOption({
    tooltip: {
      trigger: 'item',
      confine: true,
      backgroundColor: isDark.value ? '#1e293b' : '#fff',
      borderColor: isDark.value ? '#334155' : '#e2e8f0',
      textStyle: { color: isDark.value ? '#e2e8f0' : '#1e293b', fontSize: 13 },
    },
    series: [{
      type: 'pie',
      radius: ['45%', '72%'],
      center: ['50%', '45%'],
      itemStyle: { borderRadius: 8, borderColor: isDark.value ? 'rgba(255,255,255,.04)' : '#fff', borderWidth: 3 },
      data: currencyData.value.map((c: any, i: number) => ({
        name: `${c.currency} (${c.count})`,
        value: c.converted_amount,
        itemStyle: { color: palette[i % palette.length] },
      })),
      label: { fontSize: 12, color: textColor, formatter: '{b}\n{d}%' },
      labelLine: { length: 12, length2: 8 },
      emphasis: { itemStyle: { shadowBlur: 16, shadowColor: 'rgba(99,102,241,.25)' } },
    }],
    legend: { bottom: 0, type: 'scroll', textStyle: { fontSize: 12, color: textColor }, itemWidth: 12, itemHeight: 12 },
  })
}
</script>

<style scoped>
/* Comparison cards */
.comp-row {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}
.comp-card {
  flex: 1;
  min-width: 180px;
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px 24px;
  border-radius: 16px;
  background: var(--surface, #fff);
  border: 1px solid rgba(0,0,0,.04);
  box-shadow: 0 1px 3px rgba(0,0,0,.04), 0 4px 12px rgba(0,0,0,.03);
  transition: transform .2s, box-shadow .2s;
}
.comp-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(99,102,241,.1);
}
.comp-card-current { border-left: 4px solid #6366f1; }
.comp-card-last { border-left: 4px solid #8b5cf6; }
.comp-card-up { border-left: 4px solid #ef4444; }
.comp-card-down { border-left: 4px solid #10b981; }
.comp-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
}
.comp-card-current .comp-icon { background: #eef2ff; color: #6366f1; }
.comp-card-last .comp-icon { background: #f5f3ff; color: #8b5cf6; }
.comp-card-up .comp-icon { background: #fef2f2; color: #ef4444; }
.comp-card-down .comp-icon { background: #ecfdf5; color: #10b981; }
.comp-text { flex: 1; }
.comp-label { font-size: 13px; color: var(--text-muted, #94a3b8); font-weight: 500; margin-bottom: 4px; }
.comp-value { font-size: 24px; font-weight: 800; color: var(--text-primary, #0f172a); letter-spacing: -.3px; }
.comp-card-up .comp-value { color: #ef4444; }
.comp-card-down .comp-value { color: #10b981; }

/* Chart cards */
.chart-card { border-radius: 16px !important; }

/* Top subscriptions list - card style instead of table */
.top-subs-list { display: flex; flex-direction: column; gap: 4px; }
.top-sub-item {
  display: grid;
  grid-template-columns: 32px 1fr auto;
  grid-template-rows: auto auto;
  gap: 0 12px;
  padding: 12px 0;
  border-bottom: 1px solid rgba(0,0,0,.04);
  align-items: center;
}
.top-sub-item:last-child { border-bottom: none; }
.top-sub-rank {
  grid-row: 1 / 3;
  width: 28px;
  height: 28px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 700;
  color: #fff;
  background: var(--primary, #6366f1);
}
.top-sub-item:nth-child(1) .top-sub-rank { background: #6366f1; }
.top-sub-item:nth-child(2) .top-sub-rank { background: #8b5cf6; }
.top-sub-item:nth-child(3) .top-sub-rank { background: #06b6d4; }
.top-sub-item:nth-child(n+4) .top-sub-rank { background: var(--text-muted, #94a3b8); }
.top-sub-info {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}
.top-sub-name {
  font-weight: 600;
  font-size: 14px;
  color: var(--text-primary, #0f172a);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.top-sub-cost {
  text-align: right;
  white-space: nowrap;
}
.top-sub-original { font-size: 14px; font-weight: 600; color: var(--text-primary, #0f172a); }
.top-sub-converted { font-size: 12px; color: var(--text-muted, #94a3b8); margin-left: 4px; }
.top-sub-bar {
  grid-column: 2 / 4;
  height: 4px;
  border-radius: 2px;
  background: rgba(99,102,241,.08);
  margin-top: 4px;
}
.top-sub-bar-fill {
  height: 100%;
  border-radius: 2px;
  background: linear-gradient(90deg, #6366f1, #818cf8);
  transition: width .4s ease;
}

/* Dark mode */
html.dark .comp-card { border-color: rgba(255,255,255,.06); }
html.dark .comp-card:hover { box-shadow: 0 8px 24px rgba(129,140,248,.1); }
html.dark .comp-card-current .comp-icon { background: rgba(99,102,241,.15); }
html.dark .comp-card-last .comp-icon { background: rgba(139,92,246,.15); }
html.dark .comp-card-up .comp-icon { background: rgba(239,68,68,.12); }
html.dark .comp-card-down .comp-icon { background: rgba(16,185,129,.12); }
html.dark .top-sub-item { border-bottom-color: rgba(255,255,255,.04); }
html.dark .top-sub-name { color: #e2e8f0; }
html.dark .top-sub-original { color: #e2e8f0; }
html.dark .top-sub-bar { background: rgba(129,140,248,.08); }
</style>