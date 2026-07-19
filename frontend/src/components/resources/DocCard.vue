<template>
  <div class="doc-card">
    <div class="doc-card-header">
      <div class="doc-icon-wrap">
        <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414A1 1 0 0119 9.414V19a2 2 0 01-2 2z" />
        </svg>
      </div>
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2 mb-1 flex-wrap">
          <span class="doc-type-badge">知识文档</span>
          <span v-if="resource.diagnosis_driven" class="diag-badge" title="根据诊断结果的针对性资源">🧠 诊断驱动</span>
          <span class="text-xs text-gray-400">{{ formattedTime }}</span>
        </div>
        <h3 class="doc-title">{{ resource.title }}</h3>
        <p class="doc-kp">{{ resource.knowledge_point }}</p>
        <p v-if="resource.strategy_reason" class="doc-strategy">💡 {{ resource.strategy_reason }}</p>
      </div>
    </div>

    <p v-if="!expanded && contentPreview" class="doc-preview">{{ contentPreview }}</p>

    <div v-if="expanded" class="doc-content">
      <div class="prose prose-sm max-w-none text-gray-700 text-xs leading-relaxed" v-html="renderedContent" />
    </div>

    <button class="doc-expand-btn" @click="expanded = !expanded">
      {{ expanded ? '收起 ▲' : '展开阅读 →' }}
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

const contentPreview = computed(() => {
  const lines = (props.resource.content ?? '')
    .split('\n')
    .map(l => l.trim())
    .filter(l => l && !l.startsWith('#') && !l.startsWith('```'))
  const first = lines[0]?.replace(/[*_`>\[\]]/g, '').trim() ?? ''
  return first.length > 100 ? first.slice(0, 100) + '…' : first
})

const formattedTime = computed(() => {
  const d = new Date(props.resource.created_at || Date.now())
  return `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
})
</script>

<style scoped>
.doc-card {
  background: linear-gradient(135deg, white 0%, #f0f6ff 100%);
  border: 1px solid rgba(22,119,255,0.15);
  border-radius: 14px;
  padding: 16px;
  transition: all 0.25s;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.doc-card:hover {
  box-shadow: 0 6px 24px rgba(22,119,255,0.12);
  transform: translateY(-2px);
  border-color: rgba(22,119,255,0.3);
}
.doc-card-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}
.doc-icon-wrap {
  width: 38px; height: 38px;
  border-radius: 10px;
  background: linear-gradient(135deg, #1677FF, #0958D9);
  color: white;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 3px 10px rgba(22,119,255,0.3);
}
.doc-type-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 9px;
  border-radius: 999px;
  background: rgba(22,119,255,0.1);
  color: #1677FF;
  border: 1px solid rgba(22,119,255,0.2);
}
.diag-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 9px;
  border-radius: 999px;
  background: rgba(22,119,255,0.06);
  color: #0958D9;
  border: 1px solid rgba(22,119,255,0.15);
}
.doc-title {
  font-size: 14px;
  font-weight: 700;
  color: #0f172a;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin: 0;
}
.doc-kp {
  font-size: 11px;
  color: #64748b;
  margin: 2px 0 0;
}
.doc-strategy {
  font-size: 11px;
  color: #1677FF;
  margin: 3px 0 0;
  line-height: 1.4;
}
.doc-preview {
  font-size: 12px;
  color: #475569;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  padding: 8px 10px;
  background: rgba(22,119,255,0.04);
  border-radius: 8px;
  border-left: 2px solid rgba(22,119,255,0.3);
  margin: 0;
}
.doc-content {
  padding-top: 10px;
  border-top: 1px solid rgba(22,119,255,0.1);
}
.doc-expand-btn {
  font-size: 12px;
  font-weight: 600;
  color: #1677FF;
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 4px 0;
  transition: opacity 0.15s;
  text-align: left;
}
.doc-expand-btn:hover { opacity: 0.75; }
</style>
