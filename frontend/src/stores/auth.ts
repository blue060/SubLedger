import { defineStore } from 'pinia'
import { ref } from 'vue'
import { login as apiLogin, logout as apiLogout, getMe } from '../api/auth'

export const useAuthStore = defineStore('auth', () => {
  const isLoggedIn = ref(false)
  const username = ref('')
  const initialized = ref(false)
  let checkPromise: Promise<boolean> | null = null

  async function login(uname: string, pwd: string) {
    const res = await apiLogin(uname, pwd)
    isLoggedIn.value = true
    username.value = res.data.username
    initialized.value = true
  }

  async function logout() {
    await apiLogout()
    isLoggedIn.value = false
    username.value = ''
    initialized.value = true
  }

  async function checkAuth(force = false): Promise<boolean> {
    if (initialized.value && !force) return isLoggedIn.value
    if (checkPromise) return checkPromise
    checkPromise = (async () => {
      try {
        const res = await getMe()
        isLoggedIn.value = true
        username.value = res.data.username
      } catch {
        isLoggedIn.value = false
        username.value = ''
      } finally {
        initialized.value = true
        checkPromise = null
      }
      return isLoggedIn.value
    })()
    return checkPromise
  }

  return { isLoggedIn, username, initialized, login, logout, checkAuth }
})
