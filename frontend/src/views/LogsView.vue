<script setup lang="ts">
import AgentLogPanel from '@/components/AgentLogPanel.vue'
import RLDashboard from '@/components/RLDashboard.vue'
import { useChatStore } from '@/stores/chatStore'
import { computed, ref } from 'vue'

const chatStore = useChatStore()
const sessionId = computed(() => chatStore.currentSession?.sessionId ?? '')
const activeTab = ref<'logs' | 'rl'>('logs')
</script>

<template>
  <div class="space-y-5">
    <!-- Tab 切换 -->
    <div class="logs-tabs">
      <button class="l-tab" :class="{ active: activeTab === 'logs' }" @click="activeTab = 'logs'">
        📋 Agent 执行日志
      </button>
      <button class="l-tab" :class="{ active: activeTab === 'rl' }" @click="activeTab = 'rl'">
        🤖 RL 实时监控
      </button>
    </div>

    <!-- 日志面板 -->
    <div v-if="activeTab === 'logs'" class="card">
      <h2 class="section-title">多智能体协作日志</h2>
      <p class="section-desc">实时追踪各Agent的调度、推理与执行状态</p>
      <AgentLogPanel :session-id="sessionId" />
    </div>

    <!-- RL 监控面板 -->
    <div v-else class="card">
      <RLDashboard />
    </div>
  </div>
</template>

<style scoped>
.logs-tabs {
  display: flex;
  gap: 8px;
  padding: 4px;
  background: white;
  border-radius: 12px;
  border: 1px solid #e8eef8;
}

.l-tab {
  flex: 1;
  padding: 10px 14px;
  border-radius: 10px;
  border: none;
  background: transparent;
  color: #64748b;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.l-tab:hover { color: #3730a3; background: #f0f4ff; }

.l-tab.active {
  background: linear-gradient(135deg, #3730a3, #4c1d95);
  color: white;
  box-shadow: 0 2px 10px rgba(55,48,163,0.3);
}
</style>
