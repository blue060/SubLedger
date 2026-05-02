<template>
  <div>
    <div class="page-header">
      <h2>{{ zhCN.subscription.title }}</h2>
      <el-button type="primary" @click="showForm()">
        {{ zhCN.subscription.addNew }}
      </el-button>
    </div>

    <el-table :data="subscriptionStore.subscriptions" v-loading="subscriptionStore.loading" stripe>
      <el-table-column prop="name" :label="zhCN.subscription.name" />
      <el-table-column prop="amount" :label="zhCN.subscription.amount">
        <template #default="{ row }">
          {{ formatCurrency(row.amount, row.currency) }}
        </template>
      </el-table-column>
      <el-table-column prop="billing_cycle" :label="zhCN.subscription.cycle">
        <template #default="{ row }">
          {{ cycleLabel(row.billing_cycle) }}
        </template>
      </el-table-column>
      <el-table-column prop="next_payment_date" :label="zhCN.subscription.nextPayment" />
      <el-table-column v-if="hasExpiring" :label="zhCN.subscription.remainingDays" width="120">
        <template #default="{ row }">
          <el-tag v-if="row.remaining_days !== null && row.remaining_days !== undefined" :type="row.remaining_days <= 0 ? 'danger' : row.remaining_days <= 7 ? 'danger' : row.remaining_days <= 30 ? 'warning' : 'info'">
            {{ row.remaining_days <= 0 ? zhCN.subscription.expired : zhCN.subscription.daysLeft.replace('{days}', String(row.remaining_days)) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="category_name" :label="zhCN.subscription.category">
        <template #default="{ row }">
          <el-tag v-if="row.category_name" :color="row.category_color" style="color: #fff">
            {{ row.category_name }}
          </el-tag>
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
      <el-form :model="form" label-width="100px">
        <el-form-item :label="zhCN.subscription.name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item :label="zhCN.subscription.amount">
          <el-input-number v-model="form.amount" :min="0" :precision="2" />
        </el-form-item>
        <el-form-item :label="zhCN.subscription.currency">
          <el-select v-model="form.currency">
            <el-option label="CNY ¥" value="CNY" />
            <el-option label="USD $" value="USD" />
            <el-option label="EUR €" value="EUR" />
            <el-option label="GBP £" value="GBP" />
            <el-option label="JPY ¥" value="JPY" />
            <el-option label="HKD $" value="HKD" />
          </el-select>
        </el-form-item>
        <el-form-item :label="zhCN.subscription.cycle">
          <el-select v-model="form.billing_cycle">
            <el-option :label="zhCN.subscription.monthly" value="monthly" />
            <el-option :label="zhCN.subscription.quarterly" value="quarterly" />
            <el-option :label="zhCN.subscription.yearly" value="yearly" />
          </el-select>
        </el-form-item>
        <el-form-item :label="zhCN.subscription.firstPayment">
          <el-date-picker v-model="form.first_payment_date" type="date" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item :label="zhCN.subscription.category">
          <el-select v-model="form.category_id" clearable>
            <el-option
              v-for="cat in categoryStore.categories"
              :key="cat.id"
              :label="cat.name"
              :value="cat.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item :label="zhCN.subscription.notes">
          <el-input v-model="form.notes" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item :label="zhCN.subscription.url">
          <el-input v-model="form.url" placeholder="https://..." />
        </el-form-item>
        <el-form-item :label="zhCN.subscription.expiryDate">
          <el-date-picker v-model="form.expiry_date" type="date" value-format="YYYY-MM-DD" clearable />
        </el-form-item>
        <el-form-item :label="zhCN.subscription.notify">
          <el-switch v-model="form.notify" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="formVisible = false">{{ zhCN.common.cancel }}</el-button>
        <el-button type="primary" @click="handleSubmit">{{ zhCN.common.save }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useSubscriptionStore } from '../stores/subscription'
import { useCategoryStore } from '../stores/category'
import { zhCN } from '../locales/zh-CN'
import { patchSubscription } from '../api/subscriptions'
import type { Subscription } from '../types/subscription'

const subscriptionStore = useSubscriptionStore()
const categoryStore = useCategoryStore()

const hasExpiring = computed(() => subscriptionStore.subscriptions.some((s: any) => s.remaining_days != null))

const formVisible = ref(false)
const editingId = ref<number | null>(null)

const defaultForm = {
  name: '',
  amount: 0,
  currency: 'CNY',
  billing_cycle: 'monthly',
  first_payment_date: '',
  category_id: null as number | null,
  notes: null as string | null,
  url: null as string | null,
  expiry_date: null as string | null,
  notify: true,
}

const form = reactive({ ...defaultForm })

onMounted(async () => {
  await Promise.all([
    subscriptionStore.fetchList(),
    categoryStore.fetchList(),
  ])
})

function showForm(sub?: Subscription) {
  if (sub) {
    editingId.value = sub.id
    Object.assign(form, {
      name: sub.name,
      amount: sub.amount,
      currency: sub.currency,
      billing_cycle: sub.billing_cycle,
      first_payment_date: sub.first_payment_date,
      category_id: sub.category_id,
      notes: sub.notes,
      url: sub.url,
      expiry_date: sub.expiry_date,
      notify: sub.notify,
    })
  } else {
    editingId.value = null
    Object.assign(form, defaultForm)
  }
  formVisible.value = true
}

async function handleSubmit() {
  try {
    if (editingId.value) {
      await subscriptionStore.update(editingId.value, form)
    } else {
      await subscriptionStore.create(form)
    }
    ElMessage.success(zhCN.common.success)
    formVisible.value = false
  } catch {}
}

async function handleDelete(row: Subscription) {
  try {
    await ElMessageBox.confirm(zhCN.subscription.deleteConfirm, zhCN.common.confirm, { type: 'warning' })
    await subscriptionStore.remove(row.id)
    ElMessage.success(zhCN.common.success)
  } catch {}
}

async function handleToggle(row: Subscription) {
  const oldValue = !row.is_active
  try {
    await patchSubscription(row.id, { is_active: row.is_active })
  } catch {
    row.is_active = oldValue
  }
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
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
</style>