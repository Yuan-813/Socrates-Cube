<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { RadarChart, GaugeChart, LineChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, LegendComponent, GridComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import { useUserStore } from '../stores/userStore'
import { PROFILE_DIMENSION_LABELS, PROFILE_DIMENSION_ICONS } from '../types'

use([CanvasRenderer, RadarChart, GaugeChart, LineChart, TitleComponent, TooltipComponent, LegendComponent, GridComponent])

const router = useRouter()
const userStore = useUserStore()

const PROFILE_DIMS = [
  'conceptual_understanding', 'protocol_analysis', 'calculation_ability', 'error_diagnosis',
  'system_design', 'knowledge_connection', 'expression_clarity', 'self_correction',
]
const DIM_COLORS: Record<string, string> = {
  conceptual_understanding: '#6366F1', protocol_analysis: '#10B981', calculation_ability: '#38BDF8',
  error_diagnosis: '#F43F5E', system_design: '#8B5CF6', knowledge_connection: '#0EA5E9',
  expression_clarity: '#EC4899', self_correction: '#F97316',
}
const DIM_COLORS2: Record<string, string> = {
  conceptual_understanding: '#818CF8', protocol_analysis: '#34D399', calculation_ability: '#7DD3FC',
  error_diagnosis: '#FB7185', system_design: '#A78BFA', knowledge_connection: '#38BDF8',
  expression_clarity: '#F9A8D4', self_correction: '#FDBA74',
}
const DIM_SUGGESTIONS: Record<string, string> = {
  conceptual_understanding: '建议加深对基础概念的理解，打好知识基础。完成 TCP 概念梳理练习。预计 20 分钟。',
  protocol_analysis: '多进行协议报文分析练习，提升分析能力。分析真实 HTTP 报文字段。预计 25 分钟。',
  calculation_ability: '如序列号、带宽、RTT 计算等专项训练。刷计算专项题组。预计 15 分钟。',
  error_diagnosis: '提高对协议问题的定位和根因分析能力。完成 TCP 故障排查案例。预计 30 分钟。',
  system_design: '网络架构设计需要综合运用各层协议知识。完成一个小型网络方案设计。预计 40 分钟。',
  knowledge_connection: '利用思维导图梳理协议间的关联关系和依赖。绘制协议栈层次关系图。预计 20 分钟。',
  expression_clarity: '专业术语表达需反复练习，建议口语化表达训练。与 AI 进行 10 分钟对话练习。预计 10 分钟。',
  self_correction: '自我纠错能力通过苏格拉底式问答提升。完成概念挑战练习。预计 15 分钟。',
}

const expandedDim = ref<string | null>(null)
const overallScore = computed(() => Math.round(userStore.radarScores.reduce((a, b) => a + b, 0) / userStore.radarScores.length))
const dimensionDetails = computed(() => PROFILE_DIMS.map((k, i) => ({
  key: k, name: PROFILE_DIMENSION_LABELS[k] ?? k, icon: PROFILE_DIMENSION_ICONS[k] ?? '📌',
  score: userStore.radarScores[i] ?? 50, color: DIM_COLORS[k], color2: DIM_COLORS2[k], index: i,
})))
const weakDims = computed(() => [...dimensionDetails.value].sort((a, b) => a.score - b.score).slice(0, 4))

function getLabel(s: number) {
  if (s >= 80) return '优秀'; if (s >= 60) return '良好'; if (s >= 40) return '一般'; return '薄弱'
}
function getLabelColor(s: number) {
  if (s >= 80) return '#10B981'; if (s >= 60) return '#3B82F6'; if (s >= 40) return '#F59E0B'; return '#F43F5E'
}
function isWeak(s: number) { return s < 40 }

const gaugeOption = computed(() => {
  const s = overallScore.value
  return {
    series: [{
      type: 'gauge', startAngle: 90, endAngle: -270, radius: '84%',
      pointer: { show: false },
      progress: {
        show: true, overlap: false, roundCap: true, clip: false,
        itemStyle: { color: { type: 'linear', x: 0, y: 0, x2: 1, y2: 1, colorStops: [{ offset: 0, color: '#6366F1' }, { offset: 1, color: '#38BDF8' }] } },
        width: 16,
      },
      axisLine: { lineStyle: { width: 16, color: [[1, '#EEF2FF']] } },
      splitLine: { show: false }, axisTick: { show: false }, axisLabel: { show: false },
      title: { offsetCenter: ['0%', '28%'], fontSize: 12, color: '#6366F1', fontWeight: '700' },
      detail: {
        valueAnimation: true, fontSize: 46, fontWeight: 800,
        color: { type: 'linear', x: 0, y: 0, x2: 1, y2: 1, colorStops: [{ offset: 0, color: '#6366F1' }, { offset: 1, color: '#38BDF8' }] },
        formatter: (v: number) => `${v}`, offsetCenter: ['0%', '-8%'],
      },
      data: [{ value: s, name: `综合能力指数 · ${getLabel(s)}` }],
    }],
  }
})

const radarOption = computed(() => ({
  tooltip: { appendToBody: true, trigger: 'item', backgroundColor: 'rgba(255,255,255,0.96)', borderColor: '#C7D2FE', borderWidth: 1, textStyle: { color: '#334155', fontSize: 12 } },
  legend: { data: ['当前能力', '班级平均'], bottom: 2, itemWidth: 12, itemHeight: 8, textStyle: { fontSize: 11, color: '#64748B' } },
  radar: {
    indicator: PROFILE_DIMS.map(k => ({ name: PROFILE_DIMENSION_LABELS[k] ?? k, max: 100, color: DIM_COLORS[k] })),
    radius: '60%', center: ['50%', '50%'], splitNumber: 4,
    axisName: { fontSize: 11, fontWeight: '700' },
    splitArea: { areaStyle: { color: ['rgba(238,242,255,0.9)', 'rgba(224,231,255,0.7)', 'rgba(199,210,254,0.4)', 'rgba(165,180,252,0.15)'] } },
    splitLine: { lineStyle: { color: '#C7D2FE', width: 1 } },
    axisLine: { lineStyle: { color: '#A5B4FC', width: 1 } },
  },
  series: [{
    name: '能力评估', type: 'radar',
    data: [
      { value: userStore.radarScores, name: '当前能力', areaStyle: { color: 'rgba(99,102,241,0.18)' }, lineStyle: { color: '#6366F1', width: 2.5 }, itemStyle: { color: '#6366F1', borderWidth: 2, borderColor: '#fff' }, symbolSize: 5 },
      { value: [78, 82, 75, 80, 72, 78, 85, 80], name: '班级平均', lineStyle: { color: '#10B981', width: 1.5, type: 'dashed' }, itemStyle: { color: '#10B981' }, areaStyle: { color: 'rgba(16,185,129,0.06)' }, symbolSize: 4 },
    ],
  }],
}))

const trendOption = computed(() => {
  const history = userStore.masteryHistory
  if (history.length < 2) return null
  return {
    grid: { top: 12, right: 18, bottom: 24, left: 40 },
    tooltip: { trigger: 'axis', appendToBody: true, backgroundColor: 'rgba(255,255,255,0.96)', borderColor: '#E2E8F0', formatter: (p: any) => `第${p[0].dataIndex + 1}次：<b style="color:#6366F1">${p[0].value}%</b>` },
    xAxis: { type: 'category', data: history.map((_: number, i: number) => `#${i + 1}`), axisLabel: { fontSize: 10, color: '#94A3B8' }, axisLine: { lineStyle: { color: '#E2E8F0' } }, axisTick: { show: false } },
    yAxis: { type: 'value', min: 0, max: 100, interval: 25, axisLabel: { fontSize: 10, color: '#94A3B8', formatter: '{value}%' }, splitLine: { lineStyle: { color: '#F1F5F9' } } },
    series: [{
      type: 'line', data: history, smooth: true, symbol: 'circle', symbolSize: 5,
      lineStyle: { width: 2.5, color: { type: 'linear', x: 0, y: 0, x2: 1, y2: 0, colorStops: [{ offset: 0, color: '#6366F1' }, { offset: 1, color: '#38BDF8' }] } },
      itemStyle: { color: '#6366F1', borderWidth: 2.5, borderColor: '#fff' },
      areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(99,102,241,0.2)' }, { offset: 1, color: 'rgba(99,102,241,0.01)' }] } },
    }],
  }
})

function dimSparkPoints(score: number, idx: number): string {
  const r1 = ((idx * 1337 + score * 7) % 10) / 10
  const r2 = ((idx * 2771 + score * 13) % 10) / 10
  const start = Math.max(score - 22, 0)
  const vals = [start, start + (score - start) * (0.28 + r1 * 0.1), start + (score - start) * 0.52, start + (score - start) * (0.76 + r2 * 0.08), score]
  const min = Math.min(...vals), range = Math.max(...vals) - min || 1
  const w = 64, h = 22
  return vals.map((v, i) => `${((i / 4) * w).toFixed(1)},${(h - 3 - ((v - min) / range) * (h - 7)).toFixed(1)}`).join(' ')
}

function goReinforce(dimKey: string) {
  router.push({ path: '/resources', query: { topic: PROFILE_DIMENSION_LABELS[dimKey] ?? dimKey } })
}
</script>

<template>
  <div class="s1-wrap">

    <!-- AI 状态栏 -->
    <div class="s1-status-bar">
      <div class="s1-status-left">
        <span class="s1-status-pulse" />
        <span class="s1-status-text">AI 分析完成</span>
        <span class="s1-status-divider">·</span>
        <span class="s1-status-detail">最近更新 2 分钟前</span>
        <span class="s1-status-divider">·</span>
        <span class="s1-status-agent">Profiler Agent</span>
      </div>
      <div class="s1-status-right">
        <span class="s1-model-tag">🤖 AI 动态建模中</span>
      </div>
    </div>

    <!-- 顶部：仪表盘 + 雷达图 -->
    <div class="s1-top-row">
      <!-- 综合能力指数 -->
      <div class="s1-gauge-card">
        <div class="s1-card-head">
          <span class="s1-ch-icon">📊</span>
          <span class="s1-ch-title">AI 综合能力指数</span>
        </div>
        <v-chart class="s1-gauge-chart" :option="gaugeOption" autoresize />
        <div class="s1-growth-row">
          <span class="s1-growth-badge">
            <span class="s1-ga">↑</span> 最近提升 {{ Math.max(3, Math.round(overallScore * 0.08)) }}%
          </span>
          <span class="s1-growth-sub">超越 73% 的同学</span>
        </div>
        <div class="s1-gauge-dims">
          <div v-for="dim in dimensionDetails.slice(0, 4)" :key="dim.key" class="s1-gdim">
            <span class="s1-gdim-dot" :style="{ background: dim.color }" />
            <span class="s1-gdim-name">{{ dim.name }}</span>
            <span class="s1-gdim-score" :style="{ color: dim.color }">{{ dim.score }}</span>
          </div>
        </div>
        <div class="s1-gauge-dims" style="margin-top:6px">
          <div v-for="dim in dimensionDetails.slice(4, 8)" :key="dim.key" class="s1-gdim">
            <span class="s1-gdim-dot" :style="{ background: dim.color }" />
            <span class="s1-gdim-name">{{ dim.name }}</span>
            <span class="s1-gdim-score" :style="{ color: dim.color }">{{ dim.score }}</span>
          </div>
        </div>
        <div v-if="trendOption" class="s1-mini-trend">
          <v-chart class="s1-mini-chart" :option="trendOption" autoresize />
        </div>
      </div>

      <!-- 八维雷达图 -->
      <div class="s1-radar-card">
        <div class="s1-card-head">
          <span class="s1-ch-icon">🎯</span>
          <span class="s1-ch-title">八维网络工程能力模型</span>
        </div>
        <v-chart class="s1-radar-chart" :option="radarOption" autoresize />
      </div>
    </div>

    <!-- Alice + AI 建议 -->
    <div class="s1-mid-row">
      <!-- Alice 卡片 -->
      <div class="s1-alice-card">
        <div class="s1-alice-header">
          <div class="s1-alice-avatar">AI</div>
          <div class="s1-alice-meta">
            <span class="s1-alice-name">Alice</span>
            <span class="s1-alice-status">● 在线</span>
          </div>
        </div>
        <p class="s1-alice-msg">
          你好！你的 <strong style="color:#6366F1">{{ weakDims[1]?.name ?? '协议分析' }}</strong>
          能力最近提升明显。下一步建议重点突破
          <strong style="color:#F43F5E">{{ weakDims[0]?.name ?? '计算能力' }}</strong>。
        </p>
        <button class="s1-alice-btn" @click="goReinforce(weakDims[0]?.key)">
          查看成长计划 →
        </button>
        <div class="s1-alice-divider" />
        <div class="s1-alice-stat">
          <div class="s1-alstat-item">
            <span class="s1-alstat-val">{{ userStore.masteryHistory?.length ?? 0 }}</span>
            <span class="s1-alstat-lbl">学习轮次</span>
          </div>
          <div class="s1-alstat-item">
            <span class="s1-alstat-val">{{ weakDims.filter(d => d.score < 40).length }}</span>
            <span class="s1-alstat-lbl">待强化项</span>
          </div>
          <div class="s1-alstat-item">
            <span class="s1-alstat-val">{{ overallScore }}</span>
            <span class="s1-alstat-lbl">综合得分</span>
          </div>
        </div>
      </div>

      <!-- 个性化学习建议 -->
      <div class="s1-suggest-area">
        <div class="s1-sa-head">
          <span class="s1-sa-title">💡 个性化学习建议</span>
          <span class="s1-sa-sub">根据你的薄弱维度，AI 生成专属提升方案</span>
        </div>
        <div class="s1-suggest-grid">
          <div v-for="(dim, i) in weakDims" :key="dim.key" class="s1-sug-card" :style="{ '--sc': dim.color, '--sc2': dim.color2 }">
            <div class="s1-sug-stripe" :style="{ background: `linear-gradient(90deg, ${dim.color}, ${dim.color2})` }" />
            <div class="s1-sug-top">
              <span class="s1-sug-rank" :style="{ background: dim.color + '20', color: dim.color }">{{ ['最弱', '较弱', '偏弱', '待提升'][i] }}</span>
              <span class="s1-sug-icon">{{ dim.icon }}</span>
              <span class="s1-sug-name" :style="{ color: dim.color }">{{ dim.name }}提升</span>
              <span class="s1-sug-badge-weak" v-if="isWeak(dim.score)">⚠️ 弱项</span>
            </div>
            <div class="s1-sug-score-row">
              当前得分
              <strong :style="{ color: dim.color }">{{ dim.score }}/100</strong>
            </div>
            <p class="s1-sug-text">{{ DIM_SUGGESTIONS[dim.key] }}</p>
            <button class="s1-sug-btn" :style="{ background: `linear-gradient(135deg, ${dim.color}, ${dim.color2})` }" @click="goReinforce(dim.key)">
              去强化 →
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 八维能力成长矩阵 -->
    <div class="s1-matrix-section">
      <div class="s1-sec-head">
        <span class="s1-sec-title">⚡ 八维能力详情</span>
        <span class="s1-sec-sub">点击卡片查看评分标准与 AI 建议</span>
      </div>
      <div class="s1-matrix-grid">
        <div
          v-for="dim in dimensionDetails" :key="dim.key"
          class="s1-mat-card"
          :class="{ 'mat-weak': isWeak(dim.score), 'mat-active': expandedDim === dim.key }"
          :style="{ borderTopColor: isWeak(dim.score) ? '#F43F5E' : dim.color }"
          @click="expandedDim = expandedDim === dim.key ? null : dim.key"
        >
          <div class="s1-mc-head">
            <div class="s1-mc-icon" :style="{ background: dim.color + '18' }">{{ dim.icon }}</div>
            <div class="s1-mc-meta">
              <span class="s1-mc-name" :style="{ color: dim.color }">{{ dim.name }}</span>
              <span class="s1-mc-lbl" :style="{ background: getLabelColor(dim.score) + '18', color: getLabelColor(dim.score) }">{{ getLabel(dim.score) }}</span>
            </div>
          </div>
          <div class="s1-mc-score-row">
            <span class="s1-mc-score" :style="{ background: `linear-gradient(135deg,${dim.color},${dim.color2})`, WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text' }">{{ dim.score }}</span>
            <span class="s1-mc-unit">/100</span>
            <span class="s1-mc-delta" :style="{ color: dim.color }">↑+{{ Math.max(2, Math.round(dim.score * 0.11)) }}</span>
          </div>
          <!-- Sparkline -->
          <svg class="s1-spark" viewBox="0 0 64 22">
            <polyline :points="dimSparkPoints(dim.score, dim.index)" fill="none" :stroke="dim.color" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" opacity="0.8" />
          </svg>
          <div class="s1-mc-bar">
            <div class="s1-mc-bar-fill" :style="{ width: dim.score + '%', background: `linear-gradient(90deg,${dim.color},${dim.color2})` }" />
          </div>
          <!-- 展开 -->
          <transition name="s1-expand">
            <div v-if="expandedDim === dim.key" class="s1-mc-expand">
              <p class="s1-mc-ai-hint">AI 建议：{{ DIM_SUGGESTIONS[dim.key] }}</p>
              <button class="s1-mc-reinforce" :style="{ background: `linear-gradient(135deg,${dim.color},${dim.color2})` }" @click.stop="goReinforce(dim.key)">
                📚 生成专属资源
              </button>
            </div>
          </transition>
        </div>
      </div>
    </div>

    <!-- 底部 Banner -->
    <div class="s1-footer-banner">
      <div class="s1-fb-icon-wrap">🎓</div>
      <div class="s1-fb-content">
        <div class="s1-fb-title">能力提升小贴士</div>
        <div class="s1-fb-sub">坚持每日学习，专注薄弱点训练，使用 AI 助教答疑解惑，能力成长看得见！</div>
      </div>
      <button class="s1-fb-btn" @click="router.push('/path')">查看学习路径 →</button>
    </div>

  </div>
</template>

<style scoped>
/* ── 整体 ── */
.s1-wrap {
  display: flex;
  flex-direction: column;
  gap: 16px;
  background: linear-gradient(145deg, #F8F9FF 0%, #EEF0FF 100%);
  border-radius: 16px;
  padding: 16px;
  min-height: 600px;
}

/* ── 状态栏 ── */
.s1-status-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 14px;
  background: rgba(99,102,241,0.07);
  border: 1px solid rgba(99,102,241,0.15);
  border-radius: 10px;
  gap: 10px;
  flex-wrap: wrap;
}
.s1-status-left { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.s1-status-pulse {
  width: 8px; height: 8px; border-radius: 50%; background: #10B981;
  box-shadow: 0 0 0 3px rgba(16,185,129,0.2);
  animation: s1-pulse 2s infinite;
}
@keyframes s1-pulse {
  0%, 100% { box-shadow: 0 0 0 3px rgba(16,185,129,0.2); }
  50% { box-shadow: 0 0 0 6px rgba(16,185,129,0.05); }
}
.s1-status-text { font-size: 13px; font-weight: 700; color: #10B981; }
.s1-status-divider { color: #CBD5E1; font-size: 12px; }
.s1-status-detail { font-size: 12px; color: #64748B; }
.s1-status-agent { font-size: 12px; color: #6366F1; font-weight: 600; }
.s1-model-tag {
  font-size: 11px; color: #6366F1; background: rgba(99,102,241,0.1);
  border: 1px solid rgba(99,102,241,0.2); border-radius: 20px; padding: 3px 10px; font-weight: 600;
}

/* ── 顶部双列 ── */
.s1-top-row {
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: 14px;
  align-items: stretch;
}
.s1-gauge-card, .s1-radar-card {
  background: rgba(255,255,255,0.85);
  backdrop-filter: blur(12px);
  border-radius: 14px;
  border: 1px solid rgba(200,210,255,0.5);
  padding: 16px 18px;
  box-shadow: 0 4px 20px rgba(99,102,241,0.08);
}
.s1-card-head {
  display: flex; align-items: center; gap: 6px;
  font-size: 13px; font-weight: 700; color: #1E293B; margin-bottom: 6px;
}
.s1-ch-icon { font-size: 15px; }
.s1-ch-title { font-weight: 700; color: #1E293B; }
.s1-gauge-chart { width: 100%; height: 190px; }
.s1-growth-row {
  display: flex; align-items: center; gap: 10px;
  margin: 4px 0 8px; padding: 6px 10px;
  background: rgba(16,185,129,0.08); border-radius: 8px; border: 1px solid rgba(16,185,129,0.2);
}
.s1-growth-badge { font-size: 13px; font-weight: 700; color: #10B981; }
.s1-ga { font-size: 15px; }
.s1-growth-sub { font-size: 11px; color: #64748B; }
.s1-gauge-dims {
  display: grid; grid-template-columns: 1fr 1fr; gap: 5px 10px;
}
.s1-gdim { display: flex; align-items: center; gap: 5px; }
.s1-gdim-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
.s1-gdim-name { font-size: 11px; color: #64748B; flex: 1; white-space: nowrap; }
.s1-gdim-score { font-size: 11px; font-weight: 700; }
.s1-mini-trend { margin-top: 8px; padding-top: 8px; border-top: 1px solid #F1F5F9; }
.s1-mini-chart { width: 100%; height: 80px; }
.s1-radar-chart { width: 100%; height: 320px; }

/* ── Alice + Suggestions ── */
.s1-mid-row {
  display: grid;
  grid-template-columns: 220px 1fr;
  gap: 14px;
  align-items: stretch;
}
.s1-alice-card {
  background: linear-gradient(145deg, rgba(255,255,255,0.9), rgba(238,242,255,0.9));
  backdrop-filter: blur(12px);
  border-radius: 14px;
  border: 1px solid rgba(99,102,241,0.2);
  padding: 16px;
  box-shadow: 0 4px 16px rgba(99,102,241,0.1);
  display: flex; flex-direction: column; gap: 10px;
}
.s1-alice-header { display: flex; align-items: center; gap: 10px; }
.s1-alice-avatar {
  width: 44px; height: 44px; border-radius: 50%; flex-shrink: 0;
  background: linear-gradient(135deg, #6366F1, #EC4899);
  display: flex; align-items: center; justify-content: center;
  font-size: 13px; font-weight: 800; color: white;
  box-shadow: 0 4px 12px rgba(99,102,241,0.4);
}
.s1-alice-name { font-size: 15px; font-weight: 800; color: #1E293B; display: block; }
.s1-alice-status { font-size: 11px; color: #10B981; font-weight: 600; }
.s1-alice-msg { font-size: 12.5px; color: #475569; line-height: 1.6; margin: 0; }
.s1-alice-btn {
  padding: 8px 14px; border: none; border-radius: 10px;
  background: linear-gradient(135deg, #6366F1, #8B5CF6);
  color: white; font-size: 12px; font-weight: 700;
  cursor: pointer; transition: all 0.2s; width: 100%;
  box-shadow: 0 4px 12px rgba(99,102,241,0.3);
}
.s1-alice-btn:hover { transform: translateY(-1px); box-shadow: 0 6px 16px rgba(99,102,241,0.4); }
.s1-alice-divider { height: 1px; background: rgba(99,102,241,0.1); }
.s1-alice-stat { display: flex; gap: 4px; }
.s1-alstat-item { flex: 1; text-align: center; padding: 6px 4px; background: rgba(99,102,241,0.06); border-radius: 8px; }
.s1-alstat-val { font-size: 16px; font-weight: 800; color: #6366F1; display: block; }
.s1-alstat-lbl { font-size: 10px; color: #94A3B8; }

.s1-suggest-area {
  background: rgba(255,255,255,0.85);
  backdrop-filter: blur(12px);
  border-radius: 14px;
  border: 1px solid rgba(200,210,255,0.4);
  padding: 16px 18px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.04);
}
.s1-sa-head { margin-bottom: 12px; }
.s1-sa-title { font-size: 13px; font-weight: 700; color: #1E293B; }
.s1-sa-sub { font-size: 11px; color: #94A3B8; margin-left: 8px; }
.s1-suggest-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}
.s1-sug-card {
  background: #FAFBFF;
  border: 1px solid #E8EEF8;
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.2s;
  position: relative;
}
.s1-sug-card:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(0,0,0,0.08); }
.s1-sug-stripe { height: 3px; width: 100%; }
.s1-sug-top {
  display: flex; align-items: center; gap: 6px;
  padding: 10px 12px 6px; flex-wrap: nowrap;
}
.s1-sug-rank {
  font-size: 10px; font-weight: 700; padding: 2px 7px; border-radius: 5px;
  white-space: nowrap; flex-shrink: 0;
}
.s1-sug-icon { font-size: 14px; flex-shrink: 0; }
.s1-sug-name { font-size: 12px; font-weight: 700; flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.s1-sug-badge-weak {
  font-size: 10px; color: #F43F5E; background: #FFF1F2;
  border: 1px solid #FECDD3; border-radius: 4px; padding: 1px 5px;
  white-space: nowrap; flex-shrink: 0;
}
.s1-sug-score-row { font-size: 11px; color: #64748B; padding: 0 12px 4px; }
.s1-sug-score-row strong { font-weight: 700; }
.s1-sug-text {
  font-size: 11px; color: #64748B; padding: 0 12px; line-height: 1.5; margin: 0 0 8px;
  display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden;
}
.s1-sug-btn {
  margin: 0 12px 12px; width: calc(100% - 24px); display: block;
  padding: 6px; border: none; border-radius: 8px; color: white;
  font-size: 11px; font-weight: 700; cursor: pointer; transition: all 0.2s;
}
.s1-sug-btn:hover { opacity: 0.9; transform: translateY(-1px); }

/* ── 能力成长矩阵 ── */
.s1-matrix-section {
  background: rgba(255,255,255,0.85);
  backdrop-filter: blur(12px);
  border-radius: 14px;
  border: 1px solid rgba(200,210,255,0.4);
  padding: 16px 18px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.04);
}
.s1-sec-head { display: flex; align-items: center; gap: 8px; margin-bottom: 14px; }
.s1-sec-title { font-size: 14px; font-weight: 700; color: #1E293B; }
.s1-sec-sub { margin-left: auto; font-size: 11px; color: #94A3B8; }
.s1-matrix-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
}
.s1-mat-card {
  background: #FAFBFF;
  border: 1px solid #E8EEF8;
  border-top: 3px solid;
  border-radius: 12px;
  padding: 12px;
  cursor: pointer;
  transition: all 0.22s;
}
.s1-mat-card:hover { transform: translateY(-3px); box-shadow: 0 8px 24px rgba(0,0,0,0.08); }
.s1-mat-card.mat-weak {
  border-top-color: #F43F5E !important;
  background: linear-gradient(145deg, #FFF7F7, #FAFBFF);
}
.s1-mat-card.mat-active { box-shadow: 0 6px 20px rgba(0,0,0,0.1); }
.s1-mc-head { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.s1-mc-icon {
  width: 32px; height: 32px; border-radius: 8px;
  display: flex; align-items: center; justify-content: center; font-size: 15px; flex-shrink: 0;
}
.s1-mc-meta { display: flex; flex-direction: column; gap: 3px; }
.s1-mc-name { font-size: 12px; font-weight: 700; }
.s1-mc-lbl { font-size: 10px; font-weight: 700; padding: 1px 6px; border-radius: 4px; width: fit-content; }
.s1-mc-score-row { display: flex; align-items: baseline; gap: 3px; margin-bottom: 6px; }
.s1-mc-score { font-size: 26px; font-weight: 800; letter-spacing: -1px; }
.s1-mc-unit { font-size: 11px; color: #94A3B8; }
.s1-mc-delta { font-size: 11px; font-weight: 700; margin-left: auto; }
.s1-spark { width: 64px; height: 22px; display: block; margin-bottom: 8px; }
.s1-mc-bar { height: 5px; background: #F1F5F9; border-radius: 3px; overflow: hidden; }
.s1-mc-bar-fill { height: 100%; border-radius: 3px; transition: width 0.7s ease; }
.s1-mc-expand { margin-top: 10px; padding-top: 10px; border-top: 1px dashed #E2E8F0; }
.s1-mc-ai-hint { font-size: 11px; color: #64748B; line-height: 1.5; margin: 0 0 8px; }
.s1-mc-reinforce {
  width: 100%; padding: 6px; border: none; border-radius: 7px;
  color: white; font-size: 11px; font-weight: 600; cursor: pointer; transition: 0.2s;
}
.s1-mc-reinforce:hover { opacity: 0.88; }
.s1-expand-enter-active, .s1-expand-leave-active { transition: opacity 0.2s, max-height 0.25s ease; overflow: hidden; max-height: 200px; }
.s1-expand-enter-from, .s1-expand-leave-to { opacity: 0; max-height: 0; }

/* ── 底部 Banner ── */
.s1-footer-banner {
  display: flex; align-items: center; gap: 16px;
  background: linear-gradient(135deg, #6366F1 0%, #38BDF8 100%);
  border-radius: 14px; padding: 16px 22px;
  box-shadow: 0 8px 24px rgba(99,102,241,0.3);
}
.s1-fb-icon-wrap { font-size: 28px; flex-shrink: 0; }
.s1-fb-content { flex: 1; }
.s1-fb-title { font-size: 14px; font-weight: 800; color: white; margin-bottom: 3px; }
.s1-fb-sub { font-size: 12px; color: rgba(255,255,255,0.8); }
.s1-fb-btn {
  flex-shrink: 0; padding: 10px 20px; border: 2px solid rgba(255,255,255,0.7);
  background: rgba(255,255,255,0.15); backdrop-filter: blur(8px);
  color: white; font-size: 13px; font-weight: 700; border-radius: 10px;
  cursor: pointer; transition: all 0.2s; white-space: nowrap;
}
.s1-fb-btn:hover { background: rgba(255,255,255,0.25); border-color: white; }

/* ── 响应式 ── */
@media (max-width: 1200px) {
  .s1-top-row { grid-template-columns: 260px 1fr; }
  .s1-matrix-grid { grid-template-columns: repeat(3, 1fr); }
}
@media (max-width: 1024px) {
  .s1-top-row, .s1-mid-row { grid-template-columns: 1fr; }
  .s1-matrix-grid { grid-template-columns: repeat(2, 1fr); }
  .s1-suggest-grid { grid-template-columns: 1fr 1fr; }
}
@media (max-width: 640px) {
  .s1-matrix-grid, .s1-suggest-grid { grid-template-columns: 1fr 1fr; }
}
</style>
