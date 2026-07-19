import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import apiClient from '../api/client'

export interface AuthUser {
  userId: string
  username: string
  roleType: string
  isFirstLogin: number
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(null)
  const user = ref<AuthUser | null>(null)
  const isLoggedIn = computed(() => !!token.value && !!user.value)

  function setToken(t: string) {
    token.value = t
    // 注入到 apiClient 请求头
    apiClient.defaults.headers.common['Authorization'] = `Bearer ${t}`
  }

  function setUser(u: AuthUser) {
    user.value = u
  }

  function login(tokenStr: string, userData: AuthUser) {
    setToken(tokenStr)
    setUser(userData)
  }

  function logout() {
    token.value = null
    user.value = null
    delete apiClient.defaults.headers.common['Authorization']
    // 清除 userStore 持久化状态
    localStorage.removeItem('user')
    localStorage.removeItem('auth')
  }

  // 恢复 token 到 axios（持久化恢复后调用）
  function restoreToken() {
    if (token.value) {
      apiClient.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
    }
  }

  return { token, user, isLoggedIn, login, logout, setToken, setUser, restoreToken }
}, {
  persist: true,
})
