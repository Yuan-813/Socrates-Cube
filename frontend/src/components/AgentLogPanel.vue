<script setup lang="ts">
import { computed, ref } from 'vue'
import type { AgentLog } from '@/types'

const logs = ref<AgentLog[]>([
  { log_id: 'log-001', session_id: 's-001', agent_name: 'Orchestrator', action: '调度', state: '分析用户意图', timestamp: '2026-06-11 14:32:01', result: '识别为概念诊断' },
  { log_id: 'log-002', session_id: 's-001', agent_name: 'Retriever', action: '知识检索', state: '三库联合检索', timestamp: '2026-06-11 14:32:03', result: '命中 RFC 与误区库' },
  { log_id: 'log-003', session_id: 's-001', agent_name: 'Diagnosis', action: '三层诊断', state: '表层错误与根因分析', timestamp: '2026-06-11 14:32:06', result: '发现流程遗漏型误区' },
  { log_id: 'log-004', session_id: 's-001', agent_name: 'PathPlanner', action: '路径规划', state: '拓扑排序', timestamp: '2026-06-11 14:32:09', result: '生成 5 个学习节点' },
])

const filterAgent = ref('')

const agentColors: Record<string, string> = {
  Orchestrator: '#8b5cf6',
  Profiler: '#3b82f6',
  Retriever: '#10b981',
  Diagnosis: '#f59e0b',
  ResourceGenerator: '#ec4899',
  PathPlanner: '#06b6d4',
}

function agentName(log: AgentLog): string {
  return log.agent_name || log.agentName || 'Unknown'
}

function logId(log: AgentLog): string {
  return log.log_id || log.logId || `${agentName(log)}-${log.timestamp}`
}

const uniqueAgents = computed(() => [...new Set(logs.value.map(agentName))])
const filteredLogs = computed(() =>
  logs.value.filter(log => !filterAgent.value || agentName(log) === filterAgent.value),
)
</script>

<template>
  <div class="max-h-[600px] overflow-y-auto">
    <div class="mb-4">
      <el-select v-model="filterAgent" placeholder="全部 Agent" clearable size="small" style="width: 160px">
        <el-option v-for="agent in uniqueAgents" :key="agent" :label="agent" :value="agent" />
      </el-select>
    </div>

    <div class="flex flex-col">
      <div v-for="log in filteredLogs" :key="logId(log)" class="flex gap-3 py-3">
        <div class="flex w-6 shrink-0 flex-col items-center">
          <div
            class="h-3 w-3 rounded-full border-2 border-white shadow"
            :style="{ backgroundColor: agentColors[agentName(log)] || '#94a3b8' }"
          />
          <div class="mt-1 w-0.5 flex-1 bg-gray-200" />
        </div>

        <div class="flex-1 rounded-lg border border-gray-200 bg-gray-50 px-4 py-3">
          <div class="mb-2 flex items-center gap-2">
            <el-tag :color="agentColors[agentName(log)] || '#94a3b8'" effect="dark" size="small">
              {{ agentName(log) }}
            </el-tag>
            <span class="text-sm font-medium text-gray-700">{{ log.action }}</span>
            <span class="ml-auto text-xs text-gray-400">{{ log.timestamp.split(' ')[1] || log.timestamp }}</span>
          </div>
          <div class="space-y-1 text-xs text-gray-600">
            <p><span class="text-gray-400">状态：</span>{{ log.state }}</p>
            <p><span class="text-gray-400">结果：</span>{{ log.result }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
