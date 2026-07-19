<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useUserStore } from '@/stores/userStore'
import { ElMessage } from 'element-plus'

const userStore = useUserStore()
const userId = computed(() => userStore.profile?.userId || 'student-001')

// ── 页面阶段 ──────────────────────────────────────────────
type Phase = 'select' | 'exam' | 'result'
const phase = ref<Phase>('select')

// ── 考试列表 ──────────────────────────────────────────────
interface ExamInfo {
  exam_id: string
  name: string
  description: string
  question_count: number
  time_limit_minutes: number
  pass_score: number
  cert_node_id: string | null
}
const examList = ref<ExamInfo[]>([])
const loadingList = ref(false)

async function loadExamList() {
  loadingList.value = true
  try {
    const res = await fetch('/api/v1/exam/list')
    const data = await res.json()
    examList.value = data.exams || []
  } catch {
    examList.value = []
  } finally {
    loadingList.value = false
  }
}

// ── 答题状态 ──────────────────────────────────────────────
interface Question {
  index: number
  id: string
  type: string
  question: string
  options: Record<string, string>
  knowledge_point: string
}
const sessionId = ref('')
const currentExam = ref<ExamInfo | null>(null)
const questions = ref<Question[]>([])
const answers = ref<Record<string, string>>({})
const currentIndex = ref(0)
const isStarting = ref(false)
const isSubmitting = ref(false)

// 倒计时
const timeLeft = ref(0)
let timerHandle: ReturnType<typeof setInterval> | null = null

function startTimer(minutes: number) {
  timeLeft.value = minutes * 60
  timerHandle = setInterval(() => {
    if (timeLeft.value > 0) {
      timeLeft.value--
    } else {
      handleSubmit()
    }
  }, 1000)
}

function stopTimer() {
  if (timerHandle) {
    clearInterval(timerHandle)
    timerHandle = null
  }
}

const timeDisplay = computed(() => {
  const m = Math.floor(timeLeft.value / 60)
  const s = timeLeft.value % 60
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
})

const timeUrgent = computed(() => timeLeft.value < 300) // 5分钟警告

// ── 开始考试 ──────────────────────────────────────────────
async function startExam(exam: ExamInfo) {
  isStarting.value = true
  try {
    const res = await fetch('/api/v1/exam/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: userId.value,
        exam_id: exam.exam_id,
        question_count: 20,
        weak_kp_ids: userStore.profile?.weak_points || [],
      }),
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || '开始失败')
    sessionId.value = data.session_id
    currentExam.value = exam
    questions.value = data.questions
    answers.value = {}
    currentIndex.value = 0
    phase.value = 'exam'
    startTimer(exam.time_limit_minutes)
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '开始考试失败')
  } finally {
    isStarting.value = false
  }
}

// ── 切换题目 ──────────────────────────────────────────────
const currentQ = computed(() => questions.value[currentIndex.value])
const progressPct = computed(() =>
  questions.value.length ? (Object.keys(answers.value).length / questions.value.length) * 100 : 0
)

function selectAnswer(qid: string, option: string) {
  const q = questions.value.find(q => q.id === qid)
  if (!q) return
  if (q.type === 'multi') {
    // 多选：切换选项
    const cur = (answers.value[qid] || '').split('').filter(Boolean)
    const idx = cur.indexOf(option)
    if (idx >= 0) cur.splice(idx, 1)
    else cur.push(option)
    answers.value = { ...answers.value, [qid]: cur.sort().join('') }
  } else {
    answers.value = { ...answers.value, [qid]: option }
  }
}

function isSelected(qid: string, option: string): boolean {
  return (answers.value[qid] || '').includes(option)
}

// ── 结果 ──────────────────────────────────────────────────
interface WrongItem {
  question_id: string
  question: string
  user_answer: string
  correct_answer: string
  explanation: string
  knowledge_point: string
}
interface ExamResult {
  exam_name: string
  total_questions: number
  correct_count: number
  score: number
  passed: boolean
  pass_score: number
  wrong_count: number
  weak_kp_ids: string[]
  wrong_items: WrongItem[]
  grade: string
}
const result = ref<ExamResult | null>(null)
const showAllWrong = ref(false)

async function handleSubmit() {
  if (isSubmitting.value) return
  stopTimer()
  isSubmitting.value = true
  try {
    const res = await fetch(`/api/v1/exam/submit/${sessionId.value}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ answers: answers.value }),
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || '提交失败')
    result.value = data
    phase.value = 'result'
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '提交失败')
  } finally {
    isSubmitting.value = false
  }
}

function restart() {
  phase.value = 'select'
  result.value = null
  sessionId.value = ''
}

// ── 生命周期 ──────────────────────────────────────────────
onMounted(loadExamList)
onUnmounted(stopTimer)

// 考试列表图标
const examIcons: Record<string, string> = {
  hcia_mock: '🏅',
  ccna_mock: '🔵',
  computer_network_exam: '📚',
  hcip_mock: '🥇',
}
const examColors: Record<string, string> = {
  hcia_mock: 'from-red-500 to-orange-500',
  ccna_mock: 'from-blue-500 to-cyan-500',
  computer_network_exam: 'from-indigo-500 to-purple-500',
  hcip_mock: 'from-yellow-500 to-amber-600',
}

// 题目数量选择
const questionCountOptions = [10, 15, 20, 25, 30]
const selectedQuestionCount = ref(20)

async function startExamWithCount(exam: ExamInfo) {
  const maxQ = exam.question_count || 20
  const qCount = Math.min(selectedQuestionCount.value, maxQ)
  isStarting.value = true
  try {
    const res = await fetch('/api/v1/exam/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: userId.value,
        exam_id: exam.exam_id,
        question_count: qCount,
        weak_kp_ids: userStore.profile?.weak_points || [],
      }),
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || '开始失败')
    sessionId.value = data.session_id
    currentExam.value = exam
    questions.value = data.questions
    answers.value = {}
    currentIndex.value = 0
    phase.value = 'exam'
    startTimer(exam.time_limit_minutes)
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '开始考试失败')
  } finally {
    isStarting.value = false
  }
}
</script>

<template>
  <div class="space-y-5">

    <!-- ══ 选择考试 ══════════════════════════════════════════ -->
    <template v-if="phase === 'select'">
      <div class="card">
        <h2 class="section-title">证书模拟考试</h2>
        <p class="section-desc">选择考试方向，系统将根据你的薄弱点智能抽题，完成后生成成绩报告与错题诊断</p>
        <!-- 题目数量选择 -->
        <div class="mt-3 flex items-center gap-3 flex-wrap">
          <span class="text-xs text-gray-500">题目数量：</span>
          <div class="flex gap-1.5">
            <button
              v-for="n in questionCountOptions"
              :key="n"
              class="px-3 py-1 text-xs rounded-lg border transition-all"
              :class="selectedQuestionCount === n ? 'border-indigo-500 bg-indigo-50 text-indigo-700 font-semibold' : 'border-gray-200 text-gray-500 hover:border-indigo-300'"
              @click="selectedQuestionCount = n"
            >
              {{ n }}题
            </button>
          </div>
          <span class="text-xs text-gray-400">（系统按薄弱点加权抽题）</span>
        </div>
      </div>

      <div v-if="loadingList" class="text-center py-12 text-gray-400">
        <svg class="w-6 h-6 animate-spin mx-auto mb-2" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
        </svg>
        加载考试列表...
      </div>

      <div v-else class="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div
          v-for="exam in examList"
          :key="exam.exam_id"
          class="rounded-2xl overflow-hidden shadow-sm border border-gray-100 hover:shadow-md transition-all cursor-pointer group"
          @click="startExamWithCount(exam)"
        >
          <!-- 渐变头部 -->
          <div :class="`bg-gradient-to-br ${examColors[exam.exam_id] || 'from-gray-500 to-gray-700'} p-6 text-white`">
            <div class="text-4xl mb-2">{{ examIcons[exam.exam_id] || '📝' }}</div>
            <h3 class="font-bold text-lg leading-tight">{{ exam.name }}</h3>
          </div>
          <!-- 详情 -->
          <div class="bg-white p-4 space-y-3">
            <p class="text-xs text-gray-500 leading-relaxed">{{ exam.description }}</p>
            <div class="flex justify-between text-xs text-gray-600">
              <span>📊 题目数量：{{ exam.question_count }}</span>
              <span>⏱ {{ exam.time_limit_minutes }}分钟</span>
            </div>
            <div class="flex justify-between text-xs text-gray-600">
              <span>🎯 及格线：{{ exam.pass_score }}分</span>
              <span v-if="exam.cert_node_id" class="text-indigo-500">📜 官方认证方向</span>
            </div>
            <button
              :disabled="isStarting"
              class="w-full py-2 text-sm font-semibold rounded-xl text-white transition-all"
              :class="`bg-gradient-to-r ${examColors[exam.exam_id] || 'from-gray-500 to-gray-700'} group-hover:opacity-90`"
            >
              {{ isStarting ? '准备中...' : '开始模拟考试 →' }}
            </button>
          </div>
        </div>
      </div>
    </template>

    <!-- ══ 答题区 ══════════════════════════════════════════ -->
    <template v-if="phase === 'exam' && currentQ">
      <!-- 顶部状态栏 -->
      <div class="card">
        <div class="flex items-center justify-between flex-wrap gap-3">
          <div>
            <h3 class="font-semibold text-gray-800">{{ currentExam?.name }}</h3>
            <p class="text-xs text-gray-400 mt-0.5">
              第 {{ currentIndex + 1 }} / {{ questions.length }} 题 &nbsp;·&nbsp;
              已作答 {{ Object.keys(answers).length }} 题
            </p>
          </div>
          <div class="flex items-center gap-4">
            <!-- 倒计时 -->
            <div
              class="font-mono text-xl font-bold px-4 py-1.5 rounded-xl"
              :class="timeUrgent ? 'bg-red-50 text-red-600 animate-pulse' : 'bg-gray-100 text-gray-700'"
            >
              ⏱ {{ timeDisplay }}
            </div>
            <!-- 提交按钮 -->
            <button
              :disabled="isSubmitting"
              class="px-4 py-1.5 text-sm font-medium bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl transition-colors disabled:opacity-50"
              @click="handleSubmit"
            >
              {{ isSubmitting ? '提交中...' : '交卷' }}
            </button>
          </div>
        </div>
        <!-- 进度条 -->
        <div class="mt-3 h-2 bg-gray-100 rounded-full overflow-hidden">
          <div
            class="h-full bg-indigo-500 rounded-full transition-all"
            :style="`width: ${progressPct}%`"
          />
        </div>
      </div>

      <!-- 题目卡片 -->
      <div class="card space-y-4">
        <!-- 题型标签 -->
        <div class="flex items-center gap-2">
          <span class="text-xs px-2 py-0.5 rounded-full font-medium"
            :class="{
              'bg-blue-50 text-blue-600': currentQ.type === 'single',
              'bg-purple-50 text-purple-600': currentQ.type === 'multi',
              'bg-green-50 text-green-600': currentQ.type === 'judge',
            }">
            {{ { single: '单选题', multi: '多选题', judge: '判断题' }[currentQ.type] || '题目' }}
          </span>
          <span class="text-xs text-gray-400">{{ currentQ.knowledge_point }}</span>
        </div>

        <!-- 题目文本 -->
        <p class="text-sm font-medium text-gray-800 leading-relaxed">
          {{ currentIndex + 1 }}. {{ currentQ.question }}
        </p>

        <!-- 选项 -->
        <div class="space-y-2">
          <button
            v-for="(text, key) in currentQ.options"
            :key="key"
            class="w-full text-left flex items-start gap-3 px-4 py-3 rounded-xl border text-sm transition-all"
            :class="isSelected(currentQ.id, key)
              ? 'border-indigo-400 bg-indigo-50 text-indigo-700 font-medium'
              : 'border-gray-200 hover:border-indigo-200 hover:bg-indigo-50/50 text-gray-700'"
            @click="selectAnswer(currentQ.id, key)"
          >
            <span class="w-6 h-6 rounded-full border-2 flex items-center justify-center text-xs shrink-0 mt-0.5"
              :class="isSelected(currentQ.id, key)
                ? 'border-indigo-500 bg-indigo-500 text-white'
                : 'border-gray-300 text-gray-500'">
              {{ key }}
            </span>
            {{ text }}
          </button>
        </div>
      </div>

      <!-- 底部导航 -->
      <div class="flex items-center justify-between">
        <button
          :disabled="currentIndex === 0"
          class="px-4 py-2 text-sm text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-xl transition-colors disabled:opacity-30"
          @click="currentIndex--"
        >
          ← 上一题
        </button>

        <!-- 题目跳转圆点 -->
        <div class="flex gap-1.5 flex-wrap justify-center max-w-xs">
          <button
            v-for="(q, i) in questions"
            :key="q.id"
            class="w-7 h-7 rounded-full text-xs font-medium transition-all"
            :class="i === currentIndex
              ? 'bg-indigo-600 text-white'
              : answers[q.id]
                ? 'bg-emerald-100 text-emerald-700 hover:bg-emerald-200'
                : 'bg-gray-100 text-gray-500 hover:bg-gray-200'"
            @click="currentIndex = i"
          >
            {{ i + 1 }}
          </button>
        </div>

        <button
          v-if="currentIndex < questions.length - 1"
          class="px-4 py-2 text-sm text-white bg-indigo-600 hover:bg-indigo-700 rounded-xl transition-colors"
          @click="currentIndex++"
        >
          下一题 →
        </button>
        <button
          v-else
          :disabled="isSubmitting"
          class="px-4 py-2 text-sm text-white bg-emerald-600 hover:bg-emerald-700 rounded-xl transition-colors disabled:opacity-50"
          @click="handleSubmit"
        >
          {{ isSubmitting ? '提交中...' : '✅ 提交答卷' }}
        </button>
      </div>
    </template>

    <!-- ══ 成绩报告 ══════════════════════════════════════════ -->
    <template v-if="phase === 'result' && result">
      <!-- 总分卡 -->
      <div class="card text-center py-6">
        <div
          class="text-6xl font-extrabold mb-2"
          :class="result.passed ? 'text-emerald-500' : 'text-red-500'"
        >
          {{ result.score }}
          <span class="text-2xl font-normal text-gray-400">分</span>
        </div>
        <div
          class="inline-flex items-center gap-1.5 px-4 py-1.5 rounded-full text-sm font-semibold mb-4"
          :class="result.passed
            ? 'bg-emerald-50 text-emerald-700'
            : 'bg-red-50 text-red-600'"
        >
          {{ result.passed ? '🎉 通过' : '❌ 未通过' }} · {{ result.grade }}
        </div>
        <div class="flex justify-center gap-6 text-sm text-gray-600">
          <div><span class="font-bold text-gray-800">{{ result.correct_count }}</span> / {{ result.total_questions }} 题正确</div>
          <div>错误 <span class="font-bold text-red-500">{{ result.wrong_count }}</span> 题</div>
          <div>及格线 <span class="font-bold">{{ result.pass_score }}</span> 分</div>
        </div>
      </div>

      <!-- 薄弱点提示 -->
      <div v-if="result.weak_kp_ids.length" class="card border-l-4 border-amber-400 bg-amber-50/40">
        <p class="text-sm font-semibold text-amber-800 mb-2">⚠️ 检测到薄弱知识点</p>
        <div class="flex flex-wrap gap-2">
          <span
            v-for="kp in result.weak_kp_ids"
            :key="kp"
            class="text-xs bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full"
          >
            {{ kp }}
          </span>
        </div>
        <p class="text-xs text-amber-600 mt-2">建议前往「学习路径」页面，针对这些知识点制定复习计划。</p>
      </div>

      <!-- 错题列表 -->
      <div class="card">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-sm font-semibold text-gray-700">错题解析（{{ result.wrong_count }} 道）</h3>
          <button
            v-if="result.wrong_count > 3"
            class="text-xs text-indigo-500 hover:text-indigo-700"
            @click="showAllWrong = !showAllWrong"
          >
            {{ showAllWrong ? '收起 ▲' : '展开全部 ▼' }}
          </button>
        </div>

        <div v-if="result.wrong_count === 0" class="text-center py-6 text-emerald-500 font-medium">
          🎊 全部答对，太棒了！
        </div>

        <div v-else class="space-y-4">
          <div
            v-for="(item, _idx) in showAllWrong ? result.wrong_items : result.wrong_items.slice(0, 3)"
            :key="item.question_id"
            class="rounded-xl border border-red-100 bg-red-50/30 p-4 space-y-2"
          >
            <p class="text-sm font-medium text-gray-800">
              <span class="text-red-500 font-bold mr-1">✗</span>
              {{ item.question }}
            </p>
            <div class="flex flex-wrap gap-3 text-xs">
              <span class="bg-red-100 text-red-600 px-2 py-0.5 rounded">
                你的答案：{{ item.user_answer }}
              </span>
              <span class="bg-emerald-100 text-emerald-600 px-2 py-0.5 rounded">
                正确答案：{{ item.correct_answer }}
              </span>
            </div>
            <p v-if="item.explanation" class="text-xs text-gray-600 bg-white rounded-lg p-2 border border-gray-100">
              💡 {{ item.explanation }}
            </p>
            <p class="text-xs text-gray-400">知识点：{{ item.knowledge_point }}</p>
          </div>
        </div>
      </div>

      <!-- 底部操作 -->
      <div class="flex gap-3 justify-center">
        <button
          class="px-6 py-2 text-sm font-medium bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl transition-colors"
          @click="restart"
        >
          ← 返回选择考试
        </button>
        <button
          class="px-6 py-2 text-sm font-medium bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl transition-colors"
          @click="startExam(currentExam!)"
        >
          🔄 重新考试
        </button>
      </div>
    </template>

  </div>
</template>
