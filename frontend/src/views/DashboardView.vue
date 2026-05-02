<template>
  <div>
    <h2>{{ zhCN.dashboard.title }}</h2>

    <!-- Summary cards -->
    <el-row :gutter="16" class="summary-row">
      <el-col :span="6" :xs="12">
        <el-card shadow="hover">
          <template #header>{{ zhCN.dashboard.monthlySpend }}</template>
          <div class="amount">{{ summary.monthly_total_currency }} {{ (summary.monthly_total ?? 0).toFixed(2) }}</div>
        </el-card>
      </el-col>
      <el-col :span="6" :xs="12">
        <el-card shadow="hover">
          <template #header>{{ zhCN.dashboard.nextMonthProjected }}</template>
          <div class="amount">{{ summary.next_month_projected_currency }} {{ (summary.next_month_projected ?? 0).toFixed(2) }}</div>
        </el-card>
      </el-col>
      <el-col :span="6" :xs="12">
        <el-card shadow="hover">
          <template #header>{{ zhCN.dashboard.allSubscriptions }}</template>
          <div class="amount">{{ activeCount }}</div>
        </el-card>
      </el-col>
      <el-col :span="6" :xs="12">
        <el-card shadow="hover" :class="{ 'budget-exceeded': budget.exceeded }">
          <template #header>{{ zhCN.dashboard.budget }}</template>
          <div v-if="budget.budget" class="budget-info">
            <div class="amount" :class="{ 'text-danger': budget.exceeded }">{{ budget.spent.toFixed(2) }} / {{ budget.budget.toFixed(2) }}</div>
            <el-progress :percentage="Math.min(budget.spent / budget.budget * 100, 100)" :color="budget.exceeded ? '#f56c6c' : '#409eff'" :stroke-width="8" style="margin-top: 8px" />
            <div v-if="budget.exceeded" class="budget-warn">{{ zhCN.dashboard.budgetExceeded }}</div>
            <div v-else class="budget-remain">{{ zhCN.dashboard.budgetRemaining }}: {{ budget.remaining?.toFixed(2) }}</div>
          </div>
          <div v-else class="amount muted">{{ zhCN.dashboard.budgetNotSet }}</div>
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
          <div class="sub-card-amount">{{ formatCurrency(sub.amount, sub.currency) }}<span class="sub-card-cycle"> /{{ cycleLabel(sub.billing_cycle) }}</span></div>
          <div class="sub-card-info">
            <span>{{ zhCN.dashboard.nextBill }}: {{ sub.next_payment_date }}</span>
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

function renderTrend() {
  if (!trendRef.value || !trend.value.length) return
  trendChart = echarts.init(trendRef.value)
  trendChart.setOption({
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: trend.value.map((t: any) => t.month.slice(5)),
      axisLabel: { fontSize: 12 },
    },
    yAxis: { type: 'value', axisLabel: { fontSize: 12 } },
    series: [{
      type: 'bar',
      data: trend.value.map((t: any) => t.total),
      itemStyle: { color: '#409eff', borderRadius: [4, 4, 0, 0] },
    }],
    grid: { left: 60, right: 20, top: 20, bottom: 30 },
  })
}

function formatCurrency(amount: number, currency: string) {
  const symbols: Record<string, string> = { CNY: '¥', USD: '$', EUR: '€', GBP: '£', JPY: '¥', HKD: '$' }
  return `${symbols[currency] || ''}${amount.toFixed(2)}`
}

function cycleLabel(cycle: string) {
  const labels: Record<string, string> = {
    monthly: zhCN.subscription.monthly,
    quarterly: zhCN.subscription.quarterly,
    yearly: zhCN.subscription.yearly,
  }
  return labels[cycle] || cycle
}
</script>

<style scoped>
.amount {
  font-size: 22px;
  font-weight: 600;
  color: #409eff;
}
.amount.muted {
  color: #909399;
  font-size: 14px;
}
.text-danger {
  color: #f56c6c !important;
}
.summary-row .el-col {
  margin-bottom: 16px;
}
.budget-exceeded {
  border: 1px solid #fde2e2;
}
.budget-warn {
  color: #f56c6c;
  font-size: 12px;
  margin-top: 4px;
}
.budget-remain {
  color: #909399;
  font-size: 12px;
  margin-top: 4px;
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
.expiring-name { font-weight: 500; }
.expiring-date { color: #909399; font-size: 12px; }
.sub-cards .el-col { margin-bottom: 16px; }
.sub-card { height: 100%; }
.sub-card.sub-expiring { border: 1px solid #fde2e2; }
.sub-card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.sub-card-name { font-weight: 600; font-size: 15px; }
.sub-card-amount { font-size: 18px; font-weight: 600; color: #409eff; margin-bottom: 8px; }
.sub-card-cycle { font-size: 12px; color: #909399; font-weight: 400; }
.sub-card-info { color: #606266; font-size: 13px; margin-bottom: 6px; }
.sub-card-expiry { display: flex; align-items: center; gap: 8px; margin-top: 6px; }
.sub-card-expiry-date { color: #909399; font-size: 12px; }
.sub-card-method { color: #909399; font-size: 12px; margin-top: 6px; }
</style>
