<template>
  <div>
    <h2>{{ zhCN.dashboard.title }}</h2>

    <!-- Summary cards -->
    <el-row :gutter="16" class="summary-row">
      <el-col :span="8" :xs="12">
        <el-card shadow="hover" class="stat-card stat-gradient-blue" :body-style="{ padding: '20px' }">
          <div class="stat-label">{{ zhCN.dashboard.monthlySpend }}</div>
          <div class="stat-value">{{ summary.monthly_total_currency }} {{ (summary.monthly_total ?? 0).toFixed(2) }}</div>
          <div v-if="summary.monthly_change != null" class="stat-change" :class="summary.monthly_change >= 0 ? 'change-up' : 'change-down'">
            {{ summary.monthly_change >= 0 ? '↑' : '↓' }} {{ zhCN.dashboard.monthlyChange }} {{ Math.abs(summary.monthly_change).toFixed(2) }}
          </div>
        </el-card>
      </el-col>
      <el-col :span="8" :xs="12">
        <el-card shadow="hover" class="stat-card stat-gradient-green" :body-style="{ padding: '20px' }">
          <div class="stat-label">{{ zhCN.dashboard.nextMonthProjected }}</div>
          <div class="stat-value">{{ summary.next_month_projected_currency }} {{ (summary.next_month_projected ?? 0).toFixed(2) }}</div>
        </el-card>
      </el-col>
      <el-col :span="8" :xs="12">
        <el-card shadow="hover" class="stat-card stat-gradient-purple" :body-style="{ padding: '20px' }">
          <div class="stat-label">{{ zhCN.dashboard.yearlySpend }}</div>
          <div class="stat-value">{{ summary.yearly_total_currency }} {{ (summary.yearly_total ?? 0).toFixed(2) }}</div>
        </el-card>
      </el-col>
    </el-row>
    <el-row :gutter="16" class="summary-row">
      <el-col :span="8" :xs="12">
        <el-card shadow="hover" class="stat-card stat-gradient-cyan" :body-style="{ padding: '20px' }">
          <div class="stat-label">{{ zhCN.dashboard.allSubscriptions }}</div>
          <div class="stat-value">{{ activeCount }}</div>
        </el-card>
      </el-col>
      <el-col :span="16" :xs="12">
        <el-card shadow="hover" class="stat-card" :class="budget.exceeded ? 'stat-gradient-red' : 'stat-gradient-orange'" :body-style="{ padding: '20px' }">
          <div class="stat-label">{{ zhCN.dashboard.budget }}</div>
          <div v-if="budget.budget" class="budget-info">
            <div class="stat-value" :class="{ 'text-danger': budget.exceeded }">{{ budget.spent.toFixed(2) }} / {{ budget.budget.toFixed(2) }}</div>
            <el-progress :percentage="Math.min(budget.spent / budget.budget * 100, 100)" :color="budget.exceeded ? '#fca5a5' : '#fff'" :stroke-width="6" style="margin-top: 6px" :show-text="false" />
            <div v-if="budget.exceeded" class="budget-warn">{{ zhCN.dashboard.budgetExceeded }}</div>
            <div v-else class="budget-remain">{{ zhCN.dashboard.budgetRemaining }}: {{ budget.remaining?.toFixed(2) }}</div>
          </div>
          <div v-else class="stat-value muted">{{ zhCN.dashboard.budgetNotSet }}</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Expiring soon alert -->
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

    <!-- Trend chart -->
    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :span="24">
        <el-card shadow="hover">
          <template #header>{{ zhCN.dashboard.monthlyTrend }}</template>
          <div ref="trendRef" style="height: 280px"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Charts row -->
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
              <span v-if="Math.abs(entry.converted_amount - entry.amount) > 0.005">
                (≈ {{ Number(entry.converted_amount).toFixed(2) }})
              </span>
            </el-timeline-item>
          </el-timeline>
          <el-empty v-else :description="zhCN.common.noData" />
        </el-card>
      </el-col>
    </el-row>

    <!-- Subscription cards overview -->
    <h3 style="margin-top: 24px">{{ zhCN.dashboard.allSubscriptions }}</h3>
    <el-empty v-if="!subscriptions.length" :description="zhCN.dashboard.noSubscriptions" />
    <el-row v-else :gutter="16" class="sub-cards">
      <el-col v-for="sub in subscriptions" :key="sub.id" :xs="24" :sm="12" :md="8" :lg="6">
        <el-card shadow="hover" class="sub-card" :class="{ 'sub-expiring': sub.remaining_days != null && sub.remaining_days <= 30 }">
          <div class="sub-card-header">
            <img v-if="sub.url" :src="getFavicon(sub.url)" class="sub-card-favicon" alt="" @error="($event.target as HTMLImageElement).style.display='none'" />
            <span class="sub-card-name">{{ sub.name }}</span>
            <el-tag v-if="sub.category_name" :color="sub.category_color" size="small" style="color: #fff; border: none">
              {{ sub.category_name }}
            </el-tag>
          </div>
          <div class="sub-card-amount">{{ formatCurrency(sub.amount, sub.currency) }}<span class="sub-card-cycle"> /{{ cycleLabel(sub.billing_cycle, sub.billing_cycle_num, sub.billing_cycle_unit) }}</span></div>
          <div class="sub-card-info">
            <span v-if="sub.billing_cycle === 'once' || sub.billing_cycle === 'permanent'">{{ zhCN.dashboard.permanentPurchase }}</span>
            <span v-else>{{ zhCN.dashboard.nextBill }}: {{ sub.next_payment_date || '--' }}</span>
          </div>
          <div v-if="sub.billing_cycle === 'permanent'" class="sub-card-expiry">
            <el-tag type="success" size="small">{{ zhCN.dashboard.permanentLabel }}</el-tag>
          </div>
          <div v-else-if="sub.remaining_days != null" class="sub-card-expiry">
            <el-tag :type="sub.remaining_days <= 0 ? 'danger' : sub.remaining_days <= 7 ? 'danger' : sub.remaining_days <= 30 ? 'warning' : 'info'" size="small">
              {{ sub.remaining_days <= 0 ? zhCN.subscription.expired : zhCN.subscription.daysLeft.replace('{days}', String(sub.remaining_days)) }}
            </el-tag>
            <span class="sub-card-expiry-date">{{ zhCN.dashboard.expires }}: {{ sub.expiry_date }}</span>
          </div>
          <div v-else-if="sub.next_payment_date && sub.billing_cycle !== 'once'" class="sub-card-expiry">
            <el-tag type="" size="small">{{ zhCN.dashboard.daysUntilBill.replace('{days}', String(daysUntil(sub.next_payment_date))) }}</el-tag>
          </div>
          <div v-if="sub.payment_method" class="sub-card-method">
            {{ sub.payment_method }}
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, nextTick, computed } from 'vue'
import * as echarts from 'echarts'
import { getDashboardSummary, getDashboardStats, getDashboardCalendar, getDashboardExpiring, getDashboardTrend, getDashboardBudget } from '../api/dashboard'
import { listSubscriptions } from '../api/subscriptions'
import { zhCN } from '../locales/zh-CN'

const summary = ref<Record<string, any>>({})
const stats = ref<any[]>([])
const calendar = ref<any[]>([])
const expiring = ref<any[]>([])
const subscriptions = ref<any[]>([])
const trend = ref<any[]>([])
const budget = ref<Record<string, any>>({})
const chartRef = ref<HTMLElement>()
const trendRef = ref<HTMLElement>()
let chartInstance: echarts.ECharts | null = null
let trendChart: echarts.ECharts | null = null

const activeCount = computed(() => zhCN.dashboard.activeCount.replace('{count}', String(subscriptions.value.length)))

function daysUntil(dateStr: string) {
  const d = new Date(dateStr)
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return Math.ceil((d.getTime() - today.getTime()) / (1000 * 60 * 60 * 24))
}

const isDark = ref(document.documentElement.classList.contains('dark'))

const resizeHandler = () => { chartInstance?.resize(); trendChart?.resize() }

onMounted(async () => {
  const [summaryRes, statsRes, calendarRes, expiringRes, subsRes, trendRes, budgetRes] = await Promise.all([
    getDashboardSummary().catch(() => ({ data: {} })),
    getDashboardStats().catch(() => ({ data: [] })),
    getDashboardCalendar().catch(() => ({ data: [] })),
    getDashboardExpiring().catch(() => ({ data: [] })),
    listSubscriptions({ is_active: true }).catch(() => ({ data: [] })),
    getDashboardTrend().catch(() => ({ data: [] })),
    getDashboardBudget().catch(() => ({ data: {} })),
  ])
  summary.value = summaryRes.data
  stats.value = statsRes.data
  calendar.value = calendarRes.data
  expiring.value = expiringRes.data
  subscriptions.value = subsRes.data
  trend.value = trendRes.data
  budget.value = budgetRes.data

  await nextTick()
  renderChart()
  renderTrend()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeHandler)
  chartInstance?.dispose()
  trendChart?.dispose()
})

function renderChart() {
  if (!chartRef.value) return
  chartInstance = echarts.init(chartRef.value)
  const palette = ['#4f46e5','#7c3aed','#06b6d4','#059669','#d97706','#dc2626','#ec4899','#6366f1','#0ea5e9','#10b981']
  const textColor = isDark.value ? '#e2e8f0' : '#334155'
  chartInstance.setOption({
    tooltip: { trigger: 'item', confine: true },
    legend: { bottom: 0, type: 'scroll', textStyle: { fontSize: 12, color: textColor } },
    series: [{
      type: 'pie',
      radius: ['45%', '72%'],
      center: ['50%', '45%'],
      itemStyle: { borderRadius: 6, borderColor: isDark.value ? '#1e293b' : '#fff', borderWidth: 2 },
      data: stats.value.map((s: any, i: number) => ({
        name: s.category_name,
        value: s.total_amount,
        itemStyle: { color: s.color || palette[i % palette.length] },
      })),
      label: { fontSize: 12, color: textColor },
    }],
  })
  window.addEventListener('resize', resizeHandler)
}

function renderTrend() {
  if (!trendRef.value || !trend.value.length) return
  trendChart = echarts.init(trendRef.value)
  const textColor = isDark.value ? '#94a3b8' : '#64748b'
  const splitColor = isDark.value ? '#1e293b' : '#f1f5f9'
  trendChart.setOption({
    tooltip: { trigger: 'axis', confine: true },
    xAxis: {
      type: 'category',
      data: trend.value.map((t: any) => t.month.slice(5)),
      axisLabel: { fontSize: 12, color: textColor },
      axisLine: { lineStyle: { color: isDark.value ? '#334155' : '#e2e8f0' } },
    },
    yAxis: {
      type: 'value',
      axisLabel: { fontSize: 12, color: textColor },
      splitLine: { lineStyle: { color: splitColor } },
    },
    series: [{
      type: 'bar',
      data: trend.value.map((t: any) => t.total),
      itemStyle: {
        borderRadius: [6, 6, 0, 0],
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: '#818cf8' },
          { offset: 1, color: '#4f46e5' },
        ]),
      },
      barWidth: '40%',
    }],
    grid: { left: 60, right: 20, top: 20, bottom: 30 },
  })
}

function formatCurrency(amount: number, currency: string) {
  const symbols: Record<string, string> = { CNY: '¥', USD: '$', EUR: '€', GBP: '£', JPY: '¥', HKD: '$' }
  return `${symbols[currency] || ''}${amount.toFixed(2)}`
}

function getFavicon(url: string) {
  try {
    const domain = new URL(url).hostname
    return `https://www.google.com/s2/favicons?domain=${domain}&sz=32`
  } catch {
    return ''
  }
}

function cycleLabel(cycle: string, num?: number, unit?: string) {
  if (cycle === 'permanent') return zhCN.subscription.permanent
  if (cycle === 'once') return zhCN.subscription.once
  if (cycle === 'custom' && num && unit) {
    const unitLabel = unit === 'year' ? zhCN.subscription.unitYear : zhCN.subscription.unitMonth
    return `每${num}${unitLabel}`
  }
  const labels: Record<string, string> = {
    monthly: zhCN.subscription.monthly,
    quarterly: zhCN.subscription.quarterly,
    yearly: zhCN.subscription.yearly,
  }
  return labels[cycle] || cycle
}
</script>

<style scoped>
/* Summary cards - gradient backgrounds */
.stat-card {
  position: relative;
  overflow: hidden;
  color: #fff;
  border: none !important;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 24px rgba(0,0,0,.15) !important;
}
.stat-gradient-blue {
  background: linear-gradient(135deg, #4f46e5, #818cf8) !important;
}
.stat-gradient-green {
  background: linear-gradient(135deg, #059669, #34d399) !important;
}
.stat-gradient-purple {
  background: linear-gradient(135deg, #7c3aed, #a78bfa) !important;
}
.stat-gradient-cyan {
  background: linear-gradient(135deg, #0891b2, #67e8f9) !important;
}
.stat-gradient-orange {
  background: linear-gradient(135deg, #d97706, #fbbf24) !important;
}
.stat-gradient-red {
  background: linear-gradient(135deg, #dc2626, #f87171) !important;
}

.stat-label {
  font-size: 13px;
  color: rgba(255,255,255,.75);
  font-weight: 500;
  margin-bottom: 8px;
}
.stat-value {
  font-size: 26px;
  font-weight: 700;
  color: #fff;
  line-height: 1.2;
}
.stat-value.muted {
  font-size: 14px;
  color: rgba(255,255,255,.6);
  font-weight: 500;
}
.text-danger { color: #fca5a5 !important; }
.summary-row .el-col { margin-bottom: 16px; }
.budget-warn { color: #fca5a5; font-size: 12px; margin-top: 4px; font-weight: 500; }
.budget-remain { color: rgba(255,255,255,.7); font-size: 12px; margin-top: 4px; }
.stat-change { font-size: 13px; font-weight: 600; margin-top: 4px; }
.change-up { color: #fca5a5; }
.change-down { color: #bbf7d0; }

/* Expiring */
.expiring-card { border: none; background: #fef2f2; }
.expiring-list { display: flex; flex-wrap: wrap; gap: 12px; }
.expiring-item {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 16px; background: #fff; border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,.06);
}
.expiring-name { font-weight: 600; font-size: 14px; color: #1e293b; }
.expiring-date { color: #94a3b8; font-size: 12px; }

/* Subscription cards */
.sub-cards .el-col { margin-bottom: 16px; }
.sub-card { height: 100%; border-radius: 12px; transition: transform 0.2s ease, box-shadow 0.2s ease; }
.sub-card:hover { transform: translateY(-2px); }
.sub-card.sub-expiring { border-left: 3px solid #ef4444; }
.sub-card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; gap: 8px; }
.sub-card-favicon { width: 22px; height: 22px; border-radius: 4px; flex-shrink: 0; }
.sub-card-name { font-weight: 700; font-size: 15px; color: #1e293b; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.sub-card-amount { font-size: 20px; font-weight: 700; color: #4f46e5; margin-bottom: 8px; }
.sub-card-cycle { font-size: 12px; color: #94a3b8; font-weight: 400; }
.sub-card-info { color: #64748b; font-size: 13px; margin-bottom: 6px; }
.sub-card-expiry { display: flex; align-items: center; gap: 8px; margin-top: 8px; }
.sub-card-expiry-date { color: #94a3b8; font-size: 12px; }
.sub-card-method { color: #94a3b8; font-size: 12px; margin-top: 6px; }

/* Dark mode */
html.dark .expiring-card { background: #1e1030; }
html.dark .expiring-item { background: #1e293b; }
html.dark .expiring-name { color: #e2e8f0; }
html.dark .sub-card-name { color: #e2e8f0; }
html.dark .sub-card-amount { color: #818cf8; }
html.dark .sub-card-info { color: #94a3b8; }
html.dark .sub-card.sub-expiring { border-left-color: #f87171; background: #1e1030; }
</style>