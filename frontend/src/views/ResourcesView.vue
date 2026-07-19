<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useResourceStore } from '@/stores/resourceStore'
import { useChatStore } from '@/stores/chatStore'
import { useUserStore } from '@/stores/userStore'
import DocCard from '@/components/resources/DocCard.vue'
import ExerciseCard from '@/components/resources/ExerciseCard.vue'
import CodeCard from '@/components/resources/CodeCard.vue'
import MindmapCard from '@/components/resources/MindmapCard.vue'
import ScriptCard from '@/components/resources/ScriptCard.vue'
import InfoCard from '@/components/resources/InfoCard.vue'
import GenerationProgress from '@/components/resources/GenerationProgress.vue'
import type { LearningResource, ResourceType } from '@/types'

const resourceStore = useResourceStore()
const chatStore = useChatStore()
const userStore = useUserStore()

// === 主Tab：学习资源 vs 题目生成 vs 信息图 ===
const mainTab = ref<'resources' | 'questions' | 'infographic' | 'pdf'>('resources')

// === 题目生成状态 ===
const qTopic = ref('')
const qSelectedTypes = ref<string[]>(['choice', 'fill'])
const qCount = ref(5)
const qDifficulty = ref(3)
const qIsGenerating = ref(false)
const qError = ref<string | null>(null)
const qResults = ref<Record<string, unknown[]>>({})
const qExporting = ref<'docx' | 'xlsx' | null>(null)

const questionTypeOptions = [
  { value: 'choice',       label: '单选题',     icon: '①' },
  { value: 'fill',         label: '填空题',     icon: '✏️' },
  { value: 'short_answer', label: '简答题',     icon: '📝' },
  { value: 'diagram',      label: '图形判断题', icon: '🖼️' },
  { value: 'case',         label: '案例分析',   icon: '📁' },
]

const qTotalCount = computed(() =>
  Object.values(qResults.value).reduce((s, arr) => s + arr.length, 0)
)

async function handleGenerateQuestions() {
  if (!qTopic.value.trim() || qIsGenerating.value || !qSelectedTypes.value.length) return
  qError.value = null
  qResults.value = {}
  qIsGenerating.value = true
  try {
    const resp = await fetch('/api/v1/question/batch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        topic: qTopic.value.trim(),
        question_types: qSelectedTypes.value,
        count_per_type: qCount.value,
        difficulty: qDifficulty.value,
        user_id: userStore.userId,
      }),
    })
    if (!resp.ok) throw new Error(`请求失败 HTTP ${resp.status}`)
    const data = await resp.json()
    qResults.value = data.results || {}
  } catch (e: unknown) {
    qError.value = e instanceof Error ? e.message : '题目生成失败，请稍后重试'
  } finally {
    qIsGenerating.value = false
  }
}

async function handleExportQuestions(format: 'docx' | 'xlsx') {
  if (!qTotalCount.value || qExporting.value) return
  qExporting.value = format
  try {
    const questions: unknown[] = []
    for (const [qtype, items] of Object.entries(qResults.value)) {
      for (const q of items) {
        questions.push({ ...(q as Record<string, unknown>), question_type: qtype })
      }
    }
    const resp = await fetch('/api/v1/export/questions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ questions, format, topic: qTopic.value }),
    })
    if (!resp.ok) throw new Error(`导出失败 HTTP ${resp.status}`)
    const blob = await resp.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `题目_${qTopic.value}_${Date.now()}.${format}`
    a.click()
    URL.revokeObjectURL(url)
  } catch (e: unknown) {
    qError.value = e instanceof Error ? e.message : '导出失败'
  } finally {
    qExporting.value = null
  }
}

const qTypeLabels: Record<string, string> = {
  choice: '单选题', fill: '填空题', short_answer: '简答题', diagram: '图形判断题', case: '案例分析'
}

// === 信息图生成状态 ===
const igTopic = ref('')
const igStyle = ref('flowchart')
const igLoading = ref(false)
const igError = ref<string | null>(null)
const igResult = ref<null | {
  title: string; summary: string; style: string; source: string;
  nodes: { id: string; label: string; type: string; description: string; icon: string }[];
  edges: { from_id: string; to_id: string; label: string }[];
}>(null)

const igStyles = [
  { value: 'flowchart',  label: '流程图', icon: '🔄' },
  { value: 'mindmap',    label: '思维导图', icon: '🧠' },
  { value: 'timeline',   label: '时间线', icon: '📅' },
  { value: 'comparison', label: '对比图', icon: '⚖️' },
]

async function handleGenerateInfograhic() {
  if (!igTopic.value.trim() || igLoading.value) return
  igLoading.value = true
  igError.value = null
  igResult.value = null
  try {
    const r = await fetch('/api/v1/infographic/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ topic: igTopic.value.trim(), style: igStyle.value, user_id: userStore.userId }),
    })
    if (!r.ok) throw new Error(`HTTP ${r.status}`)
    igResult.value = await r.json()
  } catch (e: unknown) {
    igError.value = e instanceof Error ? e.message : '生成失败'
  } finally {
    igLoading.value = false
  }
}

// SVG 中心布局计算
const igLayoutNodes = computed(() => {
  if (!igResult.value) return []
  const nodes = igResult.value.nodes
  const cx = 360, cy = 240, r = 160
  return nodes.map((n, i) => {
    if (n.type === 'root') return { ...n, x: cx, y: cy }
    const angle = (i / Math.max(nodes.length - 1, 1)) * 2 * Math.PI - Math.PI / 2
    return { ...n, x: cx + r * Math.cos(angle), y: cy + r * Math.sin(angle) }
  })
})

function igNodeById(id: string) {
  return igLayoutNodes.value.find(n => n.id === id)
}

// ── 生成表单状态 ──────────────────────────────
const knowledgePoint = ref('')
const selectedType = ref<ResourceType | 'all'>('all')
const difficulty = ref(3)
const isGenerating = ref(false)
const generateError = ref<string | null>(null)
const showGeneratePanel = ref(true)

// ── 知识库上传 ────────────────────────────
const showUploadPanel = ref(false)
const uploadContent = ref('')
const uploadSource = ref('')
const uploadIsMarkdown = ref(false)
const isUploading = ref(false)
const uploadResult = ref<{ success: boolean; message: string; chunks_added?: number } | null>(null)

// === PDF 上传状态 ===
const pdfFile = ref<File | null>(null)
const pdfFileName = ref('')
const pdfSourceName = ref('')
const pdfUseMineru = ref(false)
const pdfUploading = ref(false)
const pdfResult = ref<{ success: boolean; message: string; chunks_added?: number } | null>(null)
const pdfDragging = ref(false)
const builtinBooks = ref<Array<{ id: string; title: string; author: string; tags: string[] }>>([])

function handlePdfFileChange(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (file && file.type === 'application/pdf') {
    pdfFile.value = file
    pdfFileName.value = file.name
    pdfSourceName.value = file.name.replace(/\.pdf$/i, '')
    pdfResult.value = null
  }
}

function handlePdfDrop(event: DragEvent) {
  event.preventDefault()
  pdfDragging.value = false
  const file = event.dataTransfer?.files?.[0]
  if (file && file.type === 'application/pdf') {
    pdfFile.value = file
    pdfFileName.value = file.name
    pdfSourceName.value = file.name.replace(/\.pdf$/i, '')
    pdfResult.value = null
  }
}

async function handlePdfUpload() {
  if (!pdfFile.value || pdfUploading.value) return
  pdfResult.value = null
  pdfUploading.value = true
  try {
    const formData = new FormData()
    formData.append('file', pdfFile.value)
    formData.append('source_name', pdfSourceName.value || pdfFileName.value)
    formData.append('use_mineru', pdfUseMineru.value ? 'true' : 'false')
    const res = await fetch('/api/v1/kb/upload-pdf', { method: 'POST', body: formData })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || '上传失败')
    pdfResult.value = { success: true, message: data.message, chunks_added: data.chunks_added }
    pdfFile.value = null
    pdfFileName.value = ''
  } catch (e: unknown) {
    pdfResult.value = { success: false, message: e instanceof Error ? e.message : '上传失败' }
  } finally {
    pdfUploading.value = false
  }
}

async function handleUpload() {
  if (!uploadContent.value.trim() || isUploading.value) return
  uploadResult.value = null
  isUploading.value = true
  try {
    const res = await fetch('/api/v1/kb/upload', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        content: uploadContent.value,
        source: uploadSource.value.trim() || '用户上传',
        is_markdown: uploadIsMarkdown.value,
      }),
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || '上传失败')
    uploadResult.value = { success: true, message: data.message, chunks_added: data.chunks_added }
    uploadContent.value = ''
    uploadSource.value = ''
  } catch (e: unknown) {
    uploadResult.value = { success: false, message: e instanceof Error ? e.message : '上传失败' }
  } finally {
    isUploading.value = false
  }
}

// ── 资源展示 Tab（本页自有，含 all）────────────
type ViewTab = ResourceType | 'all'
const viewTab = ref<ViewTab>('all')

// ── Store 数据 ───────────────────────────────
const lastDiagnosis = computed(() => chatStore.lastDiagnosis)
const profile = computed(() => userStore.profile)

// 快捷建议：诊断薄弱点 + 画像弱点
const quickSuggestions = computed(() => {
  const items: string[] = []
  const diag = lastDiagnosis.value
  if (diag?.rootCause?.weakKnowledge) items.push(diag.rootCause.weakKnowledge)
  diag?.missing_prerequisites?.slice(0, 2).forEach(p => { if (!items.includes(p)) items.push(p) })
  profile.value.weak_points.slice(0, 3).forEach(p => { if (!items.includes(p)) items.push(p) })
  return items.slice(0, 5)
})

// ── Tab 配置 ─────────────────────────────────
const tabs = computed(() => [
  { key: 'all' as ViewTab,      label: '全部',   icon: '📚', count: resourceStore.resources.length },
  { key: 'doc' as ViewTab,      label: '文档',   icon: '📄', count: resourceStore.docResources.length },
  { key: 'exercise' as ViewTab, label: '练习',   icon: '📝', count: resourceStore.exerciseResources.length },
  { key: 'code' as ViewTab,     label: '代码',   icon: '💻', count: resourceStore.codeResources.length },
  { key: 'mindmap' as ViewTab,  label: '导图',   icon: '🗺️', count: resourceStore.mindmapResources.length },
  { key: 'script' as ViewTab,   label: '脚本',   icon: '🎬', count: resourceStore.scriptResources.length },
])

// 当前展示的资源列表
const displayedResources = computed<LearningResource[]>(() => {
  switch (viewTab.value) {
    case 'doc':      return resourceStore.docResources
    case 'exercise': return resourceStore.exerciseResources
    case 'code':     return resourceStore.codeResources
    case 'mindmap':  return resourceStore.mindmapResources
    case 'script':   return resourceStore.scriptResources
    default:         return resourceStore.resources
  }
})

// 根据资源类型选择卡片组件
const cardComponents: Record<string, unknown> = {
  doc: DocCard,
  exercise: ExerciseCard,
  code: CodeCard,
  mindmap: MindmapCard,
  script: ScriptCard,
  infographic: InfoCard,
}
function cardFor(type: string) {
  return cardComponents[type] ?? DocCard
}

// ── 资源类型选择器配置 ────────────────────────
const resourceTypeOptions = [
  { value: 'all',      label: '全部类型', icon: '⚡' },
  { value: 'doc',      label: '知识文档', icon: '📄' },
  { value: 'exercise', label: '练习题',   icon: '📝' },
  { value: 'code',     label: '代码示例', icon: '💻' },
  { value: 'mindmap',  label: '思维导图', icon: '🗺️' },
  { value: 'script',   label: '视频脚本', icon: '🎬' },
]

// 认知风格标签
const cogStyleLabels: Record<string, string> = {
  visual: '视觉型',
  practical: '实践型',
  textual: '文本型',
  analogical: '类比型',
}

// 四类教学资源分区（viewTab === 'all' 时显示）
const resourceSections = computed(() => [
  {
    key: 'understand',
    title: '理解资源',
    desc: '知识图谱 · 信息图 · 知识文档',
    icon: '📖',
    borderColor: '#bfdbfe',
    bgColor: '#eff6ff',
    titleColor: '#1d4ed8',
    items: resourceStore.resources.filter(r => ['doc', 'mindmap', 'infographic'].includes(r.resource_type ?? '')),
  },
  {
    key: 'practice',
    title: '练习资源',
    desc: '标准化试题 · 专项训练',
    icon: '📝',
    borderColor: '#fde68a',
    bgColor: '#fffbeb',
    titleColor: '#b45309',
    items: resourceStore.exerciseResources,
  },
  {
    key: 'experiment',
    title: '实践资源',
    desc: '网络实验 · 代码仿真',
    icon: '🧪',
    borderColor: '#a7f3d0',
    bgColor: '#ecfdf5',
    titleColor: '#065f46',
    items: resourceStore.codeResources,
  },
  {
    key: 'extend',
    title: '拓展资源',
    desc: 'AI教学视频 · 动态讲解',
    icon: '🎬',
    borderColor: '#e0e7ff',
    bgColor: '#f0f4ff',
    titleColor: '#4338ca',
    items: resourceStore.scriptResources,
  },
])


// 诊断推荐列表（模板中不再使用，用类型扮演避免编译报错）
const _diagRecommendList = computed(() => {
  if (!lastDiagnosis.value?.rootCause?.weakKnowledge) return []
  return [
    { icon: '🧪', label: 'TCP实验仿真', type: 'code' as const },
    { icon: '📊', label: '知识信息图', type: 'mindmap' as const },
    { icon: '📄', label: 'RFC原文解析', type: 'doc' as const },
    { icon: '📝', label: '专项练习 10题', type: 'exercise' as const },
  ]
})
void _diagRecommendList

// ── 生成操作 ─────────────────────────────────
async function handleGenerate() {
  if (!knowledgePoint.value.trim() || isGenerating.value) return
  generateError.value = null
  isGenerating.value = true
  try {
    if (selectedType.value === 'all') {
      await resourceStore.generateAll(knowledgePoint.value.trim(), difficulty.value)
      viewTab.value = 'all'
    } else {
      await resourceStore.generateResource(
        knowledgePoint.value.trim(),
        selectedType.value,
        difficulty.value,
      )
      viewTab.value = selectedType.value
    }
  } catch (e: unknown) {
    generateError.value = e instanceof Error ? e.message : '生成失败，请稍后重试'
  } finally {
    isGenerating.value = false
  }
}

// 点击诊断提示快速跳转到生成
function applyDiagnosis(kp: string) {
  knowledgePoint.value = kp
  showGeneratePanel.value = true
}

// 一键全套生成横幅专用知识点
const quickTopic = ref('')
async function handleOneClick() {
  const topic = quickTopic.value.trim() || knowledgePoint.value.trim()
  if (!topic || isGenerating.value) return
  knowledgePoint.value = topic
  quickTopic.value = topic
  generateError.value = null
  isGenerating.value = true
  try {
    await resourceStore.generateAll(topic, difficulty.value)
    viewTab.value = 'all'
  } catch (e: unknown) {
    generateError.value = e instanceof Error ? e.message : '生成失败，请稍后重试'
  } finally {
    isGenerating.value = false
  }
}

onMounted(async () => {
  await resourceStore.loadRecent()
  // 预填知识点：诊断薄弱点 > 画像弱点
  if (!knowledgePoint.value) {
    knowledgePoint.value =
      lastDiagnosis.value?.rootCause?.weakKnowledge ||
      profile.value.weak_points[0] ||
      ''
  }
  // 加载内置教材列表
  try {
    const res = await fetch('/api/v1/kb/books')
    if (res.ok) {
      const data = await res.json()
      builtinBooks.value = data.books || []
    }
  } catch { /* 静默失败 */ }
})
</script>

<template>
  <div class="resources-page">

    <!-- ★ AI 学习驾驶舱 Banner -->
    <div class="cockpit-banner">
      <div class="cockpit-inner">
        <!-- 左侧信息 -->
        <div class="cockpit-left">
          <div class="cockpit-eyebrow">
            <span class="ai-badge">AI</span>
            <span class="cockpit-subtitle">智能学习平台</span>
          </div>
          <h1 class="cockpit-title">AI 学习空间</h1>
          <p class="cockpit-focus" v-if="knowledgePoint || quickSuggestions.length">
            当前专注：<span class="focus-highlight">{{ knowledgePoint || quickSuggestions[0] || '计算机网络核心协议' }}</span>
          </p>
          <div class="cockpit-badges">
            <span v-if="profile.cognitiveStyle" class="badge-glass">
              🧠 {{ cogStyleLabels[profile.cognitiveStyle] || profile.cognitiveStyle }}学习者
            </span>
            <span v-if="profile.weak_points.length" class="badge-glass badge-warn">
              ⚡ {{ profile.weak_points.length }} 个薄弱点
            </span>
            <span class="badge-glass">
              📚 {{ resourceStore.resources.length }} 个学习资源
            </span>
          </div>
        </div>

        <!-- 右侧：AI 诊断玻璃卡 -->
        <div v-if="lastDiagnosis?.rootCause?.weakKnowledge" class="cockpit-diag">
          <div class="diag-glass">
            <div class="diag-header">
              <span class="diag-ai-badge">AI 诊断</span>
              <span class="diag-dot"></span>
            </div>
            <p class="diag-point">{{ lastDiagnosis.rootCause.weakKnowledge }}</p>
            <p v-if="lastDiagnosis.intervention_suggestion" class="diag-suggest">{{ lastDiagnosis.intervention_suggestion }}</p>
            <button class="diag-action" @click="applyDiagnosis(lastDiagnosis!.rootCause!.weakKnowledge)">生成针对性学习资源 →</button>
          </div>
        </div>
      </div>

      <!-- 嵌入式 Tab 导航 -->
      <div class="cockpit-tabs">
        <button class="ctab" :class="{ active: mainTab === 'resources' }" @click="mainTab = 'resources'">
          <svg class="ctab-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/></svg>
          AI 学习空间
        </button>
        <button class="ctab" :class="{ active: mainTab === 'questions' }" @click="mainTab = 'questions'">
          <svg class="ctab-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"/></svg>
          智能题库
        </button>
        <button class="ctab" :class="{ active: mainTab === 'infographic' }" @click="mainTab = 'infographic'">
          <svg class="ctab-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/></svg>
          知识图谱
        </button>
        <button class="ctab" :class="{ active: mainTab === 'pdf' }" @click="mainTab = 'pdf'">
          <svg class="ctab-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4"/></svg>
          知识库管理
        </button>
      </div>
    </div><!-- end cockpit -->

    <!-- 主内容区 -->
    <div class="content-area">

    <!-- 智能题库面板 -->
    <template v-if="mainTab === 'questions'">

      <!-- 题目生成表单 -->
      <div class="ai-card">
        <div class="ai-card-header">
          <div class="ai-icon-wrap ai-icon-purple">
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/></svg>
          </div>
          <div>
            <h3 class="ai-card-title">AI 智能题库</h3>
            <p class="ai-card-sub">精准针对你的薄弱知识点，生成多题型专项训练</p>
          </div>
        </div>

        <!-- 主题输入 -->
        <div>
          <label class="form-label">主题 / 知识点</label>
          <input v-model="qTopic" type="text" placeholder="如：TCP三次握手、OSI七层模型、BGP路由协议..." class="ai-input" @keyup.enter="handleGenerateQuestions" />
        </div>

        <!-- 题型多选 -->
        <div>
          <label class="form-label">题型（可多选）</label>
          <div class="flex flex-wrap gap-2">
            <button v-for="opt in questionTypeOptions" :key="opt.value"
              class="type-chip" :class="qSelectedTypes.includes(opt.value) ? 'type-chip-active-purple' : ''"
              @click="qSelectedTypes.includes(opt.value) ? qSelectedTypes.splice(qSelectedTypes.indexOf(opt.value), 1) : qSelectedTypes.push(opt.value)">
              {{ opt.icon }} {{ opt.label }}
            </button>
          </div>
        </div>

        <!-- 数量 + 难度 -->
        <div class="flex flex-wrap gap-6">
          <div class="flex-1 min-w-[140px]">
            <label class="block text-xs text-gray-500 mb-1.5">
              每种题型数量 <span class="font-semibold text-violet-500">{{ qCount }}</span> 题
            </label>
            <input v-model.number="qCount" type="range" min="1" max="20" step="1"
              class="w-full accent-violet-500 cursor-pointer" />
            <div class="flex justify-between text-xs text-gray-400 mt-0.5">
              <span>1题</span><span>10题</span><span>20题</span>
            </div>
          </div>
          <div class="w-44 shrink-0">
            <label class="block text-xs text-gray-500 mb-1.5">
              难度 <span class="font-semibold text-violet-500">{{ qDifficulty }}</span>/5
            </label>
            <input v-model.number="qDifficulty" type="range" min="1" max="5" step="1"
              class="w-full accent-violet-500 cursor-pointer" />
            <div class="flex justify-between text-xs text-gray-400 mt-0.5">
              <span>入门</span><span>中级</span><span>深入</span>
            </div>
          </div>
        </div>

        <!-- 生成按鈕 -->
        <div class="flex items-center gap-3 flex-wrap">
          <button
            class="flex items-center gap-2 px-5 py-2 bg-violet-600 hover:bg-violet-700 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-medium rounded-lg transition-colors"
            :disabled="!qTopic.trim() || qIsGenerating || !qSelectedTypes.length"
            @click="handleGenerateQuestions"
          >
            <svg v-if="!qIsGenerating" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
            </svg>
            <svg v-else class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
            </svg>
            {{ qIsGenerating ? '生成中...' : `生成 ${qSelectedTypes.length} 种题型 × ${qCount} 题` }}
          </button>
          <p v-if="qError" class="text-xs text-red-500">❌ {{ qError }}</p>
        </div>
      </div>

      <!-- 题目结果展示 -->
      <div v-if="qTotalCount > 0" class="card space-y-4">
        <div class="flex items-center justify-between flex-wrap gap-3">
          <h3 class="text-sm font-semibold text-gray-700">
            生成结果：共 <span class="text-violet-600 font-bold">{{ qTotalCount }}</span> 题
          </h3>
          <!-- 导出按鈕组 -->
          <div class="flex items-center gap-2">
            <button
              class="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg transition-colors border"
              :class="qExporting === 'docx' ? 'bg-blue-100 text-blue-600 border-blue-300' : 'border-blue-300 text-blue-600 hover:bg-blue-50'"
              :disabled="!!qExporting"
              @click="handleExportQuestions('docx')"
            >
              <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
              </svg>
              {{ qExporting === 'docx' ? '导出中...' : '导出 Word' }}
            </button>
            <button
              class="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg transition-colors border"
              :class="qExporting === 'xlsx' ? 'bg-green-100 text-green-600 border-green-300' : 'border-green-300 text-green-600 hover:bg-green-50'"
              :disabled="!!qExporting"
              @click="handleExportQuestions('xlsx')"
            >
              <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
              </svg>
              {{ qExporting === 'xlsx' ? '导出中...' : '导出 Excel' }}
            </button>
          </div>
        </div>

        <!-- 题目分组展示 -->
        <div v-for="(items, qtype) in qResults" :key="qtype" class="space-y-3">
          <div class="flex items-center gap-2 mt-2">
            <span class="text-xs font-bold text-violet-600 bg-violet-50 px-2.5 py-1 rounded-full">
              {{ qTypeLabels[qtype] || qtype }} ({{ items.length }} 题)
            </span>
          </div>
          <div
            v-for="(q, idx) in (items as Record<string, unknown>[])"
            :key="idx"
            class="bg-gray-50 rounded-xl p-4 border border-gray-100"
          >
            <p class="text-sm font-medium text-gray-800 mb-2">
              Q{{ idx + 1 }}. {{ (q as Record<string, unknown>).question || (q as Record<string, unknown>).stem }}
            </p>
            <!-- 选项（选择题） -->
            <div v-if="(q as Record<string, unknown>).options" class="space-y-1 mb-2">
              <p
                v-for="(opt, oi) in (q as Record<string, unknown>).options as string[]"
                :key="oi"
                class="text-xs text-gray-600 flex items-start gap-1"
              >
                <span class="font-medium text-gray-500 shrink-0">{{ String.fromCharCode(65 + oi) }}.</span>
                {{ opt }}
              </p>
            </div>
            <!-- 参考答案 -->
            <div class="text-xs text-emerald-600 bg-emerald-50 rounded-lg px-3 py-1.5">
              参考答案：{{ (q as Record<string, unknown>).answer || (q as Record<string, unknown>).reference_answer || (q as Record<string, unknown>).sample_answer }}
            </div>
          </div>
        </div>
      </div>

      <!-- 空状态提示 -->
      <div v-else-if="!qIsGenerating" class="text-center py-14 text-gray-400">
        <div class="text-5xl mb-3">📝</div>
        <p class="text-sm font-medium">输入主题并选择题型，点击「生成」开始</p>
      </div>
      <div v-else class="flex items-center justify-center py-12 gap-3 text-violet-500">
        <svg class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
        </svg>
        <span class="text-sm font-medium">AI 正在生成题目...</span>
      </div>
    </template>

    <!-- 知识图谱面板 -->
    <template v-if="mainTab === 'infographic'">
      <div class="ai-card space-y-4">
        <div class="ai-card-header">
          <div class="ai-icon-wrap ai-icon-teal">
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/></svg>
          </div>
          <div>
            <h3 class="ai-card-title">AI 知识图谱生成</h3>
            <p class="ai-card-sub">可视化知识结构 LLM 结构化输出 + SVG 动态渲染</p>
          </div>
        </div>

        <!-- 主题输入 -->
        <div class="flex flex-wrap gap-4">
          <div class="flex-1 min-w-[200px]">
            <label class="form-label">主题</label>
            <input v-model="igTopic" type="text" placeholder="如：TCP三次握手、OSPF协议工作流程..."
              class="ai-input"
              @keyup.enter="handleGenerateInfograhic" />
          </div>
          <div class="w-52 shrink-0">
            <label class="form-label">图表类型</label>
            <div class="flex gap-2 flex-wrap">
              <button v-for="s in igStyles" :key="s.value"
                class="type-chip"
                :class="igStyle === s.value ? 'type-chip-active-teal' : ''"
                @click="igStyle = s.value">
                {{ s.icon }} {{ s.label }}
              </button>
            </div>
          </div>
        </div>

        <div class="flex items-center gap-3">
          <button class="ai-btn ai-btn-teal"
            :disabled="!igTopic.trim() || igLoading"
            @click="handleGenerateInfograhic">
            <svg v-if="igLoading" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
            {{ igLoading ? 'AI 正在构建知识图谱...' : '生成知识图谱' }}
          </button>
          <p v-if="igError" class="text-xs text-red-500">{{ igError }}</p>
        </div>
      </div>

      <!-- SVG 渲染结果 -->
      <div v-if="igResult" class="ai-card">
        <div class="flex items-center justify-between mb-4">
          <div>
            <h3 class="text-sm font-semibold text-gray-800">{{ igResult.title }}</h3>
            <p class="text-xs text-gray-400 mt-0.5">{{ igResult.summary }}</p>
          </div>
          <span class="text-xs px-2.5 py-1 rounded-full font-medium"
            :class="igResult.source === 'sensenova' ? 'bg-ai-purple-50 text-ai-purple border border-ai-purple/20' : 'bg-ai-teal-50 text-ai-teal border border-ai-teal/20'">
            {{ igResult.source === 'sensenova' ? 'SenseNova-U1' : 'LLM 生成' }}
          </span>
        </div>

        <!-- SenseNova 图片模式 -->
        <img v-if="igResult.style === 'image'"
          :src="igResult.nodes[0]?.description"
          :alt="igResult.title"
          class="w-full rounded-xl border border-gray-100" />

        <!-- SVG 图表渲染 -->
        <div v-else class="overflow-x-auto">
          <svg viewBox="0 0 720 480" class="w-full max-h-[480px] border border-gray-100 rounded-xl bg-gradient-to-br from-slate-50 to-blue-50/30" style="min-width:480px">
            <!-- 连线 -->
            <g v-for="edge in igResult.edges" :key="edge.from_id + edge.to_id">
              <template v-if="igNodeById(edge.from_id) && igNodeById(edge.to_id)">
                <line :x1="igNodeById(edge.from_id)!.x" :y1="igNodeById(edge.from_id)!.y" :x2="igNodeById(edge.to_id)!.x" :y2="igNodeById(edge.to_id)!.y" stroke="#1677FF" stroke-width="1.5" stroke-opacity="0.3" stroke-dasharray="5,4" />
                <text v-if="edge.label" :x="((igNodeById(edge.from_id)!.x + igNodeById(edge.to_id)!.x) / 2)" :y="((igNodeById(edge.from_id)!.y + igNodeById(edge.to_id)!.y) / 2) - 4" text-anchor="middle" font-size="9" fill="#94a3b8">{{ edge.label }}</text>
              </template>
            </g>
            <!-- 节点 -->
            <g v-for="node in igLayoutNodes" :key="node.id">
              <circle :cx="node.x" :cy="node.y" :r="node.type === 'root' ? 38 : 28" :fill="node.type === 'root' ? '#1677FF' : '#E8F3FF'" :stroke="node.type === 'root' ? '#0958D9' : '#1677FF'" stroke-width="1.5" />
              <text :x="node.x" :y="node.y - 4" text-anchor="middle" font-size="16">{{ node.icon }}</text>
              <text :x="node.x" :y="node.y + 12" text-anchor="middle" font-size="9" :fill="node.type === 'root' ? 'white' : '#1677FF'" font-weight="600">{{ node.label }}</text>
              <text v-if="node.description && node.type !== 'root'" :x="node.x" :y="node.y + 48" text-anchor="middle" font-size="8" fill="#64748b">{{ node.description.length > 14 ? node.description.slice(0, 14) + '...' : node.description }}</text>
            </g>
          </svg>
        </div>

        <!-- 节点列表 -->
        <div class="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-2">
          <div v-for="n in igResult.nodes" :key="n.id"
            class="flex items-start gap-2 text-xs p-2.5 rounded-lg bg-ai-blue-50 border border-ai-blue-100">
            <span class="text-base shrink-0">{{ n.icon }}</span>
            <div>
              <span class="font-semibold text-gray-700">{{ n.label }}</span>
              <span v-if="n.description && igResult?.style !== 'image'" class="text-gray-400 ml-1">{{ n.description }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-else-if="!igLoading" class="ai-empty-state">
        <div class="empty-icon-wrap"><svg class="w-10 h-10 text-ai-teal/40" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/></svg></div>
        <p class="empty-title">知识图谱待生成</p>
        <p class="empty-sub">AI 将根据主题生成可交互的知识结构可视化图</p>
      </div>
    </template>

    <!-- 知识库管理面板 -->
    <template v-if="mainTab === 'pdf'">
      <div class="ai-card">
        <div class="ai-card-header">
          <div class="ai-icon-wrap ai-icon-blue">
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4"/></svg>
          </div>
          <div>
            <h3 class="ai-card-title">知识库管理</h3>
            <p class="ai-card-sub">上传 PDF 构建私有知识沉淀，AI 回答时自动检索引用</p>
          </div>
        </div>

        <!-- 拖拽上传区 -->
        <div
          class="pdf-drop-zone"
          :class="{ dragging: pdfDragging, hasFile: !!pdfFileName }"
          @dragover.prevent="pdfDragging = true"
          @dragleave="pdfDragging = false"
          @drop="handlePdfDrop"
          @click="($refs.pdfInput as HTMLInputElement)?.click()"
        >
          <input ref="pdfInput" type="file" accept=".pdf" style="display:none" @change="handlePdfFileChange" />
          <div v-if="pdfFileName" class="pdf-selected">
            <span class="text-2xl">📄</span>
            <div>
              <div class="font-semibold text-gray-800 text-sm">{{ pdfFileName }}</div>
              <div class="text-xs text-gray-500">已选择，点击重选或拖拽新文件</div>
            </div>
          </div>
          <div v-else>
            <div class="text-4xl mb-2">📤</div>
            <div class="text-sm font-semibold text-gray-600">拖拽 PDF 文件到此处</div>
            <div class="text-xs text-gray-400 mt-1">或点击选择文件（最大 50MB）</div>
          </div>
        </div>

        <!-- 设置项 -->
        <div v-if="pdfFileName" class="mt-4 space-y-3">
          <div>
            <label class="form-label">来源名称（用于检索标注）</label>
            <input v-model="pdfSourceName" type="text" class="ai-input" placeholder="如：计算机网络第7版" />
          </div>
          <div class="flex items-center gap-2">
            <input id="use-mineru" v-model="pdfUseMineru" type="checkbox" class="accent-ai-blue" />
            <label for="use-mineru" class="text-xs text-gray-600">启用 MinerU 高质量解析（需服务器安装 magic-pdf）</label>
          </div>
          <button class="ai-btn ai-btn-primary w-full justify-center" :disabled="pdfUploading" @click="handlePdfUpload">
            <svg v-if="pdfUploading" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
            {{ pdfUploading ? '解析中，请稍候...' : '开始解析并入知识库' }}
          </button>
        </div>

        <!-- 结果提示 -->
        <div v-if="pdfResult" class="mt-4 p-3 rounded-xl" :class="pdfResult.success ? 'bg-ai-teal-50 border border-ai-teal-200' : 'bg-red-50 border border-red-200'">
          <div class="flex items-start gap-2">
            <span>{{ pdfResult.success ? '✅' : '❌' }}</span>
            <div>
              <p class="text-sm font-medium" :class="pdfResult.success ? 'text-ai-teal' : 'text-red-700'">{{ pdfResult.message }}</p>
              <p v-if="pdfResult.chunks_added" class="text-xs text-gray-500 mt-1">共创建 {{ pdfResult.chunks_added }} 个知识块</p>
            </div>
          </div>
        </div>

        <!-- 内置教材列表 -->
        <div class="mt-6">
          <h4 class="text-sm font-semibold text-gray-700 mb-3">📖 内置教材库</h4>
          <div class="space-y-2">
            <div v-for="book in builtinBooks" :key="book.id" class="flex items-center gap-3 p-3 rounded-xl border border-gray-100 hover:border-ai-blue/30 hover:bg-ai-blue-50 transition-all">
              <div class="text-2xl">📖</div>
              <div class="flex-1">
                <div class="font-semibold text-sm text-gray-800">{{ book.title }}</div>
                <div class="text-xs text-gray-500">{{ book.author }}</div>
                <div class="flex flex-wrap gap-1 mt-1">
                  <span v-for="tag in book.tags" :key="tag" class="text-xs bg-ai-blue-50 text-ai-blue px-2 py-0.5 rounded-full border border-ai-blue/15">{{ tag }}</span>
                </div>
              </div>
              <span class="text-xs bg-ai-teal-50 text-ai-teal px-2 py-1 rounded-full border border-ai-teal/20 font-medium">内置</span>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- AI 学习空间面板 -->
    <template v-else>

    <!-- 一键全套生成横幅 -->
    <div class="oneclick-banner" v-if="knowledgePoint.trim() || quickSuggestions.length">
      <div class="ocb-left">
        <div class="ocb-ai-icon">
          <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="white"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.346.35A3.5 3.5 0 0112 18.5a3.5 3.5 0 01-2.47-1.026l-.346-.349z"/></svg>
        </div>
        <div>
          <div class="ocb-title">AI Tutor 为你生成 5 种定制学习材料</div>
          <div class="ocb-sub">知识文档 · 练习题 · 代码示例 · 思维导图 · 视频脚本</div>
        </div>
      </div>
      <div class="ocb-right">
        <input v-model="quickTopic" placeholder="输入知识点，如 TCP三次握手" class="ocb-input" @keyup.enter="handleOneClick" />
        <button class="ocb-btn" :disabled="isGenerating || (!quickTopic.trim() && !knowledgePoint.trim())" @click="handleOneClick">
          <span v-if="!isGenerating">⚡ 立即生成全套</span>
          <span v-else class="flex items-center gap-1.5">
            <svg class="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
            生成中...
          </span>
        </button>
      </div>
    </div>

    <!-- ★ 知识库上传卡片 -->
    <div class="ai-card">
      <div class="flex items-center justify-between mb-3">
        <div class="flex items-center gap-2">
          <div class="ai-icon-wrap ai-icon-teal" style="width:28px;height:28px;border-radius:8px">
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/></svg>
          </div>
          <h3 class="text-sm font-semibold text-gray-800">上传知识材料到知识库</h3>
        </div>
        <button class="text-xs text-gray-400 hover:text-gray-600 transition-colors" @click="showUploadPanel = !showUploadPanel">
          {{ showUploadPanel ? '收起 ▲' : '展开 ▼' }}
        </button>
      </div>
      <p class="text-xs text-gray-400 mb-3">AI 回答时将自动检索并引用你上传的内容</p>
      <template v-if="showUploadPanel">
        <div class="mb-3">
          <label class="form-label">来源名称（如文档名）</label>
          <input v-model="uploadSource" type="text" placeholder="如: BGP笔记.md" class="ai-input" />
        </div>
        <div class="mb-3">
          <label class="form-label">粘贴文本内容</label>
          <textarea v-model="uploadContent" rows="5" placeholder="将文本或 Markdown 内容粘贴到这里..." class="ai-input resize-y" />
        </div>
        <div class="flex items-center gap-4 flex-wrap">
          <label class="flex items-center gap-1.5 text-xs text-gray-600 cursor-pointer">
            <input type="checkbox" v-model="uploadIsMarkdown" class="accent-ai-teal" />
            Markdown 格式（按标题分割）
          </label>
          <button :disabled="isUploading || !uploadContent.trim()"
            class="ai-btn ai-btn-teal"
            style="padding: 6px 16px; font-size: 12px"
            @click="handleUpload">
            {{ isUploading ? '处理中...' : '入库' }}
          </button>
        </div>
        <div v-if="uploadResult" class="mt-3 text-xs px-3 py-2 rounded-lg"
          :class="uploadResult.success ? 'bg-ai-teal-50 text-ai-teal border border-ai-teal/20' : 'bg-red-50 text-red-600'">
          <span v-if="uploadResult.success">✅ {{ uploadResult.message }}（{{ uploadResult.chunks_added }} 个块）</span>
          <span v-else>❌ {{ uploadResult.message }}</span>
        </div>
      </template>
    </div>


    <!-- AI 诊断联动提示 -->
    <div v-if="lastDiagnosis?.rootCause?.weakKnowledge" class="ai-card" style="background: linear-gradient(135deg, #E8F3FF, #F5EEFF); border-color: #1677FF30">
      <div class="flex items-center gap-3">
        <div class="ai-icon-wrap ai-icon-blue" style="width:36px;height:36px;flex-shrink:0">
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.346.35A3.5 3.5 0 0112 18.5a3.5 3.5 0 01-2.47-1.026l-.346-.349z"/></svg>
        </div>
        <div class="flex-1 min-w-0">
          <p class="text-xs font-bold mb-0.5" style="color:#1677FF">🧠 AI 诊断发现薄弱点</p>
          <p class="text-sm font-bold text-gray-900">{{ lastDiagnosis.rootCause.weakKnowledge }}</p>
          <p v-if="lastDiagnosis.intervention_suggestion" class="text-xs text-gray-500 mt-0.5 line-clamp-1">{{ lastDiagnosis.intervention_suggestion }}</p>
        </div>
        <button class="ai-btn ai-btn-primary" style="font-size:12px;padding:7px 14px;flex-shrink:0"
          @click="applyDiagnosis(lastDiagnosis!.rootCause!.weakKnowledge)">立即生成资源</button>
      </div>
    </div>

    <!-- 资源生成面板 -->
    <div class="ai-card">
      <div class="flex items-center justify-between mb-4">
        <div class="flex items-center gap-2">
          <div class="ai-icon-wrap ai-icon-blue" style="width:28px;height:28px;border-radius:8px">
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
          </div>
          <h3 class="text-sm font-semibold text-gray-800">生成学习资源</h3>
        </div>
        <button class="text-xs text-gray-400 hover:text-gray-600 transition-colors" @click="showGeneratePanel = !showGeneratePanel">
          {{ showGeneratePanel ? '收起 ▲' : '展开 ▼' }}
        </button>
      </div>

      <template v-if="showGeneratePanel">
        <!-- 知识点输入 -->
        <div class="mb-4">
          <label class="form-label">知识点</label>
          <input v-model="knowledgePoint" type="text" placeholder="如：TCP三次握手、OSI七层模型、HTTP请求流程..." class="ai-input" @keyup.enter="handleGenerate" />
          <div v-if="quickSuggestions.length" class="flex flex-wrap gap-1.5 mt-2 items-center">
            <span class="text-xs text-gray-400">AI 推荐：</span>
            <button v-for="s in quickSuggestions" :key="s"
              class="text-xs bg-ai-blue-50 hover:bg-ai-blue-100 text-ai-blue px-2.5 py-0.5 rounded-full border border-ai-blue/15 transition-colors"
              @click="knowledgePoint = s">{{ s }}</button>
          </div>
        </div>

        <!-- 类型 + 难度 -->
        <div class="flex flex-wrap gap-5 mb-4">
          <div class="flex-1 min-w-0">
            <label class="form-label">资源类型</label>
            <div class="flex flex-wrap gap-1.5">
              <button v-for="opt in resourceTypeOptions" :key="opt.value"
                class="type-chip" :class="selectedType === opt.value ? 'type-chip-active' : ''"
                @click="selectedType = (opt.value as ResourceType | 'all')">
                {{ opt.icon }} {{ opt.label }}
              </button>
            </div>
          </div>
          <div class="w-44 shrink-0">
            <label class="form-label">难度 <span class="font-bold" style="color:var(--ai-blue)">{{ difficulty }}</span>/5</label>
            <input v-model.number="difficulty" type="range" min="1" max="5" step="1" class="ai-slider" />
            <div class="slider-labels"><span>入门</span><span>中级</span><span>深入</span></div>
          </div>
        </div>

        <!-- 生成按鈕 -->
        <div class="flex items-center gap-3 flex-wrap">
          <button class="ai-btn ai-btn-primary" :disabled="!knowledgePoint.trim() || isGenerating" @click="handleGenerate">
            <svg v-if="!isGenerating" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
            <svg v-else class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
            {{ isGenerating ? 'AI 正在构建学习方案...' : (selectedType === 'all' ? '一键生成全部类型' : '生成资源') }}
          </button>
          <p v-if="generateError" class="text-xs text-red-500">{{ generateError }}</p>
        </div>
      </template>
    </div>
    
    <!-- 资源展示区 -->
    <div class="ai-card">
      <!-- 生成进度条 -->
      <GenerationProgress />
    
      <!-- Pill Tab 导航 -->
      <div class="pill-tabs">
        <button v-for="tab in tabs" :key="tab.key" class="pill-tab" :class="{ 'pill-tab-active': viewTab === tab.key }" @click="viewTab = tab.key">
          {{ tab.icon }} {{ tab.label }}
          <span v-if="tab.count > 0" class="pill-tab-count">{{ tab.count }}</span>
        </button>
      </div>
        
      <!-- 加载状态 -->
      <div v-if="resourceStore.loading && resourceStore.resources.length === 0"
        class="flex items-center justify-center py-12 text-sm gap-2" style="color: var(--ai-blue)">
        <svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
        AI 正在加载学习资源...
      </div>
    
      <!-- 四分类分区展示（viewTab === 'all'） -->
      <template v-else-if="viewTab === 'all'">
        <template v-if="resourceStore.resources.length > 0">
          <div
            v-for="sec in resourceSections.filter(s => s.items.length > 0)"
            :key="sec.key"
            class="resource-section-block"
            :style="{ borderLeftColor: sec.borderColor }"
          >
            <!-- 分区标题栏 -->
            <div class="rsb-header" :style="{ background: sec.bgColor }">
              <span class="rsb-icon">{{ sec.icon }}</span>
              <div class="rsb-meta">
                <span class="rsb-title" :style="{ color: sec.titleColor }">{{ sec.title }}</span>
                <span class="rsb-desc">{{ sec.desc }}</span>
              </div>
              <span class="rsb-count" :style="{ background: sec.borderColor, color: sec.titleColor }">
                {{ sec.items.length }} 个
              </span>
            </div>
            <!-- 分区内卡片网格 -->
            <div class="rsb-grid">
              <component
                :is="cardFor(res.resource_type ?? 'doc')"
                v-for="res in sec.items"
                :key="res.resource_id ?? res.title"
                :resource="res"
              />
            </div>
          </div>
    
          <!-- 全部分区都为空时显示提示 -->
          <div v-if="resourceSections.every(s => s.items.length === 0)" class="text-center py-14 text-gray-400">
            <p class="text-sm font-medium">尚无学习资源</p>
            <p class="text-xs mt-1">在上方输入知识点并点击“生成资源”即可开始</p>
          </div>
        </template>
    
        <!-- 空状态 -->
        <div v-else class="text-center py-14 text-gray-400">
          <div class="empty-resource-icon">
            <svg class="w-12 h-12 mx-auto mb-3 opacity-20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"/>
            </svg>
          </div>
          <p class="text-sm font-medium">尚无学习资源</p>
          <p class="text-xs mt-1 text-gray-400">在上方输入知识点并点击“生成资源”即可开始</p>
          <button
            v-if="knowledgePoint.trim()"
            class="mt-4 text-xs bg-indigo-50 hover:bg-indigo-100 text-indigo-600 px-4 py-1.5 rounded-lg transition-colors"
            @click="handleGenerate"
          >
            立即生成「{{ knowledgePoint }}」相关资源
          </button>
        </div>
      </template>
    
      <!-- 单类平铺展示（viewTab !== 'all'） -->
      <template v-else>
        <div
          v-if="displayedResources.length > 0"
          class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3"
        >
          <component
            :is="cardFor(res.resource_type ?? 'doc')"
            v-for="res in displayedResources"
            :key="res.resource_id ?? res.title"
            :resource="res"
          />
        </div>
        <div v-else class="text-center py-14 text-gray-400">
          <p class="text-sm font-medium">暂无该类型资源</p>
          <button
            v-if="knowledgePoint.trim()"
            class="mt-3 text-xs bg-indigo-50 hover:bg-indigo-100 text-indigo-600 px-4 py-1.5 rounded-lg transition-colors"
            @click="handleGenerate"
          >
            生成该类型资源
          </button>
        </div>
      </template>
    </div>

    </template><!-- end v-else resources -->

    </div><!-- end content-area -->
  </div><!-- end resources-page -->
</template>

<style scoped>
/* ===== AI 学习空间 - 全局设计系统 ===== */

/* 页面根容器 */
.resources-page {
  display: flex;
  flex-direction: column;
  gap: 0;
  min-height: 0;
}

/* 驾驶舱 Banner */
.cockpit-banner {
  background: linear-gradient(135deg, #0D1B2A 0%, #1e3a8a 55%, #3b0764 100%);
  border-radius: 20px;
  padding: 28px 28px 0;
  margin-bottom: 20px;
  position: relative;
  overflow: hidden;
}
.cockpit-banner::before {
  content: '';
  position: absolute;
  top: -60px; right: -60px;
  width: 240px; height: 240px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(22,119,255,0.15) 0%, transparent 70%);
  pointer-events: none;
}

.cockpit-inner {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24px;
  flex-wrap: wrap;
  margin-bottom: 24px;
}

.cockpit-left { flex: 1; min-width: 260px; }

.cockpit-eyebrow {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.ai-badge {
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 1px;
  color: white;
  background: linear-gradient(135deg, #1677FF, #722ED1);
  padding: 2px 8px;
  border-radius: 6px;
}
.cockpit-subtitle {
  font-size: 12px;
  color: rgba(255,255,255,0.5);
  font-weight: 500;
}
.cockpit-title {
  font-size: 28px;
  font-weight: 800;
  color: white;
  letter-spacing: -0.5px;
  line-height: 1.2;
  margin: 0 0 8px;
}
.cockpit-focus {
  font-size: 13px;
  color: rgba(255,255,255,0.65);
  margin-bottom: 14px;
}
.focus-highlight {
  color: #64cfff;
  font-weight: 600;
}
.cockpit-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.badge-glass {
  font-size: 12px;
  color: rgba(255,255,255,0.85);
  background: rgba(255,255,255,0.1);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255,255,255,0.2);
  padding: 4px 12px;
  border-radius: 999px;
}
.badge-glass.badge-warn {
  background: rgba(251,191,36,0.15);
  border-color: rgba(251,191,36,0.3);
  color: #fde68a;
}

/* 诊断玻璃卡 */
.cockpit-diag { flex-shrink: 0; width: 280px; }
.diag-glass {
  background: rgba(255,255,255,0.08);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255,255,255,0.15);
  border-radius: 16px;
  padding: 16px;
}
.diag-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}
.diag-ai-badge {
  font-size: 10px;
  font-weight: 700;
  background: linear-gradient(135deg, #1677FF, #722ED1);
  color: white;
  padding: 2px 8px;
  border-radius: 4px;
  letter-spacing: 0.5px;
}
.diag-dot {
  width: 6px; height: 6px;
  border-radius: 50%;
  background: #4ade80;
  animation: diag-pulse 2s ease infinite;
}
@keyframes diag-pulse {
  0%,100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(1.3); }
}
.diag-point {
  font-size: 14px;
  font-weight: 700;
  color: white;
  margin: 0 0 6px;
}
.diag-suggest {
  font-size: 11px;
  color: rgba(255,255,255,0.55);
  margin: 0 0 12px;
  line-height: 1.5;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}
.diag-action {
  width: 100%;
  padding: 8px 12px;
  background: linear-gradient(135deg, #1677FF, #722ED1);
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s;
}
.diag-action:hover { opacity: 0.9; }

/* 嵌入式 Tab 导航 */
.cockpit-tabs {
  display: flex;
  gap: 4px;
  padding: 4px;
  background: rgba(255,255,255,0.06);
  border-radius: 14px 14px 0 0;
  margin: 0 -4px;
}
.ctab {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  padding: 11px 16px;
  border-radius: 10px;
  border: none;
  background: transparent;
  color: rgba(255,255,255,0.5);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}
.ctab:hover { background: rgba(255,255,255,0.08); color: rgba(255,255,255,0.85); }
.ctab.active {
  background: white;
  color: #1677FF;
  font-weight: 700;
  box-shadow: 0 2px 12px rgba(0,0,0,0.2);
}
.ctab-icon { width: 16px; height: 16px; flex-shrink: 0; }

/* 主内容区 */
.content-area {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* ===== AI 卡片基础样式 ===== */
.ai-card {
  background: white;
  border: 1px solid #e8eef8;
  border-radius: 16px;
  padding: 22px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.04);
  transition: box-shadow 0.2s;
}
.ai-card:hover { box-shadow: 0 4px 20px rgba(0,0,0,0.07); }

.ai-card-header {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  margin-bottom: 18px;
}
.ai-card-title {
  font-size: 16px;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 3px;
}
.ai-card-sub {
  font-size: 12px;
  color: #64748b;
  margin: 0;
}

/* AI 图标容器 */
.ai-icon-wrap {
  width: 42px; height: 42px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: white;
}
.ai-icon-blue  { background: linear-gradient(135deg, #1677FF, #0958D9); }
.ai-icon-teal  { background: linear-gradient(135deg, #00C2A8, #00A38D); }
.ai-icon-purple{ background: linear-gradient(135deg, #722ED1, #531DAB); }

/* ===== 一键生成横幅 ===== */
.oneclick-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 18px 24px;
  border-radius: 16px;
  background: linear-gradient(135deg, #1e40af 0%, #1e3a8a 50%, #4c1d95 100%);
  box-shadow: 0 4px 20px rgba(22,119,255,0.25);
  flex-wrap: wrap;
}
.ocb-left { display: flex; align-items: center; gap: 14px; }
.ocb-ai-icon {
  width: 40px; height: 40px;
  border-radius: 12px;
  background: rgba(255,255,255,0.12);
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.ocb-title { font-size: 15px; font-weight: 800; color: white; }
.ocb-sub { font-size: 11px; color: rgba(255,255,255,0.65); margin-top: 2px; }
.ocb-right {
  display: flex; align-items: center; gap: 10px;
  flex: 1; justify-content: flex-end; min-width: 0; flex-wrap: wrap;
}
.ocb-input {
  flex: 1; min-width: 160px; max-width: 280px;
  padding: 9px 14px;
  border-radius: 10px;
  border: 1.5px solid rgba(255,255,255,0.25);
  background: rgba(255,255,255,0.1);
  color: white; font-size: 13px; outline: none;
  backdrop-filter: blur(4px);
}
.ocb-input::placeholder { color: rgba(255,255,255,0.4); }
.ocb-input:focus { border-color: rgba(255,255,255,0.6); background: rgba(255,255,255,0.18); }
.ocb-btn {
  padding: 9px 20px; border-radius: 10px; border: none;
  background: linear-gradient(135deg, #00C2A8, #1677FF);
  color: white; font-size: 13px; font-weight: 700;
  cursor: pointer; transition: all 0.2s;
  box-shadow: 0 3px 12px rgba(0,194,168,0.35);
  white-space: nowrap; display: flex; align-items: center; gap: 6px;
}
.ocb-btn:hover:not(:disabled) { transform: translateY(-1px); opacity: 0.92; }
.ocb-btn:disabled { opacity: 0.5; cursor: not-allowed; }

/* ===== 表单元素 ===== */
.form-label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: #475569;
  margin-bottom: 6px;
  letter-spacing: 0.2px;
}
.ai-input {
  width: 100%;
  font-size: 13px;
  border: 1.5px solid #e2e8f0;
  border-radius: 10px;
  padding: 9px 13px;
  outline: none;
  transition: all 0.2s;
  background: #fafbfc;
  color: #1e293b;
}
.ai-input:focus {
  border-color: #1677FF;
  background: white;
  box-shadow: 0 0 0 3px rgba(22,119,255,0.08);
}
.ai-slider {
  width: 100%;
  accent-color: #1677FF;
  cursor: pointer;
  height: 4px;
}
.slider-labels {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: #94a3b8;
  margin-top: 3px;
}

/* ===== 类型选择 Chip ===== */
.type-chip {
  font-size: 12px;
  padding: 6px 13px;
  border-radius: 999px;
  border: 1.5px solid #e2e8f0;
  background: white;
  color: #64748b;
  cursor: pointer;
  transition: all 0.18s;
  font-weight: 500;
}
.type-chip:hover { border-color: #1677FF; color: #1677FF; background: #E8F3FF; }
.type-chip-active {
  border-color: #1677FF;
  background: #E8F3FF;
  color: #1677FF;
  font-weight: 600;
}
.type-chip-active-purple {
  border-color: #722ED1;
  background: #F5EEFF;
  color: #722ED1;
  font-weight: 600;
}
.type-chip-active-teal {
  border-color: #00C2A8;
  background: #E6FBF8;
  color: #00A38D;
  font-weight: 600;
}

/* ===== AI 按钮系统 ===== */
.ai-btn {
  display: inline-flex; align-items: center; gap: 7px;
  padding: 9px 20px;
  border-radius: 10px;
  border: none;
  font-size: 13px; font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}
.ai-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.ai-btn-primary {
  background: linear-gradient(135deg, #1677FF, #722ED1);
  color: white;
  box-shadow: 0 3px 12px rgba(22,119,255,0.3);
}
.ai-btn-primary:hover:not(:disabled) { box-shadow: 0 5px 18px rgba(22,119,255,0.45); transform: translateY(-1px); }
.ai-btn-teal {
  background: linear-gradient(135deg, #00C2A8, #00A38D);
  color: white;
  box-shadow: 0 3px 12px rgba(0,194,168,0.3);
}
.ai-btn-teal:hover:not(:disabled) { opacity: 0.9; transform: translateY(-1px); }
.ai-btn-outline-blue {
  background: #E8F3FF; color: #1677FF;
  border: 1.5px solid #1677FF;
}
.ai-btn-outline-blue:hover:not(:disabled) { background: #1677FF; color: white; }
.ai-btn-outline-teal {
  background: #E6FBF8; color: #00A38D;
  border: 1.5px solid #00C2A8;
}
.ai-btn-outline-teal:hover:not(:disabled) { background: #00C2A8; color: white; }

/* ===== Pill Tab 导航（资源展示区）===== */
.pill-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 16px;
  padding-bottom: 14px;
  border-bottom: 1px solid #f1f5f9;
}
.pill-tab {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 5px 14px;
  border-radius: 999px;
  border: 1.5px solid #e2e8f0;
  background: white;
  font-size: 12px; font-weight: 500; color: #64748b;
  cursor: pointer; transition: all 0.18s;
}
.pill-tab:hover { border-color: #1677FF; color: #1677FF; }
.pill-tab-active {
  background: #1677FF; color: white;
  border-color: #1677FF;
  font-weight: 700;
  box-shadow: 0 2px 8px rgba(22,119,255,0.3);
}
.pill-tab-count {
  font-size: 10px; font-weight: 700;
  background: rgba(255,255,255,0.25);
  padding: 1px 6px; border-radius: 999px;
}
.pill-tab:not(.pill-tab-active) .pill-tab-count {
  background: #f1f5f9; color: #64748b;
}

/* ===== 空状态 ===== */
.ai-empty-state {
  text-align: center;
  padding: 52px 20px;
}
.empty-icon-wrap {
  width: 72px; height: 72px;
  border-radius: 50%;
  background: linear-gradient(135deg, #E8F3FF, #F5EEFF);
  display: flex; align-items: center; justify-content: center;
  margin: 0 auto 16px;
}
.empty-title {
  font-size: 15px; font-weight: 700; color: #374151;
  margin-bottom: 6px;
}
.empty-sub {
  font-size: 13px; color: #94a3b8;
}

/* ===== 题目卡片 ===== */
.question-card {
  background: #f8fafc;
  border: 1px solid #e8eef8;
  border-radius: 12px;
  padding: 16px;
  border-left: 3px solid #1677FF;
}
.answer-reveal {
  font-size: 12px;
  color: #00A38D;
  background: #E6FBF8;
  border: 1px solid rgba(0,194,168,0.2);
  border-radius: 8px;
  padding: 8px 12px;
  font-weight: 500;
}

/* ===== PDF 上传区 ===== */
.pdf-drop-zone {
  border: 2px dashed #bfdbfe;
  border-radius: 14px;
  padding: 32px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  background: #fafbff;
}
.pdf-drop-zone:hover { border-color: #1677FF; background: #E8F3FF; }
.pdf-drop-zone.dragging { border-color: #1677FF; background: #eff6ff; }
.pdf-drop-zone.hasFile { border-color: #00C2A8; background: #E6FBF8; }
.pdf-selected { display: flex; align-items: center; gap: 12px; text-align: left; }

/* 主 Tab 切换栏（兼容旧代码，保留避免报错）*/
.main-tab-bar {
  display: flex;
  gap: 8px;
  background: #fff;
  border-radius: 14px;
  padding: 6px;
  box-shadow: 0 1px 6px rgba(0,0,0,0.06);
  border: 1px solid #e8eef8;
}

.main-tab-btn {
  flex: 1;
  padding: 10px 16px;
  border-radius: 10px;
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  color: #64748b;
  transition: all 0.2s;
  text-align: center;
}

.main-tab-btn:hover {
  background: #f0f4ff;
  color: #4f46e5;
}

.main-tab-btn.active {
  background: linear-gradient(135deg, #4f46e5, #7c3aed);
  color: white;
  font-weight: 600;
  box-shadow: 0 3px 12px rgba(79,70,229,0.35);
}

/* ── 一键全套生成横幅 ── */
.one-click-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 16px 22px;
  border-radius: 14px;
  background: linear-gradient(135deg, #1e40af 0%, #3730a3 50%, #4c1d95 100%);
  box-shadow: 0 4px 20px rgba(59,130,246,0.3);
  flex-wrap: wrap;
}

.ocb-left {
  display: flex;
  align-items: center;
  gap: 14px;
}

.ocb-icon {
  font-size: 28px;
  flex-shrink: 0;
  animation: pulse-scale 2s ease infinite;
}

@keyframes pulse-scale {
  0%, 100% { transform: scale(1); }
  50%       { transform: scale(1.15); }
}

.ocb-title {
  font-size: 15px;
  font-weight: 800;
  color: white;
  letter-spacing: -0.3px;
}

.ocb-sub {
  font-size: 12px;
  color: rgba(255,255,255,0.7);
  margin-top: 2px;
}

.ocb-right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  justify-content: flex-end;
  min-width: 0;
  flex-wrap: wrap;
}

.ocb-input {
  flex: 1;
  min-width: 160px;
  max-width: 280px;
  padding: 9px 14px;
  border-radius: 10px;
  border: 1.5px solid rgba(255,255,255,0.3);
  background: rgba(255,255,255,0.12);
  color: white;
  font-size: 13px;
  outline: none;
  transition: all 0.2s;
  backdrop-filter: blur(4px);
}

.ocb-input::placeholder { color: rgba(255,255,255,0.5); }
.ocb-input:focus {
  border-color: rgba(255,255,255,0.7);
  background: rgba(255,255,255,0.2);
}

.ocb-btn {
  flex-shrink: 0;
  padding: 9px 20px;
  border-radius: 10px;
  border: none;
  background: linear-gradient(135deg, #f59e0b, #ef4444);
  color: white;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 3px 12px rgba(245,158,11,0.4);
  white-space: nowrap;
}

.ocb-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 5px 18px rgba(245,158,11,0.55);
}

.ocb-btn:disabled { opacity: 0.5; cursor: not-allowed; }

/* PDF 上传区 */
.pdf-drop-zone {
  border: 2px dashed #cbd5e1;
  border-radius: 12px;
  padding: 32px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  background: #f8fafc;
}
.pdf-drop-zone:hover { border-color: #6366f1; background: #f0f4ff; }
.pdf-drop-zone.dragging { border-color: #6366f1; background: #eff6ff; }
.pdf-drop-zone.hasFile { border-color: #22c55e; background: #f0fdf4; }
.pdf-selected { display: flex; align-items: center; gap: 12px; text-align: left; }
.pdf-input {
  width: 100%; padding: 8px 12px;
  border: 1px solid #e2e8f0; border-radius: 8px;
  font-size: 13px; outline: none;
}
.pdf-input:focus { border-color: #6366f1; }
.pdf-upload-btn {
  width: 100%; padding: 11px;
  background: linear-gradient(135deg, #6366f1, #4f46e5);
  color: white; border: none; border-radius: 10px;
  font-size: 14px; font-weight: 600; cursor: pointer;
  display: flex; align-items: center; justify-content: center; gap: 8px;
  transition: all 0.18s;
}
.pdf-upload-btn:hover:not(:disabled) { opacity: 0.9; transform: translateY(-1px); }
.pdf-upload-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.form-row { display: flex; flex-direction: column; gap: 4px; }
.builtin-books { display: flex; flex-direction: column; gap: 8px; }
.book-item {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 12px; border: 1px solid #e2e8f0;
  border-radius: 10px; background: white;
}

/* ── Hero 区：AI智能学习资源中心 ── */
.resource-hero {
  position: relative;
  border-radius: 14px;
  overflow: hidden;
  min-height: 120px;
}

.hero-bg-svg {
  position: absolute; inset: 0;
  width: 100%; height: 100%;
  pointer-events: none;
}

.hero-content {
  position: relative; z-index: 1;
  padding: 20px 24px;
  display: flex;
  align-items: center;
  gap: 24px;
  flex-wrap: wrap;
}

.hero-left { flex: 1; min-width: 200px; }

.hero-eyebrow {
  display: flex; align-items: center; gap: 6px;
  font-size: 11px; color: rgba(255,255,255,0.7);
  margin-bottom: 6px;
}
.hero-ai-dot {
  width: 7px; height: 7px; border-radius: 50%;
  background: #34d399;
  animation: pulse-dot 2s ease infinite;
}
@keyframes pulse-dot {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.4); opacity: 0.7; }
}

.hero-title {
  font-size: 20px; font-weight: 800; color: white;
  margin: 0 0 4px; line-height: 1.3;
  letter-spacing: -0.3px;
  text-shadow: 0 1px 8px rgba(0,0,0,0.2);
}

.hero-desc {
  font-size: 12px; color: rgba(255,255,255,0.7);
  margin: 0 0 12px; line-height: 1.5;
}

.hero-badges { display: flex; flex-wrap: wrap; gap: 6px; }

.hero-badge {
  font-size: 11px; font-weight: 600;
  padding: 3px 10px; border-radius: 999px;
  background: rgba(255,255,255,0.15);
  color: rgba(255,255,255,0.9);
  border: 1px solid rgba(255,255,255,0.2);
  backdrop-filter: blur(4px);
}
.hero-badge-warn {
  background: rgba(251,191,36,0.2);
  border-color: rgba(251,191,36,0.4);
  color: #fde68a;
}

/* 四大分类快捷入口 */
.hero-categories {
  display: flex; gap: 8px; flex-wrap: wrap;
}

.hero-cat-item {
  display: flex; flex-direction: column; align-items: center; gap: 4px;
  padding: 10px 14px;
  border-radius: 10px;
  border: 1.5px solid;
  cursor: pointer;
  transition: all 0.2s;
  min-width: 72px;
}
.hero-cat-item:hover {
  background: rgba(255,255,255,0.18) !important;
  transform: translateY(-2px);
}

.hero-cat-icon { font-size: 18px; }
.hero-cat-name {
  font-size: 11px; font-weight: 700; color: white;
  white-space: nowrap;
}
.hero-cat-count {
  font-size: 11px; font-weight: 800;
  padding: 1px 8px; border-radius: 999px;
}

/* ── 四分类资源分区块 ── */
.resource-section-block {
  margin-bottom: 20px;
  border-left: 3px solid;
  border-radius: 0 10px 10px 0;
  overflow: hidden;
}

.rsb-header {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 14px;
}

.rsb-icon { font-size: 18px; flex-shrink: 0; }

.rsb-meta { flex: 1; min-width: 0; }

.rsb-title {
  font-size: 13px; font-weight: 800;
  display: block; margin-bottom: 1px;
}

.rsb-desc {
  font-size: 11px; color: #64748b;
  display: block;
}

.rsb-count {
  flex-shrink: 0;
  font-size: 11px; font-weight: 700;
  padding: 2px 10px; border-radius: 999px;
}

.rsb-grid {
  padding: 12px 14px;
  display: grid;
  grid-template-columns: repeat(1, 1fr);
  gap: 12px;
  background: white;
}

@media (min-width: 768px) {
  .rsb-grid { grid-template-columns: repeat(2, 1fr); }
}

@media (min-width: 1024px) {
  .rsb-grid { grid-template-columns: repeat(3, 1fr); }
}
</style>
