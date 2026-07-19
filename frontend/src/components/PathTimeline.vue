<script setup lang="ts">
import { ref, computed } from 'vue'
import type { LearningPathNode } from '@/types'

const pathNodes = ref<LearningPathNode[]>([
  { id: 'n1', title: 'TCP/IP 概述', status: 'completed', estimatedTime: 30, reason: '基础概念已掌握', reason_sources: { graph_dependency: '知识图谱起始节点，无前置依赖', diagnosis_result: '诊断显示基础概念理解良好', cognitive_style: '视觉型学习者，推荐图文结合资源' } },
  { id: 'n2', title: 'TCP 报文格式', status: 'completed', estimatedTime: 45, reason: '报文格式理解扎实', reason_sources: { graph_dependency: '前置依赖: TCP/IP 概述(kp_001)', diagnosis_result: '字段记忆准确，理解深入', cognitive_style: '适合代码实操类练习' } },
  { id: 'n3', title: 'TCP 连接管理', status: 'current', estimatedTime: 60, reason: '你在连接管理练习中3次混淆SYN/ACK标志位', reason_sources: { graph_dependency: '前置依赖: TCP 报文格式(kp_002)', diagnosis_result: '三次握手流程遗漏型错误，需强化', cognitive_style: '推荐仿真动画+步骤拆解' } },
  { id: 'n4', title: 'TCP 可靠传输', status: 'pending', estimatedTime: 50, reason_sources: { graph_dependency: '前置依赖: TCP 连接管理(kp_003)', diagnosis_result: '尚未诊断', cognitive_style: '待画像分析' } },
  { id: 'n5', title: 'TCP 拥塞控制', status: 'locked', estimatedTime: 55 },
  { id: 'n6', title: '综合实践项目', status: 'locked', estimatedTime: 120 },
])

// 扩展状态配置
const statusConfig: Record<string, { color: string; icon: string; label: string; bgGradient: string }> = {
  completed: { color: '#10b981', icon: '✓', label: '已完成', bgGradient: 'linear-gradient(135deg, #d1fae5, #ecfdf5)' },
  current: { color: '#3b82f6', icon: '▶', label: '进行中', bgGradient: 'linear-gradient(135deg, #dbeafe, #eff6ff)' },
  pending: { color: '#f59e0b', icon: '◉', label: '待学习', bgGradient: 'linear-gradient(135deg, #fef3c7, #fffbeb)' },
  locked: { color: '#94a3b8', icon: '🔒', label: '已锁定', bgGradient: 'linear-gradient(135deg, #f1f5f9, #f8fafc)' },
}

// 推荐理由弹窗
const reasonModalVisible = ref(false)
const selectedNode = ref<LearningPathNode | null>(null)

function openReasonDetail(node: LearningPathNode) {
  selectedNode.value = node
  reasonModalVisible.value = true
}

// 整体进度
const completedCount = computed(() => pathNodes.value.filter(n => n.status === 'completed').length)
const totalCount = computed(() => pathNodes.value.length)
const progressPercent = computed(() => Math.round((completedCount.value / totalCount.value) * 100))

// 总预估时间
const totalEstimatedTime = computed(() => pathNodes.value.reduce((sum, n) => sum + (n.estimatedTime || 0), 0))
const completedTime = computed(() => pathNodes.value.filter(n => n.status === 'completed').reduce((sum, n) => sum + (n.estimatedTime || 0), 0))
</script>

<template>
  <div class="path-timeline">
    <!-- 整体进度条 -->
    <div class="progress-overview">
      <div class="progress-header">
        <h4 class="progress-title">学习进度</h4>
        <span class="progress-percent">{{ progressPercent }}%</span>
      </div>
      <div class="progress-bar-bg">
        <div class="progress-bar-fill" :style="{ width: progressPercent + '%' }"></div>
      </div>
      <div class="progress-meta">
        <span>已完成 {{ completedCount }}/{{ totalCount }} 节点</span>
        <span>已学 {{ completedTime }} 分钟 / 预计 {{ totalEstimatedTime }} 分钟</span>
      </div>
    </div>

    <!-- 时间线 -->
    <div class="timeline-container">
      <div
        v-for="(node, index) in pathNodes"
        :key="node.id"
        class="timeline-item"
        :class="node.status"
        @click="node.reason_sources && openReasonDetail(node)"
      >
        <!-- 连接线 -->
        <div class="timeline-connector" v-if="index !== pathNodes.length - 1">
          <div class="connector-line" :class="{ filled: node.status === 'completed' }"></div>
        </div>

        <!-- 节点图标 -->
        <div class="timeline-dot" :style="{ borderColor: statusConfig[node.status]?.color || '#94a3b8' }">
          <span class="dot-icon" :style="{ color: statusConfig[node.status]?.color || '#94a3b8' }">
            {{ statusConfig[node.status]?.icon || '•' }}
          </span>
          <div v-if="node.status === 'current'" class="dot-pulse"></div>
        </div>

        <!-- 节点内容 -->
        <div class="timeline-content" :style="{ background: statusConfig[node.status]?.bgGradient }">
          <div class="node-header">
            <h4 class="node-title">{{ node.title }}</h4>
            <div class="node-badges">
              <el-tag
                :color="statusConfig[node.status]?.color + '18'"
                :style="{ color: statusConfig[node.status]?.color, borderColor: statusConfig[node.status]?.color + '40' }"
                size="small"
              >
                {{ statusConfig[node.status]?.label }}
              </el-tag>
              <el-tag v-if="node.estimatedTime" type="info" size="small" effect="plain">
                ⏱ {{ node.estimatedTime }}min
              </el-tag>
            </div>
          </div>

          <!-- 推荐理由摘要 -->
          <div v-if="node.reason" class="node-reason">
            <el-icon color="#3b82f6"><InfoFilled /></el-icon>
            <span>{{ node.reason }}</span>
          </div>

          <!-- 三维理由标记（如果有） -->
          <div v-if="node.reason_sources" class="reason-sources-mini">
            <span class="source-chip graph" title="图谱依赖">📊 图谱</span>
            <span class="source-chip diagnosis" title="诊断结果">🔍 诊断</span>
            <span class="source-chip cognitive" title="认知风格">🧠 风格</span>
            <span class="view-detail">点击查看 →</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 路径统计 -->
    <div class="path-stats">
      <div class="stat-item completed">
        <div class="stat-icon">✅</div>
        <div class="stat-value">{{ pathNodes.filter(n => n.status === 'completed').length }}</div>
        <div class="stat-label">已完成</div>
      </div>
      <div class="stat-item current">
        <div class="stat-icon">📖</div>
        <div class="stat-value">{{ pathNodes.filter(n => n.status === 'current').length }}</div>
        <div class="stat-label">进行中</div>
      </div>
      <div class="stat-item pending">
        <div class="stat-icon">📝</div>
        <div class="stat-value">{{ pathNodes.filter(n => n.status === 'pending').length }}</div>
        <div class="stat-label">待学习</div>
      </div>
      <div class="stat-item locked">
        <div class="stat-icon">🔒</div>
        <div class="stat-value">{{ pathNodes.filter(n => n.status === 'locked').length }}</div>
        <div class="stat-label">已锁定</div>
      </div>
    </div>

    <!-- 三维推荐理由弹窗 -->
    <el-dialog v-model="reasonModalVisible" title="推荐理由详情" width="520px" destroy-on-close>
      <div v-if="selectedNode" class="reason-detail">
        <div class="reason-node-title">
          <h3>{{ selectedNode.title }}</h3>
          <el-tag :color="statusConfig[selectedNode.status]?.color + '18'" :style="{ color: statusConfig[selectedNode.status]?.color }">
            {{ statusConfig[selectedNode.status]?.label }}
          </el-tag>
        </div>

        <!-- 三维理由分区 -->
        <div class="reason-section" v-if="selectedNode.reason_sources?.graph_dependency">
          <div class="reason-section-header">
            <span class="reason-section-icon">📊</span>
            <span class="reason-section-title">图谱依赖依据</span>
          </div>
          <p class="reason-section-text">{{ selectedNode.reason_sources.graph_dependency }}</p>
        </div>

        <div class="reason-section" v-if="selectedNode.reason_sources?.diagnosis_result">
          <div class="reason-section-header">
            <span class="reason-section-icon">🔍</span>
            <span class="reason-section-title">诊断结果依据</span>
          </div>
          <p class="reason-section-text">{{ selectedNode.reason_sources.diagnosis_result }}</p>
        </div>

        <div class="reason-section" v-if="selectedNode.reason_sources?.cognitive_style">
          <div class="reason-section-header">
            <span class="reason-section-icon">🧠</span>
            <span class="reason-section-title">认知风格依据</span>
          </div>
          <p class="reason-section-text">{{ selectedNode.reason_sources.cognitive_style }}</p>
        </div>

        <div v-if="selectedNode.reason" class="reason-overall">
          <span class="overall-label">综合推荐理由：</span>
          <p>{{ selectedNode.reason }}</p>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<style scoped>
.path-timeline {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* 整体进度条 */
.progress-overview {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 16px;
}
.progress-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.progress-title { font-size: 15px; font-weight: 600; color: #1e293b; margin: 0; }
.progress-percent { font-size: 20px; font-weight: 700; color: #3b82f6; font-family: 'JetBrains Mono', monospace; }
.progress-bar-bg {
  height: 10px;
  background: #e2e8f0;
  border-radius: 5px;
  overflow: hidden;
}
.progress-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #3b82f6, #60a5fa);
  border-radius: 5px;
  transition: width 0.6s ease;
}
.progress-meta {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-size: 12px;
  color: #64748b;
}

/* 时间线容器 */
.timeline-container {
  position: relative;
  padding-left: 28px;
}

.timeline-item {
  position: relative;
  padding-bottom: 28px;
  display: flex;
  gap: 16px;
  cursor: pointer;
  transition: transform 0.15s;
}
.timeline-item:hover { transform: translateX(4px); }
.timeline-item:last-child { padding-bottom: 0; }
.timeline-item.locked { cursor: not-allowed; opacity: 0.55; }
.timeline-item.locked:hover { transform: none; }
.timeline-item.locked .timeline-content { pointer-events: none; }

/* 连接线 */
.timeline-connector {
  position: absolute;
  left: 19px;
  top: 40px;
  width: 2px;
  height: calc(100% - 40px);
}
.connector-line {
  width: 100%;
  height: 100%;
  background: #e2e8f0;
  transition: background 0.3s;
}
.connector-line.filled { background: #10b981; }

/* 节点圆点 */
.timeline-dot {
  position: relative;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2.5px solid;
  flex-shrink: 0;
  background: #fff;
  z-index: 1;
}
.dot-icon { font-size: 16px; font-weight: 700; }

/* 当前节点脉冲动画 */
.dot-pulse {
  position: absolute;
  inset: -4px;
  border-radius: 50%;
  border: 2px solid #3b82f6;
  animation: pulse-ring 1.5s ease-out infinite;
}
@keyframes pulse-ring {
  0% { opacity: 1; transform: scale(1); }
  100% { opacity: 0; transform: scale(1.5); }
}

/* 节点内容卡片 */
.timeline-content {
  flex: 1;
  border-radius: 12px;
  padding: 14px 16px;
  border: 1px solid #e2e8f0;
  transition: all 0.2s;
}
.timeline-item:hover .timeline-content {
  box-shadow: 0 4px 12px rgba(0,0,0,0.06);
}
.timeline-item.current .timeline-content {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.node-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}
.node-title { font-size: 15px; font-weight: 600; color: #1e293b; margin: 0; }
.node-badges { display: flex; gap: 6px; }

.node-reason {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  padding: 8px 12px;
  background: rgba(255,255,255,0.7);
  border-radius: 8px;
  border-left: 3px solid #3b82f6;
  font-size: 13px;
  color: #334155;
  line-height: 1.5;
  margin-bottom: 8px;
}

/* 三维理由迷你标记 */
.reason-sources-mini {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}
.source-chip {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 500;
}
.source-chip.graph { background: #dbeafe; color: #1d4ed8; }
.source-chip.diagnosis { background: #fee2e2; color: #b91c1c; }
.source-chip.cognitive { background: #ede9fe; color: #6d28d9; }
.view-detail { font-size: 11px; color: #94a3b8; margin-left: auto; }

/* 统计面板 */
.path-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}
.stat-item {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  text-align: center;
  border: 1px solid #e2e8f0;
  transition: all 0.2s;
}
.stat-item:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.06); }
.stat-icon { font-size: 20px; margin-bottom: 4px; }
.stat-value { font-size: 24px; font-weight: 700; color: #1e293b; }
.stat-label { font-size: 12px; color: #64748b; margin-top: 4px; }

/* 理由弹窗 */
.reason-detail { display: flex; flex-direction: column; gap: 16px; }
.reason-node-title { display: flex; align-items: center; gap: 12px; }
.reason-node-title h3 { margin: 0; font-size: 18px; color: #1e293b; }

.reason-section {
  padding: 14px;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  background: #f8fafc;
}
.reason-section-header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.reason-section-icon { font-size: 18px; }
.reason-section-title { font-size: 14px; font-weight: 600; color: #1e293b; }
.reason-section-text { font-size: 13px; color: #475569; line-height: 1.6; margin: 0; }

.reason-overall {
  padding: 14px;
  background: linear-gradient(135deg, #eff6ff, #f0fdf4);
  border-radius: 10px;
  border: 1px solid #bfdbfe;
}
.overall-label { font-size: 13px; font-weight: 600; color: #1e40af; }
.reason-overall p { font-size: 13px; color: #334155; margin: 6px 0 0; line-height: 1.6; }

@media (max-width: 640px) {
  .path-stats { grid-template-columns: repeat(2, 1fr); }
  .progress-meta { flex-direction: column; gap: 4px; }
  .node-header { flex-direction: column; align-items: flex-start; gap: 6px; }
}
</style>
