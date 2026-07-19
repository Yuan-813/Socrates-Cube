/**
 * useVirtualTeacher v2.0 - 教师状态机 + 情绪驱动系统
 *
 * 从"会动的头像"升级为"有生命感的AI教师Agent"
 *
 * 架构：
 *   TeacherState (行为状态) → TeacherEmotion (情绪色彩) → 视觉渲染
 *
 * 状态机流转：
 *   IDLE → LISTENING → THINKING → EXPLAINING → ENCOURAGING/CONCERNED/CELEBRATE → IDLE
 */
import { ref, onUnmounted } from 'vue'

// ─────────────────────────────────────────────
// 类型定义
// ─────────────────────────────────────────────

export type TeacherState =
  | 'idle'        // 就绪待命
  | 'listening'   // 专注倾听用户输入
  | 'thinking'    // 等待 AI 响应，认知处理中
  | 'explaining'  // 正在讲解
  | 'encouraging' // 正面反馈，学生回答正确
  | 'concerned'   // 发现认知误区，纠正模式
  | 'celebrate'   // 阶段性掌握，庆祝时刻

export type TeacherEmotion =
  | 'neutral'    // 中性解释
  | 'smile'      // 自然微笑
  | 'encourage'  // 鼓励肯定
  | 'concerned'  // 发现问题
  | 'emphasize'  // 重点强调
  | 'celebrate'  // 庆祝

// ─────────────────────────────────────────────
// 状态元数据
// ─────────────────────────────────────────────

export const STATE_META: Record<TeacherState, { icon: string; label: string; color: string }> = {
  idle:        { icon: '',   label: 'AI 虚拟教师就绪',  color: '#34d399' },
  listening:   { icon: '👂', label: '专注倾听...',      color: '#60a5fa' },
  thinking:    { icon: '💭', label: '思考中...',        color: '#a78bfa' },
  explaining:  { icon: '📖', label: '正在讲解...',      color: '#60a5fa' },
  encouraging: { icon: '✨', label: '太棒了！',         color: '#fbbf24' },
  concerned:   { icon: '🔍', label: '发现误区',         color: '#fb923c' },
  celebrate:   { icon: '🎉', label: '已掌握！',         color: '#34d399' },
}

export const EMOTION_GLOW: Record<TeacherEmotion, string> = {
  neutral:   'rgba(96, 165, 250, 0.15)',
  smile:     'rgba(96, 165, 250, 0.18)',
  encourage: 'rgba(251, 191, 36, 0.22)',
  concerned: 'rgba(251, 146, 60, 0.22)',
  emphasize: 'rgba(255, 255, 255, 0.25)',
  celebrate: 'rgba(52, 211, 153, 0.25)',
}

// ─────────────────────────────────────────────
// 语义情绪检测引擎（客户端启发式）
// ─────────────────────────────────────────────

const EMOTION_KEYWORDS: Partial<Record<TeacherEmotion, string[]>> = {
  encourage: [
    '很好', '正确', '对的', '掌握了', '理解正确', '做得好',
    '优秀', '棒', '完全正确', '理解得很到位', '你说得对', '非常好',
    '回答正确', '思路正确', '说得对', '理解了', '学得很好',
  ],
  concerned: [
    '错误', '误区', '不对', '不是这样', '需要纠正', '容易混淆',
    '注意区分', '误解', '常见错误', '错误理解', '理解偏差',
    '需要澄清', '不完全正确', '有个误区',
  ],
  emphasize: [
    '注意', '关键', '重点', '特别重要', '必须记住',
    '核心概念', '考试', '特别强调', '切记', '务必',
    '一定要', '绝对不能', '这是重中之重', '牢记',
  ],
  celebrate: [
    '恭喜', '完全掌握', '非常棒', '学完了', '全部正确',
    '完美', '满分', '全对了',
  ],
  smile: [
    '当然', '好的', '我来', '让我们', '首先', '接下来',
    '这是一个好问题', '很好的问题',
  ],
}

export function detectEmotion(text: string): TeacherEmotion {
  // 按优先级顺序检测（celebrate > encourage > concerned > emphasize > smile）
  const priority: TeacherEmotion[] = ['celebrate', 'encourage', 'concerned', 'emphasize', 'smile']
  for (const emotion of priority) {
    const keywords = EMOTION_KEYWORDS[emotion]
    if (keywords?.some(kw => text.includes(kw))) {
      return emotion
    }
  }
  return 'neutral'
}

// ─────────────────────────────────────────────
// 主 Composable
// ─────────────────────────────────────────────

export function useVirtualTeacher() {
  const isInitialized  = ref(false)
  const isPlaying      = ref(false)
  const error          = ref<string | null>(null)
  /** 模拟音频振幅 (0-1)，用于口型动画 */
  const amplitude      = ref(0)

  /** 教师行为状态 */
  const teacherState   = ref<TeacherState>('idle')
  /** 当前情绪色彩 */
  const teacherEmotion = ref<TeacherEmotion>('neutral')

  let animationFrameId: number | null = null
  let animationStartTime = 0
  let celebrateTimer: ReturnType<typeof setTimeout> | null = null

  // ── 状态控制 ──────────────────────────────

  function setState(state: TeacherState) {
    teacherState.value = state
  }

  function setEmotion(emotion: TeacherEmotion) {
    teacherEmotion.value = emotion
  }

  /** 进入短暂庆祝状态后自动返回 idle */
  function triggerCelebrate(durationMs = 2500) {
    setState('celebrate')
    setEmotion('celebrate')
    if (celebrateTimer) clearTimeout(celebrateTimer)
    celebrateTimer = setTimeout(() => {
      setState('idle')
      setEmotion('neutral')
    }, durationMs)
  }

  // ── 初始化 ────────────────────────────────

  function initialize(): boolean {
    if (!('speechSynthesis' in window)) {
      error.value = '浏览器不支持语音合成'
      console.warn('[VirtualTeacher] speechSynthesis not available')
      return false
    }

    if (window.speechSynthesis.getVoices().length === 0) {
      window.speechSynthesis.addEventListener('voiceschanged', () => {
        console.log('[VirtualTeacher] voices loaded:', window.speechSynthesis.getVoices().length)
      }, { once: true })
    }

    isInitialized.value = true
    error.value = null
    console.log('[VirtualTeacher] v2.0 初始化成功（状态机模式）')
    return true
  }

  // ── 振幅动画 ──────────────────────────────

  function startAmplitudeSimulation() {
    animationStartTime = performance.now()

    const animate = () => {
      if (!isPlaying.value) {
        amplitude.value = 0
        return
      }
      const elapsed = performance.now() - animationStartTime
      const wave1 = Math.sin(elapsed * 0.008) * 0.3
      const wave2 = Math.sin(elapsed * 0.013) * 0.25
      const wave3 = Math.sin(elapsed * 0.021) * 0.2
      amplitude.value = Math.max(0, Math.min(1, 0.35 + wave1 + wave2 + wave3))
      animationFrameId = requestAnimationFrame(animate)
    }
    animate()
  }

  function stopAmplitudeSimulation() {
    if (animationFrameId !== null) {
      cancelAnimationFrame(animationFrameId)
      animationFrameId = null
    }
    amplitude.value = 0
  }

  // ── 语音选择 ──────────────────────────────

  function selectVoice(): SpeechSynthesisVoice | null {
    const voices = window.speechSynthesis.getVoices()
    if (voices.length === 0) return null

    const zhFemale = voices.find(v =>
      v.lang.startsWith('zh') && v.name.toLowerCase().includes('female')
    )
    if (zhFemale) return zhFemale

    const zhMsVoice = voices.find(v =>
      v.lang.startsWith('zh') && (
        v.name.includes('Xiaoxiao') ||
        v.name.includes('Xiaoyi') ||
        v.name.includes('Yaoyao')
      )
    )
    if (zhMsVoice) return zhMsVoice

    const zhVoice = voices.find(v => v.lang.startsWith('zh'))
    if (zhVoice) return zhVoice

    return null
  }

  // ── 核心语音驱动 ──────────────────────────

  function speak(text: string): Promise<void> {
    return new Promise((resolve) => {
      if (!isInitialized.value) { resolve(); return }
      if (!text || text.trim().length === 0) { resolve(); return }

      // 检测情绪并设置状态
      const emotion = detectEmotion(text)
      setEmotion(emotion)

      // 映射情绪 → 教师状态
      if (emotion === 'encourage') setState('encouraging')
      else if (emotion === 'concerned') setState('concerned')
      else setState('explaining')

      window.speechSynthesis.cancel()
      stopAmplitudeSimulation()

      if (text.length > 200) {
        speakLongText(text).then(resolve)
        return
      }

      const utterance = new SpeechSynthesisUtterance(text)
      utterance.lang    = 'zh-CN'
      utterance.rate    = 1.0
      utterance.pitch   = 1.1
      utterance.volume  = 1.0

      const voice = selectVoice()
      if (voice) utterance.voice = voice

      utterance.onstart = () => {
        isPlaying.value = true
        startAmplitudeSimulation()
      }

      utterance.onend = () => {
        isPlaying.value = false
        stopAmplitudeSimulation()
        // 讲解完毕后的状态转换
        _handleSpeakEnd(emotion)
        resolve()
      }

      utterance.onerror = (e) => {
        isPlaying.value = false
        stopAmplitudeSimulation()
        setState('idle')
        setEmotion('neutral')
        console.error('[VirtualTeacher] Speech error:', e.error)
        resolve()
      }

      window.speechSynthesis.speak(utterance)
    })
  }

  function _handleSpeakEnd(emotion: TeacherEmotion) {
    if (emotion === 'encourage' || emotion === 'celebrate') {
      triggerCelebrate(2000)
    } else if (emotion === 'concerned') {
      // 保持 concerned 状态短暂停留，让用户看到
      setTimeout(() => {
        setState('idle')
        setEmotion('neutral')
      }, 1500)
    } else {
      setState('idle')
      setEmotion('neutral')
    }
  }

  // ── 长文本分段朗读 ────────────────────────

  async function speakLongText(text: string): Promise<void> {
    const segments = text
      .split(/(?<=[。？！\n.?!])/g)
      .filter(s => s.trim().length > 0)

    const merged: string[] = []
    let current = ''
    for (const seg of segments) {
      if ((current + seg).length < 150) {
        current += seg
      } else {
        if (current) merged.push(current)
        current = seg
      }
    }
    if (current) merged.push(current)

    for (const segment of merged) {
      if (!isPlaying.value && merged.indexOf(segment) > 0) break

      await new Promise<void>((resolve) => {
        const utterance = new SpeechSynthesisUtterance(segment)
        utterance.lang   = 'zh-CN'
        utterance.rate   = 1.0
        utterance.pitch  = 1.1
        utterance.volume = 1.0

        const voice = selectVoice()
        if (voice) utterance.voice = voice

        utterance.onstart = () => {
          if (!isPlaying.value) {
            isPlaying.value = true
            startAmplitudeSimulation()
          }
        }
        utterance.onend   = () => resolve()
        utterance.onerror = () => resolve()

        window.speechSynthesis.speak(utterance)
      })
    }

    isPlaying.value = false
    stopAmplitudeSimulation()
    _handleSpeakEnd(teacherEmotion.value)
  }

  // ── 停止 ──────────────────────────────────

  function stop() {
    window.speechSynthesis.cancel()
    isPlaying.value = false
    stopAmplitudeSimulation()
    setState('idle')
    setEmotion('neutral')
    if (celebrateTimer) { clearTimeout(celebrateTimer); celebrateTimer = null }
  }

  onUnmounted(() => { stop() })

  return {
    isInitialized,
    isPlaying,
    error,
    amplitude,
    teacherState,
    teacherEmotion,
    initialize,
    speak,
    stop,
    setState,
    setEmotion,
    detectEmotion,
  }
}
