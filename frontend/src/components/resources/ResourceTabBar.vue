<template>
  <div class="resource-section">
    <!-- Tab 切换栏 -->
    <div class="flex gap-1 border-b border-gray-100 mb-3">
      <button
        v-for="tab in tabs"
        :key="tab.type"
        class="px-3 py-1.5 text-xs font-medium rounded-t-lg transition-colors relative"
        :class="activeTab === tab.type
          ? 'text-indigo-600 bg-indigo-50 border-b-2 border-indigo-500'
          : 'text-gray-500 hover:text-gray-700'"
        @click="resourceStore.activeTab = tab.type"
      >
        {{ tab.label }}
        <span v-if="tab.count > 0"
          class="ml-1 px-1 py-0.5 rounded-full text-xs bg-gray-200 text-gray-600">
          {{ tab.count }}
        </span>
      </button>
    </div>

    <!-- 资源列表 -->
    <div class="space-y-3 max-h-96 overflow-y-auto pr-1">
      <template v-if="currentResources.length > 0">
        <component
          :is="cardComponent"
          v-for="res in currentResources"
          :key="res.resource_id"
          :resource="res"
        />
      </template>
      <div v-else class="text-center py-8 text-gray-400 text-sm">
        <svg xmlns="http://www.w3.org/2000/svg" class="w-10 h-10 mx-auto mb-2 opacity-30" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
        </svg>
        <p>本次对话暂无{{ currentTabLabel }}资源</p>
        <p class="text-xs mt-1">提问相关概念时会自动生成</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useResourceStore } from '../../stores/resourceStore'
import type { ResourceType } from '../../types'
import DocCard from './DocCard.vue'
import ExerciseCard from './ExerciseCard.vue'
import CodeCard from './CodeCard.vue'

const resourceStore = useResourceStore()
const activeTab = computed(() => resourceStore.activeTab)

const tabs = computed(() => [
  { type: 'doc' as ResourceType, label: '知识文档', count: resourceStore.docResources.length },
  { type: 'exercise' as ResourceType, label: '练习题', count: resourceStore.exerciseResources.length },
  { type: 'code' as ResourceType, label: '代码示例', count: resourceStore.codeResources.length },
])

const currentResources = computed(() => {
  switch (activeTab.value) {
    case 'doc': return resourceStore.docResources
    case 'exercise': return resourceStore.exerciseResources
    case 'code': return resourceStore.codeResources
    default: return resourceStore.docResources
  }
})

const cardComponent = computed(() => {
  switch (activeTab.value) {
    case 'doc': return DocCard
    case 'exercise': return ExerciseCard
    case 'code': return CodeCard
    default: return DocCard
  }
})

const currentTabLabel = computed(() =>
  tabs.value.find(t => t.type === activeTab.value)?.label ?? ''
)
</script>
