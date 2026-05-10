<script setup lang="ts">
import { computed } from 'vue'
import SimulatorPlayer from '@/components/SimulatorPlayer.vue'
import { useAssistantStore } from '@/stores/assistantStore'

const assistantStore = useAssistantStore()
const simulatorSummary = computed(() => assistantStore.simulatorSummary)
</script>

<template>
  <div class="space-y-6">
    <div class="card">
      <h2 class="section-title">协议仿真实验室</h2>
      <p class="section-desc">可视化交互式协议流程仿真，支持播放控制与参数调节</p>
      <el-alert
        :title="simulatorSummary"
        type="info"
        :closable="false"
        show-icon
        class="mb-4"
      />
      <SimulatorPlayer />
    </div>
  </div>
</template>
