import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUserStore = defineStore('user', () => {
  const userId = ref<string>('student-001')
  const username = ref<string>('学生用户')
  const isLoggedIn = ref<boolean>(true)

  function setUser(id: string, name: string) {
    userId.value = id
    username.value = name
    isLoggedIn.value = true
  }

  return {
    userId,
    username,
    isLoggedIn,
    setUser,
  }
}, {
  persist: true,
})
