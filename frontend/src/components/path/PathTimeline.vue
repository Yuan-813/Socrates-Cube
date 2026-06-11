<template>
  <div class="flex h-full flex-col">
    <div v-if="pathStore.path" class="mb-4 flex items-start justify-between gap-3">
      <div class="min-w-0">
        <h4 class="truncate text-sm font-semibold text-gray-800">
          {{ pathStore.path.title }}
        </h4>
        <p class="mt-1 text-xs text-gray-500">
          预计 {{ Math.max(1, Math.round(pathStore.path.total_estimated_time / 60)) }} 小时 ·
          {{ pathStore.completedCount }}/{{ pathStore.totalCount }} 已完成
        </p>
      </div>
      <div class="text-right">
        <div class="text-xl font-bold text-sky-600">{{ pathStore.progressPercent }}%</div>
        <div class="text-xs text-gray-400">整体进度</div>
      </div>
    </div>

    <div class="mb-4 h-1.5 overflow-hidden rounded-full bg-gray-100">
      <div
        class="h-full rounded-full bg-sky-500 transition-all duration-500"
        :style="{ width: pathStore.progressPercent + '%' }"
      />
    </div>

    <div v-if="pathStore.path" class="min-h-0 flex-1 space-y-2 overflow-y-auto pr-1">
      <button
        v-for="(node, idx) in pathStore.path.nodes"
        :key="`${node.node_id}-${idx}`"
        type="button"
        class="group flex w-full gap-3 rounded-md text-left outline-none transition-colors hover:bg-gray-50 focus-visible:ring-2 focus-visible:ring-sky-400"
        @click="openNode(node)"
      >
        <div class="flex flex-col items-center pl-1">
          <div
            class="flex h-7 w-7 shrink-0 items-center justify-center rounded-full border-2 text-xs font-bold"
            :class="nodeCircleClass(node.status)"
          >
            <span v-if="node.status === 'completed'">✓</span>
            <span v-else-if="node.status === 'in_progress'">•</span>
            <span v-else-if="node.status === 'locked'">锁</span>
            <span v-else>{{ idx + 1 }}</span>
          </div>
          <div
            v-if="idx < pathStore.path.nodes.length - 1"
            class="mt-1 w-0.5 flex-1"
            :class="node.status === 'completed' ? 'bg-sky-300' : 'bg-gray-200'"
          />
        </div>

        <div class="min-w-0 flex-1 pb-3 pr-2">
          <div class="flex flex-wrap items-center gap-2">
            <span class="text-xs font-semibold text-gray-800">{{ node.node_name }}</span>
            <span class="text-xs text-gray-400">{{ node.chapter }}</span>
            <span
              v-if="node.is_target"
              class="rounded bg-sky-100 px-1.5 py-0.5 text-xs text-sky-700"
            >
              目标
            </span>
          </div>
          <p class="mt-1 line-clamp-2 text-xs leading-5 text-gray-500">
            {{ node.recommendation_reason }}
          </p>
          <div class="mt-2 flex items-center gap-2">
            <span class="w-12 text-xs text-gray-400">{{ node.estimated_time }} 分钟</span>
            <div class="h-1 flex-1 overflow-hidden rounded-full bg-gray-100">
              <div
                class="h-full rounded-full bg-sky-400"
                :style="{ width: Math.round(node.current_mastery * 100) + '%' }"
              />
            </div>
            <span class="w-8 text-right text-xs text-gray-400">
              {{ Math.round(node.current_mastery * 100) }}%
            </span>
          </div>
        </div>
      </button>
    </div>

    <div v-else class="flex flex-1 flex-col items-center justify-center text-center text-sm text-gray-400">
      <div class="mb-3 text-3xl">⌁</div>
      <p>学习路径生成中</p>
      <p class="mt-1 text-xs">继续对话后将自动规划</p>
    </div>

    <PathReasonModal
      :node="pathStore.selectedNode"
      :visible="pathStore.selectedNode !== null"
      @close="pathStore.selectNode(null)"
    />
  </div>
</template>

<script setup lang="ts">
import type { PathNode, PathNodeStatus } from '../../types'
import { usePathStore } from '../../stores/pathStore'
import PathReasonModal from './PathReasonModal.vue'

const pathStore = usePathStore()

function openNode(node: PathNode) {
  pathStore.selectNode(node)
}

function nodeCircleClass(status: PathNodeStatus): string {
  switch (status) {
    case 'completed':
      return 'border-sky-500 bg-sky-500 text-white'
    case 'in_progress':
      return 'border-sky-400 bg-sky-50 text-sky-700'
    case 'locked':
      return 'border-gray-200 bg-gray-50 text-gray-400'
    default:
      return 'border-gray-300 bg-white text-gray-500'
  }
}
</script>
