<template>
  <div v-if="currentAgent" class="agent-status-bar">
    <div class="agent-indicator">
      <span class="pulse-dot"></span>
      <span class="agent-name">{{ agentDisplayName }}</span>
      <span class="agent-action">处理中...</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useChatStore } from '@/stores/chatStore'

const chatStore = useChatStore()

const currentAgent = computed(() => {
  // 优先使用 currentAgent；否则从 activeAgents 中取最近一个 running 状态的 Agent
  if (chatStore.currentAgent) return chatStore.currentAgent
  const running = chatStore.activeAgents.filter(a => a.status === 'running')
  return running.length > 0 ? running[running.length - 1].agentName : null
})

const agentDisplayName = computed(() => {
  const nameMap: Record<string, string> = {
    Orchestrator: '指挥官',
    DiagnosisAgent: '诊断分析',
    Diagnosis: '诊断分析',
    ResourceGenerator: '资源生成',
    PathPlanner: '路径规划',
    PathPlannerAgent: '路径规划',
    Profiler: '画像更新',
    ProfilerAgent: '画像更新',
    Retriever: '知识检索',
    RetrieverAgent: '知识检索',
    Challenger: '挑战追问',
  }
  return nameMap[currentAgent.value || ''] || currentAgent.value
})
</script>

<style scoped>
.agent-status-bar {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  background: linear-gradient(90deg, #f0f9ff 0%, #ffffff 100%);
  border: 1px solid #e0f2fe;
  border-radius: 8px;
}

.agent-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #0369a1;
}

.pulse-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: #0ea5e9;
  animation: pulse 1s infinite;
}

.agent-name {
  font-weight: 600;
}

.agent-action {
  color: #64748b;
}

@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.3;
  }
}
</style>
