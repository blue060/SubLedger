import { createRouter, createWebHistory } from 'vue-router'
import { getMe } from '../api/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('../views/LoginView.vue'),
    },
    {
      path: '/setup',
      name: 'Setup',
      component: () => import('../views/SetupView.vue'),
    },
    {
      path: '/',
      component: () => import('../components/layout/AppLayout.vue'),
      children: [
        { path: '', redirect: '/dashboard' },
        { path: 'dashboard', name: 'Dashboard', component: () => import('../views/DashboardView.vue') },
        { path: 'subscriptions', name: 'Subscriptions', component: () => import('../views/SubscriptionsView.vue') },
        { path: 'calendar', name: 'Calendar', component: () => import('../views/CalendarView.vue') },
        { path: 'notifications', name: 'Notifications', component: () => import('../views/NotificationsView.vue') },
        { path: 'settings', name: 'Settings', component: () => import('../views/SettingsView.vue') },
      ],
    },
  ],
})

const publicPaths = ['/login', '/setup']

router.beforeEach(async (to, _from, next) => {
  if (publicPaths.includes(to.path)) {
    return next()
  }
  try {
    await getMe()
    next()
  } catch {
    next('/login')
  }
})

export default router