<script setup lang="ts">
import { computed } from 'vue'
import { useChatStore } from '@/stores/chatStore'
import { usePathStore } from '@/stores/pathStore'
import { resolveNodeName } from '@/utils/kgMap'

const chatStore = useChatStore()
const pathStore = usePathStore()

const diag = computed(() => chatStore.lastDiagnosis)
const path = computed(() => pathStore.path)

/** 是否有足够信息展示总览 */
const hasOverview = computed(() =>
  diag.value && !diag.value.is_correct && (
    diag.value.knowledge_node_ids?.length ||
    diag.value.acu_ids?.length ||
    diag.value.recommended_interventions?.length
  ),
)

/** 推荐干预类型 → 中文展示 */
const interventionTypeLabels: Record<string, string> = {
  simulation: '协议仿真演示',
  exercise: '对比练习题',
  challenge: '智能追问验证',
  doc: '知识文档讲解',
  contrast_table: '对比表格',
  follow_up_question: '追问引导',
}

function resolveIntervention(item: any): string {
  if (typeof item === 'string') return interventionTypeLabels[item] ?? item
  return interventionTypeLabels[item?.type] ?? item?.label ?? '修复练习'
}

/** 当前路径第一个 pending/in_progress 节点 */
const nextPathNode = computed(() =>
  path.value?.nodes.find(n => n.status === 'pending' || n.status === 'in_progress'),
)

/** 修复置信度：直接使用诺断 Agent 输出的 confidence 字段 */
const repairConfidence = computed(() => {
  const conf = diag.value?.confidence ?? 0
  return Math.round(conf * 100)
})

/** 置信度等级说明 */
const confidenceLabel = computed(() => {
  const c = repairConfidence.value
  if (c >= 85) return { text: '高置信', color: '#16a34a' }
  if (c >= 70) return { text: '中置信', color: '#2563eb' }
  if (c >= 50) return { text: '低置信', color: '#d97706' }
  return { text: '待确认', color: '#dc2626' }
})
</script>

<template>
  <div v-if="hasOverview" class="repair-overview">
    <div class="overview-header">
      <span class="overview-icon">🎯</span>
      <span class="overview-title">AI 认知修复方案</span>
    </div>

    <!-- 问题定位 -->
    <div class="overview-body">
      <div class="step-row">
        <span class="step-dot dot-red"></span>
        <div class="step-content">
          <span class="step-label">检测到的问题</span>
          <p class="step-value error">{{ diag!.surface_error || diag!.pattern || '认知偏差' }}</p>
        </div>
      </div>

      <!-- 课程节点定位 -->
      <div v-if="diag!.knowledge_node_ids?.length" class="step-row">
        <span class="step-dot dot-blue"></span>
        <div class="step-content">
          <span class="step-label">📚 知识缺口定位</span>
          <div class="tag-group">
            <span
              v-for="id in diag!.knowledge_node_ids"
              :key="id"
              class="mini-tag blue"
            >{{ resolveNodeName(id) }}</span>
          </div>
        </div>
      </div>

      <!-- 认知单元定位 -->
      <div v-if="diag!.acu_ids?.length" class="step-row">
        <span class="step-dot dot-orange"></span>
        <div class="step-content">
          <span class="step-label">🧠 认知缺陷定位</span>
          <div class="tag-group">
            <span
              v-for="id in diag!.acu_ids"
              :key="id"
              class="mini-tag orange"
            >{{ resolveNodeName(id) }}</span>
          </div>
        </div>
      </div>

      <!-- 修复方案 -->
      <div v-if="diag!.recommended_interventions?.length" class="step-row">
        <span class="step-dot dot-green"></span>
        <div class="step-content">
          <span class="step-label">🛠️ 推荐修复方式</span>
          <div class="tag-group">
            <span
              v-for="(item, i) in diag!.recommended_interventions!.slice(0, 3)"
              :key="i"
              class="mini-tag green"
            >{{ resolveIntervention(item) }}</span>
          </div>
        </div>
      </div>

      <!-- 下一步路径节点 -->
      <div v-if="nextPathNode" class="step-row">
        <span class="step-dot dot-purple"></span>
        <div class="step-content">
          <span class="step-label">📖 建议学习节点</span>
          <p class="step-value">{{ nextPathNode.node_name }}</p>
        </div>
      </div>

      <!-- 能力提升预估 -->
      <div class="boost-row">
        <span class="boost-label">诺断置信度</span>
        <span class="boost-value" :style="{ color: confidenceLabel.color }">
          {{ repairConfidence }}% <span class="boost-level">{{ confidenceLabel.text }}</span>
        </span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.repair-overview {
  background: linear-gradient(135deg, #f0fdf4, #ecfdf5);
  border: 1px solid #86efac;
  border-radius: 12px;
  overflow: hidden;
}

.overview-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: linear-gradient(90deg, #16a34a, #15803d);
}
.overview-icon { font-size: 16px; }
.overview-title {
  font-size: 13px;
  font-weight: 700;
  color: #fff;
  letter-spacing: 0.5px;
}

.overview-body {
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.step-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.step-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: 5px;
}
.dot-red    { background: #ef4444; }
.dot-blue   { background: #3b82f6; }
.dot-orange { background: #f59e0b; }
.dot-green  { background: #10b981; }
.dot-purple { background: #8b5cf6; }

.step-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}
.step-label {
  font-size: 11px;
  color: #64748b;
  font-weight: 500;
}
.step-value {
  font-size: 13px;
  color: #1e293b;
  line-height: 1.4;
  margin: 0;
}
.step-value.error { color: #dc2626; font-weight: 500; }

.tag-group {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}
.mini-tag {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 500;
  line-height: 1.5;
}
.mini-tag.blue   { background: #dbeafe; color: #1d4ed8; }
.mini-tag.orange { background: #fef3c7; color: #92400e; }
.mini-tag.green  { background: #d1fae5; color: #065f46; }

.boost-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 10px;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 8px;
  border: 1px solid #bbf7d0;
  margin-top: 4px;
}
.boost-label { font-size: 12px; color: #64748b; }
.boost-value {
  font-size: 16px;
  font-weight: 700;
  font-family: 'JetBrains Mono', monospace;
}
.boost-level { font-size: 11px; font-weight: 500; margin-left: 4px; }
</style>
