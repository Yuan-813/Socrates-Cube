<template>
  <div v-if="active" class="split-screen-overlay">
    <!-- 上半屏 -->
    <div class="split-half split-top" :class="topClass">
      <div class="split-top-content" :class="{ 'content-visible': contentVisible }">
        <!-- Logo 标识 -->
        <div class="brand-row">
          <span class="brand-cube">◆</span>
          <span class="brand-name">Socrates Cube</span>
        </div>
        <!-- 项目简介 -->
        <p class="intro-text">
          多智能体自适应计算机网络学习系统 · 认知科学与人工智能的融合探索
        </p>
        <!-- TCP/IP 协议栈彩色条带 -->
        <div class="osi-layers">
          <div class="osi-layer" style="background:linear-gradient(90deg,#a855f7,#c084fc)">应用层 · HTTP · DNS · SMTP</div>
          <div class="osi-layer" style="background:linear-gradient(90deg,#6366f1,#818cf8)">传输层 · TCP · UDP · QUIC</div>
          <div class="osi-layer" style="background:linear-gradient(90deg,#3b82f6,#60a5fa)">网络层 · IP · ICMP · BGP</div>
          <div class="osi-layer" style="background:linear-gradient(90deg,#06b6d4,#22d3ee)">数据链路层 · Ethernet · ARP</div>
          <div class="osi-layer" style="background:linear-gradient(90deg,#10b981,#34d399)">物理层 · 信号传输 · 编码</div>
        </div>
      </div>
    </div>

    <!-- 下半屏 -->
    <div class="split-half split-bottom" :class="bottomClass">
      <div class="split-bottom-content" :class="{ 'content-visible': contentVisible }">
        <!-- 主标语 -->
        <p class="tagline">AI 驱动 · 自适应学习</p>
        <!-- 三大核心能力气泡卡片 -->
        <div class="feature-cards">
          <div class="feat-card">
            <div class="feat-icon-wrap">🧠</div>
            <div class="feat-info">
              <span class="feat-title">认知诊断</span>
              <span class="feat-desc">三层诊断引擎，精准定位知识盲区</span>
            </div>
          </div>
          <div class="feat-card">
            <div class="feat-icon-wrap">🗺️</div>
            <div class="feat-info">
              <span class="feat-title">自适应路径</span>
              <span class="feat-desc">知识图谱驱动，个性化学习规划</span>
            </div>
          </div>
          <div class="feat-card">
            <div class="feat-icon-wrap">🤖</div>
            <div class="feat-info">
              <span class="feat-title">多Agent协同</span>
              <span class="feat-desc">苏格拉底式启发，多角色AI教学</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { prefersReducedMotion } from '@/utils/featureDetection'

const emit = defineEmits<{
  done: []
}>()

const active = ref(true)
const topClass = ref('phase-enter')
const bottomClass = ref('phase-enter')
const contentVisible = ref(false)

onMounted(() => {
  if (prefersReducedMotion()) {
    topClass.value = 'reduced-enter'
    bottomClass.value = 'reduced-enter'
    contentVisible.value = true
    setTimeout(() => {
      topClass.value = 'reduced-leave'
      bottomClass.value = 'reduced-leave'
    }, 600)
    setTimeout(() => {
      active.value = false
      emit('done')
    }, 1000)
    return
  }

  // 阶段1 (0-800ms): 上下半屏滑入
  requestAnimationFrame(() => {
    topClass.value = 'phase-visible'
    bottomClass.value = 'phase-visible'
  })

  // 阶段2 (800ms): 内容飘入
  setTimeout(() => {
    contentVisible.value = true
  }, 800)

  // 阶段3 (1800-2600ms): 上下半屏滑出
  setTimeout(() => {
    topClass.value = 'phase-leave'
    bottomClass.value = 'phase-leave'
  }, 1800)

  // 阶段4: 完全退出
  setTimeout(() => {
    active.value = false
    emit('done')
  }, 2800)
})
</script>

<style scoped>
.split-screen-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  pointer-events: none;
}

/* ===== 上半屏 ===== */
.split-top {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 50%;
  background: linear-gradient(160deg, #051b3e 0%, #0a1a4e 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  will-change: transform, opacity;
  clip-path: polygon(
    0 0, 100% 0, 100% calc(100% - 20px),
    95% 100%, 90% calc(100% - 15px), 85% 100%, 80% calc(100% - 10px),
    75% 100%, 70% calc(100% - 18px), 65% 100%, 60% calc(100% - 12px),
    55% 100%, 50% calc(100% - 20px), 45% 100%, 40% calc(100% - 8px),
    35% 100%, 30% calc(100% - 16px), 25% 100%, 20% calc(100% - 14px),
    15% 100%, 10% calc(100% - 10px), 5% 100%, 0 calc(100% - 20px)
  );
}

/* ===== 下半屏 ===== */
.split-bottom {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 50%;
  background: linear-gradient(20deg, #0d1b3e 0%, #1a1050 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  will-change: transform, opacity;
  clip-path: polygon(
    0 20px, 5% 0, 10% 10px, 15% 0, 20% 14px,
    25% 0, 30% 16px, 35% 0, 40% 8px, 45% 0,
    50% 20px, 55% 0, 60% 12px, 65% 0, 70% 18px,
    75% 0, 80% 10px, 85% 0, 90% 15px, 95% 0,
    100% 20px, 100% 100%, 0 100%
  );
}

/* ===== 阶段动画类 ===== */
.split-top.phase-enter {
  transform: translateY(-100%);
  opacity: 0;
}

.split-top.phase-visible {
  transform: translateY(0);
  opacity: 1;
  transition: transform 800ms cubic-bezier(0.34, 1.56, 0.64, 1), opacity 800ms ease;
}

.split-top.phase-leave {
  transform: translateY(-100%);
  opacity: 0;
  transition: transform 800ms cubic-bezier(0.4, 0, 0.2, 1), opacity 800ms ease;
}

.split-bottom.phase-enter {
  transform: translateY(100%);
  opacity: 0;
}

.split-bottom.phase-visible {
  transform: translateY(0);
  opacity: 1;
  transition: transform 800ms cubic-bezier(0.34, 1.56, 0.64, 1), opacity 800ms ease;
}

.split-bottom.phase-leave {
  transform: translateY(100%);
  opacity: 0;
  transition: transform 800ms cubic-bezier(0.4, 0, 0.2, 1), opacity 800ms ease;
}

/* ===== 降级动画 ===== */
.split-top.reduced-enter,
.split-bottom.reduced-enter {
  opacity: 1;
  transform: none;
  transition: opacity 400ms ease;
}

.split-top.reduced-leave,
.split-bottom.reduced-leave {
  opacity: 0;
  transform: none;
  transition: opacity 400ms ease;
}

/* ===== 上半屏内容 ===== */
.split-top-content {
  text-align: center;
  padding: 20px 40px;
  max-width: 700px;
  width: 100%;
  opacity: 0;
  transform: translateY(-16px);
  transition: opacity 500ms ease 0ms, transform 500ms cubic-bezier(0.34,1.56,0.64,1) 0ms;
}
.split-top-content.content-visible {
  opacity: 1;
  transform: translateY(0);
}

.brand-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  margin-bottom: 8px;
}

.brand-cube {
  font-size: 22px;
  color: #a78bfa;
  filter: drop-shadow(0 0 10px rgba(167,139,250,0.7));
}

.brand-name {
  font-size: 22px;
  font-weight: 700;
  color: #f1f5f9;
  letter-spacing: 1px;
}

.intro-text {
  font-size: 13px;
  color: rgba(147,197,253,0.8);
  margin: 0 0 14px;
  letter-spacing: 0.3px;
}

.osi-layers {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-width: 400px;
  margin: 0 auto;
}

.osi-layer {
  padding: 6px 16px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  color: rgba(255,255,255,0.92);
  text-align: center;
  letter-spacing: 0.5px;
}

/* ===== 下半屏内容 ===== */
.split-bottom-content {
  text-align: center;
  padding: 30px 40px 20px;
  max-width: 700px;
  width: 100%;
  opacity: 0;
  transform: translateY(16px);
  transition: opacity 500ms ease 100ms, transform 500ms cubic-bezier(0.34,1.56,0.64,1) 100ms;
}
.split-bottom-content.content-visible {
  opacity: 1;
  transform: translateY(0);
}

.tagline {
  font-size: 14px;
  color: #a78bfa;
  font-weight: 600;
  letter-spacing: 2px;
  margin: 0 0 16px;
  text-transform: uppercase;
}

.feature-cards {
  display: flex;
  gap: 14px;
  justify-content: center;
  flex-wrap: wrap;
}

.feat-card {
  display: flex;
  align-items: center;
  gap: 10px;
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(139,92,246,0.25);
  border-radius: 12px;
  padding: 10px 16px;
  min-width: 170px;
  backdrop-filter: blur(8px);
}

.feat-icon-wrap {
  font-size: 22px;
  flex-shrink: 0;
}

.feat-info {
  display: flex;
  flex-direction: column;
  text-align: left;
}

.feat-title {
  font-size: 13px;
  font-weight: 600;
  color: #f1f5f9;
  line-height: 1.2;
}

.feat-desc {
  font-size: 11px;
  color: rgba(148,163,184,0.8);
  margin-top: 2px;
  line-height: 1.4;
}
</style>
