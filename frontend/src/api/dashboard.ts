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

export function getDashboardExpiring() {
  return api.get('/dashboard/expiring')
}

export function getDashboardTrend(months = 12) {
  return api.get('/dashboard/trend', { params: { months } })
}

export function getDashboardBudget() {
  return api.get('/dashboard/budget')
}