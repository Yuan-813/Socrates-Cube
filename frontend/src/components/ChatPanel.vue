<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'
import { useChatSSE } from '@/composables/useSSE'
import { useChatStore } from '@/stores/chatStore'
import { useUserStore } from '@/stores/userStore'
import ChatMessage from './ChatMessage.vue'
import ScopeNotice from './ScopeNotice.vue'
import type { ChatMessage as ChatMessageType } from '@/stores/chatStore'

const chatStore = useChatStore()
const userStore = useUserStore()
const chatSSE = useChatSSE()
const props = defineProps<{ agentPersona?: string }>()
const inputText = ref('')
const messagesContainer = ref<HTMLElement>()
const inputRef = ref<any>(null)

const quickPrompts = [
  { icon: 'QuestionFilled', text: '什么是TCP三次握手？', label: '概念询问' },
  { icon: 'VideoPlay', text: '演示三次握手过程', label: '仿真请求' },
  { icon: 'EditPen', text: '生成协议练习题', label: '生成题目' },
  { icon: 'FirstAidKit', text: '诊断我的理解水平', label: '能力诊断' },
]

const streamingMessage = computed(() => {
  const session = chatStore.currentSession
  if (!session || !chatStore.isStreaming) return null
  const last = session.messages[session.messages.length - 1]
  return last?.role === 'assistant' && last.isStreaming ? last : null
})

async function sendMessage() {
  if (!inputText.value.trim() || chatStore.isStreaming) return

  const userMsg: ChatMessageType = {
    id: `msg-${Date.now()}`,
    role: 'user',
    content: inputText.value,
    timestamp: Date.now(),
  }

  const sessionId = chatStore.currentSession?.sessionId || chatStore.createSession().sessionId
  chatStore.addMessage(sessionId, userMsg)
  // 发送新消息时立即清除上一轮的诊断结果，避免展示过期数据
  chatStore.clearDiagnosis()

  const text = inputText.value
  inputText.value = ''

  await nextTick()
  scrollToBottom()

  await chatSSE.send(text, userStore.userId, sessionId, props.agentPersona || 'professor')

  if (chatSSE.lastError.value) {
    const session = chatStore.currentSession
    const last = session?.messages[session.messages.length - 1]
    if (last && last.role === 'assistant') {
      last.content = last.content || `连接异常：${chatSSE.lastError.value}`
      last.agentName = 'System'
    }
  }

  scrollToBottom()
}

function scrollToBottom() {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

function setPrompt(text: string) {
  inputText.value = text
  inputRef.value?.focus()
}

function clearChat() {
  chatStore.clearCurrentSessionMessages()
}

onMounted(() => {
  chatStore.ensureValidCurrentSession()

  // 修复：重置可能因刷新/中断而持久化的残留流式状态
  if (chatStore.isStreaming) {
    chatStore.setStreaming(false)
  }
  // 同时清理消息列表中可能残留的 isStreaming 标记
  const session = chatStore.currentSession
  if (session) {
    session.messages.forEach(m => {
      if (m.isStreaming) {
        m.isStreaming = false
        // 如果内容为空说明响应被中断，添加提示
        if (!m.content.trim()) m.content = '*（该回复因连接中断未完成）*'
      }
    })
  }

  scrollToBottom()
})

defineExpose({ setPrompt })
</script>

<template>
  <div class="chat-panel">
    <div ref="messagesContainer" class="messages-container">
      <div v-if="!chatStore.currentSession?.messages.length && !chatStore.isStreaming" class="chat-welcome">
        <div class="welcome-icon">
          <el-icon size="48" color="#3b82f6"><ChatDotSquare /></el-icon>
        </div>
        <h3 class="welcome-title">Socrates Cube AI 教练</h3>
        <p class="welcome-desc">
          我是你的计算机网络协议学习助手。我可以帮你诊断理解误区、<br>
          演示协议交互过程、生成个性化学习资源。
        </p>
        <div class="welcome-prompts">
          <div
            v-for="prompt in quickPrompts"
            :key="prompt.text"
            class="prompt-chip"
            @click="setPrompt(prompt.text)"
          >
            <el-icon size="14"><component :is="prompt.icon" /></el-icon>
            <span>{{ prompt.label }}</span>
          </div>
        </div>
      </div>

      <ScopeNotice
        v-if="chatStore.lastScopeNotice"
        :title="chatStore.lastScopeNotice.title"
        :description="chatStore.lastScopeNotice.description"
      />

      <ChatMessage
        v-for="msg in chatStore.currentSession?.messages"
        :key="msg.id"
        :message="msg"
      />

      <div v-if="streamingMessage && !streamingMessage.content" class="streaming-row">
        <div class="streaming-bubble">
          <div class="streaming-header">
            <el-avatar :size="28" icon="ChatDotRound" style="background-color: #10b981" />
            <span class="streaming-role">AI教练</span>
            <span class="typing-indicator">正在输入...</span>
          </div>
        </div>
      </div>
    </div>

    <div class="input-area">
      <div class="input-toolbar">
        <div class="toolbar-hints">
          <span class="hint-text">已连接后端 SSE</span>
          <span
            v-for="prompt in quickPrompts.slice(0, 3)"
            :key="prompt.text"
            class="hint-chip"
            @click="setPrompt(prompt.text)"
          >{{ prompt.label }}</span>
        </div>
        <el-button link size="small" @click="clearChat">
          <el-icon size="14"><Delete /></el-icon>
          清空对话
        </el-button>
      </div>
      <div class="input-row">
        <el-input
          ref="inputRef"
          v-model="inputText"
          type="textarea"
          :rows="2"
          placeholder="请输入你的问题，支持协议概念、流程、故障排查等...（Enter 发送，Shift+Enter 换行）"
          resize="none"
          @keydown="handleKeydown"
        />
        <el-button
          class="send-btn"
          type="primary"
          size="default"
          :disabled="!inputText.trim() || chatStore.isStreaming"
          @click="sendMessage"
        >
          <el-icon size="18"><Promotion /></el-icon>
        </el-button>
      </div>
      <div class="input-meta">
        <span class="meta-text">Socrates Cube · 计算机网络协议智能教练</span>
        <span v-if="chatStore.isStreaming" class="meta-status">正在生成回复...</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chat-panel {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 180px);
  min-height: 500px;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  background-color: #f8fafc;
  border-radius: 12px;
}

.streaming-row {
  display: flex;
  max-width: 88%;
  align-self: flex-start;
}

.streaming-bubble {
  padding: 14px 18px;
  border-radius: 14px;
  background-color: #fff;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  border: 1px solid #e2e8f0;
}

.streaming-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.streaming-role {
  font-weight: 500;
  font-size: 13px;
  color: #475569;
}

.typing-indicator {
  color: #94a3b8;
  font-size: 12px;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.chat-welcome {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  text-align: center;
  flex: 1;
}

.welcome-icon {
  width: 80px;
  height: 80px;
  border-radius: 20px;
  background-color: #eff6ff;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
}

.welcome-title {
  font-size: 20px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 8px;
}

.welcome-desc {
  font-size: 14px;
  color: #64748b;
  line-height: 1.6;
  margin-bottom: 24px;
}

.welcome-prompts {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: center;
}

.prompt-chip {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background-color: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 20px;
  font-size: 13px;
  color: #475569;
  cursor: pointer;
  transition: all 0.2s;
}

.prompt-chip:hover {
  border-color: #3b82f6;
  color: #3b82f6;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.15);
}

.input-area {
  margin-top: 36px;
  background-color: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  padding: 12px;
  box-shadow: 0 10px 24px -20px rgba(15, 23, 42, 0.3);
}

.input-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
  padding-bottom: 8px;
  border-bottom: 1px solid #f1f5f9;
}

.toolbar-hints {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.hint-text {
  font-size: 12px;
  color: #94a3b8;
}

.hint-chip {
  font-size: 12px;
  color: #3b82f6;
  cursor: pointer;
  padding: 2px 8px;
  border-radius: 4px;
  background-color: #eff6ff;
  transition: background-color 0.2s;
}

.hint-chip:hover {
  background-color: #dbeafe;
}

.input-row {
  display: flex;
  gap: 8px;
  align-items: flex-end;
}

.input-row :deep(.el-textarea__inner) {
  border-radius: 8px;
  resize: none;
}

.send-btn {
  height: 44px;
  width: 44px;
  border-radius: 10px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.input-meta {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
}

.meta-text {
  font-size: 11px;
  color: #cbd5e1;
}

.meta-status {
  font-size: 11px;
  color: #3b82f6;
  animation: pulse 1.5s infinite;
}
</style>
