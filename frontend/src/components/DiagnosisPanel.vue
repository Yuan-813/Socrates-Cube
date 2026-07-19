<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useChatStore } from '@/stores/chatStore'
import { useUserStore } from '@/stores/userStore'
import ChallengerQuizCard from '@/components/ChallengerQuizCard.vue'
import type { DiagnosisResult } from '@/types'
import { resolveNodeName } from '@/utils/kgMap'
import RepairOverview from '@/components/RepairOverview.vue'
import DiagnosisFlowStepper from '@/components/DiagnosisFlowStepper.vue'

const chatStore = useChatStore()
const userStore = useUserStore()
const router = useRouter()

const handleInterventionClick = (rec: any) => {
  const routes: Record<string, string> = {
    simulation: '/simulator',
    exercise: '/resources',
    challenge: '/challenger',
    doc: '/resources',
  }

  const query: Record<string, string> = { from: 'diagnosis' }
  if (rec.id) query.scenario = rec.id
  if (rec.type === 'exercise' || rec.type === 'doc') query.type = rec.type

  router.push({ path: routes[rec.type] || '/resources', query })
}

const handleSimulatorClick = (rec: any) => {
  console.log('[EVENT]', {
    event: 'simulator_start',
    scenario: rec.id,
    source: 'diagnosis_intervention',
  })
  router.push('/simulator?scenario=' + rec.id)
}

const diagnosis = computed<DiagnosisResult>(() => {
  return chatStore.lastDiagnosis || {
    is_correct: true,
    confidence: 0,
    surface_error: null,
    error_type: 'none',
    root_causes: [],
    missing_prerequisites: [],
    pattern: null,
    intervention_suggestion: '',
    related_node_ids: [],
  }
})

const confidencePercent = computed(() => Math.round((diagnosis.value.confidence ?? 0) * 100))

/** 只要 lastDiagnosis 不为 null 就展示（包括 is_correct=true 的正确回答） */
const hasDiagnosis = computed(() => chatStore.lastDiagnosis !== null && chatStore.lastDiagnosis !== undefined)

/** 域外问题拦截：scope_notice 触发 */
const isScopeRejected = computed(() => chatStore.lastScopeNotice !== null && chatStore.lastScopeNotice !== undefined)

/** 正在流式输出且尚未收到诊断结果 */
const isDiagnosing = computed(() => chatStore.isStreaming && !hasDiagnosis.value && !isScopeRejected.value)

// 错误类型图标和颜色映射
const errorTypeConfig: Record<string, { icon: string; color: string; label: string }> = {
  layer_misplacement: { icon: '⚠️', color: '#ef4444', label: '层级错位' },
  flow_omission: { icon: '🔄', color: '#f59e0b', label: '流程遗漏' },
  concept_confusion: { icon: '🔀', color: '#8b5cf6', label: '概念混淆' },
  term_confusion: { icon: '📝', color: '#06b6d4', label: '术语混淆' },
  over_simplification: { icon: '📉', color: '#f97316', label: '过度简化' },
  calculation_error: { icon: '🔢', color: '#ec4899', label: '计算错误' },
  factual: { icon: '❌', color: '#dc2626', label: '事实错误' },
  none: { icon: '✅', color: '#10b981', label: '回答正确' },
}

const currentErrorConfig = computed(() => {
  return errorTypeConfig[diagnosis.value.error_type || 'none'] || errorTypeConfig.none
})

// 误解模式说明 Tooltip
const patternTooltips: Record<string, string> = {
  '层次穿越型': '混淆不同网络层的协议职责，如将HTTP直接对应到IP层',
  '流程遗漏型': '记住了流程但遗漏关键步骤，不理解每步的意义',
  '局部正确型': '理解了部分但过度泛化，把特定条件结论推广到全部场景',
  '术语混淆型': '多个相似术语混用，如SYN/ACK/FIN、rwnd/cwnd',
  '过度简化型': '理解了简化版本但忽略关键细节和约束条件',
  '推理断链型': '逻辑跳跃或因果关系错误，将相关性误当作因果性',
  '混合模式': '同时具有两种以上模式的特征',
}

// ======================================================================
//  能力置信度：主指标 = 学生综合掌握度（8维均分）
//  区别于 diagnosis.confidence（AI 对本次诊断结果的局部把握）
// ======================================================================

/** 学生当前综合能力置信度 = profileCompleteness（8维均分） */
const masteryScore = computed(() => userStore.profileCompleteness)
const masteryHistory = computed(() => userStore.masteryHistory)
const hasMasteryTrend = computed(() => masteryHistory.value.length >= 2)

const masteryColor = computed(() => {
  const s = masteryScore.value
  if (s >= 80) return '#10b981'
  if (s >= 65) return '#3b82f6'
  if (s >= 50) return '#f59e0b'
  return '#ef4444'
})
const masteryLabel = computed(() => {
  const s = masteryScore.value
  if (s >= 80) return '极佳'
  if (s >= 65) return '良好'
  if (s >= 50) return '中等'
  if (s >= 35) return '待提升'
  return '薄弱'
})

/** 本次诊断的 AI 局部精度（次要指标） */
const diagAccuracyPercent = computed(() => Math.round((diagnosis.value.confidence ?? 0) * 100))

// 能力置信度成长曲线的 SVG 折线数据
const masteryPoints = computed(() => {
  const h = masteryHistory.value
  if (h.length < 2) return []
  const n = h.length
  return h.map((v, i) => ({
    x: Math.round((i / (n - 1)) * 94) + 3,
    y: Math.round(38 - (v / 100) * 34) + 2,
  }))
})
const masteryLineStr = computed(() =>
  masteryPoints.value.map(p => `${p.x},${p.y}`).join(' ')
)
const masteryAreaStr = computed(() => {
  const pts = masteryPoints.value
  if (!pts.length) return ''
  return `${pts[0].x},40 ${pts.map(p => `${p.x},${p.y}`).join(' ')} ${pts[pts.length - 1].x},40`
})
const masteryLast = computed(() => masteryPoints.value[masteryPoints.value.length - 1] ?? { x: 0, y: 0 })
const masteryMin = computed(() => masteryHistory.value.length ? Math.min(...masteryHistory.value) : 0)
const masteryMax = computed(() => masteryHistory.value.length ? Math.max(...masteryHistory.value) : 0)

// 已废弃的旧字段保留局部兴趣（三层诊断展示从 confidencePercent 读取）
// confidencePercent 已在上方第 54 行定义，不重复声明
const confidenceColor = computed(() => {
  if (confidencePercent.value >= 85) return '#10b981'
  if (confidencePercent.value >= 70) return '#3b82f6'
  if (confidencePercent.value >= 50) return '#f59e0b'
  return '#ef4444'
})
</script>

<template>
  <div class="diagnosis-panel">
    <!-- 诊断链路步骤条 -->
    <DiagnosisFlowStepper />

    <!-- 诊断运行中加载态 -->
    <section v-if="isDiagnosing" class="diagnosing-state">
      <div class="diagnosing-header">
        <span class="diagnosing-pulse"></span>
        <span class="diagnosing-title">三层认知诊断进行中…</span>
      </div>
      <div class="diagnosing-steps">
        <div class="diag-step"><span class="step-dot active"></span><span>表层错误识别</span></div>
        <div class="diag-step"><span class="step-dot"></span><span>根因溯源分析</span></div>
        <div class="diag-step"><span class="step-dot"></span><span>误区模式匹配</span></div>
      </div>
    </section>
    
    <!-- 域外拦截状态 -->
    <section v-else-if="isScopeRejected" class="scope-notice-state">
      <div class="sn-header">
        <span class="sn-icon">🛡️</span>
        <div class="sn-title-block">
          <span class="sn-title">域外问题已拦截</span>
          <span class="sn-sub">TrustMechanism 范围校验层</span>
        </div>
        <span class="sn-badge">OUT OF SCOPE</span>
      </div>
      <p class="sn-desc">{{ chatStore.lastScopeNotice?.description }}</p>
      <div class="sn-suggestions">
        <span class="sn-hint">✨ 试试问这些：</span>
        <div class="sn-chips">
          <span class="sn-chip">什么是 TCP 三次握手？</span>
          <span class="sn-chip">HTTP 和 HTTPS 的区别</span>
          <span class="sn-chip">DNS 解析流程</span>
          <span class="sn-chip">TLS 1.3 改进了什么？</span>
        </div>
      </div>
    </section>
    
    <!-- 无诊断状态 -->
    <section v-else-if="!hasDiagnosis" class="empty-state">
      <div class="empty-icon">
        <el-icon :size="36"><Search /></el-icon>
      </div>
      <p class="empty-text">暂无诊断结果</p>
      <p class="empty-hint">发送计算机网络相关问题后，系统将自动进行三层认知诊断</p>
    </section>

    <template v-else>
      <div v-if="!diagnosis.is_correct" class="diagnosis-trigger">
        <div class="trigger-icon">🔍</div>
        <div class="trigger-content">
          <span class="trigger-title">诊断触发</span>
          <p class="trigger-desc">
            {{ diagnosis.trigger || '系统检测到回答中可能存在概念边界或协议流程误区。' }}
          </p>
        </div>
        <el-tag type="danger" effect="dark" size="small">需关注</el-tag>
      </div>

      <!-- 正确回答提示 -->
      <div v-else class="correct-banner">
        <span class="correct-icon">✅</span>
        <span class="correct-text">回答正确，未发现概念性错误</span>
        <el-tag type="success" effect="dark" size="small">
          置信度 {{ confidencePercent }}%
        </el-tag>
      </div>

      <!-- 能力置信度区域：学生综合掌握度（主）+ 能力成长曲线（次） -->
      <div class="confidence-section">
        <div class="conf-section-header">
          <span class="conf-section-icon">📊</span>
          <span class="conf-section-title">学生能力置信度</span>
          <el-tooltip
            content="能力置信度 = 8 个能力维度的综合得分，展示学生对计算机网络的整体掌握水平。曲线展示每次对话后的成长轨迹。详细 8 维展示请查看『能力画像』页"
            placement="top" effect="light"
          >
            <el-icon size="12" style="color:#94a3b8;cursor:help"><InfoFilled /></el-icon>
          </el-tooltip>
          <span v-if="hasMasteryTrend" class="conf-trend-count">{{ masteryHistory.length }} 轮成长</span>
          <!-- 次要：AI 诊断精度 -->
          <span class="diag-accuracy-badge" :style="{ color: confidenceColor }">AI诊断精度 {{ diagAccuracyPercent }}%</span>
        </div>
            
        <div class="conf-body">
          <!-- 学生能力置信度仳表盘（主指标） -->
          <div class="conf-gauge">
            <svg viewBox="0 0 100 58" class="gauge-svg">
              <path d="M 8 54 A 42 42 0 0 1 92 54" fill="none" stroke="#e2e8f0" stroke-width="7" stroke-linecap="round"/>
              <path
                d="M 8 54 A 42 42 0 0 1 92 54"
                fill="none"
                :stroke="masteryColor"
                stroke-width="7"
                stroke-linecap="round"
                :stroke-dasharray="`${masteryScore * 1.32} 132`"
              />
            </svg>
            <div class="gauge-val" :style="{ color: masteryColor }">{{ masteryScore }}%</div>
            <div class="gauge-lbl">{{ masteryLabel }}</div>
          </div>
            
          <!-- 能力置信度成长曲线 -->
          <div class="conf-right">
            <template v-if="hasMasteryTrend">
              <div class="trend-label-row">
                <span class="trend-title">能力置信度成长曲线</span>
              </div>
              <svg class="sparkline" viewBox="0 0 100 40" preserveAspectRatio="none">
                <!-- 范围参考线 -->
                <line x1="3" y1="2" x2="97" y2="2" stroke="#e2e8f0" stroke-width="0.5" stroke-dasharray="2,2"/>
                <line x1="3" y1="22" x2="97" y2="22" stroke="#e2e8f0" stroke-width="0.5" stroke-dasharray="2,2"/>
                <!-- 面积渐变填充 -->
                <polygon :points="masteryAreaStr" fill="rgba(99,102,241,0.12)"/>
                <!-- 成长曲线 -->
                <polyline :points="masteryLineStr" fill="none" stroke="#6366f1" stroke-width="1.5" stroke-linejoin="round" stroke-linecap="round"/>
                <!-- 最新大圆点 -->
                <circle :cx="masteryLast.x" :cy="masteryLast.y" r="3" :fill="masteryColor" stroke="#fff" stroke-width="1"/>
              </svg>
              <div class="trend-range-row">
                <span class="range-low">{{ masteryMin }}%</span>
                <span class="range-cur" :style="{ color: masteryColor }">{{ masteryHistory.length }}轮</span>
                <span class="range-high">{{ masteryMax }}%</span>
              </div>
            </template>
            <!-- 无历史时显示图例 + 提示 -->
            <template v-else>
              <div class="conf-legend">
                <div class="legend-item"><span class="legend-dot" style="background:#10b981"></span><span>≥80% 极佳</span></div>
                <div class="legend-item"><span class="legend-dot" style="background:#3b82f6"></span><span>65%+ 良好</span></div>
                <div class="legend-item"><span class="legend-dot" style="background:#f59e0b"></span><span>50%+ 中等</span></div>
                <div class="legend-item"><span class="legend-dot" style="background:#ef4444"></span><span>&lt;50% 待提升</span></div>
              </div>
              <p class="trend-hint">每次对话 ProfilerAgent 更新画像后自动记录</p>
            </template>
          </div>
        </div>
      </div>

      <!-- 三层诊断递进展示 -->
      <div class="diagnosis-layers">
        <!-- 第一层：表层错误识别 -->
        <div class="layer-card layer-1" :class="{ 'is-correct': diagnosis.is_correct }">
          <div class="layer-header">
            <div class="layer-badge layer-badge-1">
              <span class="badge-num">1</span>
              <span class="badge-text">表层错误识别</span>
            </div>
            <span class="layer-tag">Surface Error</span>
          </div>

          <div class="layer-body">
            <div class="error-display">
              <span class="error-icon">{{ currentErrorConfig.icon }}</span>
              <div class="error-info">
                <el-tag
                  :type="diagnosis.is_correct ? 'success' : 'danger'"
                  effect="dark"
                  size="large"
                >
                  {{ diagnosis.is_correct ? '理解正确' : diagnosis.surface_error }}
                </el-tag>
                <div class="error-type-row" v-if="!diagnosis.is_correct">
                  <span class="error-type-dot" :style="{ background: currentErrorConfig.color }"></span>
                  <span class="error-type-label">{{ currentErrorConfig.label }}</span>
                  <span class="error-type-code">{{ diagnosis.error_type }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 递进箭头 -->
          <div class="layer-arrow" v-if="!diagnosis.is_correct">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
              <path d="M12 4v16m0 0l-6-6m6 6l6-6" stroke="#94a3b8" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </div>
        </div>

        <!-- 第二层：根因分析 -->
        <div class="layer-card layer-2" :class="{ 'is-correct': diagnosis.is_correct }">
          <div class="layer-header">
            <div class="layer-badge layer-badge-2">
              <span class="badge-num">2</span>
              <span class="badge-text">根因溯源分析</span>
            </div>
            <span class="layer-tag">Root Cause</span>
          </div>

          <div class="layer-body">
            <div class="root-cause-tree">
              <div
                v-for="(cause, idx) in (diagnosis.root_causes || [])"
                :key="idx"
                class="cause-node"
              >
                <div class="cause-connector"></div>
                <div class="cause-content">
                  <span class="cause-icon">🔗</span>
                  <span class="cause-text">{{ cause }}</span>
                </div>
              </div>
              <div v-if="!diagnosis.root_causes?.length" class="no-cause">
                <span class="no-cause-icon">📋</span>
                <span>暂无根因分析</span>
              </div>
            </div>

            <!-- 缺失前置知识 -->
            <div v-if="diagnosis.missing_prerequisites?.length" class="missing-prereqs">
              <span class="prereqs-label">缺失前置知识：</span>
              <el-tag
                v-for="prereq in diagnosis.missing_prerequisites"
                :key="prereq"
                size="small"
                type="warning"
                effect="plain"
                class="prereq-tag"
              >
                {{ prereq }}
              </el-tag>
            </div>
          </div>

          <div class="layer-arrow" v-if="!diagnosis.is_correct">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
              <path d="M12 4v16m0 0l-6-6m6 6l6-6" stroke="#94a3b8" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </div>
        </div>

        <!-- 第三层：误区模式匹配 -->
        <div class="layer-card layer-3" :class="{ 'is-correct': diagnosis.is_correct }">
          <div class="layer-header">
            <div class="layer-badge layer-badge-3">
              <span class="badge-num">3</span>
              <span class="badge-text">误区模式匹配</span>
            </div>
            <span class="layer-tag">Pattern Match</span>
          </div>

          <div class="layer-body">
            <div class="pattern-display">
              <el-tooltip
                v-if="diagnosis.pattern"
                :content="patternTooltips[diagnosis.pattern] || '未知模式'"
                placement="top"
                effect="dark"
              >
                <div class="pattern-badge">
                  <span class="pattern-icon">🧩</span>
                  <span class="pattern-name">{{ diagnosis.pattern }}</span>
                  <el-icon class="pattern-help"><QuestionFilled /></el-icon>
                </div>
              </el-tooltip>
              <span v-else class="no-pattern">
                <el-icon><InfoFilled /></el-icon>
                无明确模式
              </span>
            </div>

            <div v-if="diagnosis.intervention_suggestion" class="intervention-box">
              <div class="intervention-header">
                <span class="intervention-icon">💡</span>
                <span class="intervention-label">干预建议</span>
              </div>
              <p class="intervention-text">{{ diagnosis.intervention_suggestion }}</p>
            </div>

            <!-- 干预修复推荐（P0.5 闭环） -->
            <div v-if="diagnosis.recommended_interventions?.length" class="intervention-actions">
              <div class="action-header">
                <span class="action-icon">🛠️</span>
                <span class="action-label">推荐修复方式</span>
              </div>
              <div class="action-buttons">
                <template v-for="(rec, idx) in diagnosis.recommended_interventions" :key="rec.type + '-' + idx">
                  <el-button
                    v-if="rec.type === 'simulation' && rec.id"
                    type="primary"
                    size="default"
                    @click="handleSimulatorClick(rec)"
                    class="intervention-btn"
                  >
                    🎯 进入协议仿真学习
                  </el-button>
                  <el-button
                    v-else
                    :type="idx === 0 ? 'primary' : 'default'"
                    :size="idx === 0 ? 'default' : 'small'"
                    @click="handleInterventionClick(rec)"
                    class="intervention-btn"
                  >
                    {{ rec.label }}
                  </el-button>
                </template>
              </div>
              <p v-if="diagnosis.recommended_interventions[0]?.rationale" class="action-rationale">
                {{ diagnosis.recommended_interventions[0].rationale }}
              </p>
            </div>
          </div>
        </div>
      </div>

      <!-- AI认知修复总览 -->
      <RepairOverview />

      <!-- 双层图谱节点溯源（kp课程节点 + acu认知单元） -->
      <div v-if="diagnosis.knowledge_node_ids?.length || diagnosis.acu_ids?.length" class="graph-nodes-section">
        <div class="graph-nodes-header">
          <span class="graph-icon">🗺️</span>
          <span class="graph-title">知识图谱定位</span>
        </div>
        <div v-if="diagnosis.knowledge_node_ids?.length" class="graph-row">
          <span class="graph-row-label">📚 课程节点</span>
          <div class="graph-tags">
            <el-tag
              v-for="nodeId in diagnosis.knowledge_node_ids"
              :key="nodeId"
              size="small"
              type="primary"
              effect="plain"
              class="node-tag"
              :title="nodeId"
            >
              {{ resolveNodeName(nodeId) }}
            </el-tag>
          </div>
        </div>
        <div v-if="diagnosis.acu_ids?.length" class="graph-row">
          <span class="graph-row-label">🧠 认知单元</span>
          <div class="graph-tags">
            <el-tag
              v-for="acuId in diagnosis.acu_ids"
              :key="acuId"
              size="small"
              type="warning"
              effect="plain"
              class="node-tag"
              :title="acuId"
            >
              {{ resolveNodeName(acuId) }}
            </el-tag>
          </div>
        </div>
      </div>

      <!-- 关联知识点（兜底展示 related_node_ids） -->
      <div v-else-if="diagnosis.related_node_ids?.length" class="related-nodes">
        <span class="related-label">关联知识图谱节点：</span>
        <el-tag
          v-for="nodeId in diagnosis.related_node_ids"
          :key="nodeId"
          size="small"
          effect="plain"
          class="node-tag"
        >
          {{ nodeId }}
        </el-tag>
      </div>

      <!-- AI 自适应误解检验卡片（展示分隔线 + 说明） -->
      <div class="challenger-section">
        <div class="challenger-section-header">
          <span class="challenger-section-icon">⚡</span>
          <span>自适应误解检验</span>
        </div>
        <ChallengerQuizCard />
      </div>
    </template>
  </div>
</template>

<style scoped>
.diagnosis-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 自适应检验区分头 */
.challenger-section {
  margin-top: 4px;
}
.challenger-section-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  color: #6366f1;
  padding: 6px 0 4px;
  border-top: 1px dashed #e0e7ff;
  margin-bottom: 2px;
}
.challenger-section-icon { font-size: 14px; }

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 24px;
  background: linear-gradient(135deg, #f8fafc, #f1f5f9);
  border-radius: 12px;
  border: 1px dashed #cbd5e1;
}
.empty-icon { color: #94a3b8; margin-bottom: 12px; }
.empty-text { font-size: 15px; font-weight: 500; color: #64748b; margin: 0; }
.empty-hint { font-size: 13px; color: #94a3b8; margin: 4px 0 0; }

/* 域外拦截状态 */
.scope-notice-state {
  margin: 4px 0;
  border-radius: 12px;
  border: 1.5px solid #fcd34d;
  background: linear-gradient(135deg, #fffbeb, #fef3c7);
  overflow: hidden;
}
.sn-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px 8px;
  border-bottom: 1px solid #fde68a;
}
.sn-icon { font-size: 20px; flex-shrink: 0; }
.sn-title-block { flex: 1; min-width: 0; }
.sn-title {
  display: block;
  font-size: 13px;
  font-weight: 700;
  color: #92400e;
}
.sn-sub {
  display: block;
  font-size: 10px;
  color: #b45309;
  opacity: 0.8;
}
.sn-badge {
  font-size: 9px;
  font-weight: 700;
  padding: 2px 7px;
  border-radius: 4px;
  background: #f59e0b;
  color: white;
  letter-spacing: 0.5px;
  flex-shrink: 0;
}
.sn-desc {
  font-size: 12px;
  color: #78350f;
  line-height: 1.6;
  margin: 0;
  padding: 8px 12px;
  border-bottom: 1px solid #fde68a;
}
.sn-suggestions {
  padding: 8px 12px 10px;
}
.sn-hint {
  font-size: 11px;
  font-weight: 600;
  color: #92400e;
  display: block;
  margin-bottom: 6px;
}
.sn-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}
.sn-chip {
  font-size: 10px;
  padding: 3px 9px;
  border-radius: 99px;
  background: white;
  color: #d97706;
  border: 1px solid #fcd34d;
  cursor: pointer;
  transition: all 0.18s;
  font-weight: 500;
}
.sn-chip:hover {
  background: #fef3c7;
  border-color: #f59e0b;
  color: #92400e;
}

/* 诺断中状态 */
.diagnosing-state {
  padding: 20px 16px;
  background: linear-gradient(135deg, #f0f9ff, #f8fafc);
  border-radius: 12px;
  border: 1px solid #bae6fd;
}
.diagnosing-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}
.diagnosing-pulse {
  width: 10px; height: 10px;
  border-radius: 50%;
  background: #0ea5e9;
  animation: diag-pulse 1.2s ease-in-out infinite;
  flex-shrink: 0;
}
@keyframes diag-pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.4; transform: scale(0.8); }
}
.diagnosing-title {
  font-size: 14px;
  font-weight: 600;
  color: #0369a1;
}
.diagnosing-steps {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.diag-step {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  color: #64748b;
}
.step-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  background: #e2e8f0;
  flex-shrink: 0;
  transition: background 0.3s;
}
.step-dot.active {
  background: #0ea5e9;
  animation: diag-pulse 1.2s ease-in-out infinite;
}

/* 诊断触发横幅 */
.diagnosis-trigger {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px 16px;
  background: linear-gradient(135deg, #fef3c7, #fef9c3);
  border-radius: 10px;
  border: 1px solid #fcd34d;
}
.trigger-icon { font-size: 20px; flex-shrink: 0; margin-top: 2px; }
.trigger-content { flex: 1; }
.trigger-title { font-size: 13px; font-weight: 600; color: #92400e; }
.trigger-desc { font-size: 13px; color: #78350f; line-height: 1.6; margin: 4px 0 0; }

/* 正确回答横幅 */
.correct-banner {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  background: linear-gradient(135deg, #d1fae5, #ecfdf5);
  border-radius: 10px;
  border: 1px solid #6ee7b7;
}
.correct-icon { font-size: 20px; }
.correct-text { flex: 1; font-size: 14px; font-weight: 500; color: #065f46; }

/* 置信度区域（价表盘 + 历史趋势曲线） */
.confidence-section {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 12px 14px;
}
.conf-section-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 10px;
  font-size: 12px;
}
.conf-section-icon { font-size: 14px; }
.conf-section-title { font-weight: 600; color: #334155; }
.conf-trend-count {
  margin-left: auto;
  font-size: 10px;
  color: #94a3b8;
  background: #f1f5f9;
  padding: 1px 6px;
  border-radius: 8px;
}
/* 次要：AI 诊断精度小标签 */
.diag-accuracy-badge {
  font-size: 10px;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 8px;
  background: rgba(0,0,0,0.04);
  white-space: nowrap;
}
.conf-body {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}
/* 价表盘 */
.conf-gauge {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex-shrink: 0;
  width: 90px;
}
.gauge-svg { width: 90px; height: 52px; }
.gauge-val { font-size: 20px; font-weight: 700; margin-top: -6px; font-family: 'JetBrains Mono', monospace; }
.gauge-lbl { font-size: 10px; color: #64748b; margin-top: 1px; }
/* 右侧：趋势图或图例 */
.conf-right {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.trend-label-row { display: flex; align-items: center; justify-content: space-between; }
.trend-title { font-size: 10px; font-weight: 600; color: #475569; }
.sparkline {
  width: 100%;
  height: 40px;
  display: block;
  border-radius: 4px;
  overflow: visible;
}
.trend-range-row {
  display: flex;
  justify-content: space-between;
  font-size: 10px;
  color: #94a3b8;
  margin-top: 2px;
}
.range-low, .range-high { font-family: 'JetBrains Mono', monospace; }
.range-cur { font-weight: 600; font-size: 10px; }
/* 无趋势时图例 */
.conf-legend {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: #475569;
}
.legend-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
.trend-hint {
  margin: 4px 0 0;
  font-size: 10px;
  color: #94a3b8;
  line-height: 1.4;
}

/* 三层诊断卡片 */
.diagnosis-layers {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.layer-card {
  position: relative;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 16px;
  transition: all 0.2s;
}

.layer-card:not(:last-child) {
  margin-bottom: 8px;
}

.layer-card.is-correct {
  opacity: 0.6;
}

.layer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.layer-badge {
  display: flex;
  align-items: center;
  gap: 8px;
}

.badge-num {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  color: #fff;
}

.layer-badge-1 .badge-num { background: #ef4444; }
.layer-badge-2 .badge-num { background: #f59e0b; }
.layer-badge-3 .badge-num { background: #8b5cf6; }

.badge-text {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
}

.layer-tag {
  font-size: 11px;
  color: #94a3b8;
  font-family: 'JetBrains Mono', monospace;
  letter-spacing: 0.5px;
}

.layer-body { padding: 0; }

/* 递进箭头 */
.layer-arrow {
  display: flex;
  justify-content: center;
  padding-top: 8px;
}

/* 第一层 - 错误展示 */
.error-display {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}
.error-icon { font-size: 28px; flex-shrink: 0; }
.error-info { display: flex; flex-direction: column; gap: 8px; }
.error-type-row {
  display: flex;
  align-items: center;
  gap: 6px;
}
.error-type-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.error-type-label { font-size: 13px; font-weight: 500; color: #334155; }
.error-type-code { font-size: 11px; color: #94a3b8; font-family: 'JetBrains Mono', monospace; }

/* 第二层 - 根因树 */
.root-cause-tree {
  display: flex;
  flex-direction: column;
  gap: 0;
}
.cause-node {
  display: flex;
  align-items: stretch;
  gap: 12px;
  padding: 8px 0;
}
.cause-connector {
  width: 2px;
  background: linear-gradient(to bottom, #f59e0b, #fbbf24);
  margin-left: 10px;
  flex-shrink: 0;
}
.cause-content {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  padding: 8px 12px;
  background: #fffbeb;
  border-radius: 8px;
  border: 1px solid #fde68a;
}
.cause-icon { font-size: 14px; flex-shrink: 0; }
.cause-text { font-size: 13px; color: #78350f; line-height: 1.5; }
.no-cause {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  color: #94a3b8;
  font-size: 13px;
}
.no-cause-icon { font-size: 16px; }
.missing-prereqs {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid #f1f5f9;
}
.prereqs-label { font-size: 12px; color: #64748b; }
.prereq-tag { margin: 2px; }

/* 第三层 - 模式匹配 */
.pattern-display { margin-bottom: 12px; }
.pattern-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: linear-gradient(135deg, #ede9fe, #f3e8ff);
  border-radius: 10px;
  border: 1px solid #c4b5fd;
  cursor: help;
  transition: all 0.2s;
}
.pattern-badge:hover {
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.15);
  transform: translateY(-1px);
}
.pattern-icon { font-size: 18px; }
.pattern-name { font-size: 14px; font-weight: 600; color: #5b21b6; }
.pattern-help { font-size: 14px; color: #8b5cf6; }
.no-pattern {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #94a3b8;
}

.intervention-box {
  padding: 12px;
  background: #f0fdf4;
  border-radius: 8px;
  border: 1px solid #bbf7d0;
}
.intervention-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
}
.intervention-icon { font-size: 14px; }
.intervention-label { font-size: 12px; font-weight: 600; color: #166534; }
.intervention-text { font-size: 13px; color: #15803d; line-height: 1.6; margin: 0; }

/* 关联知识点 */
.related-nodes {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  padding: 12px 16px;
  background: #f8fafc;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
}
.related-label { font-size: 12px; color: #64748b; }
.node-tag { margin: 2px; }

/* 双层图谱节点溯源 */
.graph-nodes-section {
  padding: 12px 16px;
  background: linear-gradient(135deg, #f0f9ff, #f8fafc);
  border-radius: 10px;
  border: 1px solid #bae6fd;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.graph-nodes-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 2px;
}
.graph-icon { font-size: 14px; }
.graph-title { font-size: 13px; font-weight: 600; color: #0369a1; }
.graph-row {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  flex-wrap: wrap;
}
.graph-row-label { font-size: 12px; color: #475569; min-width: 72px; padding-top: 2px; flex-shrink: 0; }
.graph-tags { display: flex; flex-wrap: wrap; gap: 4px; }

/* 干预推荐卡片 */
.intervention-actions {
  margin-top: 12px;
  padding: 12px;
  background: linear-gradient(135deg, #f0f9ff 0%, #e8f4fd 100%);
  border-radius: 8px;
  border: 1px solid #b3d8fd;
}

.action-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 10px;
  font-weight: 600;
  color: #1a56db;
}

.action-icon {
  font-size: 16px;
}

.action-label {
  font-size: 14px;
}

.action-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.intervention-btn {
  border-radius: 6px;
}

.action-rationale {
  margin-top: 8px;
  font-size: 12px;
  color: #6b7280;
  line-height: 1.4;
}

/* 响应式 */
@media (max-width: 640px) {
  .confidence-dashboard { flex-direction: column; align-items: stretch; }
  .confidence-gauge { align-self: center; }
}
</style>
