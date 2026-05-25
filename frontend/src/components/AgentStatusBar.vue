<template>
  <Transition name="bar-slide">
    <div v-if="activeAgents.length > 0"
      class="flex items-center gap-2 px-3 py-1.5 bg-indigo-50 rounded-lg border border-indigo-100">
      <div class="w-2 h-2 rounded-full bg-indigo-500 animate-pulse shrink-0" />
      <span class="text-xs text-indigo-600 font-medium">
        {{ activeAgents.join(' → ') }}
      </span>
      <span class="text-xs text-indigo-400 ml-auto">处理中</span>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useChatStore } from '../stores/chatStore'

const chatStore = useChatStore()
const activeAgents = computed(() =>
  Object.entries(chatStore.activeAgents)
    .filter(([, s]) => s.status === 'running')
    .map(([name]) => name)
)
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
