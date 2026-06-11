<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div
        v-if="visible && node"
        class="fixed inset-0 z-50 flex items-center justify-center px-4"
        @click.self="$emit('close')"
      >
        <div class="absolute inset-0 bg-black/35 backdrop-blur-sm" />
        <div class="relative flex max-h-[82vh] w-full max-w-md flex-col overflow-hidden rounded-lg bg-white shadow-2xl">
          <div class="flex items-start justify-between gap-4 border-b border-gray-100 px-5 py-4">
            <div class="min-w-0">
              <h3 class="truncate text-base font-semibold text-gray-900">{{ node.node_name }}</h3>
              <p class="mt-1 text-xs text-gray-500">{{ node.chapter }} · 难度 {{ node.difficulty }}/5</p>
            </div>
            <button
              type="button"
              class="rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-700"
              aria-label="关闭"
              @click="$emit('close')"
            >
              ×
            </button>
          </div>

          <div class="min-h-0 flex-1 space-y-4 overflow-y-auto px-5 py-4">
            <section>
              <h4 class="mb-2 text-xs font-semibold uppercase text-sky-700">推荐理由</h4>
              <p class="text-sm leading-6 text-gray-700">{{ node.recommendation_reason }}</p>
            </section>

            <section v-if="node.reason_sources?.length">
              <h4 class="mb-2 text-xs font-semibold uppercase text-amber-700">依据来源</h4>
              <ul class="space-y-1">
                <li
                  v-for="(source, index) in node.reason_sources"
                  :key="index"
                  class="flex gap-2 text-xs leading-5 text-gray-600"
                >
                  <span class="text-amber-500">•</span>
                  <span>{{ source }}</span>
                </li>
              </ul>
            </section>

            <section v-if="node.prerequisites?.length">
              <h4 class="mb-2 text-xs font-semibold uppercase text-gray-500">前置知识</h4>
              <div class="flex flex-wrap gap-2">
                <span
                  v-for="prereq in node.prerequisites"
                  :key="prereq"
                  class="rounded-md px-2 py-1 text-xs"
                  :class="node.prerequisites_met ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-600'"
                >
                  {{ node.prerequisites_met ? '✓' : '!' }} {{ prereq }}
                </span>
              </div>
            </section>

            <section class="rounded-lg bg-gray-50 p-3">
              <div class="mb-2 flex justify-between text-xs text-gray-500">
                <span>当前掌握度</span>
                <span class="font-semibold text-sky-700">{{ Math.round(node.current_mastery * 100) }}%</span>
              </div>
              <div class="h-2 overflow-hidden rounded-full bg-gray-200">
                <div
                  class="h-full rounded-full bg-sky-500 transition-all duration-500"
                  :style="{ width: Math.round(node.current_mastery * 100) + '%' }"
                />
              </div>
            </section>
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
