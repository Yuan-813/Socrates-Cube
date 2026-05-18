<script setup lang="ts">
import { computed, ref } from 'vue'
import { useAssistantStore } from '@/stores/assistantStore'

const assistantStore = useAssistantStore()
const logs = computed(() => assistantStore.logs)

const agentColors: Record<string, string> = {
  Orchestrator: '#8b5cf6',
  Profiler: '#3b82f6',
  Retriever: '#10b981',
  Diagnosis: '#f59e0b',
  Simulator: '#ef4444',
  'Resource Generator': '#ec4899',
  'Path Planner': '#06b6d4',
  Challenger: '#f97316',
}

const filterAgent = ref('')

const uniqueAgents = computed(() => [...new Set(logs.value.map(l => l.agentName))])
const filteredLogs = computed(() => logs.value.filter(l => !filterAgent.value || l.agentName === filterAgent.value))
</script>

<template>
  <div class="agent-log-panel">
    <!-- 筛选 -->
    <div class="log-filters mb-4">
      <el-select v-model="filterAgent" placeholder="全部Agent" clearable size="small" style="width: 160px">
        <el-option
          v-for="agent in uniqueAgents"
          :key="agent"
          :label="agent"
          :value="agent"
        />
      </el-select>
    </div>

    <!-- 日志列表 -->
    <div v-if="filteredLogs.length" class="log-list">
      <div
        v-for="log in filteredLogs"
        :key="log.logId"
        class="log-item"
      >
        <div class="log-timeline">
          <div class="log-dot" :style="{ backgroundColor: agentColors[log.agentName] || '#94a3b8' }" />
          <div class="log-line" />
        </div>

        <div class="log-card">
          <div class="log-header">
            <el-tag
              :color="agentColors[log.agentName] || '#94a3b8'"
              effect="dark"
              size="small"
            >
              {{ log.agentName }}
            </el-tag>
            <span class="log-action">{{ log.action }}</span>
            <span class="log-time">{{ log.timestamp.split(' ')[1] }}</span>
          </div>

          <div class="log-body">
            <div class="log-state">
              <span class="state-label">状态：</span>
              <span class="state-value">{{ log.state }}</span>
            </div>
            <div class="log-result">
              <span class="result-label">结果：</span>
              <span class="result-value">{{ log.result }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
    <app-empty v-else description="等待对话后生成 Agent 联调日志" />
  </div>
</template>

<style scoped>
.agent-log-panel {
  max-height: 600px;
  overflow-y: auto;
}

.log-filters {
  padding: 4px 0;
}

.log-list {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.log-item {
  display: flex;
  gap: 12px;
  padding: 12px 0;
}

.log-timeline {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 24px;
  flex-shrink: 0;
}

.log-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 2px solid #fff;
  box-shadow: 0 0 0 2px currentColor;
}

.log-line {
  width: 2px;
  flex: 1;
  background-color: #e2e8f0;
  margin-top: 4px;
}

.log-item:last-child .log-line {
  display: none;
}

.log-card {
  flex: 1;
  background-color: #f8fafc;
  border-radius: 8px;
  padding: 12px 16px;
  border: 1px solid #e2e8f0;
}

.log-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.log-action {
  font-size: 13px;
  font-weight: 500;
  color: #475569;
}

.log-time {
  font-size: 12px;
  color: #94a3b8;
  margin-left: auto;
}

.log-body {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.state-label,
.result-label {
  font-size: 12px;
  color: #94a3b8;
}

.state-value,
.result-value {
  font-size: 13px;
  color: #334155;
}

.result-value {
  color: #059669;
}
</style>
