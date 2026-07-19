<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { RadarChart, LineChart, BarChart } from 'echarts/charts'
import { GridComponent, LegendComponent, TooltipComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import AgentSelector from '@/components/AgentSelector.vue'
import VirtualTeacherPanel from '@/components/VirtualTeacherPanel.vue'
import ChatPanel from '@/components/ChatPanel.vue'
import KGPanel from '@/components/KGPanel.vue'
import AgentLogPanel from '@/components/AgentLogPanel.vue'
import PathTimeline from '@/components/path/PathTimeline.vue'
import DiagnosisPanel from '@/components/DiagnosisPanel.vue'
import { useChatStore } from '@/stores/chatStore'
import { useUserStore } from '@/stores/userStore'
import { usePathStore } from '@/stores/pathStore'

use([CanvasRenderer, RadarChart, LineChart, BarChart, GridComponent, LegendComponent, TooltipComponent])

const router = useRouter()
const chatStore = useChatStore()
const userStore = useUserStore()
const pathStore = usePathStore()

const chatPanelRef = ref<InstanceType<typeof ChatPanel> | null>(null)
const currentPersona = ref('professor')
const showVirtualTeacher = ref(false)
const trendRange = ref('7d')
const rightTab = ref<'analysis' | 'diagnosis' | 'kg' | 'path' | 'logs'>('analysis')
const refreshing = ref(false)
const recSetIndex = ref(0)

const hasMessages = computed(() => (chatStore.currentSession?.messages?.length ?? 0) > 0)

const latestAssistantResponse = computed(() => {
  const session = chatStore.currentSession
  if (!session) return ''
  for (let i = session.messages.length - 1; i >= 0; i--) {
    if (session.messages[i].role === 'assistant' && !session.messages[i].isStreaming)
      return session.messages[i].content
  }
  return ''
})

const rfcQueries: Record<string, string> = {
  TCP: '请讲解 TCP 的三次握手与可靠传输机制（RFC 9293）',
  UDP: '请讲解 UDP 的特点与典型应用场景（RFC 768）',
  IPv4: '请讲解 IPv4 的分片与重组机制（RFC 791）',
  IPv6: '请讲解 IPv6 的新特性及与 IPv4 的对比（RFC 8200）',
  DNS: '请讲解 DNS 的递归解析流程（RFC 1034/1035）',
  HTTP: '请讲解 HTTP 的请求/响应语义（RFC 9110/9112）',
  TLS: '请讲解 TLS 1.3 的握手过程与安全改进（RFC 8446）',
  QUIC: '请讲解 QUIC 协议的核心创新点（RFC 9000）',
}

function quickAskRfc(proto: string) {
  const q = rfcQueries[proto]
  if (q) chatPanelRef.value?.setPrompt(q)
}
function setInput(text: string) {
  chatPanelRef.value?.setPrompt(text)
}
function handlePersonaChange(p: { key: string }) { currentPersona.value = p.key }

// 推荐学习多轮数据集
const recSets = [
  [
    { icon: '🌐', title: 'TCP 协议深度解析', tag: '进阶课程', duration: '45分钟', progress: 75, reason: '加深传输层协议理解', color: '#6366f1' },
    { icon: '🔧', title: '网络实战：搭建 DNS 服务器', tag: '实践项目', duration: '60分钟', progress: 25, reason: '实践 DNS 工作原理', color: '#38bdf8' },
    { icon: '📡', title: 'HTTP/2 协议新特性', tag: '新知识', duration: '30分钟', progress: 0, reason: '了解最新协议特性', color: '#2dd4bf' },
    { icon: '🛡', title: '网络安全基础', tag: '基础课程', duration: '40分钟', progress: 40, reason: '补充安全知识体系', color: '#f472b6' },
  ],
  [
    { icon: '🔗', title: 'TLS 握手深度解析', tag: '进阶课程', duration: '35分钟', progress: 0, reason: '理解加密传输机制', color: '#6366f1' },
    { icon: '⚡', title: 'QUIC 协议实战入门', tag: '新知识', duration: '50分钟', progress: 10, reason: '学习下一代传输协议', color: '#f59e0b' },
    { icon: '🗺', title: 'IPv6 网络配置实验', tag: '实践项目', duration: '45分钟', progress: 0, reason: '掌握 IPv6 部署技能', color: '#2dd4bf' },
    { icon: '📊', title: 'Wireshark 抓包分析', tag: '实践技能', duration: '60分钟', progress: 30, reason: '提升网络排障能力', color: '#38bdf8' },
  ],
  [
    { icon: '🧪', title: 'TCP 拥塞控制算法', tag: '算法分析', duration: '40分钟', progress: 0, reason: '弥补拥塞控制薄弱点', color: '#ef4444' },
    { icon: '🔍', title: 'DNS 递归查询实验', tag: '实验项目', duration: '30分钟', progress: 0, reason: '实践 DNS 解析流程', color: '#38bdf8' },
    { icon: '💻', title: 'Socket 编程入门', tag: '编程实践', duration: '55分钟', progress: 20, reason: '掌握网络编程基础', color: '#6366f1' },
    { icon: '📚', title: 'OSI 模型精讲', tag: '基础课程', duration: '25分钟', progress: 60, reason: '巩固网络分层理解', color: '#2dd4bf' },
  ],
]
const recommendations = computed(() => recSets[recSetIndex.value])
function refreshRecs() {
  if (refreshing.value) return
  refreshing.value = true
  setTimeout(() => {
    recSetIndex.value = (recSetIndex.value + 1) % recSets.length
    refreshing.value = false
  }, 260)
}

onMounted(() => {
  if (!chatStore.currentSession) chatStore.createSession('新会话')
  userStore.fetchProfile()
  pathStore.fetchPath(userStore.userId)
  if (chatStore.isStreaming) chatStore.setStreaming(false)
})

const heroActions = [
  { icon: '📖', label: '概念讲解', sub: '深入透出', prompt: '请用通俗易懂的方式讲解一个计算机网络核心概念，比如 TCP 三次握手或 DNS 解析流程' },
  { icon: '🧪', label: '实验演示', sub: '动手验证', prompt: '请演示 TCP 三次握手的完整过程，包括报文内容和状态变化' },
  { icon: '📋', label: '生成报告', sub: '总结分析', prompt: '请为我生成一份关于传输层协议（TCP/UDP）的学习总结报告，包括核心知识点和常见考题' },
  { icon: '🩺', label: '能力诊断', sub: '瓶颈评估', prompt: '请对我进行计算机网络知识诊断，检验我对 TCP、IP、HTTP 等协议的理解程度' },
]
const quickSuggestions = ['三次握手过程', 'HTTP 和 HTTPS 的区别', 'DNS 解析流程', '滑动窗口协议']

const agentMatrix = [
  { icon: '🎯', name: 'Orchestrator', role: '总调度官', desc: '协调多 Agent 协作', bg: 'linear-gradient(135deg,#6366f1,#818cf8)' },
  { icon: '👤', name: 'Profiler', role: '学习画像师', desc: '构建你的能力画像', bg: 'linear-gradient(135deg,#38bdf8,#7dd3fc)' },
  { icon: '🔍', name: 'Retriever', role: '知识检索员', desc: '精准检索知识来源', bg: 'linear-gradient(135deg,#2dd4bf,#5eead4)' },
  { icon: '🩺', name: 'Diagnosis', role: '诊断分析师', desc: '识别认知薄弱区', bg: 'linear-gradient(135deg,#f472b6,#f9a8d4)' },
  { icon: '🗺', name: 'Planner', role: '路径规划师', desc: '定制个性化路径', bg: 'linear-gradient(135deg,#fb923c,#fed7aa)' },
  { icon: '🔬', name: 'Simulator', role: '仿真实验员', desc: '提供实验环境', bg: 'linear-gradient(135deg,#a78bfa,#ddd6fe)' },
  { icon: '📚', name: 'Generator', role: '内容生成师', desc: '生成各类讲解', bg: 'linear-gradient(135deg,#34d399,#a7f3d0)' },
  { icon: '⚡', name: 'Challenger', role: '挑战激励师', desc: '设计挑战任务', bg: 'linear-gradient(135deg,#fbbf24,#fde68a)' },
]
const weakPoints = [
  { name: 'TCP 确认机制理解偏差', level: '高优先级', color: '#ef4444', bg: '#fef2f2' },
  { name: 'DNS 递归与迭代查询区别', level: '中优先级', color: '#f59e0b', bg: '#fffbeb' },
  { name: 'HTTP 状态码记忆不牢', level: '低优先级', color: '#10b981', bg: '#f0fdf4' },
]
const recentHistory = [
  { title: '学习 TCP 三次握手', time: '15 分钟前' },
  { title: '完成 DNS 实验', time: '1 小时前' },
  { title: '阅读 HTTP 协议规范', time: '2 小时前' },
  { title: '练习滑动窗口协议', time: '昨天' },
]
const skillBars = [
  { name: '网络基础', value: 85, color: '#6366f1' },
  { name: '应用层', value: 66, color: '#38bdf8' },
  { name: '传输协议', value: 72, color: '#2dd4bf' },
  { name: '网络协议', value: 65, color: '#f472b6' },
  { name: '数据链路层', value: 59, color: '#fb923c' },
]
const radarOption = computed(() => ({
  backgroundColor: 'transparent',
  radar: {
    indicator: [
      { name: '网络基础', max: 100 }, { name: '传输协议', max: 100 }, { name: '网络协议', max: 100 },
      { name: '数据链路', max: 100 }, { name: '应用层', max: 100 },
    ],
    axisName: { color: '#64748b', fontSize: 10 },
    splitArea: { areaStyle: { color: ['rgba(99,102,241,0.02)', 'rgba(99,102,241,0.05)'] } },
    splitLine: { lineStyle: { color: 'rgba(99,102,241,0.15)' } },
    axisLine: { lineStyle: { color: 'rgba(99,102,241,0.15)' } },
    radius: '70%',
  },
  series: [{ type: 'radar', data: [{ value: [85, 72, 65, 78, 66], lineStyle: { color: '#6366f1', width: 2 }, areaStyle: { color: 'rgba(99,102,241,0.18)' }, itemStyle: { color: '#6366f1' } }] }],
}))
const trendChartOption = computed(() => {
  const days = trendRange.value === '7d'
    ? ['07-14', '07-15', '07-16', '07-17', '07-18', '07-19', '07-20']
    : ['07-01', '07-05', '07-08', '07-11', '07-14', '07-17', '07-20']
  return {
    backgroundColor: 'transparent',
    grid: { top: 16, right: 16, bottom: 28, left: 36 },
    xAxis: { type: 'category', data: days, axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: '#94a3b8', fontSize: 10 } },
    yAxis: [
      { type: 'value', max: 10, splitLine: { lineStyle: { color: '#f1f5f9' } }, axisLabel: { color: '#94a3b8', fontSize: 10 } },
      { type: 'value', max: 100, splitLine: { show: false }, axisLabel: { color: '#94a3b8', fontSize: 10 } },
    ],
    series: [
      { type: 'bar', data: [3, 5, 2, 8, 4, 6, 7], itemStyle: { color: '#e0e7ff', borderRadius: [3, 3, 0, 0] }, barMaxWidth: 20 },
      { type: 'line', yAxisIndex: 1, data: [60, 65, 62, 72, 68, 75, 80], smooth: true, lineStyle: { color: '#6366f1', width: 2.5 }, areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(99,102,241,0.25)' }, { offset: 1, color: 'rgba(99,102,241,0.02)' }] } }, symbol: 'circle', symbolSize: 5, itemStyle: { color: '#6366f1', borderWidth: 2, borderColor: '#fff' } },
      { type: 'line', yAxisIndex: 1, data: [55, 58, 60, 65, 70, 72, 78], smooth: true, lineStyle: { color: '#2dd4bf', width: 2, type: 'dashed' }, symbol: 'none' },
    ],
    tooltip: { trigger: 'axis', backgroundColor: 'rgba(255,255,255,0.92)', borderColor: '#e0e7ff', borderWidth: 1, textStyle: { color: '#334155', fontSize: 12 } },
  }
})
const rightTabs = [
  { key: 'analysis', icon: '📊', label: '学习分析' },
  { key: 'diagnosis', icon: '🔍', label: '诊断结果' },
  { key: 'kg', icon: '🕸', label: '知识图谱' },
  { key: 'path', icon: '🗺', label: '学习路径' },
  { key: 'logs', icon: '📝', label: '更多工具' },
]
</script>

<template>
  <div class="s1-wrapper">
    <VirtualTeacherPanel v-model="showVirtualTeacher" :current-response="latestAssistantResponse" />
    <div class="s1-body">

      <!-- ═══ 主内容列 ═══ -->
      <div class="s1-main">

        <!-- 顶部问候栏 -->
        <div class="s1-topbar">
          <div class="topbar-greet">
            <span class="greet-emoji">🎓</span>
            <span class="greet-text">你好，未来网络工程师！</span>
          </div>
          <div class="topbar-center">
            <span class="ai-label">AI 助手：</span>
            <AgentSelector v-model="currentPersona" @change="handlePersonaChange" />
            <button class="vt-btn" :class="{ active: showVirtualTeacher }" @click="showVirtualTeacher = !showVirtualTeacher">
              🧑‍🏫 数字人
            </button>
          </div>
        </div>

        <!-- 协议快问标签栏 -->
        <div class="s1-proto-bar">
          <span class="proto-bar-label">热门协议</span>
          <button
            v-for="p in ['TCP','UDP','IPv4','IPv6','DNS','HTTP','TLS','QUIC']"
            :key="p"
            class="proto-chip"
            @click="quickAskRfc(p)"
          >{{ p }}</button>
          <span class="proto-more" @click="router.push('/kg-assist')">更多 ›</span>
        </div>

        <!-- Hero 区域（无消息时） -->
        <div v-if="!hasMessages" class="hero-card">
          <div class="hero-left">
            <div class="hero-badge">AI 学习驾驶舱</div>
            <h1 class="hero-title">Socrates Cube <span class="ai-gradient">AI</span> 教练</h1>
            <p class="hero-desc">我是你的 AI 教练，随时为你提供专业的学习支持</p>
            <div class="hero-actions">
              <div v-for="act in heroActions" :key="act.label" class="hero-action-card" @click="setInput(act.prompt)">
                <div class="ha-icon">{{ act.icon }}</div>
                <div class="ha-label">{{ act.label }}</div>
                <div class="ha-sub">{{ act.sub }}</div>
              </div>
            </div>
          </div>
          <div class="hero-right">
            <div class="ai-cube-scene">
              <div class="ai-cube">
                <div class="cube-face front"><span>AI</span></div>
                <div class="cube-face back"><span>AI</span></div>
                <div class="cube-face left"><span>SC</span></div>
                <div class="cube-face right"><span>SC</span></div>
                <div class="cube-face top"><span>⬡</span></div>
                <div class="cube-face bottom"><span>⬡</span></div>
              </div>
              <div class="cube-orbit orbit1"></div>
              <div class="cube-orbit orbit2"></div>
            </div>
          </div>
        </div>

        <!-- 快捷建议行（无消息时） -->
        <div v-if="!hasMessages" class="quick-suggest-bar">
          <span class="qs-label">你可以这样问我：</span>
          <button v-for="s in quickSuggestions" :key="s" class="qs-chip" @click="setInput(s)">{{ s }}</button>
        </div>

        <!-- ── 原版 ChatPanel（保留原有聊天交互样式） ── -->
        <div class="chat-panel-wrapper" :class="{ compact: !hasMessages }">
          <ChatPanel ref="chatPanelRef" :agent-persona="currentPersona" />
        </div>

        <!-- ════ AI 能力矩阵 ════ -->
        <section class="s1-section">
          <div class="sec-header">
            <div>
              <h2 class="sec-title">AI 能力矩阵</h2>
              <p class="sec-sub">多智能体协同工作，为你提供全方位学习支持</p>
            </div>
          </div>
          <div class="agent-grid">
            <div v-for="agent in agentMatrix" :key="agent.name" class="agent-card">
              <div class="agent-icon-bg" :style="{ background: agent.bg }">
                <span class="agent-icon">{{ agent.icon }}</span>
              </div>
              <div class="agent-info">
                <div class="agent-name">{{ agent.name }}</div>
                <div class="agent-role">{{ agent.role }}</div>
                <div class="agent-desc">{{ agent.desc }}</div>
              </div>
            </div>
          </div>
        </section>

        <!-- ════ 知识图谱 + 学习趋势 ════ -->
        <div class="s1-two-col">
          <!-- 知识图谱 -->
          <section class="s1-section s1-col">
            <div class="sec-header">
              <div>
                <h2 class="sec-title">知识图谱</h2>
                <p class="sec-sub">可视化的阶段性知识体系</p>
              </div>
            </div>
            <div class="kg-mini-wrap">
              <svg width="100%" height="250" viewBox="0 0 440 250">
                <!-- 连线 -->
                <line x1="220" y1="110" x2="220" y2="48" stroke="#e0e7ff" stroke-width="1.5"/>
                <line x1="220" y1="110" x2="105" y2="78" stroke="#e0e7ff" stroke-width="1.5"/>
                <line x1="220" y1="110" x2="335" y2="78" stroke="#e0e7ff" stroke-width="1.5"/>
                <line x1="220" y1="110" x2="220" y2="168" stroke="#e0e7ff" stroke-width="1.5"/>
                <line x1="220" y1="168" x2="138" y2="195" stroke="#e0e7ff" stroke-width="1"/>
                <line x1="220" y1="168" x2="302" y2="195" stroke="#e0e7ff" stroke-width="1"/>
                <line x1="105" y1="78" x2="38" y2="110" stroke="#bfdbfe" stroke-width="1"/>
                <!-- TCP 核心节点 -->
                <circle cx="220" cy="110" r="36" fill="#6366f1"/>
                <text x="220" y="106" text-anchor="middle" fill="white" font-size="11" font-weight="700">TCP</text>
                <text x="220" y="120" text-anchor="middle" fill="rgba(255,255,255,0.9)" font-size="9">三次握手</text>
                <!-- HTTP -->
                <circle cx="220" cy="40" r="22" fill="rgba(99,102,241,0.18)" stroke="#6366f1" stroke-width="1.5"/>
                <text x="220" y="44" text-anchor="middle" fill="#4f46e5" font-size="11" font-weight="600">HTTP</text>
                <!-- DNS -->
                <circle cx="100" cy="72" r="22" fill="rgba(56,189,248,0.15)" stroke="#38bdf8" stroke-width="1.5"/>
                <text x="100" y="76" text-anchor="middle" fill="#0284c7" font-size="11" font-weight="600">DNS</text>
                <!-- TLS -->
                <circle cx="340" cy="72" r="22" fill="rgba(45,212,191,0.15)" stroke="#2dd4bf" stroke-width="1.5"/>
                <text x="340" y="76" text-anchor="middle" fill="#0f766e" font-size="11" font-weight="600">TLS</text>
                <!-- Socket -->
                <circle cx="220" cy="170" r="22" fill="rgba(99,102,241,0.1)" stroke="#818cf8" stroke-width="1.5"/>
                <text x="220" y="174" text-anchor="middle" fill="#6366f1" font-size="11" font-weight="600">Socket</text>
                <!-- 滑动窗口（上移避免与图例重叠） -->
                <circle cx="132" cy="195" r="18" fill="rgba(99,102,241,0.07)" stroke="#c7d2fe" stroke-width="1"/>
                <text x="132" y="192" text-anchor="middle" fill="#818cf8" font-size="8.5">滑动</text>
                <text x="132" y="203" text-anchor="middle" fill="#818cf8" font-size="8.5">窗口</text>
                <!-- 拥塞控制（上移） -->
                <circle cx="308" cy="195" r="18" fill="rgba(99,102,241,0.07)" stroke="#c7d2fe" stroke-width="1"/>
                <text x="308" y="192" text-anchor="middle" fill="#818cf8" font-size="8.5">拥塞</text>
                <text x="308" y="203" text-anchor="middle" fill="#818cf8" font-size="8.5">控制</text>
                <!-- UDP -->
                <circle cx="36" cy="110" r="18" fill="rgba(56,189,248,0.1)" stroke="#7dd3fc" stroke-width="1"/>
                <text x="36" y="114" text-anchor="middle" fill="#0284c7" font-size="10" font-weight="500">UDP</text>
                <!-- 图例（置于底部，不与节点重叠） -->
                <circle cx="18" cy="235" r="5" fill="#6366f1"/>
                <text x="27" y="239" fill="#94a3b8" font-size="9">已掌握</text>
                <circle cx="72" cy="235" r="5" fill="rgba(56,189,248,0.5)" stroke="#38bdf8" stroke-width="1"/>
                <text x="81" y="239" fill="#94a3b8" font-size="9">学习中</text>
                <circle cx="135" cy="235" r="5" fill="rgba(99,102,241,0.1)" stroke="#c7d2fe" stroke-width="1"/>
                <text x="144" y="239" fill="#94a3b8" font-size="9">未掌握</text>
              </svg>
            </div>
          </section>

          <!-- 学习趋势 -->
          <section class="s1-section s1-col">
            <div class="sec-header">
              <div>
                <h2 class="sec-title">学习趋势</h2>
                <p class="sec-sub">你的学习进度和能力发展</p>
              </div>
              <div class="trend-tabs">
                <button :class="{ active: trendRange === '7d' }" @click="trendRange = '7d'">近 7 天</button>
                <button :class="{ active: trendRange === '30d' }" @click="trendRange = '30d'">近 30 天</button>
                <button disabled title="功能开发中" style="opacity:0.4;cursor:not-allowed">自定义</button>
              </div>
            </div>
            <div class="trend-legend">
              <span class="tl-dot" style="background:#c7d2fe"></span><span class="tl-text">学习量</span>
              <span class="tl-dot" style="background:#6366f1"></span><span class="tl-text">能力分</span>
              <span class="tl-dot" style="background:#2dd4bf"></span><span class="tl-text">学习速度</span>
            </div>
            <VChart class="trend-chart" :option="trendChartOption" autoresize />
          </section>
        </div>

        <!-- ════ 推荐学习 ════ -->
        <section class="s1-section">
          <div class="sec-header">
            <div>
              <h2 class="sec-title">推荐学习</h2>
              <p class="sec-sub">基于你的学习情况，AI 为你推荐</p>
            </div>
            <button class="refresh-btn" :disabled="refreshing" @click="refreshRecs">
              <span class="refresh-icon" :class="{ spinning: refreshing }">⟳</span> 换一批
            </button>
          </div>
          <div class="rec-grid">
            <div
              v-for="rec in recommendations"
              :key="rec.title"
              class="rec-card"
              @click="router.push('/resources')"
            >
              <div class="rec-top">
                <div class="rec-icon" :style="{ background: `${rec.color}18`, color: rec.color }">{{ rec.icon }}</div>
                <span class="rec-tag">{{ rec.tag }}</span>
              </div>
              <h3 class="rec-title">{{ rec.title }}</h3>
              <p class="rec-reason">推荐原因：{{ rec.reason }}</p>
              <div class="rec-bottom">
                <div class="rec-progress-bar">
                  <div class="rpb-fill" :style="{ width: rec.progress + '%', background: rec.color }"></div>
                </div>
                <div class="rec-meta">
                  <span>预计 {{ rec.duration }}</span>
                  <span class="rec-start">开始训练 →</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        <div style="height: 40px;"></div>
      </div>

      <!-- ═══ 右侧学习状态面板 ═══ -->
      <div class="s1-right">
        <div class="right-tabs">
          <button
            v-for="t in rightTabs"
            :key="t.key"
            class="rt-btn"
            :class="{ active: rightTab === t.key }"
            @click="rightTab = (t.key as typeof rightTab)"
          >
            <span class="rt-icon">{{ t.icon }}</span>
            <span class="rt-label">{{ t.label }}</span>
          </button>
        </div>

        <div v-if="rightTab === 'analysis'" class="right-content">
          <div class="analysis-block">
            <div class="ab-title">学习状态概览</div>
            <div class="radar-row">
              <div class="circular-score">
                <svg viewBox="0 0 100 100" width="100" height="100">
                  <circle cx="50" cy="50" r="42" fill="none" stroke="#e0e7ff" stroke-width="8"/>
                  <circle cx="50" cy="50" r="42" fill="none" stroke="#6366f1" stroke-width="8"
                    stroke-dasharray="264" stroke-dashoffset="71" stroke-linecap="round"
                    transform="rotate(-90 50 50)"/>
                  <text x="50" y="46" text-anchor="middle" fill="#1e293b" font-size="18" font-weight="700">72%</text>
                  <text x="50" y="62" text-anchor="middle" fill="#94a3b8" font-size="9">总体掌握度</text>
                </svg>
              </div>
              <div class="skill-bars">
                <div v-for="s in skillBars" :key="s.name" class="skill-row">
                  <span class="skill-name">{{ s.name }}</span>
                  <div class="skill-track">
                    <div class="skill-fill" :style="{ width: s.value + '%', background: s.color }"></div>
                  </div>
                  <span class="skill-val">{{ s.value }}%</span>
                </div>
              </div>
            </div>
          </div>
          <div class="analysis-block">
            <div class="ab-title">能力雷达图</div>
            <VChart style="height: 180px;" :option="radarOption" autoresize />
          </div>
          <div class="analysis-block">
            <div class="ab-title-row">
              <span class="ab-title">待解决问题</span>
              <span class="ab-badge">3 个知识点需强化</span>
            </div>
            <div v-for="wp in weakPoints" :key="wp.name" class="wp-item">
              <div class="wp-dot" :style="{ background: wp.color }"></div>
              <span class="wp-name">{{ wp.name }}</span>
              <span class="wp-level" :style="{ background: wp.bg, color: wp.color }">{{ wp.level }}</span>
            </div>
            <button class="view-detail-btn" @click="router.push('/diagnosis')">查看详情 ›</button>
          </div>
          <div class="analysis-block">
            <div class="ab-title">最近学习记录</div>
            <div v-for="h in recentHistory" :key="h.title" class="hist-item">
              <span class="hist-title">{{ h.title }}</span>
              <span class="hist-time">{{ h.time }}</span>
            </div>
            <button class="view-detail-btn" @click="router.push('/logs')">查看全部 ›</button>
          </div>
        </div>
        <div v-else-if="rightTab === 'diagnosis'" class="right-content"><DiagnosisPanel /></div>
        <div v-else-if="rightTab === 'kg'" class="right-content"><KGPanel /></div>
        <div v-else-if="rightTab === 'path'" class="right-content"><PathTimeline /></div>
        <div v-else class="right-content"><AgentLogPanel :session-id="chatStore.currentSession?.sessionId" /></div>
      </div>

    </div>
  </div>
</template>

<style scoped>
/* ═══ 整体布局 ═══ */
.s1-wrapper {
  height: 100%;
  background: #f5f7ff;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.s1-body {
  flex: 1;
  display: flex;
  gap: 16px;
  overflow: hidden;
}
.s1-main {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
  padding-bottom: 8px;
}
.s1-main::-webkit-scrollbar { width: 5px; }
.s1-main::-webkit-scrollbar-thumb { background: #ddd6fe; border-radius: 3px; }

/* ═══ 顶部栏 ═══ */
.s1-topbar {
  display: flex; align-items: center; gap: 12px; flex-wrap: wrap;
  background: rgba(255,255,255,0.85); border: 1px solid rgba(99,102,241,0.12);
  border-radius: 14px; padding: 10px 16px; backdrop-filter: blur(10px); flex-shrink: 0;
}
.topbar-greet { display: flex; align-items: center; gap: 8px; }
.greet-emoji { font-size: 20px; }
.greet-text { font-size: 15px; font-weight: 600; color: #1e293b; }
.topbar-center { display: flex; align-items: center; gap: 8px; margin-left: auto; flex-wrap: wrap; }
.ai-label { font-size: 12px; color: #94a3b8; white-space: nowrap; }
.vt-btn {
  padding: 5px 12px; border: 1px solid #e2e8f0; border-radius: 20px;
  background: white; cursor: pointer; font-size: 12px; color: #64748b; transition: all 0.2s;
}
.vt-btn:hover { border-color: #818cf8; color: #4f46e5; background: #eef2ff; }
.vt-btn.active { background: #4f46e5; color: white; border-color: #4f46e5; }

/* ═══ 协议快问栏 ═══ */
.s1-proto-bar {
  display: flex; align-items: center; gap: 8px; flex-wrap: wrap; flex-shrink: 0;
  background: rgba(255,255,255,0.78); border: 1px solid rgba(99,102,241,0.1);
  border-radius: 12px; padding: 8px 14px; backdrop-filter: blur(8px);
}
.proto-bar-label { font-size: 11px; color: #94a3b8; white-space: nowrap; font-weight: 500; }
.proto-chip {
  font-size: 11px; font-weight: 700; padding: 4px 10px; border-radius: 8px;
  background: #f1f5f9; color: #475569; border: 1px solid #e2e8f0; cursor: pointer;
  transition: all 0.18s; letter-spacing: 0.3px;
}
.proto-chip:hover { background: #6366f1; color: white; border-color: #6366f1; transform: translateY(-1px); box-shadow: 0 3px 10px rgba(99,102,241,0.35); }
.proto-more { font-size: 12px; color: #6366f1; cursor: pointer; margin-left: auto; font-weight: 500; }

/* ═══ Hero 卡片 ═══ */
.hero-card {
  background: linear-gradient(135deg, rgba(255,255,255,0.9) 0%, rgba(240,245,255,0.9) 100%);
  border: 1px solid rgba(99,102,241,0.15); border-radius: 20px; padding: 28px 24px;
  display: flex; align-items: center; gap: 24px; backdrop-filter: blur(12px);
  box-shadow: 0 8px 32px rgba(99,102,241,0.08); flex-shrink: 0; overflow: hidden; position: relative;
}
.hero-card::before {
  content: ''; position: absolute; top: -60px; right: -60px;
  width: 200px; height: 200px;
  background: radial-gradient(circle, rgba(99,102,241,0.07) 0%, transparent 70%); border-radius: 50%;
}
.hero-left { flex: 1; min-width: 0; }
.hero-badge {
  display: inline-block; padding: 3px 12px; border-radius: 20px;
  background: rgba(99,102,241,0.1); color: #6366f1; font-size: 11px; font-weight: 600;
  margin-bottom: 10px; letter-spacing: 0.5px;
}
.hero-title { font-size: 26px; font-weight: 700; color: #1e293b; margin-bottom: 6px; line-height: 1.2; }
.ai-gradient {
  background: linear-gradient(135deg, #6366f1, #38bdf8);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  font-style: italic;
}
.hero-desc { font-size: 13px; color: #64748b; margin-bottom: 20px; }
.hero-actions { display: flex; gap: 10px; flex-wrap: wrap; }
.hero-action-card {
  display: flex; flex-direction: column; align-items: center; gap: 4px; padding: 12px 16px;
  background: rgba(255,255,255,0.8); border: 1px solid rgba(99,102,241,0.15);
  border-radius: 12px; cursor: pointer; transition: all 0.2s; min-width: 72px;
}
.hero-action-card:hover { border-color: #6366f1; transform: translateY(-3px); box-shadow: 0 6px 20px rgba(99,102,241,0.2); }
.ha-icon { font-size: 20px; }
.ha-label { font-size: 12px; font-weight: 600; color: #1e293b; }
.ha-sub { font-size: 10px; color: #94a3b8; }
.hero-right { flex-shrink: 0; display: flex; align-items: center; justify-content: center; width: 180px; height: 160px; }

/* 3D AI 魔方 */
.ai-cube-scene { position: relative; width: 150px; height: 150px; perspective: 280px; display: flex; align-items: center; justify-content: center; }
.ai-cube { width: 72px; height: 72px; transform-style: preserve-3d; animation: spin-cube 10s linear infinite; position: relative; }
.cube-face {
  position: absolute; width: 72px; height: 72px; background: rgba(99,102,241,0.12);
  border: 2px solid rgba(99,102,241,0.5); display: flex; align-items: center; justify-content: center;
  font-size: 15px; font-weight: 700; color: #6366f1; backface-visibility: hidden; backdrop-filter: blur(4px);
}
.cube-face.front  { transform: translateZ(36px); }
.cube-face.back   { transform: rotateY(180deg) translateZ(36px); }
.cube-face.left   { transform: rotateY(-90deg) translateZ(36px); }
.cube-face.right  { transform: rotateY(90deg) translateZ(36px); }
.cube-face.top    { transform: rotateX(90deg) translateZ(36px); }
.cube-face.bottom { transform: rotateX(-90deg) translateZ(36px); }
@keyframes spin-cube { from { transform: rotateX(15deg) rotateY(0deg); } to { transform: rotateX(15deg) rotateY(360deg); } }
.cube-orbit { position: absolute; border-radius: 50%; border: 1px dashed rgba(99,102,241,0.3); top: 50%; left: 50%; }
.orbit1 { width: 110px; height: 110px; margin-left: -55px; margin-top: -55px; animation: spin-orbit 6s linear infinite; }
.orbit2 { width: 140px; height: 140px; margin-left: -70px; margin-top: -70px; border-color: rgba(56,189,248,0.22); animation: spin-orbit 9s linear infinite reverse; }
@keyframes spin-orbit { from { transform: rotateX(60deg) rotateZ(0deg); } to { transform: rotateX(60deg) rotateZ(360deg); } }

/* ═══ 快捷建议 ═══ */
.quick-suggest-bar {
  display: flex; align-items: center; gap: 8px; flex-wrap: wrap; flex-shrink: 0;
}
.qs-label { font-size: 13px; color: #64748b; white-space: nowrap; }
.qs-chip {
  padding: 6px 14px; border-radius: 20px; border: 1px solid #e0e7ff;
  background: rgba(255,255,255,0.82); color: #4f46e5; font-size: 12px;
  cursor: pointer; transition: all 0.18s;
}
.qs-chip:hover { background: #eef2ff; border-color: #6366f1; transform: translateY(-1px); box-shadow: 0 3px 10px rgba(99,102,241,0.15); }

/* ═══ ChatPanel 容器（保留原版样式，外层融入方案一） ═══ */
.chat-panel-wrapper {
  flex-shrink: 0; border-radius: 16px; overflow: hidden;
  background: rgba(255,255,255,0.82); border: 1px solid rgba(99,102,241,0.1);
  backdrop-filter: blur(8px); box-shadow: 0 4px 20px rgba(99,102,241,0.06);
}
.chat-panel-wrapper :deep(.chat-panel) { height: 520px; }
.chat-panel-wrapper.compact :deep(.chat-panel) { height: 190px; }
/* 隐藏 ChatPanel 内置欢迎页（由 hero-card 代替） */
:deep(.chat-welcome) { display: none !important; }
/* 让 ChatPanel 内部消息区与方案一背景融合 */
:deep(.messages-container) { background: rgba(248,250,252,0.7) !important; }
/* 输入区微调 */
:deep(.input-area) {
  margin-top: 8px !important;
  background: rgba(255,255,255,0.9) !important;
  border-color: rgba(99,102,241,0.12) !important;
}

/* ═══ 通用 Section ═══ */
.s1-section {
  background: rgba(255,255,255,0.8); border: 1px solid rgba(99,102,241,0.1);
  border-radius: 18px; padding: 20px; backdrop-filter: blur(8px);
  box-shadow: 0 4px 20px rgba(99,102,241,0.06); flex-shrink: 0;
}
.s1-two-col { display: flex; gap: 16px; flex-shrink: 0; }
.s1-col { flex: 1; min-width: 0; }
.sec-header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 16px; gap: 8px; }
.sec-title { font-size: 16px; font-weight: 700; color: #1e293b; margin-bottom: 2px; }
.sec-sub { font-size: 12px; color: #94a3b8; }

/* ═══ Agent 矩阵 ═══ */
.agent-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.agent-card {
  display: flex; align-items: flex-start; gap: 10px; padding: 12px;
  background: rgba(248,250,252,0.8); border-radius: 12px;
  border: 1px solid rgba(99,102,241,0.08); transition: all 0.2s; cursor: pointer;
}
.agent-card:hover { border-color: rgba(99,102,241,0.3); transform: translateY(-2px); box-shadow: 0 6px 18px rgba(99,102,241,0.12); }
.agent-icon-bg { width: 38px; height: 38px; border-radius: 10px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.agent-icon { font-size: 18px; filter: brightness(0) invert(1); }
.agent-info { flex: 1; min-width: 0; }
.agent-name { font-size: 12px; font-weight: 700; color: #1e293b; }
.agent-role { font-size: 10px; color: #6366f1; font-weight: 500; margin-bottom: 2px; }
.agent-desc { font-size: 10px; color: #94a3b8; line-height: 1.4; }

/* ═══ 知识图谱 ═══ */
.kg-mini-wrap { background: rgba(248,250,252,0.6); border-radius: 12px; overflow: hidden; }

/* ═══ 趋势图 ═══ */
.trend-tabs { display: flex; gap: 4px; }
.trend-tabs button { padding: 4px 10px; font-size: 11px; border-radius: 6px; border: 1px solid #e2e8f0; background: white; color: #64748b; cursor: pointer; transition: all 0.15s; }
.trend-tabs button.active { background: #6366f1; color: white; border-color: #6366f1; }
.trend-legend { display: flex; align-items: center; gap: 12px; margin-bottom: 6px; flex-wrap: wrap; }
.tl-dot { display: inline-block; width: 14px; height: 3px; border-radius: 2px; margin-right: 4px; vertical-align: middle; }
.tl-text { font-size: 11px; color: #94a3b8; }
.trend-chart { height: 190px; }

/* ═══ 推荐学习 ═══ */
.refresh-btn {
  display: flex; align-items: center; gap: 4px;
  padding: 6px 14px; border-radius: 8px; border: 1px solid #e0e7ff;
  background: white; color: #6366f1; font-size: 12px; cursor: pointer; transition: all 0.18s; flex-shrink: 0;
}
.refresh-btn:hover:not(:disabled) { background: #eef2ff; border-color: #c7d2fe; }
.refresh-btn:disabled { opacity: 0.7; cursor: not-allowed; }
.refresh-icon { display: inline-block; font-size: 14px; transition: transform 0.3s; }
.refresh-btn:hover:not(:disabled) .refresh-icon { transform: rotate(180deg); }
.spinning { animation: spin360 0.28s ease; }
@keyframes spin360 { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
.rec-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.rec-card {
  background: rgba(248,250,252,0.8); border: 1px solid rgba(99,102,241,0.08);
  border-radius: 14px; padding: 14px; cursor: pointer; transition: all 0.22s;
  display: flex; flex-direction: column; gap: 8px;
}
.rec-card:hover { border-color: rgba(99,102,241,0.25); transform: translateY(-3px); box-shadow: 0 8px 24px rgba(99,102,241,0.12); }
.rec-top { display: flex; align-items: center; justify-content: space-between; }
.rec-icon { width: 36px; height: 36px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 18px; }
.rec-tag { font-size: 10px; padding: 2px 8px; border-radius: 10px; background: #f1f5f9; color: #64748b; }
.rec-title { font-size: 13px; font-weight: 600; color: #1e293b; }
.rec-reason { font-size: 11px; color: #94a3b8; line-height: 1.4; }
.rec-bottom { margin-top: auto; }
.rec-progress-bar { height: 4px; background: #f1f5f9; border-radius: 2px; margin-bottom: 8px; }
.rpb-fill { height: 100%; border-radius: 2px; transition: width 0.5s; }
.rec-meta { display: flex; justify-content: space-between; font-size: 11px; color: #94a3b8; }
.rec-start { color: #6366f1; font-weight: 500; }

/* ═══ 右侧面板 ═══ */
.s1-right {
  width: 340px; flex-shrink: 0; display: flex; flex-direction: column;
  background: rgba(255,255,255,0.82); border: 1px solid rgba(99,102,241,0.1);
  border-radius: 18px; overflow: hidden; backdrop-filter: blur(12px);
  box-shadow: 0 4px 20px rgba(99,102,241,0.07);
}
.right-tabs { display: flex; background: #f8faff; border-bottom: 1px solid rgba(99,102,241,0.1); flex-shrink: 0; }
.rt-btn {
  flex: 1; display: flex; flex-direction: column; align-items: center; gap: 2px;
  padding: 9px 4px 8px; border: none; background: none; cursor: pointer;
  color: #94a3b8; transition: all 0.18s; border-bottom: 2px solid transparent; font-size: 9px; font-weight: 500;
}
.rt-btn:hover { color: #6366f1; background: rgba(99,102,241,0.05); }
.rt-btn.active { color: #6366f1; border-bottom-color: #6366f1; background: rgba(99,102,241,0.04); }
.rt-icon { font-size: 15px; }
.rt-label { white-space: nowrap; }
.right-content { flex: 1; overflow-y: auto; padding: 14px; }
.right-content::-webkit-scrollbar { width: 4px; }
.right-content::-webkit-scrollbar-thumb { background: #ddd6fe; border-radius: 2px; }
.analysis-block { margin-bottom: 20px; }
.ab-title { font-size: 13px; font-weight: 600; color: #1e293b; margin-bottom: 10px; }
.ab-title-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; }
.ab-badge { font-size: 10px; padding: 2px 8px; background: #fffbeb; color: #d97706; border-radius: 10px; }
.radar-row { display: flex; align-items: center; gap: 10px; }
.circular-score { flex-shrink: 0; }
.skill-bars { flex: 1; display: flex; flex-direction: column; gap: 5px; }
.skill-row { display: flex; align-items: center; gap: 6px; }
.skill-name { font-size: 10px; color: #64748b; width: 54px; flex-shrink: 0; }
.skill-track { flex: 1; height: 5px; background: #f1f5f9; border-radius: 3px; }
.skill-fill { height: 100%; border-radius: 3px; transition: width 0.6s; }
.skill-val { font-size: 10px; color: #94a3b8; width: 30px; text-align: right; }
.wp-item { display: flex; align-items: center; gap: 8px; padding: 7px 0; border-bottom: 1px solid #f8faff; }
.wp-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
.wp-name { flex: 1; font-size: 12px; color: #334155; }
.wp-level { font-size: 10px; padding: 2px 7px; border-radius: 10px; white-space: nowrap; }
.hist-item { display: flex; align-items: center; justify-content: space-between; padding: 7px 0; border-bottom: 1px solid #f8faff; }
.hist-title { font-size: 12px; color: #334155; }
.hist-time { font-size: 11px; color: #94a3b8; white-space: nowrap; }
.view-detail-btn { margin-top: 8px; font-size: 12px; color: #6366f1; background: none; border: none; cursor: pointer; padding: 0; display: block; }
.view-detail-btn:hover { text-decoration: underline; }
</style>
