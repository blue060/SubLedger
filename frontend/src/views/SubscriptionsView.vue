<template>
  <div class="subscriptions-page">
    <section class="page-hero">
      <div>
        <span class="page-eyebrow">SUBSCRIPTION LIBRARY</span>
        <h2>{{ zhCN.subscription.title }}</h2>
        <p>集中查看每项服务的续费、到期和停用状态，避免遗漏扣款。</p>
      </div>
      <div class="page-actions">
        <el-button :icon="MagicStick" @click="showTemplateDialog = true">{{ zhCN.subscription.quickAdd }}</el-button>
        <el-button type="primary" :icon="Plus" @click="showForm()">{{ zhCN.subscription.addNew }}</el-button>
      </div>
    </section>

    <div class="status-overview">
      <button
        v-for="item in statusCards"
        :key="item.key"
        class="status-card"
        :class="[`status-${item.key}`, { active: statusFilter === item.key }]"
        @click="statusFilter = item.key"
      >
        <span class="status-card-label">{{ item.label }}</span>
        <strong>{{ item.count }}</strong>
        <span class="status-card-hint">{{ item.hint }}</span>
      </button>
    </div>

    <section class="subscription-panel">
      <div class="filter-bar">
        <el-input v-model="searchText" class="search-input" placeholder="搜索名称、备注或域名" clearable :prefix-icon="Search" />
        <el-select v-model="filterCategory" :placeholder="zhCN.subscription.category" clearable class="filter-select">
          <el-option v-for="cat in categoryStore.categories" :key="cat.id" :label="cat.name" :value="cat.id" />
        </el-select>
        <el-select v-model="filterCurrency" :placeholder="zhCN.subscription.currency" clearable class="currency-select">
          <el-option v-for="currency in currencies" :key="currency" :label="currency" :value="currency" />
        </el-select>
        <el-button v-if="hasFilters" :icon="RefreshLeft" text @click="resetFilters">重置筛选</el-button>
        <span class="result-count">共 {{ filteredSubscriptions.length }} 项</span>
      </div>

      <div v-if="selectedIds.length" class="batch-bar">
        <span class="selected-info">{{ zhCN.subscription.selected.replace('{count}', String(selectedIds.length)) }}</span>
        <div class="batch-actions">
          <el-button size="small" type="success" plain @click="handleBatchToggle(true)">{{ zhCN.subscription.batchEnable }}</el-button>
          <el-button size="small" type="warning" plain @click="handleBatchToggle(false)">{{ zhCN.subscription.batchDisable }}</el-button>
          <el-button size="small" @click="showBatchCategory = true">{{ zhCN.subscription.batchSetCategory }}</el-button>
          <el-button size="small" @click="showBatchExpiry = true">{{ zhCN.subscription.batchSetExpiry }}</el-button>
          <el-button size="small" type="danger" plain @click="handleBatchDelete">{{ zhCN.subscription.batchDelete }}</el-button>
        </div>
      </div>

      <el-table
        :data="filteredSubscriptions"
        v-loading="subscriptionStore.loading"
        :row-class-name="tableRowClass"
        empty-text="当前筛选下没有订阅"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="44" />
        <el-table-column prop="name" :label="zhCN.subscription.name" min-width="210" sortable>
          <template #default="{ row }">
            <div class="service-cell">
              <ServiceIcon :name="row.name" :url="row.url" :category-color="row.category_color" :size="36" />
              <div class="service-copy">
                <strong>{{ row.name }}</strong>
                <span>{{ serviceMeta(row) }}</span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="amount" :label="zhCN.subscription.amount" min-width="145" sortable>
          <template #default="{ row }">
            <div class="amount-cell">
              <strong>{{ formatCurrency(row.my_amount ?? row.amount, row.currency) }}</strong>
              <span v-if="row.my_amount != null">总价 {{ formatCurrency(row.amount, row.currency) }}</span>
              <span v-else-if="row.intro_amount != null && row.intro_months != null">优惠 {{ formatCurrency(row.intro_amount, row.currency) }} × {{ row.intro_months }}月</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="billing_cycle" :label="zhCN.subscription.cycle" min-width="105" sortable>
          <template #default="{ row }">
            <span class="cycle-pill">{{ cycleLabel(row.billing_cycle, row.billing_cycle_num, row.billing_cycle_unit) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="next_payment_date" label="时间安排" min-width="175" sortable>
          <template #default="{ row }">
            <div class="schedule-cell">
              <strong>{{ scheduleTitle(row) }}</strong>
              <span>{{ scheduleHint(row) }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="lifecycle_status" :label="zhCN.subscription.status" width="112">
          <template #default="{ row }">
            <el-tag :type="statusMeta(row.lifecycle_status).type" effect="light" size="small" round>
              {{ statusMeta(row.lifecycle_status).label }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" :label="zhCN.subscription.active" width="76" align="center">
          <template #default="{ row }">
            <el-tooltip :disabled="row.lifecycle_status !== 'expired'" content="请先修改到期日期再启用">
              <el-switch v-model="row.is_active" :disabled="row.lifecycle_status === 'expired'" @change="handleToggle(row)" />
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="128" fixed="right" align="right">
          <template #default="{ row }">
            <el-button size="small" text type="primary" @click="showForm(row)">{{ zhCN.common.edit }}</el-button>
            <el-button size="small" text type="danger" @click="handleDelete(row)">{{ zhCN.common.delete }}</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>

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
        <el-form-item v-if="form.billing_cycle !== 'once' && form.billing_cycle !== 'permanent'" :label="zhCN.subscription.autoRenew">
          <el-switch v-model="form.auto_renew" />
          <span class="cycle-tip" style="margin-left: 8px">{{ zhCN.subscription.autoRenewHint }}</span>
        </el-form-item>
        <el-form-item :label="zhCN.subscription.firstPayment" prop="first_payment_date"><el-date-picker v-model="form.first_payment_date" type="date" value-format="YYYY-MM-DD" /></el-form-item>
        <el-form-item :label="zhCN.subscription.category">
          <el-select v-model="form.category_id" clearable>
            <el-option v-for="cat in categoryStore.categories" :key="cat.id" :label="cat.name" :value="cat.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="zhCN.subscription.notes"><el-input v-model="form.notes" type="textarea" :rows="2" /></el-form-item>
        <el-form-item :label="zhCN.subscription.url"><el-input v-model="form.url" placeholder="https://..." /></el-form-item>
        <el-form-item :label="zhCN.subscription.expiryDate" prop="expiry_date"><el-date-picker v-model="form.expiry_date" type="date" value-format="YYYY-MM-DD" clearable /></el-form-item>
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
        <el-form-item :label="zhCN.tag.title">
          <el-select v-model="form.tag_ids" multiple filterable allow-create default-first-option style="width: 100%" :placeholder="zhCN.tag.addTag">
            <el-option v-for="tag in tags" :key="tag.id" :label="tag.name" :value="tag.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="zhCN.split.sharedWith">
          <el-input v-model="form.shared_with" placeholder="如：Alice, Bob" />
        </el-form-item>
        <el-form-item :label="zhCN.split.myShare">
          <el-input-number v-model="form.my_share" :min="1" :max="100" :precision="0" />
        </el-form-item>

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

    <!-- Quick Add Template Dialog -->
    <el-dialog v-model="showTemplateDialog" :title="zhCN.subscription.quickAdd" width="640px">
      <div class="template-grid">
        <div v-for="tpl in templates" :key="tpl.name" class="template-item" @click="selectTemplate(tpl)">
          <ServiceIcon :name="tpl.name" :url="tpl.url" :size="32" />
          <div class="template-item-info">
            <div class="template-name">{{ tpl.name }}</div>
            <div class="template-meta">{{ formatCurrency(tpl.amount, tpl.currency) }} / {{ cycleLabel(tpl.billing_cycle, 1, 'month', zhCN) }}</div>
          </div>
          <div class="template-category">{{ tpl.category_name }}</div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive, computed, nextTick } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { MagicStick, Plus, RefreshLeft, Search } from '@element-plus/icons-vue'
import { echarts } from '../utils/charts'
import { useSubscriptionStore } from '../stores/subscription'
import { useCategoryStore } from '../stores/category'
import { zhCN } from '../locales/zh-CN'
import { patchSubscription, batchDelete, batchToggle, batchCategory, batchExpiry, getPriceHistory } from '../api/subscriptions'
import { listTags } from '../api/tags'
import type { Subscription } from '../types/subscription'
import { formatCurrency, cycleLabel } from '../utils/format'
import ServiceIcon from '../components/ServiceIcon.vue'
import { TEMPLATES } from '../data/templates'

const subscriptionStore = useSubscriptionStore()
const categoryStore = useCategoryStore()

const formVisible = ref(false)
const editingId = ref<number | null>(null)
const priceHistory = ref<any[]>([])
const priceChartRef = ref<HTMLElement>()
let priceChartInstance: echarts.EChartsType | null = null
const searchText = ref('')
const filterCategory = ref<number | null>(null)
const filterCurrency = ref<string | null>(null)
type StatusFilter = 'all' | 'active' | 'expiring' | 'expired' | 'inactive'
const statusFilter = ref<StatusFilter>('all')
const selectedIds = ref<number[]>([])
const showBatchCategory = ref(false)
const batchCategoryId = ref<number | null>(null)
const showBatchExpiry = ref(false)
const batchExpiryDate = ref('')
const showTemplateDialog = ref(false)
const templates = TEMPLATES
const formRef = ref<FormInstance>()
const currencies = ['CNY', 'USD', 'EUR', 'GBP', 'JPY', 'HKD']

const formRules = reactive<FormRules>({
  name: [{ required: true, message: zhCN.subscription.nameRequired, trigger: 'blur' }],
  amount: [{ required: true, message: zhCN.subscription.amountRequired, trigger: 'blur' }],
  first_payment_date: [{ required: true, message: zhCN.subscription.firstPaymentRequired, trigger: 'change' }],
  expiry_date: [{ validator: validateExpiryDate, trigger: 'change' }],
})

const statusCards = computed(() => {
  const subscriptions = subscriptionStore.subscriptions
  const expiring = subscriptions.filter((s) => ['expiring', 'expires_today'].includes(s.lifecycle_status)).length
  const expired = subscriptions.filter((s) => s.lifecycle_status === 'expired').length
  const inactive = subscriptions.filter((s) => s.lifecycle_status === 'inactive').length
  const active = subscriptions.length - expiring - expired - inactive
  return [
    { key: 'all' as const, label: '全部订阅', count: subscriptions.length, hint: '所有服务' },
    { key: 'active' as const, label: '正常使用', count: active, hint: '续费与买断' },
    { key: 'expiring' as const, label: '即将到期', count: expiring, hint: '30 天内' },
    { key: 'expired' as const, label: '已经到期', count: expired, hint: '自动停用' },
    { key: 'inactive' as const, label: '手动停用', count: inactive, hint: '不参与统计' },
  ]
})

const filteredSubscriptions = computed(() => {
  const keyword = searchText.value.trim().toLocaleLowerCase()
  return subscriptionStore.subscriptions.filter((sub) => {
    if (statusFilter.value === 'active' && ['expiring', 'expires_today', 'expired', 'inactive'].includes(sub.lifecycle_status)) return false
    if (statusFilter.value === 'expiring' && !['expiring', 'expires_today'].includes(sub.lifecycle_status)) return false
    if (statusFilter.value === 'expired' && sub.lifecycle_status !== 'expired') return false
    if (statusFilter.value === 'inactive' && sub.lifecycle_status !== 'inactive') return false
    if (filterCategory.value != null && sub.category_id !== filterCategory.value) return false
    if (filterCurrency.value && sub.currency !== filterCurrency.value) return false
    if (keyword) {
      const haystack = [sub.name, sub.notes, sub.url, sub.category_name, sub.payment_method]
        .filter(Boolean)
        .join(' ')
        .toLocaleLowerCase()
      if (!haystack.includes(keyword)) return false
    }
    return true
  })
})

const hasFilters = computed(() => Boolean(
  searchText.value || filterCategory.value != null || filterCurrency.value || statusFilter.value !== 'all'
))

const defaultForm = {
  name: '', amount: 0, currency: 'CNY', billing_cycle: 'monthly',
  billing_cycle_num: 1, billing_cycle_unit: 'month',
  first_payment_date: '',
  category_id: null as number | null, notes: null as string | null, url: null as string | null,
  expiry_date: null as string | null, payment_method: null as string | null,
  intro_amount: null as number | null, intro_months: null as number | null,
  notify: true, auto_renew: true, tag_ids: [] as number[],
  shared_with: null as string | null, my_share: 100,
}
const form = reactive({ ...defaultForm })
const tags = ref<any[]>([])

function validateExpiryDate(_rule: any, value: string | null, callback: (error?: Error) => void) {
  const recurring = ['monthly', 'quarterly', 'yearly', 'custom'].includes(form.billing_cycle)
  if (recurring && !form.auto_renew && !value) {
    callback(new Error(zhCN.subscription.expiryRequiredForNonRenew))
    return
  }
  callback()
}

onMounted(async () => {
  const [, , tagRes] = await Promise.all([
    fetchList(),
    categoryStore.fetchList(),
    listTags().catch(() => ({ data: [] })),
  ])
  tags.value = tagRes.data
})

async function fetchList() {
  await subscriptionStore.fetchList()
}

function resetFilters() {
  searchText.value = ''
  filterCategory.value = null
  filterCurrency.value = null
  statusFilter.value = 'all'
  selectedIds.value = []
}

function serviceMeta(sub: Subscription) {
  const parts: string[] = []
  if (sub.category_name) parts.push(sub.category_name)
  if (sub.url) {
    try {
      parts.push(new URL(sub.url).hostname.replace(/^www\./, ''))
    } catch {}
  }
  if (!parts.length && sub.payment_method) parts.push(sub.payment_method)
  return parts.join(' · ') || '未分类'
}

function scheduleTitle(sub: Subscription) {
  if (sub.lifecycle_status === 'expired') return sub.expiry_date || '--'
  if (sub.billing_cycle === 'permanent') return '永久有效'
  if (sub.billing_cycle === 'once') return sub.first_payment_date
  if (!sub.auto_renew && sub.expiry_date) return sub.expiry_date
  return sub.next_payment_date || '--'
}

function scheduleHint(sub: Subscription) {
  if (sub.lifecycle_status === 'expired') return '已到期并停用'
  if (sub.lifecycle_status === 'expires_today') return '今天到期'
  if (sub.lifecycle_status === 'expiring' && sub.remaining_days != null) return `${sub.remaining_days} 天后到期`
  if (sub.billing_cycle === 'permanent') return '一次付费'
  if (sub.billing_cycle === 'once') return '一次性付款'
  if (!sub.auto_renew) return '到期后停止'
  return '下次自动扣款'
}

function statusMeta(status: string): { label: string; type: 'success' | 'warning' | 'danger' | 'info' | 'primary' } {
  const states: Record<string, { label: string; type: 'success' | 'warning' | 'danger' | 'info' | 'primary' }> = {
    active: { label: '自动续费', type: 'success' },
    ending: { label: '到期停止', type: 'primary' },
    expiring: { label: '即将到期', type: 'warning' },
    expires_today: { label: '今天到期', type: 'warning' },
    expired: { label: '已到期', type: 'danger' },
    inactive: { label: '已停用', type: 'info' },
    permanent: { label: '永久有效', type: 'success' },
    one_time: { label: '一次性', type: 'info' },
  }
  return states[status] || states.active
}

function tableRowClass({ row }: { row: Subscription }) {
  if (row.lifecycle_status === 'expired') return 'row-expired'
  if (row.lifecycle_status === 'inactive') return 'row-inactive'
  if (['expiring', 'expires_today'].includes(row.lifecycle_status)) return 'row-expiring'
  return ''
}

function handleSelectionChange(rows: Subscription[]) {
  selectedIds.value = rows.map((r) => r.id)
}

function onCycleChange() {
  if (form.billing_cycle !== 'custom') {
    form.billing_cycle_num = 1
    form.billing_cycle_unit = 'month'
  }
  if (form.billing_cycle === 'once' || form.billing_cycle === 'permanent') {
    form.auto_renew = false
  } else {
    form.auto_renew = true
  }
}

function selectTemplate(tpl: any) {
  editingId.value = null
  Object.assign(form, defaultForm)
  form.name = tpl.name
  form.amount = tpl.amount
  form.currency = tpl.currency
  form.billing_cycle = tpl.billing_cycle
  form.url = tpl.url
  const cat = categoryStore.categories.find((c: any) => c.name === tpl.category_name)
  if (cat) form.category_id = cat.id
  else form.category_id = null
  showTemplateDialog.value = false
  formVisible.value = true
}

async function showForm(sub?: Subscription) {
  if (sub) {
    editingId.value = sub.id
    Object.assign(form, {
      name: sub.name, amount: sub.amount, currency: sub.currency, billing_cycle: sub.billing_cycle,
      billing_cycle_num: sub.billing_cycle_num || 1, billing_cycle_unit: sub.billing_cycle_unit || 'month',
      first_payment_date: sub.first_payment_date, category_id: sub.category_id, notes: sub.notes,
      url: sub.url, expiry_date: sub.expiry_date, payment_method: sub.payment_method, notify: sub.notify, auto_renew: sub.auto_renew,
      intro_amount: sub.intro_amount, intro_months: sub.intro_months,
      tag_ids: (sub.tags || []).map((t: any) => t.id),
      shared_with: sub.shared_with, my_share: sub.my_share || 100,
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
  try {
    const res = await patchSubscription(row.id, { is_active: row.is_active })
    Object.assign(row, res.data)
  } catch {
    row.is_active = oldValue
  }
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
    const res = await batchToggle(selectedIds.value, is_active)
    if (res.data.skipped) ElMessage.warning(`${res.data.skipped} 个已到期订阅未启用，请先修改到期日期`)
    else ElMessage.success(zhCN.common.success)
    selectedIds.value = []
    await fetchList()
  } catch {}
}

async function handleBatchCategory() {
  if (batchCategoryId.value == null) return
  try {
    await batchCategory(selectedIds.value, batchCategoryId.value)
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
    await batchExpiry(selectedIds.value, batchExpiryDate.value)
    ElMessage.success(zhCN.subscription.batchSuccess.replace('{count}', String(selectedIds.value.length)))
    showBatchExpiry.value = false
    selectedIds.value = []
    batchExpiryDate.value = ''
    await fetchList()
  } catch {}
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
.subscriptions-page {
  width: 100%;
  max-width: 1500px;
  margin: 0 auto;
}
.page-hero {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 22px;
}
.page-hero h2 {
  margin: 3px 0 6px;
  font-size: 28px;
}
.page-hero p {
  margin-bottom: 0;
  color: var(--text-secondary);
  font-size: 13px;
}
.page-eyebrow {
  color: var(--primary);
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 1.6px;
}
.page-actions {
  display: flex;
  flex-shrink: 0;
  gap: 9px;
}
.status-overview {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}
.status-card {
  position: relative;
  min-width: 0;
  padding: 15px 16px;
  overflow: hidden;
  color: var(--text-primary);
  text-align: left;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 14px;
  box-shadow: 0 2px 10px rgba(15, 23, 42, .025);
  cursor: pointer;
  transition: border-color .16s, box-shadow .16s, transform .16s;
}
.status-card::after {
  position: absolute;
  top: 0;
  right: 0;
  width: 4px;
  height: 100%;
  background: #cbd5e1;
  content: '';
}
.status-card:hover {
  transform: translateY(-2px);
  border-color: var(--border-strong);
  box-shadow: var(--card-shadow-hover);
}
.status-card.active {
  border-color: color-mix(in srgb, var(--status-color, var(--primary)) 45%, var(--border));
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--status-color, var(--primary)) 10%, transparent);
}
.status-card-label {
  display: block;
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 650;
}
.status-card strong {
  display: block;
  margin: 5px 0 2px;
  font-size: 24px;
  line-height: 1;
}
.status-card-hint {
  color: var(--text-muted);
  font-size: 11px;
}
.status-all { --status-color: #6366f1; }
.status-active { --status-color: #10b981; }
.status-expiring { --status-color: #f59e0b; }
.status-expired { --status-color: #ef4444; }
.status-inactive { --status-color: #94a3b8; }
.status-card::after { background: var(--status-color); }
.subscription-panel {
  overflow: hidden;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 16px;
  box-shadow: var(--card-shadow);
}
.filter-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  border-bottom: 1px solid var(--border);
}
.search-input { width: min(360px, 36vw); }
.filter-select { width: 145px; }
.currency-select { width: 110px; }
.result-count {
  margin-left: auto;
  color: var(--text-muted);
  font-size: 12px;
  white-space: nowrap;
}
.batch-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 16px;
  background: var(--primary-bg);
  border-bottom: 1px solid color-mix(in srgb, var(--primary) 18%, var(--border));
}
.batch-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}
.selected-info {
  color: var(--primary-dark);
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
}
.service-cell {
  display: flex;
  align-items: center;
  gap: 11px;
  min-width: 0;
}
.service-copy,
.amount-cell,
.schedule-cell {
  display: flex;
  flex-direction: column;
  min-width: 0;
  gap: 3px;
}
.service-copy strong,
.amount-cell strong,
.schedule-cell strong {
  overflow: hidden;
  color: var(--text-primary);
  font-size: 13px;
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.service-copy span,
.amount-cell span,
.schedule-cell span {
  overflow: hidden;
  color: var(--text-muted);
  font-size: 11px;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.amount-cell strong {
  color: var(--primary-dark);
  font-size: 14px;
}
.cycle-pill {
  display: inline-flex;
  padding: 4px 8px;
  color: var(--text-secondary);
  font-size: 11px;
  font-weight: 650;
  background: var(--surface-secondary);
  border: 1px solid var(--border);
  border-radius: 7px;
}
:deep(.row-expired td.el-table__cell),
:deep(.row-inactive td.el-table__cell) {
  color: var(--text-muted);
  background: color-mix(in srgb, var(--surface-secondary) 64%, var(--surface));
}
:deep(.row-expired .service-copy strong),
:deep(.row-inactive .service-copy strong) {
  color: var(--text-secondary);
}
:deep(.row-expiring td:first-child) {
  box-shadow: 3px 0 0 #f59e0b inset;
}
.template-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  max-height: 400px;
  overflow-y: auto;
}
.template-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 11px 12px;
  border: 1px solid var(--border);
  border-radius: 12px;
  cursor: pointer;
  transition: all .16s ease;
}
.template-item:hover {
  background: var(--primary-bg);
  border-color: var(--primary);
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(91, 92, 226, .12);
}
.template-item-info { flex: 1; min-width: 0; }
.template-name { overflow: hidden; color: var(--text-primary); font-size: 13px; font-weight: 700; text-overflow: ellipsis; white-space: nowrap; }
.template-meta { margin-top: 3px; color: var(--primary); font-size: 12px; }
.template-category { color: var(--text-muted); font-size: 11px; white-space: nowrap; }
.cycle-group { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.cycle-tip { margin-top: 4px; color: var(--text-muted); font-size: 11px; }
.intro-group { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.intro-x { color: var(--text-muted); font-size: 14px; }
.intro-unit { color: var(--text-muted); font-size: 12px; }
.sub-favicon { display: none; }

@media (max-width: 1100px) {
  .status-overview { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .status-card:nth-child(4), .status-card:nth-child(5) { grid-column: span 1; }
}

@media (max-width: 767px) {
  .page-hero { align-items: flex-start; flex-direction: column; }
  .page-actions { width: 100%; }
  .page-actions .el-button { flex: 1; }
  .status-overview { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }
  .status-card { padding: 12px; }
  .status-card:first-child { grid-column: 1 / -1; }
  .status-card strong { font-size: 21px; }
  .filter-bar { align-items: stretch; flex-wrap: wrap; }
  .search-input { width: 100%; }
  .filter-select, .currency-select { flex: 1; width: auto; min-width: 120px; }
  .result-count { width: 100%; margin-left: 0; }
  .batch-bar { align-items: flex-start; flex-direction: column; }
  .template-grid { grid-template-columns: 1fr; }
}

html.dark .selected-info { color: #a5b4fc; }
html.dark .amount-cell strong { color: #a5b4fc; }
html.dark .template-item:hover { box-shadow: 0 6px 16px rgba(99, 102, 241, .08); }
</style>
