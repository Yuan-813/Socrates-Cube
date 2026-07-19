<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { logsApi } from '@/api/logs'
import { useChatStore } from '@/stores/chatStore'
import type { AgentLog } from '@/types'

const props = defineProps<{
  sessionId?: string
}>()

const chatStore = useChatStore()
const logs = ref<AgentLog[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const filterAgent = ref('')
const expandedLogs = ref<Set<string>>(new Set())

const agentColors: Record<string, string> = {
  Orchestrator: '#8b5cf6',
  Profiler: '#3b82f6',
  Retriever: '#10b981',
  Diagnosis: '#f59e0b',
  ResourceGenerator: '#ec4899',
  PathPlanner: '#06b6d4',
  Challenger: '#ef4444',
  Simulator: '#84cc16',
}

const agentLabels: Record<string, string> = {
  Orchestrator: '指挥官',
  Profiler: '画像师',
  Retriever: '检索员',
  Diagnosis: '诊断师',
  ResourceGenerator: '资源生成',
  PathPlanner: '路径规划',
  Challenger: '挑战者',
  Simulator: '仿真器',
}

const activeSessionId = computed(
  () => props.sessionId || chatStore.currentSession?.sessionId || '',
)

function agentName(log: AgentLog): string {
  return log.agent_name || log.agentName || 'Unknown'
}

function logId(log: AgentLog): string {
  return log.log_id || log.logId || `${agentName(log)}-${log.timestamp}`
}

function formatTime(timestamp: string): string {
  const date = new Date(timestamp)
  if (Number.isNaN(date.getTime())) return timestamp
  return date.toLocaleTimeString()
}

function formatDuration(log: AgentLog): string {
  const d = (log as any).duration_ms
  if (typeof d === 'number') {
    if (d < 1000) return `${d}ms`
    return `${(d / 1000).toFixed(1)}s`
  }
  return ''
}

function toggleExpand(log: AgentLog) {
  const id = logId(log)
  if (expandedLogs.value.has(id)) {
    expandedLogs.value.delete(id)
  } else {
    expandedLogs.value.add(id)
  }
}

function isExpanded(log: AgentLog): boolean {
  return expandedLogs.value.has(logId(log))
}

async function fetchLogs() {
  const sessionId = activeSessionId.value
  if (!sessionId) {
    logs.value = []
    return
  }

  loading.value = true
  error.value = null
  try {
    logs.value = await logsApi.getSessionLogs(sessionId)
  } catch (e) {
    logs.value = []
    error.value = e instanceof Error ? e.message : '日志加载失败'
  } finally {
    loading.value = false
  }
}

watch(activeSessionId, fetchLogs, { immediate: true })

watch(
  () => chatStore.isStreaming,
  (streaming, wasStreaming) => {
    if (wasStreaming && !streaming) {
      fetchLogs()
    }
  },
)

const uniqueAgents = computed(() => [...new Set(logs.value.map(agentName))])
const filteredLogs = computed(() =>
  logs.value.filter(log => !filterAgent.value || agentName(log) === filterAgent.value),
)
</script>

<template>
  <div class="max-h-[600px] overflow-y-auto">
    <div class="mb-4 flex items-center justify-between gap-2">
      <el-select v-model="filterAgent" placeholder="全部 Agent" clearable size="small" style="width: 180px">
        <el-option v-for="agent in uniqueAgents" :key="agent" :value="agent">
          <div style="display: flex; align-items: center; gap: 8px">
            <span
              class="inline-block h-2.5 w-2.5 rounded-full"
              :style="{ backgroundColor: agentColors[agent] || '#94a3b8' }"
            />
            <span>{{ agentLabels[agent] || agent }}</span>
          </div>
        </el-option>
      </el-select>
      <span class="text-xs text-gray-400">{{ filteredLogs.length }} 条日志</span>
      <el-button size="small" link :loading="loading" @click="fetchLogs">刷新</el-button>
    </div>

    <div v-if="loading && !logs.length" class="py-8 text-center text-sm text-gray-400">
      正在加载 Agent 日志...
    </div>

    <div v-else-if="error" class="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-600">
      {{ error }}
    </div>

    <div v-else-if="!filteredLogs.length" class="py-8 text-center text-sm text-gray-400">
      当前会话暂无 Agent 调度日志，发送一条消息后刷新查看。
    </div>

    <div v-else class="flex flex-col">
      <div
        v-for="log in filteredLogs"
        :key="logId(log)"
        class="flex gap-3 py-3 cursor-pointer"
        @click="toggleExpand(log)"
      >
        <div class="flex w-6 shrink-0 flex-col items-center">
          <div
            class="h-3 w-3 rounded-full border-2 border-white shadow"
            :style="{ backgroundColor: agentColors[agentName(log)] || '#94a3b8' }"
          />
          <div class="mt-1 w-0.5 flex-1 bg-gray-200" />
        </div>

        <div class="flex-1 rounded-lg border border-gray-200 bg-gray-50 px-4 py-3 transition-all hover:shadow-sm">
          <div class="mb-2 flex items-center gap-2">
            <el-tag :color="agentColors[agentName(log)] || '#94a3b8'" effect="dark" size="small">
              {{ agentLabels[agentName(log)] || agentName(log) }}
            </el-tag>
            <span class="text-sm font-medium text-gray-700">{{ log.action }}</span>
            <span v-if="formatDuration(log)" class="text-xs text-amber-600 font-mono">
              {{ formatDuration(log) }}
            </span>
            <span class="ml-auto text-xs text-gray-400">{{ formatTime(log.timestamp) }}</span>
          </div>

          <!-- 折叠状态 -->
          <div v-if="!isExpanded(log)" class="space-y-1 text-xs text-gray-600">
            <p class="line-clamp-2"><span class="text-gray-400">操作：</span>{{ log.action }}</p>
          </div>

          <!-- 展开状态 -->
          <div v-else class="space-y-2 text-xs text-gray-600 mt-2">
            <div class="rounded bg-white p-2 border border-gray-100">
              <p class="font-semibold text-gray-500 mb-1">输入状态 (input_state):</p>
              <pre class="whitespace-pre-wrap text-gray-600 max-h-32 overflow-y-auto">{{ typeof log.state === 'object' ? JSON.stringify(log.state, null, 2) : log.state || 'N/A' }}</pre>
            </div>
            <div class="rounded bg-white p-2 border border-gray-100">
              <p class="font-semibold text-gray-500 mb-1">输出结果 (output_state):</p>
              <pre class="whitespace-pre-wrap text-gray-600 max-h-32 overflow-y-auto">{{ typeof log.result === 'object' ? JSON.stringify(log.result, null, 2) : log.result || 'N/A' }}</pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
