<script setup lang="ts">
import { computed, ref } from 'vue'
import { renderMarkdown } from '@/utils/markdown'
import type { ChatMessage, AgentTraceItem } from '@/stores/chatStore'

interface Props {
  message: ChatMessage
}

const props = defineProps<Props>()

const renderedContent = computed(() => renderMarkdown(props.message.content))
const isUser = computed(() => props.message.role === 'user')

// 执行链路展开/收起
const showTrace = ref(false)

// Agent 图标映射
const AGENT_ICONS: Record<string, string> = {
  '知识检索': '🔍',
  '认知诊断': '🧠',
  '画像更新': '👤',
  '资源生成': '📚',
  '路径规划': '🗳️',
  '挑战追问': '⚡',
}

function formatMs(ms: number): string {
  if (ms >= 1000) return `${(ms / 1000).toFixed(1)}s`
  return `${ms}ms`
}

const confColor = computed(() => {
  const v = (props.message.diagnosisConfidence ?? 0) * 100
  if (v >= 85) return '#10b981'
  if (v >= 70) return '#3b82f6'
  if (v >= 50) return '#f59e0b'
  return '#ef4444'
})

function traceNodeClass(item: AgentTraceItem) {
  if (item.durationMs > 2000) return 'node-slow'
  if (item.durationMs > 500) return 'node-normal'
  return 'node-fast'
}
</script>

<template>
  <div class="message-wrapper" :class="message.role">
    <div class="message-row">
      <div class="message-bubble">
        <div class="message-header">
          <el-avatar
            :size="28"
            :icon="isUser ? 'UserFilled' : 'ChatDotRound'"
            :style="{ backgroundColor: isUser ? '#3b82f6' : '#10b981' }"
          />
          <span class="message-role">{{ isUser ? '你' : (message.agentName || 'AI教练') }}</span>
          <span class="message-time">{{ new Date(message.timestamp).toLocaleTimeString() }}</span>
        </div>

        <div class="message-body markdown-body" v-html="renderedContent" />

        <!-- 响应质量元数据（流式结束后展示） -->
        <div
          v-if="!isUser && !message.isStreaming && (message.responseTimeMs || message.diagnosisConfidence)"
          class="msg-meta"
        >
          <span v-if="message.responseTimeMs" class="meta-chip time-chip">
            ⏱ {{ formatMs(message.responseTimeMs) }}
          </span>
          <span
            v-if="message.diagnosisConfidence"
            class="meta-chip conf-chip"
            :style="{ borderColor: confColor, color: confColor }"
          >
            🎯 {{ Math.round(message.diagnosisConfidence * 100) }}% 置信
          </span>
          <span v-if="message.sourceCount" class="meta-chip src-chip">
            📚 {{ message.sourceCount }} 篇来源
          </span>
        </div>

        <!-- Agent 执行链路（可折叠） -->
        <div
          v-if="!isUser && !message.isStreaming && message.agentTrace?.length"
          class="trace-section"
        >
          <button class="trace-toggle" @click="showTrace = !showTrace">
            <span class="trace-toggle-icon">&#x26D3;</span>
            <span class="trace-toggle-label">Agent 执行链路</span>
            <span class="trace-toggle-count">{{ message.agentTrace.length }} 步</span>
            <span v-if="message.responseTimeMs" class="trace-toggle-total">
              总耗时 {{ formatMs(message.responseTimeMs) }}
            </span>
            <span class="trace-toggle-arrow" :class="{ 'is-open': showTrace }">&#x25BE;</span>
          </button>

          <div v-show="showTrace" class="trace-pipeline">
            <template v-for="(item, idx) in message.agentTrace" :key="item.agentName + idx">
              <div class="trace-node" :class="traceNodeClass(item)">
                <span class="node-icon">{{ AGENT_ICONS[item.displayName] ?? '🤖' }}</span>
                <div class="node-body">
                  <span class="node-name">{{ item.displayName }}</span>
                  <span class="node-ms">{{ item.durationMs }}ms</span>
                </div>
              </div>
              <div v-if="idx < message.agentTrace!.length - 1" class="trace-arrow">
                <svg width="16" height="16" viewBox="0 0 16 16">
                  <path d="M3 8h10M9 4l4 4-4 4" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round"/>
                </svg>
              </div>
            </template>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<style scoped>
.message-wrapper {
  display: flex;
  width: 100%;
  animation: msg-slide-in 0.35s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes msg-slide-in {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message-wrapper.user {
  justify-content: flex-end;
}

.message-wrapper.assistant {
  justify-content: flex-start;
}

.message-row {
  display: flex;
  max-width: min(88%, 680px);
}

.message-bubble {
  padding: 12px 16px;
  border-radius: 18px;
  background-color: #ffffff;
  box-shadow: none;
  border: 1px solid #edf2f7;
  position: relative;
}

.message-wrapper.assistant .message-bubble {
  border-top-left-radius: 6px;
  background: #ffffff;
}

.message-wrapper.assistant .message-bubble::after {
  content: '';
  position: absolute;
  left: -6px;
  top: 16px;
  width: 12px;
  height: 12px;
  background: #fff;
  border-left: 1px solid #e5edf8;
  border-bottom: 1px solid #e5edf8;
  transform: rotate(45deg);
  border-bottom-left-radius: 2px;
}

.message-wrapper.user .message-bubble {
  background: linear-gradient(180deg, #34d399 0%, #10b981 100%);
  color: #fff;
  border-color: #10b981;
  box-shadow: none;
  border-top-right-radius: 6px;
  min-width: 120px;
  max-width: 420px;
}

.message-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.message-wrapper.user .message-header {
  margin-bottom: 8px;
}

.message-role {
  font-weight: 500;
  font-size: 12px;
  color: #64748b;
}

.message-wrapper.user .message-role {
  color: rgba(236, 253, 245, 0.95);
  font-weight: 500;
}

.message-time {
  color: #cbd5e1;
  font-size: 10px;
  margin-left: auto;
}

.message-wrapper.user .message-time {
  color: rgba(220, 252, 231, 0.8);
}

.message-body {
  font-size: 14px;
  line-height: 1.7;
  word-break: break-word;
}

.message-wrapper.user .message-body {
  font-size: 14px;
  line-height: 1.65;
  color: #ffffff;
}

.message-wrapper.user .message-bubble::before {
  content: none;
}

.message-wrapper.user .message-bubble::after {
  content: '';
  position: absolute;
  right: -6px;
  top: 16px;
  width: 12px;
  height: 12px;
  background: #10b981;
  border-right: 1px solid #10b981;
  border-top: 1px solid #10b981;
  transform: rotate(45deg);
  border-top-right-radius: 2px;
}

.message-wrapper.user .message-row {
  justify-content: flex-end;
}

.message-wrapper.user .message-bubble {
  margin-left: auto;
  position: relative;
}

.message-wrapper.user .message-header {
  gap: 6px;
}

.message-wrapper.user .message-bubble .el-avatar {
  opacity: 0.72;
}

.message-wrapper.assistant .message-bubble .el-avatar {
  opacity: 0.72;
}

.message-wrapper.assistant .message-header {
  gap: 6px;
}

/* ======================== 响应元数据条 ======================== */
.msg-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 10px;
  padding-top: 8px;
  border-top: 1px solid #f1f5f9;
}

.meta-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 500;
  border: 1px solid;
}

.time-chip {
  color: #64748b;
  border-color: #e2e8f0;
  background: #f8fafc;
}

.conf-chip {
  background: #fafafa;
}

.src-chip {
  color: #6366f1;
  border-color: #c7d2fe;
  background: #eef2ff;
}

/* ======================== Agent 执行链路 ======================== */
.trace-section {
  margin-top: 10px;
  border-top: 1px solid #f1f5f9;
  padding-top: 8px;
}

.trace-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
  padding: 6px 8px;
  background: linear-gradient(90deg, #f0f9ff, #fafafa);
  border: 1px solid #e0f2fe;
  border-radius: 8px;
  cursor: pointer;
  font-size: 12px;
  color: #0369a1;
  transition: all 0.2s;
  text-align: left;
}

.trace-toggle:hover {
  background: #e0f2fe;
  border-color: #bae6fd;
}

.trace-toggle-icon { font-size: 13px; }
.trace-toggle-label { font-weight: 600; flex: 1; }
.trace-toggle-count {
  background: #0ea5e9;
  color: #fff;
  padding: 1px 6px;
  border-radius: 10px;
  font-size: 10px;
}
.trace-toggle-total {
  color: #64748b;
  font-size: 11px;
}
.trace-toggle-arrow {
  font-size: 10px;
  transition: transform 0.2s;
  color: #94a3b8;
}
.trace-toggle-arrow.is-open { transform: rotate(180deg); }

.trace-pipeline {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
  padding: 10px 8px 4px;
  overflow-x: auto;
}

.trace-node {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border-radius: 8px;
  border: 1px solid;
  min-width: 80px;
  transition: box-shadow 0.15s;
}
.trace-node:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.08); }

.node-fast  { background: #f0fdf4; border-color: #86efac; }
.node-normal{ background: #fffbeb; border-color: #fcd34d; }
.node-slow  { background: #fef2f2; border-color: #fca5a5; }

.node-icon { font-size: 14px; flex-shrink: 0; }
.node-body { display: flex; flex-direction: column; }
.node-name { font-size: 11px; font-weight: 600; color: #1e293b; }
.node-ms   { font-size: 10px; color: #64748b; font-family: 'JetBrains Mono', monospace; }

.trace-arrow {
  color: #94a3b8;
  flex-shrink: 0;
}
</style>

<style>
/* Markdown 样式 */
.markdown-body h1,
.markdown-body h2,
.markdown-body h3 {
  margin: 12px 0 8px;
  font-weight: 600;
  color: inherit;
}

.markdown-body p {
  margin: 6px 0;
}

.markdown-body ul,
.markdown-body ol {
  margin: 6px 0;
  padding-left: 20px;
}

.markdown-body li {
  margin: 2px 0;
}

.markdown-body code {
  background-color: rgba(0,0,0,0.05);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Fira Code', 'Consolas', monospace;
  font-size: 13px;
}

.message-wrapper.user .markdown-body code {
  background-color: rgba(255,255,255,0.15);
}

.markdown-body pre {
  margin: 10px 0;
  border-radius: 8px;
  overflow: hidden;
}

.markdown-body pre code {
  background: none;
  padding: 0;
  border-radius: 0;
}

.markdown-body blockquote {
  margin: 8px 0;
  padding: 8px 16px;
  border-left: 3px solid #cbd5e1;
  background-color: rgba(0,0,0,0.02);
  border-radius: 0 8px 8px 0;
}

.markdown-body table {
  border-collapse: collapse;
  margin: 10px 0;
  width: 100%;
}

.markdown-body th,
.markdown-body td {
  border: 1px solid #e2e8f0;
  padding: 8px 12px;
  text-align: left;
}

.markdown-body th {
  background-color: #f8fafc;
  font-weight: 600;
}

/* 代码块头部 */
.code-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 14px;
  background-color: #1e293b;
  border-bottom: 1px solid #334155;
}

.code-lang {
  font-size: 12px;
  color: #94a3b8;
  text-transform: uppercase;
  font-family: monospace;
}

.copy-btn {
  font-size: 11px;
  color: #94a3b8;
  background: transparent;
  border: 1px solid #475569;
  border-radius: 4px;
  padding: 2px 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.copy-btn:hover {
  color: #e2e8f0;
  border-color: #94a3b8;
}
</style>
