<script setup lang="ts">
import { ref, onMounted } from 'vue'
import apiClient from '@/api/client'

// ── Tab 切换 ──────────────────────────────────────────────────────
type Tab = 'upload' | 'search' | 'qa' | 'stats'
const activeTab = ref<Tab>('upload')
const bsTabs: { key: Tab; label: string }[] = [
  { key: 'upload', label: '📤 上传文档' },
  { key: 'search', label: '🔍 语义搜索' },
  { key: 'qa', label: '💬 智能问答' },
  { key: 'stats', label: '📊 知识库统计' },
]

// ── 上传区 ────────────────────────────────────────────────────────
const uploadText = ref('')
const uploadSource = ref('')
const isMarkdown = ref(false)
const uploading = ref(false)
const uploadResult = ref<{ success: boolean; message: string; chunks?: number } | null>(null)

const uploadedDocs = ref<{ source: string; chunks: number; timestamp: string }[]>([])

async function handleUpload() {
  if (!uploadText.value.trim() || !uploadSource.value.trim()) return
  uploading.value = true
  uploadResult.value = null
  try {
    const { data } = await apiClient.post('/api/v1/kb/upload', {
      content: uploadText.value,
      source: uploadSource.value,
      is_markdown: isMarkdown.value,
    })
    uploadResult.value = { success: true, message: data.message, chunks: data.chunks_added }
    uploadedDocs.value.unshift({
      source: uploadSource.value,
      chunks: data.chunks_added,
      timestamp: new Date().toLocaleTimeString(),
    })
    uploadText.value = ''
    uploadSource.value = ''
  } catch (e: unknown) {
    const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '上传失败'
    uploadResult.value = { success: false, message: msg }
  } finally {
    uploading.value = false
  }
}

// 预设网络知识文本（便于演示）
const presets = [
  {
    name: 'TCP三次握手详解',
    source: 'TCP连接建立-自学笔记',
    content: `# TCP 三次握手

TCP 三次握手（Three-way Handshake）是 TCP 协议建立可靠连接的标准过程。

## 流程

**第一次握手（SYN）**
客户端发送 SYN 报文段，设置 SYN=1，选择随机初始序列号 ISN(c)，进入 SYN_SENT 状态。
- 报文头部: SYN=1, seq=x (x 为 ISN)

**第二次握手（SYN+ACK）**
服务端收到 SYN 后，发送 SYN+ACK 报文，选择自己的 ISN(s)，确认客户端序列号，进入 SYN_RCVD 状态。
- 报文头部: SYN=1, ACK=1, seq=y, ack=x+1

**第三次握手（ACK）**
客户端发送 ACK 确认服务端 SYN，双方进入 ESTABLISHED 状态，连接建立完成。
- 报文头部: ACK=1, seq=x+1, ack=y+1

## 为什么需要三次握手？

两次握手无法防止历史连接请求。若网络中存在延迟的旧 SYN 报文，服务端在两次握手下会误建立连接，浪费资源。第三次 ACK 的作用是让服务端确认客户端能正常接收，防止历史失效请求干扰。

## SYN 洪泛攻击
攻击者发送大量 SYN 包但不响应 SYN+ACK，导致服务端半连接队列溢出，无法处理正常连接。
防御：SYN Cookie 技术（不分配资源直到完成三次握手）。`,
    isMarkdown: true,
  },
  {
    name: 'HTTP/1.1 vs HTTP/2 对比',
    source: 'HTTP协议对比文档',
    content: `# HTTP/1.1 vs HTTP/2 核心差异

## HTTP/1.1 局限性
- **队头阻塞 (HOL Blocking)**：同一 TCP 连接按序处理请求，前一请求未完成则后续等待
- **无头部压缩**：每次请求都携带完整 HTTP 头，重复 Cookie/UA 等字段浪费带宽
- **明文协议**：本身不加密（需配合 TLS）

## HTTP/2 改进

**多路复用 (Multiplexing)**
在同一 TCP 连接上并行传输多个请求/响应流，解决 HOL 阻塞。每个流有独立 stream_id。

**HPACK 头部压缩**
使用 Huffman 编码 + 索引表压缩头部，减少 80%+ 头部体积。

**服务端推送 (Server Push)**
服务端可主动推送资源（如 CSS/JS），减少往返延迟。

**二进制分帧**
将消息拆成二进制帧传输，解析更高效，替代 HTTP/1.1 的文本格式。

## HTTP/3 (QUIC)
基于 UDP 的 QUIC 协议，彻底解决 TCP 层面的 HOL 阻塞，内置 TLS 1.3，连接建立更快（0-RTT）。`,
    isMarkdown: true,
  },
  {
    name: 'DNS递归与迭代查询',
    source: 'DNS协议学习笔记',
    content: `# DNS 解析过程详解

DNS（Domain Name System）将域名解析为 IP 地址，采用分布式层次数据库架构。

## 查询类型

**递归查询（Recursive Query）**
客户端向本地 DNS 发起查询，本地 DNS 负责代为查询并返回最终结果。
客户端只需一次请求即可获得答案。

**迭代查询（Iterative Query）**
本地 DNS 向根/TLD/权威服务器依次迭代查询，每步返回"下一步询问谁"的指引。

## 完整解析流程

1. 浏览器检查本地 DNS 缓存（hosts 文件 → 浏览器缓存）
2. 操作系统递归查询本地 DNS 服务器
3. 本地 DNS 迭代查询根服务器 → 获得 .com TLD 地址
4. 迭代查询 .com TLD → 获得 example.com 权威 DNS 地址
5. 迭代查询权威 DNS → 获得最终 IP 地址
6. 本地 DNS 将结果返回客户端，并按 TTL 缓存

## 记录类型
- A：域名 → IPv4 地址
- AAAA：域名 → IPv6 地址
- CNAME：别名 → 规范域名
- MX：邮件服务器
- NS：域名 → 权威 DNS 服务器`,
    isMarkdown: true,
  },
]

function loadPreset(p: typeof presets[0]) {
  uploadText.value = p.content
  uploadSource.value = p.source
  isMarkdown.value = p.isMarkdown
}

// ── 搜索区 ────────────────────────────────────────────────────────
const searchQuery = ref('')
const searchCollection = ref('user_uploads')
const searchResults = ref<{ document: string; metadata?: { source?: string }; distance?: number }[]>([])
const searching = ref(false)
const searched = ref(false)

async function handleSearch() {
  if (!searchQuery.value.trim()) return
  searching.value = true
  searched.value = false
  searchResults.value = []
  try {
    const { data } = await apiClient.post('/api/v1/kb/search', {
      query: searchQuery.value,
      collection: searchCollection.value,
      n_results: 5,
    })
    searchResults.value = data.results || []
    searched.value = true
  } catch {
    searched.value = true
  } finally {
    searching.value = false
  }
}

// ── Q&A 区 ────────────────────────────────────────────────────────
interface QARecord {
  question: string
  answer: string
  sources: string[]
  timestamp: string
}
const qaQuestion = ref('')
const qaRecords = ref<QARecord[]>([])
const qaLoading = ref(false)

async function handleQA() {
  if (!qaQuestion.value.trim()) return
  qaLoading.value = true
  const q = qaQuestion.value
  qaQuestion.value = ''

  try {
    // 先搜索相关文档
    const { data: searchData } = await apiClient.post('/api/v1/kb/search', {
      query: q,
      collection: searchCollection.value,
      n_results: 3,
    })
    const docs = (searchData.results || []) as { document: string; metadata?: { source?: string } }[]
    const sources = docs.map(d => d.metadata?.source || '未知来源').filter((v, i, a) => a.indexOf(v) === i)
    const context = docs.map(d => d.document.slice(0, 300)).join('\n---\n')

    // 调用 chat API 生成答案（context 作为 background）
    const chatContext = context
      ? `基于以下知识库内容回答问题：\n${context}\n\n问题：${q}\n请给出准确、详细的解答。`
      : `请回答以下计算机网络问题：${q}`

    const { data: chatData } = await apiClient.post('/api/v1/resources/generate', {
      knowledge_point: q,
      resource_type: 'doc',
      difficulty: 2,
      context: chatContext,
    }).catch(() => ({ data: null }))

    const answer = chatData?.content || chatData?.description
      || `关于「${q}」的回答：\n\n${context ? '根据你的知识库内容：\n' + docs[0]?.document?.slice(0, 400) : '暂无相关内容，请先上传相关学习资料。'}`

    qaRecords.value.unshift({
      question: q,
      answer,
      sources,
      timestamp: new Date().toLocaleTimeString(),
    })
  } catch {
    qaRecords.value.unshift({
      question: q,
      answer: '查询失败，请检查知识库是否已上传内容。',
      sources: [],
      timestamp: new Date().toLocaleTimeString(),
    })
  } finally {
    qaLoading.value = false
  }
}

// ── 统计区 ────────────────────────────────────────────────────────
interface KBStats {
  collections: Record<string, number>
  total: number
}
const kbStats = ref<KBStats | null>(null)
const loadingStats = ref(false)

async function loadStats() {
  loadingStats.value = true
  try {
    const { data } = await apiClient.get('/api/v1/kb/stats')
    kbStats.value = data
  } catch {
    kbStats.value = null
  } finally {
    loadingStats.value = false
  }
}

const collectionLabels: Record<string, { label: string; icon: string; color: string }> = {
  course_docs: { label: '课程文档', icon: '📚', color: '#3b82f6' },
  protocol_specs: { label: '协议规范', icon: '📋', color: '#10b981' },
  misconceptions: { label: '误区库', icon: '⚠️', color: '#ef4444' },
  user_uploads: { label: '用户上传', icon: '📤', color: '#7c3aed' },
}

onMounted(() => {
  loadStats()
})
</script>

<template>
  <div class="bookshelf-view">
    <div class="bs-header">
      <h1>📚 PDF 智能知识库</h1>
      <p class="bs-subtitle">上传学习资料，构建专属知识库，支持语义搜索与智能问答</p>
    </div>

    <!-- Tab 切换 -->
    <div class="bs-tabs">
      <button
        v-for="tab in bsTabs"
        :key="tab.key"
        :class="['bs-tab', { active: activeTab === tab.key }]"
        @click="activeTab = tab.key"
      >{{ tab.label }}</button>
    </div>

    <!-- 上传 Tab -->
    <div v-if="activeTab === 'upload'" class="tab-content">
      <div class="upload-area">
        <div class="upload-main">
          <h3 class="section-title">上传学习资料</h3>
          <div class="form-row">
            <label>文档来源（名称）</label>
            <input v-model="uploadSource" placeholder="如：TCP协议笔记、RFC793摘要、第3章课件" class="form-input" />
          </div>
          <div class="form-row">
            <label>文档内容（粘贴文本）</label>
            <textarea
              v-model="uploadText"
              placeholder="粘贴文本内容，支持纯文本或 Markdown 格式..."
              rows="12"
              class="form-textarea"
            ></textarea>
          </div>
          <div class="form-row row-inline">
            <label class="toggle-label">
              <input type="checkbox" v-model="isMarkdown" />
              <span>Markdown 格式</span>
            </label>
            <div class="char-count">{{ uploadText.length }} 字符</div>
          </div>

          <button class="btn-upload" :disabled="uploading || !uploadText.trim() || !uploadSource.trim()" @click="handleUpload">
            <span v-if="uploading">⏳ 处理并入库中...</span>
            <span v-else>🚀 上传到知识库</span>
          </button>

          <div v-if="uploadResult" :class="['upload-result', uploadResult.success ? 'success' : 'error']">
            {{ uploadResult.success ? '✅' : '❌' }} {{ uploadResult.message }}
            <span v-if="uploadResult.chunks"> ({{ uploadResult.chunks }} 个知识块)</span>
          </div>
        </div>

        <!-- 预设内容 -->
        <div class="upload-presets">
          <h3 class="section-title">📋 预设知识片段（一键加载）</h3>
          <p class="preset-tip">点击加载经典计算机网络知识片段，快速体验知识库功能</p>
          <div class="preset-list">
            <div v-for="p in presets" :key="p.name" class="preset-card" @click="loadPreset(p)">
              <div class="pc-name">{{ p.name }}</div>
              <div class="pc-source">{{ p.source }}</div>
              <div class="pc-len">{{ p.content.length }} 字符</div>
            </div>
          </div>

          <!-- 已上传文档列表 -->
          <div v-if="uploadedDocs.length" class="uploaded-list">
            <h4>本次已上传 ({{ uploadedDocs.length }})</h4>
            <div v-for="doc in uploadedDocs" :key="doc.source" class="ul-item">
              <span class="ul-icon">📄</span>
              <span class="ul-name">{{ doc.source }}</span>
              <span class="ul-chunks">{{ doc.chunks }} 块</span>
              <span class="ul-time">{{ doc.timestamp }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 搜索 Tab -->
    <div v-if="activeTab === 'search'" class="tab-content">
      <div class="search-area">
        <h3 class="section-title">语义相似度搜索</h3>
        <div class="search-bar">
          <select v-model="searchCollection" class="coll-select">
            <option value="user_uploads">用户上传</option>
            <option value="course_docs">课程文档</option>
            <option value="protocol_specs">协议规范</option>
            <option value="misconceptions">误区库</option>
          </select>
          <input
            v-model="searchQuery"
            placeholder="输入搜索内容，如：TCP三次握手第三个ACK的作用..."
            class="search-input"
            @keydown.enter="handleSearch"
          />
          <button class="btn-search" :disabled="searching || !searchQuery.trim()" @click="handleSearch">
            <span v-if="searching">搜索中...</span>
            <span v-else>搜索</span>
          </button>
        </div>

        <div class="search-tips">
          <span>💡 示例搜索：</span>
          <span
            v-for="tip in ['TCP滑动窗口', 'HTTP状态码', 'DNS递归查询', 'ARP协议', '子网掩码计算']"
            :key="tip"
            class="search-tip-tag"
            @click="searchQuery = tip; handleSearch()"
          >{{ tip }}</span>
        </div>

        <div v-if="searching" class="loading-msg">🔍 向量检索中...</div>

        <div v-else-if="searched && !searchResults.length" class="empty-result">
          未找到相关内容。请先上传相关文档，或切换到其他集合搜索。
        </div>

        <div v-else-if="searchResults.length" class="search-results">
          <div class="sr-count">找到 {{ searchResults.length }} 条相关知识片段</div>
          <div v-for="(res, idx) in searchResults" :key="idx" class="sr-item">
            <div class="sr-header">
              <span class="sr-rank">#{{ idx + 1 }}</span>
              <span class="sr-source">{{ res.metadata?.source || '未知来源' }}</span>
              <span v-if="res.distance != null" class="sr-dist">
                相关度: {{ (1 - res.distance).toFixed(2) }}
              </span>
            </div>
            <div class="sr-content">{{ res.document }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Q&A Tab -->
    <div v-if="activeTab === 'qa'" class="tab-content">
      <div class="qa-area">
        <h3 class="section-title">基于知识库的智能问答</h3>
        <p class="qa-tip">AI 将优先从你的知识库中检索相关内容来回答问题</p>

        <div class="qa-input-bar">
          <select v-model="searchCollection" class="coll-select">
            <option value="user_uploads">用户上传</option>
            <option value="course_docs">课程文档</option>
            <option value="protocol_specs">协议规范</option>
          </select>
          <textarea
            v-model="qaQuestion"
            placeholder="问一个计算机网络问题..."
            rows="2"
            class="qa-input"
            @keydown.ctrl.enter="handleQA"
          ></textarea>
          <button class="btn-ask" :disabled="qaLoading || !qaQuestion.trim()" @click="handleQA">
            <span v-if="qaLoading">思考中...</span>
            <span v-else>提问</span>
          </button>
        </div>
        <div class="qa-shortcut">Ctrl+Enter 快速提问</div>

        <div v-if="qaLoading" class="loading-msg">🤔 正在检索知识库并生成答案...</div>

        <div v-else-if="!qaRecords.length" class="qa-empty">
          <div class="qe-icon">💡</div>
          <div class="qe-text">先上传学习资料，再来这里提问，AI 会基于你的知识库给出更准确的答案</div>
          <div class="qe-examples">
            <span v-for="q in ['TCP为什么需要三次握手？', 'HTTP/2的多路复用原理是什么？', 'DNS解析过程中递归和迭代的区别？']"
              :key="q" class="qe-q" @click="qaQuestion = q">{{ q }}</span>
          </div>
        </div>

        <div v-else class="qa-records">
          <div v-for="rec in qaRecords" :key="rec.timestamp" class="qa-record">
            <div class="qr-question">
              <span class="qr-icon">🙋</span>
              <span>{{ rec.question }}</span>
              <span class="qr-time">{{ rec.timestamp }}</span>
            </div>
            <div class="qr-answer">
              <span class="qr-ai">🤖</span>
              <div class="qr-content">
                <div class="qr-text">{{ rec.answer }}</div>
                <div v-if="rec.sources.length" class="qr-sources">
                  <span>📌 来源：</span>
                  <span v-for="src in rec.sources" :key="src" class="qr-src-tag">{{ src }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 统计 Tab -->
    <div v-if="activeTab === 'stats'" class="tab-content">
      <div class="stats-area">
        <div class="stats-header">
          <h3 class="section-title">知识库统计</h3>
          <button class="btn-refresh" @click="loadStats" :disabled="loadingStats">
            {{ loadingStats ? '刷新中...' : '🔄 刷新' }}
          </button>
        </div>

        <div v-if="kbStats" class="stats-cards">
          <div class="stat-total">
            <div class="st-num">{{ kbStats.total }}</div>
            <div class="st-label">知识块总量</div>
          </div>
          <div
            v-for="(count, name) in kbStats.collections"
            :key="name"
            class="stat-card"
            :style="{ borderTopColor: collectionLabels[name]?.color || '#64748b' }"
          >
            <div class="sc-icon">{{ collectionLabels[name]?.icon || '📦' }}</div>
            <div class="sc-count">{{ count }}</div>
            <div class="sc-label">{{ collectionLabels[name]?.label || name }}</div>
          </div>
        </div>

        <div class="info-panel">
          <h4>📖 知识库内容说明</h4>
          <div class="ip-items">
            <div v-for="(meta, key) in collectionLabels" :key="key" class="ip-item">
              <span :style="{ color: meta.color }">{{ meta.icon }}</span>
              <strong>{{ meta.label }}</strong>
              <span>：{{
                key === 'course_docs' ? '谢希仁《计算机网络》第8版教材各章节内容' :
                key === 'protocol_specs' ? 'RFC标准文档（TCP/UDP/IPv4/IPv6/HTTP/DNS/TLS/QUIC）' :
                key === 'misconceptions' ? '50+ 条常见学习误解与正确解释' :
                '你上传的个人学习笔记和资料'
              }}</span>
            </div>
          </div>
        </div>

        <div class="usage-guide">
          <h4>🚀 使用指南</h4>
          <ol>
            <li>在「上传文档」页面粘贴你的学习笔记或课件内容</li>
            <li>在「语义搜索」页面用自然语言查找相关知识</li>
            <li>在「智能问答」页面提问，AI 会基于知识库给出答案</li>
            <li>课程文档和协议规范已预置，可直接搜索</li>
          </ol>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.bookshelf-view { max-width: 1000px; margin: 0 auto; padding: 24px; }

.bs-header { text-align: center; margin-bottom: 24px; }
.bs-header h1 { font-size: 28px; font-weight: 700; color: #1e293b; margin-bottom: 8px; }
.bs-subtitle { color: #64748b; font-size: 15px; }

.bs-tabs { display: flex; gap: 4px; background: #f1f5f9; border-radius: 12px; padding: 4px; margin-bottom: 24px; flex-wrap: wrap; }
.bs-tab { flex: 1; min-width: 120px; background: transparent; border: none; padding: 10px 16px; border-radius: 8px; cursor: pointer; color: #64748b; font-size: 14px; font-weight: 500; transition: all .2s; white-space: nowrap; }
.bs-tab.active { background: white; color: #1e293b; font-weight: 700; box-shadow: 0 2px 8px rgba(0,0,0,.08); }

.tab-content { background: white; border-radius: 16px; padding: 24px; box-shadow: 0 4px 16px rgba(0,0,0,.07); }
.section-title { font-size: 16px; font-weight: 700; color: #1e293b; margin-bottom: 16px; }

/* 上传 */
.upload-area { display: grid; grid-template-columns: 1.4fr 1fr; gap: 24px; }
@media (max-width: 720px) { .upload-area { grid-template-columns: 1fr; } }
.form-row { margin-bottom: 14px; }
.form-row label { display: block; font-size: 13px; font-weight: 600; color: #374151; margin-bottom: 6px; }
.form-input { width: 100%; border: 2px solid #e2e8f0; border-radius: 8px; padding: 10px 12px; font-size: 14px; transition: border .2s; box-sizing: border-box; }
.form-input:focus { outline: none; border-color: #7c3aed; }
.form-textarea { width: 100%; border: 2px solid #e2e8f0; border-radius: 8px; padding: 12px; font-size: 13px; resize: vertical; font-family: 'Consolas', monospace; line-height: 1.5; transition: border .2s; box-sizing: border-box; color: #1e293b; }
.form-textarea:focus { outline: none; border-color: #7c3aed; }
.row-inline { display: flex; align-items: center; justify-content: space-between; }
.toggle-label { display: flex; align-items: center; gap: 8px; font-size: 13px; color: #374151; cursor: pointer; }
.char-count { font-size: 12px; color: #94a3b8; }
.btn-upload { width: 100%; background: linear-gradient(135deg, #7c3aed, #6366f1); color: white; border: none; padding: 12px; border-radius: 10px; font-size: 15px; font-weight: 600; cursor: pointer; transition: opacity .2s; margin-top: 6px; }
.btn-upload:disabled { opacity: .5; cursor: not-allowed; }
.upload-result { margin-top: 12px; padding: 12px 16px; border-radius: 8px; font-size: 14px; }
.upload-result.success { background: #f0fdf4; color: #166534; border: 1px solid #bbf7d0; }
.upload-result.error { background: #fef2f2; color: #991b1b; border: 1px solid #fecaca; }

.preset-tip { font-size: 13px; color: #64748b; margin-bottom: 12px; }
.preset-list { display: flex; flex-direction: column; gap: 8px; margin-bottom: 16px; }
.preset-card { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 12px 16px; cursor: pointer; transition: all .2s; }
.preset-card:hover { border-color: #7c3aed; background: #f5f3ff; }
.pc-name { font-size: 14px; font-weight: 600; color: #1e293b; margin-bottom: 4px; }
.pc-source { font-size: 12px; color: #64748b; }
.pc-len { font-size: 11px; color: #94a3b8; margin-top: 2px; }

.uploaded-list { border-top: 1px solid #f1f5f9; padding-top: 12px; }
.uploaded-list h4 { font-size: 13px; font-weight: 600; color: #374151; margin-bottom: 8px; }
.ul-item { display: flex; align-items: center; gap: 8px; padding: 6px 0; border-bottom: 1px solid #f8fafc; font-size: 13px; }
.ul-icon { font-size: 16px; }
.ul-name { flex: 1; color: #374151; }
.ul-chunks { color: #7c3aed; font-size: 12px; }
.ul-time { color: #94a3b8; font-size: 12px; }

/* 搜索 */
.search-bar { display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; }
.coll-select { border: 2px solid #e2e8f0; border-radius: 8px; padding: 10px 12px; font-size: 14px; color: #374151; background: white; }
.search-input { flex: 1; border: 2px solid #e2e8f0; border-radius: 8px; padding: 10px 12px; font-size: 14px; transition: border .2s; min-width: 200px; }
.search-input:focus { outline: none; border-color: #3b82f6; }
.btn-search { background: #3b82f6; color: white; border: none; padding: 10px 24px; border-radius: 8px; font-size: 14px; font-weight: 600; cursor: pointer; white-space: nowrap; }
.btn-search:disabled { opacity: .5; }
.search-tips { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin-bottom: 20px; font-size: 13px; color: #64748b; }
.search-tip-tag { background: #f1f5f9; padding: 4px 12px; border-radius: 20px; cursor: pointer; font-size: 12px; transition: background .2s; }
.search-tip-tag:hover { background: #eff6ff; color: #3b82f6; }
.loading-msg { text-align: center; padding: 40px; color: #64748b; }
.empty-result { text-align: center; padding: 40px; color: #94a3b8; }
.sr-count { font-size: 13px; color: #64748b; margin-bottom: 12px; }
.sr-item { background: #f8fafc; border-radius: 10px; padding: 16px; margin-bottom: 10px; border-left: 3px solid #3b82f6; }
.sr-header { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; flex-wrap: wrap; }
.sr-rank { background: #3b82f6; color: white; width: 22px; height: 22px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 700; flex-shrink: 0; }
.sr-source { background: #e0f2fe; color: #0369a1; padding: 2px 8px; border-radius: 6px; font-size: 12px; }
.sr-dist { color: #10b981; font-size: 12px; margin-left: auto; }
.sr-content { font-size: 13px; color: #374151; line-height: 1.6; white-space: pre-wrap; }

/* Q&A */
.qa-tip { font-size: 13px; color: #64748b; margin-bottom: 16px; }
.qa-input-bar { display: flex; gap: 8px; margin-bottom: 6px; align-items: flex-end; }
.qa-input { flex: 1; border: 2px solid #e2e8f0; border-radius: 8px; padding: 10px 12px; font-size: 14px; resize: none; font-family: inherit; transition: border .2s; }
.qa-input:focus { outline: none; border-color: #7c3aed; }
.btn-ask { background: linear-gradient(135deg, #7c3aed, #6366f1); color: white; border: none; padding: 10px 20px; border-radius: 8px; font-size: 14px; font-weight: 600; cursor: pointer; white-space: nowrap; }
.btn-ask:disabled { opacity: .5; }
.qa-shortcut { font-size: 12px; color: #94a3b8; margin-bottom: 20px; }
.qa-empty { text-align: center; padding: 40px 20px; }
.qe-icon { font-size: 48px; margin-bottom: 12px; }
.qe-text { color: #64748b; font-size: 14px; margin-bottom: 16px; }
.qe-examples { display: flex; flex-direction: column; gap: 8px; align-items: flex-start; }
.qe-q { background: #f5f3ff; color: #7c3aed; padding: 8px 16px; border-radius: 8px; cursor: pointer; font-size: 14px; border: 1px solid #e9d5ff; transition: background .2s; }
.qe-q:hover { background: #ede9fe; }
.qa-records { display: flex; flex-direction: column; gap: 16px; }
.qa-record { background: #f8fafc; border-radius: 12px; overflow: hidden; }
.qr-question { display: flex; align-items: flex-start; gap: 10px; padding: 12px 16px; background: #eff6ff; font-size: 14px; font-weight: 600; color: #1e293b; }
.qr-icon { font-size: 18px; flex-shrink: 0; }
.qr-time { margin-left: auto; font-size: 11px; color: #94a3b8; font-weight: 400; white-space: nowrap; }
.qr-answer { display: flex; align-items: flex-start; gap: 10px; padding: 16px; }
.qr-ai { font-size: 18px; flex-shrink: 0; }
.qr-content { flex: 1; }
.qr-text { font-size: 14px; color: #374151; line-height: 1.7; white-space: pre-wrap; margin-bottom: 8px; }
.qr-sources { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; font-size: 12px; color: #64748b; }
.qr-src-tag { background: #fef9c3; color: #713f12; padding: 2px 8px; border-radius: 4px; }

/* 统计 */
.stats-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.btn-refresh { background: #f1f5f9; border: none; padding: 8px 16px; border-radius: 8px; color: #374151; cursor: pointer; font-size: 13px; }
.stats-cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 14px; margin-bottom: 24px; }
.stat-total { background: linear-gradient(135deg, #6366f1, #7c3aed); color: white; border-radius: 12px; padding: 20px; text-align: center; }
.st-num { font-size: 42px; font-weight: 800; line-height: 1; }
.st-label { font-size: 13px; opacity: .85; margin-top: 4px; }
.stat-card { background: white; border: 1px solid #e2e8f0; border-top: 4px solid; border-radius: 12px; padding: 18px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,.04); }
.sc-icon { font-size: 28px; margin-bottom: 6px; }
.sc-count { font-size: 32px; font-weight: 800; color: #1e293b; }
.sc-label { font-size: 12px; color: #64748b; margin-top: 4px; }
.info-panel { background: #f8fafc; border-radius: 12px; padding: 18px; margin-bottom: 16px; }
.info-panel h4 { font-size: 14px; font-weight: 700; color: #1e293b; margin-bottom: 12px; }
.ip-items { display: flex; flex-direction: column; gap: 8px; }
.ip-item { font-size: 13px; color: #374151; display: flex; align-items: baseline; gap: 6px; }
.usage-guide { background: #fffff0; border: 1px solid #fef08a; border-radius: 12px; padding: 18px; }
.usage-guide h4 { font-size: 14px; font-weight: 700; color: #713f12; margin-bottom: 10px; }
.usage-guide ol { padding-left: 20px; }
.usage-guide li { font-size: 13px; color: #374151; margin-bottom: 6px; line-height: 1.5; }
</style>
