<script setup lang="ts">
import { ref, computed } from 'vue'
import { SIM_DIALOGUES } from '@/data/simDialogues'
import { startChatStream } from '@/api/chat'
import { useUserStore } from '@/stores/userStore'
import DiagnosisFlowStepper from '@/components/DiagnosisFlowStepper.vue'
import ChallengerQuizCard from '@/components/ChallengerQuizCard.vue'

defineProps<{ visible: boolean }>()
const emit = defineEmits<{ (e: 'close'): void }>()

const userStore = useUserStore()

const screen   = ref<'input' | 'result' | 'simulation' | 'challenger'>('input')
const inputVal = ref('')
const sel      = ref('TLS 握手流程')
const loading  = ref(false)
const focused  = ref(false)
const maxLen   = 300
const simStep  = ref(1)
const simTotal = 22
let   abort: AbortController | null = null

const PROTOCOLS = [
  { label: 'TCP/IP 基础',  dot: '#00C8FF' },
  { label: 'HTTP/3 协议',  dot: '#00AAFF' },
  { label: 'TLS 握手流程', dot: '#1A5CFF' },
  { label: 'QUIC 传输',    dot: '#5566FF' },
  { label: 'DNS 递归解析', dot: '#00C8FF' },
  { label: 'IPv6 迁移',    dot: '#0088CC' },
]

const MASTERY_MAP: Record<string, Array<{label: string; pct: number; color: string}>> = {
  'TLS 握手流程': [
    { label: '序列号同步', pct: 35, color: '#ef4444' },
    { label: 'MSS 协商',   pct: 55, color: '#f97316' },
    { label: '半连接队列', pct: 40, color: '#ef4444' },
    { label: '三次握手流程', pct: 82, color: '#10b981' },
    { label: 'ACK 确认机制', pct: 78, color: '#00C8FF' },
  ],
  'TCP/IP 基础': [
    { label: 'IP 寻址',   pct: 65, color: '#f97316' },
    { label: 'ARP 协议',  pct: 48, color: '#ef4444' },
    { label: '子网划分', pct: 72, color: '#10b981' },
    { label: '路由选择', pct: 55, color: '#f97316' },
    { label: 'ICMP 机制', pct: 80, color: '#10b981' },
  ],
  'HTTP/3 协议': [
    { label: 'QUIC 握手', pct: 45, color: '#ef4444' },
    { label: '流量控制', pct: 60, color: '#f97316' },
    { label: '头部压缩', pct: 38, color: '#ef4444' },
    { label: '多路复用', pct: 85, color: '#10b981' },
    { label: '0-RTT',     pct: 30, color: '#ef4444' },
  ],
  'QUIC 传输': [
    { label: '连接迁移', pct: 28, color: '#ef4444' },
    { label: 'UDP 封装', pct: 65, color: '#f97316' },
    { label: '加密握手', pct: 52, color: '#f97316' },
    { label: '拥塑控制', pct: 75, color: '#10b981' },
    { label: '流式传输', pct: 88, color: '#10b981' },
  ],
  'DNS 递归解析': [
    { label: '递归查询', pct: 72, color: '#10b981' },
    { label: '权威 DNS', pct: 48, color: '#ef4444' },
    { label: 'TTL 缓存', pct: 65, color: '#f97316' },
    { label: 'DNSSEC',  pct: 35, color: '#ef4444' },
    { label: '反向解析', pct: 82, color: '#10b981' },
  ],
  'IPv6 迁移': [
    { label: '地址格式', pct: 68, color: '#f97316' },
    { label: '无状态配置', pct: 42, color: '#ef4444' },
    { label: '双栈机制', pct: 75, color: '#10b981' },
    { label: 'NDP 协议', pct: 38, color: '#ef4444' },
    { label: '隊道技术', pct: 55, color: '#f97316' },
  ],
}

const topicMastery = computed(() => MASTERY_MAP[sel.value] ?? MASTERY_MAP['TLS 握手流程'])
const weakCount    = computed(() => topicMastery.value.filter(m => m.pct < 60).length)
const patternCount = computed(() => Math.max(1, Math.floor(weakCount.value / 2)))

const TCP_IP_LAYERS = [
  { name: 'Application', rfc: 'RFC 9110', color: '#818cf8' },
  { name: 'Transport',   rfc: 'RFC 9293', color: '#38bdf8' },
  { name: 'Network',     rfc: 'RFC 8200', color: '#34d399' },
  { name: 'Link',        rfc: 'IEEE 802', color: '#a78bfa' },
]

const currentDialogue = computed(() => {
  const steps = SIM_DIALOGUES[sel.value] ?? SIM_DIALOGUES['TLS 握手流程']
  const idx = Math.min(simStep.value - 1, steps.length - 1)
  return steps[Math.max(0, idx)]
})

const simBarPoints = computed(() => {
  const pts = [12, 28, 18, 35, 22, 42, 30, 55, 38, 48]
  const w = 120, h = 40
  return pts.map((v, i) => `${Math.round(i * w / (pts.length - 1))},${Math.round(h - v * h / 60)}`).join(' ')
})

function diagnose(topic: string) {
  if (loading.value) return
  loading.value = true
  const msg = inputVal.value.trim()
    ? inputVal.value.trim()
    : `请针对「${topic}」进行深度认知漏洞诊断，分析该协议的常见误解模式`

  abort = startChatStream(
    { message: msg, user_id: userStore.userId ?? 'student-001' },
    () => {},
    () => { loading.value = false; screen.value = 'result' },
    () => { loading.value = false },
  )
}

function handleClose() {
  abort?.abort()
  loading.value = false
  emit('close')
}

function reset() {
  screen.value = 'input'
  inputVal.value = ''
  sel.value = 'TLS 握手流程'
  simStep.value = 1
}

const TAB_LIST = [
  { id: 'input',      label: 'AI诊断输入',   num: 1 },
  { id: 'result',     label: '诊断结果',     num: 2 },
  { id: 'simulation', label: '沉浸仿真场景', num: 3 },
  { id: 'challenger', label: '误解检验',     num: 4 },
]
</script>

<template>
  <!-- 遮罩层 -->
  <Teleport to="body">
    <Transition name="zysy-fade">
      <div v-if="visible" class="zysy-overlay" @click.self="handleClose">
        <div class="zysy-modal" :class="{ 'is-result': screen === 'result' }">

          <!-- 电路折角装饰 -->
          <svg class="zysy-corner tl" width="28" height="28" viewBox="0 0 28 28">
            <path d="M2,26 L2,7 Q2,2 7,2 L26,2" stroke="#00C8FF" stroke-width="1.8" fill="none" opacity="0.75"/>
            <circle cx="6" cy="6" r="2.5" fill="#00C8FF" opacity="0.9"/>
          </svg>
          <svg class="zysy-corner tr" width="28" height="28" viewBox="0 0 28 28">
            <path d="M2,26 L2,7 Q2,2 7,2 L26,2" stroke="#00C8FF" stroke-width="1.8" fill="none" opacity="0.75"/>
            <circle cx="6" cy="6" r="2.5" fill="#00C8FF" opacity="0.9"/>
          </svg>
          <svg class="zysy-corner bl" width="28" height="28" viewBox="0 0 28 28">
            <path d="M2,26 L2,7 Q2,2 7,2 L26,2" stroke="#00C8FF" stroke-width="1.8" fill="none" opacity="0.75"/>
            <circle cx="6" cy="6" r="2.5" fill="#00C8FF" opacity="0.9"/>
          </svg>
          <svg class="zysy-corner br" width="28" height="28" viewBox="0 0 28 28">
            <path d="M2,26 L2,7 Q2,2 7,2 L26,2" stroke="#00C8FF" stroke-width="1.8" fill="none" opacity="0.75"/>
            <circle cx="6" cy="6" r="2.5" fill="#00C8FF" opacity="0.9"/>
          </svg>

          <!-- 顶部光线描线 -->
          <div class="zysy-top-line" />

          <!-- ── Header ── -->
          <div class="zysy-header">
            <div class="zysy-logo-row">
              <div class="zysy-logo">
                <svg width="28" height="28" viewBox="0 0 28 28">
                  <circle cx="14" cy="14" r="3.5" fill="#00C8FF"/>
                  <circle cx="4"  cy="7"  r="2.2" fill="#00C8FF" opacity="0.75"/>
                  <circle cx="24" cy="7"  r="2.2" fill="#00C8FF" opacity="0.75"/>
                  <circle cx="4"  cy="21" r="2.2" fill="#00C8FF" opacity="0.75"/>
                  <circle cx="24" cy="21" r="2.2" fill="#00C8FF" opacity="0.75"/>
                  <line x1="14" y1="14" x2="4"  y2="7"  stroke="#00C8FF" stroke-width="1.2" opacity="0.55"/>
                  <line x1="14" y1="14" x2="24" y2="7"  stroke="#00C8FF" stroke-width="1.2" opacity="0.55"/>
                  <line x1="14" y1="14" x2="4"  y2="21" stroke="#00C8FF" stroke-width="1.2" opacity="0.55"/>
                  <line x1="14" y1="14" x2="24" y2="21" stroke="#00C8FF" stroke-width="1.2" opacity="0.55"/>
                </svg>
              </div>
              <div>
                <div class="zysy-title">智问溯源</div>
                <div class="zysy-subtitle">AI 深度诊断 · 精析协议真知</div>
              </div>
            </div>
            <div class="zysy-header-right">
              <span v-if="screen === 'input'" class="zysy-badge">INPUT MODE</span>
              <span v-else-if="screen === 'result'" class="zysy-badge result">RESULT</span>
              <span v-else class="zysy-badge challenger-badge">CHALLENGER</span>
              <button class="zysy-close" @click="handleClose">×</button>
            </div>
          </div>

          <!-- ══ Tab 导航条 ══ -->
          <div class="zysy-tabs">
            <button
              v-for="tab in TAB_LIST"
              :key="tab.id"
              class="zysy-tab"
              :class="{ active: screen === tab.id }"
              @click="screen = tab.id as any"
            >
              <span class="tab-num">{{ tab.num }}.</span>
              {{ tab.label }}
            </button>
          </div>

          <!-- ══════ Screen 1：诊断输入 ══════ -->
          <Transition name="zysy-slide">
            <div v-if="screen === 'input'" class="zysy-body" key="input">

              <!-- 文本输入区 -->
              <div class="zysy-input-wrap" :class="{ focused }">
                <div class="zysy-input-label">INPUT QUERY</div>
                <textarea
                  v-model="inputVal"
                  :maxlength="maxLen"
                  rows="4"
                  placeholder="例如：分析 TCP 三次握手中序列号的同步机制与半连接队列溢出攻击…"
                  class="zysy-textarea"
                  @focus="focused = true"
                  @blur="focused = false"
                />
                <div class="zysy-input-foot">
                  <span class="zysy-status-dot">{{ focused ? '◈ READY' : '○ IDLE' }}</span>
                  <span class="zysy-char-count">{{ inputVal.length }}/{{ maxLen }}</span>
                </div>
              </div>

              <!-- 自由诊断按钮 -->
              <div class="zysy-btn-center">
                <button
                  class="zysy-btn-ghost"
                  :class="{ loading }"
                  :disabled="loading"
                  @click="diagnose(sel)"
                >
                  <svg v-if="loading" class="spin-icon" width="14" height="14" viewBox="0 0 14 14">
                    <circle cx="7" cy="7" r="5.5" fill="none" stroke="#00C8FF" stroke-width="1.5" stroke-dasharray="10 6"/>
                  </svg>
                  <svg v-else width="14" height="14" viewBox="0 0 14 14">
                    <path d="M7,0.5 L8.8,5.2 L13.5,7 L8.8,8.8 L7,13.5 L5.2,8.8 L0.5,7 L5.2,5.2 Z" fill="#00C8FF"/>
                  </svg>
                  {{ loading ? '诊断中…' : '开始诊断' }}
                </button>
              </div>

              <!-- 分隔线 -->
              <div class="zysy-divider"><span>或</span></div>

              <!-- 协议课题选择卡 -->
              <div class="zysy-protocol-card">
                <div class="zysy-pc-top-line" />
                <div class="zysy-pc-icon">
                  <svg width="26" height="26" viewBox="0 0 26 26">
                    <rect x="2" y="2"  width="22" height="5" rx="1.5" fill="#00C8FF" opacity="0.85"/>
                    <rect x="2" y="9"  width="22" height="5" rx="1.5" fill="#1A5CFF" opacity="0.7"/>
                    <rect x="2" y="16" width="22" height="5" rx="1.5" fill="#00C8FF" opacity="0.5"/>
                    <circle cx="21" cy="4.5"  r="1.5" fill="white" opacity="0.8"/>
                    <circle cx="21" cy="11.5" r="1.5" fill="white" opacity="0.8"/>
                    <circle cx="21" cy="18.5" r="1.5" fill="white" opacity="0.8"/>
                  </svg>
                </div>
                <div class="zysy-pc-title">基于协议诊断</div>
                <div class="zysy-pc-desc">选择经典协议课题，由 AI 引擎完成认知漏洞精准定位</div>

                <div class="zysy-tags">
                  <button
                    v-for="p in PROTOCOLS"
                    :key="p.label"
                    class="zysy-tag"
                    :class="{ active: sel === p.label }"
                    @click="sel = p.label"
                  >
                    <span
                      class="zysy-tag-dot"
                      :style="{ background: sel === p.label ? p.dot : '#2E4560', boxShadow: sel === p.label ? `0 0 6px ${p.dot}` : 'none' }"
                    />
                    {{ p.label }}
                  </button>
                </div>

                <div class="zysy-btn-center">
                  <button
                    class="zysy-btn-primary"
                    :class="{ loading }"
                    :disabled="loading"
                    @click="diagnose(sel)"
                  >
                    <svg v-if="loading" class="spin-icon" width="15" height="15" viewBox="0 0 15 15">
                      <circle cx="7.5" cy="7.5" r="6" fill="none" stroke="white" stroke-width="1.5" stroke-dasharray="12 6"/>
                    </svg>
                    <svg v-else width="15" height="15" viewBox="0 0 15 15">
                      <path d="M7.5,0.5 L9.5,5.5 L14.5,7.5 L9.5,9.5 L7.5,14.5 L5.5,9.5 L0.5,7.5 L5.5,5.5 Z" fill="white"/>
                    </svg>
                    {{ loading ? `诊断中：${sel}…` : '开始诊断' }}
                  </button>
                </div>
              </div>

            </div><!-- /input screen -->
          </Transition>

          <!-- ══════ Screen 2：诊断结果 ══════ -->
          <Transition name="zysy-slide">
            <div v-if="screen === 'result'" class="zysy-body result-body" key="result">

              <!-- 状态行 -->
              <div class="zysy-status-row">
                <div class="zysy-done-label">
                  <svg width="20" height="20" viewBox="0 0 20 20">
                    <circle cx="10" cy="10" r="9" fill="rgba(46,204,113,0.1)" stroke="#2ECC71" stroke-width="1.5"/>
                    <path d="M6,10 L9,13.5 L14,7" stroke="#2ECC71" stroke-width="2.2" fill="none" stroke-linecap="round"/>
                  </svg>
                  <span>「{{ sel }}」诊断完成</span>
                </div>
                <span class="zysy-ai-badge">
                  <svg width="12" height="12" viewBox="0 0 12 12">
                    <circle cx="6" cy="6" r="4.5" fill="none" stroke="#00C8FF" stroke-width="1.3"/>
                    <path d="M3,7 L5,4.5 L7,8 L9,5.5" stroke="#00C8FF" stroke-width="1.3" fill="none" stroke-linecap="round"/>
                  </svg>
                  AI 诊断
                </span>
              </div>

              <!-- 诊断流程步进 -->
              <div class="zysy-stepper-wrap">
                <DiagnosisFlowStepper />
              </div>

              <!-- 核心可视化：TCP 三次握手 SVG 动画 -->
              <div class="zysy-handshake-viz">
                <svg width="100%" height="290" viewBox="0 0 480 290" style="display:block">
                  <defs>
                    <marker id="ah-c" markerWidth="7" markerHeight="5" refX="6" refY="2.5" orient="auto">
                      <polygon points="0,0 7,2.5 0,5" fill="#00C8FF"/>
                    </marker>
                    <marker id="ah-b" markerWidth="7" markerHeight="5" refX="6" refY="2.5" orient="auto">
                      <polygon points="0,0 7,2.5 0,5" fill="#5599FF"/>
                    </marker>
                    <marker id="ah-g" markerWidth="7" markerHeight="5" refX="6" refY="2.5" orient="auto">
                      <polygon points="0,0 7,2.5 0,5" fill="#2ECC71"/>
                    </marker>
                    <pattern id="hsDotGrid" width="24" height="24" patternUnits="userSpaceOnUse">
                      <circle cx="12" cy="12" r="0.7" fill="rgba(0,200,255,0.07)"/>
                    </pattern>
                  </defs>
                  <rect width="480" height="290" fill="url(#hsDotGrid)"/>
                  <!-- CLIENT -->
                  <rect x="58"  y="10" width="64" height="22" rx="5" fill="rgba(0,200,255,0.08)"  stroke="rgba(0,200,255,0.35)" stroke-width="1"/>
                  <text x="90"  y="21" text-anchor="middle" dominant-baseline="middle" font-size="9" fill="#00C8FF" font-family="monospace" font-weight="700">CLIENT</text>
                  <!-- SERVER -->
                  <rect x="358" y="10" width="64" height="22" rx="5" fill="rgba(26,92,255,0.08)"  stroke="rgba(26,92,255,0.4)"  stroke-width="1"/>
                  <text x="390" y="21" text-anchor="middle" dominant-baseline="middle" font-size="9" fill="#7AABFF" font-family="monospace" font-weight="700">SERVER</text>
                  <!-- 时序纵线 -->
                  <line x1="90"  y1="32" x2="90"  y2="270" stroke="#00C8FF" stroke-width="1.5" stroke-dasharray="4,3" opacity="0.4"/>
                  <line x1="390" y1="32" x2="390" y2="270" stroke="#5599FF" stroke-width="1.5" stroke-dasharray="4,3" opacity="0.4"/>
                  <!-- SYN → -->
                  <line x1="94" y1="80" x2="382" y2="80" stroke="#00C8FF" stroke-width="1.6" marker-end="url(#ah-c)" opacity="0.85"/>
                  <rect x="202" y="60" width="76" height="18" rx="4" fill="rgba(0,200,255,0.1)" stroke="rgba(0,200,255,0.4)" stroke-width="0.8"/>
                  <text x="240" y="69"  text-anchor="middle" dominant-baseline="middle" font-size="8.5" fill="#00C8FF" font-family="monospace" font-weight="700">SYN</text>
                  <text x="240" y="92"  text-anchor="middle" dominant-baseline="middle" font-size="7.5" fill="#5E88B0" font-family="monospace">seq = ISN_c</text>
                  <circle cx="90"  cy="80" r="5" fill="#050D18" stroke="#00C8FF" stroke-width="1.5"/>
                  <circle cx="386" cy="80" r="5" fill="#050D18" stroke="#00C8FF" stroke-width="1.5"/>
                  <circle r="3.5" fill="#00C8FF" opacity="0.9"><animateMotion dur="1.6s" repeatCount="indefinite" path="M90,80 L386,80"/></circle>
                  <!-- ← SYN-ACK -->
                  <line x1="386" y1="155" x2="98" y2="155" stroke="#5599FF" stroke-width="1.6" marker-end="url(#ah-b)" opacity="0.85"/>
                  <rect x="202" y="135" width="76" height="18" rx="4" fill="rgba(85,153,255,0.1)" stroke="rgba(85,153,255,0.4)" stroke-width="0.8"/>
                  <text x="240" y="144" text-anchor="middle" dominant-baseline="middle" font-size="8.5" fill="#5599FF" font-family="monospace" font-weight="700">SYN-ACK</text>
                  <text x="240" y="167" text-anchor="middle" dominant-baseline="middle" font-size="7.5" fill="#5E88B0" font-family="monospace">seq=ISN_s  ack=ISN_c+1</text>
                  <circle cx="390" cy="155" r="5" fill="#050D18" stroke="#5599FF" stroke-width="1.5"/>
                  <circle cx="94"  cy="155" r="5" fill="#050D18" stroke="#5599FF" stroke-width="1.5"/>
                  <circle r="3.5" fill="#5599FF" opacity="0.9"><animateMotion dur="1.2s" repeatCount="indefinite" path="M390,155 L94,155"/></circle>
                  <!-- ACK → -->
                  <line x1="94" y1="220" x2="382" y2="220" stroke="#2ECC71" stroke-width="1.6" marker-end="url(#ah-g)" opacity="0.85"/>
                  <rect x="202" y="200" width="76" height="18" rx="4" fill="rgba(46,204,113,0.1)" stroke="rgba(46,204,113,0.4)" stroke-width="0.8"/>
                  <text x="240" y="209" text-anchor="middle" dominant-baseline="middle" font-size="8.5" fill="#2ECC71" font-family="monospace" font-weight="700">ACK</text>
                  <text x="240" y="232" text-anchor="middle" dominant-baseline="middle" font-size="7.5" fill="#5E88B0" font-family="monospace">ack = ISN_s+1</text>
                  <circle cx="90"  cy="220" r="5" fill="#050D18" stroke="#2ECC71" stroke-width="1.5"/>
                  <circle cx="386" cy="220" r="5" fill="#050D18" stroke="#2ECC71" stroke-width="1.5"/>
                  <circle r="3.5" fill="#2ECC71" opacity="0.9"><animateMotion dur="1.8s" repeatCount="indefinite" path="M90,220 L386,220"/></circle>
                  <!-- ESTABLISHED -->
                  <rect x="78" y="238" width="140" height="20" rx="4" fill="rgba(46,204,113,0.08)" stroke="rgba(46,204,113,0.4)" stroke-width="0.8"/>
                  <text x="148" y="248" text-anchor="middle" dominant-baseline="middle" font-size="8.5" fill="#2ECC71" font-family="monospace" font-weight="600">✓ 连接建立 · ESTABLISHED</text>
                  <!-- RFC tag -->
                  <rect x="370" y="5" width="102" height="18" rx="4" fill="rgba(0,200,255,0.06)" stroke="rgba(0,200,255,0.25)" stroke-width="0.8"/>
                  <text x="421" y="14" text-anchor="middle" dominant-baseline="middle" font-size="7.5" fill="#00C8FF" font-family="monospace">RFC 9293 § 3.5</text>
                </svg>
              </div>

              <!-- 知识点掌握度分析 -->
              <div class="zysy-mastery-panel">
                <div class="mastery-hd">
                  <span class="mastery-title">◈ 知识点掌握度分析</span>
                  <span class="mastery-weak">{{ weakCount }} 项薄弱 · 需强化</span>
                </div>
                <div v-for="item in topicMastery" :key="item.label" class="mastery-row">
                  <span class="mastery-name" :style="{ color: item.pct < 60 ? '#FF8070' : '#5E88B0' }">{{ item.label }}</span>
                  <div class="mastery-track">
                    <div class="mastery-fill" :style="{
                      width: item.pct + '%',
                      background: item.pct < 60
                        ? 'linear-gradient(90deg,#AA2020,' + item.color + ')'
                        : 'linear-gradient(90deg,#1A5CFF,' + item.color + ')'
                    }"></div>
                  </div>
                  <span class="mastery-pct" :style="{ color: item.color }">{{ item.pct }}%</span>
                </div>
              </div>

              <!-- AI 诊断文本块 -->
              <div class="zysy-ai-text-block">
                <div class="ai-text-title">【AI诊断】{{ sel }}·深度协议解析</div>
                <p class="ai-text-body">
                  AI 认知引擎根据「{{ sel }}」课题自动分析，覆盖序列号同步、握手状态机、拥塞控制初始化等知识点，识别出
                  <span class="ai-text-highlight">{{ weakCount }} 项认知薄弱区</span> 与
                  <span class="ai-text-highlight">{{ patternCount }} 项误解模式</span>。
                </p>
                <div class="ai-text-rfc">推荐复习 RFC 793 §3.4 · RFC 9293 §3.5 · 预计强化时长 {{ weakCount * 8 + 9 }} min</div>
                <div class="ai-text-date">诊断日期：{{ new Date().toLocaleDateString('zh-CN') }}</div>
              </div>

              <!-- 底部操作行 -->
              <div class="zysy-result-foot">
                <button class="zysy-btn-ghost small" @click="reset">← 重新诊断</button>
                <button class="zysy-btn-ghost small" @click="screen = 'simulation'">🔬 展开仿真场景</button>
                <button class="zysy-btn-ghost small" @click="screen = 'challenger'">⚡ 进入误解检验</button>
                <button class="zysy-btn-ghost small close-btn" @click="handleClose">关闭</button>
              </div>

            </div><!-- /result screen -->
          </Transition>

          <!-- ══════ Screen 3：沉浸仿真场景 ══════ -->
          <Transition name="zysy-slide">
            <div v-if="screen === 'simulation'" class="zysy-body sim-body" key="simulation">

              <!-- 沉浸场景主体 -->
              <div class="sim-stage">
                <!-- 星空背景 -->
                <svg style="position:absolute;inset:0;width:100%;height:100%;pointer-events:none">
                  <circle v-for="i in 40" :key="i"
                    :cx="`${(i * 41 + 17) % 100}%`"
                    :cy="`${(i * 61 + 11) % 80}%`"
                    :r="i % 4 === 0 ? 1.8 : 0.7"
                    fill="white"
                    :opacity="0.06 + (i % 6) * 0.04"
                  />
                </svg>
                <!-- 透视网格 -->
                <svg style="position:absolute;bottom:0;left:0;width:100%;height:55%;pointer-events:none">
                  <defs>
                    <linearGradient id="gf2" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stop-color="rgba(0,200,255,0.18)"/>
                      <stop offset="100%" stop-color="rgba(0,200,255,0.01)"/>
                    </linearGradient>
                  </defs>
                  <line v-for="i in 11" :key="'v'+i" :x1="`${50+(i-6)*7}%`" y1="0%" :x2="`${50+(i-6)*75}%`" y2="100%" stroke="url(#gf2)" stroke-width="0.7"/>
                  <line v-for="(yv, hi) in [0.1,0.25,0.45,0.65,0.85]" :key="'h'+hi" x1="0%" :y1="`${yv*100}%`" x2="100%" :y2="`${yv*100}%`" stroke="rgba(0,200,255,0.07)" stroke-width="0.5"/>
                </svg>
                <!-- 顶部光带 -->
                <div class="sim-top-glow-bar"></div>

                <!-- NET MONITOR -->
                <div class="sim-abs-panel sim-panel-left">
                  <div class="sim-panel-lbl">▶ NET MONITOR</div>
                  <svg width="108" height="44" viewBox="0 0 108 44">
                    <polyline points="0,38 12,32 22,18 34,27 48,12 62,22 76,9 92,18 108,13" fill="none" stroke="#00C8FF" stroke-width="1.4"/>
                    <polyline points="0,38 12,32 22,18 34,27 48,12 62,22 76,9 92,18 108,13 108,44 0,44" fill="rgba(0,200,255,0.04)" stroke-width="0"/>
                  </svg>
                  <div class="sim-ptag-row">
                    <span class="sim-ptag active">TCP</span>
                    <span class="sim-ptag">UDP</span>
                    <span class="sim-ptag">ICMP</span>
                  </div>
                </div>

                <!-- TCP/IP STACK -->
                <div class="sim-abs-panel sim-panel-right">
                  <div class="sim-panel-lbl blue">▶ TCP/IP STACK</div>
                  <div v-for="layer in TCP_IP_LAYERS" :key="layer.name" class="sim-stack-item">
                    <span :style="{ color: layer.color, fontWeight: 600, fontSize: '8px', fontFamily: 'monospace' }">{{ layer.name }}</span>
                    <span style="opacity:0.55;font-size:7px;font-family:monospace;color:#5E88B0">{{ layer.rfc }}</span>
                  </div>
                </div>

                <!-- 中心题目标题 -->
                <div class="sim-center-lbl">◈ 考察 {{ sel }} 深度理解</div>

                <!-- 数据包动画 -->
                <div class="sim-pkt-wrap">
                  <svg width="220" height="36">
                    <rect x="30" y="6" width="160" height="24" rx="6" fill="rgba(0,200,255,0.07)" stroke="rgba(0,200,255,0.3)" stroke-width="1"/>
                    <text x="110" y="18" text-anchor="middle" dominant-baseline="middle" font-size="8.5" fill="#00C8FF" font-family="monospace" font-weight="600">TCP SYN  |  seq = 0x4A9F  |  win = 65535</text>
                    <circle r="3.5" fill="#00C8FF" opacity="0.85">
                      <animateMotion dur="2.2s" repeatCount="indefinite" path="M10,18 L210,18"/>
                    </circle>
                  </svg>
                </div>

                <!-- 苏格拉底虚拟形象 -->
                <div class="sim-avatar-wrap">
                  <div class="sim-avatar-glow"></div>
                  <svg width="140" height="248" viewBox="0 0 140 248" style="position:relative;z-index:2">
                    <ellipse cx="70" cy="242" rx="52" ry="9" fill="rgba(0,200,255,0.12)"/>
                    <rect x="42" y="174" width="21" height="58" rx="7" fill="#07101E" stroke="#1A5CFF" stroke-width="1.2"/>
                    <rect x="77" y="174" width="21" height="58" rx="7" fill="#07101E" stroke="#1A5CFF" stroke-width="1.2"/>
                    <path d="M38,220 Q36,236 46,238 L63,238 Q70,236 68,228 L64,220 Z" fill="#050D18" stroke="#1A5CFF" stroke-width="1"/>
                    <path d="M72,220 Q70,236 80,238 L97,238 Q104,236 102,228 L98,220 Z" fill="#050D18" stroke="#1A5CFF" stroke-width="1"/>
                    <path d="M16,174 L18,106 Q18,98 27,98 L113,98 Q122,98 122,106 L124,174 Z" fill="#08121E" stroke="#1A5CFF" stroke-width="1.3"/>
                    <path d="M18,108 L47,130 L70,122 L93,130 L122,108" fill="#0C1D38" stroke="rgba(0,200,255,0.38)" stroke-width="1.2"/>
                    <circle cx="70" cy="142" r="13" fill="rgba(0,200,255,0.04)" stroke="#00C8FF" stroke-width="1"/>
                    <circle cx="70" cy="142" r="8" fill="rgba(0,200,255,0.08)" stroke="#00C8FF" stroke-width="0.7"/>
                    <circle cx="70" cy="142" r="3.5" fill="#00C8FF" opacity="0.7">
                      <animate attributeName="opacity" values="0.7;1;0.7" dur="2s" repeatCount="indefinite"/>
                      <animate attributeName="r" values="3.5;5;3.5" dur="2s" repeatCount="indefinite"/>
                    </circle>
                    <path d="M18,110 L-2,162 Q-4,172 5,174 L16,174 Q26,172 26,162 L30,116 Z" fill="#07101E" stroke="#1A5CFF" stroke-width="1.1"/>
                    <path d="M122,110 L142,162 Q144,172 135,174 L124,174 Q114,172 114,162 L110,116 Z" fill="#07101E" stroke="#1A5CFF" stroke-width="1.1"/>
                    <ellipse cx="4"   cy="175" rx="8" ry="5.5" fill="#07101E" stroke="#1A5CFF" stroke-width="1"/>
                    <ellipse cx="136" cy="175" rx="8" ry="5.5" fill="#07101E" stroke="#00C8FF" stroke-width="1"/>
                    <circle cx="22" cy="104" r="3" fill="#00C8FF" opacity="0.75">
                      <animate attributeName="opacity" values="0.75;1;0.4;1;0.75" dur="3s" repeatCount="indefinite"/>
                    </circle>
                    <circle cx="118" cy="104" r="3" fill="#00C8FF" opacity="0.75">
                      <animate attributeName="opacity" values="0.4;0.75;1;0.75;0.4" dur="3s" repeatCount="indefinite"/>
                    </circle>
                    <rect x="60" y="90" width="20" height="12" rx="5" fill="#09131F" stroke="#00C8FF" stroke-width="1.1"/>
                    <ellipse cx="70" cy="58" rx="30" ry="36" fill="#09131F" stroke="#00C8FF" stroke-width="1.8"/>
                    <ellipse cx="57" cy="58" rx="7.5" ry="5.5" fill="#011518" stroke="rgba(180,215,240,0.32)" stroke-width="0.9"/>
                    <ellipse cx="57" cy="58" rx="4.5" ry="4" fill="#002535"/>
                    <ellipse cx="57" cy="58" rx="2.8" ry="2.8" fill="#00C8FF" opacity="0.9">
                      <animate attributeName="opacity" values="0.9;1;0.7;1;0.9" dur="4s" repeatCount="indefinite"/>
                    </ellipse>
                    <ellipse cx="83" cy="58" rx="7.5" ry="5.5" fill="#011518" stroke="rgba(180,215,240,0.32)" stroke-width="0.9"/>
                    <ellipse cx="83" cy="58" rx="4.5" ry="4" fill="#002535"/>
                    <ellipse cx="83" cy="58" rx="2.8" ry="2.8" fill="#00C8FF" opacity="0.9">
                      <animate attributeName="opacity" values="0.7;0.9;1;0.9;0.7" dur="4s" repeatCount="indefinite"/>
                    </ellipse>
                    <path d="M58,83 Q70,92 82,83" stroke="rgba(0,200,255,0.62)" stroke-width="1.6" fill="none" stroke-linecap="round"/>
                  </svg>
                </div>
              </div><!-- /sim-stage -->

              <!-- 苏格拉底对话栈 -->
              <div class="sim-teacher-dock">
                <div class="sim-t-hd">
                  <div class="sim-t-bar-indicator"></div>
                  <span class="sim-t-name">苏格拉底老师</span>
                  <span class="sim-t-scene">（{{ sel }}）</span>
                </div>
                <p class="sim-t-text">{{ currentDialogue }}</p>
                <div class="sim-t-nav">
                  <div class="sim-t-progress">
                    <div class="sim-t-fill" :style="{ width: (simStep / simTotal * 100) + '%' }"></div>
                  </div>
                  <span class="sim-t-count">{{ simStep }}/{{ simTotal }}</span>
                  <button class="sim-t-btn" @click="simStep = Math.min(simStep + 1, simTotal)">下一步 →</button>
                </div>
              </div>

              <!-- 底部返回操作 -->
              <div class="zysy-result-foot" style="flex-shrink:0;background:#091320;border-top:1px solid rgba(0,200,255,0.08);">
                <button class="zysy-btn-ghost small" @click="screen = 'result'">← 返回诊断结果</button>
                <button class="zysy-btn-ghost small close-btn" @click="handleClose">关闭</button>
              </div>

            </div><!-- /simulation screen -->
          </Transition>

          <!-- ══════ Screen 4：自适应误解检验 ══════ -->
          <Transition name="zysy-slide">
            <div v-if="screen === 'challenger'" class="zysy-body challenger-body" key="challenger">

              <!-- 标题行 -->
              <div class="zysy-chall-header">
                <div class="zysy-chall-icon">
                  <svg width="18" height="18" viewBox="0 0 18 18">
                    <path d="M9 1L11 6.5H17L12.5 9.5L14 15L9 12L4 15L5.5 9.5L1 6.5H7Z" fill="none" stroke="#00C8FF" stroke-width="1.5"/>
                    <circle cx="9" cy="9" r="2" fill="rgba(0,200,255,0.3)"/>
                  </svg>
                </div>
                <div>
                  <div class="zysy-chall-title">自适应误解检验</div>
                  <div class="zysy-chall-sub">Challenger Agent 针对诊断结果追问，验证理解深度</div>
                </div>
                <span class="zysy-chall-badge">
                  <svg width="10" height="10" viewBox="0 0 10 10"><circle cx="5" cy="5" r="3.5" fill="none" stroke="#FFD700" stroke-width="1.3"/><circle cx="5" cy="5" r="1.5" fill="#FFD700" opacity="0.7"/></svg>
                  ACTIVE
                </span>
              </div>

              <!-- 误解检验卡片（深色视觉包裹） -->
              <div class="zysy-chall-card-wrap">
                <ChallengerQuizCard />
              </div>

              <!-- 底部操作行 -->
              <div class="zysy-result-foot">
                <button class="zysy-btn-ghost small" @click="screen = 'result'">
                  ← 返回诊断结果
                </button>
                <button class="zysy-btn-ghost small close-btn" @click="handleClose">
                  关闭
                </button>
              </div>

            </div><!-- /challenger screen -->
          </Transition>

        </div><!-- /.zysy-modal -->
      </div><!-- /.zysy-overlay -->
    </Transition>
  </Teleport>
</template>

<style scoped>
/* ── 遮罩 ─────────────────────────────────────────────── */
.zysy-overlay {
  position: fixed; inset: 0; z-index: 9000;
  display: flex; align-items: center; justify-content: center;
  background: rgba(4, 8, 18, 0.82);
  backdrop-filter: blur(6px);
  padding: 24px 16px;
}

/* ── 弹窗主体 ────────────────────────────────────────── */
.zysy-modal {
  position: relative;
  width: 100%; max-width: 560px;
  background: #0B1121;
  border: 1px solid #1E3A58;
  border-radius: 14px;
  box-shadow: 0 0 80px rgba(0,200,255,0.08), 0 28px 70px rgba(0,0,0,0.65);
  overflow: hidden;
  max-height: 90vh;
  display: flex; flex-direction: column;
}

/* ── 电路折角 ────────────────────────────────────────── */
.zysy-corner {
  position: absolute; pointer-events: none; z-index: 10;
}
.zysy-corner.tl { top: -2px; left: -2px; }
.zysy-corner.tr { top: -2px; right: -2px; transform: scaleX(-1); }
.zysy-corner.bl { bottom: -2px; left: -2px; transform: scaleY(-1); }
.zysy-corner.br { bottom: -2px; right: -2px; transform: scale(-1,-1); }

/* ── 顶部描线 ───────────────────────────────────────── */
.zysy-top-line {
  position: absolute; top: 0; left: 28px; right: 28px; height: 1px;
  background: linear-gradient(90deg, transparent, rgba(0,200,255,0.5), transparent);
  z-index: 6;
}

/* ── Header ─────────────────────────────────────────── */
.zysy-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 20px 13px;
  border-bottom: 1px solid #192840;
  background: linear-gradient(180deg, rgba(0,200,255,0.05) 0%, transparent 100%);
  flex-shrink: 0;
}
.zysy-logo-row { display: flex; align-items: center; gap: 12px; }
.zysy-logo {
  width: 46px; height: 46px; border-radius: 10px;
  background: linear-gradient(135deg, #002B40, #004D66);
  border: 1.5px solid #00C8FF;
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 0 16px rgba(0,200,255,0.35);
  flex-shrink: 0;
  animation: pulse-logo 2.4s ease-in-out infinite;
}
.zysy-title {
  font-family: 'Courier New', monospace;
  font-size: 20px; font-weight: 800; color: #fff;
  letter-spacing: 4px;
  text-shadow: 0 0 20px rgba(0,200,255,0.4);
}
.zysy-subtitle { font-size: 11px; color: #5E88B0; margin-top: 2px; letter-spacing: 1.2px; }
.zysy-header-right { display: flex; align-items: center; gap: 8px; }
.zysy-badge {
  padding: 3px 10px; border-radius: 20px;
  background: rgba(0,200,255,0.08); border: 1px solid rgba(0,200,255,0.35);
  font-size: 10px; color: #00C8FF; letter-spacing: 0.8px; font-family: monospace;
}
.zysy-badge.result {
  background: rgba(46,204,113,0.1); border-color: rgba(46,204,113,0.4);
  color: #2ECC71;
}
.zysy-close {
  width: 28px; height: 28px; border-radius: 50%;
  background: rgba(255,255,255,0.04); border: 1px solid #192840;
  color: #5E88B0; cursor: pointer; font-size: 16px;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.15s;
}
.zysy-close:hover { background: rgba(255,255,255,0.1); color: #C5DCF2; }

/* ── 内容区 ──────────────────────────────────────────── */
.zysy-body {
  padding: 18px 20px 22px;
  overflow-y: auto;
  flex: 1;
}
.result-body { padding: 16px 20px 20px; }

/* ── 输入框 ──────────────────────────────────────────── */
.zysy-input-wrap {
  position: relative;
  background: #0D1520;
  border: 1.5px solid #192840;
  border-radius: 10px; padding: 12px 14px 8px;
  margin-bottom: 14px;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.zysy-input-wrap.focused {
  border-color: #00C8FF;
  box-shadow: 0 0 16px rgba(0,200,255,0.14), inset 0 0 20px rgba(0,200,255,0.03);
}
.zysy-input-label {
  position: absolute; top: -11px; left: 14px;
  font-size: 9px; color: #00C8FF; background: #0D1520;
  padding: 0 6px; letter-spacing: 1px; font-family: monospace;
  border: 1px solid rgba(0,200,255,0.25); border-radius: 4px;
}
.zysy-textarea {
  width: 100%; background: transparent; border: none; outline: none;
  resize: none; color: #C5DCF2; font-size: 13px; line-height: 1.75;
  font-family: system-ui, sans-serif; box-sizing: border-box;
}
.zysy-textarea::placeholder { color: #2E4560; }
.zysy-input-foot {
  display: flex; justify-content: space-between; align-items: center;
  margin-top: 4px; border-top: 1px solid #192840; padding-top: 6px;
}
.zysy-status-dot { font-size: 9px; color: #2E4560; font-family: monospace; letter-spacing: 0.5px; }
.zysy-char-count  { font-size: 10px; color: #2E4560; }

/* ── 按钮 ────────────────────────────────────────────── */
.zysy-btn-center { display: flex; justify-content: center; margin-bottom: 20px; }
.zysy-btn-ghost {
  padding: 10px 34px; border-radius: 24px;
  background: linear-gradient(135deg, #001E30, #003348);
  border: 1px solid #1E3A58; color: #fff;
  cursor: pointer; font-size: 13px; font-weight: 600;
  display: flex; align-items: center; gap: 8px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.4);
  transition: all 0.2s;
}
.zysy-btn-ghost:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 0 20px rgba(0,200,255,0.35), 0 6px 16px rgba(0,0,0,0.4);
  border-color: #00C8FF;
}
.zysy-btn-ghost.loading { opacity: 0.75; cursor: not-allowed; }
.zysy-btn-ghost.small {
  padding: 7px 18px; font-size: 12px; margin-bottom: 0;
}
.zysy-btn-ghost.close-btn { border-color: rgba(0,200,255,0.3); }

.zysy-btn-primary {
  padding: 12px 44px; border-radius: 26px;
  background: linear-gradient(135deg, #004D6A, #006E8F);
  border: 1.5px solid #00C8FF; color: #fff;
  cursor: pointer; font-size: 13.5px; font-weight: 700;
  display: flex; align-items: center; gap: 9px; letter-spacing: 0.8px;
  box-shadow: 0 0 18px rgba(0,200,255,0.25), 0 4px 14px rgba(0,0,0,0.35);
  transition: all 0.2s;
}
.zysy-btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 0 28px rgba(0,200,255,0.45), 0 6px 20px rgba(0,0,0,0.4);
}
.zysy-btn-primary.loading { opacity: 0.75; cursor: not-allowed; }

/* ── 分隔线 ──────────────────────────────────────────── */
.zysy-divider {
  display: flex; align-items: center; gap: 12px; margin-bottom: 22px;
}
.zysy-divider::before, .zysy-divider::after {
  content: ''; flex: 1; height: 1px; background: #192840;
}
.zysy-divider span { color: #2E4560; font-size: 12px; letter-spacing: 2px; }

/* ── 协议卡片 ────────────────────────────────────────── */
.zysy-protocol-card {
  background: #0F1828; border: 1px solid #192840;
  border-radius: 12px; padding: 20px 18px;
  position: relative;
  box-shadow: inset 0 1px 0 rgba(0,200,255,0.06);
}
.zysy-pc-top-line {
  position: absolute; top: 0; left: 24px; right: 24px; height: 1px;
  background: linear-gradient(90deg, transparent, rgba(0,200,255,0.3), transparent);
}
.zysy-pc-icon {
  display: flex; justify-content: center; margin-bottom: 14px;
}
.zysy-pc-icon > svg {
  width: 52px; height: 52px; padding: 13px;
  border-radius: 50%;
  background: rgba(0,200,255,0.06);
  border: 1.5px solid rgba(0,200,255,0.25);
  box-shadow: 0 0 16px rgba(0,200,255,0.12);
  box-sizing: content-box;
}
.zysy-pc-title {
  text-align: center; font-size: 15px; font-weight: 700;
  color: #C5DCF2; letter-spacing: 1.5px; margin-bottom: 6px;
  font-family: 'Courier New', monospace;
}
.zysy-pc-desc {
  text-align: center; font-size: 11.5px; color: #5E88B0;
  margin-bottom: 20px; line-height: 1.65;
}

/* ── 协议标签 ────────────────────────────────────────── */
.zysy-tags {
  display: flex; flex-wrap: wrap; gap: 8px;
  justify-content: center; margin-bottom: 22px;
}
.zysy-tag {
  padding: 6px 14px; border-radius: 20px;
  background: rgba(255,255,255,0.025);
  border: 1px solid #192840; color: #5E88B0;
  cursor: pointer; font-size: 12px; font-weight: 400;
  display: flex; align-items: center; gap: 6px;
  transition: all 0.18s;
}
.zysy-tag:hover { border-color: rgba(0,200,255,0.5); color: #7ADCFF; }
.zysy-tag.active {
  background: rgba(0,200,255,0.12);
  border-color: #00C8FF; color: #00C8FF;
  font-weight: 700;
  box-shadow: 0 0 10px rgba(0,200,255,0.22);
}
.zysy-tag-dot {
  width: 6px; height: 6px; border-radius: 50%;
  display: inline-block; flex-shrink: 0;
  transition: all 0.18s;
}

/* ── 结果屏 ──────────────────────────────────────────── */
.zysy-status-row {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 16px;
}
.zysy-done-label {
  display: flex; align-items: center; gap: 8px;
  font-size: 14px; font-weight: 700; color: #C5DCF2; letter-spacing: 0.5px;
}
.zysy-ai-badge {
  display: flex; align-items: center; gap: 6px;
  background: rgba(0,200,255,0.1); border: 1px solid rgba(0,200,255,0.4);
  border-radius: 20px; padding: 4px 12px;
  font-size: 11px; font-weight: 700; color: #00C8FF; letter-spacing: 0.8px;
  box-shadow: 0 0 10px rgba(0,200,255,0.12);
}
.zysy-stepper-wrap { margin-bottom: 16px; }
.zysy-result-foot {
  display: flex; justify-content: flex-end; gap: 8px; flex-wrap: wrap;
  margin-top: 16px; padding-top: 14px;
  border-top: 1px solid rgba(0,200,255,0.1);
}

/* ── 诊断结果可视化面板 ─────────────────── */
.zysy-viz-panel {
  background: #0A1020;
  border: 1px solid rgba(0,200,255,0.15);
  border-radius: 10px; padding: 14px 16px;
  margin-bottom: 14px;
  position: relative;
}
/* CLIENT/SERVER 头部 */
.viz-cs-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 8px;
}
.viz-cs-box {
  padding: 3px 12px; border-radius: 4px;
  background: rgba(0,200,255,0.08); border: 1px solid rgba(0,200,255,0.35);
  font-size: 10px; font-weight: 700; color: #00C8FF; font-family: monospace;
  letter-spacing: 1px;
}
.viz-server-box { position: relative; display: flex; flex-direction: column; align-items: center; gap: 3px; }
.viz-rfc-tag { font-size: 8px; color: rgba(0,200,255,0.5); letter-spacing: 0.5px; }
.viz-syn-area { display: flex; flex-direction: column; align-items: center; gap: 3px; flex: 1; }
.viz-syn-label {
  font-size: 9px; font-weight: 700; color: #00C8FF; font-family: monospace;
  background: rgba(0,200,255,0.1); border: 1px solid rgba(0,200,255,0.3);
  padding: 2px 8px; border-radius: 3px;
}
.viz-syn-arrow {
  width: 80%; height: 1px;
  background: linear-gradient(90deg, rgba(0,200,255,0.2), rgba(0,200,255,0.6), rgba(0,200,255,0.2));
  position: relative;
}
.viz-syn-arrow::after {
  content: ''; position: absolute; right: 0; top: -3px;
  width: 0; height: 0;
  border-left: 5px solid rgba(0,200,255,0.6);
  border-top: 3px solid transparent;
  border-bottom: 3px solid transparent;
}
/* 虽制线 */
.viz-dash-lines { display: flex; justify-content: space-between; padding: 0 24px; margin-bottom: 6px; }
.viz-dash-left, .viz-dash-right {
  width: 1px; height: 16px;
  background: repeating-linear-gradient(to bottom, rgba(0,200,255,0.4) 0, rgba(0,200,255,0.4) 3px, transparent 3px, transparent 6px);
}
.viz-dash-center {
  width: 1px; height: 16px;
  background: rgba(0,200,255,0.15);
}
/* 控制点 */
.viz-dots-row { display: flex; justify-content: space-between; padding: 0 22px; margin-bottom: 10px; }
.viz-dot { width: 6px; height: 6px; border-radius: 50%; background: rgba(0,200,255,0.25); border: 1px solid rgba(0,200,255,0.4); }
.viz-dot.active { background: #00C8FF; box-shadow: 0 0 6px #00C8FF; }
/* 进度条 */
.viz-bars { display: flex; flex-direction: column; gap: 7px; }
.viz-bar-row { display: flex; align-items: center; gap: 8px; }
.viz-bar-label { font-size: 11px; min-width: 82px; font-family: monospace; letter-spacing: 0.3px; }
.viz-bar-track {
  flex: 1; height: 5px; background: rgba(255,255,255,0.06);
  border-radius: 3px; overflow: hidden;
}
.viz-bar-fill {
  height: 100%; border-radius: 3px;
  transition: width 0.8s ease;
  box-shadow: 0 0 6px currentColor;
}
.viz-bar-pct { font-size: 11px; font-weight: 700; min-width: 34px; text-align: right; font-family: monospace; }

/* AI 诊断文本块 */
.zysy-ai-text-block {
  background: #0A1020;
  border: 1px solid rgba(0,200,255,0.1);
  border-left: 3px solid rgba(0,200,255,0.5);
  border-radius: 8px; padding: 14px 16px;
  margin-bottom: 14px;
}
.ai-text-title {
  font-size: 14px; font-weight: 700; color: #C5DCF2;
  margin-bottom: 8px; letter-spacing: 0.5px;
}
.ai-text-body {
  font-size: 12px; color: #5E88B0; line-height: 1.7;
  margin: 0 0 10px;
}
.ai-text-highlight { color: #C5DCF2; font-weight: 600; }
.ai-text-rfc {
  font-size: 11px; color: #2E4560; background: rgba(0,200,255,0.04);
  border: 1px solid #192840; border-radius: 5px;
  padding: 6px 10px; font-family: monospace; letter-spacing: 0.5px;
  margin-bottom: 8px;
}
.ai-text-date { font-size: 10px; color: #2E4560; }

/* ── 沉浸仿真场景屏 ──────────────────── */
/* ── 沉浸仿真场景屏 (v2) ──────────── */
.sim-body { padding: 0; overflow: hidden; display: flex; flex-direction: column; }
.sim-stage {
  position: relative; overflow: hidden; flex: 1; min-height: 280px;
  background: linear-gradient(180deg, #020810 0%, #040D1A 55%, #06101E 100%);
}
.sim-top-glow-bar {
  position: absolute; top: 0; left: 20%; right: 20%; height: 2px;
  background: linear-gradient(90deg, transparent, rgba(0,200,255,0.6), transparent);
  box-shadow: 0 0 20px 4px rgba(0,200,255,0.2);
}
.sim-abs-panel {
  position: absolute; top: 24px;
  background: #040B15; border-radius: 7px; padding: 8px 10px;
}
.sim-panel-left  { left: 14px; width: 128px; border: 1px solid rgba(0,200,255,0.2); box-shadow: 0 0 20px rgba(0,200,255,0.08); }
.sim-panel-right { right: 14px; width: 148px; border: 1px solid rgba(26,92,255,0.28); box-shadow: 0 0 20px rgba(26,92,255,0.1); }
.sim-panel-lbl { font-size: 7.5px; font-family: monospace; margin-bottom: 6px; letter-spacing: 1px; color: rgba(0,200,255,0.6); }
.sim-panel-lbl.blue { color: #7AABFF; }
.sim-ptag-row { display: flex; gap: 4px; margin-top: 5px; }
.sim-ptag { font-size: 7px; padding: 1.5px 5px; border-radius: 3px; font-family: monospace; background: rgba(0,200,255,0.06); border: 1px solid rgba(0,200,255,0.15); color: rgba(0,200,255,0.4); }
.sim-ptag.active { background: rgba(0,200,255,0.12); border-color: rgba(0,200,255,0.4); color: #00C8FF; }
.sim-stack-item {
  display: flex; justify-content: space-between; align-items: center;
  padding: 4px 7px; margin-bottom: 4px; border-radius: 4px;
  background: rgba(26,92,255,0.07); border: 1px solid rgba(26,92,255,0.22);
  font-family: monospace;
}
.sim-center-lbl {
  position: absolute; top: 14px; left: 50%; transform: translateX(-50%);
  font-size: 11px; font-weight: 700; color: #00C8FF;
  font-family: 'Courier New', monospace; letter-spacing: 2px;
  text-shadow: 0 0 16px rgba(0,200,255,0.4);
  background: rgba(0,200,255,0.05); padding: 5px 16px; border-radius: 20px;
  border: 1px solid rgba(0,200,255,0.2);
  max-width: 60%; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  pointer-events: none;
}
.sim-pkt-wrap {
  position: absolute; top: 28%; left: 50%; transform: translateX(-50%);
  pointer-events: none;
}
.sim-avatar-wrap {
  position: absolute; bottom: 0; left: 50%; transform: translateX(-50%);
  display: flex; flex-direction: column; align-items: center;
  animation: float-up-center 4s ease-in-out infinite;
}
.sim-avatar-glow {
  position: absolute; bottom: -6px; width: 140px; height: 28px;
  background: radial-gradient(ellipse, rgba(0,200,255,0.18) 0%, transparent 70%);
}
/* 苏格拉底对话底栏 */
.sim-teacher-dock {
  background: linear-gradient(180deg, #091320 0%, #0B1728 100%);
  border-top: 1px solid rgba(0,200,255,0.2);
  padding: 13px 20px 12px;
  flex-shrink: 0;
}
.sim-t-hd { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.sim-t-bar-indicator {
  width: 3px; height: 20px; background: #00C8FF; border-radius: 2px; flex-shrink: 0;
  box-shadow: 0 0 8px rgba(0,200,255,0.4);
}
.sim-t-name { color: #00C8FF; font-weight: 800; font-size: 14px; letter-spacing: 0.5px; line-height: 1; }
.sim-t-scene {
  font-size: 10px; color: #5E88B0;
  background: rgba(0,200,255,0.06); border: 1px solid rgba(0,200,255,0.18);
  padding: 2px 8px; border-radius: 10px; line-height: 1.4;
}
.sim-t-text {
  font-size: 12.5px; color: #9BBFD8; line-height: 1.78; letter-spacing: 0.15px;
  height: 68px; overflow: hidden; margin: 0 0 12px;
  border-left: 2px solid rgba(0,200,255,0.16); padding-left: 11px;
}
.sim-t-nav { display: flex; align-items: center; gap: 12px; }
.sim-t-progress { flex: 1; height: 4px; background: rgba(255,255,255,0.05); border-radius: 4px; overflow: hidden; }
.sim-t-fill {
  height: 100%; border-radius: 4px;
  background: linear-gradient(90deg, #1A5CFF, #00C8FF);
  box-shadow: 0 0 8px rgba(0,200,255,0.4);
  transition: width 0.35s ease;
}
.sim-t-count { font-size: 10px; color: #2E4560; font-family: monospace; white-space: nowrap; }
.sim-t-btn {
  padding: 7px 16px; border-radius: 18px;
  background: rgba(0,200,255,0.08); border: 1px solid rgba(0,200,255,0.28);
  color: #C5DCF2; cursor: pointer; font-size: 11.5px; font-weight: 600;
  white-space: nowrap; transition: all 0.2s; letter-spacing: 0.3px;
}
.sim-t-btn:hover { background: rgba(0,200,255,0.14); border-color: rgba(0,200,255,0.5); transform: translateX(2px); }

/* ── TCP 握手 SVG 面板 ──────────────── */
.zysy-handshake-viz {
  background: #050D18; border: 1px solid #192840;
  border-radius: 10px; margin-bottom: 16px; overflow: hidden;
}
/* ── 掌握度面板 ───────────────── */
.zysy-mastery-panel {
  background: #0F1828; border: 1px solid #192840;
  border-radius: 10px; padding: 14px 16px; margin-bottom: 16px;
}
.mastery-hd { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.mastery-title { font-size: 10px; color: #5E88B0; font-weight: 600; font-family: monospace; letter-spacing: 1px; }
.mastery-weak  { font-size: 10px; color: #FF7060; }
.mastery-row   { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.mastery-name  { font-size: 11px; min-width: 82px; font-family: monospace; }
.mastery-track { flex: 1; height: 5px; background: rgba(255,255,255,0.05); border-radius: 3px; overflow: hidden; }
.mastery-fill  { height: 100%; border-radius: 3px; transition: width 0.4s ease; box-shadow: 0 0 5px currentColor; }
.mastery-pct   { font-size: 10px; font-weight: 700; min-width: 34px; text-align: right; font-family: monospace; }

/* ── 旋转图标 ────────────────────────────────────────── */
.spin-icon { animation: spin 0.8s linear infinite; }

/* ── 动画 ────────────────────────────────────────────── */
@keyframes pulse-logo {
  0%,100% { box-shadow: 0 0 10px rgba(0,200,255,0.3); opacity: 0.9; }
  50%      { box-shadow: 0 0 22px rgba(0,200,255,0.65); opacity: 1; }
}
@keyframes spin {
  0%   { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
@keyframes float-up-center {
  0%,100% { transform: translateX(-50%) translateY(0); }
  50%      { transform: translateX(-50%) translateY(-5px); }
}

/* ── 过渡 ─────────────────────────────────────────────── */
.zysy-fade-enter-active, .zysy-fade-leave-active { transition: opacity 0.25s ease; }
.zysy-fade-enter-from, .zysy-fade-leave-to { opacity: 0; }

.zysy-slide-enter-active { transition: opacity 0.2s ease, transform 0.2s ease; }
.zysy-slide-leave-active { transition: opacity 0.15s ease, transform 0.15s ease; position: absolute; width: 100%; }
.zysy-slide-enter-from   { opacity: 0; transform: translateX(16px); }
.zysy-slide-leave-to     { opacity: 0; transform: translateX(-16px); }

/* ── 滚动条美化 ──────────────────────────────────────── */
.zysy-body::-webkit-scrollbar,
.zysy-panel-wrap::-webkit-scrollbar { width: 4px; }
.zysy-body::-webkit-scrollbar-track,
.zysy-panel-wrap::-webkit-scrollbar-track { background: transparent; }
.zysy-body::-webkit-scrollbar-thumb,
.zysy-panel-wrap::-webkit-scrollbar-thumb {
  background: rgba(0,200,255,0.2); border-radius: 2px;
}

/* ── Tab 导航条 ──────────────────────────── */
.zysy-tabs {
  display: flex; align-items: center; justify-content: center; gap: 0;
  padding: 0 20px;
  border-bottom: 1px solid #192840;
  background: rgba(0,0,0,0.2);
  flex-shrink: 0;
}
.zysy-tab {
  padding: 9px 16px; border: none; background: transparent;
  color: #2E4560; font-size: 11px; font-weight: 600; cursor: pointer;
  display: flex; align-items: center; gap: 5px;
  border-bottom: 2px solid transparent;
  transition: all 0.2s; letter-spacing: 0.3px;
  white-space: nowrap;
}
.zysy-tab:hover { color: #5E88B0; }
.zysy-tab.active {
  color: #00C8FF;
  border-bottom-color: #00C8FF;
  background: rgba(0,200,255,0.04);
}
.tab-num {
  width: 16px; height: 16px; border-radius: 50%;
  background: rgba(0,200,255,0.06); border: 1px solid #192840;
  display: flex; align-items: center; justify-content: center;
  font-size: 9px; font-family: monospace; flex-shrink: 0;
  color: #2E4560;
}
.zysy-tab.active .tab-num {
  background: rgba(0,200,255,0.12); border-color: rgba(0,200,255,0.4);
  color: #00C8FF;
}
.zysy-badge.challenger-badge {
  background: rgba(255,215,0,0.08); border: 1px solid rgba(255,215,0,0.3);
  color: #FFD700;
}

/* ── 误解检验屏───────────────────────────── */
.challenger-body { padding: 16px 20px 20px; }
.zysy-chall-header {
  display: flex; align-items: center; gap: 12px;
  margin-bottom: 18px; padding-bottom: 14px;
  border-bottom: 1px solid #192840;
}
.zysy-chall-icon {
  width: 38px; height: 38px; border-radius: 9px; flex-shrink: 0;
  background: rgba(0,200,255,0.06); border: 1.5px solid rgba(0,200,255,0.25);
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 0 12px rgba(0,200,255,0.1);
}
.zysy-chall-title {
  font-size: 14px; font-weight: 700; color: #C5DCF2; letter-spacing: 0.8px;
}
.zysy-chall-sub { font-size: 11px; color: #5E88B0; margin-top: 2px; }
.zysy-chall-badge {
  margin-left: auto; flex-shrink: 0;
  display: flex; align-items: center; gap: 5px;
  background: rgba(255,215,0,0.08); border: 1px solid rgba(255,215,0,0.3);
  border-radius: 14px; padding: 3px 10px;
  font-size: 10px; color: #FFD700; font-weight: 700; font-family: monospace;
  letter-spacing: 0.5px;
}

/* ChallengerQuizCard 深色覆盖 */
.zysy-chall-card-wrap :deep(.challenger-quiz-card) {
  background: #0F1828 !important;
  border-color: #1E3A58 !important;
  margin-top: 0 !important;
}
.zysy-chall-card-wrap :deep(.card-title) {
  color: #00C8FF !important;
}
.zysy-chall-card-wrap :deep(.card-subtitle) {
  color: #5E88B0 !important;
}
.zysy-chall-card-wrap :deep(.empty-hint) {
  color: #5E88B0 !important;
}
.zysy-chall-card-wrap :deep(.question-text) {
  background: rgba(0,200,255,0.04) !important;
  border-left-color: #00C8FF !important;
  color: #C5DCF2 !important;
}
.zysy-chall-card-wrap :deep(.feedback-box) {
  background: #0D1520 !important;
  border-color: #192840 !important;
  color: #C5DCF2 !important;
}
.zysy-chall-card-wrap :deep(.feedback-box.feedback-correct) {
  background: rgba(46,204,113,0.06) !important;
  border-color: rgba(46,204,113,0.3) !important;
  color: #6EE7B7 !important;
}
.zysy-chall-card-wrap :deep(.feedback-box.feedback-incorrect) {
  background: rgba(245,158,11,0.06) !important;
  border-color: rgba(245,158,11,0.25) !important;
  color: #FCD34D !important;
}
.zysy-chall-card-wrap :deep(.feedback-label) { color: inherit !important; }
.zysy-chall-card-wrap :deep(.assessment-box) {
  background: rgba(46,204,113,0.06) !important;
  border-color: rgba(46,204,113,0.25) !important;
}
.zysy-chall-card-wrap :deep(.assessment-title) { color: #6EE7B7 !important; }
.zysy-chall-card-wrap :deep(.assessment-score) { color: #A7F3D0 !important; }
.zysy-chall-card-wrap :deep(.suggestion-list) { color: #6EE7B7 !important; }
.zysy-chall-card-wrap :deep(.round-meta .el-tag) {
  background: rgba(0,200,255,0.08) !important;
  border-color: rgba(0,200,255,0.25) !important;
  color: #00C8FF !important;
}
.zysy-chall-card-wrap :deep(.el-textarea__inner) {
  background: #0D1520 !important;
  border-color: #1E3A58 !important;
  color: #C5DCF2 !important;
}
.zysy-chall-card-wrap :deep(.el-textarea__inner:focus) {
  border-color: #00C8FF !important;
  box-shadow: 0 0 8px rgba(0,200,255,0.15) !important;
}
.zysy-chall-card-wrap :deep(.el-button--primary) {
  background: linear-gradient(135deg, #004D6A, #006E8F) !important;
  border-color: #00C8FF !important;
  color: #fff !important;
}
.zysy-chall-card-wrap :deep(.el-button--primary:hover) {
  box-shadow: 0 0 16px rgba(0,200,255,0.3) !important;
}
</style>
