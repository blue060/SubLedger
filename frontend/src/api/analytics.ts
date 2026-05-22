import api from '../composables/useApi'

export function getMonthlyComparison() {
  return api.get('/analytics/monthly-comparison')
}

export function getCategoryTrend(months = 12) {
  return api.get('/analytics/category-trend', { params: { months } })
}

export function getTopSubscriptions(limit = 10) {
  return api.get('/analytics/top-subscriptions', { params: { limit } })
}

export function getCurrencyBreakdown() {
  return api.get('/analytics/currency-breakdown')
}

export function getAnnualReport(year?: number) {
  return api.get('/analytics/annual-report', { params: year ? { year } : {} })
}