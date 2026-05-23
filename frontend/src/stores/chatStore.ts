import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  type?: 'text' | 'code' | 'diagnosis' | 'resource' | 'simulator'
  timestamp: number
  agentName?: string
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
    if (session) {
      session.messages.push(message)
    }
  }

  function setStreaming(value: boolean) {
    isStreaming.value = value
  }

  function renameSession(sessionId: string, title: string) {
    const session = sessions.value.find(s => s.sessionId === sessionId)
    if (session) {
      session.title = title
    }
  }

  function clearCurrentSessionMessages() {
    const session = currentSession.value
    if (session) {
      session.messages = []
    }
  }

  function switchSession(sessionId: string) {
    currentSessionId.value = sessionId
  }

  function deleteSession(sessionId: string) {
    const idx = sessions.value.findIndex(s => s.sessionId === sessionId)
    if (idx === -1) return
    sessions.value.splice(idx, 1)
    if (currentSessionId.value === sessionId) {
      currentSessionId.value = sessions.value[0]?.sessionId || ''
    }
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
    createSession,
    addMessage,
    renameSession,
    clearCurrentSessionMessages,
    switchSession,
    deleteSession,
    ensureValidCurrentSession,
    setStreaming,
  }
}, {
  persist: true,
})
