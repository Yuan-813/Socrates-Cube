<script setup lang="ts">
interface Props {
  text?: string
  fullscreen?: boolean
  variant?: 'spinner' | 'dots' | 'progress'
  progress?: number
}

withDefaults(defineProps<Props>(), {
  text: '加载中...',
  fullscreen: false,
  variant: 'spinner',
  progress: 0,
})
</script>

<template>
  <div class="app-loading" :class="{ fullscreen }">
    <div class="loading-content">
      <!-- Spinner 变体 -->
      <template v-if="variant === 'spinner'">
        <div class="spinner">
          <div class="spinner-ring"></div>
          <div class="spinner-ring"></div>
          <div class="spinner-ring"></div>
        </div>
      </template>

      <!-- Dots 变体 -->
      <template v-else-if="variant === 'dots'">
        <div class="dots-loader">
          <span class="dot"></span>
          <span class="dot"></span>
          <span class="dot"></span>
        </div>
      </template>

      <!-- Progress 变体 -->
      <template v-else-if="variant === 'progress'">
        <div class="progress-loader">
          <div class="progress-track">
            <div class="progress-fill" :style="{ width: Math.min(progress, 100) + '%' }"></div>
          </div>
          <span class="progress-percent">{{ Math.round(progress) }}%</span>
        </div>
      </template>

      <p class="loading-text">{{ text }}</p>
    </div>
  </div>
</template>

<style scoped>
.app-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
}

.app-loading.fullscreen {
  position: fixed;
  inset: 0;
  background-color: rgba(255, 255, 255, 0.9);
  z-index: 2000;
}

.loading-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

/* Spinner */
.spinner {
  position: relative;
  width: 48px;
  height: 48px;
}

.spinner-ring {
  position: absolute;
  inset: 0;
  border: 3px solid transparent;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1.2s linear infinite;
}

.spinner-ring:nth-child(2) {
  border-top-color: #10b981;
  animation-delay: 0.15s;
  inset: 6px;
}

.spinner-ring:nth-child(3) {
  border-top-color: #f59e0b;
  animation-delay: 0.3s;
  inset: 12px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Dots */
.dots-loader {
  display: flex;
  gap: 8px;
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background-color: #3b82f6;
  animation: dot-bounce 1.4s ease-in-out infinite both;
}

.dot:nth-child(1) { animation-delay: -0.32s; background-color: #3b82f6; }
.dot:nth-child(2) { animation-delay: -0.16s; background-color: #10b981; }
.dot:nth-child(3) { background-color: #f59e0b; }

@keyframes dot-bounce {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.5; }
  40% { transform: scale(1); opacity: 1; }
}

/* Progress */
.progress-loader {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  min-width: 200px;
}

.progress-track {
  width: 100%;
  height: 6px;
  background-color: #e2e8f0;
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #3b82f6, #10b981);
  border-radius: 3px;
  transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.progress-percent {
  font-size: 12px;
  color: #64748b;
  font-weight: 600;
}

.loading-text {
  font-size: 14px;
  color: #64748b;
}
</style>
