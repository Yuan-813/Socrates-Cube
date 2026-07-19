<template>
  <div class="manual-page" :class="page.bgClass">
    <!-- 封面/封底 布局 -->
    <template v-if="page.type === 'cover' || page.type === 'back'">
      <div class="cover-layout">
        <div class="cover-body">
          <!-- RFC 徽章 -->
          <div class="cover-badge">RFC</div>
          <h1 class="cover-title">{{ page.title }}</h1>
          <p v-if="page.subtitle" class="cover-subtitle">{{ page.subtitle }}</p>
          <div class="cover-content" v-html="page.content"></div>
        </div>
      </div>
    </template>

    <!-- 目录布局 -->
    <template v-else-if="page.type === 'toc'">
      <div class="toc-layout">
        <div class="toc-header-line"></div>
        <h2 class="toc-title">{{ page.title }}</h2>
        <div class="toc-body" v-html="page.content"></div>
        <div class="page-footer">Socrates Cube · User Manual</div>
      </div>
    </template>

    <!-- 正文内容布局 -->
    <template v-else>
      <div class="content-layout">
        <div class="page-header">
          <span class="header-tag">{{ page.headerTag }}</span>
          <span class="header-page">{{ page.id }}</span>
        </div>
        <h2 class="content-title">{{ page.title }}</h2>
        <div class="content-body" v-html="page.content"></div>
        <div class="page-footer">
          <div class="footer-line"></div>
          <span>Socrates Cube User Manual</span>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import type { ManualPage } from '@/data/userManualContent'

defineProps<{
  page: ManualPage
}>()
</script>

<style scoped>
.manual-page {
  width: 100%;
  height: 100%;
  box-sizing: border-box;
  font-family: system-ui, -apple-system, sans-serif;
  overflow: hidden;
}

/* ====== 封面/封底样式 ====== */
.page-cover {
  background: linear-gradient(155deg, #051b3e 0%, #0d2a5e 40%, #0a1a4e 100%);
  position: relative;
  overflow: hidden;
}

/* 电路板纹理叠加层 */
.page-cover::before {
  content: '';
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(99,202,246,0.06) 1px, transparent 1px),
    linear-gradient(90deg, rgba(99,202,246,0.06) 1px, transparent 1px);
  background-size: 28px 28px;
  pointer-events: none;
  z-index: 0;
}

/* 圆弧光晕装饰 */
.page-cover::after {
  content: '';
  position: absolute;
  top: -60px;
  left: 50%;
  transform: translateX(-50%);
  width: 400px;
  height: 400px;
  background: radial-gradient(ellipse, rgba(99,102,241,0.15) 0%, transparent 70%);
  pointer-events: none;
  z-index: 0;
}

.cover-layout {
  position: relative;
  z-index: 1;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  box-sizing: border-box;
}

.cover-body {
  text-align: center;
  position: relative;
}

/* RFC 徽章 */
.cover-badge {
  position: absolute;
  top: -60px;
  right: -30px;
  background: linear-gradient(135deg, #1e40af, #3b82f6);
  color: #fff;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 1.5px;
  padding: 6px 10px;
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(59,130,246,0.4);
}

.cover-title {
  font-size: 26px;
  font-weight: 700;
  background: linear-gradient(90deg, #60d5fa, #a78bfa);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  margin: 0 0 14px 0;
  letter-spacing: 3px;
}

.cover-subtitle {
  font-size: 14px;
  color: rgba(147,197,253,0.85);
  margin: 0 0 28px 0;
  font-weight: 300;
  letter-spacing: 1px;
}

:deep(.cover-meta) { margin-top: 36px; }

:deep(.cover-meta .version) {
  color: rgba(99,202,246,0.8);
  font-size: 13px;
  font-family: monospace;
  margin: 0 0 8px 0;
}

:deep(.cover-meta .team) {
  color: rgba(255,255,255,0.45);
  font-size: 11px;
  margin: 0 0 10px 0;
}

:deep(.cover-meta .cover-powered) {
  display: inline-block;
  font-size: 10px;
  color: rgba(99,202,246,0.55);
  border: 1px solid rgba(99,202,246,0.2);
  border-radius: 4px;
  padding: 2px 8px;
  letter-spacing: 1px;
  font-family: monospace;
}

:deep(.back-content) { margin-top: 20px; }

:deep(.encourage-text) {
  color: rgba(203,213,225,0.8);
  font-size: 14px;
  margin: 0 0 12px 0;
  line-height: 1.8;
}

:deep(.enter-btn-placeholder) {
  margin-top: 28px;
  display: inline-block;
  padding: 12px 36px;
  background: linear-gradient(135deg, #3b82f6, #6366f1);
  color: #fff;
  border-radius: 24px;
  font-size: 14px;
  font-weight: 600;
  letter-spacing: 1px;
  box-shadow: 0 4px 16px rgba(99,102,241,0.45);
}

/* ====== 浅色页面背景 ====== */
.page-light {
  background: #f8fafd;
}

/* ====== 目录样式 ====== */
.toc-layout {
  width: 100%;
  height: 100%;
  padding: 40px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
}

.toc-header-line {
  height: 3px;
  background: linear-gradient(90deg, #6366f1, #8b5cf6, transparent);
  border-radius: 2px;
  margin-bottom: 24px;
}

.toc-title {
  font-size: 22px;
  font-weight: 700;
  color: #1e293b;
  text-align: center;
  margin: 0 0 28px 0;
  letter-spacing: 4px;
}

.toc-body { flex: 1; }

:deep(.toc-list) {
  list-style: none;
  padding: 0;
  margin: 0;
}

:deep(.toc-list li) {
  display: flex;
  align-items: baseline;
  padding: 13px 0;
  border-bottom: 1px solid #f1f5f9;
}

:deep(.toc-list li::before) {
  content: '◈';
  color: #6366f1;
  font-size: 13px;
  margin-right: 10px;
  flex-shrink: 0;
}

:deep(.toc-chapter) {
  font-size: 15px;
  color: #334155;
  font-weight: 500;
}

:deep(.toc-dots) {
  flex: 1;
  border-bottom: 2px dotted #cbd5e1;
  margin: 0 12px;
  position: relative;
  top: -4px;
}

:deep(.toc-page) {
  font-size: 13px;
  color: #6366f1;
  font-weight: 700;
  font-family: monospace;
}

/* ====== 正文内容样式 ====== */
.content-layout {
  width: 100%;
  height: 100%;
  padding: 36px 40px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 18px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e2e8f0;
}

.header-tag {
  font-size: 11px;
  color: #fff;
  font-weight: 600;
  letter-spacing: 1px;
  text-transform: uppercase;
  background: linear-gradient(90deg, #6366f1, #8b5cf6);
  padding: 3px 10px;
  border-radius: 20px;
}

.header-page {
  font-size: 11px;
  color: #94a3b8;
  font-family: monospace;
}

.content-title {
  font-size: 22px;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 18px 0;
}

.content-body {
  flex: 1;
  overflow: hidden;
  font-size: 13.5px;
  line-height: 1.75;
  color: #475569;
}

:deep(.section) { margin-bottom: 14px; }

:deep(.section h3) {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 5px 0;
}

:deep(.section p) { margin: 0; font-size: 13px; line-height: 1.7; }

:deep(.agent-list) { list-style: none; padding: 0; margin: 6px 0 0 0; }
:deep(.agent-list li) { padding: 4px 0; font-size: 12.5px; }

/* 功能卡片 */
:deep(.feature-cards) {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

:deep(.feature-card) {
  background: linear-gradient(135deg, #f8faff, #eef2ff);
  border: 1px solid #e0e7ff;
  border-radius: 10px;
  padding: 12px;
  text-align: center;
  transition: box-shadow 0.2s;
}

:deep(.feature-card:last-child) { grid-column: 1 / -1; }
:deep(.feature-icon) { font-size: 22px; margin-bottom: 5px; }
:deep(.feature-card h4) { font-size: 12.5px; font-weight: 600; color: #1e293b; margin: 0 0 4px 0; }
:deep(.feature-card p) { font-size: 11px; color: #64748b; margin: 0; line-height: 1.5; }

/* 步骤样式 */
:deep(.steps) { display: flex; flex-direction: column; gap: 18px; }
:deep(.step) { display: flex; gap: 14px; align-items: flex-start; }

:deep(.step-number) {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 15px;
  font-weight: 700;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(99,102,241,0.35);
}

:deep(.step-content h4) { font-size: 14px; font-weight: 600; color: #1e293b; margin: 0 0 4px 0; }
:deep(.step-content p) { font-size: 12.5px; color: #64748b; margin: 0; line-height: 1.6; }

/* 页脚 */
.page-footer {
  margin-top: auto;
  padding-top: 10px;
  text-align: center;
  font-size: 10px;
  color: #94a3b8;
  font-family: monospace;
  letter-spacing: 0.5px;
}

.footer-line {
  width: 36px;
  height: 1px;
  background: linear-gradient(90deg, transparent, #6366f1, transparent);
  margin: 0 auto 6px auto;
}
</style>
