import type { SSEPayload } from '../types'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || ''

export interface ChatRequest {
  message: string
  session_id?: string
  user_id?: string
}

/**
 * 发起 SSE 流式对话请求（POST body），返回 AbortController 供调用方取消。
 */
export function startChatStream(
  req: ChatRequest,
  onEvent: (payload: SSEPayload) => void,
  onDone: () => void,
  onError: (err: Error) => void,
): AbortController {
  const controller = new AbortController()

  fetch(`${BASE_URL}/api/v1/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message: req.message,
      user_id: req.user_id ?? 'student-001',
      session_id: req.session_id ?? null,
    }),
    signal: controller.signal,
  })
    .then(async (resp) => {
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
      if (!resp.body) throw new Error('响应体为空')

      const reader = resp.body.getReader()
      const decoder = new TextDecoder()
      let buf = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buf += decoder.decode(value, { stream: true })

        // SSE 格式：每条消息以 \n\n 结尾
        const parts = buf.split('\n\n')
        buf = parts.pop() ?? ''

        for (const part of parts) {
          const line = part.trim()
          if (!line.startsWith('data:')) continue
          const jsonStr = line.slice(5).trim()
          if (!jsonStr) continue
          try {
            const payload: SSEPayload = JSON.parse(jsonStr)
            if (payload.event === 'done') {
              onDone()
              return
            }
            onEvent(payload)
          } catch {
            // 跳过非JSON行
          }
        }
      }
      onDone()
    })
    .catch((err: Error) => {
      if (err.name !== 'AbortError') onError(err)
    })

  return controller
}
