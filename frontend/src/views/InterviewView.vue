<script setup lang="ts">
import { ref, computed, onUnmounted } from 'vue'
import apiClient from '@/api/client'

// ── 面试模式选择 ──────────────────────────────────────────────────
type InterviewMode = 'select' | 'running' | 'result'
const mode = ref<InterviewMode>('select')

const examTypes = [
  {
    id: 'hcia',
    name: 'HCIA-Datacom',
    icon: '🔵',
    desc: '华为认证网络工程师，考察数据通信基础、路由交换、WLAN',
    color: '#ef4444',
    bg: '#fef2f2',
    topics: ['OSI/TCP-IP分层', 'IP编址与子网', '静态路由', 'OSPF协议', 'VLAN与STP', 'ACL访问控制'],
    count: 10,
    time: 90,
  },
  {
    id: 'ccna',
    name: 'CCNA',
    icon: '🔴',
    desc: '思科认证网络工程师，涵盖路由交换、网络基础、安全基础',
    color: '#0891b2',
    bg: '#ecfeff',
    topics: ['TCP/UDP协议', '以太网与交换', 'IPv4/IPv6路由', 'EIGRP/OSPF', 'NAT/PAT', '网络安全基础'],
    count: 10,
    time: 90,
  },
  {
    id: 'interview',
    name: '网络工程师面试',
    icon: '💼',
    desc: '模拟真实企业技术面试，覆盖理论+场景排障+编程题',
    color: '#7c3aed',
    bg: '#f5f3ff',
    topics: ['TCP连接管理', '拥塞控制算法', 'HTTP/HTTPS', 'DNS解析流程', '网络故障排查', 'Socket编程'],
    count: 8,
    time: 60,
  },
]

const selectedExam = ref(examTypes[0])
// const customTopic = ref('') // reserved

// ── 面试进行中 ────────────────────────────────────────────────────
interface Question {
  id: string
  question: string
  type: string
  options?: Record<string, string>
  answer?: string
  explanation?: string
  knowledge_point: string
  difficulty?: number
}

interface AnswerRecord {
  question: Question
  userAnswer: string
  isCorrect: boolean | null
  feedback: string
  timeUsed: number
}

const questions = ref<Question[]>([])
const currentIdx = ref(0)
const userAnswer = ref('')
const records = ref<AnswerRecord[]>([])
const loading = ref(false)
const evaluating = ref(false)
const timerVal = ref(0)
let timerInterval: ReturnType<typeof setInterval> | null = null

const currentQ = computed(() => questions.value[currentIdx.value])
const progress = computed(() => currentIdx.value / Math.max(questions.value.length, 1) * 100)

function startTimer() {
  timerVal.value = 0
  if (timerInterval) clearInterval(timerInterval)
  timerInterval = setInterval(() => { timerVal.value++ }, 1000)
}
function stopTimer() {
  if (timerInterval) { clearInterval(timerInterval); timerInterval = null }
}

async function startInterview() {
  loading.value = true
  questions.value = []
  records.value = []
  currentIdx.value = 0
  mode.value = 'running'

  const exam = selectedExam.value
  const topics = exam.topics.slice(0, exam.count)
  // 分批生成不同类型题目
  const typeMap = exam.id === 'interview' ? ['short_answer', 'case'] : ['choice', 'fill', 'short_answer']
  const allQ: Question[] = []

  for (let i = 0; i < Math.min(topics.length, exam.count); i++) {
    const topic = topics[i % topics.length]
    const qtype = typeMap[i % typeMap.length]
    try {
      const { data } = await apiClient.post('/api/v1/question/generate', {
        knowledge_point: topic,
        question_type: qtype,
        difficulty: exam.id === 'hcia' ? 3 : exam.id === 'ccna' ? 3 : 4,
        count: 1,
        context: `面试场景：${exam.name}，知识点：${topic}`,
      })
      if (data.questions?.length) {
        allQ.push(data.questions[0])
      }
    } catch {
      allQ.push({
        id: `fb-${i}`,
        question: `请描述 ${topic} 的核心原理及其在实际网络中的应用场景。`,
        type: 'short_answer',
        knowledge_point: topic,
        difficulty: 3,
      })
    }
  }

  questions.value = allQ
  loading.value = false
  startTimer()
}

async function submitAnswer() {
  if (!userAnswer.value.trim() || !currentQ.value) return
  evaluating.value = true
  stopTimer()
  const timeUsed = timerVal.value

  let isCorrect: boolean | null = null
  let feedback = ''

  // 选择题直接对比
  if (currentQ.value.type === 'choice' && currentQ.value.answer) {
    isCorrect = userAnswer.value.trim().toUpperCase() === currentQ.value.answer.trim().toUpperCase()
    feedback = isCorrect
      ? `✅ 正确！${currentQ.value.explanation || ''}`
      : `❌ 答案应为 ${currentQ.value.answer}。${currentQ.value.explanation || ''}`
  } else {
    // 主观题调用资源生成接口进行 AI 评分
    try {
      const evalPrompt = `你是计算机网络面试官，请评估以下回答：\n题目：${currentQ.value.question}\n参考答案要点：${currentQ.value.answer || '按计算机网络教材'}\n学生回答：${userAnswer.value}\n返回JSON：{"is_correct":true/false,"score":0-100,"feedback":"评语和改进建议","key_points_hit":["命中的要点"]}`
      const { data: evalData } = await apiClient.post('/api/v1/resources/generate', {
        knowledge_point: currentQ.value.knowledge_point || currentQ.value.question.slice(0, 50),
        resource_type: 'doc',
        difficulty: currentQ.value.difficulty || 3,
        context: evalPrompt,
      })
      // 解析 LLM 返回的评估 JSON
      try {
        const raw = evalData?.content || evalData?.description || ''
        const jsonMatch = raw.match(/\{[\s\S]*\}/)
        if (jsonMatch) {
          const parsed = JSON.parse(jsonMatch[0])
          isCorrect = parsed.is_correct ?? null
          const hits = Array.isArray(parsed.key_points_hit) && parsed.key_points_hit.length
            ? `\n✅ 命中要点：${parsed.key_points_hit.slice(0, 3).join('、')}`
            : ''
          feedback = `${isCorrect ? '✅' : '💡'} [AI评分: ${parsed.score ?? '?'}/100] ${parsed.feedback || ''}${hits}\n\n📚 参考：${currentQ.value.answer?.slice(0, 150) || '见教材相关章节'}`
        } else {
          throw new Error('no json')
        }
      } catch {
        isCorrect = null
        feedback = `📝 已记录回答。\n📚 参考要点：${currentQ.value.explanation || currentQ.value.answer?.slice(0, 200) || '见教材相关章节'}`
      }
    } catch {
      isCorrect = null
      feedback = `📝 已记录回答。\n📚 参考要点：${currentQ.value.explanation || currentQ.value.answer?.slice(0, 200) || '见教材相关章节'}`
    }
  }

  records.value.push({
    question: currentQ.value,
    userAnswer: userAnswer.value,
    isCorrect,
    feedback,
    timeUsed,
  })

  evaluating.value = false
  userAnswer.value = ''

  if (currentIdx.value + 1 >= questions.value.length) {
    mode.value = 'result'
  } else {
    currentIdx.value++
    startTimer()
  }
}

function skipQuestion() {
  if (!currentQ.value) return
  records.value.push({
    question: currentQ.value,
    userAnswer: '（跳过）',
    isCorrect: false,
    feedback: '未作答',
    timeUsed: timerVal.value,
  })
  if (currentIdx.value + 1 >= questions.value.length) {
    mode.value = 'result'
  } else {
    currentIdx.value++
    stopTimer()
    startTimer()
  }
}

// ── 结果分析 ──────────────────────────────────────────────────────
const resultStats = computed(() => {
  const total = records.value.length
  const correct = records.value.filter(r => r.isCorrect === true).length
  const skipped = records.value.filter(r => r.userAnswer === '（跳过）').length
  const avgTime = total ? Math.round(records.value.reduce((s, r) => s + r.timeUsed, 0) / total) : 0
  const score = total ? Math.round(correct / total * 100) : 0
  return { total, correct, skipped, avgTime, score }
})

const scoreGrade = computed(() => {
  const s = resultStats.value.score
  if (s >= 90) return { label: '优秀', color: '#10b981', icon: '🏆' }
  if (s >= 75) return { label: '良好', color: '#3b82f6', icon: '🎯' }
  if (s >= 60) return { label: '及格', color: '#f59e0b', icon: '📚' }
  return { label: '需加强', color: '#ef4444', icon: '💪' }
})

const weakTopics = computed(() => {
  return records.value
    .filter(r => r.isCorrect === false)
    .map(r => r.question.knowledge_point)
    .filter((v, i, a) => a.indexOf(v) === i)
})

function resetInterview() {
  stopTimer()
  mode.value = 'select'
  questions.value = []
  records.value = []
  currentIdx.value = 0
  userAnswer.value = ''
}

onUnmounted(() => { stopTimer() })
</script>

<template>
  <div class="interview-view">
    <!-- ── 选择面试类型 ── -->
    <div v-if="mode === 'select'" class="select-panel">
      <div class="iv-header">
        <h1>🎤 AI 面试模拟中心</h1>
        <p class="iv-subtitle">模拟 HCIA / CCNA / 企业技术面试，精准检验网络知识掌握深度</p>
      </div>

      <div class="exam-cards">
        <div
          v-for="exam in examTypes"
          :key="exam.id"
          class="exam-card"
          :class="{ selected: selectedExam.id === exam.id }"
          :style="{ borderColor: selectedExam.id === exam.id ? exam.color : 'transparent', background: exam.bg }"
          @click="selectedExam = exam"
        >
          <div class="ec-top">
            <span class="ec-icon">{{ exam.icon }}</span>
            <span class="ec-name" :style="{ color: exam.color }">{{ exam.name }}</span>
          </div>
          <p class="ec-desc">{{ exam.desc }}</p>
          <div class="ec-meta">
            <span>📋 {{ exam.count }} 题</span>
            <span>⏱ {{ exam.time }}s/题</span>
            <span>{{ exam.topics.length }} 个知识点</span>
          </div>
          <div class="ec-topics">
            <span v-for="t in exam.topics.slice(0,4)" :key="t" class="ec-tag">{{ t }}</span>
          </div>
        </div>
      </div>

      <div class="start-area">
        <button class="btn-start" :disabled="loading" @click="startInterview">
          <span v-if="loading">题目生成中...</span>
          <span v-else>🚀 开始模拟面试 — {{ selectedExam.name }}</span>
        </button>
        <p class="start-tip">AI 将根据知识点动态生成题目，模拟真实面试场景</p>
      </div>
    </div>

    <!-- ── 面试进行中 ── -->
    <div v-else-if="mode === 'running'" class="running-panel">
      <div v-if="loading" class="loading-block">
        <div class="spin"></div>
        <p>AI 正在为你生成面试题目，请稍候...</p>
      </div>
      <template v-else-if="currentQ">
        <!-- 顶部进度条 -->
        <div class="rp-topbar">
          <div class="rp-info">
            <span class="rp-exam">{{ selectedExam.name }}</span>
            <span class="rp-counter">{{ currentIdx + 1 }} / {{ questions.length }}</span>
          </div>
          <div class="rp-progress-wrap">
            <div class="rp-progress-bar" :style="{ width: progress + '%' }"></div>
          </div>
          <div class="rp-timer" :class="{ warning: timerVal > 60 }">
            ⏱ {{ Math.floor(timerVal / 60) }}:{{ String(timerVal % 60).padStart(2, '0') }}
          </div>
        </div>

        <!-- 题目卡片 -->
        <div class="question-card">
          <div class="qc-meta">
            <span class="qc-type">{{ currentQ.type === 'choice' ? '选择题' : currentQ.type === 'fill' ? '填空题' : currentQ.type === 'case' ? '案例分析' : '简答题' }}</span>
            <span class="qc-topic">{{ currentQ.knowledge_point }}</span>
            <span class="qc-diff">难度 {{ '⭐'.repeat(currentQ.difficulty || 3) }}</span>
          </div>
          <div class="qc-question">{{ currentQ.question }}</div>

          <!-- 选择题选项 -->
          <div v-if="currentQ.type === 'choice' && currentQ.options" class="qc-options">
            <label
              v-for="(val, key) in currentQ.options"
              :key="key"
              class="qc-option"
              :class="{ selected: userAnswer === key }"
            >
              <input type="radio" :value="key" v-model="userAnswer" />
              <span class="opt-key">{{ key }}</span>
              <span class="opt-val">{{ val }}</span>
            </label>
          </div>

          <!-- 填空/简答/案例输入 -->
          <div v-else class="qc-textarea-wrap">
            <textarea
              v-model="userAnswer"
              placeholder="请在此输入你的回答，尽量完整描述核心概念和关键要点..."
              rows="6"
              class="qc-textarea"
              :disabled="evaluating"
            ></textarea>
            <div class="textarea-tip">
              💡 面试建议：先说核心概念，再举例或结合实际场景，最后说应用价值
            </div>
          </div>

          <div class="qc-actions">
            <button class="btn-skip" @click="skipQuestion" :disabled="evaluating">跳过</button>
            <button
              class="btn-submit"
              :disabled="!userAnswer.trim() || evaluating"
              @click="submitAnswer"
            >
              <span v-if="evaluating">AI评估中...</span>
              <span v-else>提交答案 →</span>
            </button>
          </div>
        </div>

        <!-- 已答记录 -->
        <div v-if="records.length" class="answered-list">
          <div v-for="(rec, idx) in records.slice().reverse()" :key="idx" class="answered-item"
            :class="{ correct: rec.isCorrect === true, wrong: rec.isCorrect === false }">
            <span class="ai-icon">{{ rec.isCorrect === true ? '✅' : rec.isCorrect === false ? '❌' : '⏭' }}</span>
            <span class="ai-q">{{ rec.question.question.slice(0, 40) }}...</span>
            <span class="ai-time">{{ rec.timeUsed }}s</span>
          </div>
        </div>
      </template>
    </div>

    <!-- ── 结果报告 ── -->
    <div v-else-if="mode === 'result'" class="result-panel">
      <div class="rp-hero" :style="{ borderColor: scoreGrade.color }">
        <div class="rp-grade-icon">{{ scoreGrade.icon }}</div>
        <div class="rp-score" :style="{ color: scoreGrade.color }">{{ resultStats.score }}</div>
        <div class="rp-score-label">综合得分</div>
        <div class="rp-grade-label" :style="{ background: scoreGrade.color }">{{ scoreGrade.label }}</div>
      </div>

      <div class="rp-stats">
        <div class="rs-item">
          <div class="rs-val">{{ resultStats.correct }}/{{ resultStats.total }}</div>
          <div class="rs-key">答对/总题数</div>
        </div>
        <div class="rs-item">
          <div class="rs-val">{{ resultStats.skipped }}</div>
          <div class="rs-key">跳过题数</div>
        </div>
        <div class="rs-item">
          <div class="rs-val">{{ resultStats.avgTime }}s</div>
          <div class="rs-key">平均用时</div>
        </div>
      </div>

      <!-- 薄弱点 -->
      <div v-if="weakTopics.length" class="rp-weak">
        <h3>📍 薄弱知识点（建议重点学习）</h3>
        <div class="weak-tags">
          <span v-for="t in weakTopics" :key="t" class="weak-tag">{{ t }}</span>
        </div>
      </div>

      <!-- 答题详情 -->
      <div class="rp-detail">
        <h3>📋 答题详情</h3>
        <div v-for="(rec, idx) in records" :key="idx" class="rd-item">
          <div class="rd-header">
            <span class="rd-num">Q{{ idx + 1 }}</span>
            <span class="rd-correct" :class="{ ok: rec.isCorrect === true, bad: rec.isCorrect === false }">
              {{ rec.isCorrect === true ? '✅ 正确' : rec.isCorrect === false ? '❌ 错误' : '⏭ 跳过' }}
            </span>
            <span class="rd-kp">{{ rec.question.knowledge_point }}</span>
            <span class="rd-time">{{ rec.timeUsed }}s</span>
          </div>
          <div class="rd-q">{{ rec.question.question }}</div>
          <div class="rd-ans">你的回答：{{ rec.userAnswer.slice(0, 100) }}{{ rec.userAnswer.length > 100 ? '...' : '' }}</div>
          <div class="rd-feedback">{{ rec.feedback }}</div>
        </div>
      </div>

      <div class="rp-actions">
        <button class="btn-retry" @click="startInterview">🔄 再次挑战</button>
        <button class="btn-back" @click="resetInterview">← 返回选择</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.interview-view {
  max-width: 900px;
  margin: 0 auto;
  padding: 24px;
  min-height: 100vh;
}

/* 选择面板 */
.iv-header { text-align: center; margin-bottom: 32px; }
.iv-header h1 { font-size: 28px; font-weight: 700; color: #1e293b; margin-bottom: 8px; }
.iv-subtitle { color: #64748b; font-size: 15px; }

.exam-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 16px; margin-bottom: 28px; }
.exam-card { border: 2px solid transparent; border-radius: 16px; padding: 20px; cursor: pointer; transition: all .25s; }
.exam-card:hover { transform: translateY(-3px); box-shadow: 0 8px 24px rgba(0,0,0,.1); }
.exam-card.selected { box-shadow: 0 4px 16px rgba(0,0,0,.12); }
.ec-top { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.ec-icon { font-size: 28px; }
.ec-name { font-size: 18px; font-weight: 700; }
.ec-desc { font-size: 13px; color: #64748b; margin-bottom: 10px; line-height: 1.5; }
.ec-meta { display: flex; gap: 10px; font-size: 12px; color: #94a3b8; margin-bottom: 8px; }
.ec-topics { display: flex; flex-wrap: wrap; gap: 6px; }
.ec-tag { background: rgba(0,0,0,.06); padding: 2px 8px; border-radius: 20px; font-size: 11px; color: #475569; }

.start-area { text-align: center; }
.btn-start { background: linear-gradient(135deg, #3b82f6, #6366f1); color: white; border: none; padding: 14px 48px; border-radius: 12px; font-size: 16px; font-weight: 600; cursor: pointer; transition: opacity .2s; }
.btn-start:hover { opacity: .9; }
.btn-start:disabled { opacity: .5; cursor: not-allowed; }
.start-tip { color: #94a3b8; font-size: 13px; margin-top: 10px; }

/* 进行中 */
.loading-block { text-align: center; padding: 80px 0; }
.spin { width: 48px; height: 48px; border: 4px solid #e2e8f0; border-top-color: #3b82f6; border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 16px; }
@keyframes spin { to { transform: rotate(360deg); } }

.rp-topbar { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; }
.rp-info { display: flex; gap: 10px; min-width: 140px; }
.rp-exam { font-weight: 600; color: #1e293b; font-size: 14px; }
.rp-counter { color: #64748b; font-size: 14px; }
.rp-progress-wrap { flex: 1; height: 6px; background: #e2e8f0; border-radius: 3px; overflow: hidden; }
.rp-progress-bar { height: 100%; background: linear-gradient(90deg, #3b82f6, #6366f1); transition: width .3s; }
.rp-timer { font-size: 14px; font-weight: 600; color: #3b82f6; min-width: 70px; text-align: right; }
.rp-timer.warning { color: #ef4444; }

.question-card { background: white; border-radius: 16px; padding: 28px; box-shadow: 0 4px 16px rgba(0,0,0,.08); margin-bottom: 16px; }
.qc-meta { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 16px; }
.qc-type { background: #eff6ff; color: #3b82f6; padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: 600; }
.qc-topic { background: #f5f3ff; color: #7c3aed; padding: 4px 10px; border-radius: 20px; font-size: 12px; }
.qc-diff { color: #f59e0b; font-size: 12px; }
.qc-question { font-size: 17px; font-weight: 600; color: #1e293b; line-height: 1.6; margin-bottom: 20px; }

.qc-options { display: flex; flex-direction: column; gap: 10px; margin-bottom: 20px; }
.qc-option { display: flex; align-items: flex-start; gap: 10px; padding: 12px 16px; border: 2px solid #e2e8f0; border-radius: 10px; cursor: pointer; transition: all .2s; }
.qc-option input { margin-top: 2px; }
.qc-option.selected { border-color: #3b82f6; background: #eff6ff; }
.opt-key { background: #3b82f6; color: white; width: 22px; height: 22px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; flex-shrink: 0; }
.opt-val { font-size: 14px; color: #374151; line-height: 1.5; }

.qc-textarea-wrap { margin-bottom: 16px; }
.qc-textarea { width: 100%; border: 2px solid #e2e8f0; border-radius: 10px; padding: 14px; font-size: 14px; line-height: 1.6; resize: vertical; transition: border .2s; box-sizing: border-box; font-family: inherit; color: #1e293b; }
.qc-textarea:focus { outline: none; border-color: #3b82f6; }
.textarea-tip { font-size: 12px; color: #94a3b8; margin-top: 6px; }

.qc-actions { display: flex; justify-content: flex-end; gap: 10px; }
.btn-skip { background: white; border: 2px solid #e2e8f0; color: #64748b; padding: 10px 24px; border-radius: 8px; cursor: pointer; font-size: 14px; }
.btn-submit { background: linear-gradient(135deg, #3b82f6, #6366f1); color: white; border: none; padding: 10px 28px; border-radius: 8px; cursor: pointer; font-size: 14px; font-weight: 600; }
.btn-submit:disabled { opacity: .5; cursor: not-allowed; }

.answered-list { display: flex; flex-direction: column; gap: 8px; }
.answered-item { display: flex; align-items: center; gap: 10px; padding: 8px 14px; border-radius: 8px; background: white; font-size: 13px; box-shadow: 0 1px 4px rgba(0,0,0,.05); }
.answered-item.correct { border-left: 3px solid #10b981; }
.answered-item.wrong { border-left: 3px solid #ef4444; }
.ai-icon { font-size: 16px; }
.ai-q { flex: 1; color: #475569; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ai-time { color: #94a3b8; font-size: 12px; }

/* 结果面板 */
.rp-hero { border: 3px solid; border-radius: 20px; padding: 36px 24px; text-align: center; margin-bottom: 24px; background: white; }
.rp-grade-icon { font-size: 52px; margin-bottom: 8px; }
.rp-score { font-size: 64px; font-weight: 800; line-height: 1; }
.rp-score-label { font-size: 14px; color: #64748b; margin-bottom: 12px; }
.rp-grade-label { display: inline-block; color: white; padding: 6px 20px; border-radius: 20px; font-weight: 700; font-size: 16px; }

.rp-stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 24px; }
.rs-item { background: white; border-radius: 12px; padding: 18px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,.06); }
.rs-val { font-size: 28px; font-weight: 800; color: #1e293b; }
.rs-key { font-size: 12px; color: #94a3b8; margin-top: 4px; }

.rp-weak { background: #fff7ed; border: 1px solid #fed7aa; border-radius: 12px; padding: 18px; margin-bottom: 20px; }
.rp-weak h3 { font-size: 14px; font-weight: 700; color: #92400e; margin-bottom: 10px; }
.weak-tags { display: flex; flex-wrap: wrap; gap: 8px; }
.weak-tag { background: #fef3c7; color: #92400e; padding: 4px 12px; border-radius: 20px; font-size: 13px; }

.rp-detail { background: white; border-radius: 12px; padding: 20px; margin-bottom: 20px; }
.rp-detail h3 { font-size: 15px; font-weight: 700; margin-bottom: 16px; color: #1e293b; }
.rd-item { border-bottom: 1px solid #f1f5f9; padding-bottom: 16px; margin-bottom: 16px; }
.rd-item:last-child { border-bottom: none; margin-bottom: 0; }
.rd-header { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; flex-wrap: wrap; }
.rd-num { background: #f1f5f9; color: #64748b; padding: 2px 8px; border-radius: 6px; font-size: 12px; font-weight: 700; }
.rd-correct.ok { color: #10b981; font-size: 13px; font-weight: 600; }
.rd-correct.bad { color: #ef4444; font-size: 13px; font-weight: 600; }
.rd-kp { background: #f5f3ff; color: #7c3aed; padding: 2px 8px; border-radius: 6px; font-size: 12px; }
.rd-time { color: #94a3b8; font-size: 12px; margin-left: auto; }
.rd-q { font-size: 14px; color: #374151; font-weight: 500; margin-bottom: 6px; }
.rd-ans { font-size: 13px; color: #64748b; background: #f8fafc; padding: 8px 12px; border-radius: 6px; margin-bottom: 6px; }
.rd-feedback { font-size: 13px; color: #475569; line-height: 1.5; }

.rp-actions { display: flex; gap: 12px; justify-content: center; }
.btn-retry { background: linear-gradient(135deg, #3b82f6, #6366f1); color: white; border: none; padding: 12px 32px; border-radius: 10px; font-size: 15px; font-weight: 600; cursor: pointer; }
.btn-back { background: white; border: 2px solid #e2e8f0; color: #64748b; padding: 12px 32px; border-radius: 10px; font-size: 15px; cursor: pointer; }
</style>
