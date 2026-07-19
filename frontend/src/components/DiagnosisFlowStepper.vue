<script setup lang="ts">
import { computed } from 'vue'
import { useChatStore } from '@/stores/chatStore'

const chatStore = useChatStore()

const steps = [
  { id: 'input',     label: '学生回答',   icon: '✏️', desc: '接收学生输入' },
  { id: 'diagnosis', label: 'AI诊断',    icon: '🔬', desc: '三层认知分析' },
  { id: 'graph',     label: '图谱定位',   icon: '🗺️', desc: '双层知识图谱' },
  { id: 'repair',    label: '修复规划',   icon: '🛠️', desc: '路径+资源生成' },
  { id: 'update',    label: '画像更新',   icon: '📈', desc: '掌握度提升' },
]

/**
 * 域外拦截模式：有 scope_notice 且无诊断结果
 */
const isScopeRejected = computed(() =>
  chatStore.lastScopeNotice !== null &&
  chatStore.lastScopeNotice !== undefined &&
  !chatStore.lastDiagnosis
)

/**
 * 推进步骤：
 * - 域外拦截             → input blocked（拦截标识）
 * - 未开始对话         → 停在 input（灰）
 * - 正在流式且无诊断    → diagnosis 脉冲中
 * - 有诊断且有错误  → graph/repair 激活
 * - 有诊断且正确       → update 激活
 */
const activeStep = computed(() => {
  if (isScopeRejected.value) return 'scope_blocked'
  if (chatStore.isStreaming && !chatStore.lastDiagnosis) return 'diagnosis'
  if (!chatStore.lastDiagnosis) return 'input'
  if (!chatStore.lastDiagnosis.is_correct) return 'repair'
  return 'update'
})

function stepState(stepId: string): 'done' | 'active' | 'pending' | 'blocked' {
  if (activeStep.value === 'scope_blocked') {
    return stepId === 'input' ? 'blocked' : 'pending'
  }
  const order = steps.map(s => s.id)
  const activeIdx = order.indexOf(activeStep.value)
  const stepIdx  = order.indexOf(stepId)
  if (stepIdx < activeIdx)  return 'done'
  if (stepIdx === activeIdx) return 'active'
  return 'pending'
}
</script>

<template>
  <div class="flow-stepper">
    <div class="steps-track">
      <div
        v-for="(step, i) in steps"
        :key="step.id"
        class="step-item"
        :class="stepState(step.id)"
      >
        <!-- 连接线（第一个之前不显示） -->
        <div v-if="i > 0" class="step-connector">
          <div
            class="connector-fill"
            :class="{ filled: stepState(step.id) === 'done' || stepState(steps[i - 1].id) === 'active' }"
          ></div>
        </div>

        <!-- 圆形节点 -->
        <div class="step-circle" :class="stepState(step.id)">
          <span v-if="stepState(step.id) === 'done'" class="circle-check">✓</span>
          <span v-else-if="stepState(step.id) === 'blocked'" class="circle-block">🛡️</span>
          <span v-else class="circle-icon">{{ step.icon }}</span>
          <div v-if="stepState(step.id) === 'active'" class="circle-pulse"></div>
        </div>

        <!-- 标签（仅显示主标签，去掉 desc） -->
        <div class="step-label-group">
          <span class="step-label">{{ step.label }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.flow-stepper {
  padding: 12px 10px;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
}

.steps-track {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  position: relative;
}

.step-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
  flex: 1;
  position: relative;
  z-index: 1;
}

/* 连接线 */
.step-connector {
  position: absolute;
  top: 13px;   /* center of 26px circle */
  right: 50%;
  left: -50%;
  height: 2px;
  z-index: 0;
}
.connector-fill {
  width: 100%;
  height: 100%;
  background: #e2e8f0;
  transition: background 0.4s;
}
.connector-fill.filled {
  background: linear-gradient(90deg, #3b82f6, #60a5fa);
}

/* 圆形节点（缩小至26px） */
.step-circle {
  position: relative;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  border: 2px solid #e2e8f0;
  background: #f8fafc;
  transition: all 0.3s;
  flex-shrink: 0;
}
.step-circle.done {
  background: #dbeafe;
  border-color: #3b82f6;
}
.step-circle.active {
  background: #eff6ff;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.12);
}
.step-circle.blocked {
  background: #fef3c7;
  border-color: #f59e0b;
  box-shadow: 0 0 0 3px rgba(245, 158, 11, 0.15);
}
.circle-check {
  font-size: 11px;
  font-weight: 700;
  color: #2563eb;
}
.circle-block { font-size: 12px; }
.circle-icon { font-size: 13px; }

/* 脉冲动画 */
.circle-pulse {
  position: absolute;
  inset: -4px;
  border-radius: 50%;
  border: 2px solid #3b82f6;
  animation: stepper-pulse 1.4s ease-out infinite;
}
@keyframes stepper-pulse {
  0%   { opacity: 1; transform: scale(1); }
  100% { opacity: 0; transform: scale(1.5); }
}

/* 标签（许屁行） */
.step-label-group {
  display: flex;
  flex-direction: column;
  align-items: center;
}
.step-label {
  font-size: 10px;
  font-weight: 600;
  color: #1e293b;
  text-align: center;
  line-height: 1.3;
  word-break: keep-all;
  max-width: 48px;
}
.step-item.pending .step-label { color: #94a3b8; }
.step-item.done    .step-label { color: #2563eb; }
.step-item.active  .step-label { color: #1d4ed8; }
.step-item.blocked .step-label { color: #d97706; font-weight: 700; }
</style>
