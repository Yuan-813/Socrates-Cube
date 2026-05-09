<script setup lang="ts">
import { computed } from 'vue'
import { renderMarkdown } from '@/utils/markdown'
import type { ChatMessage } from '@/stores/chatStore'

interface Props {
  message: ChatMessage
}

const props = defineProps<Props>()

const renderedContent = computed(() => {
  return renderMarkdown(props.message.content)
})

const isUser = computed(() => props.message.role === 'user')
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
      </div>
    </div>
  </div>
</template>

<style scoped>
.message-wrapper {
  display: flex;
  width: 100%;
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
