import api from '../composables/useApi'

export function login(password: string) {
  return api.post('/auth/login', { password })
}

export function logout() {
  return api.post('/auth/logout')
}

export function getMe() {
  return api.get('/auth/me')
}