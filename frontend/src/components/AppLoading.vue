<script setup lang="ts">
interface Props {
  text?: string
  fullscreen?: boolean
}

withDefaults(defineProps<Props>(), {
  text: '加载中...',
  fullscreen: false,
})
</script>

<template>
  <div class="app-loading" :class="{ fullscreen }">
    <div class="loading-content">
      <div class="spinner">
        <div class="spinner-ring"></div>
        <div class="spinner-ring"></div>
        <div class="spinner-ring"></div>
      </div>
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
  to {
    transform: rotate(360deg);
  }
}

.loading-text {
  font-size: 14px;
  color: #64748b;
}
</style>
