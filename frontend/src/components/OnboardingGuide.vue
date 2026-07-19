<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

const emit = defineEmits<{ (e: 'done'): void }>()

const currentPage = ref(0)

const pages = [
  {
    icon: '🧠',
    title: '认知诊断引擎',
    subtitle: '你不只是在问问题，系统在理解你',
    desc: 'Socrates Cube 通过三层诊断模型，识别你的表层错误、根本原因和认知误区模式，让每次对话都产生真实学习效果。',
    color: '#4f46e5',
    bg: 'linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%)',
    visual: `<svg width="120" height="100" viewBox="0 0 120 100">
      <circle cx="60" cy="50" r="35" fill="none" stroke="#4f46e5" stroke-width="2" opacity="0.3"/>
      <circle cx="60" cy="50" r="25" fill="none" stroke="#4f46e5" stroke-width="2" opacity="0.6"/>
      <circle cx="60" cy="50" r="15" fill="#4f46e5" opacity="0.8"/>
      <text x="60" y="54" text-anchor="middle" fill="white" font-size="10">诊断</text>
    </svg>`,
  },
  {
    icon: '🎯',
    title: '自适应学习路径',
    subtitle: '专属于你的知识图谱导航',
    desc: '基于你的 8 维能力画像，系统自动规划最短学习路径。哪里薄弱补哪里，循序渐进，从概念理解到协议分析全面提升。',
    color: '#0891b2',
    bg: 'linear-gradient(135deg, #ecfeff 0%, #cffafe 100%)',
    visual: `<svg width="120" height="100" viewBox="0 0 120 100">
      <path d="M20,80 L45,50 L70,60 L95,20" fill="none" stroke="#0891b2" stroke-width="3" stroke-linecap="round"/>
      <circle cx="20" cy="80" r="5" fill="#0891b2"/>
      <circle cx="45" cy="50" r="5" fill="#0891b2"/>
      <circle cx="70" cy="60" r="5" fill="#0891b2"/>
      <circle cx="95" cy="20" r="5" fill="#0891b2"/>
    </svg>`,
  },
  {
    icon: '🤖',
    title: '多角色 AI 助手',
    subtitle: '选择你喜欢的学习方式',
    desc: '严教授用专业框架讲清原理，学长/学姐用类比让概念变有趣，职场导师结合实战场景指导你。不同情境选择不同智能体，学习效率翻倍。',
    color: '#7c3aed',
    bg: 'linear-gradient(135deg, #f5f3ff 0%, #ede9fe 100%)',
    visual: `<svg width="120" height="100" viewBox="0 0 120 100">
      <rect x="20" y="30" width="25" height="30" rx="5" fill="#7c3aed" opacity="0.8"/>
      <rect x="47" y="20" width="25" height="40" rx="5" fill="#7c3aed"/>
      <rect x="74" y="35" width="25" height="25" rx="5" fill="#7c3aed" opacity="0.6"/>
      <text x="32" y="49" text-anchor="middle" fill="white" font-size="8">教授</text>
      <text x="59" y="44" text-anchor="middle" fill="white" font-size="8">学长</text>
      <text x="86" y="51" text-anchor="middle" fill="white" font-size="8">专家</text>
    </svg>`,
  },
  {
    icon: '📊',
    title: '能力画像系统',
    subtitle: '看见你自己的成长',
    desc: '实时追踪概念理解、协议分析、计算能力等 8 个维度，生成个性化能力雷达图。每次对话后自动更新，让进步看得见。',
    color: '#059669',
    bg: 'linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%)',
    visual: `<svg width="120" height="100" viewBox="0 0 120 100">
      <polygon points="60,10 85,35 85,65 60,90 35,65 35,35" fill="none" stroke="#059669" stroke-width="2" opacity="0.3"/>
      <polygon points="60,22 76,42 76,58 60,78 44,58 44,42" fill="#059669" opacity="0.15"/>
      <polygon points="60,34 68,49 68,51 60,66 52,51 52,49" fill="#059669" opacity="0.5"/>
    </svg>`,
  },
  {
    icon: '⚔️',
    title: 'Challenger 检验',
    subtitle: '真正的理解需要被检验',
    desc: '学完知识点后，Challenger Agent 会根据你的误区模式生成专项对抗题。答对了才算真的懂，让学习闭环真正闭合。',
    color: '#dc2626',
    bg: 'linear-gradient(135deg, #fff1f2 0%, #ffe4e6 100%)',
    visual: `<svg width="120" height="100" viewBox="0 0 120 100">
      <path d="M50,20 L50,65 M70,20 L70,65" stroke="#dc2626" stroke-width="4" stroke-linecap="round"/>
      <path d="M30,35 Q50,25 60,40 Q70,25 90,35" fill="none" stroke="#dc2626" stroke-width="2"/>
      <rect x="45" y="65" width="30" height="10" rx="3" fill="#dc2626" opacity="0.8"/>
    </svg>`,
  },
  {
    icon: '🚀',
    title: '开始你的学习之旅',
    subtitle: '一切准备就绪',
    desc: '接下来，告诉我们你的学习目标和背景，系统将为你生成专属的摸底测试，快速建立你的知识基线。整个过程只需 5 分钟！',
    color: '#f59e0b',
    bg: 'linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%)',
    visual: `<svg width="120" height="100" viewBox="0 0 120 100">
      <path d="M40,80 L60,20 L80,80 Z" fill="#f59e0b" opacity="0.8"/>
      <circle cx="60" cy="55" r="8" fill="white"/>
      <path d="M30,70 Q60,40 90,70" fill="none" stroke="#f59e0b" stroke-width="2" stroke-dasharray="4,3" opacity="0.6"/>
    </svg>`,
  },
]

const totalPages = pages.length
const currentPageData = computed(() => pages[currentPage.value])
const progress = computed(() => ((currentPage.value + 1) / totalPages) * 100)

// 音效（使用 Web Audio API，无需外部库）
let audioCtx: AudioContext | null = null

function playFlipSound() {
  try {
    if (!audioCtx) audioCtx = new (window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext)()
    const osc = audioCtx.createOscillator()
    const gain = audioCtx.createGain()
    osc.connect(gain)
    gain.connect(audioCtx.destination)
    osc.frequency.setValueAtTime(800, audioCtx.currentTime)
    osc.frequency.exponentialRampToValueAtTime(400, audioCtx.currentTime + 0.15)
    gain.gain.setValueAtTime(0.15, audioCtx.currentTime)
    gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.15)
    osc.start(audioCtx.currentTime)
    osc.stop(audioCtx.currentTime + 0.15)
  } catch { /* ignore */ }
}

function playSuccessSound() {
  try {
    if (!audioCtx) audioCtx = new (window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext)()
    const notes = [523, 659, 784]
    notes.forEach((freq, i) => {
      const osc = audioCtx!.createOscillator()
      const gain = audioCtx!.createGain()
      osc.connect(gain)
      gain.connect(audioCtx!.destination)
      osc.frequency.value = freq
      osc.type = 'sine'
      gain.gain.setValueAtTime(0, audioCtx!.currentTime + i * 0.12)
      gain.gain.linearRampToValueAtTime(0.1, audioCtx!.currentTime + i * 0.12 + 0.05)
      gain.gain.exponentialRampToValueAtTime(0.001, audioCtx!.currentTime + i * 0.12 + 0.3)
      osc.start(audioCtx!.currentTime + i * 0.12)
      osc.stop(audioCtx!.currentTime + i * 0.12 + 0.3)
    })
  } catch { /* ignore */ }
}

const isAnimating = ref(false)
const slideDirection = ref<'left' | 'right'>('left')

async function goNext() {
  if (isAnimating.value) return
  if (currentPage.value < totalPages - 1) {
    isAnimating.value = true
    slideDirection.value = 'left'
    playFlipSound()
    setTimeout(() => {
      currentPage.value++
      isAnimating.value = false
    }, 300)
  } else {
    playSuccessSound()
    setTimeout(() => emit('done'), 400)
  }
}

function goPrev() {
  if (currentPage.value > 0) {
    slideDirection.value = 'right'
    playFlipSound()
    setTimeout(() => { currentPage.value-- }, 150)
  }
}

onMounted(() => {
  // 键盘导航
  document.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowRight' || e.key === ' ') goNext()
    if (e.key === 'ArrowLeft') goPrev()
    if (e.key === 'Escape') emit('done')
  })
})
</script>

<template>
  <div class="onboarding-overlay" @click.self="$emit('done')">
    <div class="onboarding-card">
      <!-- 顶部进度 -->
      <div class="top-bar">
        <div class="progress-bar">
          <div class="progress-fill" :style="`width: ${progress}%`"></div>
        </div>
        <span class="page-indicator">{{ currentPage + 1 }} / {{ totalPages }}</span>
        <button class="skip-btn" @click="$emit('done')">跳过</button>
      </div>

      <!-- 页面内容 -->
      <div
        class="page-content"
        :class="[isAnimating ? 'slide-out' : 'slide-in']"
        :style="`background: ${currentPageData.bg}`"
      >
        <!-- 视觉图形 -->
        <div class="visual-area" v-html="currentPageData.visual"></div>

        <!-- 文字内容 -->
        <div class="text-area">
          <div class="page-icon">{{ currentPageData.icon }}</div>
          <h2 class="page-title" :style="`color: ${currentPageData.color}`">
            {{ currentPageData.title }}
          </h2>
          <p class="page-subtitle">{{ currentPageData.subtitle }}</p>
          <p class="page-desc">{{ currentPageData.desc }}</p>
        </div>
      </div>

      <!-- 底部导航 -->
      <div class="nav-area">
        <!-- 圆点指示器 -->
        <div class="dots">
          <span
            v-for="i in totalPages"
            :key="i"
            class="dot"
            :class="{ active: i - 1 === currentPage }"
            :style="i - 1 === currentPage ? `background: ${currentPageData.color}` : ''"
            @click="currentPage = i - 1; playFlipSound()"
          ></span>
        </div>

        <div class="btn-group">
          <button v-if="currentPage > 0" class="nav-btn prev-btn" @click="goPrev">
            ← 上一步
          </button>
          <button
            class="nav-btn next-btn"
            :style="`background: ${currentPageData.color}`"
            @click="goNext"
          >
            {{ currentPage === totalPages - 1 ? '开始学习 🚀' : '下一步 →' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.onboarding-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.6);
  backdrop-filter: blur(4px);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.onboarding-card {
  width: 100%;
  max-width: 520px;
  background: white;
  border-radius: 24px;
  overflow: hidden;
  box-shadow: 0 24px 80px rgba(0,0,0,0.25);
  display: flex;
  flex-direction: column;
}

/* 顶部进度条 */
.top-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 20px;
  background: white;
  border-bottom: 1px solid #f1f5f9;
}
.progress-bar {
  flex: 1;
  height: 4px;
  background: #e2e8f0;
  border-radius: 2px;
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #4f46e5, #7c3aed);
  border-radius: 2px;
  transition: width 0.4s ease;
}
.page-indicator { font-size: 12px; color: #94a3b8; white-space: nowrap; }
.skip-btn {
  font-size: 12px; color: #94a3b8; background: none;
  border: none; cursor: pointer; padding: 4px 8px;
  border-radius: 6px; transition: all 0.2s;
}
.skip-btn:hover { background: #f1f5f9; color: #4f46e5; }

/* 页面内容 */
.page-content {
  padding: 36px 32px 28px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  min-height: 340px;
  transition: opacity 0.3s, transform 0.3s;
}
.slide-out { opacity: 0; transform: translateX(-30px); }
.slide-in  { opacity: 1; transform: translateX(0); }

.visual-area svg { filter: drop-shadow(0 4px 12px rgba(0,0,0,0.1)); }

.text-area { text-align: center; }
.page-icon { font-size: 36px; margin-bottom: 12px; }
.page-title { font-size: 22px; font-weight: 800; margin: 0 0 6px; }
.page-subtitle { font-size: 15px; color: #475569; font-weight: 600; margin: 0 0 12px; }
.page-desc { font-size: 14px; color: #64748b; line-height: 1.7; margin: 0; }

/* 底部导航 */
.nav-area {
  padding: 20px 24px;
  background: white;
  border-top: 1px solid #f1f5f9;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.dots { display: flex; gap: 8px; }
.dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: #e2e8f0; cursor: pointer;
  transition: all 0.3s;
}
.dot.active { width: 24px; border-radius: 4px; }

.btn-group { display: flex; gap: 12px; width: 100%; }
.nav-btn {
  flex: 1; padding: 12px;
  border: none; border-radius: 12px;
  font-size: 14px; font-weight: 600;
  cursor: pointer; transition: all 0.2s;
}
.prev-btn {
  background: #f1f5f9; color: #475569;
  flex: 0.5;
}
.prev-btn:hover { background: #e2e8f0; }
.next-btn {
  color: white;
}
.next-btn:hover { filter: brightness(1.08); transform: translateY(-1px); }
</style>
