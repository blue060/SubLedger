import api from '../composables/useApi'
import type { SubscriptionCreate, SubscriptionUpdate } from '../types/subscription'

export function listSubscriptions(params?: Record<string, any>) {
  return api.get('/subscriptions', { params })
}

export function createSubscription(data: SubscriptionCreate) {
  return api.post('/subscriptions', data)
}

export function getSubscription(id: number) {
  return api.get(`/subscriptions/${id}`)
}

export function getPriceHistory(id: number) {
  return api.get(`/subscriptions/${id}/price-history`)
}

export function updateSubscription(id: number, data: SubscriptionUpdate) {
  return api.put(`/subscriptions/${id}`, data)
}

export function patchSubscription(id: number, data: Partial<SubscriptionUpdate>) {
  return api.patch(`/subscriptions/${id}`, data)
}

export function deleteSubscription(id: number) {
  return api.delete(`/subscriptions/${id}`)
}

export function batchDelete(ids: number[]) {
  return api.post('/subscriptions/batch-delete', { ids })
}

export function batchToggle(ids: number[], is_active: boolean) {
  return api.post('/subscriptions/batch-toggle', { ids, is_active })
}