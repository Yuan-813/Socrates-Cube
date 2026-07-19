import axios from 'axios'
import { installMockInterceptor } from './mockInterceptor'

const apiClient = axios.create({
  // 开发环境留空，走 Vite proxy（/api -> localhost:8000）
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 安装 Mock 拦截器（仅在 VITE_MOCK_MODE=true 时生效）
installMockInterceptor(apiClient)

/**
 * 请求拦截器：自动注入 JWT Token
 * pinia-plugin-persistedstate 将 authStore 序列化至 localStorage['auth']
 * 在拦截器中读取而非依赖 defaults.headers，确保页面刷新后首个请求也携带 Token
 */
apiClient.interceptors.request.use(
  (config) => {
    try {
      const raw = localStorage.getItem('auth')
      if (raw) {
        const parsed = JSON.parse(raw) as { token?: string }
        if (parsed.token) {
          config.headers['Authorization'] = `Bearer ${parsed.token}`
        }
      }
    } catch {
      // localStorage 不可用时静默忽略（SSR 环境或隐私模式）
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

/**
 * 响应拦截器：
 * - 401 Token 失效 → 清除本地鉴权状态并跳转登录页
 * - 其他错误 → 打印日志后继续 reject
 */
apiClient.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    const requestUrl = error?.config?.url || ''
    const shouldSilence = typeof requestUrl === 'string' && requestUrl.includes('/health')

    if (error?.response?.status === 401) {
      // Token 过期或无效，清除持久化鉴权状态并重定向登录
      try {
        localStorage.removeItem('auth')
        localStorage.removeItem('user')
      } catch { /* ignore */ }
      if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    } else if (!shouldSilence) {
      console.error('[API Error]', error)
    }

    return Promise.reject(error)
  }
)

export default apiClient
