<script setup lang="ts">
import AgentLogPanel from '@/components/AgentLogPanel.vue'
</script>

<template>
  <div class="space-y-6">
    <div class="card">
      <h2 class="section-title">多智能体协作日志</h2>
      <p class="section-desc">实时追踪各Agent的调度、推理与执行状态</p>
      <AgentLogPanel />
    </div>
  </div>
</template>
