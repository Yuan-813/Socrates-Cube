<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { BOOKS, searchBooks, getBookById, type Book } from '@/data/books'
import { renderMarkdown } from '@/utils/markdown'

const router = useRouter()

// ── 视图切换 ──────────────────────────────
type ViewMode = 'list' | 'detail'
const viewMode = ref<ViewMode>('list')
const currentBook = ref<Book | null>(null)
const detailTab = ref<'summary' | 'chapters' | 'ai'>('summary')

// ── 搜索 ──────────────────────────────────
const searchQuery = ref('')
const filteredBooks = computed(() => searchBooks(searchQuery.value))

// ── 书签 ──────────────────────────────────
const bookmarked = ref<Set<string>>(new Set())
function toggleBookmark(id: string, e?: Event) {
  e?.stopPropagation()
  if (bookmarked.value.has(id)) bookmarked.value.delete(id)
  else bookmarked.value.add(id)
}

// ── AI 顾问 ──────────────────────────────
const aiQuestion = ref('')
const aiAnswer = ref('')
const aiLoading = ref(false)

async function askAI() {
  if (!aiQuestion.value.trim() || !currentBook.value || aiLoading.value) return
  aiLoading.value = true
  aiAnswer.value = ''
  try {
    const res = await fetch('/api/v1/resources/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        knowledge_point: `[关于《${currentBook.value.title}》] ${aiQuestion.value}`,
        resource_type: 'doc',
        difficulty: 3,
      }),
    })
    if (res.ok) {
      const data = await res.json()
      aiAnswer.value = data.content || data.description || '暂无回答，请检查后端连接。'
    } else {
      aiAnswer.value = '服务暂时不可用，请稍后重试。'
    }
  } catch {
    aiAnswer.value = `**关于「${aiQuestion.value}」**\n\n请先确保后端服务正常运行，或直接查阅书籍章节内容。`
  } finally {
    aiLoading.value = false
  }
}

// ── 导航 ─────────────────────────────────
function openDetail(book: Book) {
  currentBook.value = book
  viewMode.value = 'detail'
  detailTab.value = 'summary'
  aiAnswer.value = ''
  currentChapterIdx.value = 0
}
function backToList() {
  viewMode.value = 'list'
  currentBook.value = null
}
function openReader(bookId: string) {
  router.push(`/bookhouse/${bookId}/read`)
}
function openZlib(book: Book, e?: Event) {
  e?.stopPropagation()
  const q = encodeURIComponent(book.title)
  window.open(`https://z-library.sk/s/${q}`, '_blank', 'noopener,noreferrer')
}

// ── 章节 ──────────────────────────────────
const currentChapterIdx = ref(0)
const currentChapterContent = computed(() => {
  if (!currentBook.value) return ''
  const ch = currentBook.value.chapters[currentChapterIdx.value]
  return ch ? renderMarkdown(ch.content) : ''
})

// ── 热门标签 ─────────────────────────────
const hotTags = ['TCP', 'IPv6', 'OSPF', 'VLAN', '防火墙', '华为', 'HTTP', 'SDN', '网络安全', 'ARP', 'UDP', '路由交换']

onMounted(() => {
  const urlParams = new URLSearchParams(window.location.search)
  const bookId = urlParams.get('book')
  if (bookId) {
    const book = getBookById(bookId)
    if (book) openDetail(book)
  }
})
</script>

<template>
  <div class="bh-page">

    <!-- ░░░░░░░░░ 书库列表视图 ░░░░░░░░░ -->
    <template v-if="viewMode === 'list'">

      <!-- 背景拓扑 SVG 水印 -->
      <div class="topo-watermark" aria-hidden="true">
        <svg viewBox="0 0 1200 600" preserveAspectRatio="xMidYMid slice">
          <circle cx="80" cy="120" r="3" class="topo-node"/><circle cx="260" cy="60" r="3" class="topo-node"/>
          <circle cx="480" cy="180" r="3" class="topo-node"/><circle cx="700" cy="50" r="3" class="topo-node"/>
          <circle cx="920" cy="140" r="3" class="topo-node"/><circle cx="1100" cy="80" r="3" class="topo-node"/>
          <circle cx="150" cy="320" r="3" class="topo-node"/><circle cx="380" cy="400" r="3" class="topo-node"/>
          <circle cx="600" cy="310" r="3" class="topo-node"/><circle cx="830" cy="380" r="3" class="topo-node"/>
          <circle cx="1050" cy="290" r="3" class="topo-node"/><circle cx="320" cy="500" r="3" class="topo-node"/>
          <circle cx="650" cy="520" r="3" class="topo-node"/><circle cx="950" cy="480" r="3" class="topo-node"/>
          <line x1="80" y1="120" x2="260" y2="60" class="topo-line"/>
          <line x1="260" y1="60" x2="480" y2="180" class="topo-line"/>
          <line x1="480" y1="180" x2="700" y2="50" class="topo-line"/>
          <line x1="700" y1="50" x2="920" y2="140" class="topo-line"/>
          <line x1="920" y1="140" x2="1100" y2="80" class="topo-line"/>
          <line x1="80" y1="120" x2="150" y2="320" class="topo-line"/>
          <line x1="260" y1="60" x2="380" y2="400" class="topo-line"/>
          <line x1="480" y1="180" x2="600" y2="310" class="topo-line"/>
          <line x1="700" y1="50" x2="830" y2="380" class="topo-line"/>
          <line x1="920" y1="140" x2="1050" y2="290" class="topo-line"/>
          <line x1="150" y1="320" x2="380" y2="400" class="topo-line"/>
          <line x1="380" y1="400" x2="600" y2="310" class="topo-line"/>
          <line x1="600" y1="310" x2="830" y2="380" class="topo-line"/>
          <line x1="830" y1="380" x2="1050" y2="290" class="topo-line"/>
          <line x1="380" y1="400" x2="320" y2="500" class="topo-line"/>
          <line x1="600" y1="310" x2="650" y2="520" class="topo-line"/>
          <line x1="830" y1="380" x2="950" y2="480" class="topo-line"/>
        </svg>
      </div>

      <!-- OSI 层水印（右侧竖排） -->
      <div class="osi-watermark" aria-hidden="true">
        <span v-for="l in ['Physical','Data Link','Network','Transport','Session','Presentation','Application']" :key="l">{{ l }}</span>
      </div>

      <!-- ── 顶部横幅 ── -->
      <header class="bh-header">
        <div class="header-inner">
          <!-- 标题区 -->
          <div class="header-title-block">
            <div class="header-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path stroke-linecap="round" stroke-linejoin="round"
                  d="M12 6.042A8.967 8.967 0 0 0 6 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 0 1 6 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 0 1 6-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0 0 18 18a8.967 8.967 0 0 0-6 2.292m0-14.25v14.25"/>
              </svg>
            </div>
            <div>
              <h1 class="header-title">计算机网络数字书库</h1>
              <p class="header-sub">精研标准 &middot; 立足协议 &middot; 深入原理</p>
            </div>
          </div>

          <!-- 搜索框 -->
          <div class="bh-search-wrap">
            <div class="bh-search-bar">
              <svg class="search-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M21 21l-4.35-4.35M17 11A6 6 0 1 1 5 11a6 6 0 0 1 12 0z"/>
              </svg>
              <input v-model="searchQuery" type="text"
                placeholder="搜索书名、作者、协议标签（如 TCP、OSPF、防火墙…）"
                class="search-input"/>
              <button v-if="searchQuery" class="search-clear" @click="searchQuery = ''">✕</button>
            </div>
          </div>

          <!-- 热门标签（芯片样式） -->
          <div class="hot-tags-row">
            <span class="hot-label">热门：</span>
            <button v-for="tag in hotTags" :key="tag" class="hot-chip" @click="searchQuery = tag">
              {{ tag }}
            </button>
          </div>
        </div>
      </header>

      <!-- 结果统计 -->
      <div class="result-bar">
        <span v-if="searchQuery" class="result-text">
          搜索 <em class="result-keyword">「{{ searchQuery }}」</em> 找到
          <strong class="result-count">{{ filteredBooks.length }}</strong> 本书
          <button class="clear-filter" @click="searchQuery = ''">清除筛选</button>
        </span>
        <span v-else class="result-text">
          共收录 <strong class="result-count">{{ BOOKS.length }}</strong> 本经典教材与协议规范
        </span>
      </div>

      <!-- ── 书籍网格 ── -->
      <div class="books-grid" v-if="filteredBooks.length > 0">
        <article v-for="book in filteredBooks" :key="book.id" class="book-card">

          <!-- 封面 -->
          <div class="book-cover" :style="{ background: `linear-gradient(150deg, ${book.coverFrom}, ${book.coverTo})` }"
            @click="openDetail(book)">
            <!-- 书脊阴影线 -->
            <div class="spine-shadow"/>
            <!-- 类别徽章 -->
            <span class="cover-badge" :style="{ color: book.coverText }">{{ book.coverTag }}</span>
            <!-- 书名（竖排） -->
            <div class="cover-title-v" :style="{ color: book.coverText }">{{ book.shortTitle }}</div>
            <!-- 作者 -->
            <div class="cover-author-v" :style="{ color: book.coverText, opacity: 0.6 }">{{ book.author }}</div>
            <!-- 悬停遮罩 -->
            <div class="cover-hover-mask">
              <span class="cover-hover-text">查看摘要</span>
            </div>
          </div>

          <!-- 书籍信息 -->
          <div class="book-info">
            <h3 class="book-title" @click="openDetail(book)">{{ book.title }}</h3>
            <p class="book-author">{{ book.author }}</p>

            <!-- 芯片标签 -->
            <div class="tag-chips">
              <span v-for="tag in book.tags.slice(0, 3)" :key="tag" class="tag-chip">{{ tag }}</span>
            </div>

            <!-- 操作按钮 -->
            <div class="card-actions">
              <button class="btn-summary" @click="openDetail(book)">
                <svg viewBox="0 0 16 16" fill="currentColor" class="btn-icon">
                  <path d="M3 2a1 1 0 011-1h8a1 1 0 011 1v12a1 1 0 01-1 1H4a1 1 0 01-1-1V2zm2 2v1h6V4H5zm0 3v1h6V7H5zm0 3v1h4v-1H5z"/>
                </svg>
                内容摘要
              </button>
              <button class="btn-zlib" @click="openZlib(book, $event)" title="在 Z-Library 搜索此书">
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" class="btn-icon">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M10 3h3v3m0-3L7 9M5 4H3a1 1 0 00-1 1v7a1 1 0 001 1h7a1 1 0 001-1v-2"/>
                </svg>
                获取原版 ↗
              </button>
            </div>
          </div>

          <!-- 收藏按钮 -->
          <button class="bookmark-btn" :class="{ active: bookmarked.has(book.id) }"
            @click="toggleBookmark(book.id, $event)" :title="bookmarked.has(book.id) ? '取消收藏' : '加入书签'">
            <svg viewBox="0 0 24 24" :fill="bookmarked.has(book.id) ? '#f59e0b' : 'none'"
              :stroke="bookmarked.has(book.id) ? '#f59e0b' : '#64748b'" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round"
                d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"/>
            </svg>
          </button>
        </article>
      </div>

      <!-- 空状态 -->
      <div v-else class="empty-state">
        <div class="empty-icon">⌀</div>
        <p>未找到「{{ searchQuery }}」相关书籍</p>
        <button class="empty-clear" @click="searchQuery = ''">清除搜索条件</button>
      </div>

    </template>

    <!-- ░░░░░░░░░ 书籍详情视图 ░░░░░░░░░ -->
    <template v-else-if="currentBook">
      <div class="detail-page">

        <!-- 顶部工具栏 -->
        <div class="detail-toolbar">
          <button class="back-btn" @click="backToList">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M10 19l-7-7m0 0l7-7m-7 7h18"/>
            </svg>
            返回书库
          </button>
          <div class="breadcrumb">
            <span class="bc-home" @click="backToList">书库</span>
            <span class="bc-sep">/</span>
            <span class="bc-cur">{{ currentBook.shortTitle }}</span>
          </div>
          <div class="toolbar-actions">
            <button class="btn-read" @click="openReader(currentBook.id)">
              <svg viewBox="0 0 20 20" fill="currentColor" class="w-4 h-4">
                <path d="M9 4.804A7.968 7.968 0 005.5 4c-1.255 0-2.443.29-3.5.804v10A7.969 7.969 0 015.5 14c1.669 0 3.218.51 4.5 1.385A7.962 7.962 0 0114.5 14c1.255 0 2.443.29 3.5.804v-10A7.968 7.968 0 0014.5 4c-1.255 0-2.443.29-3.5.804V12a1 1 0 11-2 0V4.804z"/>
              </svg>
              进入阅读器
            </button>
            <button class="btn-zlib-detail" @click="openZlib(currentBook)">获取原版 ↗</button>
          </div>
        </div>

        <!-- 书籍头部信息 -->
        <div class="detail-hero">
          <!-- 封面 -->
          <div class="detail-cover"
            :style="{ background: `linear-gradient(150deg, ${currentBook.coverFrom}, ${currentBook.coverTo})` }">
            <div class="spine-shadow"/>
            <span class="cover-badge" :style="{ color: currentBook.coverText }">{{ currentBook.coverTag }}</span>
            <div class="cover-title-v" :style="{ color: currentBook.coverText }">{{ currentBook.shortTitle }}</div>
            <div class="cover-author-v" :style="{ color: currentBook.coverText, opacity: 0.6 }">{{ currentBook.author }}</div>
          </div>

          <!-- 书籍元数据 -->
          <div class="detail-meta">
            <h1 class="detail-title">{{ currentBook.title }}</h1>
            <p class="detail-author">{{ currentBook.author }}</p>
            <p class="detail-position">{{ currentBook.academicPosition }}</p>
            <div class="detail-tags">
              <span v-for="tag in currentBook.tags" :key="tag" class="tag-chip">{{ tag }}</span>
            </div>
            <p class="detail-desc">{{ currentBook.description }}</p>
          </div>
        </div>

        <!-- 选项卡 -->
        <div class="detail-tabs">
          <button v-for="tab in [
            { id: 'summary', label: '内容摘要' },
            { id: 'chapters', label: '章节内容' },
            { id: 'ai', label: 'AI 顾问' },
          ]" :key="tab.id" class="detail-tab" :class="{ active: detailTab === tab.id }"
            @click="detailTab = (tab.id as any)">
            {{ tab.label }}
          </button>
        </div>

        <!-- 选项卡内容 -->
        <div class="detail-content">

          <!-- 内容摘要 -->
          <div v-if="detailTab === 'summary'" class="tab-summary">
            <div class="summary-card">
              <h3 class="summary-label">核心内容</h3>
              <p class="summary-text">{{ currentBook.coreContent }}</p>
            </div>
            <div class="summary-card">
              <h3 class="summary-label">学术定位</h3>
              <p class="summary-text">{{ currentBook.academicPosition }}</p>
            </div>
            <div class="summary-card">
              <h3 class="summary-label">章节目录</h3>
              <ul class="chapter-list">
                <li v-for="(ch, idx) in currentBook.chapters" :key="ch.id"
                  class="chapter-item" :class="{ active: currentChapterIdx === idx }"
                  @click="detailTab = 'chapters'; currentChapterIdx = idx">
                  <span class="chapter-num">{{ String(idx + 1).padStart(2, '0') }}</span>
                  <span class="chapter-name">{{ ch.title }}</span>
                </li>
              </ul>
            </div>
          </div>

          <!-- 章节内容 -->
          <div v-else-if="detailTab === 'chapters'" class="tab-chapters">
            <div class="chapter-nav">
              <button v-for="(ch, idx) in currentBook.chapters" :key="ch.id"
                class="chapter-nav-btn" :class="{ active: currentChapterIdx === idx }"
                @click="currentChapterIdx = idx">
                {{ ch.title }}
              </button>
            </div>
            <div class="chapter-body markdown-body" v-html="currentChapterContent"/>
          </div>

          <!-- AI 顾问 -->
          <div v-else-if="detailTab === 'ai'" class="tab-ai">
            <div class="ai-header">
              <span class="ai-badge">AI</span>
              <span class="ai-label">关于《{{ currentBook.shortTitle }}》的智能问答</span>
            </div>
            <div class="ai-input-row">
              <input v-model="aiQuestion" type="text"
                class="ai-input" placeholder="输入你的问题，例如：什么是三次握手？"
                @keyup.enter="askAI"/>
              <button class="ai-send-btn" :disabled="aiLoading" @click="askAI">
                {{ aiLoading ? '思考中…' : '提问' }}
              </button>
            </div>
            <div v-if="aiAnswer" class="ai-answer markdown-body" v-html="renderMarkdown(aiAnswer)"/>
            <div v-if="!aiAnswer && !aiLoading" class="ai-hints">
              <span class="hint-label">推荐问法：</span>
              <button v-for="q in ['三次握手的原因？', 'IP路由转发流程？', '防火墙安全区域？', 'OSPF工作原理？']"
                :key="q" class="hint-btn" @click="aiQuestion = q">{{ q }}</button>
            </div>
          </div>

        </div>
      </div>
    </template>

  </div>
</template>

<style scoped>
/* ═══════════════════════════════════════
   基础页面
═══════════════════════════════════════ */
.bh-page {
  min-height: 100vh;
  background-color: #08152b;
  background-image:
    radial-gradient(circle, rgba(74,144,217,0.13) 1px, transparent 1px);
  background-size: 32px 32px;
  color: #cdd9ea;
  position: relative;
  overflow-x: hidden;
}

/* 拓扑 SVG 水印 */
.topo-watermark {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  opacity: 0.5;
}
.topo-watermark svg { width: 100%; height: 100%; }
.topo-node { fill: #4a90d9; opacity: 0.15; }
.topo-line { stroke: #4a90d9; stroke-width: 1; opacity: 0.07; }

/* OSI 水印 */
.osi-watermark {
  position: fixed;
  right: 16px;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  flex-direction: column;
  gap: 6px;
  pointer-events: none;
  z-index: 0;
  opacity: 0.04;
}
.osi-watermark span {
  font-size: 9px;
  letter-spacing: 3px;
  text-transform: uppercase;
  color: #7ec8f7;
  white-space: nowrap;
}

/* ═══════════════════════════════════════
   顶部横幅
═══════════════════════════════════════ */
.bh-header {
  position: relative;
  z-index: 10;
  background: linear-gradient(160deg, #0d1e3a 0%, #1a3460 50%, #0d1e3a 100%);
  border-bottom: 1px solid rgba(74,144,217,0.2);
  padding: 32px 24px 28px;
}
.header-inner { max-width: 1200px; margin: 0 auto; }
.header-title-block {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 20px;
}
.header-icon {
  width: 44px; height: 44px;
  background: rgba(74,144,217,0.15);
  border: 1px solid rgba(74,144,217,0.3);
  border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  color: #60a5fa;
  flex-shrink: 0;
}
.header-icon svg { width: 22px; height: 22px; }
.header-title { font-size: 24px; font-weight: 700; color: #e2f0ff; margin: 0; letter-spacing: 0.02em; }
.header-sub { font-size: 13px; color: #7095b8; margin: 2px 0 0; letter-spacing: 0.1em; }

/* 搜索框 */
.bh-search-wrap { margin-bottom: 14px; }
.bh-search-bar {
  display: flex; align-items: center;
  background: rgba(15,34,64,0.9);
  border: 1px solid rgba(74,144,217,0.35);
  border-radius: 8px;
  padding: 0 12px;
  transition: border-color 0.2s;
}
.bh-search-bar:focus-within { border-color: rgba(74,144,217,0.7); box-shadow: 0 0 0 3px rgba(74,144,217,0.1); }
.search-icon { width: 16px; height: 16px; color: #4a7fa8; flex-shrink: 0; }
.search-input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  padding: 12px 10px;
  color: #cdd9ea;
  font-size: 14px;
}
.search-input::placeholder { color: #3a6080; }
.search-clear { background: none; border: none; color: #4a7fa8; cursor: pointer; font-size: 12px; padding: 4px; }
.search-clear:hover { color: #94c9f0; }

/* 热门芯片标签 */
.hot-tags-row { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; }
.hot-label { font-size: 12px; color: #4a7fa8; }
.hot-chip {
  padding: 3px 10px;
  font-size: 11px;
  font-family: 'Courier New', monospace;
  background: rgba(30,58,95,0.8);
  border: 1px solid rgba(96,165,250,0.3);
  border-radius: 4px;
  color: #7ec8f7;
  cursor: pointer;
  transition: all 0.15s;
  letter-spacing: 0.02em;
}
.hot-chip:hover {
  background: rgba(59,130,246,0.2);
  border-color: rgba(96,165,250,0.6);
  color: #bae6fd;
}

/* ═══════════════════════════════════════
   结果条
═══════════════════════════════════════ */
.result-bar {
  position: relative; z-index: 10;
  max-width: 1200px; margin: 0 auto;
  padding: 14px 24px;
  font-size: 13px; color: #4a7fa8;
}
.result-keyword { font-style: normal; color: #60a5fa; }
.result-count { color: #60a5fa; font-weight: 700; }
.clear-filter {
  margin-left: 8px; background: none;
  border: 1px solid rgba(74,144,217,0.3); border-radius: 4px;
  color: #4a90d9; cursor: pointer; font-size: 11px; padding: 1px 8px;
}
.clear-filter:hover { border-color: #60a5fa; color: #93c5fd; }

/* ═══════════════════════════════════════
   书籍网格
═══════════════════════════════════════ */
.books-grid {
  position: relative; z-index: 10;
  max-width: 1200px; margin: 0 auto;
  padding: 0 20px 40px;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(185px, 1fr));
  gap: 24px;
}

/* 书籍卡片 */
.book-card {
  position: relative;
  background: rgba(13,31,60,0.85);
  border: 1px solid rgba(30,58,95,0.8);
  border-radius: 10px;
  overflow: hidden;
  transition: border-color 0.2s, transform 0.2s, box-shadow 0.2s;
}
.book-card:hover {
  border-color: rgba(59,130,246,0.5);
  transform: translateY(-3px);
  box-shadow: 0 12px 32px rgba(0,0,0,0.4), 0 0 20px rgba(59,130,246,0.08);
}

/* 封面 */
.book-cover {
  width: 100%;
  aspect-ratio: 2 / 3;
  position: relative;
  cursor: pointer;
  overflow: hidden;
  border-radius: 8px 8px 0 0;
}
.spine-shadow {
  position: absolute; left: 0; top: 0; bottom: 0; width: 8px;
  background: rgba(0,0,0,0.3);
  border-radius: 8px 0 0 0;
}
.cover-badge {
  position: absolute; top: 8px; right: 8px;
  font-size: 9px; font-weight: 700; letter-spacing: 1.5px;
  text-transform: uppercase;
  background: rgba(0,0,0,0.3); border-radius: 3px;
  padding: 2px 6px;
}
.cover-title-v {
  position: absolute; bottom: 36px; left: 18px; right: 10px;
  font-size: 13px; font-weight: 700; line-height: 1.5;
  writing-mode: vertical-rl; text-orientation: mixed;
  max-height: 140px; overflow: hidden;
}
.cover-author-v {
  position: absolute; bottom: 10px; left: 18px;
  font-size: 10px; writing-mode: vertical-rl; text-orientation: mixed;
}
.cover-hover-mask {
  position: absolute; inset: 0;
  background: rgba(15,60,120,0.6);
  display: flex; align-items: center; justify-content: center;
  opacity: 0; transition: opacity 0.2s;
}
.book-cover:hover .cover-hover-mask { opacity: 1; }
.cover-hover-text { color: #bae6fd; font-size: 13px; font-weight: 600; }

/* 书籍信息区 */
.book-info { padding: 12px 12px 14px; }
.book-title {
  font-size: 13px; font-weight: 600; color: #cce4f7;
  line-height: 1.4; margin-bottom: 4px; cursor: pointer;
  display: -webkit-box; -webkit-line-clamp: 2;
  -webkit-box-orient: vertical; overflow: hidden;
}
.book-title:hover { color: #93c5fd; }
.book-author { font-size: 11px; color: #4a7fa8; margin-bottom: 8px; }

/* 芯片标签 */
.tag-chips { display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 10px; }
.tag-chip {
  display: inline-block; padding: 2px 7px;
  font-size: 10px; font-family: 'Courier New', monospace;
  background: rgba(15,40,80,0.9);
  border: 1px solid rgba(59,130,246,0.3);
  border-radius: 3px; color: #60a5fa;
  letter-spacing: 0.02em;
}

/* 操作按钮 */
.card-actions { display: flex; gap: 6px; }
.btn-summary, .btn-zlib {
  flex: 1; display: flex; align-items: center; justify-content: center; gap: 4px;
  padding: 6px 4px; font-size: 11px; border-radius: 5px; cursor: pointer;
  transition: all 0.15s; white-space: nowrap;
}
.btn-icon { width: 11px; height: 11px; flex-shrink: 0; }
.btn-summary {
  background: rgba(29,78,216,0.7); border: 1px solid rgba(59,130,246,0.4); color: #bae6fd;
}
.btn-summary:hover { background: rgba(37,99,235,0.9); border-color: #60a5fa; }
.btn-zlib {
  background: transparent; border: 1px solid rgba(30,58,95,0.8); color: #64748b;
}
.btn-zlib:hover { border-color: rgba(59,130,246,0.4); color: #60a5fa; }

/* 书签按钮 */
.bookmark-btn {
  position: absolute; top: 6px; left: 6px;
  background: rgba(8,21,43,0.7); border: none;
  border-radius: 50%; width: 26px; height: 26px;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; transition: transform 0.15s;
}
.bookmark-btn svg { width: 14px; height: 14px; }
.bookmark-btn:hover { transform: scale(1.15); }
.bookmark-btn.active { background: rgba(30,20,5,0.8); }

/* 空状态 */
.empty-state { text-align: center; padding: 80px 24px; position: relative; z-index: 10; }
.empty-icon { font-size: 48px; opacity: 0.3; margin-bottom: 12px; }
.empty-state p { color: #4a7fa8; font-size: 14px; margin-bottom: 16px; }
.empty-clear { background: rgba(29,78,216,0.3); border: 1px solid rgba(59,130,246,0.3);
  border-radius: 6px; color: #60a5fa; padding: 8px 18px; cursor: pointer; font-size: 13px; }

/* ═══════════════════════════════════════
   详情视图
═══════════════════════════════════════ */
.detail-page { max-width: 1100px; margin: 0 auto; padding: 20px 24px 60px; position: relative; z-index: 10; }

.detail-toolbar {
  display: flex; align-items: center; gap: 12px; margin-bottom: 24px;
  padding-bottom: 16px; border-bottom: 1px solid rgba(30,58,95,0.5);
}
.back-btn {
  display: flex; align-items: center; gap: 6px;
  background: transparent; border: 1px solid rgba(30,58,95,0.8);
  border-radius: 6px; color: #94a3b8; padding: 6px 12px; cursor: pointer;
  font-size: 13px; transition: all 0.15s;
}
.back-btn svg { width: 14px; height: 14px; }
.back-btn:hover { border-color: #3b82f6; color: #60a5fa; }
.breadcrumb { flex: 1; font-size: 12px; color: #4a7fa8; }
.bc-home { cursor: pointer; } .bc-home:hover { color: #60a5fa; }
.bc-sep { margin: 0 6px; } .bc-cur { color: #94a3b8; }
.toolbar-actions { display: flex; gap: 8px; }
.btn-read {
  display: flex; align-items: center; gap: 5px;
  background: rgba(29,78,216,0.7); border: 1px solid rgba(59,130,246,0.4);
  border-radius: 6px; color: #bae6fd; padding: 6px 14px; cursor: pointer;
  font-size: 12px; transition: all 0.15s;
}
.btn-read:hover { background: rgba(37,99,235,0.9); }
.btn-zlib-detail {
  background: transparent; border: 1px solid rgba(30,58,95,0.8);
  border-radius: 6px; color: #64748b; padding: 6px 14px; cursor: pointer;
  font-size: 12px; transition: all 0.15s;
}
.btn-zlib-detail:hover { border-color: rgba(59,130,246,0.4); color: #60a5fa; }

.detail-hero { display: flex; gap: 32px; margin-bottom: 28px; align-items: flex-start; }
.detail-cover {
  width: 120px; flex-shrink: 0; aspect-ratio: 2/3;
  border-radius: 6px 2px 2px 6px; position: relative; overflow: hidden;
  box-shadow: -4px 4px 16px rgba(0,0,0,0.5);
}
.detail-meta { flex: 1; }
.detail-title { font-size: 22px; font-weight: 700; color: #e2f0ff; margin: 0 0 6px; }
.detail-author { font-size: 13px; color: #4a90d9; margin-bottom: 6px; }
.detail-position { font-size: 12px; color: #4a7fa8; margin-bottom: 12px; font-style: italic; }
.detail-tags { display: flex; flex-wrap: wrap; gap: 5px; margin-bottom: 12px; }
.detail-desc { font-size: 13px; color: #7095b8; line-height: 1.7; }

.detail-tabs { display: flex; gap: 2px; border-bottom: 1px solid rgba(30,58,95,0.6); margin-bottom: 20px; }
.detail-tab {
  padding: 8px 18px; font-size: 13px; cursor: pointer;
  background: none; border: none; color: #4a7fa8;
  border-bottom: 2px solid transparent; margin-bottom: -1px; transition: all 0.15s;
}
.detail-tab:hover { color: #94a3b8; }
.detail-tab.active { color: #60a5fa; border-bottom-color: #3b82f6; }

.detail-content { min-height: 300px; }

/* 摘要 Tab */
.summary-card { background: rgba(13,31,60,0.8); border: 1px solid rgba(30,58,95,0.6);
  border-radius: 8px; padding: 14px 18px; margin-bottom: 12px; }
.summary-label { font-size: 11px; letter-spacing: 1px; text-transform: uppercase;
  color: #4a90d9; margin: 0 0 8px; }
.summary-text { font-size: 13px; color: #94a3b8; line-height: 1.7; margin: 0; }
.chapter-list { list-style: none; margin: 0; padding: 0; }
.chapter-item {
  display: flex; align-items: center; gap: 10px; padding: 8px 10px;
  border-radius: 6px; cursor: pointer; transition: background 0.15s;
}
.chapter-item:hover, .chapter-item.active { background: rgba(29,78,216,0.15); }
.chapter-num { font-size: 11px; color: #3b82f6; font-family: monospace; flex-shrink: 0; }
.chapter-name { font-size: 13px; color: #94a3b8; }
.chapter-item:hover .chapter-name, .chapter-item.active .chapter-name { color: #93c5fd; }

/* 章节 Tab */
.chapter-nav { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 20px; }
.chapter-nav-btn {
  padding: 5px 12px; font-size: 12px; border-radius: 5px; cursor: pointer;
  background: rgba(13,31,60,0.8); border: 1px solid rgba(30,58,95,0.7); color: #64748b;
  transition: all 0.15s;
}
.chapter-nav-btn:hover { border-color: rgba(59,130,246,0.4); color: #94a3b8; }
.chapter-nav-btn.active { background: rgba(29,78,216,0.3); border-color: #3b82f6; color: #93c5fd; }
.chapter-body { background: rgba(13,31,60,0.6); border: 1px solid rgba(30,58,95,0.5);
  border-radius: 10px; padding: 24px 28px; }

/* AI Tab */
.tab-ai { max-width: 700px; }
.ai-header { display: flex; align-items: center; gap: 8px; margin-bottom: 16px; }
.ai-badge {
  font-size: 10px; font-weight: 800; letter-spacing: 1px;
  background: rgba(29,78,216,0.4); border: 1px solid #3b82f6;
  border-radius: 4px; padding: 2px 7px; color: #93c5fd;
}
.ai-label { font-size: 13px; color: #64748b; }
.ai-input-row { display: flex; gap: 8px; margin-bottom: 16px; }
.ai-input {
  flex: 1; background: rgba(13,31,60,0.8); border: 1px solid rgba(30,58,95,0.8);
  border-radius: 6px; padding: 9px 14px; color: #cdd9ea; font-size: 13px; outline: none;
}
.ai-input:focus { border-color: rgba(59,130,246,0.5); }
.ai-send-btn {
  background: rgba(29,78,216,0.7); border: 1px solid rgba(59,130,246,0.4);
  border-radius: 6px; color: #bae6fd; padding: 9px 18px;
  cursor: pointer; font-size: 13px; white-space: nowrap; transition: all 0.15s;
}
.ai-send-btn:hover:not(:disabled) { background: rgba(37,99,235,0.9); }
.ai-send-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.ai-answer { background: rgba(13,31,60,0.6); border: 1px solid rgba(30,58,95,0.5);
  border-radius: 8px; padding: 16px 20px; }
.ai-hints { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; }
.hint-label { font-size: 12px; color: #4a7fa8; }
.hint-btn {
  font-size: 12px; background: rgba(13,31,60,0.8); border: 1px solid rgba(30,58,95,0.6);
  border-radius: 4px; color: #64748b; padding: 3px 10px; cursor: pointer; transition: all 0.15s;
}
.hint-btn:hover { border-color: rgba(59,130,246,0.4); color: #93c5fd; }

/* Markdown 排版 */
.markdown-body :deep(h1), .markdown-body :deep(h2), .markdown-body :deep(h3) { color: #93c5fd; margin-top: 1.4em; }
.markdown-body :deep(p) { color: #94a3b8; line-height: 1.8; font-size: 13px; }
.markdown-body :deep(table) { width: 100%; border-collapse: collapse; font-size: 12px; }
.markdown-body :deep(th) { background: rgba(29,78,216,0.2); color: #60a5fa; padding: 7px 12px; text-align: left; border: 1px solid rgba(30,58,95,0.6); }
.markdown-body :deep(td) { padding: 6px 12px; color: #94a3b8; border: 1px solid rgba(30,58,95,0.4); }
.markdown-body :deep(tr:nth-child(even) td) { background: rgba(13,31,60,0.4); }
.markdown-body :deep(pre) { background: rgba(0,0,0,0.4); border: 1px solid rgba(30,58,95,0.5); border-radius: 6px; padding: 12px 16px; overflow-x: auto; }
.markdown-body :deep(code) { font-family: 'Courier New', monospace; font-size: 12px; color: #a5f3fc; background: rgba(0,0,0,0.3); padding: 1px 5px; border-radius: 3px; }
.markdown-body :deep(pre code) { background: none; padding: 0; }
.markdown-body :deep(strong) { color: #60a5fa; }
.markdown-body :deep(em) { color: #c084fc; }
.markdown-body :deep(blockquote) { border-left: 3px solid #3b82f6; padding-left: 12px; color: #64748b; margin: 12px 0; }
.markdown-body :deep(ul), .markdown-body :deep(ol) { padding-left: 1.4em; color: #94a3b8; font-size: 13px; }
.markdown-body :deep(li) { margin-bottom: 4px; line-height: 1.7; }
</style>
