import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import type { DiagnosisResult } from '../types'

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  type?: 'text' | 'code' | 'diagnosis' | 'resource' | 'simulator'
  timestamp: number
  agentName?: string
  diagnosisResult?: DiagnosisResult
  isStreaming?: boolean
}

export interface AgentStatus {
  agentName: string
  status: 'running' | 'done'
  message: string
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
  const lastDiagnosis = ref<DiagnosisResult | null>(null)

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
      last.isStreaming = false
    }
  }

  /** 更新代理运行状态（显示在状态栏） */
  function updateAgentStatus(agentName: string, status: 'running' | 'done', message: string) {
    const idx = activeAgents.value.findIndex(a => a.agentName === agentName)
    if (idx >= 0) {
      activeAgents.value[idx] = { agentName, status, message }
    } else {
      activeAgents.value.push({ agentName, status, message })
    }
    // 清理已完成的代理（保留最近5条）
    activeAgents.value = activeAgents.value.filter(a => a.status === 'running').slice(-5)
  }

  /** 设置最新诊断结果 */
  function setDiagnosisResult(diag: DiagnosisResult) {
    lastDiagnosis.value = diag
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
    if (!value) activeAgents.value = []
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
    lastDiagnosis,
    createSession,
    addMessage,
    appendStreamToken,
    finalizeStreaming,
    updateAgentStatus,
    setDiagnosisResult,
    setStreaming,
    clearCurrentSessionMessages,
    ensureValidCurrentSession,
  }
}, {
  persist: true,
})
