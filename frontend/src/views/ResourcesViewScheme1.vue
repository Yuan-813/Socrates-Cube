<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useResourceStore } from '@/stores/resourceStore'
import { useChatStore } from '@/stores/chatStore'
import { useUserStore } from '@/stores/userStore'
import DocCard from '@/components/resources/DocCard.vue'
import ExerciseCard from '@/components/resources/ExerciseCard.vue'
import CodeCard from '@/components/resources/CodeCard.vue'
import MindmapCard from '@/components/resources/MindmapCard.vue'
import ScriptCard from '@/components/resources/ScriptCard.vue'
import InfoCard from '@/components/resources/InfoCard.vue'
import type { LearningResource, ResourceType } from '@/types'

const resourceStore = useResourceStore()
const chatStore = useChatStore()
const userStore = useUserStore()

// === 主Tab ===
const mainTab = ref<'spaces' | 'questions' | 'infographic' | 'pdf'>('spaces')

// === 当前活跃的资源空间 ===
const activeSpace = ref<'protocol' | 'misconception' | 'lab' | 'rfc' | 'code' | null>(null)

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
const qTypeLabels: Record<string, string> = {
  choice: '单选题', fill: '填空题', short_answer: '简答题', diagram: '图形判断题', case: '案例分析'
}

async function handleGenerateQuestions() {
  if (!qTopic.value.trim() || qIsGenerating.value || !qSelectedTypes.value.length) return
  qError.value = null; qResults.value = {}; qIsGenerating.value = true
  try {
    const resp = await fetch('/api/v1/question/batch', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ topic: qTopic.value.trim(), question_types: qSelectedTypes.value,
        count_per_type: qCount.value, difficulty: qDifficulty.value, user_id: userStore.userId }),
    })
    if (!resp.ok) throw new Error(`请求失败 HTTP ${resp.status}`)
    const data = await resp.json()
    qResults.value = data.results || {}
  } catch (e: unknown) {
    qError.value = e instanceof Error ? e.message : '题目生成失败，请稍后重试'
  } finally { qIsGenerating.value = false }
}

async function handleExportQuestions(format: 'docx' | 'xlsx') {
  if (!qTotalCount.value || qExporting.value) return
  qExporting.value = format
  try {
    const questions: unknown[] = []
    for (const [qtype, items] of Object.entries(qResults.value)) {
      for (const q of items) questions.push({ ...(q as Record<string, unknown>), question_type: qtype })
    }
    const resp = await fetch('/api/v1/export/questions', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ questions, format, topic: qTopic.value }),
    })
    if (!resp.ok) throw new Error(`导出失败 HTTP ${resp.status}`)
    const blob = await resp.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a'); a.href = url
    a.download = `题目_${qTopic.value}_${Date.now()}.${format}`; a.click(); URL.revokeObjectURL(url)
  } catch (e: unknown) {
    qError.value = e instanceof Error ? e.message : '导出失败'
  } finally { qExporting.value = null }
}

// === 信息图生成 ===
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
  { value: 'flowchart', label: '流程图', icon: '🔄' },
  { value: 'mindmap', label: '思维导图', icon: '🧠' },
  { value: 'timeline', label: '时间线', icon: '📅' },
  { value: 'comparison', label: '对比图', icon: '⚖️' },
]
async function handleGenerateInfograhic() {
  if (!igTopic.value.trim() || igLoading.value) return
  igLoading.value = true; igError.value = null; igResult.value = null
  try {
    const r = await fetch('/api/v1/infographic/generate', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ topic: igTopic.value.trim(), style: igStyle.value, user_id: userStore.userId }),
    })
    if (!r.ok) throw new Error(`HTTP ${r.status}`)
    igResult.value = await r.json()
  } catch (e: unknown) { igError.value = e instanceof Error ? e.message : '生成失败' }
  finally { igLoading.value = false }
}
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
function igNodeById(id: string) { return igLayoutNodes.value.find(n => n.id === id) }

// === 资源生成 ===
const knowledgePoint = ref('')
const selectedType = ref<ResourceType | 'all'>('all')
const difficulty = ref(3)
const isGenerating = ref(false)
const generateError = ref<string | null>(null)
const quickTopic = ref('')

// === PDF 上传 ===
const pdfFile = ref<File | null>(null)
const pdfFileName = ref('')
const pdfSourceName = ref('')
const pdfUseMineru = ref(false)
const pdfUploading = ref(false)
const pdfResult = ref<{ success: boolean; message: string; chunks_added?: number } | null>(null)
const pdfDragging = ref(false)
const builtinBooks = ref<Array<{ id: string; title: string; author: string; tags: string[] }>>([])

function handlePdfFileChange(event: Event) {
  const target = event.target as HTMLInputElement; const file = target.files?.[0]
  if (file && file.type === 'application/pdf') {
    pdfFile.value = file; pdfFileName.value = file.name
    pdfSourceName.value = file.name.replace(/\.pdf$/i, ''); pdfResult.value = null
  }
}
function handlePdfDrop(event: DragEvent) {
  event.preventDefault(); pdfDragging.value = false
  const file = event.dataTransfer?.files?.[0]
  if (file && file.type === 'application/pdf') {
    pdfFile.value = file; pdfFileName.value = file.name
    pdfSourceName.value = file.name.replace(/\.pdf$/i, ''); pdfResult.value = null
  }
}
async function handlePdfUpload() {
  if (!pdfFile.value || pdfUploading.value) return
  pdfResult.value = null; pdfUploading.value = true
  try {
    const formData = new FormData()
    formData.append('file', pdfFile.value)
    formData.append('source_name', pdfSourceName.value || pdfFileName.value)
    formData.append('use_mineru', pdfUseMineru.value ? 'true' : 'false')
    const res = await fetch('/api/v1/kb/upload-pdf', { method: 'POST', body: formData })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || '上传失败')
    pdfResult.value = { success: true, message: data.message, chunks_added: data.chunks_added }
    pdfFile.value = null; pdfFileName.value = ''
  } catch (e: unknown) {
    pdfResult.value = { success: false, message: e instanceof Error ? e.message : '上传失败' }
  } finally { pdfUploading.value = false }
}

// === 上传知识库 ===
const uploadContent = ref('')
const uploadSource = ref('')
const uploadIsMarkdown = ref(false)
const isUploading = ref(false)
const uploadResult = ref<{ success: boolean; message: string; chunks_added?: number } | null>(null)
const showUploadPanel = ref(false)
async function handleUpload() {
  if (!uploadContent.value.trim() || isUploading.value) return
  uploadResult.value = null; isUploading.value = true
  try {
    const res = await fetch('/api/v1/kb/upload', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: uploadContent.value, source: uploadSource.value.trim() || '用户上传', is_markdown: uploadIsMarkdown.value }),
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || '上传失败')
    uploadResult.value = { success: true, message: data.message, chunks_added: data.chunks_added }
    uploadContent.value = ''; uploadSource.value = ''
  } catch (e: unknown) {
    uploadResult.value = { success: false, message: e instanceof Error ? e.message : '上传失败' }
  } finally { isUploading.value = false }
}

// === 资源展示 ===
type ViewTab = ResourceType | 'all'
const viewTab = ref<ViewTab>('all')
const lastDiagnosis = computed(() => chatStore.lastDiagnosis)
const profile = computed(() => userStore.profile)
const quickSuggestions = computed(() => {
  const items: string[] = []
  const diag = lastDiagnosis.value
  if (diag?.rootCause?.weakKnowledge) items.push(diag.rootCause.weakKnowledge)
  diag?.missing_prerequisites?.slice(0, 2).forEach(p => { if (!items.includes(p)) items.push(p) })
  profile.value.weak_points.slice(0, 3).forEach(p => { if (!items.includes(p)) items.push(p) })
  return items.slice(0, 5)
})
// eslint-disable-next-line @typescript-eslint/no-unused-vars
const resourceTypeOptions = [
  { value: 'all', label: '全部类型', icon: '⚡' },
  { value: 'doc', label: '知识文档', icon: '📄' },
  { value: 'exercise', label: '练习题', icon: '📝' },
  { value: 'code', label: '代码示例', icon: '💻' },
  { value: 'mindmap', label: '思维导图', icon: '🗺️' },
  { value: 'script', label: '视频脚本', icon: '🎬' },
]
const cardComponents: Record<string, unknown> = {
  doc: DocCard, exercise: ExerciseCard, code: CodeCard,
  mindmap: MindmapCard, script: ScriptCard, infographic: InfoCard,
}
function cardFor(type: string) { return cardComponents[type] ?? DocCard }

const displayedResources = computed<LearningResource[]>(() => {
  switch (viewTab.value) {
    case 'doc': return resourceStore.docResources
    case 'exercise': return resourceStore.exerciseResources
    case 'code': return resourceStore.codeResources
    case 'mindmap': return resourceStore.mindmapResources
    case 'script': return resourceStore.scriptResources
    default: return resourceStore.resources
  }
})

// eslint-disable-next-line @typescript-eslint/no-unused-vars
async function handleGenerate() {
  if (!knowledgePoint.value.trim() || isGenerating.value) return
  generateError.value = null; isGenerating.value = true
  try {
    if (selectedType.value === 'all') {
      await resourceStore.generateAll(knowledgePoint.value.trim(), difficulty.value)
      viewTab.value = 'all'
    } else {
      await resourceStore.generateResource(knowledgePoint.value.trim(), selectedType.value, difficulty.value)
      viewTab.value = selectedType.value
    }
  } catch (e: unknown) { generateError.value = e instanceof Error ? e.message : '生成失败' }
  finally { isGenerating.value = false }
}
// eslint-disable-next-line @typescript-eslint/no-unused-vars
function applyDiagnosis(kp: string) { knowledgePoint.value = kp }
async function handleOneClick() {
  const topic = quickTopic.value.trim() || knowledgePoint.value.trim()
  if (!topic || isGenerating.value) return
  knowledgePoint.value = topic; quickTopic.value = topic
  generateError.value = null; isGenerating.value = true
  try {
    await resourceStore.generateAll(topic, difficulty.value); viewTab.value = 'all'
  } catch (e: unknown) { generateError.value = e instanceof Error ? e.message : '生成失败' }
  finally { isGenerating.value = false }
}

// === KG 动画 ===
const kgCanvas = ref<HTMLCanvasElement | null>(null)
let kgTimer: number | null = null
const kgNodes = [
  { label: 'TCP', x: 0.5, y: 0.45, color: '#2563EB' },
  { label: 'HTTP', x: 0.75, y: 0.25, color: '#7C3AED' },
  { label: 'DNS', x: 0.8, y: 0.6, color: '#10B981' },
  { label: 'IP', x: 0.25, y: 0.3, color: '#F59E0B' },
  { label: 'TLS', x: 0.65, y: 0.75, color: '#EF4444' },
  { label: 'QUIC', x: 0.3, y: 0.7, color: '#06B6D4' },
]
const kgEdges = [[0,1],[0,2],[0,3],[1,4],[1,5],[0,4]]
let kgAngle = 0

function drawKG() {
  const canvas = kgCanvas.value; if (!canvas) return
  const ctx = canvas.getContext('2d'); if (!ctx) return
  const w = canvas.width, h = canvas.height
  ctx.clearRect(0, 0, w, h)
  const pulseFactor = 0.05 * Math.sin(kgAngle * 2)
  const nodes = kgNodes.map((n, i) => ({
    ...n,
    px: n.x * w + Math.cos(kgAngle + i * 1.2) * 8,
    py: n.y * h + Math.sin(kgAngle * 0.7 + i * 0.9) * 6,
  }))
  // Draw edges
  kgEdges.forEach(([a, b]) => {
    ctx.beginPath()
    ctx.moveTo(nodes[a].px, nodes[a].py)
    ctx.lineTo(nodes[b].px, nodes[b].py)
    ctx.strokeStyle = 'rgba(37,99,235,0.15)'
    ctx.lineWidth = 1.5
    ctx.stroke()
  })
  // Draw nodes
  nodes.forEach(n => {
    const r = 22 + pulseFactor * 10
    const grad = ctx.createRadialGradient(n.px, n.py, 0, n.px, n.py, r)
    grad.addColorStop(0, n.color + 'dd')
    grad.addColorStop(1, n.color + '33')
    ctx.beginPath(); ctx.arc(n.px, n.py, r, 0, Math.PI * 2)
    ctx.fillStyle = grad; ctx.fill()
    ctx.strokeStyle = n.color + '88'; ctx.lineWidth = 1.5; ctx.stroke()
    ctx.fillStyle = '#fff'; ctx.font = 'bold 11px Inter,system-ui'
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle'
    ctx.fillText(n.label, n.px, n.py)
  })
  kgAngle += 0.008
}

onMounted(async () => {
  await resourceStore.loadRecent()
  if (!knowledgePoint.value) {
    knowledgePoint.value = lastDiagnosis.value?.rootCause?.weakKnowledge || profile.value.weak_points[0] || ''
  }
  try {
    const res = await fetch('/api/v1/kb/books')
    if (res.ok) { const data = await res.json(); builtinBooks.value = data.books || [] }
  } catch {}
  kgTimer = window.setInterval(drawKG, 40)
})
onUnmounted(() => { if (kgTimer) clearInterval(kgTimer) })

// 资源空间定义
const resourceSpaces = [
  {
    key: 'protocol', title: '协议知识库', subtitle: 'Protocol Knowledge Base',
    icon: '📡', color: '#2563EB', bgGrad: 'linear-gradient(135deg,#EFF6FF,#DBEAFE)',
    borderColor: '#BFDBFE', count: '295个知识节点', tags: ['TCP/IP','HTTP','DNS','TLS'],
    tabKey: 'doc',
  },
  {
    key: 'misconception', title: '错误模式库', subtitle: 'Misconceptions',
    icon: '🎯', color: '#F59E0B', bgGrad: 'linear-gradient(135deg,#FFFBEB,#FEF3C7)',
    borderColor: '#FDE68A', count: '150+典型错误', tags: ['认知误区','易混淡'],
    tabKey: 'exercise',
  },
  {
    key: 'lab', title: '实验案例库', subtitle: 'Lab & Practice',
    icon: '🛠', color: '#10B981', bgGrad: 'linear-gradient(135deg,#ECFDF5,#D1FAE5)',
    borderColor: '#A7F3D0', count: '38个实验案例', tags: ['H3C','Wireshark'],
    tabKey: 'code',
  },
  {
    key: 'rfc', title: 'RFC标准库', subtitle: 'RFC Standards',
    icon: '📄', color: '#7C3AED', bgGrad: 'linear-gradient(135deg,#F5F3FF,#EDE9FE)',
    borderColor: '#DDD6FE', count: '16份RFC精读', tags: ['RFC793','RFC9110'],
    tabKey: 'doc',
  },
  {
    key: 'code', title: '工程代码库', subtitle: 'Code Repository',
    icon: '💻', color: '#374151', bgGrad: 'linear-gradient(135deg,#F9FAFB,#F3F4F6)',
    borderColor: '#D1D5DB', count: '60+代码示例', tags: ['Python','Socket'],
    tabKey: 'code',
  },
]

// Stats
const statsItems = computed(() => [
  { label: '学习资源', value: resourceStore.resources.length || 62, icon: '📚', color: '#2563EB' },
  { label: '协议节点', value: 295, icon: '🔗', color: '#7C3AED' },
  { label: '误解模式', value: 150, icon: '🎯', color: '#F59E0B' },
  { label: '掌握度', value: `62%`, icon: '🏆', color: '#10B981' },
])
</script>

<template>
  <div class="s1-page">

    <!-- ===== HERO SECTION ===== -->
    <div class="s1-hero">
      <div class="s1-hero-content">
        <div class="s1-hero-left">
          <div class="s1-eyebrow">
            <span class="s1-ai-dot"></span>
            <span>AI Knowledge Hub · Socrates Cube</span>
          </div>
          <h1 class="s1-hero-title">
            计算机网络<br>
            <span class="s1-hero-title-accent">智能学习资源中心</span>
          </h1>
          <p class="s1-hero-desc">
            知识组织 · 推理诊断 · 自适应学习<br>为你的认知薄弱点精准生成学习材料
          </p>

          <!-- Stats Row -->
          <div class="s1-stats-row">
            <div v-for="s in statsItems" :key="s.label" class="s1-stat-item">
              <span class="s1-stat-icon">{{ s.icon }}</span>
              <div>
                <div class="s1-stat-value" :style="{ color: s.color }">{{ s.value }}</div>
                <div class="s1-stat-label">{{ s.label }}</div>
              </div>
            </div>
          </div>

          <!-- CTA Buttons -->
          <div class="s1-hero-ctas">
            <button class="s1-btn-primary" @click="mainTab = 'spaces'">
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/></svg>
              进入资源空间
            </button>
            <button class="s1-btn-ghost" @click="mainTab = 'questions'">
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
              AI智能生成
            </button>
          </div>
        </div>

        <!-- KG Animation Canvas -->
        <div class="s1-hero-right">
          <div class="s1-kg-wrap">
            <canvas ref="kgCanvas" width="340" height="220" class="s1-kg-canvas"></canvas>
            <div class="s1-kg-label">知识图谱 · 实时感知</div>
          </div>
        </div>
      </div>

      <!-- Tab Nav -->
      <div class="s1-tab-nav">
        <button v-for="tab in [
          { key:'spaces', icon:'🗂', label:'五类资源空间' },
          { key:'questions', icon:'📝', label:'AI智能题库' },
          { key:'infographic', icon:'🕸', label:'知识图谱生成' },
          { key:'pdf', icon:'📦', label:'知识库管理' },
        ]" :key="tab.key"
          class="s1-tab-btn"
          :class="{ 's1-tab-active': mainTab === tab.key }"
          @click="mainTab = tab.key as typeof mainTab">
          <span>{{ tab.icon }}</span>
          <span>{{ tab.label }}</span>
        </button>
      </div>
    </div>

    <!-- ===== MAIN CONTENT ===== -->
    <div class="s1-main">

      <!-- ===== 五类资源空间 ===== -->
      <template v-if="mainTab === 'spaces'">

        <!-- AI 诊断联动提示 -->
        <div v-if="lastDiagnosis?.rootCause?.weakKnowledge" class="s1-diag-banner">
          <div class="s1-diag-icon">🧠</div>
          <div class="s1-diag-content">
            <span class="s1-diag-label">AI 诊断发现薄弱点</span>
            <span class="s1-diag-kp">{{ lastDiagnosis.rootCause.weakKnowledge }}</span>
            <span v-if="lastDiagnosis.intervention_suggestion" class="s1-diag-suggest">{{ lastDiagnosis.intervention_suggestion }}</span>
          </div>
          <button class="s1-btn-primary s1-btn-sm"
            @click="knowledgePoint = lastDiagnosis!.rootCause!.weakKnowledge; mainTab = 'spaces'">
            立即生成资源 →
          </button>
        </div>

        <!-- 五类资源空间大卡片 -->
        <div class="s1-section-header">
          <h2 class="s1-section-title">五类知识资源空间</h2>
          <p class="s1-section-sub">点击进入并自动筛选对应资源，或通过 AI 生成定制学习材料</p>
        </div>

        <div class="s1-spaces-wrap">
          <div class="s1-spaces-grid">
          <div v-for="space in resourceSpaces" :key="space.key"
            class="s1-space-card"
            :class="{ 's1-space-active': activeSpace === space.key }"
            :style="{ background: space.bgGrad, borderColor: activeSpace === space.key ? space.color : space.borderColor }"
            @click="activeSpace = activeSpace === space.key ? null : (space.key as typeof activeSpace); viewTab = space.tabKey as ViewTab">
            <div class="s1-space-header">
              <div class="s1-space-icon-wrap" :style="{ background: space.color + '18', border: `1.5px solid ${space.color}30` }">
                <span class="s1-space-icon">{{ space.icon }}</span>
              </div>
              <div class="s1-space-arrow" :class="{ 'rotate-90': activeSpace === space.key }">›</div>
            </div>
            <h3 class="s1-space-title" :style="{ color: space.color }">{{ space.title }}</h3>
            <p class="s1-space-subtitle">{{ space.subtitle }}</p>
            <div class="s1-space-tags">
              <span v-for="tag in space.tags" :key="tag" class="s1-space-tag"
                :style="{ color: space.color, background: space.color + '12', border: `1px solid ${space.color}28` }">
                {{ tag }}
              </span>
            </div>
            <div class="s1-space-footer">
              <span class="s1-space-count" :style="{ color: space.color }">{{ space.count }}</span>
              <span class="s1-space-cta" :style="{ color: space.color }">进入 →</span>
            </div>
          </div>
          </div>
        </div>

        <!-- 一键生成区 -->
        <div class="s1-gen-section">
          <div class="s1-gen-header">
            <div class="s1-gen-icon">⚡</div>
            <div>
              <h3 class="s1-gen-title">AI 一键生成全套学习材料</h3>
              <p class="s1-gen-sub">知识文档 · 练习题 · 代码示例 · 思维导图 · 视频脚本</p>
            </div>
          </div>
          <div class="s1-gen-form">
            <input v-model="knowledgePoint" type="text"
              placeholder="输入知识点，如：TCP三次握手、OSPF路由协议..."
              class="s1-gen-input" @keyup.enter="handleOneClick" />
            <div class="s1-gen-row">
              <div class="s1-quick-tags" v-if="quickSuggestions.length">
                <span class="s1-quick-label">AI推荐：</span>
                <button v-for="s in quickSuggestions" :key="s" class="s1-quick-tag" @click="knowledgePoint = s">{{ s }}</button>
              </div>
              <div class="s1-gen-controls">
                <label class="s1-gen-label">难度 <strong>{{ difficulty }}</strong>/5</label>
                <input v-model.number="difficulty" type="range" min="1" max="5" class="s1-range" />
              </div>
            </div>
            <div class="s1-gen-actions">
              <button class="s1-btn-primary" :disabled="isGenerating || !knowledgePoint.trim()" @click="handleOneClick">
                <svg v-if="isGenerating" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                </svg>
                <span>{{ isGenerating ? '生成中...' : '⚡ 生成全套学习材料' }}</span>
              </button>
              <span v-if="generateError" class="s1-error-text">❌ {{ generateError }}</span>
            </div>
          </div>
        </div>

        <!-- 资源列表 -->
        <div v-if="resourceStore.resources.length > 0" class="s1-resources-section">
          <div class="s1-section-header">
            <h2 class="s1-section-title">已生成学习资源</h2>
            <div class="s1-view-tabs">
              <button v-for="t in [
                { key:'all', label:'全部', count: resourceStore.resources.length },
                { key:'doc', label:'📄 文档', count: resourceStore.docResources.length },
                { key:'exercise', label:'📝 练习', count: resourceStore.exerciseResources.length },
                { key:'code', label:'💻 代码', count: resourceStore.codeResources.length },
                { key:'mindmap', label:'🗺️ 导图', count: resourceStore.mindmapResources.length },
                { key:'script', label:'🎬 脚本', count: resourceStore.scriptResources.length },
              ]" :key="t.key"
                class="s1-vtab" :class="{ 's1-vtab-active': viewTab === t.key }"
                @click="viewTab = t.key as ViewTab">
                {{ t.label }}
                <span class="s1-vtab-count">{{ t.count }}</span>
              </button>
            </div>
          </div>

          <div class="s1-resource-grid">
            <component
              v-for="r in displayedResources" :key="r.id || r.resource_type"
              :is="cardFor(r.resource_type ?? 'doc')"
              :resource="r"
            />
          </div>
        </div>

        <!-- 空态 -->
        <div v-else class="s1-empty-state">
          <div class="s1-empty-icon">📚</div>
          <p class="s1-empty-title">知识空间待激活</p>
          <p class="s1-empty-sub">输入知识点并生成学习材料，或通过 AI 诊断发现薄弱点</p>
          <button class="s1-btn-primary s1-btn-sm" @click="handleOneClick">从 TCP 三次握手开始</button>
        </div>
      </template>

      <!-- ===== 智能题库 ===== -->
      <template v-if="mainTab === 'questions'">
        <div class="s1-card">
          <div class="s1-card-header">
            <div class="s1-card-icon" style="background:#7C3AED18;border-color:#7C3AED30">
              <span>📝</span>
            </div>
            <div>
              <h3 class="s1-card-title">AI 智能题库生成</h3>
              <p class="s1-card-sub">精准针对薄弱知识点，生成多题型专项训练</p>
            </div>
          </div>

          <div class="s1-form-group">
            <label class="s1-label">主题 / 知识点</label>
            <input v-model="qTopic" type="text"
              placeholder="如：TCP三次握手、OSI七层模型、BGP路由协议..."
              class="s1-input" @keyup.enter="handleGenerateQuestions" />
          </div>

          <div class="s1-form-group">
            <label class="s1-label">题型（可多选）</label>
            <div class="s1-chip-group">
              <button v-for="opt in questionTypeOptions" :key="opt.value"
                class="s1-chip" :class="qSelectedTypes.includes(opt.value) ? 's1-chip-active-purple' : ''"
                @click="qSelectedTypes.includes(opt.value) ? qSelectedTypes.splice(qSelectedTypes.indexOf(opt.value), 1) : qSelectedTypes.push(opt.value)">
                {{ opt.icon }} {{ opt.label }}
              </button>
            </div>
          </div>

          <div class="s1-form-row">
            <div class="s1-form-item">
              <label class="s1-label">每种题型数量 <strong style="color:#7C3AED">{{ qCount }}</strong> 题</label>
              <input v-model.number="qCount" type="range" min="1" max="20" class="s1-range s1-range-purple" />
            </div>
            <div class="s1-form-item s1-form-item-sm">
              <label class="s1-label">难度 <strong style="color:#7C3AED">{{ qDifficulty }}</strong>/5</label>
              <input v-model.number="qDifficulty" type="range" min="1" max="5" class="s1-range s1-range-purple" />
            </div>
          </div>

          <div class="s1-gen-actions">
            <button class="s1-btn-purple"
              :disabled="!qTopic.trim() || qIsGenerating || !qSelectedTypes.length"
              @click="handleGenerateQuestions">
              <svg v-if="qIsGenerating" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
              </svg>
              {{ qIsGenerating ? '生成中...' : `生成 ${qSelectedTypes.length} 种题型 × ${qCount} 题` }}
            </button>
            <p v-if="qError" class="s1-error-text">❌ {{ qError }}</p>
          </div>
        </div>

        <!-- 题目结果 -->
        <div v-if="qTotalCount > 0" class="s1-card">
          <div class="s1-result-header">
            <h3 class="s1-card-title">生成结果：共 <span style="color:#7C3AED">{{ qTotalCount }}</span> 题</h3>
            <div class="s1-export-btns">
              <button class="s1-btn-outline-blue" :disabled="!!qExporting" @click="handleExportQuestions('docx')">
                📄 {{ qExporting === 'docx' ? '导出中...' : '导出 Word' }}
              </button>
              <button class="s1-btn-outline-green" :disabled="!!qExporting" @click="handleExportQuestions('xlsx')">
                📊 {{ qExporting === 'xlsx' ? '导出中...' : '导出 Excel' }}
              </button>
            </div>
          </div>

          <div v-for="(items, qtype) in qResults" :key="qtype" class="s1-qtype-section">
            <div class="s1-qtype-label">
              <span class="s1-qtype-badge">{{ qTypeLabels[qtype] || qtype }}</span>
              <span class="s1-qtype-count">{{ (items as unknown[]).length }} 题</span>
            </div>
            <div v-for="(q, idx) in (items as Record<string, unknown>[])" :key="idx" class="s1-question-card">
              <p class="s1-q-stem">Q{{ idx + 1 }}. {{ q.question || q.stem }}</p>
              <div v-if="q.options" class="s1-q-options">
                <div v-for="(opt, oi) in (q.options as string[])" :key="oi" class="s1-q-option">
                  <span class="s1-q-option-key">{{ String.fromCharCode(65 + oi) }}</span>
                  <span>{{ opt }}</span>
                </div>
              </div>
              <div class="s1-q-answer">
                ✅ 参考答案：{{ q.answer || q.reference_answer || q.sample_answer }}
              </div>
            </div>
          </div>
        </div>

        <div v-else-if="!qIsGenerating" class="s1-empty-state">
          <div class="s1-empty-icon">📝</div>
          <p class="s1-empty-title">输入主题并选择题型，点击「生成」开始</p>
        </div>
        <div v-else class="s1-loading">
          <svg class="w-6 h-6 animate-spin" style="color:#7C3AED" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
          </svg>
          <span style="color:#7C3AED">AI 正在生成题目...</span>
        </div>
      </template>

      <!-- ===== 知识图谱生成 ===== -->
      <template v-if="mainTab === 'infographic'">
        <div class="s1-card">
          <div class="s1-card-header">
            <div class="s1-card-icon" style="background:#10B98118;border-color:#10B98130">
              <span>🕸</span>
            </div>
            <div>
              <h3 class="s1-card-title">AI 知识图谱生成</h3>
              <p class="s1-card-sub">可视化知识结构 · LLM 结构化输出 + SVG 动态渲染</p>
            </div>
          </div>
          <div class="s1-form-row">
            <div class="s1-form-item">
              <label class="s1-label">主题</label>
              <input v-model="igTopic" type="text" placeholder="如：TCP三次握手、OSPF协议工作流程..." class="s1-input" @keyup.enter="handleGenerateInfograhic" />
            </div>
            <div class="s1-form-item s1-form-item-sm">
              <label class="s1-label">图表类型</label>
              <div class="s1-chip-group">
                <button v-for="s in igStyles" :key="s.value"
                  class="s1-chip" :class="igStyle === s.value ? 's1-chip-active-teal' : ''"
                  @click="igStyle = s.value">{{ s.icon }} {{ s.label }}</button>
              </div>
            </div>
          </div>
          <div class="s1-gen-actions">
            <button class="s1-btn-teal" :disabled="!igTopic.trim() || igLoading" @click="handleGenerateInfograhic">
              <svg v-if="igLoading" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
              </svg>
              {{ igLoading ? 'AI 正在构建知识图谱...' : '生成知识图谱' }}
            </button>
            <p v-if="igError" class="s1-error-text">{{ igError }}</p>
          </div>
        </div>

        <div v-if="igResult" class="s1-card">
          <div class="s1-result-header">
            <div>
              <h3 class="s1-card-title">{{ igResult.title }}</h3>
              <p class="s1-card-sub">{{ igResult.summary }}</p>
            </div>
            <span class="s1-source-badge">{{ igResult.source === 'sensenova' ? 'SenseNova-U1' : 'LLM 生成' }}</span>
          </div>
          <img v-if="igResult.style === 'image'" :src="igResult.nodes[0]?.description" :alt="igResult.title" class="s1-ig-img" />
          <div v-else class="s1-svg-wrap">
            <svg viewBox="0 0 720 480" class="s1-kg-svg">
              <g v-for="edge in igResult.edges" :key="edge.from_id + edge.to_id">
                <template v-if="igNodeById(edge.from_id) && igNodeById(edge.to_id)">
                  <line :x1="igNodeById(edge.from_id)!.x" :y1="igNodeById(edge.from_id)!.y" :x2="igNodeById(edge.to_id)!.x" :y2="igNodeById(edge.to_id)!.y" stroke="#2563EB" stroke-width="1.5" stroke-opacity="0.3" stroke-dasharray="5,4"/>
                  <text v-if="edge.label" :x="((igNodeById(edge.from_id)!.x + igNodeById(edge.to_id)!.x)/2)" :y="((igNodeById(edge.from_id)!.y + igNodeById(edge.to_id)!.y)/2)-4" text-anchor="middle" font-size="9" fill="#94a3b8">{{ edge.label }}</text>
                </template>
              </g>
              <g v-for="node in igLayoutNodes" :key="node.id">
                <circle :cx="node.x" :cy="node.y" :r="node.type==='root'?38:28" :fill="node.type==='root'?'#2563EB':'#EFF6FF'" :stroke="node.type==='root'?'#1D4ED8':'#2563EB'" stroke-width="1.5"/>
                <text :x="node.x" :y="node.y-4" text-anchor="middle" font-size="16">{{ node.icon }}</text>
                <text :x="node.x" :y="node.y+12" text-anchor="middle" font-size="9" :fill="node.type==='root'?'white':'#2563EB'" font-weight="600">{{ node.label }}</text>
              </g>
            </svg>
          </div>
          <div class="s1-node-grid">
            <div v-for="n in igResult.nodes" :key="n.id" class="s1-node-item">
              <span class="text-lg">{{ n.icon }}</span>
              <div>
                <span class="s1-node-label">{{ n.label }}</span>
                <span v-if="n.description && igResult?.style!=='image'" class="s1-node-desc"> {{ n.description }}</span>
              </div>
            </div>
          </div>
        </div>

        <div v-else-if="!igLoading" class="s1-empty-state">
          <div class="s1-empty-icon">🕸</div>
          <p class="s1-empty-title">知识图谱待生成</p>
          <p class="s1-empty-sub">AI 将根据主题生成可交互的知识结构可视化图</p>
        </div>
      </template>

      <!-- ===== 知识库管理 ===== -->
      <template v-if="mainTab === 'pdf'">
        <div class="s1-card">
          <div class="s1-card-header">
            <div class="s1-card-icon" style="background:#2563EB18;border-color:#2563EB30"><span>📦</span></div>
            <div>
              <h3 class="s1-card-title">知识库管理</h3>
              <p class="s1-card-sub">上传 PDF 构建私有知识沉淀，AI 回答时自动检索引用</p>
            </div>
          </div>

          <!-- PDF 上传 -->
          <div class="s1-drop-zone"
            :class="{ 's1-drop-dragging': pdfDragging, 's1-drop-has-file': !!pdfFileName }"
            @dragover.prevent="pdfDragging = true"
            @dragleave="pdfDragging = false"
            @drop="handlePdfDrop"
            @click="($refs.pdfInput as HTMLInputElement)?.click()">
            <input ref="pdfInput" type="file" accept=".pdf" style="display:none" @change="handlePdfFileChange" />
            <div v-if="pdfFileName" class="s1-drop-selected">
              <span class="text-3xl">📄</span>
              <div>
                <div class="font-semibold text-gray-800">{{ pdfFileName }}</div>
                <div class="text-xs text-gray-400">点击重选或拖拽新文件</div>
              </div>
            </div>
            <div v-else class="text-center">
              <div class="text-4xl mb-2">📤</div>
              <div class="text-sm font-semibold text-gray-600">拖拽 PDF 文件到此处</div>
              <div class="text-xs text-gray-400 mt-1">或点击选择文件（最大 50MB）</div>
            </div>
          </div>

          <div v-if="pdfFileName" class="s1-pdf-settings">
            <label class="s1-label">来源名称（用于检索标注）</label>
            <input v-model="pdfSourceName" class="s1-input" placeholder="如：计算机网络第7版" />
            <div class="flex items-center gap-2 mt-2">
              <input id="use-mineru" v-model="pdfUseMineru" type="checkbox" class="accent-blue-600" />
              <label for="use-mineru" class="text-xs text-gray-600">启用 MinerU 高质量解析</label>
            </div>
            <button class="s1-btn-primary s1-btn-full" :disabled="pdfUploading" @click="handlePdfUpload">
              <svg v-if="pdfUploading" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
              </svg>
              {{ pdfUploading ? '解析中...' : '开始解析并入知识库' }}
            </button>
          </div>

          <div v-if="pdfResult" class="s1-result-msg" :class="pdfResult.success ? 's1-msg-success' : 's1-msg-error'">
            {{ pdfResult.success ? '✅' : '❌' }} {{ pdfResult.message }}
            <span v-if="pdfResult.chunks_added">（{{ pdfResult.chunks_added }} 个知识块）</span>
          </div>
        </div>

        <!-- 文本上传 -->
        <div class="s1-card">
          <div class="flex items-center justify-between mb-3">
            <h3 class="s1-card-title">上传文本到知识库</h3>
            <button class="s1-toggle-btn" @click="showUploadPanel = !showUploadPanel">{{ showUploadPanel ? '收起 ▲' : '展开 ▼' }}</button>
          </div>
          <template v-if="showUploadPanel">
            <div class="s1-form-group">
              <label class="s1-label">来源名称</label>
              <input v-model="uploadSource" class="s1-input" placeholder="如: BGP笔记.md" />
            </div>
            <div class="s1-form-group">
              <label class="s1-label">粘贴文本内容</label>
              <textarea v-model="uploadContent" rows="5" class="s1-input s1-textarea" placeholder="将文本或 Markdown 内容粘贴到这里..." />
            </div>
            <div class="flex items-center gap-4">
              <label class="flex items-center gap-1.5 text-xs text-gray-600 cursor-pointer">
                <input type="checkbox" v-model="uploadIsMarkdown" /> Markdown 格式
              </label>
              <button class="s1-btn-teal s1-btn-sm" :disabled="isUploading || !uploadContent.trim()" @click="handleUpload">
                {{ isUploading ? '处理中...' : '入库' }}
              </button>
            </div>
            <div v-if="uploadResult" class="s1-result-msg mt-2" :class="uploadResult.success ? 's1-msg-success' : 's1-msg-error'">
              {{ uploadResult.success ? `✅ ${uploadResult.message}（${uploadResult.chunks_added} 个块）` : `❌ ${uploadResult.message}` }}
            </div>
          </template>
        </div>

        <!-- 内置教材 -->
        <div class="s1-card">
          <h3 class="s1-card-title mb-4">📖 内置教材库</h3>
          <div class="s1-books-list">
            <div v-for="book in builtinBooks" :key="book.id" class="s1-book-item">
              <div class="text-2xl">📖</div>
              <div class="flex-1">
                <div class="font-semibold text-sm text-gray-800">{{ book.title }}</div>
                <div class="text-xs text-gray-500">{{ book.author }}</div>
                <div class="flex flex-wrap gap-1 mt-1">
                  <span v-for="tag in book.tags" :key="tag" class="s1-book-tag">{{ tag }}</span>
                </div>
              </div>
              <span class="s1-built-badge">内置</span>
            </div>
            <div v-if="!builtinBooks.length" class="text-center text-sm text-gray-400 py-4">暂无内置教材</div>
          </div>
        </div>
      </template>

    </div><!-- end s1-main -->
  </div>
</template>

<style scoped>
/* ========== 全局 ========== */
.s1-page {
  min-height: 100vh;
  background: #F7F9FC;
  font-family: 'Inter', 'PingFang SC', system-ui, sans-serif;
}

/* ========== HERO ========== */
.s1-hero {
  background: linear-gradient(135deg, #1E3A8A 0%, #2563EB 45%, #4F46E5 100%);
  padding: 0;
}
.s1-hero-content {
  display: flex;
  align-items: center;
  gap: 32px;
  padding: 40px 40px 24px;
}
.s1-hero-left { flex: 1; min-width: 0; color: white; }
.s1-eyebrow {
  display: flex; align-items: center; gap: 8px;
  font-size: 12px; font-weight: 500; letter-spacing: 0.05em;
  color: #BFDBFE; margin-bottom: 16px;
}
.s1-ai-dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: #10B981;
  box-shadow: 0 0 8px #10B981;
  animation: s1-pulse 2s ease-in-out infinite;
}
@keyframes s1-pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:.7;transform:scale(1.2)} }
.s1-hero-title {
  font-size: 2rem; font-weight: 800; line-height: 1.2;
  margin-bottom: 12px; letter-spacing: -0.02em;
  color: white;
}
.s1-hero-title-accent { color: #93C5FD; }
.s1-hero-desc {
  font-size: 0.875rem; color: #BFDBFE; line-height: 1.7;
  margin-bottom: 24px;
}
.s1-stats-row {
  display: flex; flex-wrap: wrap; gap: 20px;
  margin-bottom: 28px;
}
.s1-stat-item { display: flex; align-items: center; gap: 10px; }
.s1-stat-icon { font-size: 1.5rem; }
.s1-stat-value { font-size: 1.25rem; font-weight: 700; color: white; line-height: 1; }
.s1-stat-label { font-size: 0.7rem; color: #93C5FD; margin-top: 2px; }
.s1-hero-ctas { display: flex; gap: 12px; flex-wrap: wrap; }

/* ========== KG Canvas ========== */
.s1-hero-right {
  flex-shrink: 0; width: 340px;
  display: flex; align-items: center; justify-content: center;
}
.s1-kg-wrap {
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.15);
  border-radius: 16px;
  padding: 16px; text-align: center;
  backdrop-filter: blur(8px);
}
.s1-kg-canvas { border-radius: 8px; display: block; }
.s1-kg-label { font-size: 11px; color: #93C5FD; margin-top: 8px; letter-spacing: 0.05em; }

/* ========== Tab Nav ========== */
.s1-tab-nav {
  display: flex; gap: 0;
  background: rgba(0,0,0,0.2);
  border-top: 1px solid rgba(255,255,255,0.1);
  padding: 0 40px;
}
.s1-tab-btn {
  display: flex; align-items: center; gap: 8px;
  padding: 14px 20px;
  font-size: 0.8rem; font-weight: 500;
  color: rgba(255,255,255,0.6);
  border: none; background: none;
  cursor: pointer; border-bottom: 2px solid transparent;
  transition: all 0.2s; white-space: nowrap;
}
.s1-tab-btn:hover { color: rgba(255,255,255,0.9); }
.s1-tab-active {
  color: white !important;
  border-bottom-color: #60A5FA !important;
  background: rgba(255,255,255,0.05);
}

/* ========== Main ========== */
.s1-main {
  max-width: 1200px; margin: 0 auto;
  padding: 32px 40px 60px;
  display: flex; flex-direction: column; gap: 24px;
}

/* ========== Sections ========== */
.s1-section-header { margin-bottom: 16px; }
.s1-section-title { font-size: 1.125rem; font-weight: 700; color: #0F172A; margin: 0; }
.s1-section-sub { font-size: 0.8rem; color: #64748B; margin-top: 4px; }

/* ========== AI Diag Banner ========== */
.s1-diag-banner {
  display: flex; align-items: center; gap: 16px;
  background: linear-gradient(135deg, #EFF6FF, #F5F3FF);
  border: 1px solid #BFDBFE; border-radius: 16px;
  padding: 16px 20px;
}
.s1-diag-icon { font-size: 1.75rem; flex-shrink: 0; }
.s1-diag-content { flex: 1; min-width: 0; }
.s1-diag-label { font-size: 11px; font-weight: 600; color: #2563EB; display: block; }
.s1-diag-kp { font-size: 0.9rem; font-weight: 700; color: #0F172A; display: block; }
.s1-diag-suggest { font-size: 0.75rem; color: #64748B; display: block; margin-top: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

/* ========== Resource Spaces ========== */
.s1-spaces-wrap {
  overflow-x: auto;
  margin: 0 -2px;
  padding: 2px;
}
.s1-spaces-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 12px;
}
.s1-space-card {
  border: 1.5px solid transparent;
  border-radius: 16px; padding: 18px 16px 14px;
  cursor: pointer; transition: all 0.2s;
  position: relative; min-width: 160px;
}
.s1-space-card:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,0.08); }
.s1-space-active { box-shadow: 0 8px 24px rgba(37,99,235,0.15); }
.s1-space-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px; }
.s1-space-icon-wrap { width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center; }
.s1-space-icon { font-size: 1.25rem; }
.s1-space-arrow {
  font-size: 1.1rem; color: #94A3B8; transition: transform 0.2s;
  display: flex; align-items: center;
}
.s1-space-title { font-size: 0.9rem; font-weight: 700; margin: 0 0 2px; }
.s1-space-subtitle { font-size: 0.65rem; color: #94A3B8; font-family: 'Courier New', monospace; margin-bottom: 8px; }
.s1-space-tags { display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 10px; }
.s1-space-tag { font-size: 10px; padding: 2px 8px; border-radius: 999px; font-weight: 500; }
.s1-space-footer { display: flex; justify-content: space-between; align-items: center; }
.s1-space-count { font-size: 0.73rem; font-weight: 700; }
.s1-space-cta { font-size: 0.73rem; font-weight: 600; }

/* ========== Generate Section ========== */
.s1-gen-section {
  background: white; border: 1px solid #E2E8F0;
  border-radius: 16px; padding: 24px;
}
.s1-gen-header { display: flex; gap: 16px; margin-bottom: 20px; align-items: center; }
.s1-gen-icon {
  width: 44px; height: 44px; border-radius: 12px;
  background: linear-gradient(135deg, #2563EB, #4F46E5);
  display: flex; align-items: center; justify-content: center;
  font-size: 1.25rem; flex-shrink: 0;
}
.s1-gen-title { font-size: 1rem; font-weight: 700; color: #0F172A; margin: 0; }
.s1-gen-sub { font-size: 0.75rem; color: #64748B; margin-top: 2px; }
.s1-gen-form { display: flex; flex-direction: column; gap: 12px; }
.s1-gen-input {
  width: 100%; padding: 12px 16px;
  border: 1.5px solid #E2E8F0; border-radius: 10px;
  font-size: 0.875rem; outline: none;
  background: #F8FAFC; transition: border-color 0.2s;
  box-sizing: border-box;
}
.s1-gen-input:focus { border-color: #2563EB; background: white; }
.s1-gen-row { display: flex; align-items: center; gap: 16px; flex-wrap: wrap; }
.s1-quick-tags { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; flex: 1; }
.s1-quick-label { font-size: 11px; color: #94A3B8; }
.s1-quick-tag {
  font-size: 11px; padding: 3px 10px; border-radius: 999px;
  background: #EFF6FF; color: #2563EB;
  border: 1px solid #BFDBFE; cursor: pointer; transition: all 0.15s;
}
.s1-quick-tag:hover { background: #DBEAFE; }
.s1-gen-controls { display: flex; align-items: center; gap: 8px; white-space: nowrap; }
.s1-gen-label { font-size: 0.75rem; color: #64748B; }
.s1-gen-actions { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }

/* ========== Resource Grid ========== */
.s1-resources-section { }
.s1-view-tabs { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 8px; }
.s1-vtab {
  display: flex; align-items: center; gap: 4px;
  padding: 6px 12px; border-radius: 8px;
  font-size: 0.75rem; font-weight: 500; cursor: pointer;
  border: 1px solid #E2E8F0; background: white; color: #64748B;
  transition: all 0.15s;
}
.s1-vtab:hover { border-color: #2563EB; color: #2563EB; }
.s1-vtab-active { background: #2563EB; color: white; border-color: #2563EB; }
.s1-vtab-count {
  background: rgba(255,255,255,0.2); color: inherit;
  font-size: 10px; padding: 0 6px; border-radius: 999px;
  min-width: 18px; text-align: center;
}
.s1-vtab:not(.s1-vtab-active) .s1-vtab-count { background: #F1F5F9; color: #94A3B8; }
.s1-resource-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 16px; margin-top: 16px;
}

/* ========== Cards ========== */
.s1-card {
  background: white; border: 1px solid #E2E8F0;
  border-radius: 16px; padding: 24px;
  display: flex; flex-direction: column; gap: 16px;
}
.s1-card-header { display: flex; gap: 14px; align-items: flex-start; }
.s1-card-icon {
  width: 40px; height: 40px; border-radius: 10px;
  border: 1.5px solid transparent;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.25rem; flex-shrink: 0;
}
.s1-card-title { font-size: 0.9rem; font-weight: 700; color: #0F172A; margin: 0; }
.s1-card-sub { font-size: 0.75rem; color: #64748B; margin-top: 3px; }

/* ========== Form elements ========== */
.s1-form-group { display: flex; flex-direction: column; gap: 6px; }
.s1-label { font-size: 0.75rem; font-weight: 600; color: #374151; }
.s1-input {
  width: 100%; padding: 10px 14px;
  border: 1.5px solid #E2E8F0; border-radius: 8px;
  font-size: 0.875rem; outline: none;
  background: #F8FAFC; transition: border-color 0.2s;
  box-sizing: border-box;
}
.s1-input:focus { border-color: #2563EB; background: white; }
.s1-textarea { resize: vertical; min-height: 100px; }
.s1-form-row { display: flex; gap: 16px; flex-wrap: wrap; }
.s1-form-item { flex: 1; min-width: 180px; display: flex; flex-direction: column; gap: 6px; }
.s1-form-item-sm { flex: 0 0 220px; }
.s1-chip-group { display: flex; flex-wrap: wrap; gap: 6px; }
.s1-chip {
  padding: 5px 12px; border-radius: 8px; font-size: 0.75rem;
  border: 1.5px solid #E2E8F0; background: #F8FAFC; color: #374151;
  cursor: pointer; transition: all 0.15s;
}
.s1-chip:hover { border-color: #94A3B8; }
.s1-chip-active-purple { background: #F5F3FF; border-color: #7C3AED; color: #7C3AED; }
.s1-chip-active-teal { background: #F0FDF4; border-color: #10B981; color: #10B981; }
.s1-range { width: 100%; accent-color: #2563EB; cursor: pointer; }
.s1-range-purple { accent-color: #7C3AED; }

/* ========== Buttons ========== */
.s1-btn-primary {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 10px 20px; border-radius: 10px;
  background: linear-gradient(135deg, #2563EB, #4F46E5);
  color: white; font-size: 0.875rem; font-weight: 600;
  border: none; cursor: pointer; transition: all 0.2s;
  white-space: nowrap;
}
.s1-btn-primary:hover { opacity: 0.9; transform: translateY(-1px); }
.s1-btn-primary:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
.s1-btn-ghost {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 10px 20px; border-radius: 10px;
  background: rgba(255,255,255,0.15); color: white;
  font-size: 0.875rem; font-weight: 600;
  border: 1px solid rgba(255,255,255,0.3); cursor: pointer;
  transition: all 0.2s; backdrop-filter: blur(4px);
}
.s1-btn-ghost:hover { background: rgba(255,255,255,0.25); }
.s1-btn-purple {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 10px 20px; border-radius: 10px;
  background: linear-gradient(135deg, #7C3AED, #6D28D9);
  color: white; font-size: 0.875rem; font-weight: 600;
  border: none; cursor: pointer; transition: all 0.2s;
}
.s1-btn-purple:hover { opacity: 0.9; }
.s1-btn-purple:disabled { opacity: 0.5; cursor: not-allowed; }
.s1-btn-teal {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 10px 20px; border-radius: 10px;
  background: linear-gradient(135deg, #10B981, #059669);
  color: white; font-size: 0.875rem; font-weight: 600;
  border: none; cursor: pointer; transition: all 0.2s;
}
.s1-btn-teal:hover { opacity: 0.9; }
.s1-btn-teal:disabled { opacity: 0.5; cursor: not-allowed; }
.s1-btn-sm { padding: 7px 14px; font-size: 0.8rem; }
.s1-btn-full { width: 100%; justify-content: center; margin-top: 12px; }
.s1-btn-outline-blue {
  padding: 6px 14px; border-radius: 8px; font-size: 0.75rem; font-weight: 500;
  border: 1px solid #BFDBFE; color: #2563EB; background: white; cursor: pointer; transition: all 0.15s;
}
.s1-btn-outline-blue:hover { background: #EFF6FF; }
.s1-btn-outline-green {
  padding: 6px 14px; border-radius: 8px; font-size: 0.75rem; font-weight: 500;
  border: 1px solid #A7F3D0; color: #10B981; background: white; cursor: pointer; transition: all 0.15s;
}
.s1-btn-outline-green:hover { background: #ECFDF5; }
.s1-toggle-btn { font-size: 0.75rem; color: #94A3B8; background: none; border: none; cursor: pointer; }

/* ========== Questions ========== */
.s1-result-header { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; }
.s1-export-btns { display: flex; gap: 8px; }
.s1-qtype-section { display: flex; flex-direction: column; gap: 8px; }
.s1-qtype-label { display: flex; align-items: center; gap: 8px; }
.s1-qtype-badge {
  font-size: 0.75rem; font-weight: 700; color: #7C3AED;
  background: #F5F3FF; padding: 3px 10px; border-radius: 999px;
}
.s1-qtype-count { font-size: 0.75rem; color: #94A3B8; }
.s1-question-card {
  background: #F8FAFC; border: 1px solid #E2E8F0;
  border-radius: 12px; padding: 16px;
}
.s1-q-stem { font-size: 0.875rem; font-weight: 600; color: #0F172A; margin-bottom: 10px; }
.s1-q-options { display: flex; flex-direction: column; gap: 4px; margin-bottom: 10px; }
.s1-q-option { display: flex; gap: 8px; font-size: 0.8rem; color: #374151; }
.s1-q-option-key { font-weight: 600; color: #64748B; flex-shrink: 0; }
.s1-q-answer {
  font-size: 0.75rem; color: #10B981;
  background: #ECFDF5; border-radius: 8px; padding: 8px 12px;
  border: 1px solid #A7F3D0;
}

/* ========== Infographic ========== */
.s1-source-badge {
  font-size: 0.75rem; padding: 3px 10px; border-radius: 999px;
  background: #F5F3FF; color: #7C3AED; border: 1px solid #DDD6FE;
  white-space: nowrap;
}
.s1-ig-img { width: 100%; border-radius: 12px; border: 1px solid #E2E8F0; }
.s1-svg-wrap { overflow-x: auto; }
.s1-kg-svg {
  width: 100%; max-height: 480px;
  border: 1px solid #E2E8F0; border-radius: 12px;
  background: linear-gradient(135deg, #F8FAFC, #EFF6FF);
  min-width: 480px;
}
.s1-node-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 8px; margin-top: 16px; }
.s1-node-item {
  display: flex; align-items: flex-start; gap: 8px;
  padding: 10px; border-radius: 10px;
  background: #EFF6FF; border: 1px solid #BFDBFE;
  font-size: 0.75rem;
}
.s1-node-label { font-weight: 600; color: #1E40AF; }
.s1-node-desc { color: #64748B; }

/* ========== PDF/Upload ========== */
.s1-drop-zone {
  border: 2px dashed #CBD5E1; border-radius: 12px;
  padding: 32px; text-align: center; cursor: pointer;
  background: #F8FAFC; transition: all 0.2s;
}
.s1-drop-zone:hover { border-color: #2563EB; background: #EFF6FF; }
.s1-drop-dragging { border-color: #2563EB; background: #EFF6FF; }
.s1-drop-has-file { border-color: #10B981; background: #ECFDF5; }
.s1-drop-selected { display: flex; align-items: center; gap: 12px; justify-content: center; }
.s1-pdf-settings { display: flex; flex-direction: column; gap: 10px; }
.s1-result-msg {
  font-size: 0.8rem; padding: 10px 14px; border-radius: 8px;
}
.s1-msg-success { background: #ECFDF5; color: #059669; border: 1px solid #A7F3D0; }
.s1-msg-error { background: #FEF2F2; color: #DC2626; border: 1px solid #FECACA; }
.s1-books-list { display: flex; flex-direction: column; gap: 8px; }
.s1-book-item {
  display: flex; align-items: center; gap: 12px;
  padding: 12px; border-radius: 12px;
  border: 1px solid #E2E8F0; transition: all 0.15s;
}
.s1-book-item:hover { border-color: #BFDBFE; background: #EFF6FF; }
.s1-book-tag {
  font-size: 10px; background: #EFF6FF; color: #2563EB;
  padding: 1px 8px; border-radius: 999px; border: 1px solid #BFDBFE;
}
.s1-built-badge {
  font-size: 0.7rem; background: #ECFDF5; color: #10B981;
  padding: 2px 8px; border-radius: 999px; border: 1px solid #A7F3D0;
  font-weight: 500; white-space: nowrap;
}

/* ========== Empty / Loading ========== */
.s1-empty-state {
  text-align: center; padding: 48px 24px;
  display: flex; flex-direction: column; align-items: center; gap: 8px;
}
.s1-empty-icon { font-size: 3rem; margin-bottom: 8px; }
.s1-empty-title { font-size: 1rem; font-weight: 600; color: #374151; }
.s1-empty-sub { font-size: 0.8rem; color: #94A3B8; margin-bottom: 8px; }
.s1-loading {
  display: flex; align-items: center; justify-content: center; gap: 10px;
  padding: 48px; font-size: 0.875rem; font-weight: 500;
}
.s1-error-text { font-size: 0.75rem; color: #DC2626; }

/* ========== Responsive ========== */
@media (max-width: 768px) {
  .s1-hero-content { flex-direction: column; padding: 24px 20px 16px; }
  .s1-hero-right { display: none; }
  .s1-hero-title { font-size: 1.5rem; }
  .s1-tab-nav { padding: 0 16px; overflow-x: auto; }
  .s1-main { padding: 20px 16px 40px; }
  .s1-spaces-grid { grid-template-columns: repeat(2, 1fr); overflow-x: auto; }
  .s1-resource-grid { grid-template-columns: 1fr; }
}
</style>
