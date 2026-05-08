<template>
  <el-dialog v-model="visible" :title="zhCN.search.title" width="520px" @close="query = ''">
    <el-input v-model="query" :placeholder="zhCN.search.placeholder" ref="inputRef" @input="debouncedSearch" clearable />
    <div v-if="results.subscriptions.length || results.notifications.length || results.categories.length" class="search-results">
      <div v-if="results.subscriptions.length" class="search-group">
        <div class="search-group-title">{{ zhCN.nav.subscriptions }}</div>
        <div v-for="s in results.subscriptions" :key="'s'+s.id" class="search-item" @click="goTo('/subscriptions')">
          <span>{{ s.name }}</span>
          <span class="search-item-amount">{{ s.currency }} {{ s.amount.toFixed(2) }}</span>
        </div>
      </div>
      <div v-if="results.notifications.length" class="search-group">
        <div class="search-group-title">{{ zhCN.nav.notifications }}</div>
        <div v-for="n in results.notifications" :key="'n'+n.id" class="search-item" @click="goTo('/notifications')">
          {{ n.message }}
        </div>
      </div>
      <div v-if="results.categories.length" class="search-group">
        <div class="search-group-title">{{ zhCN.search.categoryLabel }}</div>
        <div v-for="c in results.categories" :key="'c'+c.id" class="search-item" @click="goTo('/subscriptions')">
          {{ c.name }}
        </div>
      </div>
    </div>
    <div v-else-if="query && !loading" class="search-empty">{{ zhCN.search.noResults }}</div>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { globalSearch } from '../api/search'
import { zhCN } from '../locales/zh-CN'

const visible = defineModel<boolean>('visible', { default: false })
const router = useRouter()
const query = ref('')
const loading = ref(false)
const results = ref<Record<string, any[]>>({ subscriptions: [], notifications: [], categories: [] })
let searchTimer: ReturnType<typeof setTimeout> | null = null
const inputRef = ref<any>(null)

watch(visible, (v) => {
  if (v) {
    query.value = ''
    results.value = { subscriptions: [], notifications: [], categories: [] }
    nextTick(() => inputRef.value?.focus())
  }
})

function debouncedSearch() {
  if (searchTimer) clearTimeout(searchTimer)
  if (!query.value.trim()) {
    results.value = { subscriptions: [], notifications: [], categories: [] }
    return
  }
  searchTimer = setTimeout(doSearch, 300)
}

async function doSearch() {
  loading.value = true
  try {
    const res = await globalSearch(query.value.trim())
    results.value = res.data
  } catch {
    results.value = { subscriptions: [], notifications: [], categories: [] }
  } finally {
    loading.value = false
  }
}

function goTo(path: string) {
  visible.value = false
  router.push(path)
}
</script>

<style scoped>
.search-results { margin-top: 12px; max-height: 360px; overflow-y: auto; }
.search-group { margin-bottom: 12px; }
.search-group-title { font-size: 12px; color: #909399; font-weight: 600; margin-bottom: 4px; }
.search-item { padding: 8px 12px; cursor: pointer; border-radius: 6px; font-size: 14px; display: flex; justify-content: space-between; }
.search-item:hover { background: #f5f7fa; }
.search-item-amount { color: #4f46e5; font-size: 13px; }
.search-empty { text-align: center; color: #909399; padding: 20px 0; }
html.dark .search-item:hover { background: #1e293b; }
</style>