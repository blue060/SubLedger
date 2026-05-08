import api from '../composables/useApi'

export function listTags() {
  return api.get('/tags')
}

export function createTag(data: { name: string; color?: string }) {
  return api.post('/tags', data)
}

export function updateTag(id: number, data: { name?: string; color?: string }) {
  return api.put(`/tags/${id}`, data)
}

export function deleteTag(id: number) {
  return api.delete(`/tags/${id}`)
}
