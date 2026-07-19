<template>
  <div class="ai-gen-progress" v-if="isVisible">
    <div class="agp-header">
      <div class="agp-icon">
        <svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
        </svg>
      </div>
      <div class="agp-text">
        <span class="agp-title">{{ statusText }}</span>
        <span class="agp-percent">{{ percent }}%</span>
      </div>
    </div>
    <div class="agp-track">
      <div class="agp-fill" :style="{ width: percent + '%' }"></div>
    </div>
    <div class="agp-tabs">
      <span v-for="tab in resourceTabs" :key="tab.type" class="agp-tab"
        :class="{ 'agp-tab-done': tab.done, 'agp-tab-active': tab.active }">
        {{ tab.icon }} {{ tab.label }}
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useResourceStore } from '../../stores/resourceStore'

const resourceStore = useResourceStore()
const progress = computed(() => resourceStore.generationProgress)

const isVisible = computed(() =>
  progress.value.current > 0 && progress.value.current < progress.value.total
)
const percent = computed(() => {
  if (progress.value.total === 0) return 0
  return Math.round((progress.value.current / progress.value.total) * 100)
})
const statusText = computed(() => {
  const typeMap: Record<string, string> = {
    doc: 'AI Tutor 正在生成知识文档...',
    exercise: 'AI Tutor 正在生成练习题...',
    code: 'AI Tutor 正在生成代码示例...',
    mindmap: 'AI Tutor 正在构建思维导图...',
    script: 'AI Tutor 正在编写视频脚本...',
  }
  if (progress.value.current >= progress.value.total) return '全部学习材料生成完成 ✓'
  return typeMap[progress.value.currentType] || 'AI Tutor 正在为你构建学习方案...'
})
const resourceTabs = computed(() => {
  const types = [
    { type: 'doc', label: '知识文档', icon: '📄' },
    { type: 'exercise', label: '练习题', icon: '📝' },
    { type: 'code', label: '代码', icon: '💻' },
    { type: 'mindmap', label: '导图', icon: '🗺️' },
    { type: 'script', label: '脚本', icon: '🎬' },
  ]
  return types.map((t, idx) => ({
    ...t,
    done: idx < progress.value.current,
    active: t.type === progress.value.currentType,
  }))
})
</script>

<style scoped>
.ai-gen-progress {
  padding: 14px 16px;
  background: linear-gradient(135deg, rgba(22,119,255,0.06), rgba(114,46,209,0.06));
  border: 1px solid rgba(22,119,255,0.2);
  border-radius: 12px;
  margin-bottom: 14px;
}
.agp-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}
.agp-icon {
  width: 28px; height: 28px;
  border-radius: 8px;
  background: linear-gradient(135deg, #1677FF, #722ED1);
  display: flex; align-items: center; justify-content: center;
  color: white;
  flex-shrink: 0;
}
.agp-text {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.agp-title {
  font-size: 13px;
  font-weight: 600;
  color: #1e293b;
}
.agp-percent {
  font-size: 13px;
  font-weight: 800;
  color: #1677FF;
}
.agp-track {
  height: 5px;
  background: rgba(22,119,255,0.12);
  border-radius: 999px;
  overflow: hidden;
  margin-bottom: 10px;
}
.agp-fill {
  height: 100%;
  background: linear-gradient(90deg, #1677FF, #722ED1);
  border-radius: 999px;
  transition: width 0.4s ease;
}
.agp-tabs {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.agp-tab {
  font-size: 11px;
  padding: 3px 10px;
  border-radius: 999px;
  background: rgba(22,119,255,0.06);
  color: #94a3b8;
  border: 1px solid transparent;
  transition: all 0.2s;
}
.agp-tab.agp-tab-done {
  background: rgba(0,194,168,0.1);
  color: #00A38D;
  border-color: rgba(0,194,168,0.25);
}
.agp-tab.agp-tab-active {
  background: rgba(22,119,255,0.12);
  color: #1677FF;
  border-color: rgba(22,119,255,0.3);
  font-weight: 700;
  animation: pulse-tab 1.5s ease infinite;
}
@keyframes pulse-tab {
  0%,100% { opacity: 1; }
  50% { opacity: 0.65; }
}
</style>
