<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/userStore'
import {
  PROFILE_DIMENSION_LABELS,
  PROFILE_DIMENSION_ICONS,
} from '@/types'

const userStore = useUserStore()
const router = useRouter()

const PROFILE_DIMS = [
  'conceptual_understanding',
  'protocol_analysis',
  'calculation_ability',
  'error_diagnosis',
  'system_design',
  'knowledge_connection',
  'expression_clarity',
  'self_correction',
]

const DIM_COLORS: Record<string, string> = {
  conceptual_understanding: '#3b82f6',
  protocol_analysis:        '#10b981',
  calculation_ability:      '#06b6d4',
  error_diagnosis:          '#ef4444',
  system_design:            '#8b5cf6',
  knowledge_connection:     '#6366f1',
  expression_clarity:       '#ec4899',
  self_correction:          '#f97316',
}

const overallScore = computed(() => {
  const s = userStore.radarScores
  return Math.round(s.reduce((a, b) => a + b, 0) / s.length)
})

function scoreColor(s: number) {
  if (s >= 80) return '#22c55e'
  if (s >= 60) return '#84cc16'
  if (s >= 40) return '#eab308'
  if (s >= 20) return '#f97316'
  return '#ef4444'
}

function scoreLabel(s: number) {
  if (s >= 80) return '优秀'
  if (s >= 60) return '良好'
  if (s >= 40) return '中等'
  if (s >= 20) return '较弱'
  return '薄弱'
}

const dimensions = computed(() =>
  PROFILE_DIMS.map((k, i) => ({
    key: k,
    name: PROFILE_DIMENSION_LABELS[k] ?? k,
    icon: PROFILE_DIMENSION_ICONS[k] ?? '📌',
    score: userStore.radarScores[i] ?? 0,
    color: DIM_COLORS[k],
  }))
)

const weakDims = computed(() =>
  [...dimensions.value].sort((a, b) => a.score - b.score).slice(0, 3)
)

const overallColor = computed(() => scoreColor(overallScore.value))
const overallLbl = computed(() => scoreLabel(overallScore.value))
</script>

<template>
  <div class="profile-summary">

    <!-- ① 总分卡片 -->
    <div class="overall-card">
      <div class="overall-left">
        <!-- SVG 环形进度 -->
        <svg width="56" height="56" viewBox="0 0 56 56" class="score-ring-svg">
          <circle cx="28" cy="28" r="22" fill="none" stroke="#e8eef8" stroke-width="6"/>
          <circle
            cx="28" cy="28" r="22" fill="none"
            :stroke="overallColor"
            stroke-width="6"
            stroke-linecap="round"
            :stroke-dasharray="`${overallScore * 1.382} 138.2`"
            stroke-dashoffset="34.5"
          />
          <text x="28" y="33" text-anchor="middle"
            :fill="overallColor"
            font-size="14" font-weight="800">{{ overallScore }}</text>
        </svg>
        <div class="overall-meta">
          <span class="overall-label">综合能力置信度</span>
          <span class="overall-badge" :style="{ background: overallColor + '20', color: overallColor }">
            {{ overallLbl }}
          </span>
        </div>
      </div>
      <button class="goto-btn" @click="router.push('/profile')">
        完整画像
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7"/></svg>
      </button>
    </div>

    <!-- ② 8维横向进度条 -->
    <div class="dim-list">
      <div class="dim-list-header">
        <span class="dim-list-title">八维能力分布</span>
      </div>
      <div
        v-for="dim in dimensions"
        :key="dim.key"
        class="dim-row"
      >
        <span class="dim-icon">{{ dim.icon }}</span>
        <span class="dim-name">{{ dim.name }}</span>
        <div class="dim-bar-wrap">
          <div
            class="dim-bar-fill"
            :style="{ width: dim.score + '%', background: dim.color }"
          />
        </div>
        <span class="dim-score" :style="{ color: dim.color }">{{ dim.score }}</span>
      </div>
    </div>

    <!-- ③ 最弱3项快捷提示 -->
    <div class="weak-section">
      <div class="weak-header">
        <span class="weak-icon">⚠️</span>
        <span class="weak-title">待强化维度</span>
      </div>
      <div class="weak-list">
        <div
          v-for="dim in weakDims"
          :key="dim.key"
          class="weak-item"
          :style="{ borderColor: dim.color + '60' }"
        >
          <span class="weak-item-icon">{{ dim.icon }}</span>
          <span class="weak-item-name">{{ dim.name }}</span>
          <span class="weak-item-score" :style="{ color: scoreColor(dim.score) }">{{ dim.score }}分</span>
          <button
            class="weak-item-btn"
            :style="{ background: dim.color }"
            @click="router.push({ path: '/resources', query: { topic: dim.name } })"
          >强化</button>
        </div>
      </div>
    </div>

  </div>
</template>

<style scoped>
.profile-summary {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

/* ── 总分卡片 ── */
.overall-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 16px;
  background: linear-gradient(135deg, #f0f4ff 0%, #f8faff 100%);
  border: 1px solid #dbeafe;
  border-radius: 14px;
}

.overall-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.score-ring-svg {
  flex-shrink: 0;
}

.overall-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.overall-label {
  font-size: 12px;
  font-weight: 600;
  color: #1e293b;
}

.overall-badge {
  display: inline-block;
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 10px;
  width: fit-content;
}

.goto-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 6px 10px;
  background: white;
  border: 1px solid #dbeafe;
  border-radius: 8px;
  font-size: 11px;
  font-weight: 600;
  color: #3b82f6;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.18s;
  flex-shrink: 0;
}
.goto-btn:hover {
  background: #eff6ff;
  border-color: #93c5fd;
}

/* ── 8维进度条 ── */
.dim-list {
  background: white;
  border: 1px solid #e8eef8;
  border-radius: 12px;
  padding: 12px 14px;
}

.dim-list-header {
  margin-bottom: 10px;
}

.dim-list-title {
  font-size: 12px;
  font-weight: 700;
  color: #475569;
}

.dim-row {
  display: flex;
  align-items: center;
  gap: 7px;
  margin-bottom: 7px;
}
.dim-row:last-child {
  margin-bottom: 0;
}

.dim-icon {
  font-size: 13px;
  width: 16px;
  text-align: center;
  flex-shrink: 0;
}

.dim-name {
  font-size: 11.5px;
  color: #475569;
  width: 56px;
  flex-shrink: 0;
  white-space: nowrap;
}

.dim-bar-wrap {
  flex: 1;
  height: 5px;
  background: #f1f5f9;
  border-radius: 3px;
  overflow: hidden;
}

.dim-bar-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.5s ease;
  opacity: 0.85;
}

.dim-score {
  font-size: 11px;
  font-weight: 700;
  width: 22px;
  text-align: right;
  flex-shrink: 0;
}

/* ── 待强化 ── */
.weak-section {
  background: white;
  border: 1px solid #e8eef8;
  border-radius: 12px;
  padding: 12px 14px;
}

.weak-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 10px;
}

.weak-icon { font-size: 13px; }
.weak-title {
  font-size: 12px;
  font-weight: 700;
  color: #475569;
}

.weak-list {
  display: flex;
  flex-direction: column;
  gap: 7px;
}

.weak-item {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 7px 10px;
  background: #fafbff;
  border: 1px solid;
  border-radius: 8px;
}

.weak-item-icon { font-size: 13px; flex-shrink: 0; }

.weak-item-name {
  flex: 1;
  font-size: 12px;
  font-weight: 600;
  color: #334155;
  min-width: 0;
  white-space: nowrap;
}

.weak-item-score {
  font-size: 11px;
  font-weight: 700;
  white-space: nowrap;
  flex-shrink: 0;
}

.weak-item-btn {
  flex-shrink: 0;
  padding: 3px 9px;
  border: none;
  border-radius: 6px;
  color: white;
  font-size: 10px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.18s;
  white-space: nowrap;
  opacity: 0.9;
}
.weak-item-btn:hover {
  opacity: 1;
  transform: scale(1.04);
}
</style>
