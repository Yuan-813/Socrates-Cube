<template>
  <div class="resource-card info-card">
    <div class="card-header">
      <span class="card-icon">🗂️</span>
      <h4 class="card-title">{{ resource.title || '信息图' }}</h4>
      <el-tag size="small" type="info">信息图</el-tag>
    </div>

    <div class="card-body" v-if="parsed">
      <!-- 摘要 -->
      <div v-if="parsed.summary" class="info-summary">
        {{ parsed.summary }}
      </div>

      <!-- 关键数字 -->
      <div v-if="parsed.key_numbers?.length" class="info-section">
        <div class="info-section-label">📊 关键数字</div>
        <div class="key-numbers">
          <div v-for="(kn, i) in parsed.key_numbers" :key="i" class="kn-item">
            <div class="kn-value">{{ kn.value }}<span class="kn-unit">{{ kn.unit }}</span></div>
            <div class="kn-desc">{{ kn.desc }}</div>
          </div>
        </div>
      </div>

      <!-- 对比表 -->
      <div v-if="parsed.comparison?.rows?.length" class="info-section">
        <div class="info-section-label">⚖️ 对比分析</div>
        <table class="cmp-table">
          <thead>
            <tr>
              <th v-for="h in parsed.comparison.header" :key="h">{{ h }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, i) in parsed.comparison.rows" :key="i">
              <td v-for="(cell, j) in row" :key="j">{{ cell }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 时间线流程 -->
      <div v-if="parsed.timeline?.length" class="info-section">
        <div class="info-section-label">🔄 关键流程</div>
        <div class="timeline">
          <div v-for="(item, i) in parsed.timeline" :key="i" class="tl-item">
            <div class="tl-num">{{ i + 1 }}</div>
            <div class="tl-content">
              <div class="tl-step">{{ item.step }}</div>
              <div class="tl-desc">{{ item.desc }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 标签 -->
      <div v-if="parsed.tags?.length" class="info-tags">
        <el-tag v-for="tag in parsed.tags" :key="tag" size="small" effect="plain" type="info" class="info-tag">
          {{ tag }}
        </el-tag>
      </div>
    </div>

    <!-- 原始内容（解析失败） -->
    <div class="card-body" v-else>
      <!-- Mermaid 代码块渲染 -->
      <div v-if="mermaidCode" class="mermaid-container">
        <div ref="mermaidRef" class="mermaid-diagram"></div>
      </div>
      <pre v-else class="raw-content">{{ resource.content }}</pre>
    </div>

    <div class="card-footer">
      <span class="meta-item">知识点：{{ resource.knowledge_point }}</span>
      <span v-if="resource.metadata?.difficulty" class="meta-item">
        难度：{{ resource.metadata.difficulty }}
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch, nextTick, onMounted } from 'vue'
import type { LearningResource } from '../../types'

const props = defineProps<{ resource: LearningResource }>()

const mermaidRef = ref<HTMLElement | null>(null)

// 提取 Mermaid 代码块
const mermaidCode = computed<string | null>(() => {
  const c = props.resource.content || ''
  const m = c.match(/```(?:mermaid)\n([\s\S]*?)```/)
  return m ? m[1].trim() : null
})

async function renderMermaid() {
  if (!mermaidCode.value || !mermaidRef.value) return
  try {
    const mermaid = (await import('mermaid')).default
    mermaid.initialize({ startOnLoad: false, theme: 'default', securityLevel: 'loose' })
    const id = `mermaid-${Math.random().toString(36).slice(2)}`
    const { svg } = await mermaid.render(id, mermaidCode.value)
    // 检测 Mermaid v11 将错误渲染为 SVG 而非抛异常的情况
    if (svg.includes('Syntax error') || svg.includes('mermaid version')) {
      throw new Error('Mermaid syntax error')
    }
    if (mermaidRef.value) mermaidRef.value.innerHTML = svg
  } catch (err) {
    if (mermaidRef.value) mermaidRef.value.textContent = `图表渲染失败`
  }
}

watch(mermaidCode, () => nextTick(renderMermaid))
onMounted(() => nextTick(renderMermaid))

interface InfoData {
  title?: string
  summary?: string
  key_numbers?: Array<{ value: string | number; unit?: string; desc: string }>
  comparison?: { header: string[]; rows: string[][] }
  timeline?: Array<{ step: string; desc: string }>
  tags?: string[]
}

const parsed = computed<InfoData | null>(() => {
  try {
    const c = props.resource.content || ''
    const jsonMatch = c.match(/```json\n([\s\S]*?)```/)
    const jsonStr = jsonMatch ? jsonMatch[1] : c.trim().startsWith('{') ? c.trim() : null
    if (jsonStr) return JSON.parse(jsonStr)
  } catch { /* ignore */ }
  return null
})
</script>

<style scoped>
.info-card {
  border: 1px solid #e0e7ff;
  border-radius: 10px;
  background: linear-gradient(135deg, #f0f4ff 0%, #fff 100%);
  overflow: hidden;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 14px;
  border-bottom: 1px solid #e0e7ff;
}

.card-icon  { font-size: 18px; }
.card-title { font-size: 14px; font-weight: 600; color: #3730a3; flex: 1; }
.card-body  { padding: 14px; display: flex; flex-direction: column; gap: 12px; }

.info-summary {
  font-size: 13px;
  color: #475569;
  line-height: 1.6;
  padding: 10px 12px;
  background: white;
  border-radius: 8px;
  border-left: 3px solid #6366f1;
}

.info-section { display: flex; flex-direction: column; gap: 8px; }

.info-section-label {
  font-size: 11px;
  font-weight: 700;
  color: #6366f1;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* 关键数字 */
.key-numbers {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  gap: 8px;
}

.kn-item {
  background: white;
  border-radius: 8px;
  padding: 10px 12px;
  border: 1px solid #e0e7ff;
  text-align: center;
}

.kn-value {
  font-size: 22px;
  font-weight: 800;
  color: #6366f1;
  line-height: 1.1;
}

.kn-unit {
  font-size: 11px;
  font-weight: 600;
  color: #94a3b8;
  margin-left: 2px;
}

.kn-desc {
  font-size: 11px;
  color: #64748b;
  margin-top: 4px;
  line-height: 1.3;
}

/* 对比表 */
.cmp-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}

.cmp-table th {
  background: #eff2ff;
  color: #3730a3;
  font-weight: 700;
  padding: 6px 10px;
  text-align: left;
  border: 1px solid #e0e7ff;
}

.cmp-table td {
  padding: 6px 10px;
  border: 1px solid #e0e7ff;
  color: #475569;
}

.cmp-table tr:nth-child(even) td { background: #fafbff; }

/* 时间线 */
.timeline { display: flex; flex-direction: column; gap: 6px; }

.tl-item {
  display: flex;
  gap: 10px;
  align-items: flex-start;
}

.tl-num {
  width: 22px; height: 22px;
  border-radius: 50%;
  background: #6366f1;
  color: white;
  font-size: 11px;
  font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
  margin-top: 1px;
}

.tl-content { flex: 1; }
.tl-step { font-size: 12px; font-weight: 600; color: #1e293b; }
.tl-desc  { font-size: 11px; color: #64748b; margin-top: 2px; }

/* 标签 */
.info-tags { display: flex; flex-wrap: wrap; gap: 6px; }
.info-tag  { font-size: 11px; }

.raw-content {
  font-size: 12px;
  color: #475569;
  white-space: pre-wrap;
  max-height: 200px;
  overflow-y: auto;
}

.card-footer {
  display: flex;
  gap: 12px;
  padding: 8px 14px;
  border-top: 1px solid #e0e7ff;
  font-size: 11px;
  color: #64748b;
}
</style>
