<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useResourceStore } from '@/stores/resourceStore'
import DocCard from '@/components/resources/DocCard.vue'
import ExerciseCard from '@/components/resources/ExerciseCard.vue'
import CodeCard from '@/components/resources/CodeCard.vue'
import MindmapCard from '@/components/resources/MindmapCard.vue'
import ScriptCard from '@/components/resources/ScriptCard.vue'

const resourceStore = useResourceStore()

// 本地过滤状态，'' 表示全部
const filterType = ref<string>('')

const typeLabels: Record<string, string> = {
  doc: '文档',
  exercise: '练习',
  code: '代码',
  mindmap: '导图',
  script: '脚本',
}

const filteredResources = computed(() => {
  if (!filterType.value) return resourceStore.resources
  return resourceStore.resources.filter(r => r.resource_type === filterType.value)
})

/** 当前资源列表中是否包含诺断驱动的资源 */
const hasDiagnosisDriven = computed(() =>
  resourceStore.resources.some(r => r.diagnosis_driven),
)

const cardComponents: Record<string, unknown> = {
  doc: DocCard,
  exercise: ExerciseCard,
  code: CodeCard,
  mindmap: MindmapCard,
  script: ScriptCard,
}

function cardFor(type: string) {
  return cardComponents[type] ?? DocCard
}

onMounted(() => {
  resourceStore.loadRecent()
})
</script>

<template>
  <div>
    <div class="mb-4 flex flex-wrap items-center justify-between gap-3">
      <div class="flex gap-1">
        <button
          class="text-xs px-3 py-1 rounded-lg border transition-all"
          :class="!filterType
            ? 'border-indigo-400 bg-indigo-50 text-indigo-600 font-medium'
            : 'border-gray-200 text-gray-500 hover:border-gray-300'"
          @click="filterType = ''"
        >
          全部
        </button>
        <button
          v-for="(label, type) in typeLabels"
          :key="type"
          class="text-xs px-3 py-1 rounded-lg border transition-all"
          :class="filterType === type
            ? 'border-indigo-400 bg-indigo-50 text-indigo-600 font-medium'
            : 'border-gray-200 text-gray-500 hover:border-gray-300'"
          @click="filterType = type"
        >
          {{ label }}
        </button>
      </div>
      <div class="flex items-center gap-2">
        <span
          v-if="hasDiagnosisDriven"
          class="inline-flex items-center gap-1 rounded-full bg-sky-50 px-2.5 py-0.5 text-xs font-medium text-sky-700 border border-sky-200"
          title="包含诊断驱动的针对性修复资源"
        >
          🧠 诺断驱动
        </span>
        <span class="text-xs text-gray-400">共 {{ filteredResources.length }} 个资源</span>
      </div>
    </div>

    <div v-if="resourceStore.loading && filteredResources.length === 0" class="text-center py-8 text-gray-400 text-sm">
      加载中...
    </div>

    <div v-else-if="filteredResources.length > 0" class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
      <component
        :is="cardFor(res.resource_type ?? 'doc')"
        v-for="res in filteredResources"
        :key="res.resource_id ?? res.title"
        :resource="res"
      />
    </div>

    <div v-else class="text-center py-10 text-gray-400 text-sm">
      <p>暂无学习资源</p>
      <p class="text-xs mt-1 text-gray-300">提问相关概念时会自动生成</p>
    </div>
  </div>
</template>
