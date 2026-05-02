import { defineStore } from 'pinia'
import { ref } from 'vue'
import { listSubscriptions, createSubscription, updateSubscription, deleteSubscription } from '../api/subscriptions'
import type { Subscription, SubscriptionCreate, SubscriptionUpdate } from '../types/subscription'

export const useSubscriptionStore = defineStore('subscription', () => {
  const subscriptions = ref<Subscription[]>([])
  const loading = ref(false)

  async function fetchList(params?: Record<string, any>) {
    loading.value = true
    try {
      const res = await listSubscriptions(params)
      subscriptions.value = res.data
    } finally {
      loading.value = false
    }
  }

  async function create(data: SubscriptionCreate) {
    const res = await createSubscription(data)
    subscriptions.value.push(res.data)
    return res.data
  }

  async function update(id: number, data: SubscriptionUpdate) {
    const res = await updateSubscription(id, data)
    const idx = subscriptions.value.findIndex((s) => s.id === id)
    if (idx !== -1) subscriptions.value[idx] = res.data
    return res.data
  }

  async function remove(id: number) {
    await deleteSubscription(id)
    subscriptions.value = subscriptions.value.filter((s) => s.id !== id)
  }

  return { subscriptions, loading, fetchList, create, update, remove }
})