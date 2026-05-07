<template>
  <div>
    <div class="page-header">
      <h2>{{ zhCN.subscription.title }}</h2>
      <el-button type="primary" @click="showForm()">
        {{ zhCN.subscription.addNew }}
      </el-button>
    </div>

    <!-- Filters -->
    <div class="filter-bar">
      <el-input v-model="searchText" :placeholder="zhCN.common.search" clearable style="width: 200px" @input="fetchList" />
      <el-select v-model="filterCategory" :placeholder="zhCN.subscription.category" clearable style="width: 140px" @change="fetchList">
        <el-option :label="zhCN.subscription.filterAll" :value="null" />
        <el-option v-for="cat in categoryStore.categories" :key="cat.id" :label="cat.name" :value="cat.id" />
      </el-select>
      <el-select v-model="filterCurrency" :placeholder="zhCN.subscription.currency" clearable style="width: 100px" @change="fetchList">
        <el-option :label="zhCN.subscription.filterAll" :value="null" />
        <el-option label="CNY" value="CNY" />
        <el-option label="USD" value="USD" />
        <el-option label="EUR" value="EUR" />
        <el-option label="GBP" value="GBP" />
        <el-option label="JPY" value="JPY" />
        <el-option label="HKD" value="HKD" />
      </el-select>
      <div v-if="selectedIds.length" class="batch-actions">
        <span class="selected-info">{{ zhCN.subscription.selected.replace('{count}', String(selectedIds.length)) }}</span>
        <el-button size="small" type="success" @click="handleBatchToggle(true)">{{ zhCN.subscription.batchEnable }}</el-button>
        <el-button size="small" type="warning" @click="handleBatchToggle(false)">{{ zhCN.subscription.batchDisable }}</el-button>
        <el-button size="small" @click="showBatchCategory = true">{{ zhCN.subscription.batchSetCategory }}</el-button>
        <el-button size="small" @click="showBatchExpiry = true">{{ zhCN.subscription.batchSetExpiry }}</el-button>
        <el-button size="small" type="danger" @click="handleBatchDelete">{{ zhCN.subscription.batchDelete }}</el-button>
      </div>
    </div>

    <el-table :data="subscriptionStore.subscriptions" v-loading="subscriptionStore.loading" stripe @selection-change="handleSelectionChange">
      <el-table-column type="selection" width="40" />
      <el-table-column prop="name" :label="zhCN.subscription.name">
        <template #default="{ row }">
          <div style="display: flex; align-items: center; gap: 8px">
            <img v-if="row.url" :src="getFavicon(row.url)" class="sub-favicon" alt="" @error="($event.target as HTMLImageElement).style.display='none'" />
            <span>{{ row.name }}</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="amount" :label="zhCN.subscription.amount">
        <template #default="{ row }">
          {{ formatCurrency(row.amount, row.currency) }}
          <span v-if="row.intro_amount != null && row.intro_months != null" class="intro-hint">({{ formatCurrency(row.intro_amount, row.currency) }}×{{ row.intro_months }}{{ zhCN.subscription.unitMonth }})</span>
        </template>
      </el-table-column>
      <el-table-column prop="billing_cycle" :label="zhCN.subscription.cycle">
        <template #default="{ row }">{{ cycleLabel(row.billing_cycle, row.billing_cycle_num, row.billing_cycle_unit) }}</template>
      </el-table-column>
      <el-table-column prop="next_payment_date" :label="zhCN.subscription.nextPayment">
        <template #default="{ row }">{{ (row.billing_cycle === 'once' || row.billing_cycle === 'permanent') ? zhCN.dashboard.permanentPurchase : (row.next_payment_date || '--') }}</template>
      </el-table-column>
      <el-table-column v-if="hasExpiring" :label="zhCN.subscription.remainingDays" width="120">
        <template #default="{ row }">
          <el-tag v-if="row.billing_cycle === 'permanent'" type="success" size="small">{{ zhCN.dashboard.permanentLabel }}</el-tag>
          <el-tag v-else-if="row.remaining_days != null" :type="row.remaining_days <= 0 ? 'danger' : row.remaining_days <= 7 ? 'danger' : row.remaining_days <= 30 ? 'warning' : 'info'" size="small">
            {{ row.remaining_days <= 0 ? zhCN.subscription.expired : zhCN.subscription.daysLeft.replace('{days}', String(row.remaining_days)) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="payment_method" :label="zhCN.subscription.paymentMethod" width="120">
        <template #default="{ row }">{{ row.payment_method || '-' }}</template>
      </el-table-column>
      <el-table-column prop="category_name" :label="zhCN.subscription.category">
        <template #default="{ row }">
          <el-tag v-if="row.category_name" :color="row.category_color" style="color: #fff">{{ row.category_name }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="is_active" :label="zhCN.subscription.active" width="80">
        <template #default="{ row }">
          <el-switch v-model="row.is_active" @change="handleToggle(row)" />
        </template>
      </el-table-column>
      <el-table-column label="" width="120">
        <template #default="{ row }">
          <el-button size="small" @click="showForm(row)">{{ zhCN.common.edit }}</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">{{ zhCN.common.delete }}</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="formVisible" :title="editingId ? zhCN.common.edit : zhCN.subscription.addNew" width="500px">
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="100px">
        <el-form-item :label="zhCN.subscription.name" prop="name"><el-input v-model="form.name" /></el-form-item>
        <el-form-item :label="zhCN.subscription.amount" prop="amount"><el-input-number v-model="form.amount" :min="0" :precision="2" /></el-form-item>
        <el-form-item :label="zhCN.subscription.currency">
          <el-select v-model="form.currency">
            <el-option label="CNY ¥" value="CNY" /><el-option label="USD $" value="USD" />
            <el-option label="EUR €" value="EUR" /><el-option label="GBP £" value="GBP" />
            <el-option label="JPY ¥" value="JPY" /><el-option label="HKD $" value="HKD" />
          </el-select>
        </el-form-item>
        <el-form-item :label="zhCN.subscription.cycle">
          <div class="cycle-group">
            <el-select v-model="form.billing_cycle" style="width: 140px" @change="onCycleChange">
              <el-option :label="zhCN.subscription.monthly" value="monthly" />
              <el-option :label="zhCN.subscription.quarterly" value="quarterly" />
              <el-option :label="zhCN.subscription.yearly" value="yearly" />
              <el-option :label="zhCN.subscription.permanent" value="permanent" />
              <el-option :label="zhCN.subscription.once" value="once" />
              <el-option :label="zhCN.subscription.custom" value="custom" />
            </el-select>
            <template v-if="form.billing_cycle === 'custom'">
              <el-input-number v-model="form.billing_cycle_num" :min="1" :max="99" style="width: 100px" />
              <el-select v-model="form.billing_cycle_unit" style="width: 80px">
                <el-option :label="zhCN.subscription.unitMonth" value="month" />
                <el-option :label="zhCN.subscription.unitYear" value="year" />
              </el-select>
            </template>
          </div>
          <div v-if="form.billing_cycle === 'custom'" class="cycle-tip">{{ zhCN.subscription.customCycleExample }}</div>
        </el-form-item>
        <el-form-item :label="zhCN.subscription.firstPayment" prop="first_payment_date"><el-date-picker v-model="form.first_payment_date" type="date" value-format="YYYY-MM-DD" /></el-form-item>
        <el-form-item :label="zhCN.subscription.category">
          <el-select v-model="form.category_id" clearable>
            <el-option v-for="cat in categoryStore.categories" :key="cat.id" :label="cat.name" :value="cat.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="zhCN.subscription.notes"><el-input v-model="form.notes" type="textarea" :rows="2" /></el-form-item>
        <el-form-item :label="zhCN.subscription.url"><el-input v-model="form.url" placeholder="https://..." /></el-form-item>
        <el-form-item :label="zhCN.subscription.expiryDate"><el-date-picker v-model="form.expiry_date" type="date" value-format="YYYY-MM-DD" clearable /></el-form-item>
        <el-form-item :label="zhCN.subscription.paymentMethod"><el-input v-model="form.payment_method" placeholder="如：招商银行信用卡" /></el-form-item>

        <!-- Intro pricing -->
        <el-form-item :label="zhCN.subscription.introAmount">
          <div class="intro-group">
            <el-input-number v-model="form.intro_amount" :precision="2" :placeholder="zhCN.subscription.introAmountPlaceholder" :controls="false" style="width: 140px" />
            <span class="intro-x">×</span>
            <el-input-number v-model="form.intro_months" :min="1" :max="999" :placeholder="zhCN.subscription.introMonthsPlaceholder" :controls="false" style="width: 120px" />
            <span class="intro-unit">{{ zhCN.subscription.unitMonth }}</span>
          </div>
          <div v-if="form.intro_amount != null && form.intro_months != null && form.intro_amount !== 0 && form.intro_months !== 0" class="cycle-tip">
            {{ zhCN.subscription.introTip.replace('{months}', String(form.intro_months)).replace('{amount}', formatCurrency(form.intro_amount, form.currency)) }}
          </div>
        </el-form-item>

        <el-form-item :label="zhCN.subscription.notify"><el-switch v-model="form.notify" /></el-form-item>

        <!-- Price history -->
        <el-collapse v-if="editingId" style="margin-top: 12px">
          <el-collapse-item :title="zhCN.subscription.priceHistory">
            <div v-if="priceHistory.length > 1" ref="priceChartRef" style="height: 200px; margin-bottom: 12px"></div>
            <el-timeline v-if="priceHistory.length">
              <el-timeline-item v-for="h in priceHistory" :key="h.id" :timestamp="h.created_at">
                {{ formatCurrency(h.old_amount, h.old_currency) }} → {{ formatCurrency(h.new_amount, h.new_currency) }}
              </el-timeline-item>
            </el-timeline>
            <div v-else style="color: #909399; font-size: 13px">{{ zhCN.subscription.noPriceHistory }}</div>
          </el-collapse-item>
        </el-collapse>
      </el-form>
      <template #footer>
        <el-button @click="formVisible = false">{{ zhCN.common.cancel }}</el-button>
        <el-button type="primary" @click="handleSubmit">{{ zhCN.common.save }}</el-button>
      </template>
    </el-dialog>

    <!-- Batch set category dialog -->
    <el-dialog v-model="showBatchCategory" :title="zhCN.subscription.batchSetCategory" width="400px">
      <el-select v-model="batchCategoryId" :placeholder="zhCN.subscription.batchCategoryPlaceholder" clearable style="width: 100%">
        <el-option v-for="cat in categoryStore.categories" :key="cat.id" :label="cat.name" :value="cat.id" />
      </el-select>
      <template #footer>
        <el-button @click="showBatchCategory = false">{{ zhCN.common.cancel }}</el-button>
        <el-button type="primary" @click="handleBatchCategory">{{ zhCN.common.save }}</el-button>
      </template>
    </el-dialog>

    <!-- Batch set expiry date dialog -->
    <el-dialog v-model="showBatchExpiry" :title="zhCN.subscription.batchSetExpiry" width="400px">
      <el-date-picker v-model="batchExpiryDate" type="date" :placeholder="zhCN.subscription.batchExpiryPlaceholder" value-format="YYYY-MM-DD" style="width: 100%" />
      <template #footer>
        <el-button @click="showBatchExpiry = false">{{ zhCN.common.cancel }}</el-button>
        <el-button type="primary" @click="handleBatchExpiry">{{ zhCN.common.save }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive, computed, nextTick, onBeforeUnmount } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import * as echarts from 'echarts'
import { useSubscriptionStore } from '../stores/subscription'
import { useCategoryStore } from '../stores/category'
import { zhCN } from '../locales/zh-CN'
import { patchSubscription, batchDelete, batchToggle, getPriceHistory } from '../api/subscriptions'
import type { Subscription } from '../types/subscription'

const subscriptionStore = useSubscriptionStore()
const categoryStore = useCategoryStore()

const formVisible = ref(false)
const editingId = ref<number | null>(null)
const priceHistory = ref<any[]>([])
const priceChartRef = ref<HTMLElement>()
let priceChartInstance: echarts.ECharts | null = null
const searchText = ref('')
const filterCategory = ref<number | null>(null)
const filterCurrency = ref<string | null>(null)
const selectedIds = ref<number[]>([])
const showBatchCategory = ref(false)
const batchCategoryId = ref<number | null>(null)
const showBatchExpiry = ref(false)
const batchExpiryDate = ref('')
const formRef = ref<FormInstance>()

const formRules = reactive<FormRules>({
  name: [{ required: true, message: zhCN.subscription.nameRequired, trigger: 'blur' }],
  amount: [{ required: true, message: zhCN.subscription.amountRequired, trigger: 'blur' }],
  first_payment_date: [{ required: true, message: zhCN.subscription.firstPaymentRequired, trigger: 'change' }],
})

const hasExpiring = computed(() => subscriptionStore.subscriptions.some((s: any) => s.remaining_days != null))

const defaultForm = {
  name: '', amount: 0, currency: 'CNY', billing_cycle: 'monthly',
  billing_cycle_num: 1, billing_cycle_unit: 'month',
  first_payment_date: '',
  category_id: null as number | null, notes: null as string | null, url: null as string | null,
  expiry_date: null as string | null, payment_method: null as string | null,
  intro_amount: null as number | null, intro_months: null as number | null,
  notify: true,
}
const form = reactive({ ...defaultForm })

onMounted(() => Promise.all([fetchList(), categoryStore.fetchList()]))

async function fetchList() {
  const params: Record<string, any> = {}
  if (searchText.value) params.search = searchText.value
  if (filterCategory.value != null) params.category_id = filterCategory.value
  if (filterCurrency.value) params.currency = filterCurrency.value
  await subscriptionStore.fetchList(params)
}

function handleSelectionChange(rows: Subscription[]) {
  selectedIds.value = rows.map((r) => r.id)
}

function onCycleChange() {
  if (form.billing_cycle !== 'custom') {
    form.billing_cycle_num = 1
    form.billing_cycle_unit = 'month'
  }
}

async function showForm(sub?: Subscription) {
  if (sub) {
    editingId.value = sub.id
    Object.assign(form, {
      name: sub.name, amount: sub.amount, currency: sub.currency, billing_cycle: sub.billing_cycle,
      billing_cycle_num: sub.billing_cycle_num || 1, billing_cycle_unit: sub.billing_cycle_unit || 'month',
      first_payment_date: sub.first_payment_date, category_id: sub.category_id, notes: sub.notes,
      url: sub.url, expiry_date: sub.expiry_date, payment_method: sub.payment_method, notify: sub.notify,
      intro_amount: sub.intro_amount, intro_months: sub.intro_months,
    })
    try {
      const res = await getPriceHistory(sub.id)
      priceHistory.value = res.data
      await nextTick()
      renderPriceChart()
    } catch { priceHistory.value = [] }
  } else {
    editingId.value = null
    Object.assign(form, defaultForm)
    priceHistory.value = []
  }
  formVisible.value = true
  await nextTick()
  formRef.value?.clearValidate()
}

async function handleSubmit() {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  try {
    if (editingId.value) await subscriptionStore.update(editingId.value, form)
    else await subscriptionStore.create(form)
    ElMessage.success(zhCN.common.success)
    formVisible.value = false
    await fetchList()
  } catch {}
}

async function handleDelete(row: Subscription) {
  try {
    await ElMessageBox.confirm(zhCN.subscription.deleteConfirm, zhCN.common.confirm, { type: 'warning' })
    await subscriptionStore.remove(row.id)
    ElMessage.success(zhCN.common.success)
    await fetchList()
  } catch {}
}

async function handleToggle(row: Subscription) {
  const oldValue = !row.is_active
  try { await patchSubscription(row.id, { is_active: row.is_active }) } catch { row.is_active = oldValue }
}

async function handleBatchDelete() {
  try {
    await ElMessageBox.confirm(zhCN.subscription.batchDeleteConfirm.replace('{count}', String(selectedIds.value.length)), zhCN.common.confirm, { type: 'warning' })
    await batchDelete(selectedIds.value)
    ElMessage.success(zhCN.common.success)
    selectedIds.value = []
    await fetchList()
  } catch {}
}

async function handleBatchToggle(is_active: boolean) {
  try {
    await batchToggle(selectedIds.value, is_active)
    ElMessage.success(zhCN.common.success)
    selectedIds.value = []
    await fetchList()
  } catch {}
}

async function handleBatchCategory() {
  if (batchCategoryId.value == null) return
  try {
    for (const id of selectedIds.value) {
      await patchSubscription(id, { category_id: batchCategoryId.value })
    }
    ElMessage.success(zhCN.subscription.batchSuccess.replace('{count}', String(selectedIds.value.length)))
    showBatchCategory.value = false
    selectedIds.value = []
    batchCategoryId.value = null
    await fetchList()
  } catch {}
}

async function handleBatchExpiry() {
  if (!batchExpiryDate.value) return
  try {
    for (const id of selectedIds.value) {
      await patchSubscription(id, { expiry_date: batchExpiryDate.value })
    }
    ElMessage.success(zhCN.subscription.batchSuccess.replace('{count}', String(selectedIds.value.length)))
    showBatchExpiry.value = false
    selectedIds.value = []
    batchExpiryDate.value = ''
    await fetchList()
  } catch {}
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
  const labels: Record<string, string> = { monthly: zhCN.subscription.monthly, quarterly: zhCN.subscription.quarterly, yearly: zhCN.subscription.yearly }
  return labels[cycle] || cycle
}

function renderPriceChart() {
  if (!priceChartRef.value || priceHistory.value.length <= 1) return
  priceChartInstance?.dispose()
  priceChartInstance = echarts.init(priceChartRef.value)
  const sorted = [...priceHistory.value].reverse()
  const labels = sorted.map((h: any) => h.created_at?.slice(0, 10) || '')
  const amounts = sorted.map((h: any) => h.new_amount)
  priceChartInstance.setOption({
    tooltip: { trigger: 'axis', confine: true },
    grid: { left: 50, right: 10, top: 10, bottom: 25 },
    xAxis: { type: 'category', data: labels, axisLabel: { fontSize: 11, color: '#94a3b8' } },
    yAxis: { type: 'value', axisLabel: { fontSize: 11, color: '#94a3b8' }, splitLine: { lineStyle: { color: '#f1f5f9' } } },
    series: [{
      type: 'line',
      data: amounts,
      smooth: true,
      symbol: 'circle',
      symbolSize: 6,
      lineStyle: { color: '#4f46e5', width: 2 },
      itemStyle: { color: '#4f46e5' },
      areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(79,70,229,0.3)' }, { offset: 1, color: 'rgba(79,70,229,0.02)' }]) },
    }],
  })
}
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.filter-bar {
  display: flex; gap: 12px; margin-bottom: 20px; flex-wrap: wrap; align-items: center;
  padding: 16px; background: #fff; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,.06);
}
.batch-actions { display: flex; align-items: center; gap: 8px; margin-left: auto; }
.selected-info { color: #4f46e5; font-size: 13px; font-weight: 500; }
.intro-hint { color: #f59e0b; font-size: 12px; font-weight: 500; }
.cycle-group { display: flex; align-items: center; gap: 8px; }
.cycle-tip { color: #94a3b8; font-size: 12px; margin-top: 4px; }
.intro-group { display: flex; align-items: center; gap: 6px; }
.intro-x { color: #94a3b8; font-size: 14px; }
.intro-unit { color: #94a3b8; font-size: 13px; }
.sub-favicon { width: 20px; height: 20px; border-radius: 4px; flex-shrink: 0; }
html.dark .filter-bar { background: #1e293b; }
</style>