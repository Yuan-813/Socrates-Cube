<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

/* ── 类型定义 ─────────────────────────────────── */
interface Template {
  id: string
  title: string
  description: string
  chapter: string
  duration_min: number
  slide_count: number
  has_quiz: boolean
  has_simulation: boolean
  tags: string[]
}

interface LessonSlide {
  id: string
  title: string
  type: string  // title|concept|protocol|diagram|quiz|summary
  content: string
  key_points: string[]
  speaker_notes: string
  rfc_refs: string[]
  visual_hint: string
}

interface LessonQuiz {
  question: string
  options: string[]
  answer_index: number
  explanation: string
}

interface LessonData {
  lesson_id: string
  title: string
  topic: string
  difficulty: number
  duration_min: number
  slides: LessonSlide[]
  quiz: LessonQuiz[]
  summary: string
  references: string[]
  generated_at: string
  inspired_by: string
}

/* ── 状态 ─────────────────────────────────────── */
const templates = ref<Template[]>([])
const currentLesson = ref<LessonData | null>(null)
const currentSlideIdx = ref(0)
const activeMode = ref<'templates' | 'custom' | 'lesson'>('templates')

const customTopic = ref('')
const customDifficulty = ref(2)
const customSlideCount = ref(5)
const customIncludeQuiz = ref(true)
const generating = ref(false)
const loadingTemplates = ref(false)
const errorMsg = ref('')

// 测验状态
const quizAnswers = ref<Record<number, number>>({})
const quizSubmitted = ref(false)

/* ── 计算属性 ────────────────────────────────── */
const currentSlide = computed<LessonSlide | null>(() =>
  currentLesson.value?.slides[currentSlideIdx.value] ?? null
)

const totalSlides = computed(() => currentLesson.value?.slides.length ?? 0)
const progress = computed(() => totalSlides.value ? Math.round(((currentSlideIdx.value + 1) / totalSlides.value) * 100) : 0)

const quizScore = computed(() => {
  if (!currentLesson.value?.quiz.length || !quizSubmitted.value) return null
  const correct = currentLesson.value.quiz.filter((q, i) => quizAnswers.value[i] === q.answer_index).length
  return Math.round((correct / currentLesson.value.quiz.length) * 100)
})

const slideTypeConfig: Record<string, { icon: string; color: string; label: string }> = {
  title:    { icon: '🎯', color: '#6366f1', label: '封面' },
  concept:  { icon: '💡', color: '#0ea5e9', label: '概念' },
  protocol: { icon: '🔌', color: '#10b981', label: '协议' },
  diagram:  { icon: '📊', color: '#f59e0b', label: '图示' },
  quiz:     { icon: '❓', color: '#ec4899', label: '测验' },
  summary:  { icon: '✅', color: '#8b5cf6', label: '总结' },
}

const difficultyLabels = ['', '入门', '基础', '中等', '进阶', '专家']

/* ── 方法 ────────────────────────────────────── */
async function loadTemplates() {
  loadingTemplates.value = true
  errorMsg.value = ''
  try {
    const res = await axios.get('/api/v1/lesson/templates')
    templates.value = res.data.templates || []
  } catch {
    errorMsg.value = '加载模板失败，请稍后重试'
  } finally {
    loadingTemplates.value = false
  }
}

async function generateFromTemplate(tpl: Template) {
  generating.value = true
  errorMsg.value = ''
  activeMode.value = 'lesson'
  try {
    const res = await axios.post('/api/v1/lesson/generate', {
      topic: tpl.title,
      difficulty: 2,
      slide_count: tpl.slide_count,
      include_quiz: tpl.has_quiz,
      target_audience: '计算机网络课程学生',
    })
    currentLesson.value = res.data
    currentSlideIdx.value = 0
    quizAnswers.value = {}
    quizSubmitted.value = false
  } catch {
    errorMsg.value = '课程生成失败，请稍后重试'
    activeMode.value = 'templates'
  } finally {
    generating.value = false
  }
}

async function generateCustom() {
  if (!customTopic.value.trim() || generating.value) return
  generating.value = true
  errorMsg.value = ''
  activeMode.value = 'lesson'
  try {
    const res = await axios.post('/api/v1/lesson/generate', {
      topic: customTopic.value,
      difficulty: customDifficulty.value,
      slide_count: customSlideCount.value,
      include_quiz: customIncludeQuiz.value,
      target_audience: '计算机网络课程学生',
    })
    currentLesson.value = res.data
    currentSlideIdx.value = 0
    quizAnswers.value = {}
    quizSubmitted.value = false
  } catch {
    errorMsg.value = '课程生成失败，请稍后重试'
    activeMode.value = 'custom'
  } finally {
    generating.value = false
  }
}

function prevSlide() { if (currentSlideIdx.value > 0) currentSlideIdx.value-- }
function nextSlide() { if (currentSlideIdx.value < totalSlides.value - 1) currentSlideIdx.value++ }
function goToSlide(idx: number) { currentSlideIdx.value = idx }

function submitQuiz() {
  quizSubmitted.value = true
}

function resetLesson() {
  currentLesson.value = null
  currentSlideIdx.value = 0
  quizAnswers.value = {}
  quizSubmitted.value = false
  activeMode.value = 'templates'
}

onMounted(loadTemplates)
</script>

<template>
  <div class="lesson-wrap">

    <!-- 顶部标题栏 -->
    <div class="lesson-header card">
      <div class="header-left">
        <div class="header-icon">🎓</div>
        <div>
          <h2 class="header-title">互动课堂</h2>
          <p class="header-sub">
            受 <a href="https://github.com/THU-MAIC/OpenMAIC" target="_blank" class="link-blue">OpenMAIC</a>
            启发 · AI 生成结构化互动课程
          </p>
        </div>
      </div>
      <div class="header-actions" v-if="currentLesson">
        <button class="btn-outline" @click="resetLesson">← 返回</button>
      </div>
    </div>

    <!-- 错误提示 -->
    <div v-if="errorMsg" class="error-banner">{{ errorMsg }}</div>

    <!-- ───── 生成中遮罩 ───── -->
    <div v-if="generating" class="generating-overlay card">
      <div class="gen-spinner">⚙️</div>
      <p class="gen-text">AI 正在生成互动课程...</p>
      <p class="gen-sub">分析课程结构 · 生成幻灯片 · 编写测验题</p>
    </div>

    <!-- ───── 课堂模式：显示幻灯片 ───── -->
    <template v-else-if="currentLesson && activeMode === 'lesson'">

      <!-- 课程信息栏 -->
      <div class="lesson-meta card">
        <div class="meta-info">
          <span class="meta-title">{{ currentLesson.title }}</span>
          <span class="diff-badge" :class="`diff-${currentLesson.difficulty}`">
            {{ difficultyLabels[currentLesson.difficulty] }}
          </span>
          <span class="meta-stat">🕐 {{ currentLesson.duration_min }} 分钟</span>
          <span class="meta-stat">📑 {{ totalSlides }} 张幻灯片</span>
        </div>
        <!-- 进度条 -->
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: progress + '%' }"></div>
        </div>
        <div class="progress-text">{{ currentSlideIdx + 1 }} / {{ totalSlides }}</div>
      </div>

      <!-- 幻灯片缩略图导航 -->
      <div class="slide-nav-strip card">
        <button
          v-for="(slide, idx) in currentLesson.slides"
          :key="slide.id"
          class="slide-thumb"
          :class="{ active: idx === currentSlideIdx }"
          @click="goToSlide(idx)"
          :title="slide.title"
        >
          <span class="thumb-icon">{{ slideTypeConfig[slide.type]?.icon || '📄' }}</span>
          <span class="thumb-num">{{ idx + 1 }}</span>
        </button>
      </div>

      <!-- 当前幻灯片内容 -->
      <div v-if="currentSlide" class="slide-card card" :class="`slide-type-${currentSlide.type}`">
        <!-- 幻灯片头部 -->
        <div class="slide-head">
          <span class="slide-type-badge" :style="{ background: slideTypeConfig[currentSlide.type]?.color + '20', color: slideTypeConfig[currentSlide.type]?.color }">
            {{ slideTypeConfig[currentSlide.type]?.icon }}
            {{ slideTypeConfig[currentSlide.type]?.label }}
          </span>
          <div class="rfc-refs" v-if="currentSlide.rfc_refs.length">
            <span v-for="rfc in currentSlide.rfc_refs" :key="rfc" class="rfc-badge">{{ rfc }}</span>
          </div>
        </div>

        <!-- 幻灯片标题 -->
        <h2 class="slide-title">{{ currentSlide.title }}</h2>

        <!-- 内容区 -->
        <p class="slide-content">{{ currentSlide.content }}</p>

        <!-- 要点列表 -->
        <ul v-if="currentSlide.key_points.length" class="key-points">
          <li v-for="point in currentSlide.key_points" :key="point" class="key-point">
            <span class="point-dot" :style="{ background: slideTypeConfig[currentSlide.type]?.color }"></span>
            {{ point }}
          </li>
        </ul>

        <!-- 视觉提示 -->
        <div v-if="currentSlide.visual_hint" class="visual-hint">
          <span class="hint-icon">🎨</span>
          <span class="hint-text">{{ currentSlide.visual_hint }}</span>
        </div>

        <!-- 讲师备注 -->
        <div v-if="currentSlide.speaker_notes" class="speaker-notes">
          <span class="notes-label">📝 讲师备注</span>
          <span class="notes-text">{{ currentSlide.speaker_notes }}</span>
        </div>
      </div>

      <!-- 上下翻页 -->
      <div class="slide-controls">
        <button class="ctrl-btn" :disabled="currentSlideIdx === 0" @click="prevSlide">← 上一页</button>
        <span class="ctrl-info">{{ currentSlideIdx + 1 }} / {{ totalSlides }}</span>
        <button class="ctrl-btn ctrl-btn--next" :disabled="currentSlideIdx === totalSlides - 1" @click="nextSlide">下一页 →</button>
      </div>

      <!-- 测验区块 -->
      <div v-if="currentLesson.quiz.length" class="quiz-section card">
        <h3 class="quiz-title">🧪 随堂测验</h3>
        <div class="quiz-list">
          <div v-for="(q, qi) in currentLesson.quiz" :key="qi" class="quiz-item">
            <p class="q-text">{{ qi + 1 }}. {{ q.question }}</p>
            <div class="q-options">
              <button
                v-for="(opt, oi) in q.options"
                :key="oi"
                class="q-option"
                :class="{
                  selected: quizAnswers[qi] === oi,
                  correct: quizSubmitted && oi === q.answer_index,
                  wrong: quizSubmitted && quizAnswers[qi] === oi && oi !== q.answer_index,
                }"
                :disabled="quizSubmitted"
                @click="!quizSubmitted && (quizAnswers[qi] = oi)"
              >{{ opt }}</button>
            </div>
            <div v-if="quizSubmitted" class="q-explanation">
              💬 {{ q.explanation }}
            </div>
          </div>
        </div>

        <div v-if="!quizSubmitted" class="quiz-actions">
          <button class="btn-submit-quiz" @click="submitQuiz">提交答案</button>
        </div>
        <div v-else class="quiz-result">
          <span class="quiz-score" :class="quizScore! >= 60 ? 'pass' : 'fail'">
            🏆 得分：{{ quizScore }}%
          </span>
          <span class="quiz-msg">{{ quizScore! >= 80 ? '优秀！' : quizScore! >= 60 ? '良好，继续加油！' : '需要再复习一下' }}</span>
        </div>
      </div>

      <!-- 课程总结 -->
      <div v-if="currentLesson.summary" class="summary-card card">
        <h3 class="summary-title">📖 课程摘要</h3>
        <p class="summary-text">{{ currentLesson.summary }}</p>
        <div v-if="currentLesson.references.length" class="refs">
          <span class="refs-label">参考资料：</span>
          <span v-for="ref in currentLesson.references" :key="ref" class="ref-item">{{ ref }}</span>
        </div>
        <p class="inspired-by">{{ currentLesson.inspired_by }}</p>
      </div>

    </template>

    <!-- ───── 首页：模板 + 自定义 ───── -->
    <template v-else>
      <div class="home-grid">

        <!-- 左侧：预置模板 -->
        <div class="templates-panel">
          <div class="panel-header">
            <h3 class="panel-title">📚 预置课程模板</h3>
            <p class="panel-sub">网络协议权威教材配套课程，一键生成</p>
          </div>
          <div v-if="loadingTemplates" class="loading-tip">加载模板中...</div>
          <div v-else class="template-list">
            <div
              v-for="tpl in templates"
              :key="tpl.id"
              class="template-card"
              @click="!generating && generateFromTemplate(tpl)"
            >
              <div class="tpl-header">
                <span class="tpl-chapter">{{ tpl.chapter }}</span>
                <span class="tpl-duration">🕐 {{ tpl.duration_min }}min</span>
              </div>
              <h4 class="tpl-title">{{ tpl.title }}</h4>
              <p class="tpl-desc">{{ tpl.description }}</p>
              <div class="tpl-tags">
                <span v-for="tag in tpl.tags" :key="tag" class="tpl-tag">{{ tag }}</span>
              </div>
              <div class="tpl-footer">
                <span class="tpl-stat">📑 {{ tpl.slide_count }} 张</span>
                <span v-if="tpl.has_quiz" class="tpl-stat tpl-quiz">🧪 含测验</span>
                <span v-if="tpl.has_simulation" class="tpl-stat tpl-sim">🎬 含仿真</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 右侧：自定义生成 -->
        <div class="custom-panel">
          <div class="panel-header">
            <h3 class="panel-title">✨ 自定义课程生成</h3>
            <p class="panel-sub">输入任意网络协议主题，AI 即时生成结构化课程</p>
          </div>
          <div class="custom-form">
            <div class="form-group">
              <label class="form-label">课程主题</label>
              <input
                v-model="customTopic"
                class="form-input"
                placeholder="如：HTTP/2 多路复用、QUIC 协议、BGP 路由策略..."
                @keyup.enter="generateCustom"
              />
            </div>
            <div class="form-row">
              <div class="form-group">
                <label class="form-label">难度等级</label>
                <select v-model="customDifficulty" class="form-select">
                  <option :value="1">🟢 入门</option>
                  <option :value="2">🔵 基础</option>
                  <option :value="3">🟡 中等</option>
                  <option :value="4">🟠 进阶</option>
                  <option :value="5">🔴 专家</option>
                </select>
              </div>
              <div class="form-group">
                <label class="form-label">幻灯片数量</label>
                <select v-model="customSlideCount" class="form-select">
                  <option :value="3">3 张</option>
                  <option :value="5">5 张</option>
                  <option :value="7">7 张</option>
                  <option :value="10">10 张</option>
                </select>
              </div>
            </div>
            <div class="form-check">
              <input id="include-quiz" type="checkbox" v-model="customIncludeQuiz" class="check-input" />
              <label for="include-quiz" class="check-label">🧪 包含随堂测验题（推荐）</label>
            </div>
            <button
              class="btn-generate"
              :disabled="!customTopic.trim() || generating"
              @click="generateCustom"
            >
              🚀 一键生成互动课程
            </button>
          </div>

          <!-- OpenMAIC 说明 -->
          <div class="openmaic-card">
            <div class="openmaic-header">
              <span class="openmaic-badge">OpenMAIC</span>
              <span class="openmaic-title">多智能体互动课堂设计理念</span>
            </div>
            <ul class="openmaic-features">
              <li>📐 结构化课程生成：主题 → 完整幻灯片序列</li>
              <li>🎯 多类型内容：讲解 + 图示 + 测验组合</li>
              <li>📚 RFC 标准引用：每页关联权威来源</li>
              <li>🎓 难度分级：1-5级覆盖入门到专家</li>
            </ul>
            <a href="https://github.com/THU-MAIC/OpenMAIC" target="_blank" class="openmaic-link">
              🔗 github.com/THU-MAIC/OpenMAIC
            </a>
          </div>
        </div>

      </div>
    </template>

  </div>
</template>

<style scoped>
.lesson-wrap { display: flex; flex-direction: column; gap: 16px; }

/* 头部 */
.lesson-header { display: flex; align-items: center; justify-content: space-between; }
.header-left { display: flex; align-items: center; gap: 14px; }
.header-icon { font-size: 36px; }
.header-title { font-size: 20px; font-weight: 800; color: #1e293b; margin: 0; }
.header-sub { font-size: 12px; color: #64748b; margin: 2px 0 0; }
.link-blue { color: #3b82f6; text-decoration: none; }
.link-blue:hover { text-decoration: underline; }

/* 错误 */
.error-banner { background: #fee2e2; border: 1px solid #fca5a5; border-radius: 10px; padding: 10px 14px; font-size: 13px; color: #dc2626; }

/* 生成遮罩 */
.generating-overlay { text-align: center; padding: 48px; }
.gen-spinner { font-size: 48px; animation: spin 1.5s linear infinite; display: inline-block; }
.gen-text { font-size: 16px; font-weight: 700; color: #1e293b; margin: 12px 0 4px; }
.gen-sub { font-size: 12px; color: #94a3b8; }
@keyframes spin { to { transform: rotate(360deg); } }

/* 课程元信息 */
.lesson-meta { display: flex; flex-direction: column; gap: 8px; }
.meta-info { display: flex; align-items: center; flex-wrap: wrap; gap: 10px; }
.meta-title { font-size: 15px; font-weight: 700; color: #1e293b; }
.meta-stat { font-size: 12px; color: #64748b; }
.diff-badge { font-size: 11px; padding: 2px 8px; border-radius: 6px; font-weight: 600; }
.diff-1 { background: #dcfce7; color: #16a34a; }
.diff-2 { background: #dbeafe; color: #1d4ed8; }
.diff-3 { background: #fef9c3; color: #ca8a04; }
.diff-4 { background: #ffedd5; color: #c2410c; }
.diff-5 { background: #fee2e2; color: #dc2626; }
.progress-bar { height: 4px; background: #e2e8f0; border-radius: 2px; overflow: hidden; }
.progress-fill { height: 100%; background: linear-gradient(90deg, #6366f1, #8b5cf6); border-radius: 2px; transition: width 0.4s ease; }
.progress-text { font-size: 11px; color: #94a3b8; text-align: right; }

/* 幻灯片缩略图 */
.slide-nav-strip { display: flex; gap: 6px; padding: 10px; overflow-x: auto; flex-wrap: wrap; }
.slide-thumb {
  width: 44px; height: 44px; border: 2px solid #e2e8f0; border-radius: 8px;
  background: white; cursor: pointer; display: flex; flex-direction: column;
  align-items: center; justify-content: center; gap: 2px; transition: all 0.15s;
  flex-shrink: 0;
}
.slide-thumb:hover { border-color: #a5b4fc; background: #f5f3ff; }
.slide-thumb.active { border-color: #6366f1; background: #eef2ff; }
.thumb-icon { font-size: 16px; line-height: 1; }
.thumb-num { font-size: 10px; color: #64748b; font-weight: 600; }

/* 幻灯片主体 */
.slide-card { padding: 28px; min-height: 280px; transition: all 0.3s; }
.slide-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; flex-wrap: wrap; gap: 8px; }
.slide-type-badge { font-size: 12px; font-weight: 700; padding: 4px 12px; border-radius: 20px; }
.rfc-refs { display: flex; gap: 6px; flex-wrap: wrap; }
.rfc-badge { font-size: 10px; background: #f0fdf4; color: #15803d; border: 1px solid #bbf7d0; border-radius: 4px; padding: 2px 7px; font-weight: 600; font-family: monospace; }
.slide-title { font-size: 22px; font-weight: 800; color: #1e293b; margin: 0 0 12px; }
.slide-content { font-size: 14px; color: #374151; line-height: 1.7; margin: 0 0 16px; }
.key-points { list-style: none; padding: 0; margin: 0 0 14px; display: flex; flex-direction: column; gap: 8px; }
.key-point { display: flex; align-items: flex-start; gap: 10px; font-size: 13px; color: #374151; }
.point-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; margin-top: 5px; }
.visual-hint { display: flex; align-items: flex-start; gap: 8px; background: #fffbeb; border: 1px solid #fde68a; border-radius: 8px; padding: 10px 12px; font-size: 12px; color: #92400e; margin: 10px 0; }
.hint-icon { font-size: 16px; flex-shrink: 0; }
.speaker-notes { display: flex; align-items: flex-start; gap: 8px; background: #f8fafc; border-left: 3px solid #cbd5e1; padding: 10px 12px; font-size: 12px; color: #64748b; margin-top: 12px; border-radius: 0 6px 6px 0; }
.notes-label { font-weight: 700; color: #475569; white-space: nowrap; flex-shrink: 0; }
.notes-text { line-height: 1.5; }

/* 翻页控制 */
.slide-controls { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.ctrl-btn {
  padding: 10px 22px; border: 2px solid #6366f1; border-radius: 9px;
  background: white; color: #6366f1; font-size: 13px; font-weight: 700;
  cursor: pointer; transition: all 0.18s;
}
.ctrl-btn:hover:not(:disabled) { background: #6366f1; color: white; }
.ctrl-btn:disabled { opacity: 0.3; cursor: not-allowed; }
.ctrl-btn--next { background: #6366f1; color: white; }
.ctrl-btn--next:hover:not(:disabled) { background: #4f46e5; }
.ctrl-info { font-size: 13px; color: #94a3b8; font-weight: 600; }

/* 测验区块 */
.quiz-section {}
.quiz-title { font-size: 15px; font-weight: 700; color: #1e293b; margin: 0 0 16px; }
.quiz-list { display: flex; flex-direction: column; gap: 20px; }
.quiz-item {}
.q-text { font-size: 14px; font-weight: 600; color: #1e293b; margin: 0 0 10px; }
.q-options { display: flex; flex-direction: column; gap: 7px; }
.q-option {
  padding: 9px 14px; background: white; border: 2px solid #e2e8f0;
  border-radius: 8px; text-align: left; cursor: pointer; font-size: 13px;
  color: #374151; transition: all 0.15s; font-weight: 500;
}
.q-option:hover:not(:disabled) { border-color: #a5b4fc; background: #f5f3ff; }
.q-option.selected { border-color: #6366f1; background: #eef2ff; color: #4f46e5; }
.q-option.correct { border-color: #22c55e; background: #f0fdf4; color: #15803d; }
.q-option.wrong { border-color: #ef4444; background: #fef2f2; color: #dc2626; }
.q-explanation { font-size: 12px; color: #64748b; background: #f8fafc; padding: 8px 12px; border-radius: 6px; margin-top: 8px; }
.quiz-actions { display: flex; justify-content: flex-end; margin-top: 14px; }
.btn-submit-quiz {
  padding: 10px 24px; background: #6366f1; color: white;
  border: none; border-radius: 9px; font-size: 14px; font-weight: 700;
  cursor: pointer; transition: all 0.18s;
}
.btn-submit-quiz:hover { background: #4f46e5; }
.quiz-result { display: flex; align-items: center; gap: 12px; margin-top: 16px; padding: 12px 16px; background: #f8fafc; border-radius: 10px; }
.quiz-score { font-size: 16px; font-weight: 800; }
.quiz-score.pass { color: #22c55e; }
.quiz-score.fail { color: #ef4444; }
.quiz-msg { font-size: 13px; color: #64748b; }

/* 课程摘要 */
.summary-title { font-size: 15px; font-weight: 700; color: #1e293b; margin: 0 0 10px; }
.summary-text { font-size: 13px; color: #374151; line-height: 1.7; margin: 0 0 10px; }
.refs { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin-top: 8px; }
.refs-label { font-size: 12px; font-weight: 600; color: #64748b; }
.ref-item { font-size: 11px; background: #f1f5f9; color: #475569; padding: 2px 8px; border-radius: 4px; }
.inspired-by { font-size: 11px; color: #94a3b8; margin-top: 8px; }

/* 首页双栏布局 */
.home-grid { display: grid; grid-template-columns: 1fr 360px; gap: 16px; }
@media (max-width: 900px) { .home-grid { grid-template-columns: 1fr; } }

/* 面板通用 */
.panel-header { margin-bottom: 14px; }
.panel-title { font-size: 15px; font-weight: 700; color: #1e293b; margin: 0 0 4px; }
.panel-sub { font-size: 12px; color: #64748b; margin: 0; }
.loading-tip { font-size: 13px; color: #94a3b8; padding: 20px; text-align: center; }

/* 模板列表 */
.templates-panel {}
.template-list { display: flex; flex-direction: column; gap: 10px; }
.template-card {
  background: white; border: 2px solid #e2e8f0; border-radius: 12px; padding: 14px;
  cursor: pointer; transition: all 0.18s;
}
.template-card:hover { border-color: #a5b4fc; box-shadow: 0 4px 16px rgba(99,102,241,0.12); transform: translateY(-2px); }
.tpl-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.tpl-chapter { font-size: 11px; background: #e0e7ff; color: #4338ca; padding: 2px 7px; border-radius: 4px; font-weight: 600; }
.tpl-duration { font-size: 11px; color: #94a3b8; }
.tpl-title { font-size: 14px; font-weight: 700; color: #1e293b; margin: 0 0 5px; }
.tpl-desc { font-size: 12px; color: #64748b; margin: 0 0 8px; line-height: 1.5; }
.tpl-tags { display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 8px; }
.tpl-tag { font-size: 10px; background: #f0fdf4; color: #15803d; border: 1px solid #bbf7d0; padding: 1px 6px; border-radius: 4px; font-family: monospace; }
.tpl-footer { display: flex; gap: 8px; flex-wrap: wrap; }
.tpl-stat { font-size: 10px; color: #64748b; }
.tpl-quiz { color: #ec4899; }
.tpl-sim { color: #f59e0b; }

/* 自定义表单 */
.custom-form { display: flex; flex-direction: column; gap: 14px; background: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 16px; }
.form-group { display: flex; flex-direction: column; gap: 5px; }
.form-label { font-size: 12px; font-weight: 600; color: #374151; }
.form-input { padding: 9px 12px; border: 1px solid #e2e8f0; border-radius: 8px; font-size: 13px; outline: none; transition: border-color 0.15s; }
.form-input:focus { border-color: #6366f1; }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.form-select { padding: 9px 12px; border: 1px solid #e2e8f0; border-radius: 8px; font-size: 13px; outline: none; cursor: pointer; }
.form-check { display: flex; align-items: center; gap: 8px; }
.check-input { width: 15px; height: 15px; cursor: pointer; accent-color: #6366f1; }
.check-label { font-size: 13px; color: #374151; cursor: pointer; }
.btn-generate {
  padding: 12px; background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: white; border: none; border-radius: 10px; font-size: 14px; font-weight: 700;
  cursor: pointer; transition: all 0.2s;
}
.btn-generate:hover:not(:disabled) { opacity: 0.9; transform: translateY(-1px); }
.btn-generate:disabled { opacity: 0.4; cursor: not-allowed; }

/* OpenMAIC 说明卡片 */
.openmaic-card { background: linear-gradient(135deg, #1e1b4b, #312e81); border-radius: 12px; padding: 16px; }
.openmaic-header { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
.openmaic-badge { font-size: 10px; background: rgba(255,255,255,0.2); color: white; padding: 2px 8px; border-radius: 4px; font-weight: 700; letter-spacing: 0.5px; }
.openmaic-title { font-size: 12px; color: rgba(255,255,255,0.7); font-weight: 600; }
.openmaic-features { list-style: none; padding: 0; margin: 0 0 12px; display: flex; flex-direction: column; gap: 6px; }
.openmaic-features li { font-size: 12px; color: rgba(255,255,255,0.85); }
.openmaic-link { font-size: 11px; color: #a5b4fc; text-decoration: none; }
.openmaic-link:hover { text-decoration: underline; color: #c7d2fe; }

/* 通用按钮 */
.btn-outline { padding: 7px 16px; border: 2px solid #6366f1; background: white; color: #6366f1; border-radius: 8px; font-size: 13px; font-weight: 600; cursor: pointer; transition: all 0.15s; }
.btn-outline:hover { background: #eef2ff; }

/* .card 复用全局 */
</style>
