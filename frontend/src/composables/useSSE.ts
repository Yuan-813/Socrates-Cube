import { ref } from 'vue'
import type { SSEPayload, DiagnosisResult, LearningPath, LearningResource } from '../types'
import { useChatStore } from '../stores/chatStore'
import { useUserStore } from '../stores/userStore'
import { useResourceStore } from '../stores/resourceStore'
import { usePathStore } from '../stores/pathStore'

/**
 * useChatSSE：与后端 /api/v1/chat/stream 对话，处理全部 SSE 事件
 */
export function useChatSSE() {
  const isStreaming = ref(false)
  const lastError = ref<string | null>(null)
  let abortController: AbortController | null = null

  const BASE_URL = import.meta.env.VITE_API_BASE_URL || ''

  async function send(
    message: string,
    userId: string,
    sessionId: string,
  ): Promise<void> {
    if (isStreaming.value) abort()

    const chatStore = useChatStore()
    const userStore = useUserStore()
    const resourceStore = useResourceStore()
    const pathStore = usePathStore()

    isStreaming.value = true
    lastError.value = null
    abortController = new AbortController()
    chatStore.setStreaming(true)

    // 预先插入空 assistant 消息，准备追加 token
    chatStore.addMessage(sessionId, {
      id: `msg-${Date.now()}`,
      role: 'assistant',
      content: '',
      timestamp: Date.now(),
      isStreaming: true,
    })

    try {
      const resp = await fetch(`${BASE_URL}/api/v1/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, user_id: userId, session_id: sessionId }),
        signal: abortController.signal,
      })

      if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
      if (!resp.body) throw new Error('响应体为空')

      const reader = resp.body.getReader()
      const decoder = new TextDecoder()
      let buf = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buf += decoder.decode(value, { stream: true })

        const parts = buf.split('\n\n')
        buf = parts.pop() ?? ''

        for (const part of parts) {
          const line = part.trim()
          if (!line.startsWith('data:')) continue
          const jsonStr = line.slice(5).trim()
          if (!jsonStr) continue
          try {
            const payload: SSEPayload = JSON.parse(jsonStr)
            _handleEvent(payload, sessionId, chatStore, userStore, resourceStore, pathStore)
          } catch {
            // 忽略非JSON行
          }
        }
      }
    } catch (e: unknown) {
      if (e instanceof Error && e.name !== 'AbortError') {
        lastError.value = e.message
      }
    } finally {
      chatStore.finalizeStreaming(sessionId)
      chatStore.setStreaming(false)
      isStreaming.value = false
      abortController = null
    }
  }

  function abort() {
    abortController?.abort()
    abortController = null
    isStreaming.value = false
  }

  return { isStreaming, lastError, send, abort }
}

export function useFetchSSE() {
  let abortController: AbortController | null = null

  async function connect(
    url: string,
    options: {
      body?: unknown
      onMessage?: (chunk: string) => void
      onDone?: () => void
      onError?: (error: Error) => void
    } = {},
  ) {
    abortController = new AbortController()
    try {
      const resp = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(options.body ?? {}),
        signal: abortController.signal,
      })
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
      if (!resp.body) throw new Error('empty response body')

      const reader = resp.body.getReader()
      const decoder = new TextDecoder()
      let buf = ''
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buf += decoder.decode(value, { stream: true })
        const parts = buf.split('\n\n')
        buf = parts.pop() ?? ''
        for (const part of parts) {
          const line = part.trim()
          if (!line.startsWith('data:')) continue
          const payload = JSON.parse(line.slice(5).trim()) as SSEPayload
          if (payload.event === 'token') {
            options.onMessage?.((payload.data as { token?: string })?.token ?? '')
          }
        }
      }
      options.onDone?.()
    } catch (error) {
      options.onError?.(error instanceof Error ? error : new Error(String(error)))
    }
  }

  function abort() {
    abortController?.abort()
    abortController = null
  }

  return { connect, abort }
}

// ------------------------------------------------------------------
// SSE 事件分发处理器
// ------------------------------------------------------------------
function _handleEvent(
  payload: SSEPayload,
  sessionId: string,
  chatStore: ReturnType<typeof useChatStore>,
  userStore: ReturnType<typeof useUserStore>,
  resourceStore: ReturnType<typeof useResourceStore>,
  pathStore: ReturnType<typeof usePathStore>,
) {
  switch (payload.event) {
    case 'agent_start':
      chatStore.updateAgentStatus(payload.agent_name, 'running', (payload.data as { message?: string })?.message ?? '')
      break

    case 'agent_end': {
      const d = payload.data as { message?: string; profile_summary?: object }
      chatStore.updateAgentStatus(payload.agent_name, 'done', d?.message ?? '')
      // Profiler 结束时顺便更新画像摘要
      if (payload.agent_name === 'Profiler' && d?.profile_summary) {
        userStore.updateFromSSE(d.profile_summary as Parameters<typeof userStore.updateFromSSE>[0])
      }
      break
    }

    case 'token':
      chatStore.appendStreamToken(sessionId, (payload.data as { token: string }).token)
      break

    case 'diagnosis':
      chatStore.setDiagnosisResult(payload.data as DiagnosisResult)
      break

    case 'resource':
      resourceStore.addResource(payload.data as LearningResource)
      break

    case 'path_update':
      pathStore.updateFromSSE(payload.data as LearningPath)
      break

    case 'error':
      console.error('[SSE error]', payload.data)
      break

    default:
      break
  }
}

