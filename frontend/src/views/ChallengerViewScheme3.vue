<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import ChallengerQuizCard from '@/components/ChallengerQuizCard.vue'
import { useChatStore } from '@/stores/chatStore'

const router = useRouter()
const chatStore = useChatStore()
const hasActiveChallenge = computed(() =>
  chatStore.lastChallenger !== null && chatStore.lastChallenger?.status !== 'completed'
)

interface ChallengeRound {
  id: number; topic: string; statement: string; isCorrect: boolean
  misconception: string; truth: string; explanation: string; difficulty: string; diffColor: string
}

const rounds: ChallengeRound[] = [
  { id: 1, topic: 'TCP 可靠性', difficulty: '中等', diffColor: '#F59E0B',
    statement: 'TCP 协议通过三次握手建立连接后，就不会再丢失任何数据包了，因为连接已经建立。',
    isCorrect: false, misconception: '认为建立连接后就不会丢包',
    truth: 'TCP 的可靠性通过序列号、确认应答和重传机制实现，连接建立后仍可能丢包，只是 TCP 会自动重传。',
    explanation: '三次握手仅用于同步初始序列号和分配资源，数据传输阶段的可靠性依赖于 ACK、超时重传、滑动窗口等机制。' },
  { id: 2, topic: 'UDP vs TCP', difficulty: '简单', diffColor: '#10B981',
    statement: 'UDP 比 TCP 快是因为 UDP 的头部比 TCP 小，所以传输效率更高。',
    isCorrect: false, misconception: '将速度快完全归因于头部大小',
    truth: 'UDP 快的主要原因是无连接、无握手、无拥塞控制、无重传，头部小只是次要因素。',
    explanation: 'UDP 省去连接建立、流量控制、拥塞控制等机制，减少了延迟和状态维护开销，而不仅仅是头部大小的差异。' },
  { id: 3, topic: '三次握手', difficulty: '中等', diffColor: '#F59E0B',
    statement: 'TCP 三次握手中，第三次握手（ACK）丢失的话，连接仍然可以正常建立，因为服务端已经发送了 SYN+ACK。',
    isCorrect: false, misconception: '认为服务端发出 SYN+ACK 即算连接建立',
    truth: '第三次 ACK 丢失会导致服务端重传 SYN+ACK，直到超时或收到 ACK。连接必须双方都确认才建立。',
    explanation: 'TCP 是全双工连接，必须双方都进入 ESTABLISHED 状态。服务端没收到第三次 ACK 时仍处于 SYN_RCVD 状态。' },
  { id: 4, topic: 'IP 与 MAC', difficulty: '简单', diffColor: '#10B981',
    statement: '在同一个局域网内，数据帧通过目的 IP 地址直接找到目标主机。',
    isCorrect: false, misconception: '混淆网络层和数据链路层',
    truth: '局域网内通过 MAC 地址寻址，需要 ARP 协议将 IP 解析为 MAC，数据帧头部只包含 MAC 地址。',
    explanation: 'IP 地址用于网络层路由，MAC 地址用于数据链路层局域网内寻址。' },
  { id: 5, topic: '子网掩码', difficulty: '困难', diffColor: '#EF4444',
    statement: '子网掩码 255.255.255.0 表示这个子网最多可以有 256 台主机。',
    isCorrect: false, misconception: '忽略网络地址和广播地址',
    truth: '8 位主机号最多有 2^8 - 2 = 254 个可用主机地址，要减去全 0（网络地址）和全 1（广播地址）。',
    explanation: '主机号全 0 表示网络本身，全 1 表示广播地址，这两个地址不能分配给主机使用。' },
  { id: 6, topic: 'HTTP 与 TCP', difficulty: '困难', diffColor: '#EF4444',
    statement: 'HTTP/1.1 的持久连接（Keep-Alive）意味着一个 TCP 连接上可以同时并行传输多个请求。',
    isCorrect: false, misconception: '混淆持久连接和多路复用',
    truth: 'HTTP/1.1 Keep-Alive 允许复用连接串行发送请求，真正的并行需要 HTTP/2 的多路复用。',
    explanation: 'HTTP/1.1 持久连接解决了重复建立 TCP 连接的开销，但请求仍是串行的。' },
]

const currentIndex = ref(0)
const userJudgment = ref<'correct' | 'incorrect' | null>(null)
const showResult = ref(false)
const score = ref(0)
const streak = ref(0)
const maxStreak = ref(0)
const history = ref<{ round: number; correct: boolean }[]>([])

const currentRound = computed(() => rounds[currentIndex.value])
const totalRounds = rounds.length
const isFinished = computed(() => currentIndex.value >= totalRounds)
const wrongCount = computed(() => history.value.filter(h => !h.correct).length)
const progressPercent = computed(() => isFinished.value ? 100 : (currentIndex.value / totalRounds) * 100)
const correctRate = computed(() => history.value.length === 0 ? 0 : Math.round((score.value / history.value.length) * 100))

const circleCircumference = 2 * Math.PI * 40
const progressDasharray = computed(() => {
  const fill = (progressPercent.value / 100) * circleCircumference
  return `${fill.toFixed(1)} ${(circleCircumference - fill).toFixed(1)}`
})

// Filter tabs
const topicFilter = ref('全部')
const topicOptions = computed(() => ['全部', ...new Set(rounds.map(r => r.topic))])
const topicCount = (topic: string) => topic === '全部' ? rounds.length : rounds.filter(r => r.topic === topic).length
const filteredRounds = computed(() =>
  topicFilter.value === '全部' ? rounds : rounds.filter(r => r.topic === topicFilter.value)
)

// ── 认知漏洞数据 ──
interface VulnItem { name: string; severity: string; sevClass: string; pct: number; fill: string; detail: string }
const allVulnerabilities: VulnItem[] = [
  { name: 'TCP 状态转换理解不足', severity: '中等', sevClass: 's3-sev-medium', pct: 70, fill: 'linear-gradient(90deg,#f59e0b,#f97316)', detail: '状态机迁移路径混淆' },
  { name: 'ACK 机制理解不完整', severity: '较低', sevClass: 's3-sev-low',    pct: 40, fill: 'linear-gradient(90deg,#10b981,#06b6d4)', detail: '确认机制偏差' },
  { name: '拥塞控制理解偏差',   severity: '中等', sevClass: 's3-sev-medium', pct: 55, fill: 'linear-gradient(90deg,#f59e0b,#f97316)', detail: '拥塞窗口机制理解不足' },
  { name: 'HTTP 与 TCP 关系混淆', severity: '较低', sevClass: 's3-sev-low', pct: 28, fill: 'linear-gradient(90deg,#10b981,#06b6d4)', detail: '协议层级理解偏差' },
]
const showAllVulns = ref(false)
const displayedVulns = computed(() => showAllVulns.value ? allVulnerabilities : allVulnerabilities.slice(0, 2))
const vulnTotal = computed(() => wrongCount.value > 0 ? allVulnerabilities.length : 2)

// 是否已有诊断结果
const hasDiagnosis = computed(() => !!chatStore.lastDiagnosis)

// Scan line animation (for question panel)
const scanLine = ref(0)
let scanTimer: ReturnType<typeof setInterval> | null = null
onMounted(() => { scanTimer = setInterval(() => { scanLine.value = (scanLine.value + 1.5) % 100 }, 40) })
onUnmounted(() => { if (scanTimer) clearInterval(scanTimer) })

// Ticker
const tickerItems = ['TCP', 'IP', 'UDP', 'HTTP/2', 'DNS', 'TLS 1.3', 'ARP', 'ICMP', 'BGP', 'OSPF', 'SYN', 'ACK', 'QUIC', 'WebSocket']
const tickerText = computed(() => tickerItems.join('  ·  ') + '  ·  ' + tickerItems.join('  ·  '))

function judge(correct: boolean) { userJudgment.value = correct ? 'correct' : 'incorrect' }
function submitAnswer() {
  if (!userJudgment.value) return
  const isUserCorrect = (userJudgment.value === 'correct') === currentRound.value.isCorrect
  if (isUserCorrect) { score.value++; streak.value++; if (streak.value > maxStreak.value) maxStreak.value = streak.value }
  else { streak.value = 0 }
  history.value.push({ round: currentRound.value.id, correct: isUserCorrect })
  showResult.value = true
}
function nextRound() { currentIndex.value++; userJudgment.value = null; showResult.value = false }
function resetAll() {
  currentIndex.value = 0; userJudgment.value = null; showResult.value = false
  score.value = 0; streak.value = 0; maxStreak.value = 0; history.value = []
}
function getHistoryItem(id: number) { return history.value.find(x => x.round === id) }

// ── 导航函数（严谨逻辑）──

/** 前往认知诊断页 */
function goToDiagnosis() {
  router.push('/diagnosis')
}

/** 前往学习路径页 */
function goToPath() {
  router.push('/path')
}

/** 前往能力画像页 */
function goToProfile() {
  router.push('/profile')
}

/** 前往知识图谱AI助手页 */
function goToKGAssist() {
  router.push('/kg-assist')
}

/**
 * 点击“分析漏洞”小圆片：
 * 若尚未完成诊断，提示并跳转诊断页；已有诊断结果则直接跳转
 */
function onAnalysisClick() {
  if (!hasDiagnosis.value) {
    ElMessage.warning('请先完成认知诊断，AI 将自动分析你的知识漏洞')
    router.push('/diagnosis')
  } else {
    ElMessage.success('已检测到诊断结果，正在分析知识漏洞...')
  }
}

/**
 * 点击“推送题目”小圆片：已在当前页面，平滑滚动到挑战卡
 */
function scrollToChallenge() {
  const el = document.querySelector('.s3-challenge-card-wrap') as HTMLElement | null
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
    // 闪烁高亮效果
    el.style.boxShadow = '0 0 0 2px #6366f1, 0 4px 24px rgba(99,102,241,0.3)'
    setTimeout(() => { el.style.boxShadow = '' }, 1200)
  }
  ElMessage.info('当前正处于纳正建议阶段，继续完成挑战题即可')
}
</script>

<template>
  <div class="s3-page">
    <!-- Cosmic particles -->
    <div class="s3-particles" aria-hidden="true">
      <span v-for="i in 18" :key="i" class="s3-particle"
        :style="{ left: (i*5.5-2)+'%', animationDelay: (i*0.35)+'s', animationDuration: (8+i%5)+'s' }"></span>
    </div>

    <!-- ═══ Ticker Bar (from Scheme 2, light style) ═══ -->
    <div class="s3-ticker-bar">
      <span class="s3-ticker-chip">PROTOCOL STACK</span>
      <div class="s3-ticker-track">
        <div class="s3-ticker-inner">{{ tickerText }}</div>
      </div>
      <div class="s3-ticker-leds">
        <span class="s3-t-led s3-t-green" title="诊断陈述正确"></span>
        <span class="s3-t-led s3-t-purple" title="分析误解原因"></span>
        <span class="s3-t-led s3-t-red" title="固化正确认知"></span>
        <span class="s3-ticker-online">ONLINE</span>
      </div>
    </div>

    <!-- ═══ HERO (dark gradient section) ═══ -->
    <div class="s3-hero">
      <div class="s3-hero-inner">
        <div class="s3-hero-left">
          <div class="s3-hero-orb">
            <span class="s3-orb-icon">⚡</span>
            <div class="s3-orb-ring"></div>
          </div>
          <div class="s3-hero-info">
            <div class="s3-hero-sup">
              <span class="s3-lv-badge">Lv.2 训练中</span>
              <span class="s3-time-badge">⏱ 预计5分钟</span>
            </div>
            <h1 class="s3-hero-title">Concept Challenge Lab</h1>
            <p class="s3-hero-sub">AI 主动挑战你对计算机网络概念的认知模型，识别并纠正错误认知</p>
            <div class="s3-hero-theme-row">
              <span class="s3-theme-label">当前主题</span>
              <span class="s3-theme-value">{{ isFinished ? '挑战完成' : currentRound.topic }}</span>
              <span class="s3-theme-sep">·</span>
              <span class="s3-theme-tags">TCP / 状态转换 / 连接建立</span>
            </div>
          </div>
        </div>
        <!-- Circular progress -->
        <div class="s3-hero-progress">
          <p class="s3-pg-label">当前进度</p>
          <div class="s3-pg-ring-wrap">
            <svg viewBox="0 0 90 90" class="s3-pg-svg">
              <circle cx="45" cy="45" r="40" class="s3-pg-bg"/>
              <circle cx="45" cy="45" r="40" class="s3-pg-fill" :style="{ strokeDasharray: progressDasharray }"/>
            </svg>
            <div class="s3-pg-center">
              <span class="s3-pg-main">{{ currentIndex }}</span>
              <span class="s3-pg-sub">/ {{ totalRounds }}</span>
              <span class="s3-pg-pct">{{ progressPercent.toFixed(0) }}%</span>
            </div>
          </div>
        </div>
        <!-- Stats -->
        <div class="s3-hero-stats">
          <div class="s3-stat-card">
            <div class="s3-stat-icon">🎯</div>
            <div class="s3-stat-val">{{ correctRate }}%</div>
            <div class="s3-stat-lbl">正确率</div>
          </div>
          <div class="s3-stat-card">
            <div class="s3-stat-icon">🔥</div>
            <div class="s3-stat-val">{{ streak }}</div>
            <div class="s3-stat-lbl">连续</div>
          </div>
          <div class="s3-stat-card">
            <div class="s3-stat-icon">📊</div>
            <div class="s3-stat-val">{{ score >= 5 ? '高级' : score >= 3 ? '中级' : '初级' }}</div>
            <div class="s3-stat-lbl">掌握度</div>
          </div>
          <div class="s3-stat-card">
            <div class="s3-stat-icon">⚡</div>
            <div class="s3-stat-val">{{ maxStreak }}</div>
            <div class="s3-stat-lbl">最高连胜</div>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══ Main Body (light area) ═══ -->
    <div class="s3-body">
      <div class="s3-main-grid">

        <!-- ── Col 1: AI Tutor + Cognitive Scanner ── -->
        <div class="s3-left-col">
          <!-- AI Tutor card -->
          <div class="s3-glass-card">
            <div class="s3-card-head">
              <div class="s3-card-title-row">
                <div class="s3-card-dot s3-dot-purple"></div>
                <span class="s3-card-title">AI Tutor 对话挑战</span>
                <span class="s3-card-badge">自适应追问中</span>
              </div>
            </div>
            <div v-if="hasActiveChallenge" class="s3-quiz-wrap">
              <ChallengerQuizCard />
            </div>
            <div v-else class="s3-ai-empty">
              <div class="s3-chat-bubble-wrap">
                <div class="s3-chat-avatar">🤖</div>
                <div class="s3-chat-bubble">
                  <p>我发现你在 TCP 连接建立的理解上可能存在一些误解。完成诊断后我将根据你的知识漏洞生成个性化追问。</p>
                </div>
              </div>
              <div class="s3-ai-flow-steps">
                <div class="s3-flow-pill s3-flow-active s3-flow-btn" @click="goToDiagnosis" title="前往完成认知诊断">
                  完成诊断
                </div>
                <div class="s3-flow-conn"><div class="s3-flow-dot-anim"></div></div>
                <div class="s3-flow-pill s3-flow-btn"
                  :class="hasDiagnosis ? '' : 's3-flow-locked'"
                  @click="onAnalysisClick"
                  :title="hasDiagnosis ? '查看诊断分析结果' : '需先完成诊断'">
                  分析漏洞
                </div>
                <div class="s3-flow-conn"></div>
                <div class="s3-flow-pill s3-flow-btn s3-flow-current" @click="scrollToChallenge" title="当前即为推送题目阶段">
                  推送题目
                </div>
              </div>
            </div>
          </div>

          <!-- ── Cognitive Scanner (图三 style) ── -->
          <div class="s3-glass-card s3-scanner-card">
            <div class="s3-card-head">
              <div class="s3-card-title-row">
                <span class="s3-brain-icon">🧠</span>
                <span class="s3-card-title">认知漏洞扫描器</span>
              </div>
              <div class="s3-scanner-status-badge">
                <span class="s3-status-dot"></span>
                <span>扫描中...</span>
              </div>
            </div>

            <!-- Status banner -->
            <div class="s3-scan-banner" :class="wrongCount > 0 ? 's3-scan-warn' : 's3-scan-ok'">
              <span class="s3-scan-banner-icon">{{ wrongCount > 0 ? '⚠️' : '✅' }}</span>
              <span>{{ wrongCount > 0 ? `检测到 ${wrongCount} 个潜在认知漏洞` : '当前未发现认知漏洞，继续挑战！' }}</span>
            </div>

            <!-- Vulnerability items (v-for driven, 可展开) -->
            <div class="s3-vuln-list">
              <div v-for="v in displayedVulns" :key="v.name" class="s3-vuln-card">
                <div class="s3-vc-top">
                  <span class="s3-vc-name">{{ v.name }}</span>
                  <span class="s3-vc-sev" :class="v.sevClass">{{ v.severity }}</span>
                </div>
                <div class="s3-vc-bar-wrap">
                  <div class="s3-vc-bar"><div class="s3-vc-fill" :style="{ width: v.pct+'%', background: v.fill }"></div></div>
                  <span class="s3-vc-pct">{{ v.pct }}%</span>
                </div>
                <div class="s3-vc-detail">错误模式：{{ v.detail }}</div>
              </div>
            </div>
            <div class="s3-view-all-link" @click="showAllVulns = !showAllVulns">
              {{ showAllVulns ? '收起漏洞列表 ↑' : `查看全部漏洞 (${vulnTotal}) →` }}
            </div>
          </div>
        </div>

        <!-- ── Col 2: Challenge Section ── -->
        <div class="s3-glass-card s3-challenge-card-wrap">
          <!-- Header with filter tabs (图二 style) -->
          <div class="s3-challenge-header">
            <div class="s3-card-title-row">
              <div class="s3-card-dot s3-dot-blue"></div>
              <span class="s3-card-title">误解挑战题库</span>
              <span class="s3-card-badge s3-badge-blue">AI 推荐中</span>
            </div>
          </div>
          <!-- Filter tabs (图二 style) -->
          <div class="s3-filter-tabs">
            <button v-for="opt in topicOptions" :key="opt"
              class="s3-filter-tab" :class="{ 's3-tab-active': topicFilter === opt }"
              @click="topicFilter = opt">
              {{ opt }} ({{ topicCount(opt) }})
            </button>
          </div>

          <!-- Progress bar -->
          <div class="s3-prog-row">
            <div class="s3-prog-bar"><div class="s3-prog-fill" :style="{ width: progressPercent + '%' }"></div></div>
            <span class="s3-prog-text">{{ currentIndex }} / {{ totalRounds }}</span>
          </div>

          <!-- 对话自适应检验 data streamer (图五 style, light) -->
          <div class="s3-panel-header-bar">
            <div class="s3-phb-left">
              <span class="s3-phb-dot s3-phb-blue"></span>
              <span class="s3-phb-title">对话动自适应检验</span>
              <span class="s3-phb-badge">AI 根据诊断结果生成</span>
            </div>
          </div>
          <!-- Data streamer row -->
          <div class="s3-data-streamer">
            <span>第 {{ currentIndex + 1 }}/{{ totalRounds }} 轮</span>
            <span class="s3-ds-sep">·</span>
            <span>{{ isFinished ? 'COMPLETED' : (currentRound?.topic ?? 'TCP') }}</span>
            <span class="s3-ds-sep">·</span>
            <span>三次握手</span>
            <span class="s3-ds-sep">·</span>
            <span>状态机</span>
            <span class="s3-ds-sep">·</span>
            <span>TCP</span>
            <span class="s3-ds-sep">·</span>
            <span>ACK</span>
          </div>

          <div v-if="!isFinished">
            <!-- Challenger label (图五 style) -->
            <div class="s3-challenger-label">
              <span class="s3-phb-dot s3-phb-orange"></span>
              <span class="s3-challenger-title">Challenger 说明检验</span>
            </div>
            <div class="s3-challenger-sub">针对前期元认知历史成风，检验理解融合性</div>
            <!-- Round tags -->
            <div class="s3-round-tags">
              <span class="s3-rtag">第 {{ currentIndex + 1 }}/{{ totalRounds }} 轮</span>
              <span class="s3-rtag">{{ currentRound?.topic ?? 'TCP' }}</span>
              <span class="s3-rtag">三次握手</span>
            </div>

            <!-- ── Scan-line question panel (图四 style) ── -->
            <div class="s3-question-holo">
              <div class="s3-scan-line-anim" :style="{ top: scanLine + '%' }"></div>
              <div class="s3-question-text">{{ currentRound.statement }}</div>
            </div>

            <!-- Judge area -->
            <div v-if="!showResult" class="s3-judgment">
              <p class="s3-judge-q">这个观点是否正确？</p>
              <div class="s3-judge-btns">
                <button class="s3-jbtn s3-jbtn-ok" :class="{ 's3-jbtn-sel-ok': userJudgment === 'correct' }" @click="judge(true)">
                  <span>✓</span> 正确
                </button>
                <button class="s3-jbtn s3-jbtn-err" :class="{ 's3-jbtn-sel-err': userJudgment === 'incorrect' }" @click="judge(false)">
                  <span>✕</span> 错误
                </button>
              </div>
              <div v-if="userJudgment" class="s3-mini-flow">
                <span class="s3-mf-step s3-mf-active">你的选择</span>
                <span class="s3-mf-a">→</span><span class="s3-mf-step">AI 分析</span>
                <span class="s3-mf-a">→</span><span class="s3-mf-step">知识定位</span>
                <span class="s3-mf-a">→</span><span class="s3-mf-step">纠正建议</span>
              </div>
              <button v-if="userJudgment" class="s3-submit-btn" @click="submitAnswer">
                <span class="s3-submit-shine"></span>提交分析 →
              </button>
            </div>

            <!-- Result -->
            <div v-else class="s3-result">
              <div class="s3-result-banner" :class="history[history.length-1]?.correct ? 's3-rb-ok' : 's3-rb-err'">
                <span class="s3-rb-emoji">{{ history[history.length-1]?.correct ? '🎉' : '💡' }}</span>
                <div>
                  <div class="s3-rb-title">{{ history[history.length-1]?.correct ? '判断正确！' : '判断有误' }}</div>
                  <div v-if="!history[history.length-1]?.correct" class="s3-rb-sub">正确答案：{{ currentRound.isCorrect ? '正确' : '错误' }}</div>
                </div>
              </div>
              <div class="s3-truth-stack">
                <div class="s3-ts-item s3-ts-warn">
                  <span class="s3-ts-icon">⚠️</span>
                  <div><div class="s3-ts-label">常见误解</div><p>{{ currentRound.misconception }}</p></div>
                </div>
                <div class="s3-ts-item s3-ts-ok">
                  <span class="s3-ts-icon">✅</span>
                  <div><div class="s3-ts-label">事实真相</div><p>{{ currentRound.truth }}</p></div>
                </div>
                <div class="s3-ts-item s3-ts-blue">
                  <span class="s3-ts-icon">📖</span>
                  <div><div class="s3-ts-label">深度解析</div><p>{{ currentRound.explanation }}</p></div>
                </div>
              </div>
              <button class="s3-next-btn" @click="nextRound">{{ currentIndex < totalRounds - 1 ? '下一题 →' : '查看总结 →' }}</button>
            </div>
          </div>

          <!-- Other rounds list (filtered) -->
          <div class="s3-rounds-list">
            <div v-for="r in filteredRounds.filter(r => r.id !== (currentRound?.id ?? -1))" :key="r.id"
              class="s3-round-row" :class="{
                's3-rr-ok': getHistoryItem(r.id)?.correct === true,
                's3-rr-err': getHistoryItem(r.id)?.correct === false
              }">
              <div class="s3-rr-tag" :style="{ background: r.diffColor+'15', color: r.diffColor }">{{ r.topic }}</div>
              <span class="s3-rr-id">Challenge #{{ r.id }}</span>
              <span class="s3-rr-diff" :style="{ color: r.diffColor }">{{ r.difficulty }}</span>
              <span class="s3-rr-status">
                <span v-if="getHistoryItem(r.id)?.correct === true" class="s3-status-ok">✓ 正确</span>
                <span v-else-if="getHistoryItem(r.id)?.correct === false" class="s3-status-err">✗ 错误</span>
                <span v-else class="s3-status-pending">未开始</span>
              </span>
            </div>
          </div>

          <!-- Summary -->
          <div v-if="isFinished" class="s3-summary">
            <div class="s3-sum-trophy">🏆</div>
            <h3>挑战完成！</h3>
            <div class="s3-sum-score"><span class="s3-sum-n">{{ score }}</span><span class="s3-sum-of">/ {{ totalRounds }}</span></div>
            <p>正确率 {{ Math.round((score/totalRounds)*100) }}% · 最高连胜 {{ maxStreak }}</p>
            <div class="s3-histo">
              <span v-for="h in history" :key="h.round" class="s3-hdot" :class="h.correct ? 's3-hd-ok':'s3-hd-err'">{{ h.round }}</span>
            </div>
            <button class="s3-reset-btn" @click="resetAll">🔄 再来一轮</button>
          </div>
        </div>

        <!-- ── Col 3: Knowledge graph ── -->
        <div class="s3-glass-card s3-kg-card">
          <div class="s3-card-head">
            <div class="s3-card-title-row">
              <div class="s3-card-dot s3-dot-violet"></div>
              <span class="s3-card-title">知识图谱关联</span>
            </div>
          </div>
          <svg viewBox="-8 -10 236 200" class="s3-graph-svg">
            <defs>
              <radialGradient id="s3gc" cx="50%" cy="50%">
                <stop offset="0%" stop-color="#6366f1"/>
                <stop offset="100%" stop-color="#a855f7"/>
              </radialGradient>
              <filter id="s3glow">
                <feGaussianBlur stdDeviation="2.5" result="coloredBlur"/>
                <feMerge><feMergeNode in="coloredBlur"/><feMergeNode in="SourceGraphic"/></feMerge>
              </filter>
              <marker id="s3arr" markerWidth="6" markerHeight="6" refX="3" refY="3" orient="auto">
                <path d="M0,0 L6,3 L0,6 Z" fill="#a5b4fc"/>
              </marker>
            </defs>
            <circle cx="110" cy="87" r="28" fill="url(#s3gc)" filter="url(#s3glow)" opacity="0.9"/>
            <text x="110" y="84" text-anchor="middle" class="s3-gn-center">TCP</text>
            <text x="110" y="97" text-anchor="middle" class="s3-gn-sub">连接建立</text>
            <line x1="110" y1="59" x2="62" y2="22" stroke="#a5b4fc" stroke-width="1.5" marker-end="url(#s3arr)"/>
            <line x1="138" y1="63" x2="178" y2="22" stroke="#a5b4fc" stroke-width="1.5" marker-end="url(#s3arr)"/>
            <line x1="82" y1="87" x2="32" y2="87" stroke="#a5b4fc" stroke-width="1.5" marker-end="url(#s3arr)"/>
            <line x1="138" y1="87" x2="188" y2="87" stroke="#a5b4fc" stroke-width="1.5" marker-end="url(#s3arr)"/>
            <line x1="110" y1="115" x2="65" y2="155" stroke="#a5b4fc" stroke-width="1.5" marker-end="url(#s3arr)"/>
            <line x1="110" y1="115" x2="155" y2="155" stroke="#a5b4fc" stroke-width="1.5" marker-end="url(#s3arr)"/>
            <circle cx="46" cy="16" r="18" fill="#ede9fe" stroke="#7c3aed" stroke-width="1.5"/>
            <text x="46" y="12" text-anchor="middle" class="s3-gn-sat">三次</text><text x="46" y="24" text-anchor="middle" class="s3-gn-sat">握手</text>
            <circle cx="194" cy="16" r="18" fill="#ede9fe" stroke="#7c3aed" stroke-width="1.5"/>
            <text x="194" y="12" text-anchor="middle" class="s3-gn-sat">SYN/</text><text x="194" y="24" text-anchor="middle" class="s3-gn-sat">ACK</text>
            <circle cx="16" cy="87" r="18" fill="#fef3c7" stroke="#f59e0b" stroke-width="1.5"/>
            <text x="16" y="83" text-anchor="middle" class="s3-gn-sat">状态</text><text x="16" y="95" text-anchor="middle" class="s3-gn-sat">机</text>
            <circle cx="204" cy="87" r="18" fill="#ecfdf5" stroke="#10b981" stroke-width="1.5"/>
            <text x="204" y="83" text-anchor="middle" class="s3-gn-sat">超时</text><text x="204" y="95" text-anchor="middle" class="s3-gn-sat">重传</text>
            <circle cx="49" cy="162" r="18" fill="#fef2f2" stroke="#ef4444" stroke-width="1.5"/>
            <text x="49" y="158" text-anchor="middle" class="s3-gn-sat">流量</text><text x="49" y="170" text-anchor="middle" class="s3-gn-sat">控制</text>
            <circle cx="171" cy="162" r="18" fill="#f0f9ff" stroke="#0ea5e9" stroke-width="1.5"/>
            <text x="171" y="158" text-anchor="middle" class="s3-gn-sat">拥塞</text><text x="171" y="170" text-anchor="middle" class="s3-gn-sat">控制</text>
          </svg>
          <div class="s3-kg-error">当前关联错误：TCP 状态转换理解不足</div>
          <div class="s3-kg-advice">建议复习：状态机迁移规则、状态转换条件</div>
          <button class="s3-kg-btn" @click="goToPath">查看学习路径 →</button>
        </div>

      </div><!-- end s3-main-grid -->

      <!-- ═══ AI 反馈预览 — 一字排开 (图一 style, full width) ═══ -->
      <div class="s3-glass-card s3-pipeline-card">
        <div class="s3-pipeline-head">
          <div class="s3-card-title-row">
            <div class="s3-card-dot s3-dot-green"></div>
            <span class="s3-card-title">AI 反馈预览</span>
            <span class="s3-pl-sub">提交后触发完整分析链路</span>
          </div>
          <span class="s3-boost-tag">📈 能力提升预测 <strong>+18%</strong></span>
        </div>
        <!-- 一字排开 pipeline (图一 style) -->
        <div class="s3-pipeline-row">
          <div class="s3-pipe-step">
            <div class="s3-pipe-icon">🎯</div>
            <div class="s3-pipe-lbl">你的选择</div>
            <div class="s3-pipe-desc">{{ userJudgment ? (userJudgment === 'correct' ? '判断：正确' : '判断：错误') : '待选择' }}</div>
          </div>
          <div class="s3-pipe-arrow">→</div>
          <div class="s3-pipe-step">
            <div class="s3-pipe-icon">🤖</div>
            <div class="s3-pipe-lbl">AI 分析</div>
            <div class="s3-pipe-desc">定位误解原因</div>
          </div>
          <div class="s3-pipe-arrow">→</div>
          <div class="s3-pipe-step">
            <div class="s3-pipe-icon">🗺️</div>
            <div class="s3-pipe-lbl">知识定位</div>
            <div class="s3-pipe-desc">映射到知识图谱</div>
          </div>
          <div class="s3-pipe-arrow">→</div>
          <div class="s3-pipe-step">
            <div class="s3-pipe-icon">✨</div>
            <div class="s3-pipe-lbl">纠正建议</div>
            <div class="s3-pipe-desc">生成学习建议</div>
          </div>
          <div class="s3-pipe-arrow">→</div>
          <div class="s3-pipe-step">
            <div class="s3-pipe-icon">👤</div>
            <div class="s3-pipe-lbl">画像更新</div>
            <div class="s3-pipe-desc">强化认知模型</div>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<style scoped>
/* === Base === */
.s3-page { display: flex; flex-direction: column; gap: 0; min-height: 100vh; background: #eef2ff; }

/* === Particles === */
.s3-particles { position: fixed; inset: 0; pointer-events: none; z-index: 0; overflow: hidden; }
.s3-particle {
  position: absolute; width: 3px; height: 3px; border-radius: 50%;
  background: rgba(99,102,241,0.25); bottom: -10px;
  animation: s3-float linear infinite;
}
@keyframes s3-float { 0%{transform:translateY(0);opacity:0} 10%{opacity:1} 90%{opacity:0.5} 100%{transform:translateY(-100vh);opacity:0} }

/* === Ticker Bar === */
.s3-ticker-bar {
  position: relative; z-index: 10;
  display: flex; align-items: center; gap: 12px;
  background: linear-gradient(135deg, #0f0a30 0%, #1a1060 100%);
  padding: 8px 20px; overflow: hidden;
  border-bottom: 1px solid rgba(99,102,241,0.3);
}
.s3-ticker-chip { font-size: 10px; font-weight: 800; color: rgba(167,139,250,0.9); font-family: monospace; letter-spacing: 2px; flex-shrink: 0; background: rgba(99,102,241,0.2); padding: 3px 10px; border-radius: 6px; border: 1px solid rgba(99,102,241,0.3); }
.s3-ticker-track { flex: 1; overflow: hidden; }
.s3-ticker-inner { font-size: 11px; color: rgba(199,210,254,0.5); font-family: monospace; white-space: nowrap; letter-spacing: 1.5px; animation: s3-ticker-scroll 22s linear infinite; }
@keyframes s3-ticker-scroll { 0%{transform:translateX(0)} 100%{transform:translateX(-50%)} }
.s3-ticker-leds { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
.s3-t-led { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
.s3-t-green { background: #00ff88; box-shadow: 0 0 7px #00ff88; animation: s3-blink 2s infinite; }
.s3-t-purple { background: #bf00ff; box-shadow: 0 0 7px #bf00ff; animation: s3-blink 2.5s infinite; }
.s3-t-red { background: #ff4466; box-shadow: 0 0 7px #ff4466; animation: s3-blink 1.8s infinite; }
.s3-ticker-online { font-size: 10px; color: rgba(255,255,255,0.35); font-family: monospace; letter-spacing: 1px; }
@keyframes s3-blink { 0%,100%{opacity:1} 50%{opacity:0.3} }

/* === HERO === */
.s3-hero {
  background: linear-gradient(135deg, #0f0a30 0%, #1a1060 40%, #2d1b8c 70%, #1e3a8a 100%);
  padding: 26px 28px; position: relative; z-index: 1; overflow: hidden;
}
.s3-hero::after { content:''; position:absolute; inset:0; pointer-events:none; background:radial-gradient(ellipse at 80% 50%, rgba(168,85,247,0.12) 0%, transparent 60%); }
.s3-hero-inner { display: flex; align-items: center; gap: 20px; flex-wrap: wrap; position: relative; z-index: 1; }
.s3-hero-left { display: flex; align-items: center; gap: 18px; flex: 1; min-width: 260px; }
.s3-hero-orb { width: 60px; height: 60px; position: relative; flex-shrink: 0; display: flex; align-items: center; justify-content: center; }
.s3-orb-icon { font-size: 26px; position: relative; z-index: 1; }
.s3-orb-ring { position: absolute; inset: 0; border-radius: 50%; border: 2px solid rgba(168,85,247,0.6); box-shadow: 0 0 20px rgba(168,85,247,0.4), inset 0 0 20px rgba(99,102,241,0.2); background: rgba(99,102,241,0.1); animation: s3-ring-pulse 3s ease-in-out infinite; }
@keyframes s3-ring-pulse { 0%,100%{box-shadow:0 0 20px rgba(168,85,247,0.4)} 50%{box-shadow:0 0 32px rgba(168,85,247,0.7)} }
.s3-hero-info { color: white; }
.s3-hero-sup { display: flex; align-items: center; gap: 10px; margin-bottom: 6px; }
.s3-lv-badge { background: rgba(168,85,247,0.3); border: 1px solid rgba(168,85,247,0.5); color: #d8b4fe; border-radius: 20px; padding: 2px 10px; font-size: 12px; font-weight: 600; }
.s3-time-badge { background: rgba(255,255,255,0.1); color: rgba(255,255,255,0.6); border-radius: 20px; padding: 2px 10px; font-size: 12px; }
.s3-hero-title { margin: 0 0 3px; font-size: 24px; font-weight: 800; }
.s3-hero-sub { margin: 0 0 8px; font-size: 13px; color: rgba(255,255,255,0.6); line-height: 1.5; }
.s3-hero-theme-row { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.s3-theme-label { font-size: 12px; color: rgba(255,255,255,0.45); }
.s3-theme-value { font-size: 13px; font-weight: 700; color: #a5b4fc; }
.s3-theme-sep { color: rgba(255,255,255,0.25); }
.s3-theme-tags { background: rgba(255,255,255,0.08); border-radius: 8px; padding: 2px 8px; font-size: 11px; color: rgba(255,255,255,0.4); }

.s3-hero-progress { flex-shrink: 0; text-align: center; }
.s3-pg-label { font-size: 11px; color: rgba(255,255,255,0.45); margin: 0 0 4px; }
.s3-pg-ring-wrap { position: relative; width: 86px; height: 86px; }
.s3-pg-svg { width: 100%; height: 100%; transform: rotate(-90deg); }
.s3-pg-bg { fill: none; stroke: rgba(255,255,255,0.1); stroke-width: 7; }
.s3-pg-fill { fill: none; stroke: #a78bfa; stroke-width: 7; stroke-linecap: round; transition: stroke-dasharray 0.5s ease; }
.s3-pg-center { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; color: white; }
.s3-pg-main { font-size: 22px; font-weight: 800; line-height: 1; }
.s3-pg-sub { font-size: 12px; color: rgba(255,255,255,0.55); }
.s3-pg-pct { font-size: 10px; color: rgba(255,255,255,0.4); }

.s3-hero-stats { display: flex; gap: 8px; flex-shrink: 0; flex-wrap: wrap; }
.s3-stat-card { background: rgba(255,255,255,0.08); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.14); border-radius: 14px; padding: 10px 14px; text-align: center; color: white; min-width: 68px; transition: all 0.2s; }
.s3-stat-card:hover { background: rgba(255,255,255,0.14); transform: translateY(-2px); }
.s3-stat-icon { font-size: 18px; margin-bottom: 3px; }
.s3-stat-val { font-size: 17px; font-weight: 800; display: block; }
.s3-stat-lbl { font-size: 10px; color: rgba(255,255,255,0.55); display: block; }

/* === Body === */
.s3-body { padding: 20px; position: relative; z-index: 1; display: flex; flex-direction: column; gap: 16px; }
.s3-main-grid { display: grid; grid-template-columns: 290px 1fr 300px; gap: 20px; align-items: start; }
@media (max-width: 1200px) { .s3-main-grid { grid-template-columns: 1fr 1fr; } }
@media (max-width: 768px) { .s3-main-grid { grid-template-columns: 1fr; } }

/* === Glass Card base === */
.s3-glass-card {
  background: rgba(255,255,255,0.88);
  backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255,255,255,0.95);
  border-radius: 18px; padding: 20px 22px;
  box-shadow: 0 4px 24px rgba(79,70,229,0.07), 0 1px 0 rgba(255,255,255,0.8) inset;
  display: flex; flex-direction: column; gap: 14px;
}

/* Card common */
.s3-card-head { display: flex; align-items: center; justify-content: space-between; }
.s3-card-title-row { display: flex; align-items: center; gap: 8px; }
.s3-card-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.s3-dot-purple { background: #a855f7; box-shadow: 0 0 6px rgba(168,85,247,0.5); }
.s3-dot-blue { background: #3b82f6; box-shadow: 0 0 6px rgba(59,130,246,0.5); }
.s3-dot-green { background: #10b981; box-shadow: 0 0 6px rgba(16,185,129,0.5); }
.s3-dot-orange { background: #f59e0b; box-shadow: 0 0 6px rgba(245,158,11,0.5); }
.s3-dot-violet { background: #6366f1; box-shadow: 0 0 6px rgba(99,102,241,0.5); }
.s3-card-title { font-size: 14px; font-weight: 700; color: #0f172a; }
.s3-card-badge { font-size: 10px; background: #ede9fe; color: #7c3aed; border-radius: 8px; padding: 2px 8px; font-weight: 600; }
.s3-badge-blue { background: #dbeafe; color: #1d4ed8; }

/* === Left column === */
.s3-left-col { display: flex; flex-direction: column; gap: 14px; }

/* AI Tutor */
.s3-quiz-wrap :deep(.challenger-quiz-card) { border: none; padding: 0; background: transparent; margin: 0; }
.s3-chat-bubble-wrap { display: flex; gap: 10px; }
.s3-chat-avatar { font-size: 26px; flex-shrink: 0; }
.s3-chat-bubble { background: #f1f5f9; border-radius: 0 12px 12px 12px; padding: 12px 14px; font-size: 13px; color: #334155; line-height: 1.6; border: 1px solid #e2e8f0; }
.s3-chat-bubble p { margin: 0; }
.s3-ai-flow-steps { display: flex; align-items: center; gap: 4px; }
.s3-flow-pill { padding: 4px 10px; border-radius: 12px; border: 1px solid #e2e8f0; background: #f8fafc; font-size: 11px; color: #64748b; flex-shrink: 0; }
.s3-flow-active { background: #ede9fe; border-color: #c4b5fd; color: #6d28d9; font-weight: 600; }
.s3-flow-conn { flex: 1; height: 2px; background: linear-gradient(90deg, #c4b5fd, #e2e8f0); position: relative; overflow: visible; min-width: 8px; }
.s3-flow-dot-anim { position: absolute; top: 50%; transform: translateY(-50%); width: 5px; height: 5px; border-radius: 50%; background: #a78bfa; animation: s3-flow-dot 1.5s linear infinite; }
@keyframes s3-flow-dot { 0%{left:-3px;opacity:0} 20%{opacity:1} 80%{opacity:1} 100%{left:calc(100% + 3px);opacity:0} }

/* ── Cognitive Scanner (图三 style) ── */
.s3-scanner-card { }
.s3-brain-icon { font-size: 18px; }
.s3-scanner-status-badge { display: flex; align-items: center; gap: 6px; font-size: 12px; color: #7c3aed; font-weight: 600; }
.s3-status-dot { width: 8px; height: 8px; border-radius: 50%; background: #7c3aed; animation: s3-blink 1.5s infinite; }
.s3-scan-banner { display: flex; align-items: center; gap: 8px; padding: 10px 14px; border-radius: 10px; font-size: 13px; font-weight: 500; }
.s3-scan-ok { background: #ecfdf5; border: 1px solid #a7f3d0; color: #065f46; }
.s3-scan-warn { background: #fff7ed; border: 1px solid #fed7aa; color: #92400e; }
.s3-scan-banner-icon { font-size: 16px; }
.s3-vuln-list { display: flex; flex-direction: column; gap: 10px; }
.s3-vuln-card { background: white; border: 1px solid #f1f5f9; border-radius: 12px; padding: 12px 14px; box-shadow: 0 1px 4px rgba(0,0,0,0.04); }
.s3-vc-top { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
.s3-vc-name { font-size: 13px; font-weight: 600; color: #1e293b; }
.s3-vc-sev { font-size: 11px; font-weight: 700; padding: 2px 9px; border-radius: 8px; }
.s3-sev-medium { background: #fef3c7; color: #92400e; }
.s3-sev-low { background: #d1fae5; color: #065f46; }
.s3-vc-bar-wrap { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.s3-vc-bar { flex: 1; height: 6px; background: #f1f5f9; border-radius: 3px; overflow: hidden; }
.s3-vc-fill { height: 100%; border-radius: 3px; transition: width 0.5s; }
.s3-vc-pct { font-size: 11px; color: #64748b; font-weight: 600; flex-shrink: 0; }
.s3-vc-detail { font-size: 11px; color: #94a3b8; }
.s3-view-all-link { text-align: center; font-size: 13px; color: #6366f1; font-weight: 600; cursor: pointer; padding: 4px 0; }
.s3-view-all-link:hover { text-decoration: underline; }

/* === Challenge column === */
.s3-challenge-card-wrap { min-width: 0; }
.s3-challenge-header { }

/* Filter tabs (图二 style) */
.s3-filter-tabs { display: flex; gap: 6px; flex-wrap: wrap; padding-bottom: 2px; border-bottom: 1px solid #eef2ff; }
.s3-filter-tab { padding: 5px 12px; border-radius: 20px; border: 1px solid #e2e8f0; background: #f8fafc; font-size: 12px; color: #64748b; cursor: pointer; transition: all 0.2s; white-space: nowrap; }
.s3-filter-tab:hover { border-color: #7c3aed; color: #7c3aed; background: #faf5ff; }
.s3-tab-active { background: linear-gradient(135deg, #6366f1, #7c3aed) !important; color: white !important; border-color: transparent !important; box-shadow: 0 3px 10px rgba(99,102,241,0.3); }

/* Progress bar */
.s3-prog-row { display: flex; align-items: center; gap: 10px; margin-top: 2px; }
.s3-prog-bar { flex: 1; height: 5px; background: #e8edf5; border-radius: 3px; overflow: hidden; }
.s3-prog-fill { height: 100%; background: linear-gradient(90deg, #6366f1, #a855f7); border-radius: 3px; transition: width 0.4s; }
.s3-prog-text { font-size: 12px; color: #64748b; font-weight: 500; flex-shrink: 0; }

/* Panel header bar (图五 style) */
.s3-panel-header-bar { display: flex; align-items: center; justify-content: space-between; padding-top: 6px; border-top: 1px solid #eef2ff; }
.s3-phb-left { display: flex; align-items: center; gap: 8px; }
.s3-phb-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.s3-phb-blue { background: #3b82f6; box-shadow: 0 0 5px rgba(59,130,246,0.5); }
.s3-phb-orange { background: #f59e0b; box-shadow: 0 0 5px rgba(245,158,11,0.5); }
.s3-phb-title { font-size: 13px; font-weight: 700; color: #1e293b; }
.s3-phb-badge { font-size: 10px; background: #fef9c3; color: #a16207; border-radius: 8px; padding: 2px 8px; font-weight: 600; }

/* Data streamer (图五 style, light) */
.s3-data-streamer {
  display: flex; align-items: center; gap: 8px; flex-wrap: nowrap; overflow: hidden;
  background: #f0f4ff; border: 1px solid #c7d2fe;
  border-radius: 8px; padding: 8px 14px;
  font-size: 11px; color: #6366f1; font-weight: 600; letter-spacing: 0.3px;
  min-width: 0;
}
.s3-ds-sep { color: #a5b4fc; }

/* Challenger label (图五 style) */
.s3-challenger-label { display: flex; align-items: center; gap: 8px; margin-top: 2px; }
.s3-challenger-title { font-size: 13px; font-weight: 700; color: #1e293b; }
.s3-challenger-sub { font-size: 11px; color: #94a3b8; margin-top: 2px; line-height: 1.4; }
.s3-round-tags { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 2px; }
.s3-rtag { background: #f1f5f9; border: 1px solid #e2e8f0; color: #475569; font-size: 11px; padding: 3px 10px; border-radius: 8px; font-weight: 500; }

/* ── Scan-line question panel (图四 style) ── */
.s3-question-holo {
  position: relative; overflow: hidden;
  background: #0f1a3a;
  border-radius: 12px; padding: 22px 22px;
  border: 1px solid rgba(99,102,241,0.4);
  box-shadow: 0 4px 20px rgba(15,26,58,0.25), inset 0 0 40px rgba(99,102,241,0.05);
  margin-top: 4px;
}
.s3-scan-line-anim {
  position: absolute; left: 0; right: 0; height: 2px; pointer-events: none;
  background: linear-gradient(90deg, transparent 0%, rgba(99,102,241,0.6) 30%, rgba(167,139,250,0.8) 50%, rgba(99,102,241,0.6) 70%, transparent 100%);
  box-shadow: 0 0 8px rgba(99,102,241,0.5);
  transition: top 0.08s linear;
}
.s3-question-text {
  font-size: 14px; font-weight: 600; color: rgba(255,255,255,0.92); line-height: 1.75;
  font-family: 'Menlo', 'Consolas', 'Courier New', monospace;
  position: relative; z-index: 1; word-break: break-all;
  letter-spacing: 0.2px;
}

/* Judgment */
.s3-judgment { display: flex; flex-direction: column; align-items: center; gap: 14px; margin-top: 8px; }
.s3-judge-q { font-size: 14px; font-weight: 600; color: #1e293b; margin: 0; }
.s3-judge-btns { display: flex; gap: 12px; width: 100%; }
.s3-jbtn { flex: 1; padding: 11px; border-radius: 12px; border: 2px solid #e2e8f0; background: white; font-size: 14px; font-weight: 700; cursor: pointer; transition: all 0.2s; display: flex; align-items: center; justify-content: center; gap: 6px; color: #475569; }
.s3-jbtn:hover { transform: translateY(-1px); }
.s3-jbtn-ok:hover { border-color: #10b981; color: #059669; background: #f0fdf4; }
.s3-jbtn-err:hover { border-color: #ef4444; color: #dc2626; background: #fef2f2; }
.s3-jbtn-sel-ok { border-color: #10b981 !important; color: #059669 !important; background: #f0fdf4 !important; box-shadow: 0 0 0 3px rgba(16,185,129,0.15); }
.s3-jbtn-sel-err { border-color: #ef4444 !important; color: #dc2626 !important; background: #fef2f2 !important; box-shadow: 0 0 0 3px rgba(239,68,68,0.15); }
.s3-mini-flow { display: flex; align-items: center; gap: 6px; font-size: 11px; color: #94a3b8; flex-wrap: wrap; justify-content: center; }
.s3-mf-step { padding: 2px 8px; border-radius: 8px; background: #f1f5f9; }
.s3-mf-active { background: #ede9fe; color: #6d28d9; font-weight: 600; }
.s3-mf-a { color: #c4b5fd; }
.s3-submit-btn { position: relative; width: 100%; padding: 13px; background: linear-gradient(135deg, #4f46e5, #7c3aed); color: white; border: none; border-radius: 12px; font-size: 14px; font-weight: 700; cursor: pointer; overflow: hidden; box-shadow: 0 4px 16px rgba(79,70,229,0.35); transition: all 0.2s; }
.s3-submit-btn:hover { transform: translateY(-1px); box-shadow: 0 6px 24px rgba(79,70,229,0.5); }
.s3-submit-shine { position: absolute; inset: 0; background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.15) 50%, transparent 100%); animation: s3-shine 2.5s infinite; }
@keyframes s3-shine { 0%{transform:translateX(-100%)} 100%{transform:translateX(100%)} }

/* Result */
.s3-result { display: flex; flex-direction: column; gap: 10px; margin-top: 4px; }
.s3-result-banner { display: flex; align-items: center; gap: 12px; padding: 12px 16px; border-radius: 10px; }
.s3-rb-ok { background: #ecfdf5; border: 1px solid #a7f3d0; }
.s3-rb-err { background: #fff7ed; border: 1px solid #fed7aa; }
.s3-rb-emoji { font-size: 24px; }
.s3-rb-title { font-size: 14px; font-weight: 700; color: #0f172a; }
.s3-rb-sub { font-size: 12px; color: #64748b; }
.s3-truth-stack { display: flex; flex-direction: column; gap: 8px; }
.s3-ts-item { display: flex; align-items: flex-start; gap: 10px; padding: 10px 12px; border-radius: 10px; }
.s3-ts-icon { font-size: 15px; flex-shrink: 0; margin-top: 1px; }
.s3-ts-label { font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 3px; }
.s3-ts-item p { margin: 0; font-size: 12px; line-height: 1.6; color: #334155; }
.s3-ts-warn { background: #fff7ed; border: 1px solid #fed7aa; }
.s3-ts-warn .s3-ts-label { color: #92400e; }
.s3-ts-ok { background: #ecfdf5; border: 1px solid #a7f3d0; }
.s3-ts-ok .s3-ts-label { color: #065f46; }
.s3-ts-blue { background: #eff6ff; border: 1px solid #bfdbfe; }
.s3-ts-blue .s3-ts-label { color: #1d4ed8; }
.s3-next-btn { align-self: flex-end; padding: 9px 22px; background: linear-gradient(135deg, #4f46e5, #7c3aed); color: white; border: none; border-radius: 10px; font-size: 13px; font-weight: 700; cursor: pointer; transition: all 0.2s; }
.s3-next-btn:hover { box-shadow: 0 4px 12px rgba(79,70,229,0.35); transform: translateY(-1px); }

/* Rounds list */
.s3-rounds-list { display: flex; flex-direction: column; gap: 7px; margin-top: 4px; padding-top: 10px; border-top: 1px solid #eef2ff; }
.s3-round-row { display: flex; align-items: center; gap: 10px; padding: 10px 14px; border-radius: 10px; border: 1px solid #f1f5f9; background: #f8fafc; font-size: 12px; transition: all 0.15s; }
.s3-round-row:hover { border-color: #e0e7ff; background: white; }
.s3-rr-ok { border-color: #a7f3d0 !important; background: #f0fdf4 !important; }
.s3-rr-err { border-color: #fecaca !important; background: #fef2f2 !important; }
.s3-rr-tag { padding: 2px 8px; border-radius: 8px; font-weight: 600; font-size: 11px; flex-shrink: 0; }
.s3-rr-id { flex: 1; color: #64748b; }
.s3-rr-diff { font-weight: 600; font-size: 11px; }
.s3-status-ok { background: #dcfce7; color: #15803d; padding: 2px 7px; border-radius: 7px; font-weight: 600; }
.s3-status-err { background: #fee2e2; color: #991b1b; padding: 2px 7px; border-radius: 7px; font-weight: 600; }
.s3-status-pending { background: #f1f5f9; color: #64748b; padding: 2px 7px; border-radius: 7px; font-weight: 600; }

/* Summary */
.s3-summary { text-align: center; padding: 16px 0; }
.s3-sum-trophy { font-size: 40px; }
.s3-summary h3 { margin: 6px 0; font-size: 18px; color: #0f172a; }
.s3-sum-score { display: flex; align-items: baseline; justify-content: center; gap: 4px; }
.s3-sum-n { font-size: 40px; font-weight: 800; color: #4f46e5; }
.s3-sum-of { font-size: 20px; color: #94a3b8; }
.s3-summary p { font-size: 13px; color: #64748b; }
.s3-histo { display: flex; gap: 6px; justify-content: center; margin: 8px 0; }
.s3-hdot { width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; }
.s3-hd-ok { background: #d1fae5; color: #065f46; }
.s3-hd-err { background: #fee2e2; color: #991b1b; }
.s3-reset-btn { padding: 10px 28px; background: linear-gradient(135deg, #4f46e5, #7c3aed); color: white; border: none; border-radius: 12px; font-size: 14px; font-weight: 700; cursor: pointer; box-shadow: 0 4px 12px rgba(79,70,229,0.3); }

/* === Knowledge graph === */
.s3-kg-card { overflow: visible; }
.s3-graph-svg { width: 100%; height: auto; display: block; overflow: visible; }
.s3-gn-center { font-size: 11px; font-weight: 800; fill: white; font-family: sans-serif; }
.s3-gn-sub { font-size: 7px; fill: rgba(255,255,255,0.7); font-family: sans-serif; }
.s3-gn-sat { font-size: 7px; fill: #475569; font-family: sans-serif; }
.s3-kg-error { font-size: 12px; color: #dc2626; font-weight: 500; line-height: 1.5; }
.s3-kg-advice { font-size: 11px; color: #64748b; line-height: 1.5; margin-top: 2px; }
.s3-kg-btn { padding: 8px 16px; background: transparent; border: 1.5px solid #4f46e5; color: #4f46e5; border-radius: 10px; font-size: 12px; font-weight: 700; cursor: pointer; transition: all 0.2s; width: 100%; }
.s3-kg-btn:hover { background: #4f46e5; color: white; }

/* === Pipeline card (图一: 一字排开) === */
.s3-pipeline-card { margin-top: 0; }
.s3-pipeline-head { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px; margin-bottom: 4px; }
.s3-pl-sub { font-size: 12px; color: #94a3b8; margin-left: 4px; }
.s3-boost-tag { font-size: 12px; color: #10b981; font-weight: 600; }
.s3-pipeline-row { display: flex; align-items: center; justify-content: space-between; gap: 0; margin-top: 8px; padding: 4px 0; }
.s3-pipe-step { display: flex; flex-direction: column; align-items: center; gap: 8px; flex: 1; min-width: 80px; max-width: 160px; }
.s3-pipe-icon { width: 52px; height: 52px; border-radius: 16px; background: linear-gradient(135deg, #ede9fe, #ddd6fe); display: flex; align-items: center; justify-content: center; font-size: 24px; box-shadow: 0 3px 10px rgba(99,102,241,0.18); transition: all 0.2s; }
.s3-pipe-step:hover .s3-pipe-icon { transform: translateY(-3px); box-shadow: 0 6px 18px rgba(99,102,241,0.3); background: linear-gradient(135deg, #6366f1, #7c3aed); }
.s3-pipe-lbl { font-size: 13px; font-weight: 700; color: #1e293b; text-align: center; margin-top: 2px; }
.s3-pipe-desc { font-size: 11px; color: #94a3b8; text-align: center; line-height: 1.4; margin-top: 2px; }
.s3-pipe-arrow { font-size: 20px; color: #c4b5fd; flex-shrink: 0; padding: 0 4px; margin-bottom: 28px; }
</style>
