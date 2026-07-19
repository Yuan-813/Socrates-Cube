<script setup lang="ts">
import { ref, computed, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// ─── Types ───────────────────────────────────────────────────────────────────
type Phase = 'input' | 'generating' | 'result'

interface VideoResult {
  video_url: string
  title: string
  description: string
  generated_at: string
  topic: string
}

// ─── State ───────────────────────────────────────────────────────────────────
const phase        = ref<Phase>('input')
const freeText     = ref('')
const selectedTopic = ref('')
const isMockMode   = ref(false)
const progress     = ref(0)
const result       = ref<VideoResult | null>(null)
const errorMsg     = ref('')
let   pollTimer: ReturnType<typeof setInterval> | null = null

const MAX_LEN = 300

const TOPICS = [
  'TCP三次握手', 'IP路由原理', 'HTTP/HTTPS', 'DNS解析',
  'ARP协议', 'VLAN配置', '防火墙策略',
]

// ─── Computed ────────────────────────────────────────────────────────────────
const charCount = computed(() => freeText.value.length)
const canFreeGen = computed(() => freeText.value.trim().length > 0)
const canTopicGen = computed(() => !!selectedTopic.value)

// ─── Methods ─────────────────────────────────────────────────────────────────
function selectTopic(t: string) {
  selectedTopic.value = selectedTopic.value === t ? '' : t
}

async function startGenerate(mode: 'free' | 'topic') {
  const prompt = mode === 'free' ? freeText.value.trim() : ''
  const topic  = mode === 'topic' ? selectedTopic.value : ''
  if (mode === 'free' && !prompt) return
  if (mode === 'topic' && !topic) return

  phase.value    = 'generating'
  progress.value = 0
  errorMsg.value = ''

  try {
    const resp = await fetch('/api/v1/video/generate', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ prompt, topic }),
    })
    const data = await resp.json()
    if (!data.task_id) throw new Error('未获得 task_id')
    isMockMode.value = !!data.mock
    startPolling(data.task_id)
  } catch (e: any) {
    errorMsg.value = e?.message || '提交失败，请重试'
    phase.value = 'input'
  }
}

function startPolling(taskId: string) {
  // 模拟进度动画（独立于实际进度）
  let fakeProgress = 0
  let failCount = 0
  const fakeTimer = setInterval(() => {
    if (fakeProgress < 90) { fakeProgress += 2; progress.value = fakeProgress }
  }, 500)

  pollTimer = setInterval(async () => {
    try {
      const resp = await fetch(`/api/v1/video/status/${taskId}`)
      const data = await resp.json()
      failCount = 0  // 成功请求重置计数

      if (data.status === 'succeeded') {
        clearInterval(pollTimer!)
        clearInterval(fakeTimer)
        progress.value = 100
        result.value = {
          video_url:    data.video_url,
          title:        data.title,
          description:  data.description,
          generated_at: data.generated_at || new Date().toISOString().slice(0, 10),
          topic:        data.topic || selectedTopic.value,
        }
        setTimeout(() => { phase.value = 'result' }, 400)
      } else if (data.status === 'failed') {
        clearInterval(pollTimer!)
        clearInterval(fakeTimer)
        errorMsg.value = '生成失败，请重试'
        phase.value = 'input'
      } else if (typeof data.progress === 'number') {
        progress.value = Math.max(progress.value, data.progress)
      }
    } catch {
      failCount++
      if (failCount >= 5) {
        clearInterval(pollTimer!)
        clearInterval(fakeTimer)
        errorMsg.value = '网络连接中断，请刷新页面后重试'
        phase.value = 'input'
      }
    }
  }, 2000)
}

function reset() {
  if (pollTimer) clearInterval(pollTimer)
  phase.value    = 'input'
  result.value   = null
  progress.value = 0
  errorMsg.value = ''
}

onUnmounted(() => { if (pollTimer) clearInterval(pollTimer) })
</script>

<template>
  <div class="vg-page">
    <!-- 中央卡片容器 -->
    <div class="vg-card">

      <!-- ── Header ─────────────────────────────────────────── -->
      <div class="vg-header">
        <div class="vg-header-left">
          <div class="vg-icon-badge">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <rect x="2" y="4" width="14" height="14" rx="2" stroke="currentColor" stroke-width="2"/>
              <path d="M16 8l4 4-4 4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <div>
            <h2 class="vg-title">AI视频生成</h2>
            <p class="vg-subtitle">AI 智能生成 &middot; 教学演示视频</p>
          </div>
        </div>
        <button class="vg-close-btn" @click="router.back()">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
            <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>

      <!-- ── Scrollable Body ────────────────────────────────── -->
      <div class="vg-body">

        <!-- ===== Phase: input ============================= -->
        <template v-if="phase === 'input'">

          <!-- Section 1: 自由输入 -->
          <div class="vg-section">
            <div class="vg-textarea-wrap">
              <textarea
                v-model="freeText"
                class="vg-textarea"
                :maxlength="MAX_LEN"
                placeholder="例如：生成一个关于「TCP三次握手」的基础教学视频，要求包含报文交互动画和 Wireshark 抓包演示..."
              />
              <span class="vg-count">{{ charCount }}/{{ MAX_LEN }}</span>
            </div>
            <div class="vg-btn-row">
              <button
                class="vg-gen-btn"
                :disabled="!canFreeGen"
                @click="startGenerate('free')"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>
                开始生成
              </button>
            </div>
            <p v-if="errorMsg" class="vg-error">{{ errorMsg }}</p>
          </div>

          <!-- 或 分隔线 -->
          <div class="vg-divider">
            <span class="vg-divider-line"/>
            <span class="vg-divider-text">或</span>
            <span class="vg-divider-line"/>
          </div>

          <!-- Section 2: 基于课题生成 -->
          <div class="vg-topic-card">
            <div class="vg-topic-header">
              <div class="vg-topic-icon">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
                  <rect x="3" y="5" width="12" height="12" rx="2" stroke="#e53e3e" stroke-width="1.5"/>
                  <path d="M15 9l4 3-4 3" stroke="#e53e3e" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </div>
              <div>
                <h3 class="vg-topic-title">基于课题生成</h3>
                <p class="vg-topic-desc">选择经典课题，由 AI 快速生成专业的教学演示视频。</p>
              </div>
            </div>

            <div class="vg-chips">
              <button
                v-for="t in TOPICS"
                :key="t"
                class="vg-chip"
                :class="{ active: selectedTopic === t }"
                @click="selectTopic(t)"
              >{{ t }}</button>
            </div>

            <div class="vg-btn-row">
              <button
                class="vg-gen-btn"
                :disabled="!canTopicGen"
                @click="startGenerate('topic')"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>
                开始生成
              </button>
            </div>
          </div>

        </template>

        <!-- ===== Phase: generating ======================== -->
        <template v-else-if="phase === 'generating'">
          <div class="vg-generating">
            <div class="vg-spin-ring">
              <svg class="vg-spinner" width="56" height="56" viewBox="0 0 56 56">
                <circle cx="28" cy="28" r="24" fill="none" stroke="#f0f0f0" stroke-width="4"/>
                <circle cx="28" cy="28" r="24" fill="none" stroke="#e53e3e" stroke-width="4"
                  stroke-linecap="round" stroke-dasharray="150" stroke-dashoffset="60"/>
              </svg>
              <svg class="vg-gen-icon" width="24" height="24" viewBox="0 0 24 24" fill="#e53e3e">
                <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
              </svg>
            </div>
            <p class="vg-gen-title">视频生成中</p>
            <p class="vg-gen-sub">AI 正在编排教学脚本并渲染视频，预计 30-60 秒...</p>

            <!-- 进度条 -->
            <div class="vg-progress-wrap">
              <div class="vg-progress-bar">
                <div class="vg-progress-fill" :style="{ width: progress + '%' }"/>
              </div>
              <span class="vg-progress-text">{{ progress }}%</span>
            </div>

            <!-- 步骤说明 -->
            <div class="vg-steps">
              <div class="vg-step" :class="{ done: progress >= 20 }">
                <span class="vg-step-dot"/>知识检索与脚本生成
              </div>
              <div class="vg-step" :class="{ done: progress >= 50 }">
                <span class="vg-step-dot"/>动画帧渲染与合成
              </div>
              <div class="vg-step" :class="{ done: progress >= 80 }">
                <span class="vg-step-dot"/>语音配音与字幕添加
              </div>
              <div class="vg-step" :class="{ done: progress >= 95 }">
                <span class="vg-step-dot"/>视频封装与质量检验
              </div>
            </div>

            <p v-if="isMockMode" class="vg-mock-tip">演示模式：使用示例视频展示完整功能流程</p>
          </div>
        </template>

        <!-- ===== Phase: result ============================ -->
        <template v-else-if="phase === 'result' && result">

          <!-- 完成标题行 -->
          <div class="vg-result-bar">
            <div class="vg-result-done">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="10" fill="#38a169"/>
                <path d="M7 12.5l3.5 3.5 6.5-7" stroke="white" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              <span>视频制作完成</span>
            </div>
            <div class="vg-ai-badge">
              <span class="vg-ai-dot">🤖</span> AI合成
            </div>
          </div>

          <!-- 视频播放器 -->
          <div class="vg-player-wrap">
            <video
              class="vg-player"
              controls
              :src="result.video_url"
              preload="metadata"
            >
              您的浏览器不支持视频播放
            </video>
          </div>

          <!-- 视频信息卡 -->
          <div class="vg-info-card">
            <div class="vg-info-bar"/>
            <div class="vg-info-body">
              <h4 class="vg-info-title">{{ result.title }}</h4>
              <p class="vg-info-desc">{{ result.description }}</p>
              <p class="vg-info-date">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>
                </svg>
                生成日期：{{ result.generated_at }}
              </p>
            </div>
          </div>

          <!-- 操作按钮 -->
          <div class="vg-action-row">
            <a
              v-if="result.video_url"
              :href="result.video_url"
              target="_blank"
              class="vg-action-btn primary"
            >
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
              下载视频
            </a>
            <button class="vg-action-btn secondary" @click="reset">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"/><path d="M20.5 15a9 9 0 11-2.8-6.4L23 10"/></svg>
              重新生成
            </button>
          </div>

        </template>

      </div><!-- /vg-body -->
    </div><!-- /vg-card -->
  </div>
</template>

<style scoped>
/* ── 页面底板 ─────────────────────────────────────────── */
.vg-page {
  min-height: 100vh;
  background: #f2f3f5;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: 32px 16px 60px;
}

/* ── 主卡片 ──────────────────────────────────────────── */
.vg-card {
  width: 100%;
  max-width: 580px;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 4px 32px rgba(0,0,0,0.10);
  overflow: hidden;
  border: 1px solid #e8e8e8;
  /* 左侧装饰线，对应截图 */
  border-left: 3px solid #c9a96e;
}

/* ── Header ──────────────────────────────────────────── */
.vg-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 20px 14px;
  border-bottom: 1px solid #f0ece4;
  background: #faf8f5;
}
.vg-header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}
.vg-icon-badge {
  width: 38px; height: 38px;
  background: #2d2d2d;
  border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  color: #fff;
}
.vg-title {
  font-size: 16px; font-weight: 700; color: #1a1a1a; margin: 0;
}
.vg-subtitle {
  font-size: 11px; color: #888; margin: 2px 0 0;
}
.vg-close-btn {
  width: 30px; height: 30px;
  background: transparent;
  border: none; cursor: pointer;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  color: #999;
  transition: background 0.15s, color 0.15s;
}
.vg-close-btn:hover { background: #f5f5f5; color: #333; }

/* ── Body 滚动区 ─────────────────────────────────────── */
.vg-body {
  padding: 20px;
  max-height: calc(100vh - 180px);
  overflow-y: auto;
}

/* ── Section 1: 文本输入 ─────────────────────────────── */
.vg-section { margin-bottom: 4px; }
.vg-textarea-wrap {
  position: relative;
  background: #fafafa;
  border: 1px solid #e8e8e8;
  border-radius: 10px;
  padding: 12px 14px 28px;
}
.vg-textarea {
  width: 100%;
  min-height: 90px;
  background: transparent;
  border: none;
  outline: none;
  resize: vertical;
  font-size: 13.5px;
  color: #333;
  line-height: 1.7;
  font-family: inherit;
}
.vg-textarea::placeholder { color: #bbb; }
.vg-count {
  position: absolute;
  right: 12px; bottom: 8px;
  font-size: 11px; color: #bbb;
}

/* ── 生成按钮 ─────────────────────────────────────────── */
.vg-btn-row {
  display: flex;
  justify-content: center;
  margin-top: 14px;
}
.vg-gen-btn {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 10px 32px;
  background: #1a1a1a;
  color: #fff;
  border: none;
  border-radius: 24px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s, transform 0.1s;
}
.vg-gen-btn:hover:not(:disabled) { background: #333; transform: translateY(-1px); }
.vg-gen-btn:active:not(:disabled) { transform: translateY(0); }
.vg-gen-btn:disabled { opacity: 0.4; cursor: not-allowed; }

.vg-error {
  text-align: center;
  color: #e53e3e;
  font-size: 12px;
  margin-top: 8px;
}

/* ── 分隔线 ──────────────────────────────────────────── */
.vg-divider {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 20px 0;
}
.vg-divider-line {
  flex: 1;
  height: 1px;
  background: #ececec;
}
.vg-divider-text {
  font-size: 12px;
  color: #bbb;
  flex-shrink: 0;
}

/* ── Section 2: 基于课题 ─────────────────────────────── */
.vg-topic-card {
  border: 1px solid #e8e8e8;
  border-radius: 12px;
  padding: 18px;
  background: #fff;
}
.vg-topic-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 16px;
}
.vg-topic-icon {
  flex-shrink: 0;
  width: 44px; height: 44px;
  display: flex; align-items: center; justify-content: center;
  background: #fff5f5;
  border-radius: 10px;
}
.vg-topic-title {
  font-size: 15px; font-weight: 700; color: #1a1a1a;
  margin: 2px 0 4px;
}
.vg-topic-desc {
  font-size: 12px; color: #888; margin: 0;
}
.vg-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;
}
.vg-chip {
  padding: 5px 13px;
  border: 1px solid #ddd;
  border-radius: 20px;
  font-size: 12.5px;
  color: #555;
  background: #fafafa;
  cursor: pointer;
  transition: all 0.15s;
  display: flex; align-items: center; gap: 4px;
}
.vg-chip::before {
  content: '';
  width: 6px; height: 6px;
  border-radius: 50%;
  background: #ddd;
  display: inline-block;
  transition: background 0.15s;
}
.vg-chip:hover { border-color: #e53e3e; color: #e53e3e; }
.vg-chip.active {
  border-color: #e53e3e;
  background: #fff5f5;
  color: #e53e3e;
  font-weight: 600;
}
.vg-chip.active::before { background: #e53e3e; }

/* ── Generating 阶段 ─────────────────────────────────── */
.vg-generating {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 24px 16px;
  gap: 12px;
  text-align: center;
}
.vg-spin-ring {
  position: relative;
  width: 56px; height: 56px;
  display: flex; align-items: center; justify-content: center;
}
.vg-spinner {
  position: absolute;
  inset: 0;
  animation: spin 1.4s linear infinite;
}
.vg-gen-icon { position: relative; z-index: 1; }
@keyframes spin { to { transform: rotate(360deg); } }

.vg-gen-title  { font-size: 17px; font-weight: 700; color: #1a1a1a; margin: 4px 0 0; }
.vg-gen-sub    { font-size: 12.5px; color: #888; margin: 0; }

.vg-progress-wrap {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 10px;
}
.vg-progress-bar {
  flex: 1;
  height: 6px;
  background: #f0f0f0;
  border-radius: 3px;
  overflow: hidden;
}
.vg-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #e53e3e, #fc8181);
  border-radius: 3px;
  transition: width 0.4s ease;
}
.vg-progress-text { font-size: 12px; color: #888; min-width: 34px; text-align: right; }

.vg-steps {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 8px;
  text-align: left;
  margin-top: 4px;
}
.vg-step {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12.5px;
  color: #aaa;
  transition: color 0.3s;
}
.vg-step.done { color: #38a169; }
.vg-step-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  background: #ddd;
  flex-shrink: 0;
  transition: background 0.3s;
}
.vg-step.done .vg-step-dot { background: #38a169; }

.vg-mock-tip {
  font-size: 11px;
  color: #999;
  background: #fafafa;
  border: 1px dashed #ddd;
  border-radius: 6px;
  padding: 6px 12px;
  margin-top: 4px;
}

/* ── Result 阶段 ─────────────────────────────────────── */
.vg-result-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}
.vg-result-done {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 15px;
  font-weight: 700;
  color: #1a1a1a;
}
.vg-ai-badge {
  display: flex;
  align-items: center;
  gap: 4px;
  background: #e53e3e;
  color: #fff;
  font-size: 12px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 20px;
}

.vg-player-wrap {
  background: #000;
  border-radius: 10px;
  overflow: hidden;
  margin-bottom: 14px;
  aspect-ratio: 16/9;
}
.vg-player {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: contain;
}

.vg-info-card {
  display: flex;
  gap: 12px;
  background: #fafafa;
  border: 1px solid #efefef;
  border-radius: 10px;
  padding: 14px;
  margin-bottom: 16px;
}
.vg-info-bar {
  width: 4px;
  background: #e53e3e;
  border-radius: 2px;
  flex-shrink: 0;
}
.vg-info-body { flex: 1; }
.vg-info-title {
  font-size: 14px;
  font-weight: 700;
  color: #1a1a1a;
  margin: 0 0 6px;
}
.vg-info-desc {
  font-size: 12.5px;
  color: #666;
  line-height: 1.7;
  margin: 0 0 8px;
}
.vg-info-date {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11.5px;
  color: #999;
  margin: 0;
}

.vg-action-row {
  display: flex;
  gap: 10px;
  justify-content: center;
}
.vg-action-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 9px 22px;
  border-radius: 22px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: all 0.15s;
  text-decoration: none;
}
.vg-action-btn.primary {
  background: #e53e3e;
  color: #fff;
}
.vg-action-btn.primary:hover { background: #c53030; }
.vg-action-btn.secondary {
  background: #f5f5f5;
  color: #555;
  border: 1px solid #e0e0e0;
}
.vg-action-btn.secondary:hover { background: #eee; }
</style>
