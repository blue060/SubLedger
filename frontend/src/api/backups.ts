import api from '../composables/useApi'

export function listBackups() {
  return api.get('/backups')
}

export function triggerBackup() {
  return api.post('/backups/trigger')
}

export function downloadBackup(id: number) {
  return api.get(`/backups/${id}/download`, { responseType: 'blob' })
}

export function deleteBackup(id: number) {
  return api.delete(`/backups/${id}`)
}