import api from '../composables/useApi'

export function globalSearch(q: string) {
  return api.get('/search', { params: { q } })
}