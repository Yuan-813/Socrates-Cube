<script setup lang="ts">
import { computed, ref } from 'vue'
import type { DiagnosisResult } from '@/types'

const diagnosis = ref<DiagnosisResult>({
  is_correct: false,
  confidence: 0.86,
  surface_error: '把 HTTP 与 TCP/IP 层次关系混淆',
  error_type: 'conceptual',
  root_causes: ['TCP/IP 分层封装机制理解不充分', '应用层与传输层职责边界不清'],
  missing_prerequisites: ['kn_001', 'kn_005'],
  pattern: '层次穿越型',
  intervention_suggestion: '用 HTTP -> TCP -> IP -> Ethernet 的封装链路进行对比追问。',
  related_node_ids: ['kn_001', 'kn_005'],
})

const confidencePercent = computed(() => Math.round((diagnosis.value.confidence ?? 0) * 100))
</script>

<template>
  <div class="space-y-6">
    <section class="rounded-lg border border-amber-200 bg-amber-50 p-4">
      <div class="mb-2 flex items-center gap-2 font-semibold text-amber-800">
        <el-icon><Warning /></el-icon>
        <span>诊断触发</span>
      </div>
      <p class="text-sm leading-6 text-amber-900">
        {{ diagnosis.trigger || '系统检测到回答中可能存在概念边界或协议流程误区。' }}
      </p>
    </section>

    <div class="grid grid-cols-1 gap-4 md:grid-cols-3">
      <section class="rounded-lg border border-gray-200 bg-white p-4">
        <div class="mb-3 text-xs font-semibold uppercase text-gray-400">第一层</div>
        <h3 class="mb-2 font-semibold text-gray-900">表层错误识别</h3>
        <el-tag :type="diagnosis.is_correct ? 'success' : 'danger'" effect="dark">
          {{ diagnosis.is_correct ? '理解正确' : diagnosis.surface_error }}
        </el-tag>
        <p class="mt-3 text-sm leading-6 text-gray-600">
          错误类型：{{ diagnosis.error_type || 'none' }}
        </p>
      </section>

      <section class="rounded-lg border border-gray-200 bg-white p-4">
        <div class="mb-3 text-xs font-semibold uppercase text-gray-400">第二层</div>
        <h3 class="mb-2 font-semibold text-gray-900">根因分析</h3>
        <el-progress :percentage="confidencePercent" color="#3b82f6" />
        <ul class="mt-3 space-y-2 text-sm text-gray-600">
          <li v-for="cause in diagnosis.root_causes || []" :key="cause">• {{ cause }}</li>
        </ul>
      </section>

      <section class="rounded-lg border border-gray-200 bg-white p-4">
        <div class="mb-3 text-xs font-semibold uppercase text-gray-400">第三层</div>
        <h3 class="mb-2 font-semibold text-gray-900">误区模式匹配</h3>
        <el-tag type="warning" effect="dark">{{ diagnosis.pattern || '无明确模式' }}</el-tag>
        <p class="mt-3 text-sm leading-6 text-gray-600">
          {{ diagnosis.intervention_suggestion }}
        </p>
      </section>
    </div>

    <section class="rounded-lg border border-gray-200 bg-white p-5">
      <h3 class="mb-4 font-semibold text-gray-900">TCP/IP 分层封装示意</h3>
      <div class="space-y-2">
        <div class="rounded border-l-4 border-amber-400 bg-gray-50 px-4 py-3">
          <div class="font-medium text-amber-700">应用层</div>
          <div class="text-sm text-gray-500">HTTP / DNS / FTP</div>
        </div>
        <div class="rounded border-l-4 border-blue-400 bg-gray-50 px-4 py-3">
          <div class="font-medium text-blue-700">传输层</div>
          <div class="text-sm text-gray-500">TCP / UDP / QUIC</div>
        </div>
        <div class="rounded border-l-4 border-emerald-400 bg-gray-50 px-4 py-3">
          <div class="font-medium text-emerald-700">网络层</div>
          <div class="text-sm text-gray-500">IP / ICMP</div>
        </div>
        <div class="rounded border-l-4 border-violet-400 bg-gray-50 px-4 py-3">
          <div class="font-medium text-violet-700">数据链路层</div>
          <div class="text-sm text-gray-500">Ethernet / Wi-Fi</div>
        </div>
      </div>
    </section>
  </div>
</template>
