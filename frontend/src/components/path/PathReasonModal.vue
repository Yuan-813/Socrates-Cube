<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div v-if="visible && node"
        class="fixed inset-0 z-50 flex items-center justify-center"
        @click.self="$emit('close')">
        <div class="absolute inset-0 bg-black/30 backdrop-blur-sm" />
        <div class="relative bg-white rounded-2xl shadow-2xl w-full max-w-md mx-4 max-h-[80vh] overflow-hidden flex flex-col">
          <!-- 头部 -->
          <div class="px-5 py-4 border-b border-gray-100 flex items-start justify-between">
            <div>
              <h3 class="text-base font-semibold text-gray-800">{{ node.node_name }}</h3>
              <span class="text-xs text-gray-500">{{ node.chapter }}</span>
            </div>
            <button class="text-gray-400 hover:text-gray-600 mt-0.5" @click="$emit('close')">
              <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <!-- 内容 -->
          <div class="flex-1 overflow-y-auto px-5 py-4 space-y-4">
            <!-- 推荐理由 -->
            <div>
              <h4 class="text-xs font-medium text-indigo-600 uppercase tracking-wide mb-2">推荐理由</h4>
              <p class="text-sm text-gray-700 leading-relaxed">{{ node.recommendation_reason }}</p>
            </div>

            <!-- 来源依据 -->
            <div v-if="node.reason_sources?.length">
              <h4 class="text-xs font-medium text-amber-600 uppercase tracking-wide mb-2">依据来源</h4>
              <ul class="space-y-1">
                <li v-for="(src, i) in node.reason_sources" :key="i"
                  class="text-xs text-gray-600 flex gap-2">
                  <span class="text-amber-400 shrink-0">◆</span>
                  <span>{{ src }}</span>
                </li>
              </ul>
            </div>

            <!-- 前置知识链 -->
            <div v-if="node.prerequisites?.length">
              <h4 class="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">前置知识</h4>
              <div class="flex flex-wrap gap-2">
                <span
                  v-for="prereq in node.prerequisites"
                  :key="prereq"
                  class="text-xs px-2 py-1 rounded-lg"
                  :class="node.prerequisites_met?.includes(prereq)
                    ? 'bg-green-50 text-green-600'
                    : 'bg-red-50 text-red-500'">
                  <span v-if="node.prerequisites_met?.includes(prereq)" class="mr-1">✓</span>
                  <span v-else class="mr-1">✗</span>
                  {{ prereq }}
                </span>
              </div>
            </div>

            <!-- 掌握度 -->
            <div class="bg-gray-50 rounded-xl p-3">
              <div class="flex justify-between text-xs mb-2 text-gray-500">
                <span>当前掌握度</span>
                <span class="font-medium text-indigo-600">{{ Math.round(node.current_mastery * 100) }}%</span>
              </div>
              <div class="h-2 bg-gray-200 rounded-full overflow-hidden">
                <div class="h-full bg-indigo-500 rounded-full transition-all duration-500"
                  :style="{ width: (node.current_mastery * 100) + '%' }" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import type { PathNode } from '../../types'

defineProps<{
  node: PathNode | null
  visible: boolean
}>()

defineEmits<{ (e: 'close'): void }>()
</script>

<style scoped>
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.2s ease;
}
.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}
</style>
