<script setup lang="ts">
withDefaults(defineProps<{
  rows?: number
  showHeader?: boolean
}>(), {
  rows: 3,
  showHeader: true,
})
</script>

<template>
  <div class="skeleton-container">
    <div v-if="showHeader" class="skeleton-header">
      <div class="skeleton-avatar"></div>
      <div class="skeleton-title"></div>
    </div>
    <div v-for="i in rows" :key="i" class="skeleton-row">
      <div class="skeleton-line" :style="{ width: i === rows ? '60%' : '100%' }"></div>
    </div>
  </div>
</template>

<style scoped>
.skeleton-container {
  padding: 16px;
  background-color: #fff;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
}

.skeleton-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.skeleton-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background-color: #e2e8f0;
  animation: shimmer 1.5s infinite;
}

.skeleton-title {
  height: 16px;
  width: 120px;
  border-radius: 4px;
  background-color: #e2e8f0;
  animation: shimmer 1.5s infinite;
}

.skeleton-row {
  margin-bottom: 10px;
}

.skeleton-line {
  height: 14px;
  border-radius: 4px;
  background-color: #e2e8f0;
  animation: shimmer 1.5s infinite;
}

@keyframes shimmer {
  0% { opacity: 1; }
  50% { opacity: 0.5; }
  100% { opacity: 1; }
}
</style>
