<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, LineChart } from 'echarts/charts'
import {
  TitleComponent, TooltipComponent, GridComponent, LegendComponent,
} from 'echarts/components'
import VChart from 'vue-echarts'
import apiClient from '@/api/client'

use([CanvasRenderer, BarChart, LineChart, TitleComponent, TooltipComponent, GridComponent, LegendComponent])

/* ── 状态 ── */
const loading = ref(false)
const error = ref<string | null>(null)
const stats = ref<any>(null)
let pollTimer: ReturnType<typeof setInterval> | null = null

/* ── 工具常量（展示用）── */
const moduleNames: Record<string, string> = {
  direction_1_linucb: 'LinUCB 上下文赌博机',
  direction_2_hmarl:  'HMARL 分层多Agent',
  direction_3_dqn:    'DQN 路径选择器',
}
const rankColors: string[] = ['#f59e0b', '#64748b', '#ef4444', '#8b5cf6', '#10b981']

/* ── 加载数据 ── */
async function loadStats() {
  try {
    const resp = await apiClient.get('/api/v1/rl/stats')
    stats.value = resp.data
  } catch (e) {
    error.value = '获取 RL 统计失败，后端模块可能未加载'
  }
}

async function loadBanditStats() {
  try {
    const resp = await apiClient.get('/api/v1/rl/stats/bandit/student-001')
    return resp.data
  } catch { return null }
}

async function loadHmarlStats() {
  try {
    const resp = await apiClient.get('/api/v1/rl/stats/hmarl')
    return resp.data
  } catch { return null }
}

const banditData = ref<any>(null)
const hmarlData = ref<any>(null)

async function refresh() {
  loading.value = true
  error.value = null
  await loadStats()
  const [bd, hd] = await Promise.all([loadBanditStats(), loadHmarlStats()])
  banditData.value = bd
  hmarlData.value = hd
  loading.value = false
}

onMounted(async () => {
  await refresh()
  // 每 10s 自动刷新
  pollTimer = setInterval(refresh, 10000)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})

/* ── LinUCB 柱状图 ── */
const ARM_LABELS: Record<string, string> = {
  doc: '知识文档', exercise: '练习题', code: '代码示例',
  mindmap: '思维导图', script: '视频脚本', infographic: '信息图',
}

function banditBarOption() {
  if (!banditData.value?.arm_stats) return null
  const arms = Object.entries(banditData.value.arm_stats) as [string, any][]
  return {
    grid: { top: 16, right: 16, bottom: 36, left: 60 },
    tooltip: {
      trigger: 'axis',
      appendToBody: true,
      formatter: (params: any) =>
        `<b>${params[0].name}</b><br/>` +
        params.map((p: any) => `${p.marker}${p.seriesName}: ${typeof p.value === 'number' ? p.value.toFixed(2) : p.value}`).join('<br/>'),
    },
    legend: { data: ['推荐次数', '平均奖励'], bottom: 0, textStyle: { fontSize: 11 } },
    xAxis: {
      type: 'category',
      data: arms.map(([k]) => ARM_LABELS[k] || k),
      axisLabel: { fontSize: 10, interval: 0 },
    },
    yAxis: [
      { type: 'value', name: '次数', nameTextStyle: { fontSize: 10 }, axisLabel: { fontSize: 10 } },
      { type: 'value', name: '奖励', nameTextStyle: { fontSize: 10 }, axisLabel: { fontSize: 10 }, min: -1, max: 1 },
    ],
    series: [
      {
        name: '推荐次数',
        type: 'bar',
        data: arms.map(([, v]) => v.pulls || 0),
        itemStyle: { color: '#6366f1', borderRadius: [4, 4, 0, 0] },
        barMaxWidth: 32,
      },
      {
        name: '平均奖励',
        type: 'bar',
        yAxisIndex: 1,
        data: arms.map(([, v]) => v.mean_reward ? Number(v.mean_reward.toFixed(3)) : 0),
        itemStyle: { color: '#10b981', borderRadius: [4, 4, 0, 0] },
        barMaxWidth: 32,
      },
    ],
  }
}

/* ── HMARL Q 值图 ── */
function hmarlQOption() {
  if (!hmarlData.value?.top5_actions) return null
  const top5 = hmarlData.value.top5_actions
  return {
    grid: { top: 14, right: 16, bottom: 50, left: 14 },
    tooltip: {
      trigger: 'axis',
      appendToBody: true,
      formatter: (params: any) => `${params[0].name}<br/>Q均值: ${params[0].value}`,
    },
    xAxis: {
      type: 'category',
      data: top5.map((a: any) => `A${a.action_id}`),
      axisLabel: { fontSize: 10 },
    },
    yAxis: {
      type: 'value',
      axisLabel: { fontSize: 10, formatter: (v: number) => v.toFixed(3) },
    },
    series: [{
      type: 'bar',
      data: top5.map((a: any) => ({ value: a.q_mean, name: a.desc })),
      itemStyle: {
        color: (params: any) => {
          const colors = ['#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#10b981']
          return colors[params.dataIndex % 5]
        },
        borderRadius: [4, 4, 0, 0],
      },
      barMaxWidth: 36,
      label: {
        show: true,
        position: 'top',
        fontSize: 10,
        formatter: (params: any) => params.value.toFixed(4),
      },
    }],
  }
}
</script>

<template>
  <div class="rl-dash">
    <!-- 头部 -->
    <div class="rl-header">
      <div class="rl-header-left">
        <span class="rl-icon">🤖</span>
        <div>
          <div class="rl-title">强化学习实时监控</div>
          <div class="rl-sub">系统正在通过三方向 RL 持续优化教学策略</div>
        </div>
      </div>
      <button class="rl-refresh-btn" :disabled="loading" @click="refresh">
        <span v-if="loading">⟳ 刷新中...</span>
        <span v-else>⟳ 刷新</span>
      </button>
    </div>

    <!-- 加载 / 错误 -->
    <div v-if="loading && !stats" class="rl-loading">
      <div class="rl-spinner" />
      <span>正在加载 RL 统计数据...</span>
    </div>

    <div v-else-if="error" class="rl-error">
      ⚠️ {{ error }}
    </div>

    <template v-else-if="stats">
      <!-- RL 模块状态卡片 -->
      <div class="rl-modules">
        <div
          v-for="(mod, key) in stats.rl_modules"
          :key="key"
          class="rl-module-card"
          :class="{ available: mod.available }"
        >
          <div class="rmc-top">
            <div class="rmc-status-dot" :class="{ on: mod.available }" />
            <div class="rmc-name">{{ moduleNames[key] || key }}</div>
          </div>
          <div class="rmc-desc">{{ mod.description }}</div>
          <div class="rmc-avail" :class="mod.available ? 'on' : 'off'">
            {{ mod.available ? '运行中' : '未加载' }}
          </div>
        </div>
      </div>

      <!-- LinUCB 统计 -->
      <div class="rl-section" v-if="banditData">
        <div class="rl-section-header">
          <span class="rl-section-icon">🎰</span>
          <div class="rl-section-title">LinUCB 上下文赌博机 — 资源类型推荐优化</div>
          <div class="rl-section-meta">
            总决策 {{ banditData.total_pulls || 0 }} 次
          </div>
        </div>
        <div class="rl-chart-wrap" v-if="banditBarOption()">
          <v-chart :option="banditBarOption()!" autoresize style="width:100%;height:180px" />
        </div>
        <div class="rl-bandit-info" v-if="banditData.epsilon !== undefined">
          <span class="rl-tag">ε = {{ (banditData.epsilon ?? 0.1).toFixed(3) }}</span>
          <span class="rl-tag">策略：ε-贪婪 + UCB 探索</span>
          <span class="rl-tag rl-tag-green">自动优化推荐偏好</span>
        </div>
      </div>

      <!-- HMARL 统计 -->
      <div class="rl-section" v-if="hmarlData">
        <div class="rl-section-header">
          <span class="rl-section-icon">🏗️</span>
          <div class="rl-section-title">HMARL 元控制器 — Top-5 动作 Q 值</div>
          <div class="rl-section-meta">
            总步数 {{ hmarlData.total_steps || 0 }}
          </div>
        </div>
        <div class="rl-chart-wrap" v-if="hmarlQOption()">
          <v-chart :option="hmarlQOption()!" autoresize style="width:100%;height:160px" />
        </div>
        <div class="rl-hmarl-top5" v-if="hmarlData.top5_actions">
          <div v-for="(a, i) in hmarlData.top5_actions" :key="a.action_id" class="hmarl-action">
            <span class="ha-rank" :style="{ background: rankColors[i] }">{{ i + 1 }}</span>
            <span class="ha-desc">{{ a.desc }}</span>
            <span class="ha-q">Q={{ a.q_mean.toFixed(4) }}</span>
          </div>
        </div>
      </div>

      <!-- DQN 简要状态 -->
      <div class="rl-section">
        <div class="rl-section-header">
          <span class="rl-section-icon">🧠</span>
          <div class="rl-section-title">DQN 路径选择器 — 学习路径节点智能决策</div>
          <div class="rl-section-meta">{{ stats.rl_modules.direction_3_dqn?.available ? '运行中' : '未加载' }}</div>
        </div>
        <div class="rl-dqn-info">
          <div class="dqn-item">
            <span class="dqn-label">算法</span>
            <span class="dqn-val">Deep Q-Network (DQN)</span>
          </div>
          <div class="dqn-item">
            <span class="dqn-label">状态空间</span>
            <span class="dqn-val">8维画像 × 知识节点掌握度</span>
          </div>
          <div class="dqn-item">
            <span class="dqn-label">动作空间</span>
            <span class="dqn-val">选择下一个最优学习节点</span>
          </div>
          <div class="dqn-item">
            <span class="dqn-label">奖励信号</span>
            <span class="dqn-val">节点完成后掌握度提升量</span>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.rl-dash {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 头部 */
.rl-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.rl-header-left {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.rl-icon { font-size: 20px; flex-shrink: 0; margin-top: 2px; }

.rl-title {
  font-size: 15px;
  font-weight: 700;
  color: #1e293b;
}

.rl-sub { font-size: 12px; color: #64748b; margin-top: 2px; }

.rl-refresh-btn {
  padding: 6px 14px;
  border-radius: 8px;
  border: 1.5px solid #e2e8f0;
  background: #fafbff;
  color: #6366f1;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.18s;
  flex-shrink: 0;
}

.rl-refresh-btn:hover:not(:disabled) { background: #eff2ff; border-color: #a5b4fc; }
.rl-refresh-btn:disabled { opacity: 0.5; cursor: not-allowed; }

/* 加载/错误 */
.rl-loading {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 20px;
  justify-content: center;
  color: #6366f1;
  font-size: 13px;
}

.rl-spinner {
  width: 18px; height: 18px;
  border: 2px solid #c7d2fe;
  border-top-color: #6366f1;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  flex-shrink: 0;
}

@keyframes spin { to { transform: rotate(360deg); } }

.rl-error {
  font-size: 12px;
  color: #ef4444;
  background: #fef2f2;
  border-radius: 8px;
  padding: 10px 14px;
}

/* 模块状态卡片 */
.rl-modules {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}

.rl-module-card {
  padding: 12px 14px;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  background: #fafbff;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.rl-module-card.available { border-color: #a7f3d0; background: #f0fdf4; }

.rmc-top {
  display: flex;
  align-items: center;
  gap: 7px;
}

.rmc-status-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  background: #e2e8f0;
  flex-shrink: 0;
}

.rmc-status-dot.on {
  background: #22c55e;
  box-shadow: 0 0 0 3px rgba(34,197,94,0.2);
}

.rmc-name { font-size: 12px; font-weight: 700; color: #1e293b; }
.rmc-desc { font-size: 11px; color: #64748b; line-height: 1.4; }

.rmc-avail {
  font-size: 11px;
  font-weight: 600;
  border-radius: 4px;
  padding: 2px 7px;
  align-self: flex-start;
}

.rmc-avail.on  { color: #16a34a; background: #dcfce7; }
.rmc-avail.off { color: #94a3b8; background: #f1f5f9; }

/* RL 区块 */
.rl-section {
  background: white;
  border-radius: 12px;
  border: 1px solid #e8eef8;
  overflow: hidden;
}

.rl-section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background: #f8faff;
  border-bottom: 1px solid #e8eef8;
}

.rl-section-icon { font-size: 15px; flex-shrink: 0; }
.rl-section-title { font-size: 13px; font-weight: 700; color: #1e293b; flex: 1; }
.rl-section-meta  { font-size: 11px; color: #94a3b8; flex-shrink: 0; }

.rl-chart-wrap { padding: 12px 14px 4px; }

/* bandit info */
.rl-bandit-info {
  display: flex;
  gap: 8px;
  padding: 8px 14px 12px;
  flex-wrap: wrap;
}

.rl-tag {
  font-size: 11px;
  color: #6366f1;
  background: #eff2ff;
  border-radius: 4px;
  padding: 2px 7px;
}

.rl-tag-green { color: #16a34a; background: #dcfce7; }

/* HMARL top5 */
.rl-hmarl-top5 {
  display: flex;
  flex-direction: column;
  gap: 5px;
  padding: 8px 14px 12px;
}

.hmarl-action {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}

.ha-rank {
  width: 20px; height: 20px;
  border-radius: 50%;
  color: white;
  font-size: 11px;
  font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}

.ha-desc { flex: 1; color: #475569; }
.ha-q    { font-family: monospace; font-size: 11px; color: #64748b; flex-shrink: 0; }

/* DQN info */
.rl-dqn-info {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
  padding: 12px 14px;
}

.dqn-item {
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding: 8px 10px;
  background: #f8faff;
  border-radius: 8px;
}

.dqn-label { font-size: 11px; color: #94a3b8; }
.dqn-val   { font-size: 12px; font-weight: 600; color: #1e293b; }

@media (max-width: 640px) {
  .rl-modules { grid-template-columns: 1fr; }
  .rl-dqn-info { grid-template-columns: 1fr; }
}
</style>
