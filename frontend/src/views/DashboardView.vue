<template>
  <div>
    <h2>{{ zhCN.dashboard.title }}</h2>

    <!-- Summary cards -->
    <el-row :gutter="20" class="summary-row">
      <el-col :span="6" :xs="12">
        <el-card shadow="hover" class="stat-card stat-blue">
          <div class="stat-label">{{ zhCN.dashboard.monthlySpend }}</div>
          <div class="stat-value">{{ summary.monthly_total_currency }} {{ (summary.monthly_total ?? 0).toFixed(2) }}</div>
        </el-card>
      </el-col>
      <el-col :span="6" :xs="12">
        <el-card shadow="hover" class="stat-card stat-green">
          <div class="stat-label">{{ zhCN.dashboard.nextMonthProjected }}</div>
          <div class="stat-value">{{ summary.next_month_projected_currency }} {{ (summary.next_month_projected ?? 0).toFixed(2) }}</div>
        </el-card>
      </el-col>
      <el-col :span="6" :xs="12">
        <el-card shadow="hover" class="stat-card stat-purple">
          <div class="stat-label">{{ zhCN.dashboard.allSubscriptions }}</div>
          <div class="stat-value">{{ activeCount }}</div>
        </el-card>
      </el-col>
      <el-col :span="6" :xs="12">
        <el-card shadow="hover" class="stat-card" :class="budget.exceeded ? 'stat-red' : 'stat-orange'">
          <div class="stat-label">{{ zhCN.dashboard.budget }}</div>
          <div v-if="budget.budget" class="budget-info">
            <div class="stat-value" :class="{ 'text-danger': budget.exceeded }">{{ budget.spent.toFixed(2) }} / {{ budget.budget.toFixed(2) }}</div>
            <el-progress :percentage="Math.min(budget.spent / budget.budget * 100, 100)" :color="budget.exceeded ? '#ef4444' : '#4f46e5'" :stroke-width="6" style="margin-top: 6px" :show-text="false" />
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
            <span class="sub-card-name">{{ sub.name }}</span>
            <el-tag v-if="sub.category_name" :color="sub.category_color" size="small" style="color: #fff; border: none">
              {{ sub.category_name }}
            </el-tag>
          </div>
          <div class="sub-card-amount">{{ formatCurrency(sub.amount, sub.currency) }}<span class="sub-card-cycle"> /{{ cycleLabel(sub.billing_cycle, sub.billing_cycle_num, sub.billing_cycle_unit) }}</span></div>
          <div class="sub-card-info">
            <span v-if="sub.billing_cycle === 'once'">{{ zhCN.dashboard.permanentPurchase }}</span>
            <span v-else>{{ zhCN.dashboard.nextBill }}: {{ sub.next_payment_date || '--' }}</span>
          </div>
          <div v-if="sub.remaining_days != null" class="sub-card-expiry">
            <el-tag :type="sub.remaining_days <= 0 ? 'danger' : sub.remaining_days <= 7 ? 'danger' : sub.remaining_days <= 30 ? 'warning' : 'info'" size="small">
              {{ sub.remaining_days <= 0 ? zhCN.subscription.expired : zhCN.subscription.daysLeft.replace('{days}', String(sub.remaining_days)) }}
            </el-tag>
            <span class="sub-card-expiry-date">{{ zhCN.dashboard.expires }}: {{ sub.expiry_date }}</span>
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
  chartInstance.setOption({
    tooltip: { trigger: 'item', confine: true },
    legend: { bottom: 0, type: 'scroll', textStyle: { fontSize: 12 } },
    series: [{
      type: 'pie',
      radius: ['45%', '72%'],
      center: ['50%', '45%'],
      itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
      data: stats.value.map((s: any, i: number) => ({
        name: s.category_name,
        value: s.total_amount,
        itemStyle: { color: palette[i % palette.length] },
      })),
      label: { fontSize: 12 },
    }],
  })
  window.addEventListener('resize', resizeHandler)
}

function renderTrend() {
  if (!trendRef.value || !trend.value.length) return
  trendChart = echarts.init(trendRef.value)
  trendChart.setOption({
    tooltip: { trigger: 'axis', confine: true },
    xAxis: {
      type: 'category',
      data: trend.value.map((t: any) => t.month.slice(5)),
      axisLabel: { fontSize: 12, color: '#94a3b8' },
      axisLine: { lineStyle: { color: '#e2e8f0' } },
    },
    yAxis: {
      type: 'value',
      axisLabel: { fontSize: 12, color: '#94a3b8' },
      splitLine: { lineStyle: { color: '#f1f5f9' } },
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

function cycleLabel(cycle: string, num?: number, unit?: string) {
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
/* Stat cards */
.stat-card {
  position: relative;
  overflow: hidden;
  padding-top: 4px;
}
.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
}
.stat-blue::before { background: linear-gradient(90deg, #4f46e5, #818cf8); }
.stat-green::before { background: linear-gradient(90deg, #059669, #34d399); }
.stat-purple::before { background: linear-gradient(90deg, #7c3aed, #a78bfa); }
.stat-orange::before { background: linear-gradient(90deg, #d97706, #fbbf24); }
.stat-red::before { background: linear-gradient(90deg, #dc2626, #f87171); }
.stat-label {
  font-size: 13px;
  color: #64748b;
  font-weight: 500;
  margin-bottom: 8px;
}
.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #1e293b;
  line-height: 1.2;
}
.stat-value.muted {
  font-size: 14px;
  color: #94a3b8;
  font-weight: 500;
}
.text-danger { color: #ef4444 !important; }
.summary-row .el-col { margin-bottom: 20px; }
.budget-warn { color: #ef4444; font-size: 12px; margin-top: 4px; font-weight: 500; }
.budget-remain { color: #94a3b8; font-size: 12px; margin-top: 4px; }

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
.sub-card { height: 100%; border-radius: 12px; }
.sub-card.sub-expiring { background: #fef2f2; }
.sub-card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.sub-card-name { font-weight: 700; font-size: 15px; color: #1e293b; }
.sub-card-amount { font-size: 20px; font-weight: 700; color: #4f46e5; margin-bottom: 8px; }
.sub-card-cycle { font-size: 12px; color: #94a3b8; font-weight: 400; }
.sub-card-info { color: #64748b; font-size: 13px; margin-bottom: 6px; }
.sub-card-expiry { display: flex; align-items: center; gap: 8px; margin-top: 8px; }
.sub-card-expiry-date { color: #94a3b8; font-size: 12px; }
.sub-card-method { color: #94a3b8; font-size: 12px; margin-top: 6px; }
</style>
