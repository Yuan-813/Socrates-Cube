<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/userStore'
import { useChatStore } from '@/stores/chatStore'
import apiClient from '@/api/client'

const router = useRouter()
const userStore = useUserStore()
const chatStore = useChatStore()

/* ── 维度配置 ── */
const DIM_LABELS: Record<string, string> = {
  conceptual_understanding: '概念理解',
  protocol_analysis:        '协议分析',
  calculation_ability:      '计算能力',
  error_diagnosis:          '错误诊断',
  system_design:            '系统设计',
  knowledge_connection:     '知识迁移',
  expression_clarity:       '表达清晰',
  self_correction:          '自我纠错',
}
const DIM_ICONS: Record<string, string> = {
  conceptual_understanding: '💡',
  protocol_analysis:        '🔬',
  calculation_ability:      '🔢',
  error_diagnosis:          '🩺',
  system_design:            '🏗️',
  knowledge_connection:     '🔗',
  expression_clarity:       '🗣️',
  self_correction:          '🔄',
}
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

/* ── 错题数据 ── */
interface MistakeItem {
  id: string
  question: string
  user_answer?: string
  correct_answer?: string
  explanation?: string
  weak_dim: string
  knowledge_point: string
  created_at: string
}

const loading = ref(false)
const mistakes = ref<MistakeItem[]>([])
const expandedId = ref<string | null>(null)

/* 从 profile 的 weak_points + mastery_map 生成展示项 */
function buildFromProfile(): MistakeItem[] {
  const profile = userStore.profile
  const items: MistakeItem[] = []

  // 从 mastery_map 找出掌握度 < 0.45 的节点
  const masteryMap = profile.mastery_map || {}
  let idx = 0
  for (const [kp, mastery] of Object.entries(masteryMap)) {
    if ((mastery as number) < 0.45) {
      // 映射到最相关的维度
      const dim = mapKpToDim(kp)
      items.push({
        id: `mastery_${idx++}`,
        question: `关于「${kp}」的掌握度不足 (${Math.round((mastery as number) * 100)}%)，建议复习`,
        weak_dim: dim,
        knowledge_point: kp,
        explanation: '该知识点在对话中被诊断为薄弱点，AI 已记录在案',
        created_at: new Date().toISOString(),
      })
    }
  }

  // 从 weak_points 补充
  for (const wp of (profile.weak_points || [])) {
    if (!items.find(i => i.knowledge_point === wp)) {
      const dim = mapKpToDim(wp)
      items.push({
        id: `wp_${idx++}`,
        question: `「${wp}」被标记为薄弱知识点`,
        weak_dim: dim,
        knowledge_point: wp,
        explanation: 'ProfilerAgent 根据多轮对话分析标记为待强化内容',
        created_at: new Date().toISOString(),
      })
    }
  }
  return items
}

function mapKpToDim(kp: string): string {
  const lower = kp.toLowerCase()
  if (lower.includes('计算') || lower.includes('子网') || lower.includes('序列')) return 'calculation_ability'
  if (lower.includes('协议') || lower.includes('报文') || lower.includes('tcp') || lower.includes('udp')) return 'protocol_analysis'
  if (lower.includes('设计') || lower.includes('架构')) return 'system_design'
  if (lower.includes('诊断') || lower.includes('故障')) return 'error_diagnosis'
  if (lower.includes('关联') || lower.includes('迁移')) return 'knowledge_connection'
  if (lower.includes('表达') || lower.includes('说明')) return 'expression_clarity'
  if (lower.includes('修正') || lower.includes('纠错')) return 'self_correction'
  return 'conceptual_understanding'
}

/* 尝试从 Challenger 日志加载错题 */
async function loadChallengerMistakes() {
  const sessionId = chatStore.currentSession?.sessionId
  if (!sessionId) return
  try {
    const resp = await apiClient.get(`/api/v1/logs/session/${sessionId}`)
    const logs: any[] = resp.data?.logs || []
    const challengeLogs = logs.filter(l =>
      l.agent_type === 'challenger' && l.metadata?.is_correct === false
    )
    for (const log of challengeLogs) {
      const meta = log.metadata || {}
      mistakes.value.push({
        id: log.log_id || String(Math.random()),
        question: meta.question || '挑战题目',
        user_answer: meta.user_answer,
        correct_answer: meta.correct_answer,
        explanation: meta.explanation,
        weak_dim: meta.weak_dim || 'conceptual_understanding',
        knowledge_point: meta.knowledge_point || '未知',
        created_at: log.created_at || new Date().toISOString(),
      })
    }
  } catch { /* 忽略加载失败 */ }
}

onMounted(async () => {
  loading.value = true
  await loadChallengerMistakes()
  // 补充 profile 中的薄弱点
  const profileItems = buildFromProfile()
  for (const pi of profileItems) {
    if (!mistakes.value.find(m => m.knowledge_point === pi.knowledge_point)) {
      mistakes.value.push(pi)
    }
  }
  loading.value = false
})

/* 按维度分组 */
const grouped = computed(() => {
  const map: Record<string, MistakeItem[]> = {}
  for (const m of mistakes.value) {
    if (!map[m.weak_dim]) map[m.weak_dim] = []
    map[m.weak_dim].push(m)
  }
  return map
})

const totalCount = computed(() => mistakes.value.length)

function toggleExpand(id: string) {
  expandedId.value = expandedId.value === id ? null : id
}

function goReinforce(kp: string) {
  router.push({ path: '/resources', query: { topic: kp } })
}

function formatTime(ts: string) {
  try { return new Date(ts).toLocaleDateString('zh-CN') } catch { return '' }
}
</script>

<template>
  <div class="mb-wrap">
    <!-- 头部 -->
    <div class="mb-header">
      <div class="mb-header-left">
        <span class="mb-title-icon">📓</span>
        <div>
          <div class="mb-title">智能错题本</div>
          <div class="mb-sub">AI 自动归集薄弱知识点，点击"去强化"生成专属资源</div>
        </div>
      </div>
      <div class="mb-count-badge" v-if="totalCount > 0">
        {{ totalCount }} 条待强化
      </div>
    </div>

    <!-- 加载中 -->
    <div v-if="loading" class="mb-loading">
      <div class="mb-spinner" />
      <span>正在分析薄弱点...</span>
    </div>

    <!-- 空状态 -->
    <div v-else-if="totalCount === 0" class="mb-empty">
      <div class="mb-empty-icon">🎯</div>
      <div class="mb-empty-text">太棒了！暂无薄弱知识点记录</div>
      <div class="mb-empty-sub">继续对话学习后，AI 会自动记录需要强化的内容</div>
    </div>

    <!-- 分组列表 -->
    <div v-else class="mb-groups">
      <div
        v-for="(items, dimKey) in grouped"
        :key="dimKey"
        class="mb-group"
      >
        <!-- 维度标题 -->
        <div class="mb-group-header" :style="{ borderLeftColor: DIM_COLORS[dimKey] }">
          <span class="mb-group-icon">{{ DIM_ICONS[dimKey] }}</span>
          <span class="mb-group-name" :style="{ color: DIM_COLORS[dimKey] }">
            {{ DIM_LABELS[dimKey] }}
          </span>
          <el-tag
            :color="DIM_COLORS[dimKey] + '20'"
            effect="plain"
            size="small"
            :style="{ color: DIM_COLORS[dimKey], borderColor: DIM_COLORS[dimKey] + '50' }"
          >
            {{ items.length }} 条
          </el-tag>
        </div>

        <!-- 错题卡片列表 -->
        <div class="mb-items">
          <div
            v-for="item in items"
            :key="item.id"
            class="mb-item"
            :class="{ expanded: expandedId === item.id }"
            @click="toggleExpand(item.id)"
          >
            <div class="mb-item-top">
              <div class="mb-item-q">{{ item.question }}</div>
              <div class="mb-item-meta">
                <span class="mb-kp-tag">{{ item.knowledge_point }}</span>
                <span class="mb-time">{{ formatTime(item.created_at) }}</span>
                <button
                  class="mb-reinforce-btn"
                  :style="{ background: DIM_COLORS[dimKey] }"
                  @click.stop="goReinforce(item.knowledge_point)"
                >
                  去强化
                </button>
              </div>
            </div>

            <!-- 展开详情 -->
            <transition name="detail-fade">
              <div v-if="expandedId === item.id" class="mb-item-detail">
                <div v-if="item.user_answer" class="mb-detail-row">
                  <span class="mb-detail-label">你的回答：</span>
                  <span class="mb-detail-val wrong">{{ item.user_answer }}</span>
                </div>
                <div v-if="item.correct_answer" class="mb-detail-row">
                  <span class="mb-detail-label">正确答案：</span>
                  <span class="mb-detail-val correct">{{ item.correct_answer }}</span>
                </div>
                <div v-if="item.explanation" class="mb-explanation">
                  <span class="mb-detail-label">解析：</span>
                  {{ item.explanation }}
                </div>
              </div>
            </transition>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.mb-wrap {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.mb-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.mb-header-left {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.mb-title-icon { font-size: 20px; flex-shrink: 0; margin-top: 2px; }

.mb-title {
  font-size: 16px;
  font-weight: 700;
  color: #1e293b;
}

.mb-sub {
  font-size: 12px;
  color: #64748b;
  margin-top: 2px;
  line-height: 1.4;
}

.mb-count-badge {
  font-size: 12px;
  font-weight: 700;
  color: #ef4444;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 20px;
  padding: 4px 12px;
  white-space: nowrap;
  flex-shrink: 0;
}

/* 加载 */
.mb-loading {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 24px;
  color: #6366f1;
  font-size: 13px;
  justify-content: center;
}

.mb-spinner {
  width: 18px; height: 18px;
  border: 2px solid #c7d2fe;
  border-top-color: #6366f1;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

/* 空状态 */
.mb-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 32px;
  background: #f8faff;
  border-radius: 12px;
  border: 1px dashed #c7d2fe;
}

.mb-empty-icon { font-size: 36px; }
.mb-empty-text { font-size: 14px; font-weight: 600; color: #475569; }
.mb-empty-sub  { font-size: 12px; color: #94a3b8; text-align: center; }

/* 分组 */
.mb-groups { display: flex; flex-direction: column; gap: 16px; }

.mb-group { display: flex; flex-direction: column; gap: 8px; }

.mb-group-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-left: 10px;
  border-left: 3px solid;
}

.mb-group-icon { font-size: 15px; }
.mb-group-name { font-size: 13px; font-weight: 700; flex: 1; }

/* 错题卡片 */
.mb-items { display: flex; flex-direction: column; gap: 6px; }

.mb-item {
  background: #fafbff;
  border: 1px solid #e8eef8;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.18s;
  overflow: hidden;
}

.mb-item:hover {
  border-color: #a5b4fc;
  box-shadow: 0 2px 8px rgba(99,102,241,0.1);
}

.mb-item.expanded { border-color: #6366f1; }

.mb-item-top {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px 14px;
}

.mb-item-q {
  font-size: 13px;
  color: #1e293b;
  line-height: 1.5;
  font-weight: 500;
}

.mb-item-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.mb-kp-tag {
  font-size: 11px;
  color: #6366f1;
  background: #eff2ff;
  border-radius: 4px;
  padding: 2px 7px;
  font-weight: 500;
}

.mb-time {
  font-size: 11px;
  color: #94a3b8;
  flex: 1;
}

.mb-reinforce-btn {
  font-size: 11px;
  font-weight: 600;
  color: white;
  border: none;
  border-radius: 6px;
  padding: 4px 10px;
  cursor: pointer;
  transition: all 0.18s;
  flex-shrink: 0;
}

.mb-reinforce-btn:hover {
  transform: scale(1.06);
  box-shadow: 0 2px 8px rgba(0,0,0,0.2);
}

/* 展开详情 */
.mb-item-detail {
  padding: 12px 14px;
  border-top: 1px dashed #e2e8f0;
  display: flex;
  flex-direction: column;
  gap: 8px;
  background: #f8faff;
}

.mb-detail-row {
  display: flex;
  gap: 6px;
  font-size: 12px;
  align-items: flex-start;
}

.mb-detail-label {
  font-weight: 600;
  color: #475569;
  flex-shrink: 0;
  font-size: 12px;
}

.mb-detail-val {
  flex: 1;
  font-size: 12px;
  line-height: 1.5;
}

.mb-detail-val.wrong   { color: #ef4444; }
.mb-detail-val.correct { color: #22c55e; font-weight: 600; }

.mb-explanation {
  font-size: 12px;
  color: #64748b;
  line-height: 1.6;
  background: white;
  border-radius: 8px;
  padding: 8px 10px;
  border: 1px solid #e2e8f0;
}

/* 动画 */
.detail-fade-enter-active,
.detail-fade-leave-active {
  transition: opacity 0.2s ease, max-height 0.25s ease;
  overflow: hidden;
  max-height: 300px;
}

.detail-fade-enter-from,
.detail-fade-leave-to {
  opacity: 0;
  max-height: 0;
}
</style>
