import api from '../composables/useApi'

export function listCategories() {
  return api.get('/categories')
}

export function createCategory(data: { name: string; icon?: string | null; color?: string | null; sort_order?: number }) {
  return api.post('/categories', data)
}

export function updateCategory(id: number, data: { name?: string; icon?: string | null; color?: string | null; sort_order?: number }) {
  return api.put(`/categories/${id}`, data)
}

export function deleteCategory(id: number) {
  return api.delete(`/categories/${id}`)
}

export function reorderCategories(ids: number[]) {
  return api.post('/categories/reorder', { ids })
}