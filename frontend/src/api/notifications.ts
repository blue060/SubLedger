import api from '../composables/useApi'

export function listNotifications(unreadOnly = false) {
  return api.get('/notifications', { params: { unread_only: unreadOnly } })
}

export function getUnreadCount() {
  return api.get('/notifications/unread-count')
}

export function markRead(id: number) {
  return api.patch(`/notifications/${id}`)
}

export function markAllRead() {
  return api.post('/notifications/mark-all-read')
}