<script setup lang="ts">
import { computed } from 'vue'

export interface TcpStateDef {
  name: string
  color: string
  role: 'client' | 'server' | 'both'
}

const props = withDefaults(defineProps<{
  clientState?: string
  serverState?: string
  scenario?: string
  compact?: boolean
}>(), {
  clientState: 'CLOSED',
  serverState: 'LISTEN',
  scenario: 'three_way_handshake',
  compact: false,
})

const tcpStates: TcpStateDef[] = [
  { name: 'CLOSED', color: '#ef4444', role: 'client' },
  { name: 'LISTEN', color: '#3b82f6', role: 'server' },
  { name: 'SYN_SENT', color: '#f59e0b', role: 'client' },
  { name: 'SYN_RCVD', color: '#8b5cf6', role: 'server' },
  { name: 'ESTABLISHED', color: '#10b981', role: 'both' },
  { name: 'FIN_WAIT_1', color: '#f97316', role: 'client' },
  { name: 'FIN_WAIT_2', color: '#f97316', role: 'client' },
  { name: 'CLOSE_WAIT', color: '#06b6d4', role: 'server' },
  { name: 'LAST_ACK', color: '#ec4899', role: 'server' },
  { name: 'TIME_WAIT', color: '#eab308', role: 'client' },
]

const supportsStateMachine = computed(() =>
  props.scenario === 'three_way_handshake' || props.scenario === 'four_way_wavehand',
)

function isStateActive(stateName: string): boolean {
  return props.clientState === stateName || props.serverState === stateName
}

function roleLabel(role: TcpStateDef['role']): string {
  if (role === 'both') return 'Client / Server'
  return role === 'client' ? 'Client' : 'Server'
}
</script>

<template>
  <div class="state-machine-card" :class="{ compact }">
    <h4 class="panel-title">
      <el-icon><SetUp /></el-icon>
      TCP 状态机
    </h4>

    <div v-if="!supportsStateMachine" class="state-machine-fallback">
      <p>当前场景「{{ scenario }}」使用步骤状态展示，不适用 TCP 连接状态机。</p>
      <div class="live-states">
        <el-tag type="primary" effect="plain">Client: {{ clientState }}</el-tag>
        <el-tag type="success" effect="plain">Server: {{ serverState }}</el-tag>
      </div>
    </div>

    <div v-else class="state-diagram">
      <div
        v-for="state in tcpStates"
        :key="state.name"
        class="state-node"
        :class="{ active: isStateActive(state.name) }"
        :style="{
          borderColor: isStateActive(state.name) ? state.color : '#e2e8f0',
          backgroundColor: isStateActive(state.name) ? state.color + '15' : '#f8fafc',
        }"
      >
        <div
          class="state-name"
          :style="{ color: isStateActive(state.name) ? state.color : '#64748b' }"
        >
          {{ state.name }}
        </div>
        <div v-if="isStateActive(state.name)" class="state-role">
          {{ roleLabel(state.role) }}
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.state-machine-card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 14px;
}

.state-machine-card.compact {
  padding: 10px;
}

.panel-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 12px;
}

.state-diagram {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.state-machine-card.compact .state-diagram {
  grid-template-columns: repeat(3, 1fr);
  gap: 6px;
}

.state-node {
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  padding: 8px 10px;
  transition: all 0.25s ease;
}

.state-node.active {
  transform: scale(1.03);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.state-name {
  font-size: 12px;
  font-weight: 700;
  font-family: 'JetBrains Mono', monospace;
}

.state-role {
  font-size: 10px;
  color: #64748b;
  margin-top: 2px;
}

.state-machine-fallback {
  font-size: 12px;
  color: #64748b;
  line-height: 1.5;
}

.state-machine-fallback p {
  margin: 0 0 10px;
}

.live-states {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
</style>
