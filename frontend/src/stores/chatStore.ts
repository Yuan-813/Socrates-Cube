import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import type { DiagnosisResult, ChallengerPayload, ScopeNoticePayload } from '../types'

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  type?: 'text' | 'code' | 'diagnosis' | 'resource' | 'simulator'
  timestamp: number
  agentName?: string
  diagnosisResult?: DiagnosisResult
  isStreaming?: boolean
  // 响应质量元数据（由 done 事件填充）
  responseTimeMs?: number
  diagnosisConfidence?: number
  sourceCount?: number
  agentTrace?: AgentTraceItem[]
}

/** 每条消息的 Agent 执行步骤记录 */
export interface AgentTraceItem {
  agentName: string
  displayName: string
  durationMs: number
}

export interface AgentStatus {
  agentName: string
  status: 'running' | 'done'
  message: string
  toolCalls?: ToolCallStatus[]
}

export interface ToolCallStatus {
  toolName: string
  status: string
}

export interface ChatSession {
  sessionId: string
  title: string
  messages: ChatMessage[]
  createdAt: number
}

export const useChatStore = defineStore('chat', () => {
  const sessions = ref<ChatSession[]>([])
  const currentSessionId = ref<string>('')
  const isStreaming = ref<boolean>(false)
  const activeAgents = ref<AgentStatus[]>([])
  const currentAgent = ref<string | null>(null)
  const lastDiagnosis = ref<DiagnosisResult | null>(null)
  const lastChallenger = ref<ChallengerPayload | null>(null)
  const lastScopeNotice = ref<ScopeNoticePayload | null>(null)
  /** KG高亮节点 ID集合（AI回答后实时更新） */
  const kgHighlightedNodes = ref<string[]>([])
  /** 历史诊断置信度序列（最近12次，供画像趋势图使用） */
  const confidenceHistory = ref<number[]>([])

  const currentSession = computed<ChatSession | null>(() => {
    if (!currentSessionId.value) return null
    return sessions.value.find(s => s.sessionId === currentSessionId.value) || null
  })

  function createSession(title: string = '新会话') {
    const session: ChatSession = {
      sessionId: `session-${Date.now()}`,
      title,
      messages: [],
      createdAt: Date.now(),
    }
    sessions.value.unshift(session)
    currentSessionId.value = session.sessionId
    return session
  }

  function addMessage(sessionId: string, message: ChatMessage) {
    const session = sessions.value.find(s => s.sessionId === sessionId)
    if (session) session.messages.push(message)
  }

  /** 向最后一条 assistant 消息追加 token */
  function appendStreamToken(sessionId: string, token: string) {
    const session = sessions.value.find(s => s.sessionId === sessionId)
    if (!session) return
    const last = session.messages[session.messages.length - 1]
    if (last && last.role === 'assistant') {
      last.content += token
    }
  }

  /** 标记最后一条 assistant 消息流结束 */
  function finalizeStreaming(sessionId: string) {
    const session = sessions.value.find(s => s.sessionId === sessionId)
    if (!session) return
    const last = session.messages[session.messages.length - 1]
    if (last && last.role === 'assistant') {
      // 内容为空时（如后端异常无输出）给出友好提示
      if (!last.content || last.content.trim() === '') {
        last.content = '> ⚠️ AI 未返回任何内容，可能是后端服务暂时不可用，请稍后重试。'
      }
      last.isStreaming = false
    }
  }

  /** 将执行链路、耗时、置信度等元数据写入最后一条 assistant 消息 */
  function finalizeMessageMetadata(
    sessionId: string,
    meta: {
      responseTimeMs?: number
      agentTrace?: import('./chatStore').AgentTraceItem[]
      diagnosisConfidence?: number
      sourceCount?: number
    },
  ) {
    const session = sessions.value.find(s => s.sessionId === sessionId)
    if (!session) return
    const last = session.messages[session.messages.length - 1]
    if (last && last.role === 'assistant') {
      if (meta.responseTimeMs !== undefined) last.responseTimeMs = meta.responseTimeMs
      if (meta.agentTrace !== undefined) last.agentTrace = meta.agentTrace
      if (meta.diagnosisConfidence !== undefined) last.diagnosisConfidence = meta.diagnosisConfidence
      if (meta.sourceCount !== undefined) last.sourceCount = meta.sourceCount
    }
  }

  /** 清除诊断结果（新一轮对话开始时调用） */
  function clearDiagnosis() {
    lastDiagnosis.value = null
    kgHighlightedNodes.value = []
  }

  function setKGNodes(nodeIds: string[]) {
    kgHighlightedNodes.value = nodeIds
  }

  /** 设置当前正在运行的 Agent（AgentStatusBar 使用） */
  function setCurrentAgent(agentName: string | null) {
    currentAgent.value = agentName
  }

  /** 更新代理运行状态（显示在状态栏） */
  function updateAgentStatus(agentName: string, status: 'running' | 'done', message: string) {
    const idx = activeAgents.value.findIndex(a => a.agentName === agentName)
    if (idx >= 0) {
      activeAgents.value[idx] = { ...activeAgents.value[idx], agentName, status, message }
    } else {
      activeAgents.value.push({ agentName, status, message, toolCalls: [] })
    }
    // 清理已完成的代理（保留最近5条）
    activeAgents.value = activeAgents.value.filter(a => a.status === 'running').slice(-5)
  }

  /** 更新工具调用状态 */
  function updateToolCall(agentName: string, toolName: string, status: string) {
    const idx = activeAgents.value.findIndex(a => a.agentName === agentName)
    if (idx < 0) {
      activeAgents.value.push({ agentName, status: 'running', message: '', toolCalls: [{ toolName, status }] })
      return
    }
    const agent = activeAgents.value[idx]
    if (!agent.toolCalls) agent.toolCalls = []
    const tcIdx = agent.toolCalls.findIndex(t => t.toolName === toolName)
    if (tcIdx >= 0) {
      agent.toolCalls[tcIdx] = { toolName, status }
    } else {
      agent.toolCalls.push({ toolName, status })
    }
  }

  /** 设置最新 Challenger 检验题 */
  function setChallengerPayload(payload: ChallengerPayload) {
    lastChallenger.value = payload
  }

  function setScopeNotice(payload: ScopeNoticePayload | null) {
    lastScopeNotice.value = payload
  }

  function setDiagnosisResult(diag: DiagnosisResult) {
    lastDiagnosis.value = diag
    // 记录置信度历史（最近12次，为画像趋势提供数据）
    if (diag.confidence != null) {
      confidenceHistory.value.push(Math.round(diag.confidence * 100))
      if (confidenceHistory.value.length > 12) {
        confidenceHistory.value = confidenceHistory.value.slice(-12)
      }
    }
    // 把诊断结果附加到最后一条助手消息
    const session = currentSession.value
    if (session) {
      const lastMsg = session.messages[session.messages.length - 1]
      if (lastMsg && lastMsg.role === 'assistant') {
        lastMsg.diagnosisResult = diag
      }
    }
  }

  function setStreaming(value: boolean) {
    isStreaming.value = value
    if (!value) {
      activeAgents.value = []
      currentAgent.value = null
    }
  }

  function clearCurrentSessionMessages() {
    const session = currentSession.value
    if (session) session.messages = []
  }

  function ensureValidCurrentSession() {
    if (currentSession.value) return currentSession.value
    if (sessions.value.length > 0) {
      currentSessionId.value = sessions.value[0].sessionId
      return sessions.value[0]
    }
    return createSession('新会话')
  }

  return {
    sessions,
    currentSessionId,
    currentSession,
    isStreaming,
    activeAgents,
    currentAgent,
    lastDiagnosis,
    lastChallenger,
    lastScopeNotice,
    confidenceHistory,
    kgHighlightedNodes,
    createSession,
    addMessage,
    appendStreamToken,
    finalizeStreaming,
    setCurrentAgent,
    updateAgentStatus,
    updateToolCall,
    setDiagnosisResult,
    setChallengerPayload,
    setScopeNotice,
    setStreaming,
    clearCurrentSessionMessages,
    ensureValidCurrentSession,
    finalizeMessageMetadata,
    clearDiagnosis,
    setKGNodes,
  }
}, {
  persist: {
    // 只持久化会话数据和分析结果，不持久化流式临时状态
    paths: ['sessions', 'currentSessionId', 'lastDiagnosis', 'lastChallenger', 'confidenceHistory'],
  },
})
