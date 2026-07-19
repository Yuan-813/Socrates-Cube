<template>
  <div class="mindmap-card">
    <!-- 卡片头部 -->
    <div class="card-header">
      <span class="card-icon">🗺️</span>
      <h4 class="card-title">{{ resource.title || '思维导图' }}</h4>
      <span class="type-badge">思维导图</span>
    </div>

    <!-- 卡片主体 -->
    <div class="card-body">
      <!-- 渲染中 -->
      <div v-if="rendering" class="state-center">
        <svg class="spin-icon" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
        </svg>
        <span>渲染中...</span>
      </div>

      <!-- 渲染成功 -->
      <div v-show="!rendering && !renderFailed" ref="svgWrapRef" class="svg-wrap" />

      <!-- 渲染失败：显示格式化源码 -->
      <div v-if="!rendering && renderFailed" class="fallback-area">
        <div class="fallback-tip">
          <svg class="w-3.5 h-3.5 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
          图形渲染失败，已显示原始代码
        </div>
        <pre class="source-code">{{ mermaidCode }}</pre>
      </div>

      <!-- 内容为空 -->
      <div v-if="!rendering && !renderFailed && !mermaidCode" class="state-center empty">
        暂无思维导图内容
      </div>
    </div>

    <!-- 卡片底部 -->
    <div class="card-footer">
      <span>知识点：{{ resource.knowledge_point }}</span>
      <span v-if="resource.metadata?.difficulty">难度：{{ resource.metadata.difficulty }}</span>
      <button v-if="!rendering && mermaidCode" class="toggle-code-btn" @click="showCode = !showCode">
        {{ showCode ? '隐藏源码' : '查看源码' }}
      </button>
    </div>

    <!-- 可折叠源码区 -->
    <div v-if="showCode" class="source-panel">
      <pre class="source-code">{{ mermaidCode }}</pre>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, watch, nextTick, getCurrentInstance } from 'vue'
import type { LearningResource } from '../../types'

const props = defineProps<{ resource: LearningResource }>()

const svgWrapRef = ref<HTMLElement | null>(null)
const rendering = ref(false)
const renderFailed = ref(false)
const showCode = ref(false)

// 为每个组件实例生成唯一渲染 ID，避免多卡片冲突
const uid = getCurrentInstance()?.uid ?? Math.floor(Math.random() * 1e8)
const renderId = `mmd-${uid}`

// 提取 mermaid 代码（支持代码块包裹或裸代码；严格校验起始关键字）
const mermaidCode = computed<string>(() => {
  const raw = (props.resource.content ?? '').trim()
  if (!raw) return ''

  // 优先匹配 ```mermaid ... ``` 代码块
  const blockMatch = raw.match(/```mermaid\s*\n([\s\S]*?)```/)
  if (blockMatch) return blockMatch[1].trim()

  // 匹配常见 mermaid 起始关键字（严格：只有以关键字开头才认为是 Mermaid）
  const keywords = ['graph ', 'flowchart ', 'sequenceDiagram', 'classDiagram',
                    'stateDiagram', 'gantt', 'pie ', 'mindmap', 'erDiagram']
  const firstLine = raw.split('\n')[0].trimStart()
  if (keywords.some(k => firstLine.startsWith(k))) return raw

  // 其余内容不尝试渲染，避免 JSON/文本触发 Mermaid 语法错误
  return ''
})

// ── 渲染核心 ───────────────────────────────────────────────
let mermaidInstance: typeof import('mermaid').default | null = null

async function renderMermaid() {
  if (!mermaidCode.value) return

  rendering.value = true
  renderFailed.value = false

  // 等待 DOM 就绪
  await nextTick()

  if (!svgWrapRef.value) {
    rendering.value = false
    return
  }

  try {
    // 懒加载 mermaid（仅第一次）
    if (!mermaidInstance) {
      const mod = await import('mermaid')
      mermaidInstance = mod.default
      mermaidInstance.initialize({
        startOnLoad: false,
        theme: 'default',
        securityLevel: 'loose',
        flowchart: { useMaxWidth: true, htmlLabels: true, curve: 'basis' },
        mindmap: { useMaxWidth: true },
      })
    }

    // 清空上次渲染残余
    svgWrapRef.value.innerHTML = ''

    const { svg } = await mermaidInstance.render(renderId, mermaidCode.value)

    // 检测 Mermaid v11 将错误渲染为 SVG 而非抛异常的情况
    if (svg.includes('Syntax error') || svg.includes('mermaid version')) {
      throw new Error('Mermaid syntax error in rendered SVG')
    }

    svgWrapRef.value.innerHTML = svg

    // ★ 关键修复：让 SVG 响应式缩放到容器宽度
    const svgEl = svgWrapRef.value.querySelector('svg')
    if (svgEl) {
      // 保存原始 viewBox；若无则用 width/height 构建
      if (!svgEl.getAttribute('viewBox')) {
        const w = svgEl.getAttribute('width')
        const h = svgEl.getAttribute('height')
        if (w && h) svgEl.setAttribute('viewBox', `0 0 ${parseFloat(w)} ${parseFloat(h)}`)
      }
      // 覆盖固定宽高，改为 100% 自适应
      svgEl.setAttribute('width', '100%')
      svgEl.removeAttribute('height')
      svgEl.style.maxWidth = '100%'
      svgEl.style.display = 'block'
    }

    renderFailed.value = false
  } catch (err) {
    console.warn('[MindmapCard] render failed:', err)
    svgWrapRef.value.innerHTML = ''
    renderFailed.value = true
  } finally {
    rendering.value = false
  }
}

onMounted(renderMermaid)
watch(() => props.resource.content, renderMermaid)
</script>

<style scoped>
.mindmap-card {
  border: 1px solid rgba(114,46,209,0.15);
  border-radius: 14px;
  background: linear-gradient(135deg, white 0%, #faf5ff 100%);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  transition: all 0.25s;
}
.mindmap-card:hover {
  box-shadow: 0 6px 24px rgba(114,46,209,0.1);
  transform: translateY(-2px);
  border-color: rgba(114,46,209,0.3);
}
.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 14px;
  border-bottom: 1px solid rgba(114,46,209,0.1);
  background: linear-gradient(90deg, rgba(114,46,209,0.04), transparent);
}
.card-icon { font-size: 17px; }
.card-title { font-size: 13px; font-weight: 700; color: #722ED1; flex: 1; min-width: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.type-badge { font-size: 11px; font-weight: 600; padding: 2px 9px; border-radius: 999px; background: rgba(114,46,209,0.1); color: #722ED1; border: 1px solid rgba(114,46,209,0.2); white-space: nowrap; }

.card-body {
  padding: 12px 14px;
  flex: 1;
  min-height: 160px;
  display: flex;
  flex-direction: column;
}

/* SVG 容器：允许内容撑高，宽度 100% */
.svg-wrap {
  width: 100%;
  overflow-x: auto;
  overflow-y: hidden;
  line-height: 0; /* 消除底部间隙 */
}
/* 强制 svg 宽度 100%，确保覆盖 mermaid 注入的内联样式 */
.svg-wrap :deep(svg) {
  max-width: 100% !important;
  width: 100% !important;
  height: auto !important;
  display: block;
}

.state-center {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  flex: 1;
  font-size: 12px;
  color: #94a3b8;
  min-height: 100px;
}
.state-center.empty { flex-direction: column; }
.spin-icon { width: 18px; height: 18px; animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.fallback-area { width: 100%; }
.fallback-tip {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: #92400e;
  background: #fef3c7;
  padding: 4px 8px;
  border-radius: 4px;
  margin-bottom: 6px;
}
.source-code {
  font-size: 11px;
  color: #475569;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  padding: 8px 10px;
  border-radius: 6px;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 200px;
  overflow-y: auto;
  margin: 0;
  text-align: left;
}

.card-footer {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 14px;
  border-top: 1px solid rgba(114,46,209,0.08);
  font-size: 11px;
  color: #64748b;
  flex-wrap: wrap;
}
.toggle-code-btn {
  margin-left: auto;
  font-size: 10px;
  color: #722ED1;
  background: transparent;
  border: 1px solid rgba(114,46,209,0.3);
  border-radius: 4px;
  padding: 2px 8px;
  cursor: pointer;
  transition: all 0.15s;
}
.toggle-code-btn:hover { background: rgba(114,46,209,0.1); }

.source-panel {
  padding: 0 14px 12px;
}
</style>
