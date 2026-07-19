<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getBookById, type Book, type BookChapter } from '@/data/books'
import { renderMarkdown } from '@/utils/markdown'
import { startChatStream } from '@/api/chat'
import type { SSEPayload } from '@/types'

const route = useRoute()
const router = useRouter()

// ── 书籍 ──────────────────────────────────
const book = ref<Book | null>(null)
const currentChapterIdx = ref(0)
const currentChapter = computed<BookChapter | null>(
  () => book.value?.chapters[currentChapterIdx.value] ?? null
)
const totalChapters = computed(() => book.value?.chapters.length ?? 1)
const renderedContent = computed(() =>
  currentChapter.value ? renderMarkdown(currentChapter.value.content) : ''
)

// ── 面板状态 ───────────────────────────────
const leftCollapsed = ref(false)
const aiOpen = ref(true)
const leftTab = ref<'toc' | 'thumbs'>('toc')

// ── 缩放 ───────────────────────────────────
const zoom = ref(100)

// ── 文字选中 → AI ──────────────────────────
const selectedText = ref('')
const selPopup = ref({ show: false, x: 0, y: 0 })

function onTextSelect() {
  const sel = window.getSelection()
  const txt = sel?.toString().trim() ?? ''
  if (txt.length > 3) {
    selectedText.value = txt
    const range = sel!.getRangeAt(0)
    const rect = range.getBoundingClientRect()
    selPopup.value = {
      show: true,
      x: Math.min(rect.left + rect.width / 2, window.innerWidth - 120),
      y: rect.top - 44,
    }
  } else {
    selPopup.value.show = false
  }
}

function hideSelPopup() { selPopup.value.show = false }

function askAboutSelection() {
  aiInput.value = `请解释这段内容：「${selectedText.value}」`
  selPopup.value.show = false
  if (!aiOpen.value) aiOpen.value = true
  sendAIMessage()
}

// ── AI 助手（SSE） ────────────────────────
interface AiMsg { role: 'user' | 'ai'; text: string; streaming?: boolean }

const aiMessages = ref<AiMsg[]>([
  {
    role: 'ai',
    text: '欢迎使用 AI 助手！我可以帮你分析文档内容、解答问题、总结要点等。\n\n**使用技巧**：在正文中选中一段文字，点击「向 AI 提问」按钮，我会结合上下文为你解释。'
  }
])
const aiInput = ref('')
const aiLoading = ref(false)
const aiScrollRef = ref<HTMLElement | null>(null)
let sseCtrl: AbortController | null = null
const sessionId = `book-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`

const quickQuestions = computed(() => {
  const title = currentChapter.value?.title || book.value?.shortTitle || ''
  return [
    `${title}的核心要点是什么？`,
    '有哪些常见误解？',
    '能举个实际例子吗？',
    '用简单的话概括一下',
  ]
})

async function sendAIMessage() {
  if (!aiInput.value.trim() || aiLoading.value || !book.value) return

  const q = aiInput.value.trim()
  aiInput.value = ''

  // 构建包含书籍上下文的 prompt
  const chapterSnippet = currentChapter.value?.content?.slice(0, 600) ?? ''
  const context = [
    `[阅读上下文]`,
    `书名：《${book.value.title}》  作者：${book.value.author}`,
    `当前章节：${currentChapter.value?.title ?? '全文'}`,
    `章节内容节选：\n${chapterSnippet}`,
    ``,
    `[用户问题]`,
    q,
  ].join('\n')

  aiMessages.value.push({ role: 'user', text: q })
  aiMessages.value.push({ role: 'ai', text: '', streaming: true })
  const idx = aiMessages.value.length - 1
  aiLoading.value = true

  sseCtrl?.abort()
  sseCtrl = startChatStream(
    { message: context, user_id: 'book-reader', session_id: sessionId },
    (payload: SSEPayload) => {
      const d = payload.data as Record<string, string>
      const chunk = d?.token ?? d?.content ?? d?.chunk ?? ''
      if (chunk) {
        aiMessages.value[idx].text += chunk
        scrollAI()
      }
    },
    () => {
      aiLoading.value = false
      if (aiMessages.value[idx]) aiMessages.value[idx].streaming = false
      scrollAI()
    },
    (err: Error) => {
      aiLoading.value = false
      if (aiMessages.value[idx]) {
        aiMessages.value[idx].text = aiMessages.value[idx].text || `抱歉，AI 服务连接失败（${err.message}）。请确认后端已启动，或在 Mock 模式下运行（npm run dev:mock）。`
        aiMessages.value[idx].streaming = false
      }
    }
  )
}

function useQuick(q: string) {
  aiInput.value = q
  sendAIMessage()
}

function scrollAI() {
  nextTick(() => {
    if (aiScrollRef.value) aiScrollRef.value.scrollTop = aiScrollRef.value.scrollHeight
  })
}

// ── 章节导航 ──────────────────────────────
function goChapter(idx: number) {
  if (idx < 0 || idx >= totalChapters.value) return
  currentChapterIdx.value = idx
  const el = document.querySelector('.doc-scroll-area')
  el?.scrollTo({ top: 0, behavior: 'smooth' })
}

function goBack() { router.push('/bookhouse') }

onMounted(() => {
  const id = route.params.id as string
  const b = getBookById(id)
  if (b) { book.value = b } else { router.push('/bookhouse') }
  document.addEventListener('mouseup', onTextSelect)
})

onUnmounted(() => {
  document.removeEventListener('mouseup', onTextSelect)
  sseCtrl?.abort()
})
</script>

<template>
  <div class="reader-wrap" v-if="book" @click.self="hideSelPopup">

    <!-- ═══════ 顶部工具栏 ═══════ -->
    <header class="reader-hdr">
      <div class="rh-left">
        <button class="rh-icon-btn" @click="goBack" title="返回书库">
          <svg viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd"
            d="M9.707 16.707a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414l6-6a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l4.293 4.293a1 1 0 010 1.414z"/></svg>
        </button>
        <span class="rh-sep"/>
        <span class="rh-breadcrumb" @click="goBack">教材书库</span>
        <svg class="rh-bc-arrow" viewBox="0 0 16 16" fill="currentColor"><path d="M6 3l5 5-5 5"/></svg>
        <span class="rh-breadcrumb active">{{ book.shortTitle }}</span>
      </div>

      <div class="rh-center">
        <span class="rh-title">{{ book.title }}</span>
      </div>

      <div class="rh-right">
        <!-- 翻页 -->
        <button class="rh-icon-btn" @click="goChapter(currentChapterIdx - 1)" :disabled="currentChapterIdx === 0">
          <svg viewBox="0 0 20 20" fill="currentColor"><path d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z"/></svg>
        </button>
        <span class="rh-pages">{{ currentChapterIdx + 1 }} / {{ totalChapters }}</span>
        <button class="rh-icon-btn" @click="goChapter(currentChapterIdx + 1)" :disabled="currentChapterIdx >= totalChapters - 1">
          <svg viewBox="0 0 20 20" fill="currentColor"><path d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"/></svg>
        </button>
        <span class="rh-sep"/>
        <!-- 缩放 -->
        <button class="rh-icon-btn" @click="zoom = Math.max(75, zoom - 10)" title="缩小">－</button>
        <span class="rh-zoom-val">{{ zoom }}%</span>
        <button class="rh-icon-btn" @click="zoom = Math.min(200, zoom + 10)" title="放大">＋</button>
        <span class="rh-sep"/>
        <!-- AI 开关 -->
        <button class="rh-ai-btn" :class="{ active: aiOpen }" @click="aiOpen = !aiOpen">
          <span class="ai-dot"/>
          AI·在线
        </button>
      </div>
    </header>

    <!-- ═══════ 主体区域 ═══════ -->
    <div class="reader-body">

      <!-- ── 左侧面板 ── -->
      <aside class="reader-left" :class="{ collapsed: leftCollapsed }">
        <!-- 折叠按钮 -->
        <button class="left-toggle" @click="leftCollapsed = !leftCollapsed">
          <svg viewBox="0 0 20 20" fill="currentColor">
            <path v-if="!leftCollapsed" d="M3 5h14M3 10h14M3 15h14"/>
            <path v-else d="M13 5l-5 5 5 5"/>
          </svg>
        </button>

        <template v-if="!leftCollapsed">
          <!-- Tab 切换 -->
          <div class="left-tabs">
            <button class="ltab" :class="{ active: leftTab === 'toc' }" @click="leftTab = 'toc'">
              <svg viewBox="0 0 20 20" fill="currentColor" class="ltab-icon">
                <path d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z"/>
              </svg>
              目录
            </button>
            <button class="ltab" :class="{ active: leftTab === 'thumbs' }" @click="leftTab = 'thumbs'">
              <svg viewBox="0 0 20 20" fill="currentColor" class="ltab-icon">
                <path d="M5 3a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2V5a2 2 0 00-2-2H5zm0 8a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2v-2a2 2 0 00-2-2H5zm8-8a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2V5a2 2 0 00-2-2h-2zm0 8a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2v-2a2 2 0 00-2-2h-2z"/>
              </svg>
              缩略图
            </button>
          </div>

          <!-- 目录视图 -->
          <div v-if="leftTab === 'toc'" class="toc-list">
            <div class="toc-book-title">{{ book.shortTitle }}</div>
            <button v-for="(ch, idx) in book.chapters" :key="ch.id"
              class="toc-item" :class="{ active: currentChapterIdx === idx }"
              @click="goChapter(idx)">
              <span class="toc-num">{{ String(idx + 1).padStart(2, '0') }}</span>
              <span class="toc-label">{{ ch.title }}</span>
            </button>
          </div>

          <!-- 缩略图视图 -->
          <div v-else class="thumb-list">
            <div v-for="(ch, idx) in book.chapters" :key="ch.id"
              class="thumb-item" :class="{ active: currentChapterIdx === idx }"
              @click="goChapter(idx)">
              <!-- 迷你页面预览 -->
              <div class="thumb-page" :style="{ background: `linear-gradient(135deg, ${book.coverFrom}22, ${book.coverTo}11)` }">
                <div class="thumb-pg-title">{{ ch.title.slice(0, 18) }}</div>
                <div class="thumb-pg-text">{{ ch.content.slice(0, 60) }}…</div>
              </div>
              <span class="thumb-pg-num">{{ idx + 1 }}</span>
            </div>
          </div>
        </template>
      </aside>

      <!-- ── 文档内容区 ── -->
      <main class="doc-area doc-scroll-area" @click="hideSelPopup">
        <!-- 文档页面 -->
        <div class="doc-page-wrap">
          <div class="doc-page" :style="{ fontSize: zoom + '%' }">
            <!-- 页眉 -->
            <div class="doc-header-bar">
              <span class="doc-hd-book">{{ book.title }}</span>
              <span class="doc-hd-chapter">{{ currentChapter?.title }}</span>
            </div>
            <!-- 正文 -->
            <article class="doc-body markdown-doc" v-html="renderedContent"/>
            <!-- 页脚 -->
            <div class="doc-footer-bar">
              <span>第 {{ currentChapterIdx + 1 }} 章，共 {{ totalChapters }} 章</span>
              <span>{{ book.author }}</span>
            </div>
          </div>
        </div>

        <!-- 章节切换导航条 -->
        <div class="chapter-nav-bar">
          <button class="cnb-btn" :disabled="currentChapterIdx === 0"
            @click="goChapter(currentChapterIdx - 1)">
            <svg viewBox="0 0 20 20" fill="currentColor"><path d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z"/></svg>
            上一章
          </button>
          <div class="cnb-chapters">
            <button v-for="(ch, idx) in book.chapters" :key="ch.id"
              class="cnb-dot" :class="{ active: currentChapterIdx === idx }"
              @click="goChapter(idx)" :title="ch.title"/>
          </div>
          <button class="cnb-btn" :disabled="currentChapterIdx >= totalChapters - 1"
            @click="goChapter(currentChapterIdx + 1)">
            下一章
            <svg viewBox="0 0 20 20" fill="currentColor"><path d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"/></svg>
          </button>
        </div>
      </main>

      <!-- ── 右侧 AI 助手 ── -->
      <aside class="ai-panel" :class="{ hidden: !aiOpen }">
        <!-- AI 头部 -->
        <div class="ai-hdr">
          <div class="ai-hdr-left">
            <span class="ai-avatar">AI</span>
            <div>
              <div class="ai-name">AI助手</div>
              <div class="ai-status">
                <span class="ai-status-dot" :class="{ loading: aiLoading }"/>
                {{ aiLoading ? '思考中…' : '在线' }}
              </div>
            </div>
          </div>
          <button class="ai-close-btn" @click="aiOpen = false">
            <svg viewBox="0 0 20 20" fill="currentColor"><path d="M15 5l-10 10M5 5l10 10"/></svg>
          </button>
        </div>

        <!-- 消息列表 -->
        <div class="ai-msg-list" ref="aiScrollRef">
          <div v-for="(msg, i) in aiMessages" :key="i"
            class="ai-msg" :class="msg.role">
            <div class="ai-msg-avatar">{{ msg.role === 'ai' ? 'AI' : '我' }}</div>
            <div class="ai-msg-bubble">
              <span v-if="msg.streaming && !msg.text" class="ai-typing">
                <span/><span/><span/>
              </span>
              <div v-else class="ai-bubble-md markdown-doc compact"
                v-html="renderMarkdown(msg.text || '…')"/>
            </div>
          </div>
        </div>

        <!-- 快速问题 -->
        <div class="ai-quick-wrap" v-if="!aiLoading">
          <button v-for="q in quickQuestions" :key="q" class="ai-quick-btn" @click="useQuick(q)">
            {{ q }}
          </button>
        </div>

        <!-- 输入区 -->
        <div class="ai-input-area">
          <textarea
            v-model="aiInput"
            class="ai-textarea"
            rows="2"
            placeholder="输入你的问题…（Enter 发送，Shift+Enter 换行）"
            @keydown.enter.exact.prevent="sendAIMessage"
          />
          <button class="ai-send" :disabled="aiLoading || !aiInput.trim()" @click="sendAIMessage">
            <svg viewBox="0 0 20 20" fill="currentColor">
              <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z"/>
            </svg>
          </button>
        </div>
      </aside>
    </div>

    <!-- ═══════ 文字选中悬浮按钮 ═══════ -->
    <Teleport to="body">
      <div v-if="selPopup.show" class="sel-popup"
        :style="{ left: selPopup.x + 'px', top: selPopup.y + 'px' }"
        @mousedown.prevent>
        <button class="sel-popup-btn" @click="askAboutSelection">
          <svg viewBox="0 0 20 20" fill="currentColor"><path d="M2 5a2 2 0 012-2h7a2 2 0 012 2v4a2 2 0 01-2 2H9l-3 3v-3H4a2 2 0 01-2-2V5z"/></svg>
          向 AI 提问
        </button>
      </div>
    </Teleport>

  </div>
</template>

<style scoped>
/* ──────────────────────────────────
   整体布局
────────────────────────────────── */
.reader-wrap {
  display: flex; flex-direction: column;
  height: calc(100vh - 58px);
  background: #0a1628;
  overflow: hidden;
  margin: -24px;   /* 撑满父级 padding */
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

/* ──────────────────────────────────
   顶部工具栏
────────────────────────────────── */
.reader-hdr {
  display: flex; align-items: center; justify-content: space-between;
  height: 48px; padding: 0 12px;
  background: #0d1e3a;
  border-bottom: 1px solid rgba(74,144,217,0.2);
  flex-shrink: 0; gap: 8px;
}
.rh-left, .rh-right { display: flex; align-items: center; gap: 6px; min-width: 200px; }
.rh-right { justify-content: flex-end; }
.rh-center { flex: 1; text-align: center; }
.rh-title { font-size: 13px; font-weight: 600; color: #cce4f7; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.rh-icon-btn {
  width: 28px; height: 28px; border: none; background: transparent;
  border-radius: 5px; cursor: pointer; color: #6890b0; display: flex;
  align-items: center; justify-content: center; transition: all 0.15s;
  font-size: 14px;
}
.rh-icon-btn svg { width: 15px; height: 15px; }
.rh-icon-btn:hover:not(:disabled) { background: rgba(74,144,217,0.15); color: #93c5fd; }
.rh-icon-btn:disabled { opacity: 0.3; cursor: not-allowed; }
.rh-sep { width: 1px; height: 18px; background: rgba(74,144,217,0.2); margin: 0 2px; }
.rh-breadcrumb { font-size: 12px; color: #4a7fa8; cursor: pointer; }
.rh-breadcrumb:hover { color: #60a5fa; }
.rh-breadcrumb.active { color: #94a3b8; cursor: default; }
.rh-bc-arrow { width: 12px; height: 12px; color: #2d4a6a; }
.rh-pages { font-size: 12px; color: #6890b0; min-width: 50px; text-align: center; }
.rh-zoom-val { font-size: 12px; color: #6890b0; min-width: 38px; text-align: center; }
.rh-ai-btn {
  display: flex; align-items: center; gap: 5px;
  padding: 4px 10px; border-radius: 5px; border: 1px solid rgba(74,144,217,0.3);
  background: transparent; color: #6890b0; cursor: pointer; font-size: 11px;
  transition: all 0.15s;
}
.rh-ai-btn.active { background: rgba(29,78,216,0.25); border-color: #3b82f6; color: #60a5fa; }
.rh-ai-btn:hover { border-color: #60a5fa; color: #93c5fd; }
.ai-dot {
  width: 7px; height: 7px; border-radius: 50%;
  background: #22c55e; box-shadow: 0 0 6px #22c55e;
  animation: pulse-dot 2s infinite;
}
@keyframes pulse-dot {
  0%, 100% { opacity: 1; } 50% { opacity: 0.4; }
}

/* ──────────────────────────────────
   主体三栏
────────────────────────────────── */
.reader-body { display: flex; flex: 1; overflow: hidden; }

/* ── 左侧面板 ── */
.reader-left {
  width: 220px; flex-shrink: 0;
  background: #0d1e3a;
  border-right: 1px solid rgba(74,144,217,0.15);
  display: flex; flex-direction: column;
  transition: width 0.2s;
  overflow: hidden;
}
.reader-left.collapsed { width: 36px; }

.left-toggle {
  width: 36px; height: 36px; flex-shrink: 0;
  background: transparent; border: none; cursor: pointer;
  color: #4a7fa8; display: flex; align-items: center; justify-content: center;
  border-bottom: 1px solid rgba(74,144,217,0.15);
}
.left-toggle svg { width: 16px; height: 16px; }
.left-toggle:hover { color: #60a5fa; background: rgba(74,144,217,0.1); }

.left-tabs { display: flex; border-bottom: 1px solid rgba(74,144,217,0.15); flex-shrink: 0; }
.ltab {
  flex: 1; display: flex; align-items: center; justify-content: center; gap: 4px;
  padding: 8px 0; font-size: 11px; background: transparent; border: none;
  border-bottom: 2px solid transparent; color: #4a7fa8; cursor: pointer; transition: all 0.15s;
}
.ltab:hover { color: #94a3b8; }
.ltab.active { color: #60a5fa; border-bottom-color: #3b82f6; }
.ltab-icon { width: 13px; height: 13px; }

.toc-list { flex: 1; overflow-y: auto; padding: 8px 0; }
.toc-book-title { font-size: 11px; color: #3a6080; letter-spacing: 0.5px;
  padding: 4px 12px 8px; text-overflow: ellipsis; overflow: hidden; white-space: nowrap; }
.toc-item {
  display: flex; align-items: flex-start; gap: 8px;
  width: 100%; padding: 8px 12px; background: transparent;
  border: none; cursor: pointer; text-align: left;
  transition: background 0.12s; border-radius: 0;
}
.toc-item:hover { background: rgba(74,144,217,0.08); }
.toc-item.active { background: rgba(29,78,216,0.2); }
.toc-num { font-size: 10px; color: #3b82f6; font-family: monospace; flex-shrink: 0; margin-top: 1px; }
.toc-label { font-size: 12px; color: #7095b8; line-height: 1.4; }
.toc-item.active .toc-label { color: #93c5fd; }

.thumb-list { flex: 1; overflow-y: auto; padding: 8px; display: flex; flex-direction: column; gap: 8px; }
.thumb-item { cursor: pointer; border-radius: 6px; overflow: hidden;
  border: 1px solid rgba(30,58,95,0.6); transition: border-color 0.15s; }
.thumb-item:hover { border-color: rgba(59,130,246,0.4); }
.thumb-item.active { border-color: #3b82f6; box-shadow: 0 0 0 1px #3b82f6; }
.thumb-page {
  padding: 8px; min-height: 80px; background: #0d2040;
  border-bottom: 1px solid rgba(30,58,95,0.4);
}
.thumb-pg-title { font-size: 9px; font-weight: 600; color: #60a5fa;
  margin-bottom: 4px; line-height: 1.3; }
.thumb-pg-text { font-size: 8px; color: #3a6080; line-height: 1.4; }
.thumb-pg-num { display: block; text-align: center; font-size: 10px;
  color: #3a6080; padding: 3px; }
.thumb-item.active .thumb-pg-num { color: #60a5fa; }

/* ── 文档区域 ── */
.doc-area {
  flex: 1; overflow-y: auto; overflow-x: hidden;
  background: #111e35;
  display: flex; flex-direction: column; align-items: center;
  padding: 32px 24px 24px;
}
.doc-page-wrap { width: 100%; max-width: 820px; }
.doc-page {
  background: #fff;
  border-radius: 4px;
  box-shadow: 0 4px 24px rgba(0,0,0,0.5), 0 0 0 1px rgba(0,0,0,0.1);
  padding: 48px 64px;
  min-height: 600px;
  position: relative;
}
.doc-header-bar {
  display: flex; justify-content: space-between;
  font-size: 10px; color: #9ca3af; letter-spacing: 0.5px;
  padding-bottom: 12px; margin-bottom: 24px;
  border-bottom: 1px solid #e5e7eb;
}
.doc-hd-book { text-overflow: ellipsis; overflow: hidden; white-space: nowrap; max-width: 55%; }
.doc-hd-chapter { color: #6b7280; }
.doc-footer-bar {
  display: flex; justify-content: space-between;
  font-size: 10px; color: #9ca3af; letter-spacing: 0.5px;
  padding-top: 16px; margin-top: 32px;
  border-top: 1px solid #e5e7eb;
}

/* Markdown 文档排版（白底页面） */
.markdown-doc :deep(h1) { font-size: 1.6em; font-weight: 700; color: #111827; margin: 0 0 0.8em; }
.markdown-doc :deep(h2) { font-size: 1.25em; font-weight: 600; color: #1f2937; margin: 1.6em 0 0.6em; border-bottom: 1px solid #e5e7eb; padding-bottom: 6px; }
.markdown-doc :deep(h3) { font-size: 1.05em; font-weight: 600; color: #374151; margin: 1.2em 0 0.5em; }
.markdown-doc :deep(p) { font-size: 0.9em; color: #374151; line-height: 1.85; margin-bottom: 0.8em; }
.markdown-doc :deep(table) { width: 100%; border-collapse: collapse; font-size: 0.85em; margin: 1em 0; }
.markdown-doc :deep(th) { background: #f3f4f6; color: #1f2937; padding: 8px 12px; border: 1px solid #e5e7eb; font-weight: 600; text-align: left; }
.markdown-doc :deep(td) { padding: 7px 12px; color: #4b5563; border: 1px solid #e5e7eb; }
.markdown-doc :deep(tr:nth-child(even) td) { background: #f9fafb; }
.markdown-doc :deep(pre) { background: #1f2937; border-radius: 6px; padding: 14px 18px; overflow-x: auto; margin: 1em 0; }
.markdown-doc :deep(code) { font-family: 'Courier New', monospace; font-size: 0.85em; background: #f3f4f6; color: #dc2626; padding: 1px 5px; border-radius: 3px; }
.markdown-doc :deep(pre code) { background: none; color: #e5e7eb; padding: 0; }
.markdown-doc :deep(strong) { color: #1d4ed8; font-weight: 600; }
.markdown-doc :deep(em) { color: #7c3aed; }
.markdown-doc :deep(blockquote) { border-left: 3px solid #3b82f6; background: #eff6ff; padding: 10px 14px; border-radius: 0 4px 4px 0; margin: 1em 0; color: #1e40af; font-size: 0.88em; }
.markdown-doc :deep(ul), .markdown-doc :deep(ol) { padding-left: 1.5em; color: #374151; font-size: 0.9em; }
.markdown-doc :deep(li) { margin-bottom: 4px; line-height: 1.7; }
.markdown-doc :deep(a) { color: #2563eb; text-decoration: underline; }
/* 紧凑版（AI 气泡中） */
.markdown-doc.compact :deep(p), .markdown-doc.compact :deep(li) { font-size: 0.82em; margin-bottom: 4px; }
.markdown-doc.compact :deep(h1), .markdown-doc.compact :deep(h2), .markdown-doc.compact :deep(h3) { font-size: 0.9em; }
.markdown-doc.compact :deep(th), .markdown-doc.compact :deep(td) { padding: 4px 8px; font-size: 0.78em; }

/* 章节导航条 */
.chapter-nav-bar {
  display: flex; align-items: center; justify-content: space-between;
  width: 100%; max-width: 820px; margin-top: 20px;
  padding: 12px 0;
}
.cnb-btn {
  display: flex; align-items: center; gap: 5px;
  padding: 7px 16px; background: rgba(29,78,216,0.2);
  border: 1px solid rgba(59,130,246,0.3); border-radius: 6px;
  color: #60a5fa; cursor: pointer; font-size: 12px; transition: all 0.15s;
}
.cnb-btn svg { width: 14px; height: 14px; }
.cnb-btn:hover:not(:disabled) { background: rgba(29,78,216,0.4); border-color: #60a5fa; }
.cnb-btn:disabled { opacity: 0.3; cursor: not-allowed; }
.cnb-chapters { display: flex; gap: 5px; align-items: center; }
.cnb-dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: rgba(74,144,217,0.25); border: 1px solid rgba(74,144,217,0.3);
  cursor: pointer; transition: all 0.15s;
}
.cnb-dot:hover { background: rgba(74,144,217,0.5); }
.cnb-dot.active { background: #3b82f6; border-color: #60a5fa; box-shadow: 0 0 6px #3b82f6; }

/* ── AI 面板 ── */
.ai-panel {
  width: 300px; flex-shrink: 0;
  background: #0d1e3a;
  border-left: 1px solid rgba(74,144,217,0.2);
  display: flex; flex-direction: column;
  transition: width 0.2s, opacity 0.2s;
}
.ai-panel.hidden { width: 0; opacity: 0; overflow: hidden; }

.ai-hdr {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 14px; border-bottom: 1px solid rgba(74,144,217,0.15);
  flex-shrink: 0;
}
.ai-hdr-left { display: flex; align-items: center; gap: 10px; }
.ai-avatar {
  width: 32px; height: 32px; border-radius: 8px;
  background: linear-gradient(135deg, #1d4ed8, #4f46e5);
  display: flex; align-items: center; justify-content: center;
  font-size: 10px; font-weight: 800; color: #bae6fd; letter-spacing: 0.5px;
}
.ai-name { font-size: 13px; font-weight: 600; color: #cce4f7; }
.ai-status { display: flex; align-items: center; gap: 4px; font-size: 10px; color: #6890b0; }
.ai-status-dot { width: 6px; height: 6px; border-radius: 50%; background: #22c55e; }
.ai-status-dot.loading { background: #f59e0b; animation: pulse-dot 0.6s infinite; }
.ai-close-btn {
  background: transparent; border: none; cursor: pointer; color: #4a7fa8;
  width: 24px; height: 24px; border-radius: 4px; display: flex; align-items: center; justify-content: center;
}
.ai-close-btn svg { width: 14px; height: 14px; }
.ai-close-btn:hover { color: #94a3b8; background: rgba(74,144,217,0.1); }

.ai-msg-list { flex: 1; overflow-y: auto; padding: 12px 12px 0; display: flex; flex-direction: column; gap: 12px; }
.ai-msg { display: flex; gap: 8px; align-items: flex-start; }
.ai-msg.user { flex-direction: row-reverse; }
.ai-msg-avatar {
  width: 26px; height: 26px; border-radius: 6px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  font-size: 9px; font-weight: 700;
}
.ai-msg.ai .ai-msg-avatar { background: linear-gradient(135deg, #1d4ed8, #4f46e5); color: #bae6fd; }
.ai-msg.user .ai-msg-avatar { background: rgba(74,144,217,0.2); color: #60a5fa; }
.ai-msg-bubble { max-width: calc(100% - 38px); }
.ai-msg.ai .ai-msg-bubble { background: rgba(13,31,60,0.8); border: 1px solid rgba(30,58,95,0.6); border-radius: 0 8px 8px 8px; padding: 9px 12px; }
.ai-msg.user .ai-msg-bubble { background: rgba(29,78,216,0.25); border: 1px solid rgba(59,130,246,0.3); border-radius: 8px 0 8px 8px; padding: 9px 12px; }
.ai-msg.user .ai-bubble-md :deep(p) { color: #bae6fd; }

/* AI 气泡中的 Markdown 颜色覆盖（深色背景） */
.ai-msg .markdown-doc :deep(h1), .ai-msg .markdown-doc :deep(h2), .ai-msg .markdown-doc :deep(h3) { color: #93c5fd; }
.ai-msg .markdown-doc :deep(p) { color: #94a3b8; }
.ai-msg .markdown-doc :deep(strong) { color: #60a5fa; }
.ai-msg .markdown-doc :deep(em) { color: #c084fc; }
.ai-msg .markdown-doc :deep(th) { background: rgba(29,78,216,0.2); color: #60a5fa; border-color: rgba(30,58,95,0.5); }
.ai-msg .markdown-doc :deep(td) { color: #94a3b8; border-color: rgba(30,58,95,0.4); }
.ai-msg .markdown-doc :deep(blockquote) { background: rgba(29,78,216,0.1); color: #60a5fa; border-left-color: #3b82f6; }
.ai-msg .markdown-doc :deep(code) { background: rgba(0,0,0,0.3); color: #a5f3fc; }

/* 打字动画 */
.ai-typing { display: flex; gap: 4px; align-items: center; padding: 2px 0; }
.ai-typing span { width: 6px; height: 6px; border-radius: 50%; background: #4a90d9; animation: bounce-dot 1.2s infinite; }
.ai-typing span:nth-child(2) { animation-delay: 0.2s; }
.ai-typing span:nth-child(3) { animation-delay: 0.4s; }
@keyframes bounce-dot { 0%,60%,100% { transform: translateY(0); } 30% { transform: translateY(-5px); } }

/* 快速问题 */
.ai-quick-wrap { padding: 8px 12px; display: flex; flex-wrap: wrap; gap: 4px; flex-shrink: 0; }
.ai-quick-btn {
  font-size: 10px; padding: 3px 8px;
  background: rgba(15,40,80,0.8); border: 1px solid rgba(30,58,95,0.6);
  border-radius: 4px; color: #4a7fa8; cursor: pointer; transition: all 0.12s;
  white-space: nowrap;
}
.ai-quick-btn:hover { border-color: rgba(59,130,246,0.4); color: #7ec8f7; }

/* 输入区 */
.ai-input-area { display: flex; gap: 6px; padding: 10px 12px; border-top: 1px solid rgba(74,144,217,0.15); flex-shrink: 0; }
.ai-textarea {
  flex: 1; background: rgba(13,31,60,0.8); border: 1px solid rgba(30,58,95,0.8);
  border-radius: 6px; padding: 8px 10px; color: #cdd9ea; font-size: 12px;
  resize: none; outline: none; font-family: inherit; line-height: 1.5;
}
.ai-textarea:focus { border-color: rgba(59,130,246,0.5); }
.ai-textarea::placeholder { color: #3a6080; }
.ai-send {
  width: 36px; height: 36px; border-radius: 6px; border: none; flex-shrink: 0; align-self: flex-end;
  background: rgba(29,78,216,0.7); color: #bae6fd; cursor: pointer; display: flex;
  align-items: center; justify-content: center; transition: all 0.15s;
}
.ai-send svg { width: 15px; height: 15px; }
.ai-send:hover:not(:disabled) { background: rgba(37,99,235,0.9); }
.ai-send:disabled { opacity: 0.35; cursor: not-allowed; }

/* ══════ 文字选中悬浮按钮 ══════ */
.sel-popup {
  position: fixed; z-index: 9999;
  transform: translateX(-50%);
  pointer-events: all;
}
.sel-popup-btn {
  display: flex; align-items: center; gap: 5px;
  padding: 6px 12px;
  background: #1d4ed8;
  border: 1px solid rgba(147,197,253,0.4);
  border-radius: 20px;
  color: #bae6fd; font-size: 12px; cursor: pointer;
  box-shadow: 0 4px 16px rgba(0,0,0,0.5);
  white-space: nowrap;
  transition: background 0.15s;
}
.sel-popup-btn svg { width: 13px; height: 13px; }
.sel-popup-btn:hover { background: #1e40af; }
.sel-popup-btn::after {
  content: ''; position: absolute;
  top: 100%; left: 50%; transform: translateX(-50%);
  border: 5px solid transparent; border-top-color: #1d4ed8;
}

/* 滚动条样式 */
.doc-area::-webkit-scrollbar, .toc-list::-webkit-scrollbar,
.thumb-list::-webkit-scrollbar, .ai-msg-list::-webkit-scrollbar {
  width: 5px;
}
.doc-area::-webkit-scrollbar-track, .toc-list::-webkit-scrollbar-track,
.thumb-list::-webkit-scrollbar-track, .ai-msg-list::-webkit-scrollbar-track {
  background: transparent;
}
.doc-area::-webkit-scrollbar-thumb, .toc-list::-webkit-scrollbar-thumb,
.thumb-list::-webkit-scrollbar-thumb, .ai-msg-list::-webkit-scrollbar-thumb {
  background: rgba(74,144,217,0.2); border-radius: 3px;
}
.doc-area::-webkit-scrollbar-thumb:hover { background: rgba(74,144,217,0.4); }
</style>
