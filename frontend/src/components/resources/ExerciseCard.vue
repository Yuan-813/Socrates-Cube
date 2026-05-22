<script setup lang="ts">
import { ref } from 'vue'
import type { ExerciseResource } from '@/types/resource'

const props = defineProps<{ resource: ExerciseResource }>()
const selectedOption = ref('')
const answered = ref(false)
const isCorrect = ref(false)

const typeLabel: Record<string, string> = {
  choice: '单选题',
  fill_blank: '填空题',
  scenario: '情景分析',
  packet_analysis: '报文分析',
}

function selectOption(label: string) {
  if (answered.value) return
  selectedOption.value = label
  answered.value = true
  isCorrect.value = label === props.resource.correct_answer
}

function getOptionClass(label: string) {
  if (!answered.value) {
    return selectedOption.value === label
      ? 'option-selected'
      : 'option-default'
  }
  if (label === props.resource.correct_answer) return 'option-correct'
  if (label === selectedOption.value) return 'option-wrong'
  return 'option-disabled'
}
</script>

<template>
  <div class="resource-card exercise-card">
    <div class="card-header">
      <span class="card-icon">✏️</span>
      <span class="card-title">{{ resource.title }}</span>
      <el-tag size="small" type="warning">{{ typeLabel[resource.exercise_type] || '练习' }}</el-tag>
    </div>
    <div class="card-body">
      <p class="question">{{ resource.question }}</p>

      <div v-if="resource.exercise_type === 'choice' && resource.options" class="options">
        <div
          v-for="opt in resource.options"
          :key="opt.label"
          :class="['option', getOptionClass(opt.label)]"
          @click="selectOption(opt.label)"
        >
          <strong>{{ opt.label }}.</strong> {{ opt.text }}
        </div>
      </div>

      <div v-if="answered" class="explanation">
        <p><strong>{{ isCorrect ? '✅ 回答正确！' : `❌ 正确答案：${resource.correct_answer}` }}</strong></p>
        <p>{{ resource.explanation }}</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.resource-card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 14px;
}
.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}
.card-title {
  font-weight: 600;
  flex: 1;
}
.question {
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 12px;
}
.options {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.option {
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}
.option-default:hover {
  border-color: #f59e0b;
  background: #fffbeb;
}
.option-selected {
  border-color: #f59e0b;
  background: #fffbeb;
}
.option-correct {
  border-color: #22c55e;
  background: #f0fdf4;
  color: #15803d;
}
.option-wrong {
  border-color: #ef4444;
  background: #fef2f2;
  color: #b91c1c;
}
.option-disabled {
  color: #94a3b8;
}
.explanation {
  margin-top: 12px;
  padding: 10px;
  background: #f0fdf4;
  border-radius: 8px;
  font-size: 13px;
  color: #15803d;
}
</style>
