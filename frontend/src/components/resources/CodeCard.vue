<template>
  <div class="code-card">
    <div class="code-card-header">
      <div class="code-icon-wrap">
        <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
        </svg>
      </div>
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2 mb-1">
          <span class="code-type-badge">代码示例</span>
          <span class="code-lang-badge">{{ codeLanguage }}</span>
        </div>
        <h3 class="code-title">{{ resource.title }}</h3>
        <p class="code-kp">{{ resource.knowledge_point }}</p>
      </div>
    </div>

    <div v-if="!expanded && codePreview" class="code-preview-dark">
      <span class="code-preview-label">{{ codeLanguage }}</span>
      <code>{{ codePreview }}</code>
    </div>

    <div v-if="expanded" class="code-content">
      <div class="prose prose-sm max-w-none text-xs leading-relaxed" v-html="renderedContent" />
    </div>

    <button class="code-expand-btn" @click="expanded = !expanded">
      {{ expanded ? '收起代码 ▲' : '查看代码示例 →' }}
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

const codeLanguage = computed(() => {
  if (props.resource.metadata?.language) return String(props.resource.metadata.language)
  const match = (props.resource.content ?? '').match(/```(\w+)/)
  return match?.[1] ?? 'python'
})

const codePreview = computed(() => {
  const content = props.resource.content ?? ''
  const codeMatch = content.match(/```\w*\s*\n([^`]+)/)
  if (codeMatch) {
    const firstComment = codeMatch[1].split('\n')
      .find((l: string) => l.trim().startsWith('#') || l.trim().startsWith('//'))
    if (firstComment) return firstComment.replace(/^[#/\s]+/, '').trim()
  }
  const lines = content.split('\n').map((l: string) => l.trim())
    .filter((l: string) => l && !l.startsWith('#') && !l.startsWith('```') && !l.startsWith('import'))
  const first = lines[0]?.replace(/[*_`>]/g, '').trim() ?? ''
  return first.length > 100 ? first.slice(0, 100) + '…' : first
})
</script>

<style scoped>
.code-card {
  background: linear-gradient(135deg, white 0%, #f0fdfb 100%);
  border: 1px solid rgba(0,194,168,0.18);
  border-radius: 14px;
  padding: 16px;
  transition: all 0.25s;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.code-card:hover {
  box-shadow: 0 6px 24px rgba(0,194,168,0.12);
  transform: translateY(-2px);
  border-color: rgba(0,194,168,0.35);
}
.code-card-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}
.code-icon-wrap {
  width: 38px; height: 38px;
  border-radius: 10px;
  background: linear-gradient(135deg, #00C2A8, #00A38D);
  color: white;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 3px 10px rgba(0,194,168,0.3);
}
.code-type-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 9px;
  border-radius: 999px;
  background: rgba(0,194,168,0.1);
  color: #00A38D;
  border: 1px solid rgba(0,194,168,0.25);
}
.code-lang-badge {
  font-size: 10px;
  font-weight: 700;
  padding: 2px 7px;
  border-radius: 5px;
  background: #1e293b;
  color: #7dd3fc;
  font-family: monospace;
}
.code-title {
  font-size: 14px;
  font-weight: 700;
  color: #0f172a;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin: 0;
}
.code-kp {
  font-size: 11px;
  color: #64748b;
  margin: 2px 0 0;
}
.code-preview-dark {
  background: #1e293b;
  border-radius: 8px;
  padding: 10px 12px;
  position: relative;
}
.code-preview-label {
  position: absolute;
  top: 6px; right: 8px;
  font-size: 9px;
  color: #475569;
  font-family: monospace;
  font-weight: 600;
  text-transform: uppercase;
}
.code-preview-dark code {
  font-size: 12px;
  color: #86efac;
  font-family: 'Fira Code', 'Consolas', monospace;
  display: block;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-all;
}
.code-content {
  padding-top: 10px;
  border-top: 1px solid rgba(0,194,168,0.1);
}
.code-expand-btn {
  font-size: 12px;
  font-weight: 600;
  color: #00A38D;
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 4px 0;
  transition: opacity 0.15s;
  text-align: left;
}
.code-expand-btn:hover { opacity: 0.75; }
</style>
