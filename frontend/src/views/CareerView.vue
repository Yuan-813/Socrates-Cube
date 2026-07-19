<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '@/stores/userStore'
import axios from 'axios'

const userStore = useUserStore()

// 主 Tab
type CareerTab = 'gap' | 'resume' | 'interview'
const activeTab = ref<CareerTab>('gap')

interface Job {
  job_id: string
  name: string
  description: string
  avg_salary: string
  key_skills: string[]
  recommended_cert: string | null
}

interface GapItem {
  node_id: string
  node_name: string
  node_type: string
  current_mastery: number
  required_mastery: number
  gap: number
  priority: string
}

interface GapReport {
  job_id: string
  job_name: string
  gap_score: number
  gap_level: string
  estimated_weeks: number
  total_gaps: number
  priority_skills: GapItem[]
  all_gaps: GapItem[]
  recommended_cert: string | null
  current_strengths: GapItem[]
}

interface CareerPath {
  gap_summary: {
    job_name: string
    gap_score: number
    gap_level: string
    estimated_weeks: number
  }
  path: {
    nodes: Array<{
      node_id: string
      node_name: string
      status: string
      current_mastery: number
      recommendation_reason: string
    }>
    total_estimated_time: number
  }
}

const jobs = ref<Job[]>([])
const selectedJobId = ref('')
const gapReport = ref<GapReport | null>(null)
const careerPath = ref<CareerPath | null>(null)
const isAnalyzing = ref(false)
const isGeneratingPath = ref(false)
const error = ref('')

const selectedJob = computed(() => jobs.value.find(j => j.job_id === selectedJobId.value))

const gapScorePercent = computed(() => {
  if (!gapReport.value) return 0
  return Math.round(gapReport.value.gap_score * 100)
})

const gapColor = computed(() => {
  const score = gapReport.value?.gap_score ?? 0
  if (score >= 0.8) return '#22c55e'
  if (score >= 0.6) return '#f59e0b'
  if (score >= 0.4) return '#f97316'
  return '#ef4444'
})

const priorityColors: Record<string, string> = {
  high: '#fee2e2',
  medium: '#fef9c3',
  low: '#dcfce7',
}
const priorityTextColors: Record<string, string> = {
  high: '#dc2626',
  medium: '#ca8a04',
  low: '#16a34a',
}

async function loadJobs() {
  try {
    const res = await axios.get('/api/v1/career/jobs')
    jobs.value = res.data.jobs || []
  } catch (e) {
    error.value = '加载岗位列表失败'
  }
}

async function runGapAnalysis() {
  if (!selectedJobId.value || isAnalyzing.value) return
  isAnalyzing.value = true
  error.value = ''
  gapReport.value = null
  careerPath.value = null
  try {
    const res = await axios.post('/api/v1/career/gap-analysis', {
      user_id: userStore.userId,
      target_job_id: selectedJobId.value,
    })
    gapReport.value = res.data
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'GAP分析失败'
  } finally {
    isAnalyzing.value = false
  }
}

async function generateCareerPath() {
  if (!selectedJobId.value || isGeneratingPath.value) return
  isGeneratingPath.value = true
  error.value = ''
  try {
    const res = await axios.post('/api/v1/career/path', {
      user_id: userStore.userId,
      target_job_id: selectedJobId.value,
    })
    careerPath.value = res.data
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '路径生成失败'
  } finally {
    isGeneratingPath.value = false
  }
}

function selectJob(jobId: string) {
  selectedJobId.value = jobId
  gapReport.value = null
  careerPath.value = null
}

onMounted(() => {
  loadJobs()
})

// ===== 简历生成 Tab =====
const resumeJobDesc = ref('')
const resumeGenerating = ref(false)
const resumeContent = ref('')
const resumeError = ref('')
const resumeExporting = ref(false)

async function generateResume() {
  if (resumeGenerating.value) return
  resumeGenerating.value = true
  resumeError.value = ''
  resumeContent.value = ''
  try {
    const res = await axios.post('/api/v1/career/generate-resume', {
      user_id: userStore.userId,
      job_description: resumeJobDesc.value,
    })
    resumeContent.value = res.data.resume_markdown || res.data.content || ''
  } catch (e: unknown) {
    resumeError.value = e instanceof Error ? e.message : '简历生成失败'
  } finally {
    resumeGenerating.value = false
  }
}

async function optimizeResume() {
  if (!resumeContent.value.trim() || resumeGenerating.value) return
  resumeGenerating.value = true
  resumeError.value = ''
  try {
    const res = await axios.post('/api/v1/career/optimize-resume', {
      user_id: userStore.userId,
      resume_text: resumeContent.value,
      job_description: resumeJobDesc.value,
    })
    resumeContent.value = res.data.optimized_resume || res.data.content || resumeContent.value
  } catch (e: unknown) {
    resumeError.value = e instanceof Error ? e.message : '优化失败'
  } finally {
    resumeGenerating.value = false
  }
}

async function exportResume() {
  if (!resumeContent.value.trim() || resumeExporting.value) return
  resumeExporting.value = true
  try {
    const res = await fetch('/api/v1/export/markdown', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: '个人简历', content: resumeContent.value, format: 'docx' }),
    })
    if (!res.ok) throw new Error('导出失败')
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `简历_${userStore.username || 'user'}.docx`
    a.click()
    URL.revokeObjectURL(url)
  } catch (e: unknown) {
    resumeError.value = e instanceof Error ? e.message : '导出失败'
  } finally {
    resumeExporting.value = false
  }
}

// ===== 模拟面试 Tab =====
const interviewJobType = ref('network_engineer')
const interviewQuestions = ref<Array<{ question: string; type: string; hint?: string }>>([])
const interviewAnswers = ref<Record<number, string>>({})
const interviewLoading = ref(false)
const interviewSubmitting = ref(false)
const interviewReport = ref<{
  total_score: number
  professional_score: number
  expression_score: number
  logic_score: number
  feedback: string
  dimension_feedback: Record<string, string>
} | null>(null)
const interviewError = ref('')

const interviewJobTypes = [
  { value: 'network_engineer', label: '网络工程师' },
  { value: 'cloud_engineer', label: '云计算工程师' },
  { value: 'security_engineer', label: '网络安全工程师' },
  { value: 'architect', label: '网络架构师' },
]

async function loadInterviewQuestions() {
  if (interviewLoading.value) return
  interviewLoading.value = true
  interviewError.value = ''
  interviewQuestions.value = []
  interviewAnswers.value = {}
  interviewReport.value = null
  try {
    const res = await axios.post('/api/v1/career/mock-interview', {
      user_id: userStore.userId,
      job_title: interviewJobType.value,
      question_count: 5,
    })
    interviewQuestions.value = res.data.questions || []
  } catch (e: unknown) {
    interviewError.value = e instanceof Error ? e.message : '题目加载失败'
  } finally {
    interviewLoading.value = false
  }
}

async function submitInterview() {
  if (interviewSubmitting.value || !interviewQuestions.value.length) return
  interviewSubmitting.value = true
  interviewError.value = ''
  try {
    const res = await axios.post('/api/v1/career/interview-report', {
      user_id: userStore.userId,
      job_title: interviewJobType.value,
      questions: interviewQuestions.value.map(q => ({ question: q.question, type: q.type || 'technical' })),
      answers: interviewQuestions.value.map((_, i) => interviewAnswers.value[i] || ''),
    })
    interviewReport.value = res.data.report || res.data
  } catch (e: unknown) {
    interviewError.value = e instanceof Error ? e.message : '评分失败'
  } finally {
    interviewSubmitting.value = false
  }
}

const scoreColor = computed(() => {
  const s = interviewReport.value?.total_score ?? 0
  if (s >= 80) return '#22c55e'
  if (s >= 60) return '#f59e0b'
  return '#ef4444'
})
</script>

<template>
  <div class="space-y-5">
    <!-- 页面标题 -->
    <div class="card">
      <h2 class="section-title">职业成长导航</h2>
      <p class="section-desc">职业投射、简历生成、模拟面试三大模块助你冲刺目标岗位</p>
    </div>

    <!-- 主 Tab 切换 -->
    <div class="career-tabs">
      <button class="career-tab" :class="{ active: activeTab === 'gap' }" @click="activeTab = 'gap'">
        📊 技能差距分析
      </button>
      <button class="career-tab" :class="{ active: activeTab === 'resume' }" @click="activeTab = 'resume'">
        📋 简历生成
      </button>
      <button class="career-tab" :class="{ active: activeTab === 'interview' }" @click="activeTab = 'interview'">
        🎤 模拟面试
      </button>
    </div>

    <!-- 技能差距分析 Tab -->
    <template v-if="activeTab === 'gap'">
    <div class="card">
      <h3 class="card-title">选择目标岗位</h3>
      <div class="jobs-grid">
        <button
          v-for="job in jobs"
          :key="job.job_id"
          class="job-card"
          :class="{ selected: selectedJobId === job.job_id }"
          @click="selectJob(job.job_id)"
        >
          <div class="job-header">
            <span class="job-name">{{ job.name }}</span>
            <span class="job-salary">{{ job.avg_salary }}</span>
          </div>
          <p class="job-desc">{{ job.description }}</p>
          <div class="job-skills">
            <span v-for="skill in job.key_skills.slice(0, 3)" :key="skill" class="skill-tag">
              {{ skill }}
            </span>
          </div>
        </button>
      </div>

      <button
        v-if="selectedJobId"
        class="btn-analyze"
        :disabled="isAnalyzing"
        @click="runGapAnalysis"
      >
        <svg v-if="isAnalyzing" class="spin w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path d="M12 2a10 10 0 0 1 10 10" stroke-width="2"/>
        </svg>
        {{ isAnalyzing ? '分析中...' : `分析与「${selectedJob?.name}」的技能差距` }}
      </button>
    </div>

    <!-- 错误提示 -->
    <div v-if="error" class="card bg-red-50 border-red-200">
      <p class="text-sm text-red-600">{{ error }}</p>
    </div>

    <!-- GAP 分析结果 -->
    <div v-if="gapReport" class="card">
      <h3 class="card-title">技能差距分析报告</h3>

      <!-- GAP 评分仪表盘 -->
      <div class="gap-dashboard">
        <div class="gap-score-ring">
          <svg width="120" height="120" viewBox="0 0 120 120">
            <circle cx="60" cy="60" r="50" fill="none" stroke="#e2e8f0" stroke-width="12"/>
            <circle
              cx="60" cy="60" r="50" fill="none"
              :stroke="gapColor" stroke-width="12"
              stroke-linecap="round"
              stroke-dasharray="314.16"
              :stroke-dashoffset="314.16 * (1 - gapReport.gap_score)"
              transform="rotate(-90 60 60)"
              style="transition: stroke-dashoffset 0.8s ease"
            />
          </svg>
          <div class="gap-score-center">
            <span class="gap-score-num" :style="{ color: gapColor }">{{ gapScorePercent }}%</span>
            <span class="gap-score-label">匹配度</span>
          </div>
        </div>
        <div class="gap-info">
          <h4 class="gap-title">{{ gapReport.job_name }}</h4>
          <p class="gap-level">{{ gapReport.gap_level }}</p>
          <div class="gap-stats">
            <div class="gap-stat">
              <span class="stat-num">{{ gapReport.estimated_weeks }}</span>
              <span class="stat-label">预计周数</span>
            </div>
            <div class="gap-stat">
              <span class="stat-num">{{ gapReport.total_gaps }}</span>
              <span class="stat-label">待补强技能</span>
            </div>
            <div class="gap-stat">
              <span class="stat-num">{{ gapReport.current_strengths.length }}</span>
              <span class="stat-label">已掌握技能</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 优先补强技能 -->
      <div v-if="gapReport.priority_skills.length" class="mt-4">
        <h4 class="text-sm font-semibold text-gray-700 mb-2">重点补强技能（按差距优先级）</h4>
        <div class="space-y-2">
          <div
            v-for="item in gapReport.priority_skills"
            :key="item.node_id"
            class="skill-gap-row"
          >
            <div class="skill-info">
              <span class="skill-name">{{ item.node_name }}</span>
              <span
                class="priority-badge"
                :style="{
                  background: priorityColors[item.priority],
                  color: priorityTextColors[item.priority]
                }"
              >
                {{ item.priority === 'high' ? '高优先' : item.priority === 'medium' ? '中优先' : '低优先' }}
              </span>
            </div>
            <div class="mastery-bar">
              <div class="mastery-fill" :style="{ width: `${item.current_mastery * 100}%` }"></div>
              <div class="mastery-target" :style="{ left: `${item.required_mastery * 100}%` }"></div>
            </div>
            <div class="mastery-text">
              {{ Math.round(item.current_mastery * 100) }}% / {{ Math.round(item.required_mastery * 100) }}%
            </div>
          </div>
        </div>
      </div>

      <!-- 已有优势 -->
      <div v-if="gapReport.current_strengths.length" class="mt-4">
        <h4 class="text-sm font-semibold text-gray-700 mb-2">已掌握优势技能</h4>
        <div class="flex flex-wrap gap-2">
          <span
            v-for="s in gapReport.current_strengths"
            :key="s.node_id"
            class="strength-tag"
          >
            ✓ {{ s.node_name }}
          </span>
        </div>
      </div>

      <!-- 生成路径按钮 -->
      <button
        class="btn-path mt-4"
        :disabled="isGeneratingPath"
        @click="generateCareerPath"
      >
        <svg v-if="isGeneratingPath" class="spin w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path d="M12 2a10 10 0 0 1 10 10" stroke-width="2"/>
        </svg>
        {{ isGeneratingPath ? '生成中...' : '生成职业学习路径' }}
      </button>
    </div>

    <!-- 学习路径 -->
    <div v-if="careerPath" class="card">
      <h3 class="card-title">职业导向学习路径</h3>
      <div class="path-meta">
        <span>目标岗位：{{ careerPath.gap_summary.job_name }}</span>
        <span>预计 {{ careerPath.gap_summary.estimated_weeks }} 周完成</span>
        <span>共 {{ careerPath.path.nodes.length }} 个节点</span>
      </div>
      <div class="path-nodes">
        <div
          v-for="(node, idx) in careerPath.path.nodes"
          :key="node.node_id"
          class="path-node"
          :class="node.status"
        >
          <div class="node-seq">{{ idx + 1 }}</div>
          <div class="node-body">
            <span class="node-name">{{ node.node_name }}</span>
            <span class="node-status-badge">
              {{ node.status === 'completed' ? '已完成' : node.status === 'in_progress' ? '进行中' : '待学习' }}
            </span>
            <p class="node-reason">{{ node.recommendation_reason }}</p>
          </div>
          <div class="node-mastery">
            {{ Math.round(node.current_mastery * 100) }}%
          </div>
        </div>
      </div>
    </div>
    </template><!-- /gap tab -->

    <!-- 简历生成 Tab -->
    <template v-if="activeTab === 'resume'">
      <div class="card">
        <h3 class="card-title">📋 AI 简历生成</h3>
        <p class="text-xs text-gray-500 mb-4">基于你的学习画像和目标岗位，AI 自动生成专业简历</p>
        <div class="mb-3">
          <label class="text-xs font-medium text-gray-600">投递岗位描述（可选）</label>
          <textarea v-model="resumeJobDesc" rows="2" class="resume-textarea" placeholder="如：网络工程师，负责路由交换配置和网络排障"></textarea>
        </div>
        <div class="flex gap-2 mb-4">
          <button class="career-action-btn" :disabled="resumeGenerating" @click="generateResume">
            <svg v-if="resumeGenerating" class="spin w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path d="M12 2a10 10 0 0 1 10 10" stroke-width="2"/></svg>
            {{ resumeGenerating ? '生成中...' : '生成简历' }}
          </button>
          <button v-if="resumeContent" class="career-action-btn career-action-btn--outline" :disabled="resumeGenerating" @click="optimizeResume">
            一键优化
          </button>
          <button v-if="resumeContent" class="career-action-btn career-action-btn--green" :disabled="resumeExporting" @click="exportResume">
            导出 Word
          </button>
        </div>
        <div v-if="resumeError" class="text-sm text-red-600 mb-3">{{ resumeError }}</div>
        <div v-if="resumeContent" class="resume-preview">{{ resumeContent }}</div>
      </div>
    </template>

    <!-- 模拟面试 Tab -->
    <template v-if="activeTab === 'interview'">
      <div class="card">
        <h3 class="card-title">🎤 模拟面试</h3>
        <div class="flex flex-wrap gap-2 mb-4">
          <button
            v-for="jt in interviewJobTypes" :key="jt.value"
            class="interview-job-btn"
            :class="{ active: interviewJobType === jt.value }"
            @click="interviewJobType = jt.value"
          >{{ jt.label }}</button>
        </div>
        <button class="career-action-btn" :disabled="interviewLoading" @click="loadInterviewQuestions">
          <svg v-if="interviewLoading" class="spin w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path d="M12 2a10 10 0 0 1 10 10" stroke-width="2"/></svg>
          {{ interviewLoading ? '加载中...' : '开始面试' }}
        </button>
        <div v-if="interviewError" class="text-sm text-red-600 mt-2">{{ interviewError }}</div>
        <!-- 题目列表 -->
        <div v-if="interviewQuestions.length" class="mt-4 space-y-4">
          <div v-for="(q, i) in interviewQuestions" :key="i" class="interview-question">
            <p class="text-sm font-semibold text-gray-800 mb-2">Q{{ i + 1 }}. {{ q.question }}</p>
            <p v-if="q.hint" class="text-xs text-gray-500 mb-2">💡 提示: {{ q.hint }}</p>
            <textarea
              v-model="interviewAnswers[i]"
              class="resume-textarea"
              rows="3"
              :placeholder="`请回答第 ${i + 1} 题...`"
            ></textarea>
          </div>
          <button class="career-action-btn" :disabled="interviewSubmitting" @click="submitInterview">
            <svg v-if="interviewSubmitting" class="spin w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path d="M12 2a10 10 0 0 1 10 10" stroke-width="2"/></svg>
            {{ interviewSubmitting ? '评分中...' : '提交面试答题' }}
          </button>
        </div>
        <!-- 面试报告 -->
        <div v-if="interviewReport" class="mt-4 p-4 bg-gray-50 rounded-xl">
          <h4 class="font-semibold text-gray-800 mb-3">📊 面试评分报告</h4>
          <div class="flex gap-6 mb-4">
            <div class="text-center">
              <div class="text-3xl font-bold" :style="{ color: scoreColor }">{{ interviewReport.total_score }}</div>
              <div class="text-xs text-gray-500">综合得分</div>
            </div>
            <div class="text-center">
              <div class="text-xl font-bold text-indigo-600">{{ interviewReport.professional_score }}</div>
              <div class="text-xs text-gray-500">专业性</div>
            </div>
            <div class="text-center">
              <div class="text-xl font-bold text-emerald-600">{{ interviewReport.expression_score }}</div>
              <div class="text-xs text-gray-500">语言表达</div>
            </div>
            <div class="text-center">
              <div class="text-xl font-bold text-amber-600">{{ interviewReport.logic_score }}</div>
              <div class="text-xs text-gray-500">逻辑思维</div>
            </div>
          </div>
          <p class="text-sm text-gray-700">{{ interviewReport.feedback }}</p>
        </div>
      </div>
    </template>

  </div>
</template>

<style scoped>
.card-title {
  font-size: 15px;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 14px;
}
.jobs-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}
.job-card {
  padding: 14px;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  cursor: pointer;
  text-align: left;
  transition: all 0.18s;
  background: white;
}
.job-card:hover { border-color: #a5b4fc; background: #f5f3ff; }
.job-card.selected { border-color: #6366f1; background: #eef2ff; }
.job-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.job-name { font-size: 14px; font-weight: 700; color: #1e293b; }
.job-salary { font-size: 11px; color: #6366f1; font-weight: 600; }
.job-desc { font-size: 12px; color: #64748b; margin-bottom: 8px; }
.job-skills { display: flex; flex-wrap: wrap; gap: 4px; }
.skill-tag { font-size: 10px; background: #f1f5f9; color: #475569; padding: 2px 6px; border-radius: 4px; }
.btn-analyze {
  width: 100%; padding: 11px; background: #6366f1; color: white;
  border: none; border-radius: 10px; font-size: 14px; font-weight: 600;
  cursor: pointer; transition: all 0.18s;
  display: flex; align-items: center; justify-content: center; gap: 6px;
}
.btn-analyze:hover:not(:disabled) { background: #4f46e5; }
.btn-analyze:disabled { opacity: 0.5; cursor: not-allowed; }
.gap-dashboard { display: flex; gap: 24px; align-items: center; }
.gap-score-ring { position: relative; width: 120px; height: 120px; flex-shrink: 0; }
.gap-score-center { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; }
.gap-score-num { font-size: 22px; font-weight: 800; }
.gap-score-label { font-size: 11px; color: #94a3b8; }
.gap-info { flex: 1; }
.gap-title { font-size: 16px; font-weight: 700; color: #1e293b; margin-bottom: 4px; }
.gap-level { font-size: 12px; color: #64748b; margin-bottom: 12px; }
.gap-stats { display: flex; gap: 16px; }
.gap-stat { display: flex; flex-direction: column; align-items: center; }
.stat-num { font-size: 20px; font-weight: 700; color: #6366f1; }
.stat-label { font-size: 11px; color: #94a3b8; }
.skill-gap-row { display: flex; align-items: center; gap: 10px; padding: 6px 0; border-bottom: 1px solid #f1f5f9; }
.skill-info { display: flex; align-items: center; gap: 6px; min-width: 180px; }
.skill-name { font-size: 12px; font-weight: 500; color: #374151; }
.priority-badge { font-size: 10px; padding: 1px 6px; border-radius: 4px; font-weight: 600; }
.mastery-bar { flex: 1; height: 8px; background: #e2e8f0; border-radius: 4px; position: relative; overflow: visible; }
.mastery-fill { height: 100%; background: #6366f1; border-radius: 4px; transition: width 0.5s; }
.mastery-target { position: absolute; top: -3px; width: 2px; height: 14px; background: #ef4444; border-radius: 1px; }
.mastery-text { font-size: 11px; color: #94a3b8; white-space: nowrap; min-width: 72px; text-align: right; }
.strength-tag { font-size: 11px; background: #dcfce7; color: #16a34a; padding: 3px 10px; border-radius: 20px; font-weight: 500; }
.btn-path {
  width: 100%; padding: 11px; background: linear-gradient(135deg, #10b981, #059669);
  color: white; border: none; border-radius: 10px; font-size: 14px; font-weight: 600;
  cursor: pointer; transition: all 0.18s;
  display: flex; align-items: center; justify-content: center; gap: 6px;
}
.btn-path:hover:not(:disabled) { opacity: 0.9; transform: translateY(-1px); }
.btn-path:disabled { opacity: 0.5; cursor: not-allowed; }
.path-meta { display: flex; gap: 16px; font-size: 12px; color: #64748b; margin-bottom: 14px; flex-wrap: wrap; }
.path-nodes { display: flex; flex-direction: column; gap: 8px; }
.path-node { display: flex; align-items: flex-start; gap: 12px; padding: 10px 12px; border: 1px solid #e2e8f0; border-radius: 10px; }
.path-node.completed { border-color: #bbf7d0; background: #f0fdf4; }
.path-node.in_progress { border-color: #bfdbfe; background: #eff6ff; }
.node-seq { width: 26px; height: 26px; border-radius: 50%; background: #6366f1; color: white; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; flex-shrink: 0; }
.node-body { flex: 1; }
.node-name { font-size: 13px; font-weight: 600; color: #1e293b; margin-right: 8px; }
.node-status-badge { font-size: 10px; padding: 1px 6px; border-radius: 4px; background: #e0e7ff; color: #4338ca; }
.node-reason { font-size: 11px; color: #64748b; margin-top: 3px; }
.node-mastery { font-size: 12px; font-weight: 600; color: #6366f1; white-space: nowrap; }
.spin { animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* 主 Tab */
.career-tabs {
  display: flex; gap: 4px; background: #f1f5f9;
  border-radius: 12px; padding: 4px;
}
.career-tab {
  flex: 1; padding: 9px 12px; border: none; border-radius: 9px;
  font-size: 13px; font-weight: 600; color: #64748b;
  background: none; cursor: pointer; transition: all 0.18s;
}
.career-tab.active { background: white; color: #4f46e5; box-shadow: 0 1px 4px rgba(0,0,0,0.1); }

/* 简历/面试 */
.resume-textarea {
  width: 100%; padding: 10px 12px; border: 1px solid #e2e8f0;
  border-radius: 8px; font-size: 13px; resize: vertical; outline: none;
  font-family: inherit;
}
.resume-textarea:focus { border-color: #6366f1; }
.resume-preview {
  background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px;
  padding: 16px; font-size: 12px; white-space: pre-wrap; font-family: monospace;
  max-height: 400px; overflow-y: auto; line-height: 1.7;
}
.career-action-btn {
  padding: 9px 18px; background: #6366f1; color: white;
  border: none; border-radius: 9px; font-size: 13px; font-weight: 600;
  cursor: pointer; transition: all 0.18s;
  display: inline-flex; align-items: center; gap: 6px;
}
.career-action-btn:hover:not(:disabled) { background: #4f46e5; }
.career-action-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.career-action-btn--outline {
  background: white; color: #6366f1; border: 2px solid #6366f1;
}
.career-action-btn--outline:hover:not(:disabled) { background: #eef2ff; }
.career-action-btn--green { background: #10b981; }
.career-action-btn--green:hover:not(:disabled) { background: #059669; }
.interview-job-btn {
  padding: 6px 14px; background: #f1f5f9; color: #475569;
  border: 2px solid transparent; border-radius: 8px;
  font-size: 12px; font-weight: 600; cursor: pointer; transition: all 0.15s;
}
.interview-job-btn.active { background: #eef2ff; color: #4f46e5; border-color: #6366f1; }
.interview-question {
  padding: 14px; background: #f8fafc; border-radius: 10px;
  border: 1px solid #e2e8f0;
}
</style>
