<script setup lang="ts">
import { onMounted, onUnmounted, watch, ref, computed, nextTick } from 'vue'
import { useVirtualTeacher, STATE_META, EMOTION_GLOW, type TeacherState } from '@/composables/useVirtualTeacher'
import { renderMarkdown } from '@/utils/markdown'

const props = defineProps<{
  modelValue: boolean
  currentResponse?: string
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
}>()

const {
  isInitialized, isPlaying, error,
  teacherState, teacherEmotion,
  initialize, speak, stop, setState,
} = useVirtualTeacher()

const isLoading = ref(true)
const hasVideo  = ref(false)
const idleVideoRef     = ref<HTMLVideoElement | null>(null)
const speakingVideoRef = ref<HTMLVideoElement | null>(null)

const messages  = ref<{ role: 'user' | 'assistant'; content: string; id: string }[]>([])
const inputText = ref('')
const contentRef = ref<HTMLElement>()
const isSending  = ref(false)

// ── 当前状态元数据（图标/标签/颜色） ──────────────────
const stateMeta = computed(() => STATE_META[teacherState.value])

// ── 情绪驱动的光晕颜色 CSS 变量 ─────────────────────
const emotionGlowColor = computed(() => EMOTION_GLOW[teacherEmotion.value])

// ── 需要显示状态徽章的状态列表 ─────────────────────
const BADGE_STATES: TeacherState[] = ['listening', 'thinking', 'encouraging', 'concerned', 'celebrate']
const showBadge = computed(() => BADGE_STATES.includes(teacherState.value))

// ── Mock 回复内容 ────────────────────────────────
const MOCK_RESPONSES: Record<string, string> = {
  '你好': '你好！我是你的AI虚拟教师，我可以回答计算机网络相关问题。不过目前连接有些问题，请稍等片刻再试。',
  'default': '我收到你的问题了！不过目前对话服务连接不稳定，无法实时回答。\n\n请尝试：\n- 🔄 刷新页面重试\n- ✅ 确认后端服务已启动\n- 💬 在主对话区输入问题（功能相同）',
}

function close() { emit('update:modelValue', false) }

async function detectVideo() {
  try {
    const resp = await fetch('/videos/teacher_idle.mp4', { method: 'HEAD' })
    hasVideo.value = resp.ok
  } catch {
    hasVideo.value = false
  }
}

function handleVideoError() { hasVideo.value = false }

// 输入框聚焦 → 倾听状态
function onInputFocus() {
  if (teacherState.value === 'idle') setState('listening')
}
function onInputBlur() {
  if (teacherState.value === 'listening') setState('idle')
}

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || isSending.value) return

  messages.value.push({ role: 'user', content: text, id: `u-${Date.now()}` })
  inputText.value = ''
  isSending.value = true
  setState('thinking')  // ← 进入思考状态

  await nextTick()
  scrollToBottom()

  try {
    const resp = await fetch('/api/v1/chat/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, user_id: 'default' }),
    })

    if (!resp.ok) throw new Error('请求失败')

    const reader = resp.body?.getReader()
    const decoder = new TextDecoder()
    let assistantContent = ''
    const assistantId = `a-${Date.now()}`
    messages.value.push({ role: 'assistant', content: '', id: assistantId })

    if (reader) {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        const chunk = decoder.decode(value, { stream: true })
        const lines = chunk.split('\n')
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const frame = JSON.parse(line.slice(6))
              // 后端 SSE 格式: { event, agent_name, data: { token } }
              if (frame.event === 'token' && frame.data?.token) {
                assistantContent += frame.data.token
                const msg = messages.value.find(m => m.id === assistantId)
                if (msg) msg.content = assistantContent
              }
              // 兿据拒绝（域外问题）
              if (frame.event === 'scope_notice' && frame.data?.message) {
                assistantContent = frame.data.message
                const msg = messages.value.find(m => m.id === assistantId)
                if (msg) msg.content = assistantContent
              }
            } catch { /* skip non-json / heartbeat lines */ }
          }
        }
        await nextTick()
        scrollToBottom()
      }
    }

    if (!assistantContent) {
      const mockReply = MOCK_RESPONSES[text] || MOCK_RESPONSES['default']
      const msg = messages.value.find(m => m.id === assistantId)
      if (msg) msg.content = mockReply
      assistantContent = mockReply
    }

    if (assistantContent && isInitialized.value) {
      speak(assistantContent)  // speak() 内部已处理状态转换
    }
  } catch {
    const mockReply = MOCK_RESPONSES[text] || MOCK_RESPONSES['default']
    messages.value.push({ role: 'assistant', content: mockReply, id: `mock-${Date.now()}` })
    if (isInitialized.value) speak(mockReply)
    else setState('idle')
  } finally {
    isSending.value = false
    await nextTick()
    scrollToBottom()
  }
}

function scrollToBottom() {
  if (contentRef.value) contentRef.value.scrollTop = contentRef.value.scrollHeight
}

function renderMd(content: string): string { return renderMarkdown(content) }

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage() }
}

onMounted(async () => {
  const success = initialize()
  isLoading.value = false
  if (!success) console.warn('[VirtualTeacherPanel] Web Speech API 不可用，降级为静态模式')
  await detectVideo()
})

onUnmounted(() => { stop() })

// 视频切换
watch(isPlaying, (playing) => {
  if (playing && speakingVideoRef.value) {
    speakingVideoRef.value.currentTime = 0
    speakingVideoRef.value.play().catch(() => {})
  } else if (!playing && idleVideoRef.value) {
    idleVideoRef.value.play().catch(() => {})
  }
})

// 外部传入 AI 回复
watch(
  () => props.currentResponse,
  (newText) => {
    if (newText && newText.trim() && isInitialized.value) speak(newText)
    if (newText && messages.value.length === 0) {
      messages.value.push({ role: 'assistant', content: newText, id: `ext-${Date.now()}` })
      nextTick(() => scrollToBottom())
    }
  }
)
</script>

<template>
  <Teleport to="body">
    <Transition name="vt-modal">
      <div v-if="modelValue" class="vt-overlay" @click.self="close">
        <div class="vt-dialog">
          <!-- 标题栏 -->
          <div class="vt-header">
            <div class="vt-header-left">
              <span class="vt-title">虚拟教师</span>
              <span class="vt-agent-tag">Teacher Agent</span>
            </div>
            <div class="vt-header-right">
              <span v-if="!isPlaying && teacherState === 'idle'" class="vt-status ready">
                <span class="status-dot"></span>就绪
              </span>
              <span v-if="isPlaying" class="vt-status speaking">
                <span class="wave-dot"></span>
                <span class="wave-dot"></span>
                <span class="wave-dot"></span>
                讲解中
              </span>
              <button class="vt-close" @click="close" title="关闭">&times;</button>
            </div>
          </div>

          <!-- 主体区域 -->
          <div class="vt-body">
            <!-- 左侧：虚拟人形象 -->
            <div
              class="vt-avatar-area"
              :class="[`state-${teacherState}`, `emotion-${teacherEmotion}`, { speaking: isPlaying }]"
              :style="{ '--emotion-glow': emotionGlowColor }"
            >
              <!-- 说话时的光晕扩散环 -->
              <div v-if="isPlaying" class="speaking-ring ring1"></div>
              <div v-if="isPlaying" class="speaking-ring ring2"></div>
              <div v-if="isPlaying" class="speaking-ring ring3"></div>

              <!-- ★ 教师状态徽章（核心状态机可视化）-->
              <Transition name="badge">
                <div v-if="showBadge" class="teacher-state-badge" :style="{ '--badge-color': stateMeta.color }">
                  <span class="badge-icon">{{ stateMeta.icon }}</span>
                  <span class="badge-label">{{ stateMeta.label }}</span>
                </div>
              </Transition>

              <!-- 思考状态：粒子脉冲动画 -->
              <div v-if="teacherState === 'thinking'" class="thinking-overlay">
                <span v-for="i in 6" :key="i" class="think-dot" :style="{ animationDelay: `${i * 0.15}s` }"></span>
              </div>

              <!-- 庆祝状态：彩色粒子 -->
              <div v-if="teacherState === 'celebrate'" class="celebrate-overlay">
                <span v-for="i in 12" :key="i" class="confetti" :style="{ '--ci': i }"></span>
              </div>

              <!-- 视频模式（双video无缝切换） -->
              <div v-if="hasVideo" class="vt-video-wrapper">
                <video
                  ref="idleVideoRef"
                  class="vt-video"
                  :class="{ active: !isPlaying }"
                  :src="'/videos/teacher_idle.mp4'"
                  autoplay
                  loop
                  muted
                  playsinline
                  @error="handleVideoError"
                />
                <video
                  ref="speakingVideoRef"
                  class="vt-video"
                  :class="{ active: isPlaying }"
                  :src="'/videos/teacher_speaking.mp4'"
                  loop
                  muted
                  playsinline
                  @error="handleVideoError"
                />
                <!-- 说话时的面部光效叠加 -->
                <div v-if="isPlaying" class="vt-face-glow"></div>
              </div>

              <!-- 降级模式（视频不存在时，显示静态图片 + CSS嘴部动画） -->
              <div v-else class="vt-image-fallback">
                <img
                  :src="'/images/virtual_teacher.png'"
                  alt="虚拟教师"
                  class="vt-teacher-img"
                  :class="{ speaking: isPlaying }"
                />
                <!-- CSS嘴部动画叠加层（静态图片模式） -->
                <div v-if="isPlaying" class="mouth-overlay">
                  <div class="mouth-shape">
                    <div class="mouth-inner"></div>
                  </div>
                </div>
              </div>

              <!-- 加载状态叠加 -->
              <div v-if="isLoading" class="vt-status-overlay">
                <div class="vt-spinner"></div>
                <span class="vt-loading-text">正在初始化语音...</span>
              </div>

              <!-- 音频波形条（说话时显示） -->
              <div v-if="isPlaying" class="vt-waveform">
                <span v-for="i in 12" :key="i" class="waveform-bar" :style="{ animationDelay: `${(i-1) * 0.08}s` }"></span>
              </div>

              <!-- 底部状态文字 -->
              <div class="vt-avatar-footer">
                <span
                  class="vt-footer-status"
                  :class="{
                    speaking:    isPlaying,
                    thinking:    teacherState === 'thinking',
                    encouraging: teacherState === 'encouraging',
                    concerned:   teacherState === 'concerned',
                    celebrate:   teacherState === 'celebrate',
                    idle:        teacherState === 'idle',
                  }"
                >
                  <template v-if="isPlaying">
                    <span class="wave-dot"></span><span class="wave-dot"></span><span class="wave-dot"></span>
                    {{ stateMeta.icon }} 正在讲解...
                  </template>
                  <template v-else-if="error">{{ error }}</template>
                  <template v-else>{{ stateMeta.icon }} {{ stateMeta.label }}</template>
                </span>
              </div>
            </div>

            <!-- 右侧：对话内容 -->
            <div class="vt-content-area">
              <div ref="contentRef" class="vt-messages">
                <!-- 欢迎消息 -->
                <div v-if="messages.length === 0" class="vt-welcome">
                  <p class="vt-welcome-title">欢迎使用虚拟教师</p>
                  <p class="vt-welcome-desc">您可以在下方输入问题，虚拟教师将为您讲解计算机网络相关知识。</p>
                </div>

                <!-- 消息列表 -->
                <div
                  v-for="msg in messages"
                  :key="msg.id"
                  class="vt-msg"
                  :class="{ 'vt-msg-user': msg.role === 'user', 'vt-msg-ai': msg.role === 'assistant' }"
                >
                  <div v-if="msg.role === 'user'" class="vt-msg-bubble user-bubble">
                    {{ msg.content }}
                  </div>
                  <div
                    v-else
                    class="vt-msg-bubble ai-bubble markdown-body"
                    v-html="renderMd(msg.content)"
                  ></div>
                </div>

                <!-- 发送中指示 -->
                <div v-if="isSending" class="vt-msg vt-msg-ai">
                  <div class="vt-msg-bubble ai-bubble">
                    <span class="vt-typing">
                      <span></span><span></span><span></span>
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 底部输入栏 -->
          <div class="vt-footer">
            <input
              v-model="inputText"
              type="text"
              class="vt-input"
              placeholder="请输入内容"
              :disabled="isSending"
              @keydown="handleKeydown"
              @focus="onInputFocus"
              @blur="onInputBlur"
            />
            <button
              class="vt-send-btn"
              :disabled="!inputText.trim() || isSending"
              @click="sendMessage"
            >
              发送
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
/* 遮罩层 */
.vt-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(2px);
}

/* 弹窗容器 */
.vt-dialog {
  width: 85vw;
  max-width: 1300px;
  height: 78vh;
  max-height: 820px;
  min-height: 520px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 标题栏 */
.vt-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  background: #1e293b;
  flex-shrink: 0;
}
.vt-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}
.vt-title {
  font-size: 15px;
  font-weight: 600;
  color: #fff;
  letter-spacing: 0.5px;
}
/* Agent 身份标签 */
.vt-agent-tag {
  font-size: 9px;
  font-weight: 700;
  color: #60a5fa;
  background: rgba(96, 165, 250, 0.12);
  border: 1px solid rgba(96, 165, 250, 0.3);
  border-radius: 4px;
  padding: 1px 6px;
  letter-spacing: 0.8px;
  text-transform: uppercase;
}
.vt-header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
.vt-status {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: #a0a0a0;
}
.vt-status.ready .status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #34d399;
  box-shadow: 0 0 4px #34d399;
}
.vt-status.speaking {
  color: #60a5fa;
}
.vt-status.speaking .wave-dot {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: #60a5fa;
  animation: wave 1.2s ease-in-out infinite;
}
.vt-status.speaking .wave-dot:nth-child(2) { animation-delay: 0.2s; }
.vt-status.speaking .wave-dot:nth-child(3) { animation-delay: 0.4s; }
.vt-close {
  background: none;
  border: none;
  color: #999;
  font-size: 22px;
  line-height: 1;
  cursor: pointer;
  padding: 2px 6px;
  border-radius: 4px;
  transition: all 0.15s;
}
.vt-close:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.1);
}

/* 主体区域 */
.vt-body {
  flex: 1;
  display: flex;
  min-height: 0;
}

/* 左侧虚拟人区域 */
.vt-avatar-area {
  width: 38%;
  flex-shrink: 0;
  position: relative;
  background: linear-gradient(160deg, #4a5a6e 0%, #2c3a4e 40%, #1e2a3a 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border-right: 1px solid #1a2535;
  transition: box-shadow 0.4s ease;
}
/* 默认 speaking 光晕 */
.vt-avatar-area.speaking {
  box-shadow: inset 0 0 40px rgba(96, 165, 250, 0.15), 0 0 0 1px rgba(96, 165, 250, 0.3);
}
/* 情绪驱动的光晕色彩（CSS变量注入） */
.vt-avatar-area.emotion-encourage.speaking {
  box-shadow: inset 0 0 60px rgba(251, 191, 36, 0.2), 0 0 0 1px rgba(251, 191, 36, 0.4);
}
.vt-avatar-area.emotion-concerned.speaking {
  box-shadow: inset 0 0 60px rgba(251, 146, 60, 0.2), 0 0 0 1px rgba(251, 146, 60, 0.4);
}
.vt-avatar-area.emotion-emphasize.speaking {
  box-shadow: inset 0 0 60px rgba(255, 255, 255, 0.18), 0 0 0 1px rgba(255, 255, 255, 0.35);
}
.vt-avatar-area.emotion-celebrate.speaking {
  box-shadow: inset 0 0 60px rgba(52, 211, 153, 0.22), 0 0 0 1px rgba(52, 211, 153, 0.4);
}
/* 总是为未说话的情绪状态用 CSS 变量增加微光 */
.vt-avatar-area.state-encouraging {
  box-shadow: inset 0 0 50px rgba(251, 191, 36, 0.1);
}
.vt-avatar-area.state-concerned {
  box-shadow: inset 0 0 50px rgba(251, 146, 60, 0.1);
}
.vt-avatar-area.state-celebrate {
  animation: celebratePulse 0.5s ease-in-out 3;
}
@keyframes celebratePulse {
  0%, 100% { filter: brightness(1); }
  50%       { filter: brightness(1.15); }
}

/* ★ 教师状态徽章 */
.teacher-state-badge {
  position: absolute;
  top: 14px;
  left: 14px;
  z-index: 20;
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 5px 12px;
  border-radius: 20px;
  background: rgba(0, 0, 0, 0.55);
  backdrop-filter: blur(8px);
  border: 1px solid var(--badge-color, #60a5fa);
  box-shadow: 0 0 12px color-mix(in srgb, var(--badge-color, #60a5fa) 30%, transparent);
}
.badge-icon {
  font-size: 14px;
  line-height: 1;
}
.badge-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--badge-color, #60a5fa);
  white-space: nowrap;
  letter-spacing: 0.3px;
}
/* 徽章出入动画 */
.badge-enter-active, .badge-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}
.badge-enter-from {
  opacity: 0;
  transform: translateX(-10px) scale(0.9);
}
.badge-leave-to {
  opacity: 0;
  transform: translateX(-10px) scale(0.9);
}

/* 💡 思考状态：粒子脉冲 */
.thinking-overlay {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 15;
  display: flex;
  gap: 6px;
  pointer-events: none;
}
.think-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #a78bfa;
  animation: thinkPop 1.2s ease-in-out infinite both;
  box-shadow: 0 0 8px #a78bfa;
}
@keyframes thinkPop {
  0%, 100% { transform: scale(0.6); opacity: 0.3; }
  50%       { transform: scale(1.4); opacity: 1; }
}

/* 🎉 庆祝状态：彩色粒子喷射 */
.celebrate-overlay {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 15;
  overflow: hidden;
}
.confetti {
  position: absolute;
  top: -10px;
  left: calc(var(--ci, 1) * 8% - 2%);
  width: 6px;
  height: 6px;
  border-radius: 1px;
  background: hsl(calc(var(--ci, 1) * 30deg), 90%, 65%);
  animation: confettiFall calc(0.8s + var(--ci, 1) * 0.1s) ease-in forwards;
  animation-delay: calc(var(--ci, 1) * 0.06s);
}
@keyframes confettiFall {
  0%   { top: -10px; opacity: 1; transform: rotate(0deg) scale(1); }
  100% { top: 110%; opacity: 0; transform: rotate(calc(var(--ci, 1) * 45deg)) scale(0.5); }
}

/* 说话时的光晕扩散环 */
.speaking-ring {
  position: absolute;
  border-radius: 50%;
  border: 2px solid rgba(96, 165, 250, 0.4);
  pointer-events: none;
  z-index: 10;
  animation: ringExpand 2s ease-out infinite;
}
.speaking-ring.ring1 {
  width: 200px;
  height: 200px;
  animation-delay: 0s;
}
.speaking-ring.ring2 {
  width: 200px;
  height: 200px;
  animation-delay: 0.6s;
  border-color: rgba(96, 165, 250, 0.25);
}
.speaking-ring.ring3 {
  width: 200px;
  height: 200px;
  animation-delay: 1.2s;
  border-color: rgba(96, 165, 250, 0.12);
}
@keyframes ringExpand {
  0%   { transform: scale(0.7); opacity: 0.8; }
  100% { transform: scale(2.2); opacity: 0; }
}

/* 双视频无缝切换容器 */
.vt-video-wrapper {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: flex-start;
  justify-content: center;
}
/* 底部渐变避水印叠加层 */
.vt-video-wrapper::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 72px;
  background: linear-gradient(to top, #1a2535 55%, transparent 100%);
  z-index: 8;
  pointer-events: none;
}
.vt-video {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: contain;         /* 保持全脸不裁剪 */
  object-position: center top; /* 人脸靠上对齐 */
  opacity: 0;
  transition: opacity 0.3s ease;
}
.vt-video.active {
  opacity: 1;
}

/* 降级模式：静态图片 */
.vt-image-fallback {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: flex-start;  /* 人脸靠顶对齐 */
  justify-content: center;
}
.vt-image-fallback::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 72px;
  background: linear-gradient(to top, #1a2535 55%, transparent 100%);
  z-index: 2;
  pointer-events: none;
}
.vt-teacher-img {
  width: 100%;
  height: 100%;
  object-fit: contain;          /* 保持全脸不裁剪 */
  object-position: center top;  /* 人脸靠上对齐 */
  filter: drop-shadow(0 8px 24px rgba(0, 0, 0, 0.3));
  transition: filter 0.3s ease;
}
.vt-teacher-img.speaking {
  filter: drop-shadow(0 8px 24px rgba(0, 0, 0, 0.3)) brightness(1.05);
}
/* CSS 嘴部动画叠加层（图片降级模式） */
.mouth-overlay {
  position: absolute;
  /* 嘴部大约在图片高度65%处 */
  top: 63%;
  left: 50%;
  transform: translateX(-50%);
  z-index: 5;
  pointer-events: none;
}
.mouth-shape {
  width: 42px;
  height: 14px;
  background: rgba(180, 100, 80, 0.7);
  border-radius: 50%;
  overflow: hidden;
  animation: mouthOpen 0.18s ease-in-out infinite alternate;
}
.mouth-inner {
  width: 100%;
  height: 50%;
  background: rgba(80, 20, 10, 0.8);
  border-radius: 50%;
  margin-top: 40%;
}
@keyframes mouthOpen {
  0%   { height: 4px; }
  100% { height: 16px; }
}

/* 视频模式说话时面部光效 */
.vt-face-glow {
  position: absolute;
  top: 15%;
  left: 50%;
  transform: translateX(-50%);
  width: 180px;
  height: 220px;
  background: radial-gradient(ellipse at center, rgba(147, 197, 253, 0.12) 0%, transparent 70%);
  pointer-events: none;
  z-index: 3;
  animation: faceGlowPulse 1.5s ease-in-out infinite;
}
@keyframes faceGlowPulse {
  0%, 100% { opacity: 0.4; }
  50%       { opacity: 1; }
}

/* 音频波形条 */
.vt-waveform {
  position: absolute;
  bottom: 52px;
  left: 0;
  right: 0;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  gap: 3px;
  height: 30px;
  z-index: 4;
  padding: 0 20px;
}
.waveform-bar {
  flex: 1;
  max-width: 8px;
  background: linear-gradient(to top, #3b82f6, #93c5fd);
  border-radius: 2px 2px 0 0;
  min-height: 4px;
  animation: waveformAnim 0.6s ease-in-out infinite alternate;
  opacity: 0.85;
}
@keyframes waveformAnim {
  0%   { height: 4px; }
  100% { height: 28px; }
}
/* 给每个bar一个不同的随机高度感 */
.waveform-bar:nth-child(1)  { animation-duration: 0.55s; }
.waveform-bar:nth-child(2)  { animation-duration: 0.42s; }
.waveform-bar:nth-child(3)  { animation-duration: 0.68s; }
.waveform-bar:nth-child(4)  { animation-duration: 0.38s; }
.waveform-bar:nth-child(5)  { animation-duration: 0.72s; }
.waveform-bar:nth-child(6)  { animation-duration: 0.50s; }
.waveform-bar:nth-child(7)  { animation-duration: 0.45s; }
.waveform-bar:nth-child(8)  { animation-duration: 0.62s; }
.waveform-bar:nth-child(9)  { animation-duration: 0.35s; }
.waveform-bar:nth-child(10) { animation-duration: 0.58s; }
.waveform-bar:nth-child(11) { animation-duration: 0.47s; }
.waveform-bar:nth-child(12) { animation-duration: 0.64s; }

/* 加载状态叠加层 */
.vt-status-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  background: rgba(30, 42, 58, 0.7);
  backdrop-filter: blur(4px);
  z-index: 5;
}

/* 底部状态文字 */
.vt-avatar-footer {
  position: absolute;
  bottom: 16px;
  left: 0;
  right: 0;
  text-align: center;
  z-index: 3;
}
.vt-footer-status {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  padding: 4px 14px;
  border-radius: 20px;
  background: rgba(0, 0, 0, 0.35);
  backdrop-filter: blur(4px);
}
.vt-footer-status.idle {
  color: #94d3a2;
}
.vt-footer-status.speaking {
  color: #93c5fd;
}
.vt-footer-status.thinking {
  color: #fbbf24;
  animation: pulse 1.2s infinite;
}
/* 状态文字颜色进一步扩展 */
.vt-footer-status.encouraging {
  color: #fbbf24;
}
.vt-footer-status.concerned {
  color: #fb923c;
}
.vt-footer-status.celebrate {
  color: #34d399;
  animation: pulse 0.6s ease-in-out 3;
}
.vt-footer-status.error {
  color: #fca5a5;
  font-size: 11px;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.vt-footer-status .wave-dot {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: #93c5fd;
  animation: wave 1.2s ease-in-out infinite;
}
.vt-footer-status .wave-dot:nth-child(2) { animation-delay: 0.2s; }
.vt-footer-status .wave-dot:nth-child(3) { animation-delay: 0.4s; }
.vt-spinner {
  width: 36px;
  height: 36px;
  border: 3px solid rgba(255, 255, 255, 0.15);
  border-top-color: #60a5fa;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
.vt-loading-text {
  color: #94a3b8;
  font-size: 12px;
}

/* 右侧对话内容区 */
.vt-content-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: #fff;
}
.vt-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px 24px;
  min-height: 0;
}
.vt-messages::-webkit-scrollbar {
  width: 5px;
}
.vt-messages::-webkit-scrollbar-track {
  background: transparent;
}
.vt-messages::-webkit-scrollbar-thumb {
  background: #e2e8f0;
  border-radius: 3px;
}
.vt-messages::-webkit-scrollbar-thumb:hover {
  background: #cbd5e1;
}

/* 欢迎消息 */
.vt-welcome {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 8px;
  color: #94a3b8;
}
.vt-welcome-title {
  font-size: 16px;
  font-weight: 600;
  color: #64748b;
}
.vt-welcome-desc {
  font-size: 13px;
  text-align: center;
  max-width: 280px;
  line-height: 1.6;
}

/* 消息气泡 */
.vt-msg {
  margin-bottom: 16px;
  display: flex;
}
.vt-msg-user {
  justify-content: flex-end;
}
.vt-msg-ai {
  justify-content: flex-start;
}
.vt-msg-bubble {
  max-width: 85%;
  padding: 10px 14px;
  border-radius: 10px;
  font-size: 14px;
  line-height: 1.7;
  word-break: break-word;
}
.user-bubble {
  background: #4a7fff;
  color: #fff;
  border-bottom-right-radius: 2px;
}
.ai-bubble {
  background: #f5f7fa;
  color: #1e293b;
  border-bottom-left-radius: 2px;
}

/* Markdown 内容样式 */
.ai-bubble :deep(p) {
  margin: 0 0 8px;
}
.ai-bubble :deep(p:last-child) {
  margin-bottom: 0;
}
.ai-bubble :deep(ul),
.ai-bubble :deep(ol) {
  margin: 6px 0;
  padding-left: 20px;
}
.ai-bubble :deep(li) {
  margin-bottom: 4px;
}
.ai-bubble :deep(strong) {
  font-weight: 600;
  color: #0f172a;
}
.ai-bubble :deep(code) {
  background: #e8eef8;
  padding: 1px 4px;
  border-radius: 3px;
  font-size: 12px;
}
.ai-bubble :deep(pre) {
  margin: 8px 0;
  border-radius: 6px;
  overflow-x: auto;
}

/* 打字动画 */
.vt-typing {
  display: flex;
  gap: 4px;
  padding: 4px 0;
}
.vt-typing span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #94a3b8;
  animation: typing 1.2s ease-in-out infinite;
}
.vt-typing span:nth-child(2) { animation-delay: 0.2s; }
.vt-typing span:nth-child(3) { animation-delay: 0.4s; }

@keyframes typing {
  0%, 100% { opacity: 0.3; transform: scale(0.8); }
  50% { opacity: 1; transform: scale(1.1); }
}

/* 底部输入栏 */
.vt-footer {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 20px;
  border-top: 1px solid #e8eef8;
  background: #fff;
  flex-shrink: 0;
}
.vt-input {
  flex: 1;
  height: 40px;
  padding: 0 16px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 14px;
  color: #1e293b;
  outline: none;
  transition: border-color 0.2s;
}
.vt-input::placeholder {
  color: #94a3b8;
}
.vt-input:focus {
  border-color: #4a7fff;
  box-shadow: 0 0 0 2px rgba(74, 127, 255, 0.1);
}
.vt-input:disabled {
  background: #f8fafc;
  cursor: not-allowed;
}
.vt-send-btn {
  height: 40px;
  padding: 0 24px;
  background: #4a7fff;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.18s;
  white-space: nowrap;
}
.vt-send-btn:hover:not(:disabled) {
  background: #3a6fee;
  box-shadow: 0 2px 8px rgba(74, 127, 255, 0.3);
}
.vt-send-btn:active:not(:disabled) {
  transform: scale(0.97);
}
.vt-send-btn:disabled {
  background: #94a3b8;
  cursor: not-allowed;
  opacity: 0.6;
}

/* 动画 */
@keyframes spin {
  to { transform: rotate(360deg); }
}
@keyframes wave {
  0%, 100% { transform: scale(1); opacity: 0.5; }
  50% { transform: scale(1.5); opacity: 1; }
}
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

/* 弹窗出入动画 */
.vt-modal-enter-active,
.vt-modal-leave-active {
  transition: opacity 0.25s ease;
}
.vt-modal-enter-active .vt-dialog,
.vt-modal-leave-active .vt-dialog {
  transition: transform 0.25s ease, opacity 0.25s ease;
}
.vt-modal-enter-from,
.vt-modal-leave-to {
  opacity: 0;
}
.vt-modal-enter-from .vt-dialog,
.vt-modal-leave-to .vt-dialog {
  transform: scale(0.95) translateY(10px);
  opacity: 0;
}
</style>
