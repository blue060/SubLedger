import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '../router'

const api = axios.create({
  baseURL: '/api',
  withCredentials: true,
})

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
      // Only redirect to login if we're not already on login page
      if (window.location.pathname !== '/login') {
        router.push('/login')
      }
    } else if (error.response?.status === 429) {
      ElMessage.error('请求过于频繁，请稍后再试')
    } else if (error.response?.status !== 403) {
      // Don't show generic error for CSRF failures (they'll retry)
      ElMessage.error(error.response?.data?.detail || '操作失败')
    }
    return Promise.reject(error)
  }
)

export default api