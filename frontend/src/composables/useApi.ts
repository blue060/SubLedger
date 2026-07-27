import axios from 'axios'
import { ElMessage } from 'element-plus'

const api = axios.create({
  baseURL: '/api',
  withCredentials: true,
})

let lastRateLimitNotice = 0

api.interceptors.request.use((config) => {
  const csrf = document.cookie
    .split('; ')
    .find((row) => row.startsWith('subledger_csrf='))
    ?.split('=')[1]
  if (csrf && config.method !== 'get' && config.method !== 'head') {
    config.headers['X-CSRF-Token'] = csrf
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    } else if (error.response?.status === 429) {
      const now = Date.now()
      if (now - lastRateLimitNotice > 3000) {
        const detail = error.response?.data?.detail || '操作过于频繁，请稍后再试'
        ElMessage.warning(detail)
        lastRateLimitNotice = now
      }
    } else if (error.response?.status !== 403) {
      const detail = error.response?.data?.detail
      let msg = '操作失败'
      if (Array.isArray(detail)) {
        const fieldMap: Record<string, string> = {
          name: '名称', amount: '金额', first_payment_date: '首次付款日',
          currency: '货币', billing_cycle: '计费周期',
          billing_cycle_num: '周期数', billing_cycle_unit: '周期单位',
          intro_amount: '优惠价格', intro_months: '优惠月数',
        }
        msg = detail.map((e: any) => {
          const field = e.loc?.slice(-1)[0]
          const label = fieldMap[field] || field || ''
          if (e.type === 'missing' || e.msg?.includes('required')) return `请填写${label}`
          return e.msg || `${label}格式不正确`
        }).join('；')
      } else if (typeof detail === 'string') {
        msg = detail
      }
      ElMessage.error(msg)
    }
    return Promise.reject(error)
  }
)

export default api
