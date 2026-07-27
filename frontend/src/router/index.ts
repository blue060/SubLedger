import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('../views/LoginView.vue'),
    },
    {
      path: '/',
      component: () => import('../components/layout/AppLayout.vue'),
      children: [
        { path: '', redirect: '/dashboard' },
        { path: 'dashboard', name: 'Dashboard', meta: { title: '仪表盘', description: '掌握支出、续费与近期扣款' }, component: () => import('../views/DashboardView.vue') },
        { path: 'subscriptions', name: 'Subscriptions', meta: { title: '订阅管理', description: '统一管理订阅状态、周期与费用' }, component: () => import('../views/SubscriptionsView.vue') },
        { path: 'payments', name: 'Payments', meta: { title: '付款记录', description: '核对每一笔实际付款' }, component: () => import('../views/PaymentsView.vue') },
        { path: 'analytics', name: 'Analytics', meta: { title: '支出分析', description: '查看成本结构与变化趋势' }, component: () => import('../views/AnalyticsView.vue') },
        { path: 'annual-report', name: 'AnnualReport', meta: { title: '年度报告', description: '回顾全年订阅支出' }, component: () => import('../views/AnnualReportView.vue') },
        { path: 'calendar', name: 'Calendar', meta: { title: '扣款日历', description: '按日期安排续费与到期事项' }, component: () => import('../views/CalendarView.vue') },
        { path: 'notifications', name: 'Notifications', meta: { title: '通知中心', description: '处理提醒与续费通知' }, component: () => import('../views/NotificationsView.vue') },
        { path: 'settings', name: 'Settings', meta: { title: '系统设置', description: '调整偏好、通知与数据' }, component: () => import('../views/SettingsView.vue') },
      ],
    },
  ],
})

const publicPaths = ['/login']

router.beforeEach(async (to, _from, next) => {
  if (publicPaths.includes(to.path)) {
    return next()
  }
  const authStore = useAuthStore()
  const authenticated = await authStore.checkAuth()
  if (authenticated) next()
  else next('/login')
})

export default router
