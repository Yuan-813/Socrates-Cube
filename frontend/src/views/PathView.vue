<script setup lang="ts">
import PathTimeline from '@/components/PathTimeline.vue'
</script>

<template>
  <div class="space-y-6">
    <div class="card">
      <h2 class="section-title">可解释学习路径</h2>
      <p class="section-desc">基于知识图谱依赖关系与诊断结果动态规划的学习路线</p>
      <PathTimeline />
    </div>
  </div>
</template>
