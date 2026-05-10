import { ref } from 'vue'

export interface SSEOptions {
  onMessage?: (chunk: string) => void
  onDone?: () => void
  onError?: (err: Error) => void
}

export interface FetchSSEOptions extends SSEOptions {
  method?: 'GET' | 'POST'
  headers?: Record<string, string>
  body?: string | object
}

/**
 * 使用 EventSource 的 SSE（GET 请求，无请求体）
 */
export function useSSE() {
  const isConnected = ref(false)
  const isStreaming = ref(false)
  const lastError = ref<Error | null>(null)
  let eventSource: EventSource | null = null

  function connect(url: string, options: SSEOptions = {}) {
    disconnect()
    lastError.value = null
    isStreaming.value = true

    eventSource = new EventSource(url)

    eventSource.onopen = () => {
      isConnected.value = true
    }

    eventSource.onmessage = (event) => {
      if (event.data === '[DONE]') {
        options.onDone?.()
        disconnect()
        return
      }
      options.onMessage?.(event.data)
    }

    eventSource.onerror = () => {
      lastError.value = new Error('SSE 连接异常')
      options.onError?.(lastError.value)
      disconnect()
    }

    return eventSource
  }

  function disconnect() {
    if (eventSource) {
      eventSource.close()
      eventSource = null
    }
    isConnected.value = false
    isStreaming.value = false
  }

  return {
    isConnected,
    isStreaming,
    lastError,
    connect,
    disconnect,
  }
}

/**
 * 使用 fetch + ReadableStream 的 SSE（支持 POST 请求体）
 * 适用于需要通过请求体发送上下文的场景
 */
export function useFetchSSE() {
  const isConnected = ref(false)
  const isStreaming = ref(false)
  const lastError = ref<Error | null>(null)
  let abortController: AbortController | null = null

  async function connect(url: string, options: FetchSSEOptions = {}) {
    disconnect()
    lastError.value = null
    isStreaming.value = true

    abortController = new AbortController()

    try {
      const body = typeof options.body === 'object'
        ? JSON.stringify(options.body)
        : options.body

      const response = await fetch(url, {
        method: options.method || 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
          ...options.headers,
        },
        body,
        signal: abortController.signal,
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      if (!response.body) {
        throw new Error('ReadableStream 不支持')
      }

      isConnected.value = true
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) {
          options.onDone?.()
          disconnect()
          break
        }

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          const trimmed = line.trim()
          if (trimmed.startsWith('data:')) {
            const data = trimmed.slice(5).trim()
            if (data === '[DONE]') {
              options.onDone?.()
              disconnect()
              return
            }
            if (data) {
              options.onMessage?.(data)
            }
          }
        }
      }
    } catch (err: any) {
      if (err.name === 'AbortError') {
        // 正常断开，不视为错误
        return
      }
      lastError.value = err instanceof Error ? err : new Error(String(err))
      options.onError?.(lastError.value)
      disconnect()
    }
  }

  function disconnect() {
    if (abortController) {
      abortController.abort()
      abortController = null
    }
    isConnected.value = false
    isStreaming.value = false
  }

  return {
    isConnected,
    isStreaming,
    lastError,
    connect,
    disconnect,
  }
}
