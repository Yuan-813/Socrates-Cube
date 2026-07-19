<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useChatStore } from '@/stores/chatStore'
import { useUserStore } from '@/stores/userStore'

interface KGNode {
  id: string
  name: string
  chapter?: string
  type?: string
  difficulty?: number
  highlighted?: boolean
  x?: number
  y?: number
}
interface KGEdge {
  from: string
  to: string
}

const knowledgeGraph = ref<{ nodes: KGNode[]; edges: KGEdge[] }>({ nodes: [], edges: [] })
const highlightedNodeIds = ref<Set<string>>(new Set())
// 薄弱点（红色）和已掌握（绿色）分别追踪
const weakNodeIds = ref<Set<string>>(new Set())
const strongNodeIds = ref<Set<string>>(new Set())
const selectedNode = ref<KGNode | null>(null)

const chatStore = useChatStore()
const userStore = useUserStore()

// 将知识点名称映射到节点 ID
function resolveNodeIds(names: string[]): string[] {
  const all = knowledgeGraph.value.nodes
  return names.flatMap(name => {
    const lower = name.toLowerCase()
    const matched = all.filter(n => n.name.toLowerCase().includes(lower) || n.id === name)
    return matched.map(n => n.id)
  })
}

// 监听诊断结果，提取知识点 ID 进行高亮
watch(
  () => chatStore.lastDiagnosis,
  (diag) => {
    if (!diag) return
    const d = diag as unknown as {
      knowledge_node_ids?: string[]
      weak_node_ids?: string[]
      strong_node_ids?: string[]
      related_node_ids?: string[]
    }
    if (d.knowledge_node_ids?.length) {
      highlightedNodeIds.value = new Set(d.knowledge_node_ids)
    }
    if (d.weak_node_ids?.length) weakNodeIds.value = new Set(d.weak_node_ids)
    if (d.strong_node_ids?.length) strongNodeIds.value = new Set(d.strong_node_ids)
    if (d.related_node_ids?.length) {
      highlightedNodeIds.value = new Set([...highlightedNodeIds.value, ...d.related_node_ids])
    }
  },
  { deep: true },
)

// 监听 AI 回答后实时推送的 KG 节点
watch(
  () => chatStore.kgHighlightedNodes,
  (nodeIds) => {
    if (nodeIds && nodeIds.length) {
      highlightedNodeIds.value = new Set(nodeIds)
    }
  },
)

// 监听用户 profile 中的薄弱/已掌握知识点（名称 → 节点ID）
watch(
  () => userStore.profile,
  (profile) => {
    if (!profile) return
    if (profile.weak_points?.length) {
      weakNodeIds.value = new Set(resolveNodeIds(profile.weak_points))
    }
    if (profile.strong_points?.length) {
      strongNodeIds.value = new Set(resolveNodeIds(profile.strong_points))
    }
  },
  { deep: true, immediate: true },
)

// 章节颜色映射（保留兼容）
const chapterColors: Record<string, string> = {
  '第1章': '#4f46e5',
  '第2章': '#0891b2',
  '第3章': '#059669',
  '第4章': '#d97706',
  '第5章': '#dc2626',
  '第6章': '#7c3aed',
  '第7章': '#0f766e',
}

function getNodeColor(node: KGNode): string {
  // 薄弱点：红色优先
  if (weakNodeIds.value.has(node.id)) return '#ef4444'
  // 已掌握：绿色
  if (strongNodeIds.value.has(node.id)) return '#22c55e'
  // 当前诊断高亮：琥珀色
  if (highlightedNodeIds.value.has(node.id)) return '#f59e0b'
  // 协议栈层次颜色
  return LAYER_MAP[node.id]?.color || chapterColors[node.chapter || ''] || '#6366f1'
}

// 节点状态标签（模板直接使用 weakNodeIds/strongNodeIds）

// 协议栈分层布局：按 TCP/IP 五层纵向排布，体现层次依赖关系
const LAYER_MAP: Record<string, { layer: number; label: string; color: string }> = {
  // 第1层 概念基础
  kp_001: { layer: 0, label: '概念', color: '#4f46e5' },
  kp_002: { layer: 0, label: '概念', color: '#4f46e5' },
  kp_003: { layer: 0, label: '概念', color: '#4f46e5' },
  // 第2层 物理层
  kp_004: { layer: 1, label: '物理层', color: '#64748b' },
  // 第3层 数据链路层
  kp_005: { layer: 2, label: '链路层', color: '#059669' },
  kp_006: { layer: 2, label: '链路层', color: '#059669' },
  // 第4层 网络层
  kp_007: { layer: 3, label: '网络层', color: '#d97706' },
  kp_008: { layer: 3, label: '网络层', color: '#d97706' },
  kp_009: { layer: 3, label: '网络层', color: '#d97706' },
  kp_010: { layer: 3, label: '网络层', color: '#d97706' },
  // 第5层 传输层
  kp_011: { layer: 4, label: '传输层', color: '#dc2626' },
  kp_012: { layer: 4, label: '传输层', color: '#dc2626' },
  kp_013: { layer: 4, label: '传输层', color: '#dc2626' },
  kp_014: { layer: 4, label: '传输层', color: '#dc2626' },
  kp_015: { layer: 4, label: '传输层', color: '#dc2626' },
  // 第6层 应用层
  kp_016: { layer: 5, label: '应用层', color: '#7c3aed' },
  kp_017: { layer: 5, label: '应用层', color: '#7c3aed' },
  kp_018: { layer: 5, label: '应用层', color: '#7c3aed' },
  kp_019: { layer: 5, label: '应用层', color: '#7c3aed' },
  kp_020: { layer: 5, label: '应用层', color: '#7c3aed' },
}

const LAYER_LABELS = [
  { layer: 0, label: '概念基础', color: '#4f46e5' },
  { layer: 1, label: '物理层', color: '#64748b' },
  { layer: 2, label: '数据链路层', color: '#059669' },
  { layer: 3, label: '网络层', color: '#d97706' },
  { layer: 4, label: '传输层', color: '#dc2626' },
  { layer: 5, label: '应用层', color: '#7c3aed' },
]

const SVG_W = 320
const SVG_H = 380
const LAYER_H = SVG_H / 6

// 协议栈分层布局
const layoutNodes = computed<KGNode[]>(() => {
  const nodes = knowledgeGraph.value.nodes.slice(0, 30)
  // 按层分组
  const layerGroups: Record<number, KGNode[]> = {}
  for (const node of nodes) {
    const layerInfo = LAYER_MAP[node.id]
    const layer = layerInfo?.layer ?? 5 // 未知节点默认应用层
    if (!layerGroups[layer]) layerGroups[layer] = []
    layerGroups[layer].push(node)
  }
  const result: KGNode[] = []
  for (const [layerStr, layerNodes] of Object.entries(layerGroups)) {
    const layer = parseInt(layerStr)
    const count = layerNodes.length
    layerNodes.forEach((node, i) => {
      const xStep = SVG_W / (count + 1)
      result.push({
        ...node,
        x: xStep * (i + 1),
        // 从下往上：layer 0 在底部，layer 5 在顶部
        y: SVG_H - (layer + 0.5) * LAYER_H,
      })
    })
  }
  return result
})

// 构建节点 ID → 布局位置映射
const nodePositions = computed(() => {
  const map: Record<string, { x: number; y: number }> = {}
  layoutNodes.value.forEach(n => {
    if (n.x !== undefined && n.y !== undefined) {
      map[n.id] = { x: n.x, y: n.y }
    }
  })
  return map
})

// 过滤有效的边（两端节点都在展示范围内）
const visibleEdges = computed(() =>
  knowledgeGraph.value.edges.filter(
    e => nodePositions.value[e.from] && nodePositions.value[e.to],
  ),
)

async function loadKnowledgeGraph() {
  try {
    await fetch('/api/v1/resources/')  // warm up
    // 尝试从静态数据文件加载
    const r2 = await fetch('/data/knowledge_graph.json')
    if (r2.ok) {
      const data = await r2.json()
      knowledgeGraph.value = data
    }
  } catch {
    // 使用内嵌的最小知识图谱
    knowledgeGraph.value = {
      nodes: [
        { id: 'kp_001', name: '网络概述', chapter: '第1章', type: 'concept' },
        { id: 'kp_003', name: 'TCP/IP体系', chapter: '第1章', type: 'concept' },
        { id: 'kp_013', name: 'TCP协议基础', chapter: '第5章', type: 'protocol' },
        { id: 'kp_014', name: '三次握手', chapter: '第5章', type: 'protocol' },
        { id: 'kp_015', name: '流量控制', chapter: '第5章', type: 'protocol' },
        { id: 'kp_017', name: 'DNS协议', chapter: '第6章', type: 'protocol' },
        { id: 'kp_018', name: 'HTTP/HTTPS', chapter: '第6章', type: 'protocol' },
        { id: 'kp_007', name: '网络层基础', chapter: '第4章', type: 'concept' },
        { id: 'kp_008', name: 'IP地址', chapter: '第4章', type: 'skill' },
      ],
      edges: [
        { from: 'kp_001', to: 'kp_003' },
        { from: 'kp_003', to: 'kp_007' },
        { from: 'kp_003', to: 'kp_013' },
        { from: 'kp_013', to: 'kp_014' },
        { from: 'kp_013', to: 'kp_015' },
        { from: 'kp_007', to: 'kp_008' },
        { from: 'kp_013', to: 'kp_018' },
        { from: 'kp_017', to: 'kp_018' },
      ],
    }
  }
}

onMounted(() => {
  loadKnowledgeGraph()
})

// 章节图例（保留兼容，图例现用 LAYER_LABELS）
// const chapters = Object.entries(chapterColors).map(([ch, color]) => ({ ch, color }))
</script>

<template>
  <div class="kg-panel">
    <div class="panel-header">
      <span class="panel-title">知识图谱</span>
      <span v-if="highlightedNodeIds.size" class="highlight-badge">
        {{ highlightedNodeIds.size }} 个节点高亮
      </span>
    </div>

    <!-- SVG 图谱：协议栈分层可视化 -->
    <div class="graph-container">
      <svg :viewBox="`0 0 ${SVG_W} ${SVG_H}`" class="graph-svg">
        <!-- 层级背景条 -->
        <g class="layer-backgrounds">
          <rect
            v-for="info in LAYER_LABELS"
            :key="info.layer"
            x="0"
            :y="SVG_H - (info.layer + 1) * LAYER_H"
            :width="SVG_W"
            :height="LAYER_H"
            :fill="info.color"
            opacity="0.05"
            rx="0"
          />
          <!-- 层级标签 -->
          <text
            v-for="info in LAYER_LABELS"
            :key="'lbl-'+info.layer"
            x="4"
            :y="SVG_H - info.layer * LAYER_H - LAYER_H / 2 + 4"
            font-size="7"
            :fill="info.color"
            opacity="0.7"
            font-weight="600"
          >{{ info.label }}</text>
          <!-- 层分隔线 -->
          <line
            v-for="info in LAYER_LABELS.slice(1)"
            :key="'sep-'+info.layer"
            x1="0" :y1="SVG_H - info.layer * LAYER_H"
            :x2="SVG_W" :y2="SVG_H - info.layer * LAYER_H"
            stroke="#e2e8f0" stroke-width="1"
          />
        </g>

        <!-- 边（向上箭头代表依赖方向） -->
        <g class="edges">
          <line
            v-for="(edge, i) in visibleEdges"
            :key="`e-${i}`"
            :x1="nodePositions[edge.from]?.x"
            :y1="nodePositions[edge.from]?.y"
            :x2="nodePositions[edge.to]?.x"
            :y2="nodePositions[edge.to]?.y"
            stroke="#cbd5e1"
            stroke-width="1"
            stroke-dasharray="3,2"
            opacity="0.6"
          />
        </g>

        <!-- 节点 -->
        <g class="nodes">
          <g
            v-for="node in layoutNodes"
            :key="node.id"
            :transform="`translate(${node.x}, ${node.y})`"
            class="node-group"
            :class="{ highlighted: highlightedNodeIds.has(node.id), selected: selectedNode?.id === node.id }"
            @click="selectedNode = selectedNode?.id === node.id ? null : node"
          >
            <!-- 高亮光环 -->
            <circle
              v-if="highlightedNodeIds.has(node.id) || weakNodeIds.has(node.id) || strongNodeIds.has(node.id)"
              r="13"
              :fill="getNodeColor(node)"
              opacity="0.18"
            />
            <!-- 节点圆 -->
            <circle
              r="9"
              :fill="getNodeColor(node)"
              :stroke="selectedNode?.id === node.id ? '#1e293b' : 'rgba(255,255,255,0.9)'"
              stroke-width="1.5"
              style="cursor: pointer"
            />
            <!-- 薄弱/掌握指示器 -->
            <text v-if="weakNodeIds.has(node.id)" y="-12" text-anchor="middle" font-size="8">⚠</text>
            <text v-else-if="strongNodeIds.has(node.id)" y="-12" text-anchor="middle" font-size="8">✓</text>
            <!-- 节点标签 -->
            <text
              y="19"
              text-anchor="middle"
              font-size="6.5"
              fill="#334155"
              class="node-label"
            >{{ node.name.slice(0, 6) }}</text>
          </g>
        </g>
      </svg>
    </div>

    <!-- 选中节点详情 -->
    <Transition name="fade">
      <div v-if="selectedNode" class="node-detail">
        <div class="detail-header">
          <div class="detail-dot" :style="`background: ${getNodeColor(selectedNode)}`"></div>
          <span class="detail-name">{{ selectedNode.name }}</span>
          <button class="detail-close" @click="selectedNode = null">×</button>
        </div>
        <div class="detail-meta">
          <span class="meta-tag">{{ selectedNode.chapter }}</span>
          <span class="meta-tag">{{ selectedNode.type }}</span>
          <span v-if="highlightedNodeIds.has(selectedNode.id)" class="meta-tag highlight">当前相关</span>
          <span v-if="weakNodeIds.has(selectedNode.id)" class="meta-tag weak">薄弱点</span>
          <span v-if="strongNodeIds.has(selectedNode.id)" class="meta-tag strong">已掌握</span>
        </div>
      </div>
    </Transition>

    <!-- 图例 -->
    <div class="legend">
      <div class="legend-item">
        <span class="legend-dot" style="background: #f59e0b"></span>
        <span class="legend-label">当前诊断</span>
      </div>
      <div class="legend-item">
        <span class="legend-dot" style="background: #ef4444"></span>
        <span class="legend-label">⚠ 薄弱点</span>
      </div>
      <div class="legend-item">
        <span class="legend-dot" style="background: #22c55e"></span>
        <span class="legend-label">✓ 已掌握</span>
      </div>
      <div class="legend-item">
        <span class="legend-line" style="background: #cbd5e1; width:14px; height:1px; border-top: 1px dashed #94a3b8"></span>
        <span class="legend-label">层依赖</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.kg-panel {
  background: white;
  border-radius: 12px;
  border: 1px solid #e8eef8;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border-bottom: 1px solid #f1f5f9;
}
.panel-title { font-size: 13px; font-weight: 700; color: #1e293b; }
.highlight-badge {
  font-size: 10px; padding: 2px 8px;
  background: #fef3c7; color: #d97706;
  border-radius: 10px; font-weight: 500;
}

.graph-container {
  padding: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.graph-svg {
  width: 100%; max-width: 320px; height: auto;
  overflow: visible;
}

.node-group { transition: transform 0.2s; }
.node-group:hover { transform: scale(1.2); }
.node-group.highlighted circle:last-of-type { filter: drop-shadow(0 0 4px #f59e0b); }
.node-group.selected circle:last-of-type { filter: drop-shadow(0 0 6px rgba(0,0,0,0.4)); }
.node-label { pointer-events: none; }

/* 选中详情 */
.node-detail {
  margin: 0 10px 8px;
  padding: 10px 12px;
  background: #f8faff;
  border-radius: 8px;
  border: 1px solid #e8eef8;
}
.detail-header { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.detail-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.detail-name { flex: 1; font-size: 13px; font-weight: 600; color: #1e293b; }
.detail-close {
  background: none; border: none; color: #94a3b8;
  font-size: 16px; cursor: pointer; padding: 0 2px; line-height: 1;
}
.detail-meta { display: flex; gap: 5px; flex-wrap: wrap; }
.meta-tag {
  font-size: 10px; padding: 2px 7px;
  background: #f1f5f9; color: #475569;
  border-radius: 10px;
}
.meta-tag.highlight { background: #fef3c7; color: #d97706; }
.meta-tag.weak { background: #fee2e2; color: #dc2626; }
.meta-tag.strong { background: #dcfce7; color: #16a34a; }

/* 图例 */
.legend {
  display: flex; gap: 10px; flex-wrap: wrap;
  padding: 8px 12px;
  border-top: 1px solid #f1f5f9;
}
.legend-item { display: flex; align-items: center; gap: 4px; }
.legend-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.legend-line { display: inline-block; flex-shrink: 0; }
.legend-label { font-size: 10px; color: #64748b; }

/* 动画 */
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
