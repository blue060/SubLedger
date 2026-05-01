import api from '../composables/useApi'

export function exportData(format: string) {
  return api.get('/data/export', { params: { format }, responseType: 'blob' })
}

export function importData(file: File) {
  const formData = new FormData()
  formData.append('file', file)
  return api.post('/data/import', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}