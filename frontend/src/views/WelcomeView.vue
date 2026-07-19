<template>
  <div class="welcome-page">
    <!-- 动态网络拓扑背景 -->
    <canvas ref="bgCanvas" class="bg-canvas"></canvas>

    <!-- 顶部残留条（模拟过场动画收回后的残留）-->
    <div class="panel-remnant panel-top">
      <div class="remnant-inner">
        <span class="remnant-logo">◆</span>
        <span class="remnant-title">用户指南 · Socrates Cube</span>
        <span class="remnant-version">v1.0</span>
      </div>
    </div>

    <!-- 左右浮动协议标签 -->
    <span
      v-for="tag in decorTags"
      :key="tag.label"
      class="decor-tag"
      :style="tag.style"
    >{{ tag.label }}</span>

    <!-- 中央内容区 -->
    <div class="center-area">
      <!-- 翻书组件 -->
      <div class="flipbook-area">
        <FlipBookViewer
          :pages="manualPages"
          @page-change="() => {}"
          @last-page-reached="handleLastPage"
        />
      </div>

      <!-- 对话气泡（欢迎语）-->
      <div class="dialog-bubble" :class="{ 'bubble-visible': bubbleVisible }">
        <div class="bubble-inner">
          <span class="bubble-cursor-icon">▶</span>
          <span class="bubble-text">{{ displayedText }}<span class="cursor-blink" v-if="isTyping">|</span></span>
        </div>
      </div>

      <!-- 进入系统按钮 -->
      <Transition name="fade-up">
        <button v-if="reachedLastPage" class="enter-btn" @click="enterSystem">
          <span class="enter-icon">⟶</span> 进入系统
        </button>
      </Transition>
    </div>

    <!-- 底部残留条 -->
    <div class="panel-remnant panel-bottom">
      <div class="remnant-bottom-inner">
        <button class="skip-btn" @click="skipManual">跳过手册</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/userStore'
import FlipBookViewer from '@/components/FlipBook/FlipBookViewer.vue'
import { manualPages } from '@/data/userManualContent'

const router = useRouter()
const userStore = useUserStore()
const reachedLastPage = ref(false)
const bgCanvas = ref<HTMLCanvasElement | null>(null)
const bubbleVisible = ref(false)
const displayedText = ref('')
const isTyping = ref(false)

// ── 打字机效果 ────────────────────────────────────────────────────
const welcomeText = '欢迎使用 Socrates Cube——AI 驱动的计算机网络自适应学习平台！请翻阅用户手册，快速了解系统核心功能。'
let typeTimer: ReturnType<typeof setTimeout> | null = null

function startTypewriter() {
  bubbleVisible.value = true
  isTyping.value = true
  displayedText.value = ''
  let i = 0
  const tick = () => {
    if (i < welcomeText.length) {
      displayedText.value += welcomeText[i++]
      typeTimer = setTimeout(tick, 38)
    } else {
      isTyping.value = false
    }
  }
  typeTimer = setTimeout(tick, 600)
}

// ── 背景网络拓扑动画 ──────────────────────────────────────────────
interface TopoNode { x: number; y: number; vx: number; vy: number; r: number; hue: number }
let animId: number | null = null

function initBgAnim() {
  const canvas = bgCanvas.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  let w = canvas.width = canvas.offsetWidth
  let h = canvas.height = canvas.offsetHeight
  const nodes: TopoNode[] = []
  for (let i = 0; i < 40; i++) {
    nodes.push({
      x: Math.random() * w, y: Math.random() * h,
      vx: (Math.random() - 0.5) * 0.35, vy: (Math.random() - 0.5) * 0.35,
      r: 1.5 + Math.random() * 2, hue: 190 + Math.random() * 70,
    })
  }
  const draw = () => {
    ctx.clearRect(0, 0, w, h)
    for (const n of nodes) {
      n.x += n.vx; n.y += n.vy
      if (n.x < 0 || n.x > w) n.vx *= -1
      if (n.y < 0 || n.y > h) n.vy *= -1
    }
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const dx = nodes[i].x - nodes[j].x
        const dy = nodes[i].y - nodes[j].y
        const d = Math.sqrt(dx * dx + dy * dy)
        if (d < 130) {
          ctx.strokeStyle = `rgba(99,202,246,${(1 - d / 130) * 0.25})`
          ctx.lineWidth = 0.6
          ctx.beginPath()
          ctx.moveTo(nodes[i].x, nodes[i].y)
          ctx.lineTo(nodes[j].x, nodes[j].y)
          ctx.stroke()
        }
      }
    }
    for (const n of nodes) {
      ctx.beginPath()
      ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2)
      ctx.fillStyle = `hsla(${n.hue},70%,65%,0.7)`
      ctx.shadowColor = `hsla(${n.hue},80%,60%,0.5)`
      ctx.shadowBlur = 5
      ctx.fill()
      ctx.shadowBlur = 0
    }
    animId = requestAnimationFrame(draw)
  }
  draw()
  const ro = new ResizeObserver(() => {
    w = canvas.width = canvas.offsetWidth
    h = canvas.height = canvas.offsetHeight
  })
  ro.observe(canvas)
}

function handleLastPage() {
  reachedLastPage.value = true
}

function enterSystem() {
  userStore.manualRead = true
  router.push('/')
}

function skipManual() {
  userStore.manualRead = true
  router.push('/')
}

onMounted(() => {
  nextTick(() => {
    initBgAnim()
    startTypewriter()
  })
})

onUnmounted(() => {
  if (animId) cancelAnimationFrame(animId)
  if (typeTimer) clearTimeout(typeTimer)
})

// 装饰协议标签
const decorTags = [
  { label: 'TCP/IP',  style: 'top:18%; left:3%' },
  { label: 'UDP',     style: 'top:38%; left:5%' },
  { label: 'HTTP/3',  style: 'top:62%; left:3%' },
  { label: 'BGP',     style: 'top:78%; left:6%' },
  { label: 'TLS 1.3', style: 'top:22%; right:4%' },
  { label: 'QUIC',    style: 'top:45%; right:3%' },
  { label: 'DNS',     style: 'top:68%; right:5%' },
  { label: 'OSPF',    style: 'top:82%; right:7%' },
]
</script>

<style scoped>
/* ── 页面根 ───────────────────────────────────────── */
.welcome-page {
  position: fixed;
  inset: 0;
  background: linear-gradient(160deg, #050e24 0%, #0d1b3e 50%, #080d1e 100%);
  display: flex;
  flex-direction: column;
  align-items: center;
  overflow: hidden;
  z-index: 1000;
}

/* ── 背景 Canvas ───────────────────────────────────── */
.bg-canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
}

/* ── 顶部残留条 ──────────────────────────────────── */
.panel-remnant {
  position: fixed;
  left: 0;
  right: 0;
  z-index: 20;
}

.panel-top {
  top: 0;
  height: 64px;
  background: linear-gradient(160deg, #051b3e 0%, #0a1a4e 100%);
  clip-path: polygon(
    0 0, 100% 0, 100% calc(100% - 18px),
    95% 100%, 90% calc(100% - 12px), 85% 100%, 80% calc(100% - 8px),
    75% 100%, 70% calc(100% - 16px), 65% 100%, 60% calc(100% - 10px),
    55% 100%, 50% calc(100% - 18px), 45% 100%, 40% calc(100% - 6px),
    35% 100%, 30% calc(100% - 14px), 25% 100%, 20% calc(100% - 12px),
    15% 100%, 10% calc(100% - 8px), 5% 100%, 0 calc(100% - 18px)
  );
  animation: panelSlideDown 0.6s cubic-bezier(0.34,1.56,0.64,1) both;
}

@keyframes panelSlideDown {
  from { transform: translateY(-100%); opacity: 0; }
  to   { transform: translateY(0); opacity: 1; }
}

.remnant-inner {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  height: 44px;
  padding: 0 24px;
}

.remnant-logo {
  font-size: 16px;
  color: #a78bfa;
  filter: drop-shadow(0 0 6px rgba(167,139,250,0.7));
}

.remnant-title {
  font-size: 15px;
  font-weight: 700;
  color: #f1f5f9;
  letter-spacing: 1.5px;
}

.remnant-version {
  font-size: 11px;
  color: rgba(99,202,246,0.7);
  border: 1px solid rgba(99,202,246,0.3);
  border-radius: 4px;
  padding: 1px 6px;
  font-family: monospace;
}

/* ── 底部残留条 ──────────────────────────────────── */
.panel-bottom {
  bottom: 0;
  height: 56px;
  background: linear-gradient(20deg, #0d1b3e 0%, #1a1050 100%);
  clip-path: polygon(
    0 18px, 5% 0, 10% 10px, 15% 0, 20% 14px,
    25% 0, 30% 16px, 35% 0, 40% 8px, 45% 0,
    50% 18px, 55% 0, 60% 12px, 65% 0, 70% 16px,
    75% 0, 80% 10px, 85% 0, 90% 14px, 95% 0,
    100% 18px, 100% 100%, 0 100%
  );
  animation: panelSlideUp 0.6s cubic-bezier(0.34,1.56,0.64,1) both;
}

@keyframes panelSlideUp {
  from { transform: translateY(100%); opacity: 0; }
  to   { transform: translateY(0); opacity: 1; }
}

.remnant-bottom-inner {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding-top: 16px;
}

/* ── 中央内容区 ──────────────────────────────────── */
.center-area {
  position: relative;
  z-index: 10;
  flex: 1;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 64px 0 56px;
  gap: 16px;
  min-height: 0;
}

/* ── 翻书区域 ────────────────────────────────────── */
.flipbook-area {
  flex: 1;
  width: 64vw;
  max-width: 900px;
  min-height: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* ── 对话气泡 ────────────────────────────────────── */
.dialog-bubble {
  width: 64vw;
  max-width: 860px;
  opacity: 0;
  transform: translateY(12px);
  transition: opacity 0.5s ease, transform 0.5s cubic-bezier(0.34,1.56,0.64,1);
}
.dialog-bubble.bubble-visible {
  opacity: 1;
  transform: translateY(0);
}

.bubble-inner {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(99,202,246,0.2);
  border-radius: 12px;
  padding: 14px 18px;
  backdrop-filter: blur(10px);
  min-height: 70px;
}

.bubble-cursor-icon {
  font-size: 13px;
  color: #22d3ee;
  flex-shrink: 0;
  margin-top: 2px;
  filter: drop-shadow(0 0 4px rgba(34,211,238,0.7));
}

.bubble-text {
  font-size: 14px;
  color: rgba(226,232,240,0.9);
  line-height: 1.7;
  font-family: 'JetBrains Mono', 'Consolas', monospace;
}

.cursor-blink {
  display: inline-block;
  color: #22d3ee;
  font-weight: 700;
  animation: blink 0.8s step-end infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

/* ── 进入系统按钮 ────────────────────────────────── */
.enter-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 36px;
  background: linear-gradient(135deg, #3b82f6, #6366f1, #8b5cf6);
  background-size: 200% 100%;
  border: none;
  border-radius: 30px;
  color: #fff;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  letter-spacing: 1px;
  box-shadow: 0 4px 24px rgba(99,102,241,0.45);
  transition: all 0.25s cubic-bezier(0.4,0,0.2,1);
  animation: btnGlow 3s ease-in-out infinite;
}

.enter-btn:hover {
  transform: translateY(-2px) scale(1.04);
  box-shadow: 0 8px 36px rgba(99,102,241,0.65);
  background-position: 100% 0;
}

@keyframes btnGlow {
  0%, 100% { box-shadow: 0 4px 24px rgba(99,102,241,0.45); }
  50%       { box-shadow: 0 4px 36px rgba(99,102,241,0.7); }
}

.enter-icon {
  font-size: 18px;
}

/* ── 跳过按钮 ────────────────────────────────────── */
.skip-btn {
  background: none;
  border: none;
  color: rgba(255,255,255,0.45);
  font-size: 12px;
  cursor: pointer;
  padding: 4px 10px;
  text-decoration: underline;
  text-underline-offset: 3px;
  transition: color 0.2s;
  letter-spacing: 0.5px;
}
.skip-btn:hover { color: rgba(255,255,255,0.85); }

/* ── 浮动协议标签 ────────────────────────────────── */
.decor-tag {
  position: absolute;
  font-size: 13px;
  font-weight: 700;
  color: rgba(99,202,246,0.22);
  letter-spacing: 1.5px;
  pointer-events: none;
  user-select: none;
  animation: tagFloat 7s ease-in-out infinite;
  z-index: 5;
}
.decor-tag:nth-child(odd)  { animation-delay: -3s; }
.decor-tag:nth-child(3n)   { animation-delay: -1.5s; }

@keyframes tagFloat {
  0%, 100% { transform: translateY(0); opacity: 0.22; }
  50%       { transform: translateY(-10px); opacity: 0.4; }
}

/* ── Transition ──────────────────────────────────── */
.fade-up-enter-active { transition: all 0.45s cubic-bezier(0.34,1.56,0.64,1); }
.fade-up-leave-active { transition: all 0.3s cubic-bezier(0.4,0,0.2,1); }
.fade-up-enter-from  { opacity: 0; transform: translateY(16px); }
.fade-up-leave-to    { opacity: 0; transform: translateY(16px); }
</style>
