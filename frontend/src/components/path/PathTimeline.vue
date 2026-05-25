<template>
  <div class="learning-path">
    <!-- 头部统计 -->
    <div v-if="pathStore.path" class="flex items-center justify-between mb-4">
      <div>
        <h4 class="text-sm font-semibold text-gray-700">{{ pathStore.path.title }}</h4>
        <p class="text-xs text-gray-400 mt-0.5">
          预计 {{ Math.round(pathStore.path.total_estimated_time / 60) }} 小时 ·
          {{ pathStore.completedCount }}/{{ pathStore.totalCount }} 已完成
        </p>
      </div>
      <div class="text-right">
        <div class="text-xl font-bold text-indigo-600">{{ pathStore.progressPercent }}%</div>
        <div class="text-xs text-gray-400">整体进度</div>
      </div>
    </div>

    <!-- 进度条 -->
    <div class="h-1.5 bg-gray-100 rounded-full mb-4 overflow-hidden">
      <div
        class="h-full bg-indigo-500 rounded-full transition-all duration-500"
        :style="{ width: pathStore.progressPercent + '%' }"
      />
    </div>

    <!-- 节点时间轴 -->
    <div v-if="pathStore.path" class="space-y-2 max-h-80 overflow-y-auto pr-1">
      <div
        v-for="(node, idx) in pathStore.path.nodes"
        :key="node.node_id"
        class="flex gap-3 cursor-pointer group"
        @click="pathStore.selectNode(node)"
      >
        <!-- 竖线 + 节点圆 -->
        <div class="flex flex-col items-center">
          <div class="w-7 h-7 rounded-full border-2 flex items-center justify-center text-xs font-bold shrink-0"
            :class="nodeCircleClass(node.status)">
            <span v-if="node.status === 'completed'">✓</span>
            <span v-else-if="node.status === 'in_progress'">▶</span>
            <span v-else-if="node.status === 'locked'">🔒</span>
            <span v-else>{{ idx + 1 }}</span>
          </div>
          <div v-if="idx < pathStore.path!.nodes.length - 1"
            class="w-0.5 flex-1 mt-1"
            :class="node.status === 'completed' ? 'bg-indigo-300' : 'bg-gray-200'" />
        </div>

        <!-- 节点内容 -->
        <div class="flex-1 pb-3 group-hover:bg-gray-50 rounded-lg px-2 transition-colors">
          <div class="flex items-center gap-2">
            <span class="text-xs font-medium text-gray-700">{{ node.node_name }}</span>
            <span class="text-xs text-gray-400">{{ node.chapter }}</span>
            <span v-if="node.is_target"
              class="text-xs px-1 py-0.5 rounded bg-indigo-100 text-indigo-600">目标</span>
          </div>
          <div class="flex items-center gap-3 mt-0.5">
            <span class="text-xs text-gray-400">{{ node.estimated_time }}分钟</span>
            <div class="flex-1 h-1 bg-gray-100 rounded-full overflow-hidden max-w-16">
              <div class="h-full bg-indigo-400 rounded-full"
                :style="{ width: (node.current_mastery * 100) + '%' }" />
            </div>
            <span class="text-xs text-gray-400">{{ Math.round(node.current_mastery * 100) }}%</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else class="text-center py-8 text-gray-400 text-sm">
      <svg xmlns="http://www.w3.org/2000/svg" class="w-10 h-10 mx-auto mb-2 opacity-30" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
      </svg>
      <p>学习路径生成中</p>
      <p class="text-xs mt-1">继续对话后将自动规划</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { PathNodeStatus } from '../../types'
import { usePathStore } from '../../stores/pathStore'

const pathStore = usePathStore()

function nodeCircleClass(status: PathNodeStatus): string {
  switch (status) {
    case 'completed': return 'border-indigo-500 bg-indigo-500 text-white'
    case 'in_progress': return 'border-indigo-400 bg-indigo-50 text-indigo-600'
    case 'locked': return 'border-gray-200 bg-gray-50 text-gray-400'
    default: return 'border-gray-300 bg-white text-gray-500'
  }
}
</script>
