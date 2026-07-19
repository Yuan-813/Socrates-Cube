import { ref } from 'vue'
import type { SSEPayload, DiagnosisResult, LearningPath, LearningResource } from '../types'
import { useChatStore } from '../stores/chatStore'
import type { AgentTraceItem } from '../stores/chatStore'
import { useUserStore } from '../stores/userStore'
import { useResourceStore } from '../stores/resourceStore'
import { usePathStore } from '../stores/pathStore'

/** Agent 显示名称映射 */
const AGENT_DISPLAY_NAMES: Record<string, string> = {
  Orchestrator: '指挥官',
  Retriever: '知识检索',
  Diagnosis: '认知诊断',
  DiagnosisAgent: '认知诊断',
  Profiler: '画像更新',
  ProfilerAgent: '画像更新',
  ResourceGenerator: '资源生成',
  PathPlanner: '路径规划',
  PathPlannerAgent: '路径规划',
  Challenger: '挑战追问',
  InterventionSelector: '干预选择',
  TrustMechanism: '可信校验',
}

/**
 * useChatSSE：与后端 /api/v1/chat/stream 对话，处理全部 SSE 事件
 *
 * 稳定性：支持 SSE 断线自动重连（最多 3 次，指数退避）
 */
export function useChatSSE() {
  const isStreaming = ref(false)
  const lastError = ref<string | null>(null)
  let abortController: AbortController | null = null
  let retryCount = 0
  const MAX_RETRIES = 3

  const BASE_URL = import.meta.env.VITE_API_BASE_URL || ''
  const SSE_ENDPOINT = import.meta.env.VITE_SSE_ENDPOINT || '/api/v1/chat/stream'
  const IS_MOCK = import.meta.env.VITE_MOCK_MODE === 'true'

  async function send(
    message: string,
    userId: string,
    sessionId: string,
    agentPersona: string = 'professor',
  ): Promise<void> {
    if (isStreaming.value) abort()

    const chatStore = useChatStore()
    const userStore = useUserStore()
    const resourceStore = useResourceStore()
    const pathStore = usePathStore()

    isStreaming.value = true
    lastError.value = null
    retryCount = 0
    abortController = new AbortController()
    chatStore.setStreaming(true)
    chatStore.setScopeNotice(null)
    chatStore.clearDiagnosis()    // 清除上轮诊断，让面板进入诊断中状态

    // 追踪 Agent 执行链路的本地状态
    const agentTimings = new Map<string, number>()
    const agentTrace: AgentTraceItem[] = []
    let sourceCount = 0
    let diagnosisConfidence = 0

    // 预先插入空 assistant 消息，准备追加 token
    chatStore.addMessage(sessionId, {
      id: `msg-${Date.now()}`,
      role: 'assistant',
      content: '',
      timestamp: Date.now(),
      isStreaming: true,
    })

    await _doFetch(
      message, userId, sessionId,
      chatStore, userStore, resourceStore, pathStore,
      agentTimings, agentTrace,
      agentPersona,
      (sc) => { sourceCount = sc },
      (dc) => { diagnosisConfidence = dc },
      (totalMs) => {
        chatStore.finalizeMessageMetadata(sessionId, {
          responseTimeMs: totalMs,
          agentTrace: [...agentTrace],
          diagnosisConfidence,
          sourceCount,
        })
      },
    )
  }

  /** 连接超时时间（ms），超过则降级为本地 Mock */
  const CONNECTION_TIMEOUT = 8000

  async function _doFetch(
    message: string,
    userId: string,
    sessionId: string,
    chatStore: ReturnType<typeof useChatStore>,
    userStore: ReturnType<typeof useUserStore>,
    resourceStore: ReturnType<typeof useResourceStore>,
    pathStore: ReturnType<typeof usePathStore>,
    agentTimings: Map<string, number>,
    agentTrace: AgentTraceItem[],
    agentPersona: string,
    setSourceCount: (n: number) => void,
    setDiagConf: (n: number) => void,
    onDone: (totalMs: number) => void,
  ): Promise<void> {
    try {
      // 使用循环而非递归进行重试，避免 finally 提前执行
      while (retryCount <= MAX_RETRIES) {
        let timeoutId: ReturnType<typeof setTimeout> | null = null
        let timedOut = false

        abortController = new AbortController()
        timeoutId = setTimeout(() => {
          timedOut = true
          abortController?.abort()
        }, CONNECTION_TIMEOUT)

        try {
          const resp = await fetch(`${BASE_URL}${SSE_ENDPOINT}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message, user_id: userId, session_id: sessionId, agent_persona: agentPersona }),
            signal: abortController.signal,
          })

          // 收到响应后清除超时
          if (timeoutId) { clearTimeout(timeoutId); timeoutId = null }

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
                _collectTrace(payload, agentTimings, agentTrace, setSourceCount, setDiagConf, onDone)
              } catch {
                // 忽略非 JSON 行
              }
            }
          }
          // 成功完成，退出重试循环
          retryCount = 0
          return
        } catch (e: unknown) {
          if (timeoutId) { clearTimeout(timeoutId); timeoutId = null }

          if (e instanceof Error && e.name === 'AbortError') {
            if (timedOut) {
              // 超时导致的 abort，直接降级 Mock
              console.warn('[SSE] 后端连接超时，自动降级为本地 Mock 响应')
              await _mockFallback(message, sessionId, chatStore, userStore, resourceStore, pathStore,
                agentTimings, agentTrace, setSourceCount, setDiagConf, onDone)
              return
            }
            // 用户手动 abort
            return
          }

          // 网络错误/HTTP错误，尝试重试
          if (retryCount < MAX_RETRIES && !IS_MOCK) {
            retryCount++
            const delay = Math.min(1000 * Math.pow(2, retryCount - 1), 3000)
            console.warn(`[SSE] 连接断开，${delay}ms 后重试 (${retryCount}/${MAX_RETRIES})`)
            await new Promise(resolve => setTimeout(resolve, delay))
            continue // 继续循环重试
          }

          // 所有重试失败后降级为 Mock
          console.warn('[SSE] 后端不可用，降级为本地 Mock 响应')
          await _mockFallback(message, sessionId, chatStore, userStore, resourceStore, pathStore,
            agentTimings, agentTrace, setSourceCount, setDiagConf, onDone)
          return
        }
      }
    } finally {
      chatStore.finalizeStreaming(sessionId)
      chatStore.setStreaming(false)
      isStreaming.value = false
      abortController = null
    }
  }

  /**
   * 本地 Mock 降级：当后端不可用时，模拟一个智能回复
   */
  async function _mockFallback(
    message: string,
    sessionId: string,
    chatStore: ReturnType<typeof useChatStore>,
    _userStore: ReturnType<typeof useUserStore>,
    _resourceStore: ReturnType<typeof useResourceStore>,
    _pathStore: ReturnType<typeof usePathStore>,
    agentTimings: Map<string, number>,
    agentTrace: AgentTraceItem[],
    setSourceCount: (n: number) => void,
    setDiagConf: (n: number) => void,
    onDone: (totalMs: number) => void,
  ): Promise<void> {
    // 生成一个上下文相关的 Mock 回复
    const mockResponses: Record<string, string> = {
      '你好': '你好！我是 Socrates Cube AI 教练，专注于计算机网络协议教学。\n\n我可以帮你：\n- 🔍 **诊断理解误区** — 识别你对协议细节的认知偏差\n- 🎭 **演示协议交互** — 可视化 TCP/IP 协议栈的工作过程\n- 📚 **生成学习资源** — 根据你的水平定制练习题和讲义\n- 🗺️ **规划学习路径** — 从 RFC 标准出发构建知识图谱\n\n请随时向我提问！比如「什么是TCP三次握手」或「演示DNS解析过程」。',
      'default': `关于「${message}」，这是一个很好的问题！\n\n在计算机网络中，理解协议的设计意图和工程实践同样重要。让我从以下几个维度为你分析：\n\n1. **协议规范层面** — 参照 RFC 标准文档中的定义\n2. **实现机制层面** — 协议栈如何具体执行\n3. **应用场景层面** — 为什么要这样设计\n\n> ⚠️ *当前为离线演示模式，后端服务未连接。完整的 AI 分析需要启动后端服务。*\n\n如需启动后端，请运行 \`start.bat\` 或 \`uvicorn src.loopse.main:app --reload --port 8000\`。`,
    }

    const response = mockResponses[message.trim()] || mockResponses['default']

    // 模拟打字效果（逐 token 输出）
    chatStore.updateAgentStatus('Orchestrator', 'running', '正在生成回复（离线模式）')
    agentTimings.set('Orchestrator', Date.now())

    const tokens = response.split('')
    const CHUNK_SIZE = 3
    for (let i = 0; i < tokens.length; i += CHUNK_SIZE) {
      const chunk = tokens.slice(i, i + CHUNK_SIZE).join('')
      chatStore.appendStreamToken(sessionId, chunk)
      await new Promise(r => setTimeout(r, 20))
    }

    agentTrace.push({
      agentName: 'Orchestrator',
      displayName: '指挥官',
      durationMs: Date.now() - (agentTimings.get('Orchestrator') || Date.now()),
    })
    chatStore.updateAgentStatus('Orchestrator', 'done', '回复完成（离线模式）')
    setSourceCount(0)
    setDiagConf(0)
    onDone(Date.now() - (agentTimings.get('Orchestrator') || Date.now()))
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
// SSE 执行链路 & 元数据采集（每条消息级）
// ------------------------------------------------------------------
function _collectTrace(
  payload: SSEPayload,
  agentTimings: Map<string, number>,
  agentTrace: AgentTraceItem[],
  setSourceCount: (n: number) => void,
  setDiagConf: (n: number) => void,
  onDone: (totalMs: number) => void,
) {
  const name = payload.agent_name
  const data = payload.data as Record<string, unknown>

  if (payload.event === 'agent_start') {
    // 跳过运营性接头（Orchestrator 生成回复那条不计入链路）
    const skip = new Set(['Orchestrator', 'TrustMechanism', 'InterventionSelector'])
    if (!skip.has(name)) agentTimings.set(name, Date.now())
  } else if (payload.event === 'agent_end') {
    const start = agentTimings.get(name)
    if (start !== undefined) {
      agentTrace.push({
        agentName: name,
        displayName: AGENT_DISPLAY_NAMES[name] ?? name,
        durationMs: Date.now() - start,
      })
      agentTimings.delete(name)
    }
  } else if (payload.event === 'tool_call') {
    const rc = data?.result_count
    if (typeof rc === 'number') setSourceCount(rc)
  } else if (payload.event === 'diagnosis') {
    const conf = data?.confidence
    if (typeof conf === 'number') setDiagConf(conf)
  } else if (payload.event === 'done') {
    const ms = data?.total_time_ms
    onDone(typeof ms === 'number' ? ms : 0)
  }
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
      chatStore.setCurrentAgent(payload.agent_name)
      chatStore.updateAgentStatus(payload.agent_name, 'running', (payload.data as { message?: string })?.message ?? '')
      if (payload.agent_name === 'ResourceGenerator') {
        resourceStore.updateGenerationProgress('', 0, 5)
      }
      break

    case 'agent_end': {
      const d = payload.data as { message?: string; profile_summary?: object }
      chatStore.updateAgentStatus(payload.agent_name, 'done', d?.message ?? '')
      chatStore.setCurrentAgent(null)
      if (payload.agent_name === 'ResourceGenerator') {
        resourceStore.updateGenerationProgress('', 5, 5)
      }
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

    case 'intervention_suggested': {
      const interventionData = payload.data as { recommendations?: any[] }
      if (interventionData?.recommendations && chatStore.lastDiagnosis) {
        chatStore.lastDiagnosis.recommended_interventions = interventionData.recommendations
      }
      break
    }

    case 'resource': {
      const res = payload.data as LearningResource
      resourceStore.addResource(res)
      const { current, total } = resourceStore.generationProgress
      resourceStore.updateGenerationProgress(
        res.resource_type ?? '',
        Math.min(current + 1, total || 5),
        total || 5,
      )
      break
    }

    case 'path_update':
      pathStore.updateFromSSE(payload.data as LearningPath)
      break

    case 'state_change':
      chatStore.updateAgentStatus(
        payload.agent_name,
        'running',
        (payload.data as { message?: string })?.message ?? '状态切换',
      )
      break

    case 'challenger':
      chatStore.setChallengerPayload(payload.data as import('../types').ChallengerPayload)
      break

    case 'scope_notice':
      chatStore.setScopeNotice(payload.data as import('../types').ScopeNoticePayload)
      break

    case 'tool_call': {
      const d = payload.data as { tool_name?: string; status?: string }
      chatStore.updateToolCall(payload.agent_name, d?.tool_name ?? '', d?.status ?? '')
      break
    }

    case 'kg_nodes': {
      const nodeData = payload.data as { node_ids?: string[] }
      if (nodeData?.node_ids?.length) {
        chatStore.setKGNodes(nodeData.node_ids)
      }
      break
    }

    case 'done':
      chatStore.setStreaming(false)
      break

    case 'error': {
      const errData = payload.data as { error?: string }
      const errMsg = errData?.error || 'AI 服务暂时不可用，请稍后重试'
      console.error('[SSE error]', payload.data)
      // 将错误信息插入到当前 assistant 消息内，保证用户可见
      chatStore.appendStreamToken(sessionId, `\n\n> ⚠️ **AI 服务错误**：${errMsg}`)
      break
    }

    default:
      break
  }
}

