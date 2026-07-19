<template>
  <div class="ex-card">
    <div class="ex-card-header">
      <div class="ex-icon-wrap">
        <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
        </svg>
      </div>
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2 mb-1">
          <span class="ex-type-badge">练习题</span>
          <span class="ex-stars" :title="`难度 ${diffLevel}/5`">{{ starsDisplay }}</span>
        </div>
        <h3 class="ex-title">{{ resource.title }}</h3>
        <p class="ex-kp">{{ resource.knowledge_point }}</p>
      </div>
    </div>

    <p v-if="!expanded && questionPreview" class="ex-preview">{{ questionPreview }}</p>

    <div v-if="expanded" class="ex-content">
      <div class="prose prose-sm max-w-none text-gray-700 text-xs leading-relaxed" v-html="renderedContent" />
    </div>

    <button class="ex-expand-btn" @click="expanded = !expanded">
      {{ expanded ? '收起题目 ▲' : '查看题目与解析 →' }}
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { LearningResource } from '../../types'
import { renderMarkdown } from '../../utils/markdown'

const props = defineProps<{ resource: LearningResource }>()
const expanded = ref(false)
const renderedContent = computed(() => renderMarkdown(props.resource.content ?? ''))

const diffLevel = computed(() => Number(props.resource.metadata?.difficulty ?? 3))
const starsDisplay = computed(() => {
  const n = diffLevel.value
  return '★'.repeat(n) + '☆'.repeat(5 - n)
})

const questionPreview = computed(() => {
  const content = props.resource.content ?? ''
  if (content.trim().startsWith('{')) {
    try {
      const data = JSON.parse(content)
      const q = data.question ?? data.题目 ?? ''
      return q.length > 100 ? q.slice(0, 100) + '…' : q
    } catch { /* ignore */ }
  }
  const lines = content.split('\n').map((l: string) => l.trim())
    .filter((l: string) => l && !l.startsWith('#') && !l.startsWith('```'))
  const first = lines[0]?.replace(/[*_`>\[\]]/g, '').trim() ?? ''
  return first.length > 100 ? first.slice(0, 100) + '…' : first
})
</script>

<style scoped>
.ex-card {
  background: linear-gradient(135deg, white 0%, #fffbf0 100%);
  border: 1px solid rgba(245,158,11,0.2);
  border-radius: 14px;
  padding: 16px;
  transition: all 0.25s;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.ex-card:hover {
  box-shadow: 0 6px 24px rgba(245,158,11,0.12);
  transform: translateY(-2px);
  border-color: rgba(245,158,11,0.35);
}
.ex-card-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}
.ex-icon-wrap {
  width: 38px; height: 38px;
  border-radius: 10px;
  background: linear-gradient(135deg, #f59e0b, #d97706);
  color: white;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 3px 10px rgba(245,158,11,0.3);
}
.ex-type-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 9px;
  border-radius: 999px;
  background: rgba(245,158,11,0.1);
  color: #b45309;
  border: 1px solid rgba(245,158,11,0.25);
}
.ex-stars {
  font-size: 12px;
  color: #f59e0b;
  letter-spacing: 1px;
}
.ex-title {
  font-size: 14px;
  font-weight: 700;
  color: #0f172a;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin: 0;
}
.ex-kp {
  font-size: 11px;
  color: #64748b;
  margin: 2px 0 0;
}
.ex-preview {
  font-size: 12px;
  color: #78350f;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  padding: 8px 10px;
  background: rgba(245,158,11,0.06);
  border-radius: 8px;
  border-left: 2px solid rgba(245,158,11,0.5);
  margin: 0;
}
.ex-content {
  padding-top: 10px;
  border-top: 1px solid rgba(245,158,11,0.15);
}
.ex-expand-btn {
  font-size: 12px;
  font-weight: 600;
  color: #b45309;
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 4px 0;
  transition: opacity 0.15s;
  text-align: left;
}
.ex-expand-btn:hover { opacity: 0.75; }
</style>
