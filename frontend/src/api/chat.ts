import apiClient from './client'
import { mockDiagnosis, mockLogs, mockPath, mockProfile, mockResources } from './mock'
import type { AgentLog, DiagnosisResult, LearningPathNode, LearningResource, StudentProfile } from '@/types'
import type { ChatStreamPayload, SSEEvent } from '@/types/sse'

export interface ChatRequest {
  message: string
  sessionId?: string
  userId?: string
}

export interface ChatPanelPayload {
  profile: StudentProfile
  diagnosis: DiagnosisResult
  resources: LearningResource[]
  learningPath: LearningPathNode[]
  logs: AgentLog[]
  simulatorSummary: string
}

export interface StreamChatOptions {
  payload: ChatStreamPayload
  useMock?: boolean
  endpoint?: string
  onEvent?: (event: SSEEvent) => void
  onToken?: (chunk: string) => void
  onDone?: () => void
  onError?: (err: Error) => void
}

export function getMockChatPanels(message: string): ChatPanelPayload {
  const normalized = message.toLowerCase()
  const simulatorSummary = normalized.includes('握手')
    ? '已匹配 TCP 三次握手仿真场景，可在协议仿真区播放 SYN -> SYN+ACK -> ACK。'
    : normalized.includes('http')
      ? '已匹配 HTTP 请求/响应仿真场景，可展示应用层到传输层的封装过程。'
      : '当前问题更适合做概念解释与误解诊断，仿真区保持待命。'

  return {
    profile: mockProfile,
    diagnosis: {
      ...mockDiagnosis,
      trigger: `学生提问：${message}`,
    },
    resources: mockResources,
    learningPath: mockPath,
    logs: mockLogs,
    simulatorSummary,
  }
}

function parseSSEEvent(raw: string): SSEEvent {
  try {
    return JSON.parse(raw) as SSEEvent
  } catch {
    return {
      event: 'token',
      data: raw,
      timestamp: new Date().toISOString(),
    }
  }
}

async function streamWithFetch(options: StreamChatOptions): Promise<void> {
  const { payload, endpoint = '/api/v1/chat/stream', onEvent, onToken, onDone, onError } = options

  try {
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'text/event-stream',
      },
      body: JSON.stringify(payload),
    })

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }

    if (!response.body) {
      throw new Error('当前环境不支持流式响应')
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) {
        onDone?.()
        return
      }

      buffer += decoder.decode(value, { stream: true })
      const parts = buffer.split('\n')
      buffer = parts.pop() || ''

      for (const line of parts) {
        const trimmed = line.trim()
        if (!trimmed || !trimmed.startsWith('data:')) continue

        const payloadText = trimmed.slice(5).trim()
        const event = parseSSEEvent(payloadText)
        onEvent?.(event)

        if (event.event === 'token' && typeof event.data === 'string') {
          onToken?.(event.data)
        }

        if (event.event === 'error') {
          onError?.(new Error(typeof event.data === 'string' ? event.data : 'SSE 返回错误'))
        }

        if (event.event === 'done') {
          onDone?.()
          return
        }
      }
    }
  } catch (err) {
    const error = err instanceof Error ? err : new Error(String(err))
    onError?.(error)
  }
}

function streamWithMock(options: StreamChatOptions): Promise<void> {
  const { payload, onEvent, onToken, onDone } = options
  const fullReply = `收到你的问题："${payload.message}"\n\n我正在从协议概念、误解模式和学习路径三个角度为你分析。\n\n当前为前端演示模式，你已经可以看到稳定的流式输出、右侧联动摘要和仿真提示。`

  return new Promise((resolve) => {
    let index = 0

    onEvent?.({
      event: 'agent_start',
      agent_name: 'Orchestrator',
      data: '开始调度对话主链路',
      timestamp: new Date().toISOString(),
    })

    const timer = window.setInterval(() => {
      if (index >= fullReply.length) {
        window.clearInterval(timer)
        onEvent?.({
          event: 'done',
          agent_name: 'Orchestrator',
          data: 'done',
          timestamp: new Date().toISOString(),
        })
        onDone?.()
        resolve()
        return
      }

      const chunk = fullReply[index]
      index += 1

      onEvent?.({
        event: 'token',
        agent_name: 'Orchestrator',
        data: chunk,
        timestamp: new Date().toISOString(),
      })
      onToken?.(chunk)
    }, 26)
  })
}

export async function streamChat(options: StreamChatOptions): Promise<void> {
  if (options.useMock) {
    await streamWithMock(options)
    return
  }

  await streamWithFetch(options)
}

export async function checkChatBackend(): Promise<boolean> {
  try {
    const response = await apiClient.get('/api/v1/chat/test')
    return response.status === 200
  } catch {
    return false
  }
}
