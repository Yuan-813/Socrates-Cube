<script setup lang="ts">
import { ref, computed, shallowRef } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { GraphChart } from 'echarts/charts'
import {
  TooltipComponent,
  LegendComponent,
  ToolboxComponent,
} from 'echarts/components'
import VChart from 'vue-echarts'
import { useUserStore } from '@/stores/userStore'

use([CanvasRenderer, GraphChart, TooltipComponent, LegendComponent, ToolboxComponent])

const userStore = useUserStore()

// ─── Types ───────────────────────────────────────────────────────────────────
interface KGNode {
  id: string
  name: string
  category: number
  value: number
  symbolSize: number
}
interface KGEdge {
  source: string
  target: string
  label?: string
}
interface KGGraph {
  query: string
  nodes: KGNode[]
  edges: KGEdge[]
  generatedAt: string
}

// ─── State ───────────────────────────────────────────────────────────────────
const userQuery   = ref('')
const isGenerating = ref(false)
const errorMsg    = ref('')
const history     = ref<KGGraph[]>([])
const activeIdx   = ref<number>(-1)

const QUICK_TOPICS = [
  'TCP协议', 'IP路由', 'DNS解析', 'HTTP/HTTPS',
  'ARP协议', 'VLAN', '防火墙', 'OSPF路由协议',
  'BGP协议', '交换机工作原理',
]

// 节点分类颜色
const CATEGORIES = [
  { name: '协议', color: '#3b82f6' },
  { name: '概念', color: '#8b5cf6' },
  { name: '组件', color: '#10b981' },
  { name: 'RFC标准', color: '#f59e0b' },
  { name: '应用', color: '#ef4444' },
]

// ─── ECharts option ──────────────────────────────────────────────────────────
const graph = computed<KGGraph | null>(() =>
  activeIdx.value >= 0 ? history.value[activeIdx.value] : null
)

const chartOption = computed(() => {
  if (!graph.value) return {}
  const { nodes, edges } = graph.value
  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      formatter: (p: any) => {
        if (p.dataType === 'node') {
          const cat = CATEGORIES[p.data.category] || { name: '其他' }
          return `<b>${p.data.name}</b><br/><span style="color:#888">${cat.name}</span>`
        }
        return `${p.data.source} → ${p.data.target}`
      },
      confine: true,
    },
    legend: {
      data: CATEGORIES.map(c => c.name),
      bottom: 8,
      icon: 'circle',
      itemWidth: 10,
      itemHeight: 10,
      textStyle: { fontSize: 11, color: '#666' },
    },
    series: [
      {
        type: 'graph',
        layout: 'force',
        roam: true,
        draggable: true,
        label: {
          show: true,
          position: 'bottom',
          fontSize: 11,
          color: '#333',
          formatter: (p: any) => p.data.name,
        },
        force: {
          repulsion: 200,
          edgeLength: [60, 120],
          gravity: 0.1,
        },
        categories: CATEGORIES.map(c => ({ name: c.name, itemStyle: { color: c.color } })),
        data: nodes.map(n => ({
          ...n,
          itemStyle: { color: CATEGORIES[n.category]?.color || '#6366f1' },
          label: { show: true },
        })),
        edges: edges.map(e => ({
          source: e.source,
          target: e.target,
          label: { show: !!e.label, formatter: e.label || '' },
          lineStyle: { color: '#cbd5e1', width: 1.5, curveness: 0.1 },
        })),
        emphasis: {
          focus: 'adjacency',
          lineStyle: { width: 3 },
        },
        animationDurationUpdate: 500,
      },
    ],
  }
})

// ─── Chart ref (for export) ──────────────────────────────────────────────────
const chartRef = shallowRef<InstanceType<typeof VChart> | null>(null)

// ─── Generate ────────────────────────────────────────────────────────────────
async function generate(query: string) {
  if (!query.trim() || isGenerating.value) return
  isGenerating.value = true
  errorMsg.value = ''

  const prompt = `你是知识图谱生成专家。请为「${query}」生成一个计算机网络知识图谱。
要求：
- 生成 8-15 个核心知识节点
- 每个节点有：id（英文，如tcp_syn）、name（中文）、category（数字 0-4 对应：0协议 1概念 2组件 3RFC标准 4应用）、value（重要度1-10）
- 生成 10-20 条有意义的关联边，每条含 source、target 和可选 label
- 严格输出 JSON：{"nodes":[...],"edges":[...]}
- 只输出 JSON，不加说明`

  try {
    const r = await fetch('/api/v1/chat/message', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: `kg_${Date.now()}`,
        user_id: userStore.userId,
        message: prompt,
        agent_persona: 'expert',
      }),
    })
    const data = await r.json()
    const raw = data.reply || '{}'

    const match = raw.match(/\{[\s\S]*\}/)
    if (!match) throw new Error('无法解析图谱数据')

    const parsed = JSON.parse(match[0]) as { nodes: KGNode[]; edges: KGEdge[] }

    // 补全 symbolSize
    parsed.nodes = parsed.nodes.map(n => ({
      ...n,
      symbolSize: 20 + (n.value || 5) * 3,
    }))

    const newGraph: KGGraph = {
      query,
      nodes: parsed.nodes,
      edges: parsed.edges,
      generatedAt: new Date().toLocaleString('zh-CN'),
    }
    history.value.unshift(newGraph)
    activeIdx.value = 0
  } catch (e: any) {
    errorMsg.value = e?.message || '生成失败，请重试'
    // Fallback demo graph
    const demo = buildDemoGraph(query)
    history.value.unshift(demo)
    activeIdx.value = 0
  } finally {
    isGenerating.value = false
  }
}

function buildDemoGraph(query: string): KGGraph {
  return {
    query,
    generatedAt: new Date().toLocaleString('zh-CN'),
    nodes: [
      { id: 'root', name: query, category: 0, value: 10, symbolSize: 50 },
      { id: 'c1',   name: '核心概念A', category: 1, value: 7, symbolSize: 38 },
      { id: 'c2',   name: '核心概念B', category: 1, value: 6, symbolSize: 35 },
      { id: 'c3',   name: '相关组件', category: 2, value: 5, symbolSize: 32 },
      { id: 'c4',   name: 'RFC标准', category: 3, value: 6, symbolSize: 35 },
      { id: 'c5',   name: '实际应用', category: 4, value: 5, symbolSize: 30 },
      { id: 'c6',   name: '扩展知识点', category: 1, value: 4, symbolSize: 28 },
    ],
    edges: [
      { source: 'root', target: 'c1', label: '包含' },
      { source: 'root', target: 'c2', label: '包含' },
      { source: 'root', target: 'c4', label: '定义于' },
      { source: 'c1',   target: 'c3', label: '依赖' },
      { source: 'c2',   target: 'c5', label: '应用于' },
      { source: 'c4',   target: 'c1', label: '规定' },
      { source: 'c3',   target: 'c6', label: '关联' },
    ],
  }
}

function selectHistory(idx: number) {
  activeIdx.value = idx
}

// ─── Export ──────────────────────────────────────────────────────────────────
function exportPNG() {
  if (!chartRef.value) return
  const url = (chartRef.value as any).getEchartsInstance().getDataURL({ type: 'png', pixelRatio: 2 })
  const a = document.createElement('a')
  a.href = url
  a.download = `知识图谱_${graph.value?.query || 'export'}.png`
  a.click()
}

function exportJSON() {
  if (!graph.value) return
  const blob = new Blob([JSON.stringify(graph.value, null, 2)], { type: 'application/json' })
  const url  = URL.createObjectURL(blob)
  const a    = document.createElement('a')
  a.href     = url
  a.download = `知识图谱_${graph.value.query}.json`
  a.click()
  URL.revokeObjectURL(url)
}
</script>

<template>
  <div class="kg-page">

    <!-- ── 顶部标题 ──────────────────────────────────────── -->
    <div class="kg-header card">
      <div>
        <h2 class="kg-title">
          <span class="kg-title-gradient">AI 图谱助手</span>
        </h2>
        <p class="kg-subtitle">输入任意网络知识话题，AI 自动提取节点关系，生成交互式知识图谱</p>
      </div>
      <div class="kg-stats" v-if="history.length">
        <span>已生成 <b>{{ history.length }}</b> 张图谱</span>
      </div>
    </div>

    <!-- ── 主体两栏 ──────────────────────────────────────── -->
    <div class="kg-main">

      <!-- 左侧：输入与历史 -->
      <div class="kg-sidebar card">

        <!-- 输入区 -->
        <div class="kg-input-section">
          <label class="kg-input-label">知识话题</label>
          <div class="kg-input-row">
            <input
              v-model="userQuery"
              class="kg-input"
              placeholder="如：TCP协议、IP路由原理..."
              @keyup.enter="generate(userQuery)"
            />
            <button
              class="kg-gen-btn"
              :disabled="!userQuery.trim() || isGenerating"
              @click="generate(userQuery)"
            >
              <svg v-if="isGenerating" class="kg-spin" width="15" height="15" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="2.5" stroke-dasharray="50" stroke-dashoffset="15"/>
              </svg>
              <svg v-else width="15" height="15" viewBox="0 0 24 24" fill="currentColor"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>
              {{ isGenerating ? '生成中…' : '生成图谱' }}
            </button>
          </div>
          <p v-if="errorMsg" class="kg-error">{{ errorMsg }}</p>
        </div>

        <!-- 快捷话题 -->
        <div class="kg-quick">
          <p class="kg-quick-label">快速生成</p>
          <div class="kg-quick-chips">
            <button
              v-for="t in QUICK_TOPICS"
              :key="t"
              class="kg-chip"
              @click="generate(t)"
            >{{ t }}</button>
          </div>
        </div>

        <!-- 历史记录 -->
        <div class="kg-history" v-if="history.length">
          <p class="kg-quick-label">历史图谱</p>
          <div class="kg-hist-list">
            <button
              v-for="(g, idx) in history"
              :key="g.generatedAt"
              class="kg-hist-item"
              :class="{ active: activeIdx === idx }"
              @click="selectHistory(idx)"
            >
              <span class="kg-hist-icon">🗺️</span>
              <div class="kg-hist-info">
                <span class="kg-hist-name">{{ g.query }}</span>
                <span class="kg-hist-meta">{{ g.nodes.length }}节点 · {{ g.generatedAt }}</span>
              </div>
            </button>
          </div>
        </div>

        <!-- 导出 -->
        <div class="kg-export" v-if="graph">
          <p class="kg-quick-label">导出</p>
          <div class="kg-export-btns">
            <button class="kg-export-btn" @click="exportPNG">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="3" width="18" height="18" rx="2"/>
                <circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/>
              </svg>
              导出 PNG
            </button>
            <button class="kg-export-btn" @click="exportJSON">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/>
              </svg>
              导出 JSON
            </button>
          </div>
        </div>

      </div><!-- /kg-sidebar -->

      <!-- 右侧：图谱区 -->
      <div class="kg-canvas card">

        <!-- 空状态 -->
        <div v-if="!graph && !isGenerating" class="kg-empty">
          <div class="kg-empty-icon">🕸️</div>
          <p class="kg-empty-title">从左侧输入话题开始</p>
          <p class="kg-empty-sub">AI 将自动抽取知识点并生成关联图谱</p>
          <div class="kg-empty-demo">
            <p class="kg-quick-label" style="text-align:center;margin-bottom:10px">试试这些话题</p>
            <div class="kg-quick-chips" style="justify-content:center">
              <button v-for="t in QUICK_TOPICS.slice(0,5)" :key="t" class="kg-chip" @click="generate(t)">{{ t }}</button>
            </div>
          </div>
        </div>

        <!-- 生成中 -->
        <div v-else-if="isGenerating" class="kg-empty">
          <div class="kg-gen-anim">
            <svg class="kg-big-spin" width="64" height="64" viewBox="0 0 64 64">
              <circle cx="32" cy="32" r="28" fill="none" stroke="#e0e7ff" stroke-width="4"/>
              <circle cx="32" cy="32" r="28" fill="none" stroke="#6366f1" stroke-width="4"
                stroke-linecap="round" stroke-dasharray="100" stroke-dashoffset="30"/>
            </svg>
          </div>
          <p class="kg-empty-title">AI 正在生成知识图谱…</p>
          <p class="kg-empty-sub">抽取节点、识别关系中，请稍候</p>
        </div>

        <!-- 图谱展示 -->
        <template v-else-if="graph">
          <!-- 图谱标题栏 -->
          <div class="kg-graph-header">
            <div>
              <span class="kg-graph-title">{{ graph.query }}</span>
              <span class="kg-graph-meta">{{ graph.nodes.length }} 个节点 · {{ graph.edges.length }} 条关联</span>
            </div>
            <span class="kg-graph-time">{{ graph.generatedAt }}</span>
          </div>

          <!-- 分类图例 -->
          <div class="kg-legend">
            <span v-for="cat in CATEGORIES" :key="cat.name" class="kg-legend-item">
              <span class="kg-legend-dot" :style="{ background: cat.color }"/>
              {{ cat.name }}
            </span>
          </div>

          <!-- ECharts 图谱 -->
          <div class="kg-chart-wrap">
            <VChart
              ref="chartRef"
              :option="chartOption"
              autoresize
              class="kg-chart"
            />
          </div>

          <!-- 操作提示 -->
          <p class="kg-hint">拖拽节点重排布局 · 滚轮缩放 · 点击节点查看详情</p>
        </template>

      </div><!-- /kg-canvas -->

    </div><!-- /kg-main -->

  </div>
</template>

<style scoped>
.kg-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
  height: 100%;
  min-height: 0;
}

/* ── Header ──────────────────────────────────────────── */
.kg-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
}
.kg-title { font-size: 22px; font-weight: 800; margin: 0 0 4px; }
.kg-title-gradient {
  background: linear-gradient(135deg, #6366f1, #8b5cf6, #3b82f6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.kg-subtitle { font-size: 13px; color: #888; margin: 0; }
.kg-stats { font-size: 13px; color: #6366f1; }

/* ── 主体两栏 ─────────────────────────────────────────── */
.kg-main {
  display: flex;
  gap: 16px;
  flex: 1;
  min-height: 0;
}

/* ── 左侧边栏 ─────────────────────────────────────────── */
.kg-sidebar {
  width: 260px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow-y: auto;
}

.kg-input-section { display: flex; flex-direction: column; gap: 6px; }
.kg-input-label { font-size: 12px; font-weight: 600; color: #555; }
.kg-input-row { display: flex; gap: 6px; }
.kg-input {
  flex: 1;
  border: 1.5px solid #e0e0e0;
  border-radius: 8px;
  padding: 8px 10px;
  font-size: 13px;
  outline: none;
  transition: border-color 0.15s;
  font-family: inherit;
}
.kg-input:focus { border-color: #6366f1; }
.kg-gen-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  white-space: nowrap;
  padding: 8px 14px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 12.5px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.15s;
  flex-shrink: 0;
}
.kg-gen-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.kg-gen-btn:hover:not(:disabled) { opacity: 0.9; }
.kg-spin { animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.kg-error { font-size: 11.5px; color: #ef4444; margin: 0; }

/* 快捷 */
.kg-quick-label {
  font-size: 11.5px;
  font-weight: 700;
  color: #888;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin: 0 0 6px;
}
.kg-quick-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}
.kg-chip {
  padding: 4px 10px;
  background: #f5f5f5;
  border: 1px solid #e8e8e8;
  border-radius: 14px;
  font-size: 11.5px;
  color: #555;
  cursor: pointer;
  transition: all 0.13s;
}
.kg-chip:hover { background: #ede9fe; border-color: #8b5cf6; color: #6d28d9; }

/* 历史 */
.kg-hist-list { display: flex; flex-direction: column; gap: 4px; }
.kg-hist-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 10px;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  background: #fafafa;
  cursor: pointer;
  transition: all 0.13s;
  text-align: left;
  width: 100%;
}
.kg-hist-item:hover { border-color: #c4b5fd; background: #f5f3ff; }
.kg-hist-item.active { border-color: #6366f1; background: #eef2ff; }
.kg-hist-icon { font-size: 16px; flex-shrink: 0; }
.kg-hist-info { flex: 1; min-width: 0; }
.kg-hist-name { display: block; font-size: 12.5px; font-weight: 600; color: #333; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.kg-hist-meta { display: block; font-size: 11px; color: #999; }

/* 导出 */
.kg-export-btns { display: flex; gap: 6px; }
.kg-export-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  padding: 7px 0;
  border: 1.5px solid #e0e0e0;
  border-radius: 8px;
  background: #fafafa;
  font-size: 12px;
  color: #555;
  cursor: pointer;
  transition: all 0.13s;
}
.kg-export-btn:hover { border-color: #6366f1; color: #6366f1; background: #eef2ff; }

/* ── 右侧图谱区 ───────────────────────────────────────── */
.kg-canvas {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 空/加载 状态 */
.kg-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  text-align: center;
  padding: 32px;
}
.kg-empty-icon { font-size: 48px; }
.kg-empty-title { font-size: 16px; font-weight: 700; color: #333; margin: 0; }
.kg-empty-sub   { font-size: 13px; color: #999; margin: 0; }
.kg-empty-demo  { margin-top: 12px; }
.kg-gen-anim    { margin-bottom: 8px; }
.kg-big-spin    { animation: spin 1.2s linear infinite; }

/* 图谱头部 */
.kg-graph-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
  flex-shrink: 0;
}
.kg-graph-title { font-size: 16px; font-weight: 700; color: #1a1a1a; margin-right: 8px; }
.kg-graph-meta  { font-size: 12px; color: #888; }
.kg-graph-time  { font-size: 11px; color: #bbb; white-space: nowrap; flex-shrink: 0; }

/* 图例 */
.kg-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 10px;
  flex-shrink: 0;
}
.kg-legend-item {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 11.5px;
  color: #666;
}
.kg-legend-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

/* 图谱容器 */
.kg-chart-wrap {
  flex: 1;
  min-height: 0;
  border-radius: 10px;
  background: #f9fafc;
  border: 1px solid #f0f0f0;
  overflow: hidden;
}
.kg-chart {
  width: 100%;
  height: 100%;
  min-height: 400px;
}

.kg-hint {
  font-size: 11px;
  color: #bbb;
  text-align: center;
  margin: 8px 0 0;
  flex-shrink: 0;
}
</style>
