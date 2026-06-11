<template>
  <div class="resource-card exercise-card bg-white rounded-xl border border-gray-100 shadow-sm p-4 hover:shadow-md transition-shadow">
    <div class="flex items-start gap-3">
      <div class="shrink-0 w-9 h-9 rounded-lg bg-amber-50 flex items-center justify-center text-amber-500">
        <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
        </svg>
      </div>
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2 mb-1">
          <span class="text-xs font-medium px-2 py-0.5 rounded-full bg-amber-100 text-amber-600">练习题</span>
          <span class="text-xs px-1.5 py-0.5 rounded bg-gray-100 text-gray-500">
            难度 {{ resource.metadata?.difficulty ?? 3 }}/5
          </span>
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
      class="mt-2 w-full text-xs text-amber-500 hover:text-amber-600 font-medium"
      @click="expanded = !expanded"
    >
      {{ expanded ? '收起题目' : '查看题目与解析' }}
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
</script>
