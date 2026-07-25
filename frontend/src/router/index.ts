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
        { path: 'dashboard', name: 'Dashboard', component: () => import('../views/DashboardView.vue') },
        { path: 'subscriptions', name: 'Subscriptions', component: () => import('../views/SubscriptionsView.vue') },
        { path: 'payments', name: 'Payments', component: () => import('../views/PaymentsView.vue') },
        { path: 'analytics', name: 'Analytics', component: () => import('../views/AnalyticsView.vue') },
        { path: 'annual-report', name: 'AnnualReport', component: () => import('../views/AnnualReportView.vue') },
        { path: 'calendar', name: 'Calendar', component: () => import('../views/CalendarView.vue') },
        { path: 'notifications', name: 'Notifications', component: () => import('../views/NotificationsView.vue') },
        { path: 'settings', name: 'Settings', component: () => import('../views/SettingsView.vue') },
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
