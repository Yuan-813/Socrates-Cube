<template>
  <div class="trust-badge" :class="`level-${level}`" @mouseenter="showDetail = true" @mouseleave="showDetail = false">
    <span class="trust-stars">{{ starStr }}</span>
    <span class="trust-label">{{ shortLabel }}</span>

    <!-- 悬浮详情 -->
    <transition name="fade">
      <div v-if="showDetail" class="trust-tooltip">
        <div class="tt-header">
          <span class="tt-stars">{{ starStr }}</span>
          <span class="tt-title">可信等级 {{ level }}/5</span>
        </div>
        <div class="tt-sources" v-if="sources.length">
          <div class="tt-source-label">来源依据</div>
          <div v-for="s in sources" :key="s" class="tt-source-item">• {{ s }}</div>
        </div>
        <div class="tt-audit" :class="audited ? 'pass' : 'pending'">
          {{ audited ? '✓ AI审核通过' : '⏳ 待校验' }}
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

const props = defineProps<{
  level: number       // 1-5
  sources: string[]   // 来源引用列表
  audited: boolean    // 是否已AI审核
}>()

const showDetail = ref(false)

const starStr = computed(() => {
  const full = Math.floor(props.level)
  const half = props.level - full >= 0.5 ? 1 : 0
  const empty = 5 - full - half
  return '★'.repeat(full) + (half ? '½' : '') + '☆'.repeat(empty)
})

const shortLabel = computed(() => {
  if (props.level >= 5) return '已校验'
  if (props.level >= 4) return 'RFC来源'
  if (props.level >= 3) return 'AI生成'
  return '待校验'
})
</script>

<style scoped>
.trust-badge {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 10px;
  font-weight: 600;
  cursor: default;
  user-select: none;
  white-space: nowrap;
}

.level-5 { background: #dcfce7; color: #15803d; border: 1px solid #bbf7d0; }
.level-4 { background: #dbeafe; color: #1d4ed8; border: 1px solid #bfdbfe; }
.level-3 { background: #f3f4f6; color: #4b5563; border: 1px solid #e5e7eb; }
.level-2 { background: #fef9c3; color: #854d0e; border: 1px solid #fef08a; }
.level-1 { background: #fee2e2; color: #b91c1c; border: 1px solid #fecaca; }

.trust-stars { letter-spacing: -1px; font-size: 9px; }
.trust-label { font-size: 10px; }

/* 悬浮详情 */
.trust-tooltip {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  width: 200px;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.12);
  padding: 10px 12px;
  z-index: 999;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.tt-header {
  display: flex;
  align-items: center;
  gap: 8px;
}
.tt-stars { font-size: 13px; color: #f59e0b; letter-spacing: -1px; }
.tt-title { font-size: 12px; font-weight: 700; color: #1e293b; }

.tt-sources { display: flex; flex-direction: column; gap: 3px; }
.tt-source-label { font-size: 10px; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.4px; }
.tt-source-item { font-size: 11px; color: #475569; line-height: 1.4; }

.tt-audit {
  font-size: 11px;
  font-weight: 600;
  padding: 4px 8px;
  border-radius: 6px;
  text-align: center;
}
.tt-audit.pass   { background: #f0fdf4; color: #15803d; }
.tt-audit.pending { background: #fefce8; color: #854d0e; }

.fade-enter-active, .fade-leave-active { transition: opacity 0.15s, transform 0.15s; }
.fade-enter-from, .fade-leave-to { opacity: 0; transform: translateY(-4px); }
</style>
