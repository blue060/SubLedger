import api from '../composables/useApi'

export interface ManagedUser {
  id: number
  username: string
  is_admin: boolean
  created_at: string
}

export function listUsers() {
  return api.get<ManagedUser[]>('/users')
}

export function createUser(data: { username: string; password: string; is_admin: boolean }) {
  return api.post<ManagedUser>('/users', data)
}

export function resetUserPassword(userId: number, newPassword: string) {
  return api.post(`/users/${userId}/reset-password`, { new_password: newPassword })
}

export function deleteUser(userId: number) {
  return api.delete(`/users/${userId}`)
}
