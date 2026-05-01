import { defineStore } from 'pinia'
import { ref } from 'vue'
import { login as apiLogin, logout as apiLogout, getMe } from '../api/auth'

export const useAuthStore = defineStore('auth', () => {
  const isLoggedIn = ref(false)
  const username = ref('')

  async function login(password: string) {
    const res = await apiLogin(password)
    isLoggedIn.value = true
    username.value = res.data.username
  }

  async function logout() {
    await apiLogout()
    isLoggedIn.value = false
    username.value = ''
  }

  async function checkAuth() {
    try {
      const res = await getMe()
      isLoggedIn.value = true
      username.value = res.data.username
    } catch {
      isLoggedIn.value = false
      username.value = ''
    }
  }

  return { isLoggedIn, username, login, logout, checkAuth }
})