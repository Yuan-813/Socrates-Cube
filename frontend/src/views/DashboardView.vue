<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useUserStore } from '@/stores/userStore'
import { statsApi } from '@/api/stats'
import type { StatsSummary } from '@/api/stats'
import * as echarts from 'echarts'

const userStore = useUserStore()

const loading = ref(true)
const stats = ref<StatsSummary | null>(null)

// ECharts refs
const masteryChartRef = ref<HTMLDivElement | null>(null)
const radarChartRef = ref<HTMLDivElement | null>(null)
const scoreTrendRef = ref<HTMLDivElement | null>(null)

const radarDimLabels: Record<string, string> = {
  conceptual_understanding: '概念理解',
  protocol_analysis: '协议分析',
  calculation_ability: '计算能力',
  error_diagnosis: '错误诊断',
  system_design: '系统设计',
  knowledge_connection: '知识关联',
  expression_clarity: '表达清晰',
  self_correction: '自我纠错',
}

// 概览卡片数据
const overviewCards = computed(() => {
  const s = stats.value
  if (!s) return []
  return [
    {
      label: '累计学习天数',
      value: s.learning_days,
      unit: '天',
      icon: '📅',
      color: '#3b82f6',
      bg: '#eff6ff',
      desc: '持续学习',
    },
    {
      label: '总对话轮次',
      value: s.total_messages,
      unit: '条',
      icon: '💬',
      color: '#8b5cf6',
      bg: '#faf5ff',
      desc: 'AI 对话次数',
    },
    {
      label: '知识整体掌握度',
      value: s.overall_mastery,
      unit: '%',
      icon: '📊',
      color: '#10b981',
      bg: '#f0fdf4',
      desc: '8维综合评分',
    },
    {
      label: '诊断次数',
      value: s.assessment_count,
      unit: '次',
      icon: '🔍',
      color: '#ef4444',
      bg: '#fef2f2',
      desc: `平均得分 ${s.diagnosis_avg_score}`,
    },
  ]
})

async function loadStats() {
  loading.value = true
  try {
    stats.value = await statsApi.getSummary(userStore.userId)
  } catch {
    // 降级展示 userStore 本地数据
    const profile = userStore.profile
    stats.value = {
      user_id: userStore.userId,
      total_sessions: 0,
      total_messages: 0,
      learning_days: 0,
      overall_mastery: userStore.profileCompleteness,
      mastery_history: userStore.masteryHistory.length ? userStore.masteryHistory : [userStore.profileCompleteness],
      radar_scores: userStore.radarScores,
      radar_dims: Object.keys(radarDimLabels),
      weak_points: profile.weak_points?.slice(0, 5) ?? [],
      assessment_count: 0,
      diagnosis_avg_score: 0,
      score_trend: [],
      chapter_progress: 0,
      knowledge_nodes_count: 0,
    }
  } finally {
    loading.value = false
    // 下一帧渲染图表
    setTimeout(() => {
      renderMasteryChart()
      renderRadarChart()
      renderScoreTrend()
    }, 100)
  }
}

function renderMasteryChart() {
  if (!masteryChartRef.value || !stats.value) return
  const chart = echarts.init(masteryChartRef.value)
  const history = stats.value.mastery_history
  const labels = history.map((_, i) => `第${i + 1}次`)

  chart.setOption({
    tooltip: { trigger: 'axis', formatter: '{b}<br/>掌握度：{c}%' },
    grid: { left: 36, right: 16, top: 16, bottom: 30 },
    xAxis: {
      type: 'category',
      data: labels,
      axisLabel: { fontSize: 11, color: '#94a3b8' },
      axisLine: { lineStyle: { color: '#e2e8f0' } },
    },
    yAxis: {
      type: 'value',
      min: 0, max: 100,
      axisLabel: { formatter: '{value}%', fontSize: 11, color: '#94a3b8' },
      splitLine: { lineStyle: { color: '#f1f5f9', type: 'dashed' } },
    },
    series: [{
      type: 'line',
      data: history,
      smooth: true,
      symbol: 'circle',
      symbolSize: 6,
      lineStyle: { width: 3, color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
        { offset: 0, color: '#3b82f6' },
        { offset: 1, color: '#8b5cf6' },
      ]) },
      itemStyle: { color: '#6366f1', borderWidth: 2, borderColor: '#fff' },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(99,102,241,0.18)' },
          { offset: 1, color: 'rgba(99,102,241,0)' },
        ]),
      },
    }],
  })
  window.addEventListener('resize', () => chart.resize())
}

function renderRadarChart() {
  if (!radarChartRef.value || !stats.value) return
  const chart = echarts.init(radarChartRef.value)
  const dims = stats.value.radar_dims
  const scores = stats.value.radar_scores

  chart.setOption({
    tooltip: {},
    radar: {
      indicator: dims.map((d) => ({
        name: radarDimLabels[d] || d,
        max: 100,
      })),
      shape: 'polygon',
      axisName: { fontSize: 11, color: '#64748b' },
      splitArea: { areaStyle: { color: ['rgba(99,102,241,0.02)', 'rgba(99,102,241,0.05)'] } },
      axisLine: { lineStyle: { color: '#e2e8f0' } },
      splitLine: { lineStyle: { color: '#e8eef8' } },
    },
    series: [{
      type: 'radar',
      data: [{
        value: scores,
        name: '能力维度',
        areaStyle: { color: 'rgba(99,102,241,0.15)' },
        lineStyle: { color: '#6366f1', width: 2 },
        itemStyle: { color: '#6366f1' },
      }],
    }],
  })
  window.addEventListener('resize', () => chart.resize())
}

function renderScoreTrend() {
  if (!scoreTrendRef.value || !stats.value) return
  const trend = stats.value.score_trend
  if (!trend.length) return
  const chart = echarts.init(scoreTrendRef.value)

  chart.setOption({
    tooltip: { trigger: 'axis', formatter: '{b}<br/>得分：{c}' },
    grid: { left: 36, right: 16, top: 16, bottom: 30 },
    xAxis: {
      type: 'category',
      data: trend.map(t => t.time),
      axisLabel: { fontSize: 11, color: '#94a3b8' },
      axisLine: { lineStyle: { color: '#e2e8f0' } },
    },
    yAxis: {
      type: 'value',
      min: 0, max: 100,
      axisLabel: { formatter: '{value}', fontSize: 11, color: '#94a3b8' },
      splitLine: { lineStyle: { color: '#f1f5f9', type: 'dashed' } },
    },
    series: [{
      type: 'bar',
      data: trend.map(t => ({
        value: t.score,
        itemStyle: { color: t.score >= 80 ? '#10b981' : t.score >= 60 ? '#f59e0b' : '#ef4444' },
      })),
      barMaxWidth: 32,
      borderRadius: [4, 4, 0, 0],
    }],
  })
  window.addEventListener('resize', () => chart.resize())
}

onMounted(loadStats)
</script>

<template>
  <div class="dashboard-view">
    <!-- 页头 -->
    <div class="dash-header">
      <div>
        <h2 class="dash-title">学习数据统计</h2>
        <p class="dash-sub">基于 AI 对话与诊断记录，全面展示你的学习成长轨迹</p>
      </div>
      <button class="refresh-btn" @click="loadStats" :disabled="loading">
        <el-icon :class="{ rotating: loading }"><Refresh /></el-icon>
        刷新数据
      </button>
    </div>

    <!-- 加载骨架 -->
    <div v-if="loading" class="skeleton-wrap">
      <div v-for="i in 4" :key="i" class="skeleton-card" />
      <div class="skeleton-chart" />
      <div class="skeleton-chart" />
    </div>

    <template v-else-if="stats">
      <!-- 行1：概览卡片 -->
      <div class="overview-grid">
        <div
          v-for="card in overviewCards"
          :key="card.label"
          class="ov-card"
          :style="{ background: card.bg }"
        >
          <div class="ov-icon" :style="{ background: card.color + '22' }">{{ card.icon }}</div>
          <div class="ov-body">
            <div class="ov-value" :style="{ color: card.color }">
              {{ card.value }}<span class="ov-unit">{{ card.unit }}</span>
            </div>
            <div class="ov-label">{{ card.label }}</div>
            <div class="ov-desc">{{ card.desc }}</div>
          </div>
        </div>
      </div>

      <!-- 行2：双列图表 -->
      <div class="chart-row">
        <!-- 掌握度成长曲线 -->
        <div class="chart-box">
          <div class="chart-head">
            <span class="chart-title">📈 知识掌握度成长曲线</span>
            <span class="chart-badge">最近 {{ stats.mastery_history.length }} 次更新</span>
          </div>
          <div v-if="stats.mastery_history.length > 0" ref="masteryChartRef" class="chart-canvas" />
          <div v-else class="chart-empty">
            <el-icon size="32" color="#cbd5e1"><DataAnalysis /></el-icon>
            <p>暂无历史数据，开始对话后自动更新</p>
          </div>
        </div>

        <!-- 8维雷达图 -->
        <div class="chart-box">
          <div class="chart-head">
            <span class="chart-title">🕸 能力维度雷达图</span>
            <span class="chart-badge">8 维评估</span>
          </div>
          <div ref="radarChartRef" class="chart-canvas" />
        </div>
      </div>

      <!-- 行3：薄弱点 + 诊断得分趋势 -->
      <div class="chart-row">
        <!-- 薄弱知识点 -->
        <div class="chart-box">
          <div class="chart-head">
            <span class="chart-title">⚠️ 薄弱知识点 Top 5</span>
            <span class="chart-badge">待强化</span>
          </div>
          <div v-if="stats.weak_points.length > 0" class="weak-list">
            <div
              v-for="(wp, idx) in stats.weak_points"
              :key="idx"
              class="weak-item"
            >
              <div class="weak-rank" :style="{ background: ['#ef4444','#f97316','#f59e0b','#84cc16','#10b981'][idx] + '22', color: ['#ef4444','#f97316','#f59e0b','#84cc16','#10b981'][idx] }">
                {{ idx + 1 }}
              </div>
              <div class="weak-name">{{ wp }}</div>
              <div class="weak-bar-wrap">
                <div
                  class="weak-bar"
                  :style="{
                    width: (100 - idx * 15) + '%',
                    background: ['#ef4444','#f97316','#f59e0b','#84cc16','#10b981'][idx],
                  }"
                />
              </div>
            </div>
          </div>
          <div v-else class="chart-empty">
            <el-icon size="32" color="#10b981"><CircleCheck /></el-icon>
            <p>暂未识别到薄弱知识点，继续保持！</p>
          </div>
        </div>

        <!-- 近期诊断得分趋势 -->
        <div class="chart-box">
          <div class="chart-head">
            <span class="chart-title">📋 近期诊断得分趋势</span>
            <span class="chart-badge">最近 {{ stats.score_trend.length }} 次</span>
          </div>
          <div v-if="stats.score_trend.length > 0" ref="scoreTrendRef" class="chart-canvas" />
          <div v-else class="chart-empty">
            <el-icon size="32" color="#cbd5e1"><Document /></el-icon>
            <p>暂无诊断记录，前往<router-link to="/diagnosis">诊断面板</router-link>开始</p>
          </div>
        </div>
      </div>

      <!-- 补充信息条 -->
      <div class="info-bar">
        <div class="info-item">
          <span class="info-icon">🎓</span>
          <span class="info-text">总对话会话数：<strong>{{ stats.total_sessions }}</strong></span>
        </div>
        <div class="info-item">
          <span class="info-icon">📚</span>
          <span class="info-text">知识图谱节点：<strong>{{ stats.knowledge_nodes_count }}</strong></span>
        </div>
        <div class="info-item">
          <span class="info-icon">🏆</span>
          <span class="info-text">学习路径完成度：<strong>{{ stats.chapter_progress }}%</strong></span>
        </div>
        <div class="info-item">
          <span class="info-icon">🎯</span>
          <span class="info-text">平均诊断得分：<strong>{{ stats.diagnosis_avg_score }}</strong></span>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.dashboard-view {
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
}

.dash-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
}

.dash-title {
  font-size: 20px;
  font-weight: 800;
  color: #1e293b;
  letter-spacing: -0.5px;
  margin-bottom: 4px;
}

.dash-sub {
  font-size: 13px;
  color: #64748b;
}

.refresh-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: 1.5px solid #e2e8f0;
  border-radius: 10px;
  background: white;
  color: #64748b;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
}

.refresh-btn:hover:not(:disabled) {
  border-color: #6366f1;
  color: #6366f1;
}

.refresh-btn:disabled { opacity: 0.5; cursor: not-allowed; }

@keyframes spin { to { transform: rotate(360deg); } }
.rotating { animation: spin 1s linear infinite; }

/* ── 骨架屏 ── */
.skeleton-wrap {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.skeleton-card {
  height: 100px;
  border-radius: 16px;
  background: linear-gradient(90deg, #f1f5f9 25%, #e2e8f0 50%, #f1f5f9 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

.skeleton-chart {
  grid-column: span 2;
  height: 240px;
  border-radius: 16px;
  background: linear-gradient(90deg, #f1f5f9 25%, #e2e8f0 50%, #f1f5f9 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* ── 概览卡片 ── */
.overview-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
}

.ov-card {
  border-radius: 16px;
  padding: 20px;
  border: 1px solid #e8eef8;
  display: flex;
  align-items: center;
  gap: 14px;
  transition: all 0.22s;
  box-shadow: 0 2px 6px rgba(0,0,0,0.03);
}

.ov-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.08);
}

.ov-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  flex-shrink: 0;
}

.ov-value {
  font-size: 28px;
  font-weight: 800;
  line-height: 1;
  letter-spacing: -1px;
}

.ov-unit {
  font-size: 13px;
  font-weight: 600;
  margin-left: 2px;
}

.ov-label {
  font-size: 12px;
  color: #475569;
  margin-top: 4px;
  font-weight: 600;
}

.ov-desc {
  font-size: 11px;
  color: #94a3b8;
  margin-top: 2px;
}

/* ── 图表区 ── */
.chart-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.chart-box {
  background: white;
  border-radius: 16px;
  border: 1px solid #e8eef8;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

.chart-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}

.chart-title {
  font-size: 14px;
  font-weight: 700;
  color: #1e293b;
}

.chart-badge {
  font-size: 11px;
  color: #6366f1;
  background: #eff0ff;
  padding: 2px 8px;
  border-radius: 20px;
  font-weight: 600;
}

.chart-canvas {
  height: 200px;
}

.chart-empty {
  height: 200px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: #94a3b8;
  font-size: 13px;
}

.chart-empty a {
  color: #6366f1;
  text-decoration: none;
  font-weight: 600;
}

/* ── 薄弱知识点 ── */
.weak-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.weak-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.weak-rank {
  width: 24px;
  height: 24px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  flex-shrink: 0;
}

.weak-name {
  font-size: 13px;
  font-weight: 600;
  color: #334155;
  width: 120px;
  flex-shrink: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.weak-bar-wrap {
  flex: 1;
  height: 8px;
  background: #f1f5f9;
  border-radius: 4px;
  overflow: hidden;
}

.weak-bar {
  height: 100%;
  border-radius: 4px;
  transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

/* ── 信息条 ── */
.info-bar {
  background: white;
  border-radius: 14px;
  border: 1px solid #e8eef8;
  padding: 16px 24px;
  display: flex;
  gap: 32px;
  flex-wrap: wrap;
  box-shadow: 0 2px 6px rgba(0,0,0,0.03);
}

.info-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #64748b;
}

.info-icon { font-size: 16px; }

.info-text strong {
  color: #1e293b;
  font-weight: 700;
}

/* ── 响应式 ── */
@media (max-width: 1024px) {
  .overview-grid { grid-template-columns: repeat(2, 1fr); }
  .chart-row { grid-template-columns: 1fr; }
}

@media (max-width: 640px) {
  .overview-grid { grid-template-columns: 1fr 1fr; }
}
</style>
