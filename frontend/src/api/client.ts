import axios from 'axios'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

apiClient.interceptors.request.use(
  (config) => {
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

apiClient.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    const requestUrl = error?.config?.url || ''
    const shouldSilence = typeof requestUrl === 'string' && requestUrl.includes('/health')

    if (!shouldSilence) {
      console.error('[API Error]', error)
    }

    return Promise.reject(error)
  }
)

export default apiClient
