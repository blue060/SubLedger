import api from '../composables/useApi'

export function listPayments(params?: Record<string, any>) {
  return api.get('/payments', { params })
}

export function listPendingPayments() {
  return api.get('/payments/pending')
}

export function createPayment(data: Record<string, any>) {
  return api.post('/payments', data)
}

export function updatePayment(id: number, data: Record<string, any>) {
  return api.put(`/payments/${id}`, data)
}

export function confirmPayment(id: number) {
  return api.post(`/payments/${id}/confirm`)
}

export function skipPayment(id: number) {
  return api.post(`/payments/${id}/skip`)
}

export function deletePayment(id: number) {
  return api.delete(`/payments/${id}`)
}
