import apiClient from './client'

export interface ChatRequest {
  message: string
  sessionId?: string
  userId?: string
}

export function createSSEConnection(message: string, onMessage: (chunk: string) => void, onDone: () => void, onError: (err: Error) => void) {
  const eventSource = new EventSource(`/api/v1/chat/stream?message=${encodeURIComponent(message)}`)

  eventSource.onmessage = (event) => {
    if (event.data === '[DONE]') {
      onDone()
      eventSource.close()
    } else {
      onMessage(event.data)
    }
  }

  eventSource.onerror = (error) => {
    onError(new Error('SSE连接错误'))
    eventSource.close()
  }

  return eventSource
}
