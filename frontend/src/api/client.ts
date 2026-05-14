import axios from 'axios'
import { fetchEventSource } from '@microsoft/fetch-event-source'
import type { SSEEvent } from '@/types/sse'

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

const BASE_URL = '/api/v1'

export function createSSEConnection(
  endpoint: string,
  payload: Record<string, unknown>,
  onMessage: (event: SSEEvent) => void,
  onError?: (err: Error) => void,
  onDone?: () => void
): AbortController {
  const ctrl = new AbortController()

  fetchEventSource($BASE_URL + endpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
    signal: ctrl.signal,

    onmessage(e) {
      if (!e.data) return
      try {
        const parsed: SSEEvent = JSON.parse(e.data)
        if (parsed.event === 'done') {
          onDone?.()
        } else {
          onMessage(parsed)
        }
      } catch {
        onMessage({ event: 'token', data: e.data } as SSEEvent)
      }
    },

    onerror(err) {
      onError?.(err instanceof Error ? err : new Error(String(err)))
      throw err
    },

    openWhenHidden: true,
  })

  return ctrl
}

export default apiClient
