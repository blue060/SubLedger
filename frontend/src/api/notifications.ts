import api from '../composables/useApi'

export function listNotifications(unreadOnly = false, page = 1, pageSize = 20) {
  return api.get('/notifications', { params: { unread_only: unreadOnly, page, page_size: pageSize } })
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

export function deleteNotification(id: number) {
  return api.delete(`/notifications/${id}`)
}

export function deleteReadNotifications() {
  return api.delete('/notifications')
}