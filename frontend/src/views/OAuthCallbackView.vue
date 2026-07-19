<template>
  <div class="callback-container">
    <div class="callback-card">
      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <p>正在完成登录...</p>
      </div>
      <div v-else-if="error" class="error-state">
        <p>{{ error }}</p>
        <button @click="goLogin">返回登录</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import { useUserStore } from '@/stores/userStore'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const userStore = useUserStore()
const loading = ref(true)
const error = ref('')

onMounted(async () => {
  const provider = route.params.provider as string
  const code = route.query.code as string
  const state = route.query.state as string

  if (!code) {
    error.value = '授权失败：未获取到授权码'
    loading.value = false
    return
  }

  try {
    const res = await fetch(`/api/v1/auth/oauth/${provider}/callback?code=${code}&state=${state}`)
    const data = await res.json()

    if (data.access_token) {
      const userData = {
        userId: data.user_id,
        username: data.username,
        roleType: data.role_type || 'student',
        isFirstLogin: data.is_first_login || 0,
      }
      authStore.login(data.access_token, userData)
      userStore.setUser(userData.userId, userData.username)
      router.push('/')
    } else {
      error.value = data.detail || data.message || '登录失败'
    }
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '回调处理失败'
  } finally {
    loading.value = false
  }
})

function goLogin() {
  router.push('/login')
}
</script>

<style scoped>
.callback-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f0f4f8;
}
.callback-card {
  background: white;
  border-radius: 16px;
  padding: 48px;
  box-shadow: 0 4px 24px rgba(0,0,0,0.08);
  text-align: center;
}
.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #e2e8f0;
  border-top-color: #6366f1;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 16px;
}
@keyframes spin { to { transform: rotate(360deg); } }
.error-state p {
  color: #dc2626;
  margin-bottom: 16px;
}
.error-state button {
  padding: 8px 24px;
  background: #6366f1;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
}
.error-state button:hover {
  background: #4f46e5;
}
</style>
