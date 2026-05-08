<template>
  <div v-loading="loading">
    <h2>{{ zhCN.dashboard.title }}</h2>

    <!-- Summary cards - modern style with top color bar -->
    <div class="stat-row">
      <el-card shadow="hover" class="stat-card stat-color-blue" :body-style="{ padding: '18px' }">
        <div class="stat-label">{{ zhCN.dashboard.monthlySpend }}</div>
        <div class="stat-value">{{ summary.monthly_total_currency }} {{ (summary.monthly_total ?? 0).toFixed(2) }}</div>
        <div class="stat-change" :class="summary.monthly_change >= 0 ? 'change-up' : 'change-down'">
          <template v-if="summary.monthly_change != null">{{ summary.monthly_change >= 0 ? '↑' : '↓' }} {{ Math.abs(summary.monthly_change).toFixed(2) }}</template>
          <span v-else>&nbsp;</span>
        </div>
      </el-card>
      <el-card shadow="hover" class="stat-card stat-color-green" :body-style="{ padding: '18px' }">
        <div class="stat-label">{{ zhCN.dashboard.nextMonthProjected }}</div>
        <div class="stat-value">{{ summary.next_month_projected_currency }} {{ (summary.next_month_projected ?? 0).toFixed(2) }}</div>
        <div class="stat-change"><span>&nbsp;</span></div>
      </el-card>
      <el-card shadow="hover" class="stat-card stat-color-purple" :body-style="{ padding: '18px' }">
        <div class="stat-label">{{ zhCN.dashboard.yearlySpend }}</div>
        <div class="stat-value">{{ summary.yearly_total_currency }} {{ (summary.yearly_total ?? 0).toFixed(2) }}</div>
        <div class="stat-change"><span>&nbsp;</span></div>
      </el-card>
      <el-card shadow="hover" class="stat-card stat-color-cyan" :body-style="{ padding: '18px' }">
        <div class="stat-label">{{ zhCN.dashboard.allSubscriptions }}</div>
        <div class="stat-value">{{ activeCount }}</div>
        <div class="stat-change"><span>&nbsp;</span></div>
      </el-card>
      <el-card shadow="hover" class="stat-card stat-card-budget" :class="budget.exceeded ? 'stat-color-red' : 'stat-color-orange'" :body-style="{ padding: '18px' }">
        <div class="stat-label">{{ zhCN.dashboard.budget }}</div>
        <div v-if="budget.budget" class="budget-info">
          <div class="stat-value" :class="{ 'text-danger': budget.exceeded }">{{ budget.spent.toFixed(2) }} / {{ budget.budget.toFixed(2) }}</div>
          <el-progress :percentage="Math.min(budget.spent / budget.budget * 100, 100)" :color="budget.exceeded ? '#ef4444' : '#6366f1'" :stroke-width="6" style="margin-top: 6px" :show-text="false" />
          <div v-if="budget.exceeded" class="budget-warn">{{ zhCN.dashboard.budgetExceeded }}</div>
          <div v-else class="budget-remain">{{ zhCN.dashboard.budgetRemaining }}: {{ budget.remaining?.toFixed(2) }}</div>
        </div>
        <div v-else class="stat-value muted">{{ zhCN.dashboard.budgetNotSet }}</div>
      </el-card>
    </div>

    <!-- Expiring soon alert -->
    <div v-if="expiring.length" class="expiring-strip">
      <span class="expiring-strip-label">{{ zhCN.dashboard.expiringSoon }}</span>
      <span v-for="item in expiring" :key="item.id" class="expiring-chip">
        <span class="expiring-chip-name">{{ item.name }}</span>
        <el-tag :type="item.remaining_days <= 7 ? 'danger' : 'warning'" size="small">
          {{ item.remaining_days <= 0 ? zhCN.subscription.expired : zhCN.subscription.daysLeft.replace('{days}', String(item.remaining_days)) }}
        </el-tag>
      </span>
    </div>

    <!-- Charts row: trend + pie side by side -->
    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :span="12" :xs="24">
        <el-card shadow="hover">
          <template #header>{{ zhCN.dashboard.monthlyTrend }}</template>
          <div ref="trendRef" style="height: 200px"></div>
        </el-card>
      </el-col>
      <el-col :span="12" :xs="24">
        <el-card shadow="hover">
          <template #header>{{ zhCN.dashboard.categoryBreakdown }}</template>
          <div ref="chartRef" style="height: 200px"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Upcoming payments -->
    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :span="24">
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

    <!-- Advisor tips -->
    <el-card v-if="tips.length" shadow="hover" style="margin-top: 16px">
      <template #header>{{ zhCN.advisor.title }}</template>
      <div class="tips-grid">
        <el-alert
          v-for="tip in tips"
          :key="tip.type + tip.subscription_id"
          :type="tipType(tip.type)"
          :title="tip.subscription_name"
          :description="tip.message"
          show-icon
          :closable="false"
          class="tip-alert"
        >
          <template v-if="tip.savings" #default>
            <span class="tip-savings">{{ zhCN.advisor.cancelToSave }} {{ tip.currency }} {{ tip.savings.toFixed(2) }}{{ tip.type === 'cancel_to_save' ? zhCN.advisor.perYear : '' }}</span>
          </template>
        </el-alert>
      </div>
    </el-card>

    <!-- Subscription cards overview -->
    <h3 style="margin-top: 24px">{{ zhCN.dashboard.allSubscriptions }}</h3>
    <el-empty v-if="!subscriptions.length" :description="zhCN.dashboard.noSubscriptions" />
    <el-row v-else :gutter="16" class="sub-cards">
      <el-col v-for="sub in subscriptions.slice(0, 8)" :key="sub.id" :xs="24" :sm="12" :md="8" :lg="6">
        <el-card shadow="hover" class="sub-card" :class="{ 'sub-expiring': sub.remaining_days != null && sub.remaining_days <= 30 }">
          <div class="sub-card-header">
            <ServiceIcon :name="sub.name" :url="sub.url" :category-color="sub.category_color" :size="36" />
            <span class="sub-card-name">{{ sub.name }}</span>
            <el-tag v-if="sub.category_name" :color="sub.category_color" size="small" class="sub-card-tag">
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
    <div v-if="subscriptions.length > 8" style="text-align: center; margin-top: 8px">
      <router-link to="/subscriptions" class="view-all-link">{{ zhCN.dashboard.viewAll }} →</router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, nextTick, computed } from 'vue'
import * as echarts from 'echarts'
import { getDashboardSummary, getDashboardStats, getDashboardCalendar, getDashboardExpiring, getDashboardTrend, getDashboardBudget } from '../api/dashboard'
import { listSubscriptions } from '../api/subscriptions'
import { getAdvisorTips } from '../api/analytics'
import { zhCN } from '../locales/zh-CN'
import { formatCurrency } from '../utils/format'
import ServiceIcon from '../components/ServiceIcon.vue'

const loading = ref(true)
const summary = ref<Record<string, any>>({})
const stats = ref<any[]>([])
const calendar = ref<any[]>([])
const expiring = ref<any[]>([])
const subscriptions = ref<any[]>([])
const trend = ref<any[]>([])
const budget = ref<Record<string, any>>({})
const tips = ref<any[]>([])
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

  // Advisor tips (non-blocking)
  getAdvisorTips().then(res => { tips.value = res.data }).catch(() => {})

  await nextTick()
  renderChart()
  renderTrend()
  loading.value = false
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

function tipType(type: string): string {
  const map: Record<string, string> = {
    price_increase: 'error',
    duplicate_service: 'warning',
    near_expiry: 'warning',
    cancel_to_save: 'info',
  }
  return map[type] || 'info'
}
</script>

<style scoped>
/* Summary cards - modern style with top color bar */
.stat-row {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 16px;
  align-items: stretch;
}
.stat-card {
  flex: 1;
  min-width: 160px;
  position: relative;
  overflow: hidden;
  border: none !important;
  border-top: 4px solid transparent !important;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  background: var(--surface, #fff) !important;
}
.stat-card-budget {
  flex: 0 0 220px;
  min-width: 220px;
}
.stat-card:hover {
  transform: translateY(-3px);
}
.stat-color-blue { border-top-color: #6366f1 !important; }
.stat-color-green { border-top-color: #10b981 !important; }
.stat-color-purple { border-top-color: #8b5cf6 !important; }
.stat-color-cyan { border-top-color: #06b6d4 !important; }
.stat-color-orange { border-top-color: #f59e0b !important; }
.stat-color-red { border-top-color: #ef4444 !important; }

.stat-card:hover.stat-color-blue { box-shadow: 0 8px 24px rgba(99,102,241,.18) !important; }
.stat-card:hover.stat-color-green { box-shadow: 0 8px 24px rgba(16,185,129,.18) !important; }
.stat-card:hover.stat-color-purple { box-shadow: 0 8px 24px rgba(139,92,246,.18) !important; }
.stat-card:hover.stat-color-cyan { box-shadow: 0 8px 24px rgba(6,182,212,.18) !important; }
.stat-card:hover.stat-color-orange { box-shadow: 0 8px 24px rgba(245,158,11,.18) !important; }
.stat-card:hover.stat-color-red { box-shadow: 0 8px 24px rgba(239,68,68,.18) !important; }

.stat-label {
  font-size: 13px;
  color: var(--text-muted, #94a3b8);
  font-weight: 600;
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: .5px;
}
.stat-value {
  font-size: 28px;
  font-weight: 800;
  color: var(--text-primary, #0f172a);
  line-height: 1.1;
  letter-spacing: -0.5px;
}
.stat-value.muted {
  font-size: 14px;
  color: var(--text-muted, #94a3b8);
  font-weight: 500;
}
.text-danger { color: #ef4444 !important; }
.budget-warn { color: #ef4444; font-size: 12px; margin-top: 4px; font-weight: 600; }
.budget-remain { color: var(--text-muted, #94a3b8); font-size: 12px; margin-top: 4px; }
.stat-change { font-size: 13px; font-weight: 600; margin-top: 4px; min-height: 20px; }
.change-up { color: #ef4444; }
.change-down { color: #10b981; }

/* Expiring strip */
.expiring-strip {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 16px;
  padding: 10px 14px;
  background: #fef2f2;
  border-radius: 12px;
  font-size: 13px;
  border: 1px solid #fecaca;
}
.expiring-strip-label {
  color: #ef4444;
  font-weight: 600;
  font-size: 13px;
  margin-right: 4px;
}
.expiring-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 2px rgba(0,0,0,.05);
}
.expiring-chip-name { font-weight: 600; color: #1e293b; }

/* Subscription cards */
.sub-cards .el-col { margin-bottom: 16px; }
.sub-card { height: 100%; border-radius: 16px !important; transition: transform 0.2s ease, box-shadow 0.2s ease; border: 1px solid rgba(0,0,0,.04) !important; }
.sub-card:hover { transform: translateY(-3px); box-shadow: 0 8px 24px rgba(99,102,241,.1) !important; }
.sub-card.sub-expiring { border-left: 3px solid #ef4444 !important; }
.sub-card-header { display: flex; align-items: center; margin-bottom: 10px; gap: 10px; }
.sub-card-name { font-weight: 700; font-size: 15px; color: var(--text-primary, #0f172a); flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.sub-card-tag { margin-left: auto; color: #fff !important; border: none; flex-shrink: 0; }
.sub-card-amount { font-size: 22px; font-weight: 800; color: var(--primary, #6366f1); margin-bottom: 8px; letter-spacing: -.3px; }
.sub-card-cycle { font-size: 12px; color: var(--text-muted, #94a3b8); font-weight: 400; }
.sub-card-info { color: var(--text-secondary, #64748b); font-size: 13px; margin-bottom: 6px; }
.sub-card-expiry { display: flex; align-items: center; gap: 8px; margin-top: 8px; }
.sub-card-expiry-date { color: var(--text-muted, #94a3b8); font-size: 12px; }
.sub-card-method { color: var(--text-muted, #94a3b8); font-size: 12px; margin-top: 6px; }

/* View all link */
.view-all-link {
  color: var(--primary, #6366f1); font-size: 14px; font-weight: 500;
  text-decoration: none; transition: color 0.2s;
}
.view-all-link:hover { color: var(--primary-dark, #4f46e5); }

/* Advisor tips */
.tips-grid { display: flex; flex-wrap: wrap; gap: 12px; }
.tip-alert { flex: 1; min-width: 260px; }
.tip-savings { font-size: 13px; color: var(--primary, #6366f1); font-weight: 600; }

/* Dark mode */
html.dark .expiring-strip { background: #1e1030; border-color: #5b1a3a; }
html.dark .expiring-chip { background: var(--surface-secondary, #1e293b); }
html.dark .expiring-chip-name { color: #e2e8f0; }
html.dark .sub-card { border-color: rgba(255,255,255,.06) !important; }
html.dark .sub-card:hover { box-shadow: 0 8px 24px rgba(129,140,248,.1) !important; }
html.dark .sub-card.sub-expiring { border-left-color: #f87171 !important; background: #1e1030; }
html.dark .sub-card-amount { color: #818cf8; }
html.dark .view-all-link { color: #818cf8; }
html.dark .view-all-link:hover { color: #a78bfa; }
</style>