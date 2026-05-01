import api from '../composables/useApi'

export function getDashboardSummary() {
  return api.get('/dashboard/summary')
}

export function getDashboardStats() {
  return api.get('/dashboard/stats')
}

export function getDashboardCalendar() {
  return api.get('/dashboard/calendar')
}