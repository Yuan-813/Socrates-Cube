<template>
  <Transition name="notify-slide">
    <div v-if="show" class="notify-container">
      <div class="notify-card">
        <!-- 左侧网络图标 -->
        <div class="net-icon">
          <svg viewBox="0 0 24 24" fill="none" width="22" height="22">
            <circle cx="12" cy="5"  r="2.5" stroke="#60d5fa" stroke-width="1.5"/>
            <circle cx="5"  cy="18" r="2.5" stroke="#60d5fa" stroke-width="1.5"/>
            <circle cx="19" cy="18" r="2.5" stroke="#60d5fa" stroke-width="1.5"/>
            <line x1="12" y1="7.5" x2="6.8"  y2="15.8" stroke="#60d5fa" stroke-width="1.2" stroke-dasharray="2 2"/>
            <line x1="12" y1="7.5" x2="17.2" y2="15.8" stroke="#60d5fa" stroke-width="1.2" stroke-dasharray="2 2"/>
            <line x1="7.5" y1="18" x2="16.5" y2="18" stroke="#60d5fa" stroke-width="1.2" stroke-dasharray="2 2"/>
          </svg>
        </div>

        <!-- 文案内容 -->
        <div class="notify-content">
          <p class="notify-title">连接已建立 &mdash; 欢迎加入 Socrates Cube</p>
          <p class="notify-subtitle">正在初始化学习环境...</p>
        </div>

        <!-- 协议标签 -->
        <div class="protocol-tags">
          <span class="protocol-tag">TCP</span>
          <span class="protocol-tag">HTTP</span>
        </div>

        <!-- 右侧 Ping 活动指示器 -->
        <div class="ping-wrap">
          <span class="ping-dot ping-dot-1"></span>
          <span class="ping-dot ping-dot-2"></span>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{ visible: boolean }>()
const emit  = defineEmits<{ close: [] }>()

const show = ref(false)

watch(() => props.visible, (val) => {
  if (val) {
    show.value = true
    setTimeout(() => { show.value = false }, 3000)
    setTimeout(() => { emit('close') }, 3400)
  }
})
</script>

<style scoped>
.notify-container {
  position: fixed;
  top: 28px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 9998;
}

.notify-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 24px;
  border-radius: 18px;
  background: linear-gradient(135deg, rgba(30,58,138,0.93), rgba(79,70,229,0.93));
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  white-space: nowrap;
  position: relative;
  overflow: hidden;
  /* 外发光边框 */
  box-shadow:
    0 0 0 1px rgba(99,202,246,0.3),
    0 8px 32px rgba(59,130,246,0.35),
    0 2px 8px rgba(0,0,0,0.3);
}

/* 顶部高光线 */
.notify-card::before {
  content: '';
  position: absolute;
  top: 0; left: 16px; right: 16px;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(99,202,246,0.6), transparent);
}

/* 底部扫光动画 */
.notify-card::after {
  content: '';
  position: absolute;
  top: 0; left: -100%;
  width: 60%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.06), transparent);
  animation: scanLight 2.5s linear infinite;
}

@keyframes scanLight {
  0%   { left: -100%; }
  100% { left: 160%; }
}

/* 左侧网络图标 */
.net-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: rgba(99,202,246,0.12);
  border: 1px solid rgba(99,202,246,0.25);
  flex-shrink: 0;
  filter: drop-shadow(0 0 6px rgba(96,213,250,0.4));
}

/* 文案 */
.notify-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.notify-title {
  font-size: 15px;
  font-weight: 700;
  color: #ffffff;
  margin: 0;
  letter-spacing: 0.3px;
}

.notify-subtitle {
  font-size: 12px;
  color: rgba(147,197,253,0.85);
  margin: 0;
  font-family: 'JetBrains Mono', monospace;
}

/* 协议标签 */
.protocol-tags {
  display: flex;
  gap: 6px;
}

.protocol-tag {
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
  color: rgba(99,202,246,0.9);
  background: rgba(99,202,246,0.1);
  border: 1px solid rgba(99,202,246,0.25);
  font-family: monospace;
  letter-spacing: 0.5px;
}

/* 右侧 Ping 圆点 */
.ping-wrap {
  display: flex;
  flex-direction: column;
  gap: 5px;
  align-items: center;
  padding-left: 4px;
}

.ping-dot {
  display: block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #22c55e;
  box-shadow: 0 0 6px rgba(34,197,94,0.7);
}

.ping-dot-1 {
  animation: pingPulse 1.2s ease-in-out infinite;
}

.ping-dot-2 {
  animation: pingPulse 1.2s ease-in-out 0.4s infinite;
  opacity: 0.6;
}

@keyframes pingPulse {
  0%, 100% { transform: scale(1);    opacity: 1;   }
  50%       { transform: scale(1.45); opacity: 0.45; }
}

/* Transition 动画 */
.notify-slide-enter-active {
  transition: transform 520ms cubic-bezier(0.34,1.56,0.64,1), opacity 520ms ease;
}

.notify-slide-leave-active {
  transition: transform 400ms cubic-bezier(0.4,0,0.2,1), opacity 400ms ease;
}

.notify-slide-enter-from {
  transform: translateX(-50%) translateY(-110%);
  opacity: 0;
}

.notify-slide-enter-to {
  transform: translateX(-50%) translateY(0);
  opacity: 1;
}

.notify-slide-leave-from {
  transform: translateX(-50%) translateY(0);
  opacity: 1;
}

.notify-slide-leave-to {
  transform: translateX(-50%) translateY(-110%);
  opacity: 0;
}
</style>
