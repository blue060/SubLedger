import { createRouter, createWebHistory } from 'vue-router'
import api from '../composables/useApi'

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
        { path: 'notifications', name: 'Notifications', component: () => import('../views/NotificationsView.vue') },
        { path: 'settings', name: 'Settings', component: () => import('../views/SettingsView.vue') },
      ],
    },
  ],
})

router.beforeEach(async (to) => {
  if (to.path === '/login') return true
  try {
    await api.get('/auth/me')
    return true
  } catch {
    return { path: '/login' }
  }
})

export default router