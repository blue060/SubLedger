import api from '../composables/useApi'

export function getSettings() {
  return api.get('/settings')
}

export function updateSettings(data: any) {
  return api.put('/settings', data)
}

export function changePassword(oldPassword: string, newPassword: string) {
  return api.post('/settings/password', { old_password: oldPassword, new_password: newPassword })
}

export function testEmail() {
  return api.post('/settings/test-email')
}

export function testPush() {
  return api.post('/settings/test-push')
}