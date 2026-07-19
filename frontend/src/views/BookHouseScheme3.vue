<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { BOOKS, searchBooks, getBookById, type Book } from '@/data/books'
import { renderMarkdown } from '@/utils/markdown'

const router = useRouter()

// ── 用户显示名 ────────────────────────────────
const displayName = computed(() => {
  try {
    const raw = localStorage.getItem('user')
    if (raw) {
      const u = JSON.parse(raw) as { username?: string; name?: string }
      return u.username || u.name || '演示用户'
    }
  } catch { /* ignore */ }
  return '薛晓演示用户'
})

// ── 视图状态 ──────────────────────────────────
type ViewMode = 'list' | 'detail'
const viewMode = ref<ViewMode>('list')
const currentBook = ref<Book | null>(null)
const detailTab = ref<'summary' | 'chapters' | 'ai'>('summary')
const searchQuery = ref('')
const selectedCategory = ref('all')

// ── 分类 ──────────────────────────────────────
const categories = [
  { id: 'all', label: '全部' },
  { id: 'TCP', label: 'TCP/IP' },
  { id: 'RFC', label: 'RFC 标准' },
  { id: 'HTTP', label: 'HTTP' },
  { id: 'DNS', label: 'DNS' },
  { id: 'IPv6', label: 'IPv6' },
  { id: '安全', label: '网络安全' },
  { id: '教材', label: '经典教材' },
]

// ── 协议颜色映射 ───────────────────────────────
const catColors: Record<string, string> = {
  RFC: '#64748B', TCP: '#2563EB', HTTP: '#EA580C',
  QUIC: '#9333EA', DNS: '#059669', IPv4: '#0891B2',
  IPv6: '#0284C7', '安全': '#DC2626', '华为': '#CC0000',
  '教材': '#4F46E5', OSI: '#7C3AED',
}
function bookCat(book: Book): string {
  for (const t of book.tags) if (catColors[t]) return t
  return 'RFC'
}
function bookColor(book: Book): string { return catColors[bookCat(book)] || '#6366F1' }

// ── 过滤书籍 ──────────────────────────────────
const filteredBooks = computed(() => {
  let books = searchBooks(searchQuery.value)
  if (selectedCategory.value !== 'all') {
    const cat = selectedCategory.value.toLowerCase()
    books = books.filter(b => b.tags.some(t => t.toLowerCase().includes(cat)))
  }
  return books
})

// ── 书签 ──────────────────────────────────────
const bookmarked = ref<Set<string>>(new Set())
function toggleBookmark(id: string, e?: Event) {
  e?.stopPropagation()
  if (bookmarked.value.has(id)) bookmarked.value.delete(id)
  else bookmarked.value.add(id)
}

// ── 右键 AI 操作层 ─────────────────────────────
const activeOverlayId = ref<string | null>(null)
function showCardOverlay(bookId: string, e: MouseEvent) {
  e.preventDefault()
  activeOverlayId.value = activeOverlayId.value === bookId ? null : bookId
}
function closeOverlay() {
  activeOverlayId.value = null
}
function handleOverlayAction(fn: () => void) {
  closeOverlay()
  fn()
}

// ── 章节 / AI ────────────────────────────────
const currentChapterIdx = ref(0)
const currentChapterContent = computed(() => {
  if (!currentBook.value) return ''
  const ch = currentBook.value.chapters[currentChapterIdx.value]
  return ch ? renderMarkdown(ch.content) : ''
})
const aiQuestion = ref('')
const aiAnswer = ref('')
const aiLoading = ref(false)

// ── AI 推荐 ───────────────────────────────────
const aiRecs = [
  { title: 'TCP三次握手深入分析', match: 96, tag: 'TCP', color: '#2563EB' },
  { title: 'HTTP/3 QUIC 协议', match: 92, tag: 'HTTP', color: '#EA580C' },
  { title: 'DNS 解析实验', match: 88, tag: 'DNS', color: '#059669' },
]

// ── 统计数据 ──────────────────────────────────
const statsData = computed(() => [
  { value: BOOKS.length, label: '教材资源', icon: '📘', color: '#2563EB' },
  { value: BOOKS.filter(b => b.tags.includes('RFC')).length, label: 'RFC 文档', icon: '📋', color: '#9333EA' },
  { value: 78, label: '实验案例', icon: '🔬', color: '#059669' },
  { value: 156, label: '知识节点', icon: '🧠', color: '#D97706' },
])

// ── 技能雷达 (from S2) ────────────────────────
const radarSkills = [
  { label: 'TCP', value: 86 },
  { label: 'HTTP', value: 75 },
  { label: 'Routing', value: 61 },
  { label: 'Security', value: 55 },
  { label: 'Coding', value: 68 },
  { label: 'Network', value: 72 },
]
const RCX = 100, RCY = 96, RR = 58

function radarPt(idx: number, val: number): string {
  const angle = (Math.PI * 2 * idx) / radarSkills.length - Math.PI / 2
  const r = (val / 100) * RR
  return `${RCX + r * Math.cos(angle)},${RCY + r * Math.sin(angle)}`
}
function radarOuterPt(idx: number): string {
  const angle = (Math.PI * 2 * idx) / radarSkills.length - Math.PI / 2
  return `${RCX + RR * Math.cos(angle)},${RCY + RR * Math.sin(angle)}`
}
function radarLblPos(idx: number) {
  const angle = (Math.PI * 2 * idx) / radarSkills.length - Math.PI / 2
  const d = RR + 21
  return { x: RCX + d * Math.cos(angle), y: RCY + d * Math.sin(angle) }
}
const radarPolygon = computed(() =>
  radarSkills.map((s, i) => radarPt(i, s.value)).join(' ')
)

// ── Agent 日志 (from S2) ──────────────────────
const agentLogs = [
  { time: '14:22:01', agent: 'DiagnosisAgent', msg: '分析TCP知识点掌握度', hi: true },
  { time: '14:22:03', agent: 'ProfilerAgent', msg: '更新能力画像 TCP:86%', hi: true },
  { time: '14:22:08', agent: 'PathPlanner', msg: '推荐路径: RFC9293 → QUIC', hi: false },
  { time: '14:22:12', agent: 'ResourceGen', msg: '生成TCP练习题 x3', hi: false },
  { time: '14:22:18', agent: 'ChallengerAgent', msg: '触发知识挑战模式', hi: false },
  { time: '14:22:25', agent: 'TrustAgent', msg: '校验答案置信度: 0.92', hi: false },
]

// ── 操作函数 ──────────────────────────────────
async function askAI() {
  if (!aiQuestion.value.trim() || !currentBook.value || aiLoading.value) return
  aiLoading.value = true; aiAnswer.value = ''
  try {
    const res = await fetch('/api/v1/resources/generate', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        knowledge_point: `[关于《${currentBook.value.title}》] ${aiQuestion.value}`,
        resource_type: 'doc', difficulty: 3,
      }),
    })
    if (res.ok) { const d = await res.json(); aiAnswer.value = d.content || d.description || '暂无回答。' }
    else { aiAnswer.value = '服务暂时不可用。' }
  } catch { aiAnswer.value = '请先确保后端服务正常运行。' }
  finally { aiLoading.value = false }
}

function openDetail(book: Book) {
  currentBook.value = book; viewMode.value = 'detail'
  detailTab.value = 'summary'; aiAnswer.value = ''; currentChapterIdx.value = 0
}
function openDetailAI(book: Book) {
  currentBook.value = book; viewMode.value = 'detail'
  detailTab.value = 'ai'; aiAnswer.value = ''; currentChapterIdx.value = 0
}
function backToList() { viewMode.value = 'list'; currentBook.value = null }
function openReader(bookId: string) { router.push(`/bookhouse/${bookId}/read`) }
function openZlib(book: Book, e?: Event) {
  e?.stopPropagation()
  window.open(`https://z-library.sk/s/${encodeURIComponent(book.title)}`, '_blank', 'noopener,noreferrer')
}
onMounted(() => {
  const b = getBookById(new URLSearchParams(window.location.search).get('book') || '')
  if (b) openDetail(b)
  // 点击页面其他区域关闭右键菜单
  document.addEventListener('click', closeOverlay)
  document.addEventListener('contextmenu', (e) => {
    // 仅当点击的不是卡片时才关闭
    if (!(e.target as HTMLElement).closest('.bk-card')) closeOverlay()
  })
})

onUnmounted(() => {
  document.removeEventListener('click', closeOverlay)
})
</script>

<template>
  <div class="bk-page">

    <!-- ═══════ LIST VIEW ═══════ -->
    <template v-if="viewMode === 'list'">

      <!-- ① 顶部用户栏 (from S2) -->
      <div class="bk-topbar">
        <div class="bk-topbar-inner">
          <div class="bk-page-tag">
            <svg viewBox="0 0 16 16" fill="currentColor" style="width:11px;height:11px"><path d="M2 3a1 1 0 011-1h10a1 1 0 011 1v8a1 1 0 01-1 1H3a1 1 0 01-1-1V3z"/></svg>
            教材书库
          </div>
          <div class="bk-topbar-right">
            <span class="bk-user-txt" @click="router.push('/profile')" style="cursor:pointer">Hi, {{ displayName }} ▾</span>
            <button class="bk-bell" title="通知" @click="router.push('/logs')">
              <svg viewBox="0 0 20 20" fill="currentColor" style="width:14px;height:14px">
                <path d="M10 2a6 6 0 00-6 6v3.586l-.707.707A1 1 0 004 14h12a1 1 0 00.707-1.707L16 11.586V8a6 6 0 00-6-6zM10 18a3 3 0 01-3-3h6a3 3 0 01-3 3z"/>
              </svg>
            </button>
          </div>
        </div>
      </div>

      <!-- ② Hero Banner -->
      <section class="bk-hero">
        <div class="bk-hero-inner">
          <div class="bk-hero-left">
            <div class="bk-badge"><span class="badge-spark">✦</span> AI 驱动知识中心</div>
            <h1 class="bk-hero-title">计算机网络数字书库</h1>
            <p class="bk-hero-desc">基于 RFC 标准 · 教材章节 · 实验案例构建的智能知识体系</p>
            <div class="bk-search-wrap">
              <div class="bk-sparkle">✦</div>
              <input v-model="searchQuery" class="bk-search-inp" placeholder="语义搜索：协议、作者、知识点…"/>
              <div class="bk-ai-tag">AI ✦</div>
              <button class="bk-search-btn" aria-label="搜索">
                <svg viewBox="0 0 20 20" fill="currentColor" style="width:12px;height:12px">
                  <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z"/>
                </svg>
              </button>
            </div>
          </div>

          <!-- 知识图谱动画 -->
          <div class="bk-hero-graph" aria-hidden="true">
            <svg viewBox="0 0 320 240" class="bk-kg">
              <defs>
                <filter id="bkglow"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
              </defs>
              <line x1="160" y1="120" x2="75" y2="62" class="bk-ke"/><line x1="160" y1="120" x2="245" y2="62" class="bk-ke"/>
              <line x1="160" y1="120" x2="52" y2="162" class="bk-ke"/><line x1="160" y1="120" x2="268" y2="162" class="bk-ke"/>
              <line x1="160" y1="120" x2="160" y2="205" class="bk-ke"/>
              <line x1="75" y1="62" x2="245" y2="62" class="bk-ke-t"/><line x1="36" y1="95" x2="75" y2="62" class="bk-ke-t"/>
              <line x1="284" y1="102" x2="245" y2="62" class="bk-ke-t"/>
              <circle cx="160" cy="120" r="24" class="bk-kc" filter="url(#bkglow)"/>
              <text x="160" y="125" class="bk-klc" text-anchor="middle">网络</text>
              <circle cx="75" cy="62" r="19" class="bk-kn bkn1"/><text x="75" y="67" class="bk-kl" text-anchor="middle">TCP</text>
              <circle cx="245" cy="62" r="19" class="bk-kn bkn2"/><text x="245" y="67" class="bk-kl" text-anchor="middle">DNS</text>
              <circle cx="52" cy="162" r="16" class="bk-kn bkn3"/><text x="52" y="167" class="bk-kl" text-anchor="middle">UDP</text>
              <circle cx="268" cy="162" r="19" class="bk-kn bkn4"/><text x="268" y="167" class="bk-kl" text-anchor="middle">HTTP</text>
              <circle cx="160" cy="205" r="16" class="bk-kn bkn5"/><text x="160" y="210" class="bk-kl" text-anchor="middle">QUIC</text>
              <circle cx="36" cy="95" r="13" class="bk-kn bkn6"/><text x="36" y="99" class="bk-kl-sm" text-anchor="middle">IPv6</text>
              <circle cx="284" cy="102" r="13" class="bk-kn bkn7"/><text x="284" y="106" class="bk-kl-sm" text-anchor="middle">TLS</text>
            </svg>
          </div>
        </div>
      </section>

      <!-- ③ 统计卡片 -->
      <section class="bk-stats">
        <div v-for="s in statsData" :key="s.label" class="bk-stat-card">
          <div class="bk-stat-icon" :style="{ color: s.color, background: s.color+'18', borderColor: s.color+'30' }">{{ s.icon }}</div>
          <div>
            <div class="bk-stat-num" :style="{ color: s.color }">{{ s.value }}</div>
            <div class="bk-stat-lbl">{{ s.label }}</div>
          </div>
        </div>
      </section>

      <!-- ④ 分类筛选栏 -->
      <div class="bk-filter">
        <button v-for="cat in categories" :key="cat.id"
          :class="['bk-cat-btn', { active: selectedCategory === cat.id }]"
          :style="selectedCategory === cat.id && cat.id !== 'all'
            ? { background: (catColors[cat.id.toUpperCase()]||'#4F46E5')+'20', borderColor: catColors[cat.id.toUpperCase()]||'#4F46E5', color: catColors[cat.id.toUpperCase()]||'#4F46E5' }
            : {}"
          @click="selectedCategory = cat.id">{{ cat.label }}</button>
      </div>

      <!-- ⑤ 主体：书籍网格 + AI 侧边栏 -->
      <div class="bk-body">

        <!-- 书籍网格（横向卡片） -->
        <div class="bk-grid">
          <article v-for="book in filteredBooks" :key="book.id" class="bk-card"
            :style="{ '--accent': bookColor(book) }"
            @contextmenu.prevent="showCardOverlay(book.id, $event)">

            <!-- 顶部类别色细线 -->
            <div class="bk-card-accent" :style="{ background: bookColor(book) }"/>

            <!-- 封面（左侧列） -->
            <div class="bk-cover-side"
              :style="{ background: `linear-gradient(150deg, ${book.coverFrom}, ${book.coverTo})` }"
              @click="openDetail(book)">
              <div class="bk-cover-art" aria-hidden="true">
                <svg viewBox="0 0 88 118" :style="{ color: book.coverText }">
                  <circle cx="14" cy="20" r="2.5" fill="currentColor" opacity="0.35"/>
                  <circle cx="48" cy="12" r="3" fill="currentColor" opacity="0.4"/>
                  <circle cx="76" cy="30" r="2.5" fill="currentColor" opacity="0.3"/>
                  <circle cx="26" cy="58" r="3.5" fill="currentColor" opacity="0.45"/>
                  <circle cx="70" cy="72" r="2.5" fill="currentColor" opacity="0.3"/>
                  <circle cx="44" cy="96" r="3" fill="currentColor" opacity="0.38"/>
                  <circle cx="12" cy="82" r="2" fill="currentColor" opacity="0.25"/>
                  <line x1="14" y1="20" x2="48" y2="12" stroke="currentColor" stroke-width="0.8" opacity="0.2"/>
                  <line x1="48" y1="12" x2="76" y2="30" stroke="currentColor" stroke-width="0.8" opacity="0.2"/>
                  <line x1="14" y1="20" x2="26" y2="58" stroke="currentColor" stroke-width="0.8" opacity="0.18"/>
                  <line x1="76" y1="30" x2="70" y2="72" stroke="currentColor" stroke-width="0.8" opacity="0.18"/>
                  <line x1="26" y1="58" x2="44" y2="96" stroke="currentColor" stroke-width="0.8" opacity="0.18"/>
                  <line x1="70" y1="72" x2="44" y2="96" stroke="currentColor" stroke-width="0.8" opacity="0.18"/>
                  <line x1="12" y1="82" x2="26" y2="58" stroke="currentColor" stroke-width="0.8" opacity="0.15"/>
                </svg>
              </div>
              <span class="bk-cover-badge">{{ book.coverTag }}</span>
            </div>

            <!-- 信息区（右侧） -->
            <div class="bk-card-body">
              <div class="bk-card-top">
                <span class="bk-cat-dot" :style="{ background: bookColor(book) }"/>
                <span class="bk-cat-lbl" :style="{ color: bookColor(book) }">{{ bookCat(book) }}</span>
                <button class="bk-bookmark" :class="{ active: bookmarked.has(book.id) }"
                  @click="toggleBookmark(book.id, $event)">
                  <svg viewBox="0 0 24 24"
                    :fill="bookmarked.has(book.id) ? '#F59E0B' : 'none'"
                    :stroke="bookmarked.has(book.id) ? '#F59E0B' : '#CBD5E1'"
                    stroke-width="2" style="width:12px;height:12px">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"/>
                  </svg>
                </button>
              </div>
              <h3 class="bk-card-title" @click="openDetail(book)">{{ book.title }}</h3>
              <p class="bk-card-author">{{ book.author }}</p>
              <div class="bk-tags">
                <span v-for="tag in book.tags.slice(0,3)" :key="tag" class="bk-tag"
                  :style="{ background: bookColor(book)+'15', color: bookColor(book), borderColor: bookColor(book)+'35' }">
                  {{ tag }}
                </span>
              </div>
              <div class="bk-card-actions">
                <button class="bk-btn-primary"
                  :style="{ background: `linear-gradient(135deg, ${bookColor(book)}, ${bookColor(book)}cc)` }"
                  @click="openDetail(book)">内容摘要</button>
                <button class="bk-btn-ghost" @click="openZlib(book, $event)">原版 ↗</button>
              </div>
            </div>

            <!-- 右键 AI 操作层 -->
            <Transition name="overlay-fade">
              <div v-if="activeOverlayId === book.id" class="bk-hover-overlay"
                @click.stop>
                <div class="bk-overlay-hint">右键菜单</div>
                <button class="bk-hover-ai"
                  :style="{ background: `linear-gradient(135deg, ${bookColor(book)}, ${bookColor(book)}cc)` }"
                  @click="handleOverlayAction(() => openDetailAI(book))">🤖 AI 总结此文献</button>
                <button class="bk-hover-chat"
                  @click="handleOverlayAction(() => router.push('/chat'))">💬 结合此文献提问</button>
                <button class="bk-overlay-close" @click="closeOverlay" title="关闭">✕</button>
              </div>
            </Transition>
          </article>

          <div v-if="filteredBooks.length === 0" class="bk-empty">
            <div style="font-size:40px;margin-bottom:10px">📭</div>
            <p>未找到相关资源</p>
            <button @click="searchQuery='';selectedCategory='all'">清除筛选</button>
          </div>
        </div>

        <!-- AI 侧边栏：推荐 + 技能雷达 -->
        <aside class="bk-sidebar">
          <!-- Alice 推荐 -->
          <div class="bk-sid-hdr">
            <div class="bk-sid-ava"><span class="ava-spark">✦</span><span>A</span></div>
            <div>
              <div class="bk-sid-name">Alice 推荐</div>
              <div class="bk-sid-sub">基于你的学习画像</div>
            </div>
          </div>
          <div class="bk-recs">
            <div v-for="(rec, i) in aiRecs" :key="i" class="bk-rec">
              <div class="bk-rec-rank" :style="{ color: rec.color, borderColor: rec.color+'44', background: rec.color+'15' }">{{ i+1 }}</div>
              <div class="bk-rec-body">
                <div class="bk-rec-title">{{ rec.title }}</div>
                <div class="bk-rec-bar-bg"><div class="bk-rec-bar" :style="{ width: rec.match+'%', background: rec.color }"/></div>
                <div class="bk-rec-pct" :style="{ color: rec.color }">匹配度 {{ rec.match }}%</div>
              </div>
            </div>
          </div>

          <button class="bk-chat-btn" @click="router.push('/chat')">💬 与 Alice 对话</button>

          <!-- ② 技能雷达 (from S2) -->
          <div class="bk-radar-sec">
            <div class="bk-radar-ttl">Skill Radar Chart</div>
            <svg viewBox="0 0 200 188" class="bk-radar-svg">
              <defs>
                <filter id="bkradar-glow">
                  <feGaussianBlur stdDeviation="2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
                </filter>
              </defs>
              <!-- 网格环 -->
              <polygon v-for="r in [20,39,58]" :key="r"
                :points="radarSkills.map((_,i) => { const a=(Math.PI*2*i/radarSkills.length)-Math.PI/2; return `${RCX+r*Math.cos(a)},${RCY+r*Math.sin(a)}`}).join(' ')"
                fill="none" stroke="rgba(99,102,241,0.2)" stroke-width="0.8"/>
              <!-- 网格线 -->
              <line v-for="(_,i) in radarSkills" :key="i"
                :x1="RCX" :y1="RCY"
                :x2="parseFloat(radarOuterPt(i).split(',')[0])"
                :y2="parseFloat(radarOuterPt(i).split(',')[1])"
                stroke="rgba(99,102,241,0.15)" stroke-width="0.8"/>
              <!-- 数据多边形 -->
              <polygon :points="radarPolygon"
                fill="rgba(99,102,241,0.2)" stroke="#6366F1" stroke-width="1.8"
                filter="url(#bkradar-glow)"/>
              <!-- 数据点 -->
              <circle v-for="(s,i) in radarSkills" :key="s.label"
                :cx="parseFloat(radarPt(i,s.value).split(',')[0])"
                :cy="parseFloat(radarPt(i,s.value).split(',')[1])"
                r="3" fill="#818CF8" stroke="rgba(255,255,255,0.6)" stroke-width="1"/>
              <!-- 标签 + 数值 -->
              <g v-for="(s,i) in radarSkills" :key="s.label+'l'">
                <text :x="radarLblPos(i).x" :y="radarLblPos(i).y - 5"
                  class="bk-rlbl" text-anchor="middle">{{ s.label }}</text>
                <text :x="radarLblPos(i).x" :y="radarLblPos(i).y + 8"
                  class="bk-rval" text-anchor="middle" :style="{ fill: '#4F46E5' }">{{ s.value }}%</text>
              </g>
            </svg>
          </div>
        </aside>
      </div>

      <!-- ⑥ Agent 日志面板 (from S2) -->
      <div class="bk-log-wrap">
        <div class="bk-log-inner">
          <div class="bk-log-title">AGENT 日志</div>
          <div class="bk-log-rows">
            <div v-for="(log, i) in agentLogs" :key="i" class="bk-log-row">
              <span class="bk-log-time">[{{ log.time }}]</span>
              <span class="bk-log-agent" :class="{ hi: log.hi }">{{ log.agent }}</span>
              <span class="bk-log-arrow"> → </span>
              <span class="bk-log-msg" :class="{ hi: log.hi }">{{ log.msg }}</span>
            </div>
          </div>
        </div>
      </div>

    </template>

    <!-- ═══════ DETAIL VIEW ═══════ -->
    <template v-else-if="currentBook">
      <div class="bk-detail">
        <div class="bk-det-toolbar">
          <button class="bk-back-btn" @click="backToList">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:13px;height:13px">
              <path stroke-linecap="round" stroke-linejoin="round" d="M10 19l-7-7m0 0l7-7m-7 7h18"/>
            </svg>
            返回书库
          </button>
          <span class="bk-breadcrumb">
            <span @click="backToList" style="cursor:pointer;color:#4F46E5">书库</span> / {{ currentBook.shortTitle }}
          </span>
          <div style="display:flex;gap:8px">
            <button class="bk-det-btn-p"
              :style="{ background: `linear-gradient(135deg, ${bookColor(currentBook)}, ${bookColor(currentBook)}cc)` }"
              @click="openReader(currentBook.id)">进入阅读器</button>
            <button class="bk-det-btn-g" @click="openZlib(currentBook)">获取原版 ↗</button>
          </div>
        </div>

        <div class="bk-det-hero">
          <div class="bk-det-cover"
            :style="{ background: `linear-gradient(150deg, ${currentBook.coverFrom}, ${currentBook.coverTo})`, boxShadow: `0 8px 30px ${bookColor(currentBook)}33` }">
            <span class="bk-cover-badge">{{ currentBook.coverTag }}</span>
          </div>
          <div class="bk-det-meta">
            <div class="bk-det-cat"
              :style="{ color: bookColor(currentBook), background: bookColor(currentBook)+'18', borderColor: bookColor(currentBook)+'44' }">
              {{ bookCat(currentBook) }}
            </div>
            <h1 class="bk-det-title">{{ currentBook.title }}</h1>
            <p class="bk-det-author">{{ currentBook.author }}</p>
            <p class="bk-det-pos">{{ currentBook.academicPosition }}</p>
            <div class="bk-tags" style="margin-bottom:12px">
              <span v-for="tag in currentBook.tags" :key="tag" class="bk-tag"
                :style="{ background: bookColor(currentBook)+'15', color: bookColor(currentBook), borderColor: bookColor(currentBook)+'35' }">
                {{ tag }}
              </span>
            </div>
            <p class="bk-det-desc">{{ currentBook.description }}</p>
          </div>
        </div>

        <div class="bk-det-tabs">
          <button v-for="t in [{id:'summary',label:'内容摘要'},{id:'chapters',label:'章节内容'},{id:'ai',label:'🤖 AI 顾问'}]"
            :key="t.id" :class="['bk-dtab', { active: detailTab === t.id }]"
            :style="detailTab === t.id ? { color: bookColor(currentBook), borderBottomColor: bookColor(currentBook) } : {}"
            @click="detailTab = (t.id as any)">{{ t.label }}</button>
        </div>

        <div class="bk-det-content">
          <!-- 摘要 -->
          <div v-if="detailTab === 'summary'" class="bk-summary">
            <div class="bk-sum-card" :style="{ borderTopColor: bookColor(currentBook) }">
              <h4 :style="{ color: bookColor(currentBook) }">核心内容</h4>
              <p>{{ currentBook.coreContent }}</p>
            </div>
            <div class="bk-sum-card" :style="{ borderTopColor: bookColor(currentBook) }">
              <h4 :style="{ color: bookColor(currentBook) }">学术定位</h4>
              <p>{{ currentBook.academicPosition }}</p>
            </div>
            <div class="bk-sum-card" :style="{ borderTopColor: bookColor(currentBook) }">
              <h4 :style="{ color: bookColor(currentBook) }">章节目录</h4>
              <div class="bk-ch-list">
                <div v-for="(ch, i) in currentBook.chapters" :key="ch.id"
                  class="bk-ch-item" :style="{ '--acc': bookColor(currentBook) }"
                  @click="detailTab='chapters';currentChapterIdx=i">
                  <span class="bk-ch-num" :style="{ color: bookColor(currentBook) }">{{ String(i+1).padStart(2,'0') }}</span>
                  <span class="bk-ch-name">{{ ch.title }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 章节 -->
          <div v-else-if="detailTab === 'chapters'">
            <div class="bk-ch-nav">
              <button v-for="(ch, i) in currentBook.chapters" :key="ch.id"
                :class="['bk-chnav-btn', { active: currentChapterIdx === i }]"
                :style="currentChapterIdx === i ? { borderColor: bookColor(currentBook), color: bookColor(currentBook), background: bookColor(currentBook)+'15' } : {}"
                @click="currentChapterIdx = i">{{ ch.title }}</button>
            </div>
            <div class="bk-ch-body bk-md" v-html="currentChapterContent"/>
          </div>

          <!-- AI 顾问 -->
          <div v-else-if="detailTab === 'ai'" class="bk-ai-tab">
            <div class="bk-ai-input-wrap" :style="{ borderColor: bookColor(currentBook)+'66' }">
              <span class="bk-ai-spark" :style="{ color: bookColor(currentBook) }">✦</span>
              <input v-model="aiQuestion" class="bk-ai-inp"
                placeholder="关于此文献，输入你的问题…" @keyup.enter="askAI"/>
              <button class="bk-ai-send" :disabled="aiLoading"
                :style="{ background: `linear-gradient(135deg, ${bookColor(currentBook)}, ${bookColor(currentBook)}aa)` }"
                @click="askAI">{{ aiLoading ? '思考中…' : '提问' }}</button>
            </div>
            <div v-if="aiAnswer" class="bk-ai-ans bk-md" v-html="renderMarkdown(aiAnswer)"/>
            <div v-if="!aiAnswer && !aiLoading" class="bk-ai-hints">
              <button v-for="q in ['三次握手的原因？','IP路由转发流程？','协议安全威胁？']"
                :key="q" class="bk-hint-btn"
                :style="{ background: bookColor(currentBook)+'14', borderColor: bookColor(currentBook)+'44', color: bookColor(currentBook) }"
                @click="aiQuestion=q">{{ q }}</button>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
/* ─── Page base ─────────────────────────────────── */
.bk-page {
  min-height: 100vh;
  background: #EEF2FF;
  background-image: radial-gradient(circle, rgba(99,102,241,0.09) 1px, transparent 1px);
  background-size: 28px 28px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  color: #1E293B;
}

/* ─── Top Bar (from S2) ──────────────────────────── */
.bk-topbar {
  background: rgba(255,255,255,0.85);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(99,102,241,0.12);
  padding: 10px 28px;
  position: sticky; top: 0; z-index: 50;
}
.bk-topbar-inner { max-width: 1200px; margin: 0 auto; display: flex; align-items: center; justify-content: space-between; }
.bk-page-tag {
  display: inline-flex; align-items: center; gap: 5px;
  font-size: 12px; font-weight: 600; color: #4F46E5;
}
.bk-topbar-right { display: flex; align-items: center; gap: 10px; }
.bk-user-txt { font-size: 13px; color: #475569; cursor: pointer; }
.bk-user-txt:hover { color: #1E293B; }
.bk-bell {
  width: 30px; height: 30px; border-radius: 8px;
  background: rgba(99,102,241,0.1); border: 1px solid rgba(99,102,241,0.2);
  display: flex; align-items: center; justify-content: center; cursor: pointer;
  color: #6366F1; transition: all 0.15s;
}
.bk-bell:hover { background: rgba(99,102,241,0.2); }

/* ─── Hero ───────────────────────────────────────── */
.bk-hero {
  background: linear-gradient(135deg, #1E1B4B 0%, #3730A3 40%, #1E3A8A 70%, #0F172A 100%);
  padding: 32px 28px 28px; position: relative; overflow: hidden;
}
.bk-hero::before {
  content: '';
  position: absolute; inset: 0;
  background: url("data:image/svg+xml,%3Csvg width='40' height='40' viewBox='0 0 40 40' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='%23ffffff' fill-opacity='0.02'%3E%3Cpath d='M20 20h-2v-2h2v2zm0-4h-2v-2h2v2zm0 8h-2v-2h2v2zm4-4h-2v-2h2v2zm-8 0h-2v-2h2v2z'/%3E%3C/g%3E%3C/svg%3E");
}
.bk-hero-inner { max-width: 1200px; margin: 0 auto; display: flex; align-items: center; gap: 36px; position: relative; z-index: 1; }
.bk-hero-left { flex: 1; min-width: 0; }
.bk-badge { display: inline-flex; align-items: center; gap: 5px; background: rgba(255,255,255,0.12); border: 1px solid rgba(255,255,255,0.2); border-radius: 20px; padding: 4px 12px; font-size: 12px; color: #A5B4FC; margin-bottom: 12px; backdrop-filter: blur(4px); }
.badge-spark { color: #FBBF24; }
.bk-hero-title { font-size: 28px; font-weight: 800; color: #fff; margin: 0 0 8px; line-height: 1.2; }
.bk-hero-desc { font-size: 13px; color: #A5B4FC; margin: 0 0 20px; line-height: 1.6; }

.bk-search-wrap {
  display: flex; align-items: center;
  background: rgba(255,255,255,0.12); border: 1.5px solid rgba(99,102,241,0.5);
  border-radius: 12px; padding: 0 12px; max-width: 500px;
  backdrop-filter: blur(12px); box-shadow: 0 4px 20px rgba(99,102,241,0.15);
  transition: all 0.2s;
}
.bk-search-wrap:focus-within { border-color: #818CF8; box-shadow: 0 0 0 3px rgba(99,102,241,0.25); background: rgba(255,255,255,0.16); }
.bk-sparkle { font-size: 13px; color: #818CF8; flex-shrink: 0; }
.bk-search-inp { flex: 1; border: none; outline: none; padding: 12px 10px; font-size: 13px; color: #fff; background: transparent; }
.bk-search-inp::placeholder { color: rgba(255,255,255,0.35); }
.bk-ai-tag { font-size: 10px; font-weight: 800; color: #FBBF24; background: rgba(251,191,36,0.15); border-radius: 5px; padding: 2px 7px; flex-shrink: 0; }
.bk-search-btn { width: 28px; height: 28px; border-radius: 7px; flex-shrink: 0; margin-left: 6px; background: linear-gradient(135deg, #4F46E5, #7C3AED); border: none; color: #fff; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: opacity 0.15s; }
.bk-search-btn:hover { opacity: 0.85; }

/* Knowledge Graph */
.bk-hero-graph { width: 310px; flex-shrink: 0; }
.bk-kg { width: 100%; height: auto; }
.bk-ke { stroke: rgba(148,163,250,0.3); stroke-width: 1.2; }
.bk-ke-t { stroke: rgba(148,163,250,0.15); stroke-width: 1; }
.bk-kc { fill: #4F46E5; }
.bk-klc { font-size: 10.5px; font-weight: 700; fill: #fff; }
.bk-kn { fill: rgba(99,102,241,0.35); stroke: rgba(165,180,252,0.5); stroke-width: 1.5; }
.bk-kl { font-size: 9px; font-weight: 600; fill: #E0E7FF; }
.bk-kl-sm { font-size: 7.5px; fill: #C7D2FE; }
.bkn1 { animation: bkfloat 4s ease-in-out infinite; }
.bkn2 { animation: bkfloat 5s ease-in-out infinite 0.8s; }
.bkn3 { animation: bkfloat 4.5s ease-in-out infinite 1.2s; }
.bkn4 { animation: bkfloat 5.5s ease-in-out infinite 0.4s; }
.bkn5 { animation: bkfloat 4.2s ease-in-out infinite 1.6s; }
.bkn6 { animation: bkfloat 6s ease-in-out infinite 0.2s; }
.bkn7 { animation: bkfloat 5.2s ease-in-out infinite 1s; }
@keyframes bkfloat { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-5px); } }

/* ─── Stats ──────────────────────────────────────── */
.bk-stats {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px;
  max-width: 1200px; margin: 0 auto; padding: 20px 28px 0;
}
.bk-stat-card {
  background: rgba(255,255,255,0.9); backdrop-filter: blur(8px);
  border-radius: 14px; padding: 15px 18px; display: flex; align-items: center; gap: 12px;
  border: 1px solid rgba(99,102,241,0.13); box-shadow: 0 2px 12px rgba(99,102,241,0.07);
  transition: transform 0.2s, box-shadow 0.2s;
}
.bk-stat-card:hover { transform: translateY(-2px); box-shadow: 0 8px 22px rgba(99,102,241,0.14); }
.bk-stat-icon { width: 40px; height: 40px; border-radius: 11px; font-size: 18px; display: flex; align-items: center; justify-content: center; border: 1px solid; flex-shrink: 0; }
.bk-stat-num { font-size: 23px; font-weight: 800; line-height: 1; }
.bk-stat-lbl { font-size: 11px; color: #64748B; margin-top: 2px; }

/* ─── Filter ──────────────────────────────────────── */
.bk-filter {
  max-width: 1200px; margin: 16px auto 0; padding: 0 28px;
  display: flex; flex-wrap: wrap; gap: 6px;
}
.bk-cat-btn {
  padding: 6px 15px; border-radius: 20px; font-size: 12.5px; font-weight: 500;
  border: 1.5px solid rgba(99,102,241,0.2);
  background: rgba(255,255,255,0.8); backdrop-filter: blur(4px);
  color: #64748B; cursor: pointer; transition: all 0.15s;
}
.bk-cat-btn:hover { border-color: rgba(99,102,241,0.5); color: #4F46E5; }
.bk-cat-btn.active:not([style*="background"]) {
  background: linear-gradient(135deg, #4F46E5, #7C3AED);
  border-color: transparent; color: #fff;
  box-shadow: 0 2px 10px rgba(79,70,229,0.3);
}

/* ─── Body ───────────────────────────────────────── */
.bk-body {
  max-width: 1200px; margin: 16px auto 0; padding: 0 28px;
  display: flex; gap: 20px; align-items: flex-start;
}

/* ─── Book Grid (横向卡片) ────────────────────────── */
.bk-grid {
  flex: 1; min-width: 0;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(290px, 1fr));
  gap: 12px;
  align-content: start;
}

/* 横向卡片 */
.bk-card {
  background: rgba(255,255,255,0.92);
  backdrop-filter: blur(8px);
  border-radius: 12px; overflow: hidden;
  border: 1px solid rgba(99,102,241,0.14);
  box-shadow: 0 2px 12px rgba(99,102,241,0.07);
  transition: transform 0.2s, box-shadow 0.2s, border-color 0.2s;
  position: relative;
  display: flex; flex-direction: row;
  min-height: 120px;
}
.bk-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 28px rgba(99,102,241,0.18);
  border-color: var(--accent, #4F46E5);
}

.bk-card-accent {
  position: absolute; top: 0; left: 0; right: 0; height: 2.5px;
  border-radius: 12px 12px 0 0; z-index: 1;
}

/* 封面（左侧） */
.bk-cover-side {
  width: 86px; flex-shrink: 0;
  position: relative; cursor: pointer;
  overflow: hidden; border-radius: 12px 0 0 12px;
}
.bk-cover-art { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; }
.bk-cover-art svg { width: 100%; height: 100%; }
.bk-cover-badge {
  position: absolute; bottom: 5px; right: 4px;
  font-size: 7.5px; font-weight: 700; letter-spacing: 0.8px; text-transform: uppercase;
  background: rgba(0,0,0,0.28); border-radius: 3px; padding: 1px 5px; color: rgba(255,255,255,0.88);
}

/* 卡片信息区（右侧） */
.bk-card-body {
  flex: 1; min-width: 0; padding: 10px 12px 11px;
  display: flex; flex-direction: column;
}
.bk-card-top { display: flex; align-items: center; gap: 4px; margin-bottom: 5px; }
.bk-cat-dot { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }
.bk-cat-lbl { font-size: 10px; font-weight: 700; letter-spacing: 0.3px; flex: 1; }
.bk-bookmark { background: none; border: none; padding: 1px; cursor: pointer; display: flex; margin-left: auto; transition: transform 0.15s; }
.bk-bookmark:hover { transform: scale(1.15); }
.bk-card-title {
  font-size: 12.5px; font-weight: 600; color: #1E293B; margin-bottom: 2px; cursor: pointer;
  display: -webkit-box; -webkit-line-clamp: 2; line-clamp: 2;
  -webkit-box-orient: vertical; overflow: hidden; line-height: 1.4;
}
.bk-card-title:hover { color: var(--accent, #4F46E5); }
.bk-card-author { font-size: 10px; color: #94A3B8; margin-bottom: 5px; }
.bk-tags { display: flex; flex-wrap: wrap; gap: 3px; margin-bottom: 7px; }
.bk-tag { padding: 1px 5px; font-size: 9px; font-weight: 500; border-radius: 3px; border: 1px solid; }
.bk-card-actions { display: flex; gap: 5px; margin-top: auto; }
.bk-btn-primary {
  flex: 1; padding: 5px 4px; font-size: 11px; font-weight: 600;
  border: none; border-radius: 6px; color: #fff; cursor: pointer;
  transition: opacity 0.15s; white-space: nowrap; text-align: center;
}
.bk-btn-primary:hover { opacity: 0.86; }
.bk-btn-ghost {
  padding: 5px 8px; font-size: 11px;
  border: 1.5px solid #E2E8F0; background: transparent;
  color: #64748B; border-radius: 6px; cursor: pointer; transition: all 0.15s; white-space: nowrap;
}
.bk-btn-ghost:hover { border-color: var(--accent, #4F46E5); color: var(--accent, #4F46E5); }

/* 右键 AI 层（通过 v-if 控制） */
.bk-hover-overlay {
  position: absolute; inset: 0;
  background: rgba(238,242,255,0.95);
  backdrop-filter: blur(8px); border-radius: 12px;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  gap: 8px; padding: 14px 12px;
  z-index: 10;
}
.bk-overlay-hint {
  font-size: 9.5px; font-weight: 700; letter-spacing: 1.2px;
  text-transform: uppercase; color: #94A3B8;
  border: 1px solid #E2E8F0; border-radius: 4px;
  padding: 2px 8px; margin-bottom: 2px;
  background: #fff;
}
.bk-hover-ai {
  width: 100%; padding: 9px 8px; border-radius: 8px;
  border: none; color: #fff; font-size: 12px; font-weight: 600;
  cursor: pointer; transition: opacity 0.15s; text-align: center;
  box-shadow: 0 3px 10px rgba(0,0,0,0.15);
}
.bk-hover-ai:hover { opacity: 0.88; }
.bk-hover-chat {
  width: 100%; padding: 8px 8px; border-radius: 8px;
  background: rgba(99,102,241,0.1); border: 1.5px solid rgba(99,102,241,0.3);
  color: #4F46E5; font-size: 12px; cursor: pointer;
  transition: all 0.15s; text-align: center;
}
.bk-hover-chat:hover { background: rgba(99,102,241,0.22); }
.bk-overlay-close {
  width: 24px; height: 24px; border-radius: 50%;
  background: rgba(100,116,139,0.12); border: none;
  color: #94A3B8; font-size: 12px; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.15s; margin-top: 2px;
}
.bk-overlay-close:hover { background: rgba(100,116,139,0.22); color: #475569; }

/* 过渡动画 */
.overlay-fade-enter-active, .overlay-fade-leave-active { transition: opacity 0.18s ease, transform 0.18s ease; }
.overlay-fade-enter-from, .overlay-fade-leave-to { opacity: 0; transform: scale(0.97); }
.overlay-fade-enter-to, .overlay-fade-leave-from { opacity: 1; transform: scale(1); }

.bk-empty { grid-column: 1/-1; text-align: center; padding: 50px 20px; color: #94A3B8; }
.bk-empty p { font-size: 14px; margin: 0 0 12px; }
.bk-empty button { background: rgba(79,70,229,0.1); border: none; color: #4F46E5; padding: 7px 16px; border-radius: 7px; cursor: pointer; }

/* ─── AI 侧边栏 ───────────────────────────────────── */
.bk-sidebar {
  width: 248px; flex-shrink: 0;
  background: rgba(255,255,255,0.88);
  backdrop-filter: blur(16px);
  border-radius: 16px; border: 1px solid rgba(99,102,241,0.18);
  box-shadow: 0 4px 18px rgba(99,102,241,0.09);
  padding: 18px; position: sticky; top: 54px;
}
.bk-sid-hdr { display: flex; align-items: center; gap: 10px; margin-bottom: 16px; padding-bottom: 14px; border-bottom: 1px solid rgba(99,102,241,0.1); }
.bk-sid-ava {
  width: 36px; height: 36px; border-radius: 11px; flex-shrink: 0;
  background: linear-gradient(135deg, #4F46E5, #7C3AED);
  display: flex; align-items: center; justify-content: center;
  font-size: 14px; font-weight: 800; color: #fff;
  position: relative; overflow: hidden;
}
.ava-spark { font-size: 9px; position: absolute; top: 3px; right: 4px; color: #FDE68A; }
.bk-sid-name { font-size: 13px; font-weight: 700; color: #1E293B; }
.bk-sid-sub { font-size: 10px; color: #94A3B8; }

.bk-recs { display: flex; flex-direction: column; gap: 11px; margin-bottom: 14px; }
.bk-rec { display: flex; align-items: flex-start; gap: 8px; }
.bk-rec-rank { width: 19px; height: 19px; border-radius: 50%; flex-shrink: 0; font-size: 9.5px; font-weight: 700; border: 1px solid; display: flex; align-items: center; justify-content: center; margin-top: 1px; }
.bk-rec-body { flex: 1; }
.bk-rec-title { font-size: 11.5px; font-weight: 600; color: #1E293B; margin-bottom: 4px; line-height: 1.4; }
.bk-rec-bar-bg { height: 3.5px; background: #EEF2FF; border-radius: 2px; margin-bottom: 3px; overflow: hidden; }
.bk-rec-bar { height: 100%; border-radius: 2px; }
.bk-rec-pct { font-size: 10px; font-weight: 600; }

.bk-chat-btn {
  width: 100%; padding: 9px; border-radius: 10px;
  background: linear-gradient(135deg, #4F46E5, #7C3AED);
  color: #fff; border: none; font-size: 12.5px; font-weight: 600;
  cursor: pointer; transition: opacity 0.15s; margin-bottom: 14px;
}
.bk-chat-btn:hover { opacity: 0.9; }

/* 技能雷达 (from S2) */
.bk-radar-sec { border-top: 1px solid rgba(99,102,241,0.1); padding-top: 14px; }
.bk-radar-ttl { font-size: 11px; font-weight: 700; color: #1E293B; text-align: center; margin-bottom: 8px; letter-spacing: 0.5px; }
.bk-radar-svg { width: 100%; height: auto; }
.bk-rlbl { font-size: 8px; fill: #64748B; font-weight: 600; }
.bk-rval { font-size: 7.5px; font-weight: 700; }

/* ─── Agent 日志 (from S2) ───────────────────────── */
.bk-log-wrap {
  max-width: 1200px; margin: 14px auto 32px; padding: 0 28px;
}
.bk-log-inner {
  background: rgba(15,23,42,0.06);
  border: 1px solid rgba(99,102,241,0.14);
  border-radius: 12px; padding: 14px 20px;
}
.bk-log-title { font-size: 11px; font-weight: 700; color: #475569; margin-bottom: 8px; letter-spacing: 1.5px; text-transform: uppercase; }
.bk-log-rows { display: flex; flex-direction: column; gap: 3px; }
.bk-log-row { font-size: 11px; font-family: 'Courier New', monospace; line-height: 1.8; display: flex; gap: 5px; flex-wrap: wrap; }
.bk-log-time { color: #94A3B8; }
.bk-log-agent { color: #94A3B8; }
.bk-log-agent.hi { color: #4ADE80; font-weight: 700; }
.bk-log-arrow { color: #CBD5E1; }
.bk-log-msg { color: #94A3B8; }
.bk-log-msg.hi { color: #38BDF8; }

/* ─── Detail View ─────────────────────────────────── */
.bk-detail { max-width: 1100px; margin: 0 auto; padding: 22px 28px 60px; }
.bk-det-toolbar { display: flex; align-items: center; gap: 12px; margin-bottom: 22px; padding-bottom: 14px; border-bottom: 1px solid rgba(99,102,241,0.14); }
.bk-back-btn {
  display: flex; align-items: center; gap: 5px;
  background: rgba(255,255,255,0.9); backdrop-filter: blur(4px);
  border: 1.5px solid rgba(99,102,241,0.2); border-radius: 8px;
  color: #64748B; padding: 6px 13px; cursor: pointer; font-size: 12.5px; transition: all 0.15s;
}
.bk-back-btn:hover { border-color: #4F46E5; color: #4F46E5; }
.bk-breadcrumb { flex: 1; font-size: 12px; color: #94A3B8; }
.bk-det-btn-p { padding: 7px 14px; border-radius: 8px; font-size: 12.5px; font-weight: 600; border: none; color: #fff; cursor: pointer; transition: opacity 0.15s; }
.bk-det-btn-p:hover { opacity: 0.88; }
.bk-det-btn-g { padding: 6px 14px; border-radius: 8px; font-size: 12.5px; background: rgba(255,255,255,0.9); backdrop-filter: blur(4px); border: 1.5px solid rgba(99,102,241,0.2); color: #64748B; cursor: pointer; transition: all 0.15s; }
.bk-det-btn-g:hover { border-color: #4F46E5; color: #4F46E5; }
.bk-det-hero { display: flex; gap: 26px; margin-bottom: 22px; align-items: flex-start; }
.bk-det-cover { width: 108px; flex-shrink: 0; aspect-ratio: 2/3; border-radius: 10px; overflow: hidden; position: relative; }
.bk-det-meta { flex: 1; }
.bk-det-cat { display: inline-flex; padding: 3px 10px; border-radius: 6px; font-size: 11px; font-weight: 700; border: 1px solid; margin-bottom: 9px; }
.bk-det-title { font-size: 21px; font-weight: 800; color: #1E293B; margin: 0 0 5px; }
.bk-det-author { font-size: 12.5px; font-weight: 500; color: #4F46E5; margin-bottom: 5px; }
.bk-det-pos { font-size: 11.5px; color: #94A3B8; margin-bottom: 11px; font-style: italic; }
.bk-det-desc { font-size: 12.5px; color: #64748B; line-height: 1.7; }
.bk-det-tabs { display: flex; gap: 2px; border-bottom: 2px solid rgba(99,102,241,0.14); margin-bottom: 18px; }
.bk-dtab { padding: 8px 17px; font-size: 12.5px; background: none; border: none; color: #64748B; border-bottom: 2px solid transparent; margin-bottom: -2px; cursor: pointer; transition: all 0.15s; }
.bk-dtab:hover { color: #1E293B; }
.bk-dtab.active { font-weight: 700; }
.bk-summary { display: flex; flex-direction: column; gap: 12px; }
.bk-sum-card { background: rgba(255,255,255,0.92); backdrop-filter: blur(8px); border: 1px solid rgba(99,102,241,0.12); border-top: 3px solid; border-radius: 12px; padding: 14px 18px; box-shadow: 0 2px 10px rgba(99,102,241,0.05); }
.bk-sum-card h4 { font-size: 10.5px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.8px; margin: 0 0 7px; }
.bk-sum-card p { font-size: 12.5px; color: #475569; line-height: 1.7; margin: 0; }
.bk-ch-list { display: flex; flex-direction: column; gap: 3px; }
.bk-ch-item { display: flex; align-items: center; gap: 9px; padding: 7px 9px; border-radius: 7px; cursor: pointer; transition: background 0.12s; }
.bk-ch-item:hover { background: rgba(99,102,241,0.08); }
.bk-ch-num { font-size: 10px; font-family: monospace; font-weight: 700; flex-shrink: 0; }
.bk-ch-name { font-size: 12.5px; color: #475569; }
.bk-ch-item:hover .bk-ch-name { color: var(--acc, #4F46E5); }
.bk-ch-nav { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 14px; }
.bk-chnav-btn { padding: 4px 11px; font-size: 12px; border-radius: 6px; cursor: pointer; background: rgba(255,255,255,0.9); border: 1.5px solid rgba(99,102,241,0.2); color: #64748B; transition: all 0.15s; }
.bk-chnav-btn:hover { border-color: rgba(99,102,241,0.5); color: #4F46E5; }
.bk-ch-body { background: rgba(255,255,255,0.92); backdrop-filter: blur(8px); border: 1px solid rgba(99,102,241,0.12); border-radius: 12px; padding: 22px 26px; }
.bk-ai-tab { max-width: 700px; }
.bk-ai-input-wrap { display: flex; align-items: center; gap: 7px; margin-bottom: 14px; background: rgba(255,255,255,0.9); backdrop-filter: blur(8px); border: 1.5px solid; border-radius: 12px; padding: 0 13px; }
.bk-ai-spark { font-size: 13px; flex-shrink: 0; }
.bk-ai-inp { flex: 1; border: none; outline: none; padding: 11px 7px; background: transparent; font-size: 13px; color: #1E293B; }
.bk-ai-inp::placeholder { color: #94A3B8; }
.bk-ai-send { padding: 6px 12px; border-radius: 7px; border: none; color: #fff; font-size: 12.5px; font-weight: 600; cursor: pointer; transition: opacity 0.15s; white-space: nowrap; }
.bk-ai-send:disabled { opacity: 0.5; cursor: not-allowed; }
.bk-ai-ans { background: rgba(255,255,255,0.92); backdrop-filter: blur(8px); border: 1px solid rgba(99,102,241,0.12); border-radius: 12px; padding: 14px 18px; }
.bk-ai-hints { display: flex; flex-wrap: wrap; gap: 7px; }
.bk-hint-btn { font-size: 12px; border-radius: 7px; border: 1px solid; padding: 5px 11px; cursor: pointer; transition: opacity 0.15s; }
.bk-hint-btn:hover { opacity: 0.72; }

/* ─── Markdown ────────────────────────────────────── */
.bk-md :deep(h1), .bk-md :deep(h2), .bk-md :deep(h3) { color: #1E293B; }
.bk-md :deep(p) { color: #475569; line-height: 1.8; font-size: 13px; }
.bk-md :deep(table) { width: 100%; border-collapse: collapse; font-size: 12px; }
.bk-md :deep(th) { background: #EEF2FF; color: #4F46E5; padding: 7px 11px; border: 1px solid rgba(99,102,241,0.2); font-weight: 600; text-align: left; }
.bk-md :deep(td) { padding: 6px 11px; color: #475569; border: 1px solid rgba(99,102,241,0.1); }
.bk-md :deep(pre) { background: #1E293B; border-radius: 8px; padding: 13px; overflow-x: auto; }
.bk-md :deep(code) { font-family: monospace; font-size: 12px; background: #EEF2FF; color: #4F46E5; padding: 1px 5px; border-radius: 3px; }
.bk-md :deep(pre code) { background: none; color: #E2E8F0; }
.bk-md :deep(strong) { color: #312E81; }
.bk-md :deep(blockquote) { border-left: 3px solid #4F46E5; background: #EEF2FF; padding: 9px 13px; border-radius: 0 6px 6px 0; color: #3730A3; }

/* ─── Responsive ──────────────────────────────────── */
@media (max-width: 960px) {
  .bk-hero-graph { display: none; }
  .bk-stats { grid-template-columns: repeat(2, 1fr); }
  .bk-sidebar { display: none; }
}
@media (max-width: 640px) {
  .bk-hero, .bk-stats, .bk-filter, .bk-body, .bk-log-wrap { padding-left: 14px; padding-right: 14px; }
  .bk-hero-title { font-size: 22px; }
  .bk-grid { grid-template-columns: 1fr; }
}
</style>
