<template>
  <div class="video-card">
    <!-- ── 卡片头部 ── -->
    <div class="card-header">
      <span class="type-badge">AI教学视频</span>
      <h4 class="card-title">{{ resource.title }}</h4>
      <TrustBadge :level="3" :sources="['AI结构化生成', '课程知识图谱']" :audited="true" />
    </div>

    <!-- ── 视频封面区 ── -->
    <div class="video-cover" @click="showChapters = !showChapters">
      <!-- 网络主题背景装饰 -->
      <svg class="cover-bg-svg" viewBox="0 0 400 160" preserveAspectRatio="xMidYMid slice">
        <defs>
          <linearGradient id="coverGrad" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stop-color="#0f172a"/>
            <stop offset="100%" stop-color="#1e3a5f"/>
          </linearGradient>
        </defs>
        <rect width="400" height="160" fill="url(#coverGrad)"/>
        <!-- 节点线条装饰 -->
        <circle cx="60" cy="40" r="4" fill="#3b82f6" opacity="0.6"/>
        <circle cx="180" cy="80" r="6" fill="#6366f1" opacity="0.7"/>
        <circle cx="320" cy="50" r="4" fill="#3b82f6" opacity="0.5"/>
        <circle cx="360" cy="130" r="5" fill="#8b5cf6" opacity="0.6"/>
        <circle cx="80" cy="130" r="3" fill="#22d3ee" opacity="0.5"/>
        <line x1="60" y1="40" x2="180" y2="80" stroke="#3b82f6" stroke-width="1" opacity="0.3"/>
        <line x1="180" y1="80" x2="320" y2="50" stroke="#6366f1" stroke-width="1" opacity="0.3"/>
        <line x1="320" y1="50" x2="360" y2="130" stroke="#8b5cf6" stroke-width="1" opacity="0.3"/>
        <line x1="80" y1="130" x2="180" y2="80" stroke="#22d3ee" stroke-width="1" opacity="0.3"/>
      </svg>

      <!-- 主播放按钮 -->
      <div class="play-btn-wrap">
        <div class="play-btn">
          <svg viewBox="0 0 24 24" fill="currentColor" class="play-icon">
            <path d="M8 5v14l11-7z"/>
          </svg>
        </div>
      </div>

      <!-- 时长徽章 -->
      <div class="duration-badge">{{ formattedDuration }}</div>

      <!-- 视频标题覆盖层 -->
      <div class="cover-overlay">
        <p class="cover-title">{{ resource.title }}</p>
      </div>
    </div>

    <!-- ── 视频元信息行 ── -->
    <div class="video-meta">
      <span class="meta-item">
        <svg class="meta-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
        </svg>
        {{ formattedDuration }}
      </span>
      <span class="meta-item">
        <span class="difficulty-stars">{{ difficultyStars }}</span>
        难度
      </span>
      <span class="meta-item">
        <svg class="meta-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
        </svg>
        {{ audienceLabel }}
      </span>
      <span class="meta-item scene-count">
        {{ parsedScenes.length }} 章节
      </span>
    </div>

    <!-- ── 章节目录（可折叠）── -->
    <div v-if="showChapters && parsedScenes.length" class="chapters-section">
      <div class="chapters-title">章节目录</div>
      <div class="chapters-list">
        <div v-for="(scene, i) in parsedScenes" :key="i" class="chapter-item">
          <span class="chapter-time">{{ formatTime(cumulativeTime(i)) }}</span>
          <span class="chapter-divider">│</span>
          <span class="chapter-desc">{{ scene.scene_description }}</span>
          <span class="chapter-dur">{{ scene.duration_seconds }}s</span>
        </div>
      </div>

      <!-- AI学习助手快速入口 -->
      <div class="quick-qa-section">
        <div class="qa-title">AI学习助手</div>
        <div class="qa-buttons">
          <button
            v-for="q in quickQuestions"
            :key="q"
            class="qa-btn"
            @click="goToChat(q)"
          >
            {{ q }}
          </button>
        </div>
      </div>
    </div>

    <!-- ── 操作栏 ── -->
    <button class="toggle-btn" @click="showChapters = !showChapters">
      {{ showChapters ? '收起章节 ▲' : '查看章节目录 ▼' }}
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import type { LearningResource } from '../../types'
import TrustBadge from './TrustBadge.vue'

const props = defineProps<{ resource: LearningResource }>()
const router = useRouter()
const showChapters = ref(false)

interface Scene {
  scene_number: number
  duration_seconds: number
  scene_description: string
  narration: string
  visual_notes?: string
}

const parsedScenes = computed<Scene[]>(() => {
  try {
    const content = props.resource.content || ''
    const jsonMatch = content.match(/```json\s*\n([\s\S]*?)```/)
    if (jsonMatch) {
      const data = JSON.parse(jsonMatch[1])
      return data.scenes || []
    }
    if (content.trim().startsWith('{')) {
      const data = JSON.parse(content)
      return data.scenes || []
    }
  } catch { /* ignore */ }
  return []
})

const totalSeconds = computed(() =>
  parsedScenes.value.reduce((s, sc) => s + (sc.duration_seconds || 0), 0)
)

const formattedDuration = computed(() => {
  const sec = totalSeconds.value
  if (!sec) return '短视频'
  const m = Math.floor(sec / 60)
  const s = sec % 60
  return m > 0 ? `${m}分${s > 0 ? s + '秒' : ''}` : `${sec}秒`
})

const difficultyStars = computed(() => {
  const d = Math.max(1, Math.min(5, Number(props.resource.metadata?.difficulty ?? props.resource.difficulty ?? 2)))
  return '★'.repeat(d) + '☆'.repeat(5 - d)
})

const audienceLabel = computed(() => {
  const d = Number(props.resource.metadata?.difficulty ?? props.resource.difficulty ?? 2)
  if (d <= 2) return '初学者'
  if (d <= 3) return '中级'
  return '进阶'
})

// 计算累计时间（用于时间轴）
function cumulativeTime(idx: number): number {
  return parsedScenes.value.slice(0, idx).reduce((s, sc) => s + (sc.duration_seconds || 0), 0)
}

function formatTime(sec: number): string {
  const m = Math.floor(sec / 60).toString().padStart(2, '0')
  const s = (sec % 60).toString().padStart(2, '0')
  return `${m}:${s}`
}

// 从 scene_description 生成快速提问
const quickQuestions = computed(() => {
  const questions: string[] = []
  parsedScenes.value.slice(0, 3).forEach(sc => {
    const desc = sc.scene_description ?? ''
    if (desc) questions.push(`${desc}是什么意思？`)
  })
  if (!questions.length && props.resource.knowledge_point) {
    questions.push(
      `${props.resource.knowledge_point}的核心原理是什么？`,
      `能举例说明${props.resource.knowledge_point}吗？`,
    )
  }
  return questions.slice(0, 3)
})

function goToChat(question: string) {
  // 通过 localStorage 传递预填问题，ChatView 在 onMounted 时读取
  localStorage.setItem('prefill_question', question)
  router.push('/chat')
}
</script>

<style scoped>
.video-card {
  border: 1px solid rgba(22,119,255,0.15);
  border-radius: 14px;
  background: linear-gradient(135deg, white 0%, #f0f6ff 100%);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  transition: all 0.25s;
}
.video-card:hover {
  box-shadow: 0 6px 24px rgba(22,119,255,0.1);
  transform: translateY(-2px);
  border-color: rgba(22,119,255,0.3);
}

/* ── 头部 ── */
.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px 8px;
  border-bottom: 1px solid rgba(22,119,255,0.1);
  background: linear-gradient(90deg, rgba(22,119,255,0.04), transparent);
}

.type-badge {
  flex-shrink: 0;
  font-size: 11px; font-weight: 700;
  padding: 2px 9px; border-radius: 999px;
  background: linear-gradient(135deg, #1677FF, #722ED1); color: white;
  white-space: nowrap;
}
.card-title {
  flex: 1; font-size: 13px; font-weight: 700; color: #1e293b;
  margin: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}

/* ── 视频封面 ── */
.video-cover {
  position: relative;
  width: 100%;
  height: 140px;
  overflow: hidden;
  cursor: pointer;
  background: #0f172a;
}

.cover-bg-svg {
  position: absolute; inset: 0;
  width: 100%; height: 100%;
}

.play-btn-wrap {
  position: absolute; inset: 0;
  display: flex; align-items: center; justify-content: center;
  z-index: 2;
}
.play-btn {
  width: 52px; height: 52px;
  border-radius: 50%;
  background: rgba(255,255,255,0.15);
  border: 2px solid rgba(255,255,255,0.5);
  backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center;
  transition: all 0.2s;
  color: white;
}
.video-cover:hover .play-btn {
  background: rgba(79,70,229,0.7);
  border-color: white;
  transform: scale(1.1);
}
.play-icon { width: 22px; height: 22px; margin-left: 3px; }

.duration-badge {
  position: absolute; top: 8px; right: 10px;
  font-size: 11px; font-weight: 700; color: white;
  background: rgba(0,0,0,0.5);
  padding: 2px 8px; border-radius: 4px;
  z-index: 3;
}

.cover-overlay {
  position: absolute; bottom: 0; left: 0; right: 0;
  padding: 20px 12px 10px;
  background: linear-gradient(to top, rgba(0,0,0,0.6), transparent);
  z-index: 2;
}
.cover-title {
  font-size: 13px; font-weight: 700; color: white;
  margin: 0; line-height: 1.4;
  text-shadow: 0 1px 4px rgba(0,0,0,0.5);
}

/* ── 元信息 ── */
.video-meta {
  display: flex; align-items: center; gap: 12px; flex-wrap: wrap;
  padding: 8px 14px;
  border-bottom: 1px solid #f1f5f9;
  font-size: 11px; color: #64748b;
}
.meta-item {
  display: flex; align-items: center; gap: 4px;
}
.meta-icon { width: 12px; height: 12px; }
.difficulty-stars { color: #f59e0b; font-size: 11px; letter-spacing: -1px; }
.scene-count { margin-left: auto; font-weight: 600; color: #1677FF; }

/* ── 章节 ── */
.chapters-section {
  padding: 12px 14px;
  display: flex; flex-direction: column; gap: 10px;
  border-top: 1px solid #f1f5f9;
}

.chapters-title {
  font-size: 11px; font-weight: 700; color: #475569;
  text-transform: uppercase; letter-spacing: 0.5px;
}

.chapters-list { display: flex; flex-direction: column; gap: 2px; }

.chapter-item {
  display: flex; align-items: center; gap: 8px;
  padding: 5px 8px; border-radius: 6px;
  font-size: 12px; color: #374151;
  transition: background 0.15s;
}
.chapter-item:hover { background: #f8fafc; }

.chapter-time {
  flex-shrink: 0; font-family: monospace;
  font-size: 11px; font-weight: 700; color: #1677FF;
  width: 36px;
}
.chapter-divider { color: #e2e8f0; }
.chapter-desc { flex: 1; font-size: 12px; color: #374151; }
.chapter-dur {
  flex-shrink: 0; font-size: 10px; color: #94a3b8;
  font-family: monospace;
}

/* ── AI快问 ── */
.quick-qa-section {
  padding: 10px 12px;
  background: #f8f9ff; border: 1px solid #e0e7ff;
  border-radius: 8px;
  display: flex; flex-direction: column; gap: 8px;
}

.qa-title { font-size: 11px; font-weight: 700; color: #1677FF; display: flex; align-items: center; gap: 4px; }
.qa-title::before { content: '💬'; }

.qa-buttons { display: flex; flex-direction: column; gap: 5px; }

.qa-btn {
  text-align: left;
  font-size: 12px; color: #4f46e5;
  padding: 6px 10px; border-radius: 6px;
  background: white; border: 1px solid #e0e7ff;
  cursor: pointer; transition: all 0.15s;
  line-height: 1.4;
}
.qa-btn:hover {
  background: #eff2ff; border-color: #a5b4fc;
  color: #3730a3;
}

/* ── 操作栏 ── */
.toggle-btn {
  padding: 9px 16px;
  background: transparent; border: none; border-top: 1px solid rgba(22,119,255,0.1);
  font-size: 12px; font-weight: 600; color: #1677FF;
  cursor: pointer; transition: all 0.18s; text-align: center;
}
.toggle-btn:hover { background: #E8F3FF; color: #0958D9; }
</style>
