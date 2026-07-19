<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { checkHealth } from '@/api/health'

const router = useRouter()
const backendStatus = ref<string>('检测中...')
const kgCanvasRef = ref<HTMLCanvasElement | null>(null)
let animId = 0

/* ─── Hero 知识图谱 Canvas ─── */
function initKGCanvas() {
  const canvas = kgCanvasRef.value
  if (!canvas) return
  const cvs = canvas // 非空断言别名，供闭包使用
  const ctx = cvs.getContext('2d')!
  function resize() { cvs.width = cvs.offsetWidth; cvs.height = cvs.offsetHeight }
  resize()
  window.addEventListener('resize', resize)

  const labels = ['TCP/IP', 'HTTP/2', 'QUIC', 'DNS', 'OSPF', 'WebSocket', 'BGP', 'TLS', 'UDP', 'ARP', 'SMTP', 'ICMP']
  const nodes = labels.map((label, i) => ({
    label,
    baseAngle: (i / labels.length) * Math.PI * 2,
    dist: 0.70 + (i % 3) * 0.08,
    phase: i * 0.55,
    speed: 0.06 + (i % 4) * 0.015,
  }))
  let t = 0

  function rr(c: CanvasRenderingContext2D, x: number, y: number, w: number, h: number, r: number) {
    c.beginPath()
    c.moveTo(x + r, y); c.lineTo(x + w - r, y); c.quadraticCurveTo(x + w, y, x + w, y + r)
    c.lineTo(x + w, y + h - r); c.quadraticCurveTo(x + w, y + h, x + w - r, y + h)
    c.lineTo(x + r, y + h); c.quadraticCurveTo(x, y + h, x, y + h - r)
    c.lineTo(x, y + r); c.quadraticCurveTo(x, y, x + r, y); c.closePath()
  }

  function draw() {
    ctx.clearRect(0, 0, cvs.width, cvs.height)
    const cx = cvs.width / 2, cy = cvs.height / 2
    const R = Math.min(cx, cy) * 0.86
    t += 0.005

    // 轨道虚线圈
    ;[0.48, 0.84].forEach((f, ri) => {
      ctx.beginPath()
      ctx.arc(cx, cy, R * f, 0, Math.PI * 2)
      ctx.strokeStyle = ri === 0 ? 'rgba(99,102,241,0.13)' : 'rgba(99,102,241,0.07)'
      ctx.lineWidth = 1
      ctx.setLineDash([4, 7])
      ctx.stroke()
      ctx.setLineDash([])
    })

    // 外圈节点
    nodes.forEach((nd, i) => {
      const angle = nd.baseAngle + t * nd.speed * (i % 2 === 0 ? 1 : -1)
      const nx = cx + Math.cos(angle) * R * nd.dist + Math.sin(t * 0.7 + nd.phase) * 7
      const ny = cy + Math.sin(angle) * R * nd.dist + Math.cos(t * 0.55 + nd.phase) * 5

      // 连线
      const alpha = 0.11 + 0.07 * Math.sin(t * 1.4 + i)
      ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(nx, ny)
      ctx.strokeStyle = `rgba(99,102,241,${alpha})`; ctx.lineWidth = 0.9; ctx.stroke()

      // 小节点圆
      ctx.beginPath(); ctx.arc(nx, ny, 3.5, 0, Math.PI * 2)
      ctx.fillStyle = 'rgba(99,102,241,0.62)'; ctx.fill()

      // 标签胶囊
      ctx.font = 'bold 9.5px "PingFang SC",system-ui'
      const tw = ctx.measureText(nd.label).width
      const pw = tw + 14, ph = 19, px = nx - pw / 2, py = ny - ph / 2
      rr(ctx, px, py, pw, ph, 5)
      ctx.fillStyle = 'rgba(255,255,255,0.93)'
      ctx.shadowColor = 'rgba(99,102,241,0.18)'; ctx.shadowBlur = 7; ctx.fill()
      ctx.shadowBlur = 0
      ctx.strokeStyle = 'rgba(99,102,241,0.22)'; ctx.lineWidth = 0.7; ctx.stroke()
      ctx.fillStyle = '#4338CA'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'
      ctx.fillText(nd.label, nx, ny)
    })

    // 中心光晕
    const g1 = ctx.createRadialGradient(cx, cy, 0, cx, cy, 55)
    g1.addColorStop(0, 'rgba(99,102,241,0.22)'); g1.addColorStop(1, 'transparent')
    ctx.beginPath(); ctx.arc(cx, cy, 55, 0, Math.PI * 2)
    ctx.fillStyle = g1; ctx.fill()

    // 中心节点
    const g2 = ctx.createLinearGradient(cx - 30, cy - 30, cx + 30, cy + 30)
    g2.addColorStop(0, '#6366F1'); g2.addColorStop(1, '#8B5CF6')
    ctx.beginPath()
    ctx.arc(cx, cy, 30 + Math.sin(t * 2) * 1.8, 0, Math.PI * 2)
    ctx.fillStyle = g2
    ctx.shadowColor = 'rgba(99,102,241,0.5)'; ctx.shadowBlur = 22; ctx.fill()
    ctx.shadowBlur = 0
    ctx.fillStyle = '#fff'; ctx.font = 'bold 10px "PingFang SC",system-ui'
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle'
    ctx.fillText('知识图谱', cx, cy - 7)
    ctx.font = '8px "PingFang SC",system-ui'; ctx.fillText('Knowledge', cx, cy + 7)

    animId = requestAnimationFrame(draw)
  }
  draw()
}

/* ─── Stats ─── */
const stats = [
  { value: 8,   unit: '个',    label: '专业 Agent',  icon: '🤖', color: '#6366F1' },
  { value: 8,   unit: '维',    label: '能力画像',     icon: '📊', color: '#8B5CF6' },
  { value: 6,   unit: '类',    label: '多模态资源',   icon: '🎨', color: '#06B6D4' },
  { value: 100, unit: '+节点', label: '知识图谱',     icon: '🌐', color: '#F59E0B' },
]
const displayVals = ref(stats.map(() => 0))
function runCountUp() {
  stats.forEach((s, i) => {
    let cur = 0
    const step = Math.ceil(s.value / 30)
    const id = setInterval(() => {
      cur = Math.min(cur + step, s.value)
      displayVals.value[i] = cur
      if (cur >= s.value) clearInterval(id)
    }, 40)
  })
}

/* ─── Core Features ─── */
const coreFeatures = [
  { title: '对话式学习画像',  desc: '自然语言对话自动抽取 6+ 维度特征，构建动态学生画像，随学随新', icon: '📊', color: '#8B5CF6', path: '/profile',   tag: '核心功能' },
  { title: '多模态资源生成',  desc: '5 类个性化资源：文档、思维导图、练习题库、代码案例、学习脚本',  icon: '🎨', color: '#10B981', path: '/resources', tag: '核心功能' },
  { title: '个性化学习路径',  desc: '多智能体协同，结合画像动态规划学习序列，精准推送匹配资源',    icon: '🗺️', color: '#3B82F6', path: '/path',      tag: '核心功能' },
  { title: '三层诊断引擎',   desc: '表层检测 → 根因分析 → 误区匹配，精准定位认知偏差，驱动效果评估', icon: '🔍', color: '#EF4444', path: '/diagnosis', tag: '评估加分' },
  { title: '协议仿真可视化', desc: 'TCP 握手/挥手、滑动窗口、HTTP 报文等核心协议动态演示',          icon: '🎬', color: '#EC4899', path: '/simulator', tag: '创新特色' },
  { title: '智能对话辅导',   desc: '遇到问题即时提问，AI 结合知识图谱提供图文多模态即时解答',       icon: '💬', color: '#06B6D4', path: '/chat',      tag: '辅导加分' },
]

/* ─── Agents ─── */
const agents = [
  { name: '总调度',   desc: '协调中枢',  icon: '🎯', color: '#6366F1' },
  { name: '知识检索', desc: 'RAG 语义', icon: '🔎', color: '#10B981' },
  { name: '诊断引擎', desc: '三层认知', icon: '🩺', color: '#EF4444' },
  { name: '画像构建', desc: '6 维动态', icon: '👤', color: '#8B5CF6' },
  { name: '资源生成', desc: '5 类多模', icon: '📚', color: '#F59E0B' },
  { name: '路径规划', desc: '个性序列', icon: '🗺️', color: '#06B6D4' },
  { name: '协议仿真', desc: '可视演示', icon: '🎬', color: '#EC4899' },
  { name: '概念挑战', desc: '苏式问答', icon: '⚡', color: '#F97316' },
]

/* ─── Resources ─── */
const resourceTypes = [
  { label: '专业文档', icon: '📄', desc: '知识点精讲',   color: '#6366F1', count: 86 },
  { label: '思维导图', icon: '🗺️', desc: '结构可视化', color: '#10B981', count: 124 },
  { label: '练习题库', icon: '📝', desc: '多类型习题',   color: '#F59E0B', count: 296 },
  { label: '代码案例', icon: '💻', desc: '实操示例',     color: '#8B5CF6', count: 60 },
  { label: '学习脚本', icon: '🎬', desc: '情景化剧本',   color: '#EC4899', count: 32 },
]

/* ─── Profile dims ─── */
const profileDims = [
  { label: '知识基础', icon: '📖', color: '#3B82F6' },
  { label: '认知风格', icon: '🧠', color: '#8B5CF6' },
  { label: '易错偏好', icon: '⚠️', color: '#EF4444' },
  { label: '学习目标', icon: '🎯', color: '#10B981' },
  { label: '学习进度', icon: '📈', color: '#F59E0B' },
  { label: '能力评估', icon: '⭐', color: '#06B6D4' },
]

const recommendedQuestions = [
  '什么是TCP三次握手？为什么不能是两次？',
  'HTTP是直接基于IP的吗？TCP/IP各层如何分工？',
  '滑动窗口和拥塞窗口有什么区别？',
]

const qColors = ['#6366F1', '#8B5CF6', '#10B981']

function goTo(path: string) { router.push(path) }
function startChat(q: string) { router.push({ path: '/chat', query: { q } }) }

onMounted(async () => {
  try {
    const d = await checkHealth(); backendStatus.value = d.status
  } catch { backendStatus.value = '未连接' }
  initKGCanvas()
  setTimeout(runCountUp, 400)
})
onUnmounted(() => { cancelAnimationFrame(animId) })
</script>

<template>
  <div class="home-view">

    <!-- ══ Hero ══ -->
    <section class="hero">
      <div class="hero-content">
        <div class="hero-eyebrow">
          <span class="status-dot" :class="{ online: backendStatus === 'ok' }" />
          <span>{{ backendStatus === 'ok' ? 'AI 系统运行中' : backendStatus }}</span>
          <span class="eyebrow-sep">·</span>
          <span>系统正常运行</span>
        </div>
        <div class="hero-welcome">欢迎回来，未来网络工程师 👋</div>
        <h1 class="hero-title">
          Socrates <span class="title-gradient">Cube</span>
        </h1>
        <p class="hero-sub">AI 驱动的计算机网络智能学习空间</p>
        <p class="hero-desc">
          基于多智能体协同与知识图谱驱动的学习引擎，<br />
          以认知科学为指导，为你定制专属学习路径，高效、可视化地学习网络知识。
        </p>
        <div class="hero-actions">
          <button class="btn-primary" @click="goTo('/chat')">
            <span>✨ 开始学习</span>
          </button>
          <button class="btn-ghost" @click="goTo('/profile')">📊 我的学习画像</button>
          <button class="btn-ghost" @click="goTo('/simulator')">🎬 协议仿真</button>
        </div>
      </div>
      <div class="hero-graph">
        <canvas ref="kgCanvasRef" class="kg-canvas" />
      </div>
    </section>

    <!-- ══ Stats ══ -->
    <section class="stats-row">
      <div v-for="(s, i) in stats" :key="s.label" class="stat-card">
        <div class="stat-icon-wrap" :style="{ background: s.color + '18' }">
          <span>{{ s.icon }}</span>
        </div>
        <div>
          <div class="stat-value" :style="{ color: s.color }">
            {{ displayVals[i] }}<span class="stat-unit">{{ s.unit }}</span>
          </div>
          <div class="stat-label">{{ s.label }}</div>
        </div>
      </div>
    </section>

    <!-- ══ 六大核心能力 ══ -->
    <section class="section">
      <div class="sec-head">
        <h2 class="sec-title"><span class="sec-badge">Core</span>六大核心能力</h2>
        <p class="sec-desc">对应赛题全部核心功能，多智能体协同打造完整学习闭环</p>
      </div>
      <div class="feat-grid">
        <div
          v-for="f in coreFeatures"
          :key="f.title"
          class="feat-card"
          @click="goTo(f.path)"
        >
          <div class="feat-accent" :style="{ background: f.color }" />
          <div class="feat-body">
            <div class="feat-header">
              <div class="feat-icon-wrap" :style="{ background: f.color + '18' }">{{ f.icon }}</div>
              <span class="feat-tag" :style="{ color: f.color, background: f.color + '12', border: `1px solid ${f.color}28` }">
                {{ f.tag }}
              </span>
            </div>
            <h3 class="feat-title" :style="{ color: f.color }">{{ f.title }}</h3>
            <p class="feat-desc">{{ f.desc }}</p>
            <div class="feat-go" :style="{ color: f.color }">查看详情 →</div>
          </div>
        </div>
      </div>
    </section>

    <!-- ══ 8 大智能体矩阵 ══ -->
    <section class="section">
      <div class="sec-head">
        <h2 class="sec-title"><span class="sec-badge agent-badge">Agent</span>8 大智能体矩阵</h2>
        <p class="sec-desc">各司其职、协同运作，共同服务个性化学习全流程</p>
      </div>
      <div class="agent-grid">
        <div v-for="(a, i) in agents" :key="a.name" class="agent-card">
          <div class="agent-badge-num" :style="{ color: a.color, background: a.color + '15' }">
            {{ String(i + 1).padStart(2, '0') }}
          </div>
          <div class="agent-icon-wrap" :style="{ background: a.color + '14' }">{{ a.icon }}</div>
          <div class="agent-info">
            <span class="agent-name" :style="{ color: a.color }">{{ a.name }}</span>
            <span class="agent-desc">{{ a.desc }}</span>
          </div>
        </div>
      </div>
    </section>

    <!-- ══ 两列：资源 + 画像 ══ -->
    <div class="two-col">
      <div class="col-card">
        <div class="col-head">
          <h3 class="col-title">🎨 5 类多模态资源</h3>
          <button class="col-link" @click="goTo('/resources')">生成资源 →</button>
        </div>
        <div class="res-list">
          <div v-for="r in resourceTypes" :key="r.label" class="res-item">
            <div class="res-icon" :style="{ background: r.color + '18', color: r.color }">{{ r.icon }}</div>
            <div class="res-body">
              <span class="res-name">{{ r.label }}</span>
              <span class="res-sub">{{ r.desc }}</span>
            </div>
            <span class="res-count" :style="{ color: r.color, background: r.color + '12' }">{{ r.count }}</span>
          </div>
        </div>
      </div>

      <div class="col-card">
        <div class="col-head">
          <h3 class="col-title">📊 6+ 维动态学习画像</h3>
          <button class="col-link" @click="goTo('/profile')">查看画像 →</button>
        </div>
        <div class="dim-grid">
          <div
            v-for="d in profileDims"
            :key="d.label"
            class="dim-chip"
            :style="{ background: d.color + '10', border: `1px solid ${d.color}28` }"
          >
            <span>{{ d.icon }}</span>
            <span class="dim-text" :style="{ color: d.color }">{{ d.label }}</span>
          </div>
        </div>
        <div class="dim-note">
          💡 通过自然语言对话自动构建，随学习过程持续更新迭代
        </div>
      </div>
    </div>

    <!-- ══ 快速开始 ══ -->
    <section class="section">
      <div class="sec-head">
        <h2 class="sec-title"><span class="sec-badge try-badge">Try</span>快速开始</h2>
        <p class="sec-desc">选择一个典型问题，立即体验 AI 智能诊断与辅导</p>
      </div>
      <div class="q-list">
        <div
          v-for="(q, i) in recommendedQuestions"
          :key="i"
          class="q-item"
          @click="startChat(q)"
        >
          <div class="q-num" :style="{ background: qColors[i] }">{{ i + 1 }}</div>
          <span class="q-text">{{ q }}</span>
          <span class="q-arrow">→</span>
        </div>
      </div>
    </section>

    <!-- ══ Footer ══ -->
    <footer class="home-footer">
      <div class="footer-l">
        <span class="footer-brand">Socrates Cube Team</span>
        <span class="footer-ver">v1.0.0</span>
      </div>
      <div class="footer-r">
        <span class="footer-copy">AI 驱动的计算机网络学习空间</span>
      </div>
    </footer>
  </div>
</template>

<style scoped>
/* ─── 整体容器 ─── */
.home-view {
  display: flex;
  flex-direction: column;
  gap: 24px;
  max-width: 1200px;
  margin: 0 auto;
  padding-bottom: 16px;
}

/* ─── Hero ─── */
.hero {
  position: relative;
  border-radius: 20px;
  padding: 48px 52px 48px 52px;
  background: linear-gradient(135deg, #EEF2FF 0%, #F0F9FF 45%, #FAF5FF 100%);
  border: 1px solid rgba(99, 102, 241, 0.12);
  box-shadow: 0 2px 24px rgba(99, 102, 241, 0.07);
  display: flex;
  align-items: center;
  gap: 0;
  min-height: 300px;
  overflow: hidden;
}

/* 装饰光球 */
.hero::before {
  content: '';
  position: absolute;
  width: 320px; height: 320px;
  background: radial-gradient(circle, rgba(99,102,241,0.12) 0%, transparent 70%);
  top: -80px; left: -40px;
  border-radius: 50%;
  pointer-events: none;
}
.hero::after {
  content: '';
  position: absolute;
  width: 240px; height: 240px;
  background: radial-gradient(circle, rgba(139,92,246,0.10) 0%, transparent 70%);
  bottom: -60px; right: 320px;
  border-radius: 50%;
  pointer-events: none;
}

.hero-content {
  flex: 1;
  min-width: 0;
  position: relative;
  z-index: 1;
  max-width: 540px;
}

.hero-eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 5px 13px;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(99, 102, 241, 0.18);
  border-radius: 20px;
  font-size: 12px;
  color: #6366F1;
  margin-bottom: 14px;
  backdrop-filter: blur(6px);
  font-weight: 500;
}

.status-dot {
  width: 7px; height: 7px;
  border-radius: 50%;
  background: #94a3b8;
  flex-shrink: 0;
}
.status-dot.online {
  background: #10B981;
  box-shadow: 0 0 6px rgba(16, 185, 129, 0.6);
  animation: pulse 2s infinite;
}
@keyframes pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(16,185,129,0.4); }
  50%       { box-shadow: 0 0 0 5px rgba(16,185,129,0); }
}

.eyebrow-sep { opacity: 0.4; }

.hero-welcome {
  font-size: 14px;
  color: #64748B;
  font-weight: 500;
  margin-bottom: 8px;
}

.hero-title {
  font-size: 48px;
  font-weight: 800;
  line-height: 1.08;
  letter-spacing: -2px;
  color: #111827;
  margin-bottom: 8px;
}

.title-gradient {
  background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 50%, #06B6D4 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-sub {
  font-size: 16px;
  font-weight: 600;
  color: #334155;
  margin-bottom: 10px;
}

.hero-desc {
  font-size: 13.5px;
  color: #64748B;
  line-height: 1.8;
  margin-bottom: 28px;
}

.hero-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 11px 24px;
  background: linear-gradient(135deg, #6366F1, #8B5CF6);
  color: #fff;
  border: none;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.22s;
  box-shadow: 0 4px 16px rgba(99, 102, 241, 0.35);
}
.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(99, 102, 241, 0.45);
}

.btn-ghost {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 11px 18px;
  background: rgba(255, 255, 255, 0.72);
  color: #334155;
  border: 1px solid rgba(99, 102, 241, 0.2);
  border-radius: 12px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  backdrop-filter: blur(6px);
}
.btn-ghost:hover {
  background: rgba(255, 255, 255, 0.9);
  border-color: rgba(99, 102, 241, 0.4);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.1);
}

/* Hero 右侧知识图谱 */
.hero-graph {
  flex-shrink: 0;
  width: 380px;
  height: 280px;
  position: relative;
  z-index: 1;
}

.kg-canvas {
  width: 100%;
  height: 100%;
  display: block;
}

/* ─── Stats Row ─── */
.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
}

.stat-card {
  background: #fff;
  border: 1px solid #E8EEF8;
  border-radius: 16px;
  padding: 18px 22px;
  display: flex;
  align-items: center;
  gap: 14px;
  transition: all 0.22s;
  box-shadow: 0 1px 6px rgba(0, 0, 0, 0.04);
  cursor: default;
}
.stat-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 24px rgba(99, 102, 241, 0.1);
  border-color: rgba(99, 102, 241, 0.2);
}

.stat-icon-wrap {
  width: 46px; height: 46px;
  border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  font-size: 22px;
  flex-shrink: 0;
}

.stat-value {
  font-size: 26px;
  font-weight: 800;
  line-height: 1;
  letter-spacing: -1px;
}

.stat-unit {
  font-size: 13px;
  font-weight: 600;
  margin-left: 1px;
}

.stat-label {
  font-size: 12px;
  color: #64748B;
  margin-top: 4px;
  font-weight: 500;
}

/* ─── Section ─── */
.section { display: flex; flex-direction: column; }

.sec-head { margin-bottom: 16px; }

.sec-title {
  font-size: 18px;
  font-weight: 800;
  color: #111827;
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 5px;
  letter-spacing: -0.3px;
}

.sec-badge {
  font-size: 10px;
  font-weight: 700;
  padding: 3px 8px;
  background: linear-gradient(135deg, #6366F1, #8B5CF6);
  color: #fff;
  border-radius: 6px;
  letter-spacing: 0.5px;
}
.agent-badge { background: linear-gradient(135deg, #10B981, #06B6D4); }
.try-badge   { background: linear-gradient(135deg, #F59E0B, #EF4444); }

.sec-desc {
  font-size: 13px;
  color: #64748B;
  margin: 0;
}

/* ─── 核心功能卡片 ─── */
.feat-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
}

.feat-card {
  background: #fff;
  border: 1px solid #E8EEF8;
  border-radius: 16px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.22s;
  box-shadow: 0 1px 6px rgba(0, 0, 0, 0.04);
  display: flex;
  flex-direction: column;
}
.feat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.09);
  border-color: transparent;
}

.feat-accent {
  height: 3px;
  width: 100%;
  flex-shrink: 0;
}

.feat-body {
  padding: 18px 20px 18px;
  display: flex;
  flex-direction: column;
  flex: 1;
}

.feat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.feat-icon-wrap {
  width: 42px; height: 42px;
  border-radius: 11px;
  display: flex; align-items: center; justify-content: center;
  font-size: 20px;
}

.feat-tag {
  font-size: 10px;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 6px;
  letter-spacing: 0.3px;
}

.feat-title {
  font-size: 15px;
  font-weight: 700;
  margin-bottom: 8px;
  letter-spacing: -0.2px;
}

.feat-desc {
  font-size: 12.5px;
  color: #64748B;
  line-height: 1.65;
  margin-bottom: 14px;
  flex: 1;
}

.feat-go {
  font-size: 12px;
  font-weight: 600;
  opacity: 0;
  transform: translateX(-4px);
  transition: all 0.2s;
}
.feat-card:hover .feat-go {
  opacity: 1;
  transform: translateX(0);
}

/* ─── Agent 矩阵 ─── */
.agent-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.agent-card {
  background: #fff;
  border: 1px solid #E8EEF8;
  border-radius: 14px;
  padding: 16px 14px;
  display: flex;
  align-items: center;
  gap: 10px;
  transition: all 0.22s;
  position: relative;
  overflow: hidden;
  cursor: default;
  box-shadow: 0 1px 6px rgba(0, 0, 0, 0.03);
}
.agent-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 22px rgba(0, 0, 0, 0.08);
  border-color: rgba(99, 102, 241, 0.18);
}

.agent-badge-num {
  position: absolute;
  top: 8px; right: 9px;
  font-size: 9px;
  font-weight: 800;
  padding: 1px 6px;
  border-radius: 4px;
  letter-spacing: 0.3px;
  opacity: 0.9;
}

.agent-icon-wrap {
  width: 38px; height: 38px;
  border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
}

.agent-name {
  font-size: 13px;
  font-weight: 700;
  display: block;
  line-height: 1.2;
}

.agent-desc {
  font-size: 11px;
  color: #94A3B8;
  display: block;
  margin-top: 2px;
}

/* ─── 双列 ─── */
.two-col {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}

.col-card {
  background: #fff;
  border: 1px solid #E8EEF8;
  border-radius: 18px;
  padding: 22px;
  box-shadow: 0 1px 6px rgba(0, 0, 0, 0.04);
}

.col-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.col-title {
  font-size: 14px;
  font-weight: 700;
  color: #111827;
}

.col-link {
  background: none;
  border: none;
  font-size: 12px;
  color: #6366F1;
  font-weight: 600;
  cursor: pointer;
  padding: 0;
  transition: color 0.15s;
}
.col-link:hover { color: #4F46E5; }

/* 资源列表 */
.res-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.res-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 10px;
  border-radius: 10px;
  transition: background 0.15s, transform 0.15s;
  cursor: default;
}
.res-item:hover {
  background: #F8FAFF;
  transform: translateX(2px);
}

.res-icon {
  width: 34px; height: 34px;
  border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  font-size: 16px;
  flex-shrink: 0;
}

.res-body { flex: 1; min-width: 0; }

.res-name {
  font-size: 13px;
  font-weight: 600;
  color: #1E293B;
  display: block;
}

.res-sub {
  font-size: 11px;
  color: #94A3B8;
  display: block;
}

.res-count {
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 8px;
  flex-shrink: 0;
}

/* 画像维度 */
.dim-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 14px;
}

.dim-chip {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 6px 12px;
  border-radius: 20px;
  cursor: default;
  transition: transform 0.15s;
}
.dim-chip:hover { transform: scale(1.05); }

.dim-text {
  font-size: 12.5px;
  font-weight: 600;
}

.dim-note {
  font-size: 12px;
  color: #64748B;
  background: #F8FAFF;
  border-radius: 10px;
  padding: 10px 14px;
  border-left: 3px solid #6366F1;
  line-height: 1.6;
}

/* ─── 快速开始 ─── */
.q-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.q-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 15px 20px;
  background: #fff;
  border: 1px solid #E8EEF8;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
}
.q-item:hover {
  border-color: rgba(99, 102, 241, 0.28);
  box-shadow: 0 4px 16px rgba(99, 102, 241, 0.1);
  transform: translateX(4px);
}

.q-num {
  width: 28px; height: 28px;
  border-radius: 50%;
  color: #fff;
  font-size: 12px;
  font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}

.q-text {
  flex: 1;
  font-size: 14px;
  color: #334155;
  font-weight: 500;
}

.q-arrow {
  color: #CBD5E1;
  font-size: 16px;
  transition: transform 0.2s, color 0.2s;
  flex-shrink: 0;
}
.q-item:hover .q-arrow {
  transform: translateX(4px);
  color: #6366F1;
}

/* ─── Footer ─── */
.home-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 0;
  border-top: 1px solid #E8EEF8;
  flex-wrap: wrap;
  gap: 8px;
}

.footer-l { display: flex; align-items: center; gap: 10px; }
.footer-brand { font-size: 13px; color: #475569; font-weight: 600; }
.footer-ver {
  font-size: 11px; color: #94A3B8; font-family: monospace;
  padding: 2px 7px; background: #F1F5F9; border-radius: 4px;
}

.footer-r { display: flex; gap: 8px; }
.footer-copy { font-size: 12px; color: #94A3B8; }

/* ─── 响应式 ─── */
@media (max-width: 1100px) {
  .hero-graph { width: 300px; height: 240px; }
  .feat-grid { grid-template-columns: repeat(2, 1fr); }
  .agent-grid { grid-template-columns: repeat(3, 1fr); }
  .stats-row { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 860px) {
  .hero { flex-direction: column; padding: 36px 28px; min-height: unset; }
  .hero-content { max-width: 100%; }
  .hero-graph { width: 100%; height: 220px; }
  .hero-title { font-size: 38px; }
  .two-col { grid-template-columns: 1fr; }
  .agent-grid { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 600px) {
  .feat-grid { grid-template-columns: 1fr; }
  .hero-title { font-size: 30px; }
  .hero { padding: 28px 20px; }
}
</style>
