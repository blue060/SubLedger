<template>
  <div>
    <div class="page-header">
      <h2>{{ zhCN.payment.title }}</h2>
      <el-button type="primary" @click="showAddDialog = true">{{ zhCN.payment.addManual }}</el-button>
    </div>

    <!-- Filters -->
    <div class="filter-bar">
      <el-date-picker v-model="dateRange" type="daterange" :start-placeholder="zhCN.payment.filterByDate" :end-placeholder="zhCN.payment.filterByDate" value-format="YYYY-MM-DD" style="width: 260px" @change="fetchList" />
      <el-select v-model="filterStatus" :placeholder="zhCN.payment.filterByStatus" clearable style="width: 130px" @change="fetchList">
        <el-option :label="zhCN.payment.pending" value="pending" />
        <el-option :label="zhCN.payment.confirmed" value="confirmed" />
        <el-option :label="zhCN.payment.skipped" value="skipped" />
      </el-select>
      <el-select v-model="filterSub" :placeholder="zhCN.payment.filterBySub" clearable style="width: 180px" @change="fetchList">
        <el-option v-for="s in subscriptions" :key="s.id" :label="s.name" :value="s.id" />
      </el-select>
    </div>

    <el-table :data="records" v-loading="loading" stripe>
      <el-table-column prop="payment_date" :label="zhCN.payment.date" sortable width="120" />
      <el-table-column prop="subscription_name" :label="zhCN.payment.subscription" />
      <el-table-column prop="amount" :label="zhCN.payment.amount" sortable width="120">
        <template #default="{ row }">{{ formatCurrency(row.amount, row.currency) }}</template>
      </el-table-column>
      <el-table-column prop="status" :label="zhCN.payment.status" width="100">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="notes" :label="zhCN.payment.notes" show-overflow-tooltip />
      <el-table-column label="" width="200" fixed="right">
        <template #default="{ row }">
          <template v-if="row.status === 'pending'">
            <el-button size="small" type="success" @click="handleConfirm(row.id)">{{ zhCN.payment.confirmPayment }}</el-button>
            <el-button size="small" @click="handleSkip(row.id)">{{ zhCN.payment.skipPayment }}</el-button>
          </template>
          <el-button size="small" type="danger" @click="handleDelete(row.id)">{{ zhCN.common.delete }}</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination v-if="total > pageSize" :current-page="page" :page-size="pageSize" :total="total" layout="prev, pager, next" style="margin-top: 16px; justify-content: center" @current-change="(p: number) => { page = p; fetchList() }" />

    <!-- Add manual payment dialog -->
    <el-dialog v-model="showAddDialog" :title="zhCN.payment.addManual" width="440px">
      <el-form label-width="100px">
        <el-form-item :label="zhCN.payment.subscription">
          <el-select v-model="addForm.subscription_id" style="width: 100%">
            <el-option v-for="s in subscriptions" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="zhCN.payment.amount">
          <el-input-number v-model="addForm.amount" :min="0" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item :label="zhCN.payment.date">
          <el-date-picker v-model="addForm.payment_date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item :label="zhCN.payment.notes">
          <el-input v-model="addForm.notes" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">{{ zhCN.common.cancel }}</el-button>
        <el-button type="primary" @click="handleAdd">{{ zhCN.common.save }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { listPayments, createPayment, confirmPayment, skipPayment, deletePayment } from '../api/payments'
import { listSubscriptions } from '../api/subscriptions'
import { zhCN } from '../locales/zh-CN'
import { formatCurrency } from '../utils/format'

const records = ref<any[]>([])
const subscriptions = ref<any[]>([])
const loading = ref(false)
const total = ref(0)
const page = ref(1)
const pageSize = 20

const dateRange = ref<string[] | null>(null)
const filterStatus = ref<string | null>(null)
const filterSub = ref<number | null>(null)

const showAddDialog = ref(false)
const addForm = reactive({ subscription_id: null as number | null, amount: 0, payment_date: '', notes: '' })

onMounted(async () => {
  const subsRes = await listSubscriptions({ is_active: true })
  subscriptions.value = subsRes.data
  await fetchList()
})

async function fetchList() {
  loading.value = true
  try {
    const params: Record<string, any> = { page: page.value, page_size: pageSize }
    if (dateRange.value && dateRange.value[0]) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }
    if (filterStatus.value) params.status = filterStatus.value
    if (filterSub.value) params.subscription_id = filterSub.value
    const res = await listPayments(params)
    records.value = res.data
  } finally {
    loading.value = false
  }
}

function statusType(status: string) {
  return status === 'confirmed' ? 'success' : status === 'pending' ? 'warning' : 'info'
}

function statusLabel(status: string) {
  const map: Record<string, string> = { confirmed: zhCN.payment.confirmed, pending: zhCN.payment.pending, skipped: zhCN.payment.skipped }
  return map[status] || status
}

async function handleConfirm(id: number) {
  await confirmPayment(id)
  ElMessage.success(zhCN.common.success)
  fetchList()
}

async function handleSkip(id: number) {
  await skipPayment(id)
  ElMessage.success(zhCN.common.success)
  fetchList()
}

async function handleDelete(id: number) {
  await ElMessageBox.confirm(zhCN.payment.deleteConfirm, zhCN.common.confirm, { type: 'warning' })
  await deletePayment(id)
  ElMessage.success(zhCN.common.success)
  fetchList()
}

async function handleAdd() {
  if (!addForm.subscription_id || !addForm.payment_date) {
    ElMessage.warning(zhCN.common.error)
    return
  }
  await createPayment({ ...addForm, currency: 'CNY', status: 'confirmed' })
  ElMessage.success(zhCN.common.success)
  showAddDialog.value = false
  addForm.subscription_id = null
  addForm.amount = 0
  addForm.payment_date = ''
  addForm.notes = ''
  fetchList()
}
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}
</style>
