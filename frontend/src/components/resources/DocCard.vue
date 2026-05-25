<template>
  <div class="resource-card doc-card bg-white rounded-xl border border-gray-100 shadow-sm p-4 hover:shadow-md transition-shadow">
    <div class="flex items-start gap-3">
      <div class="shrink-0 w-9 h-9 rounded-lg bg-blue-50 flex items-center justify-center text-blue-500">
        <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414A1 1 0 0119 9.414V19a2 2 0 01-2 2z" />
        </svg>
      </div>
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2 mb-1">
          <span class="text-xs font-medium px-2 py-0.5 rounded-full bg-blue-100 text-blue-600">知识文档</span>
          <span class="text-xs text-gray-400">{{ formattedTime }}</span>
        </div>
        <h3 class="font-medium text-gray-800 text-sm truncate">{{ resource.title }}</h3>
        <p class="text-xs text-gray-500 mt-1">知识点：{{ resource.knowledge_point }}</p>
      </div>
    </div>
    <div v-if="expanded" class="mt-3 pt-3 border-t border-gray-50">
      <div class="prose prose-sm max-w-none text-gray-700 text-xs leading-relaxed"
        v-html="renderedContent" />
    </div>
    <button
      class="mt-2 w-full text-xs text-blue-500 hover:text-blue-600 font-medium"
      @click="expanded = !expanded"
    >
      {{ expanded ? '收起' : '展开阅读' }}
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { LearningResource } from '../../types'
import { renderMarkdown } from '../../utils/markdown'

const props = defineProps<{ resource: LearningResource }>()
const expanded = ref(false)
const renderedContent = computed(() => renderMarkdown(props.resource.content))
const formattedTime = computed(() => {
  const d = new Date(props.resource.created_at)
  return `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
})
</script>
