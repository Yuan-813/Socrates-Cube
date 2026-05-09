<script setup lang="ts">
import DiagnosisPanel from '@/components/DiagnosisPanel.vue'
</script>

<template>
  <div class="space-y-6">
    <div class="card">
      <h2 class="section-title">认知诊断报告</h2>
      <p class="section-desc">三层诊断引擎：表面错误识别 → 根因溯源分析 → 误解模式匹配</p>
      <DiagnosisPanel />
    </div>
  </div>
</template>
