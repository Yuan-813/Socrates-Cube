<script setup lang="ts">
import { ref } from 'vue'

interface SimParams {
  windowSize: number
  rttDelay: number
  packetLossRate: number
}

const emit = defineEmits<{
  (e: 'rerun', params: SimParams): void
}>()

const windowSize = ref<number>(4096)
const rttDelay = ref<number>(50)
const packetLossRate = ref<number>(0)

const presets = [
  { label: '默认参数', windowSize: 4096, rttDelay: 50, packetLossRate: 0 },
  { label: '高延迟网络', windowSize: 2048, rttDelay: 300, packetLossRate: 5 },
  { label: '高丢包网络', windowSize: 4096, rttDelay: 100, packetLossRate: 20 },
  { label: '受限带宽', windowSize: 1024, rttDelay: 200, packetLossRate: 10 },
]

function applyPreset(preset: typeof presets[0]) {
  windowSize.value = preset.windowSize
  rttDelay.value = preset.rttDelay
  packetLossRate.value = preset.packetLossRate
}

function handleRerun() {
  emit('rerun', {
    windowSize: windowSize.value,
    rttDelay: rttDelay.value,
    packetLossRate: packetLossRate.value,
  })
}

function handleReset() {
  applyPreset(presets[0])
}
</script>

<template>
  <div class="sim-params-panel">
    <div class="params-header">
      <h4 class="params-title">
        <el-icon><Setting /></el-icon>
        仿真参数调节
      </h4>
      <el-button size="small" text type="info" @click="handleReset">重置默认</el-button>
    </div>

    <!-- 预设快捷选择 -->
    <div class="presets-row">
      <span class="presets-label">快捷预设：</span>
      <el-button
        v-for="p in presets"
        :key="p.label"
        size="small"
        @click="applyPreset(p)"
      >
        {{ p.label }}
      </el-button>
    </div>

    <!-- 窗口大小 -->
    <div class="param-item">
      <div class="param-label-row">
        <span class="param-label">窗口大小 (Window Size)</span>
        <span class="param-value">{{ windowSize }} bytes</span>
      </div>
      <el-slider
        v-model="windowSize"
        :min="512"
        :max="65535"
        :step="512"
        :format-tooltip="(val: number) => `${val} bytes`"
      />
      <div class="param-hint">控制发送端一次可发送的最大数据量，影响吞吐量与流量控制</div>
    </div>

    <!-- RTT 延迟 -->
    <div class="param-item">
      <div class="param-label-row">
        <span class="param-label">往返延迟 (RTT)</span>
        <span class="param-value">{{ rttDelay }} ms</span>
      </div>
      <el-slider
        v-model="rttDelay"
        :min="1"
        :max="1000"
        :step="10"
        :format-tooltip="(val: number) => `${val} ms`"
      />
      <div class="param-hint">模拟网络传播延迟，RTT 越高窗口利用率越低</div>
    </div>

    <!-- 丢包率 -->
    <div class="param-item">
      <div class="param-label-row">
        <span class="param-label">丢包率 (Packet Loss)</span>
        <span class="param-value">{{ packetLossRate }}%</span>
      </div>
      <el-slider
        v-model="packetLossRate"
        :min="0"
        :max="50"
        :step="1"
        :format-tooltip="(val: number) => `${val}%`"
      />
      <div class="param-hint">模拟网络丢包，触发重传与拥塞控制机制</div>
    </div>

    <!-- 重新仿真按钮 -->
    <div class="params-actions">
      <el-button type="primary" @click="handleRerun" style="width: 100%">
        <el-icon><RefreshRight /></el-icon>
        重新仿真（应用参数）
      </el-button>
    </div>
  </div>
</template>

<style scoped>
.sim-params-panel {
  background-color: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.params-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.params-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
}

.presets-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.presets-label {
  font-size: 12px;
  color: #64748b;
  white-space: nowrap;
}

.param-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.param-label-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.param-label {
  font-size: 13px;
  font-weight: 500;
  color: #334155;
}

.param-value {
  font-size: 13px;
  font-weight: 600;
  color: #3b82f6;
  font-family: 'JetBrains Mono', monospace;
}

.param-hint {
  font-size: 11px;
  color: #94a3b8;
  line-height: 1.4;
}

.params-actions {
  padding-top: 4px;
}
</style>
