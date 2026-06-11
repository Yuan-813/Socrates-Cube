<template>
  <Transition name="bar-slide">
    <div
      v-if="runningAgents.length > 0"
      class="flex items-center gap-2 rounded-lg border border-sky-100 bg-sky-50 px-3 py-2"
    >
      <div class="h-2 w-2 shrink-0 animate-pulse rounded-full bg-sky-500" />
      <div class="min-w-0 flex-1">
        <div class="truncate text-xs font-semibold text-sky-700">
          {{ runningAgents.map(agent => displayName(agent.agentName)).join(' -> ') }}
        </div>
        <div class="truncate text-xs text-sky-500">
          {{ runningAgents[runningAgents.length - 1]?.message || '处理中' }}
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useChatStore } from '../stores/chatStore'

const chatStore = useChatStore()

const runningAgents = computed(() =>
  chatStore.activeAgents.filter(agent => agent.status === 'running'),
)

function displayName(name: string): string {
  const nameMap: Record<string, string> = {
    Orchestrator: '指挥智能体',
    Retriever: '知识检索',
    Diagnosis: '认知诊断',
    ResourceGenerator: '资源生成',
    PathPlanner: '路径规划',
    Profiler: '画像更新',
  }
  return nameMap[name] || name
}
</script>

<style scoped>
.bar-slide-enter-active,
.bar-slide-leave-active {
  transition: all 0.2s ease;
}

.bar-slide-enter-from,
.bar-slide-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
