<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import DiagnosisPanel from '@/components/DiagnosisPanel.vue'
import ZhiWenSuYuanModal from '@/components/ZhiWenSuYuanModal.vue'
import { useChatStore } from '@/stores/chatStore'
import { useUserStore } from '@/stores/userStore'

const showZhiWen = ref(false)
const router = useRouter()
const chatStore = useChatStore()
const userStore = useUserStore()

const hasDiagnosis = computed(() => chatStore.lastDiagnosis !== null)
const masteryScore = computed(() => userStore.profileCompleteness)

const agents = [
  { id: 'profiler',   label: 'Profiler',   sub: '学习画像管理',   icon: '👤', color: '#6366f1' },
  { id: 'retriever',  label: 'Retriever',  sub: '知识检索器',    icon: '🔍', color: '#0ea5e9' },
  { id: 'diagnosis',  label: 'Diagnosis',  sub: '诊断分析器',    icon: '🧠', color: '#8b5cf6' },
  { id: 'planner',    label: 'Planner',    sub: '路径规划师',    icon: '🗺️', color: '#10b981' },
]

const historyRecords = [
  { time: '今天 10:25', topic: 'TCP 三次握手诊断', count: 1, color: '#ef4444', done: false },
  { time: '今天 09:15', topic: 'HTTP 状态码理解',  count: 2, color: '#f59e0b', done: false },
  { time: '昨天 18:30', topic: 'DNS 解析流程诊断', count: 1, color: '#f59e0b', done: false },
  { time: '昨天 16:45', topic: 'UDP 协议特性诊断', count: 0, color: '#10b981', done: true  },
]

const learningPath = [
  { step: 1, title: '概念巩固', sub: 'TCP 状态机与三次握手流程', mins: 8, color: '#6366f1', active: true  },
  { step: 2, title: '机制理解', sub: 'ACK 确认号计算与作用',      mins: 7, color: '#0ea5e9', active: false },
  { step: 3, title: '协议验证', sub: 'Wireshark 抓包分析实验',    mins: 15, color: '#8b5cf6', active: false },
  { step: 4, title: '综合训练', sub: '三次握手模拟实现练习',       mins: 10, color: '#10b981', active: false },
  { step: 5, title: '能力评估', sub: '诊断反馈与画像提升',         mins: 5,  color: '#f59e0b', active: false },
]

const trainItems = [
  { icon: '🎯', title: 'TCP 三次握手模拟实验', type: '实验', rate: 95, desc: '可视化实验完整三次握手过程', mins: 20, path: '/simulator' },
  { icon: '📝', title: 'ACK 确认号计算练习',   type: '练习', rate: 90, desc: '强化 ACK 计算和确认机制理解', mins: 15, path: '/resources?type=exercise' },
  { icon: '🔬', title: 'Wireshark 抓包分析实战', type: '实战', rate: 85, desc: '通过真实抓包验证 ACK 字段变化', mins: 30, path: '/resources?type=exercise' },
]
</script>

<template>
  <div class="s1-page">

    <!-- ── 顶部 Engine Banner ── -->
    <div class="s1-engine-banner">
      <div class="s1-banner-left">
        <div class="s1-brain-icon">
          <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
            <circle cx="16" cy="16" r="14" stroke="#6366f1" stroke-width="1.5" opacity="0.3"/>
            <circle cx="16" cy="16" r="8"  fill="url(#brainGrad)"/>
            <circle cx="16" cy="16" r="4"  fill="#6366f1" opacity="0.8"/>
            <defs><radialGradient id="brainGrad" cx="50%" cy="50%" r="50%"><stop offset="0%" stop-color="#818cf8"/><stop offset="100%" stop-color="#6366f1" stop-opacity="0.3"/></radialGradient></defs>
          </svg>
        </div>
        <div>
          <div class="s1-engine-title">Socrates Cognitive Engine</div>
          <div class="s1-engine-sub">AI 认知诊断引擎正在为你分析
            <span class="s1-topic-tag">
              <svg width="8" height="8" viewBox="0 0 8 8"><circle cx="4" cy="4" r="3" fill="#10b981"/></svg>
              当前主题：TCP 三次握手
            </span>
          </div>
        </div>
      </div>

      <!-- Agent 工作流 -->
      <div class="s1-agent-flow">
        <span class="s1-flow-label">AI Agent 协同工作中</span>
        <div class="s1-agents">
          <template v-for="(ag, i) in agents" :key="ag.id">
            <div class="s1-agent-node">
              <div class="s1-agent-circle" :style="{ borderColor: ag.color + '60', background: ag.color + '10' }">
                <span class="s1-agent-icon">{{ ag.icon }}</span>
                <div class="s1-agent-pulse" :style="{ background: ag.color }"></div>
              </div>
              <div class="s1-agent-label">{{ ag.label }}</div>
              <div class="s1-agent-sub">{{ ag.sub }}</div>
            </div>
            <div v-if="i < agents.length - 1" class="s1-agent-arrow">
              <svg width="16" height="16" viewBox="0 0 16 16"><path d="M3 8h10m0 0l-3-3m3 3l-3 3" stroke="#94a3b8" stroke-width="1.5" stroke-linecap="round"/></svg>
            </div>
          </template>
        </div>
      </div>

      <!-- 右侧进度环 -->
      <div class="s1-progress-area">
        <div class="s1-progress-ring">
          <svg width="64" height="64" viewBox="0 0 64 64">
            <circle cx="32" cy="32" r="26" fill="none" stroke="#e2e8f0" stroke-width="5"/>
            <circle cx="32" cy="32" r="26" fill="none" stroke="url(#ringGrad)" stroke-width="5"
              stroke-linecap="round" stroke-dasharray="163.4" :stroke-dashoffset="163.4 * (1 - masteryScore / 100)"
              transform="rotate(-90 32 32)"/>
            <defs><linearGradient id="ringGrad" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#6366f1"/><stop offset="100%" stop-color="#0ea5e9"/></linearGradient></defs>
          </svg>
          <div class="s1-ring-val">{{ masteryScore || 72 }}%</div>
        </div>
        <div class="s1-ring-info">
          <div class="s1-ring-label">分析进度</div>
          <div class="s1-status-rows">
            <div class="s1-status-row"><span class="s1-sr-key">诊断状态</span><span class="s1-sr-val s1-active">{{ hasDiagnosis ? '已完成' : '分析中...' }}</span></div>
            <div class="s1-status-row"><span class="s1-sr-key">知识节点</span><span class="s1-sr-val">ACK 确认机制</span></div>
            <div class="s1-status-row"><span class="s1-sr-key">匹配误解模型</span><span class="s1-sr-val s1-warn">M-07 确认号</span></div>
          </div>
        </div>
        <button class="s1-launch-btn" @click="showZhiWen = true">
          <svg width="14" height="14" viewBox="0 0 14 14"><path d="M7,0.5 L8.8,5.2 L13.5,7 L8.8,8.8 L7,13.5 L5.2,8.8 L0.5,7 L5.2,5.2 Z" fill="white"/></svg>
          启动诊断
        </button>
      </div>
    </div>

    <!-- ── L1/L2/L3 引擎条 ── -->
    <div class="s1-layer-bar">
      <div class="s1-layer-card">
        <div class="s1-lc-badge l1">L1</div>
        <div class="s1-lc-body">
          <div class="s1-lc-title">表面错误识别</div>
          <div class="s1-lc-sub">识别学生回答中的错误现象</div>
          <div class="s1-lc-stats">9种错误类型 · 6种 RFC 标准</div>
        </div>
      </div>
      <div class="s1-layer-arrow">
        <svg width="32" height="16" viewBox="0 0 32 16">
          <line x1="2" y1="8" x2="28" y2="8" stroke="#cbd5e1" stroke-width="1.5" stroke-dasharray="3,3"/>
          <path d="M24 4l6 4-6 4" stroke="#6366f1" stroke-width="1.5" fill="none" stroke-linecap="round"/>
        </svg>
      </div>
      <div class="s1-layer-card">
        <div class="s1-lc-badge l2">L2</div>
        <div class="s1-lc-body">
          <div class="s1-lc-title">根因分析定位</div>
          <div class="s1-lc-sub">定位知识节点与认知漏洞</div>
          <div class="s1-lc-stats">20 KP 节点 · 48 ACU 认知单元</div>
        </div>
      </div>
      <div class="s1-layer-arrow">
        <svg width="32" height="16" viewBox="0 0 32 16">
          <line x1="2" y1="8" x2="28" y2="8" stroke="#cbd5e1" stroke-width="1.5" stroke-dasharray="3,3"/>
          <path d="M24 4l6 4-6 4" stroke="#8b5cf6" stroke-width="1.5" fill="none" stroke-linecap="round"/>
        </svg>
      </div>
      <div class="s1-layer-card">
        <div class="s1-lc-badge l3">L3</div>
        <div class="s1-lc-body">
          <div class="s1-lc-title">模式匹配与干预</div>
          <div class="s1-lc-sub">配置修复模型并生成干预方案</div>
          <div class="s1-lc-stats">8种误区模式 · 150+ 误解条目</div>
        </div>
      </div>
    </div>

    <!-- ── 主内容区：左侧诊断 + 右侧侧边栏 ── -->
    <div class="s1-main-layout">

      <!-- 左侧：核心诊断报告 -->
      <div class="s1-main-col">
        <div class="s1-card">
          <div class="s1-card-header">
            <div class="s1-card-icon-wrap"><svg width="16" height="16" viewBox="0 0 16 16"><circle cx="8" cy="8" r="6" fill="none" stroke="#6366f1" stroke-width="1.5"/><path d="M8 5v3l2 2" stroke="#6366f1" stroke-width="1.5" stroke-linecap="round"/></svg></div>
            <span class="s1-card-title">认知诊断报告</span>
            <span class="s1-card-badge">AI 生成</span>
          </div>
          <p class="s1-card-desc">三层诊断引擎：表面错误识别 → 根因溯源分析 → 误解模式匹配，基于谢希仁《计算机网络》第8版 &amp; IETF RFC 标准体系</p>
          <DiagnosisPanel />
        </div>

        <!-- 个性化学习路径 -->
        <div class="s1-card s1-path-card">
          <div class="s1-card-header">
            <div class="s1-card-icon-wrap" style="background:#ecfdf5;border-color:#6ee7b7"><svg width="16" height="16" viewBox="0 0 16 16"><path d="M2 8h12M8 2l6 6-6 6" stroke="#10b981" stroke-width="1.5" fill="none" stroke-linecap="round"/></svg></div>
            <span class="s1-card-title">个性化学习路径</span>
            <span class="s1-card-badge s1-badge-green">AI Planner 生成</span>
          </div>
          <div class="s1-path-steps">
            <template v-for="(p, i) in learningPath" :key="p.step">
              <div class="s1-path-item" :class="{ active: p.active }">
                <div class="s1-path-circle" :style="{ background: p.color, boxShadow: p.active ? `0 0 12px ${p.color}60` : 'none' }">
                  <svg width="14" height="14" viewBox="0 0 14 14"><circle cx="7" cy="7" r="5" fill="none" stroke="white" stroke-width="1.5"/><path v-if="p.active" d="M5 7l2 2 4-4" stroke="white" stroke-width="1.5" stroke-linecap="round"/><text v-else x="7" y="10.5" text-anchor="middle" fill="white" font-size="7" font-weight="700">{{ p.step }}</text></svg>
                </div>
                <div class="s1-path-info">
                  <div class="s1-path-title" :style="{ color: p.active ? p.color : '#1e293b' }">{{ p.title }}</div>
                  <div class="s1-path-sub">{{ p.sub }}</div>
                </div>
                <div class="s1-path-mins">预计 {{ p.mins }} 分钟</div>
              </div>
              <div v-if="i < learningPath.length - 1" class="s1-path-connector" :style="{ borderColor: learningPath[i + 1].active ? '#e2e8f0' : '#f1f5f9' }"></div>
            </template>
          </div>
          <div class="s1-path-footer">
            <span>⏱ 总时长：45 分钟</span>
            <span>📈 预计提升：+18%</span>
            <button class="s1-start-btn" @click="router.push('/resources')">开始学习计划</button>
          </div>
        </div>
      </div>

      <!-- 右侧侧边栏 -->
      <div class="s1-sidebar">

        <!-- 推荐强化训练 -->
        <div class="s1-card">
          <div class="s1-card-header">
            <div class="s1-card-icon-wrap" style="background:#fef3c7;border-color:#fcd34d"><svg width="16" height="16" viewBox="0 0 16 16"><path d="M8 2l1.8 4.8 5.2 0.2-4 3.2 1.5 5L8 12.5l-4.5 2.7 1.5-5-4-3.2 5.2-0.2z" fill="#f59e0b"/></svg></div>
            <span class="s1-card-title">推荐强化训练</span>
            <span class="s1-card-desc-small">基于你的诊断结果</span>
          </div>
          <div class="s1-train-list">
            <div v-for="t in trainItems" :key="t.title" class="s1-train-item" @click="router.push(t.path)">
              <div class="s1-train-icon">{{ t.icon }}</div>
              <div class="s1-train-info">
                <div class="s1-train-title">{{ t.title }}</div>
                <div class="s1-train-sub">{{ t.desc }}</div>
                <div class="s1-train-meta">
                  <span class="s1-train-type">{{ t.type }}</span>
                  <span class="s1-train-mins">{{ t.mins }} 分钟</span>
                </div>
              </div>
              <div class="s1-train-rate">
                <div class="s1-rate-num">{{ t.rate }}%</div>
                <div class="s1-rate-bar"><div class="s1-rate-fill" :style="{ width: t.rate + '%', background: t.rate >= 90 ? '#10b981' : '#6366f1' }"></div></div>
              </div>
            </div>
          </div>
        </div>

        <!-- 历史诊断记录 -->
        <div class="s1-card">
          <div class="s1-card-header">
            <div class="s1-card-icon-wrap" style="background:#f0f9ff;border-color:#bae6fd"><svg width="16" height="16" viewBox="0 0 16 16"><path d="M3 3h10v10H3z" fill="none" stroke="#0ea5e9" stroke-width="1.5"/><path d="M5 6h6M5 9h4" stroke="#0ea5e9" stroke-width="1.5" stroke-linecap="round"/></svg></div>
            <span class="s1-card-title">历史诊断记录</span>
            <button class="s1-view-all" @click="router.push('/profile')">查看全部记录 →</button>
          </div>
          <div class="s1-history-list">
            <div v-for="h in historyRecords" :key="h.time" class="s1-history-item" @click="router.push('/profile')" style="cursor:pointer">
              <div class="s1-hi-dot" :style="{ background: h.color }"></div>
              <div class="s1-hi-info">
                <div class="s1-hi-title">{{ h.topic }}</div>
                <div class="s1-hi-time">{{ h.time }}</div>
              </div>
              <div class="s1-hi-count" :style="{ background: h.count === 0 ? '#dcfce7' : '#fee2e2', color: h.count === 0 ? '#166534' : '#991b1b' }">
                {{ h.count === 0 ? '无误解' : `${h.count} 个误解` }}
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>

    <ZhiWenSuYuanModal :visible="showZhiWen" @close="showZhiWen = false" />
  </div>
</template>

<style scoped>
/* ── 基础 ── */
.s1-page {
  background: linear-gradient(150deg, #F4F7FF 0%, #EEF2FF 40%, #F0F9FF 100%);
  min-height: 100%;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* ── Engine Banner ── */
.s1-engine-banner {
  background: #ffffff;
  border: 1px solid #e0e7ff;
  border-radius: 16px;
  padding: 20px 24px;
  display: flex;
  align-items: center;
  gap: 24px;
  box-shadow: 0 4px 24px rgba(99,102,241,0.08), 0 1px 3px rgba(0,0,0,0.05);
  position: relative;
  overflow: hidden;
}
.s1-engine-banner::before {
  content: '';
  position: absolute; top: 0; left: 0; right: 0; height: 3px;
  background: linear-gradient(90deg, #6366f1, #0ea5e9, #8b5cf6);
}
.s1-banner-left { display: flex; align-items: center; gap: 16px; min-width: 260px; }
.s1-brain-icon {
  width: 52px; height: 52px; border-radius: 14px;
  background: linear-gradient(135deg, #eef2ff, #e0e7ff);
  border: 1.5px solid #c7d2fe;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 4px 12px rgba(99,102,241,0.15);
}
.s1-engine-title { font-size: 18px; font-weight: 800; color: #1e293b; letter-spacing: 0.3px; }
.s1-engine-sub { font-size: 12px; color: #64748b; margin-top: 3px; display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.s1-topic-tag {
  display: inline-flex; align-items: center; gap: 4px;
  background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 20px;
  padding: 2px 8px; font-size: 11px; color: #166534; font-weight: 600;
}

/* Agent Flow */
.s1-agent-flow { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 8px; }
.s1-flow-label { font-size: 10px; color: #94a3b8; font-weight: 600; letter-spacing: 1px; text-transform: uppercase; }
.s1-agents { display: flex; align-items: center; gap: 4px; }
.s1-agent-node { display: flex; flex-direction: column; align-items: center; gap: 4px; }
.s1-agent-circle {
  width: 40px; height: 40px; border-radius: 50%; border: 1.5px solid;
  display: flex; align-items: center; justify-content: center; position: relative;
  transition: all 0.3s;
}
.s1-agent-circle:hover { transform: scale(1.1); }
.s1-agent-icon { font-size: 16px; }
.s1-agent-pulse {
  position: absolute; inset: -3px; border-radius: 50%;
  opacity: 0; animation: s1-pulse 2s ease-in-out infinite;
}
@keyframes s1-pulse { 0%,100%{opacity:0;transform:scale(1)} 50%{opacity:0.3;transform:scale(1.2)} }
.s1-agent-label { font-size: 10px; font-weight: 700; color: #1e293b; }
.s1-agent-sub { font-size: 9px; color: #94a3b8; text-align: center; max-width: 52px; line-height: 1.2; }
.s1-agent-arrow { color: #cbd5e1; display: flex; align-items: center; }

/* Progress Area */
.s1-progress-area { display: flex; align-items: center; gap: 12px; flex-shrink: 0; }
.s1-progress-ring { position: relative; width: 64px; height: 64px; flex-shrink: 0; }
.s1-progress-ring svg { transform: none; }
.s1-ring-val {
  position: absolute; inset: 0; display: flex; align-items: center; justify-content: center;
  font-size: 13px; font-weight: 800; color: #6366f1;
}
.s1-ring-info { display: flex; flex-direction: column; gap: 4px; }
.s1-ring-label { font-size: 10px; font-weight: 600; color: #64748b; margin-bottom: 2px; }
.s1-status-rows { display: flex; flex-direction: column; gap: 3px; }
.s1-status-row { display: flex; align-items: center; gap: 6px; font-size: 10px; }
.s1-sr-key { color: #94a3b8; white-space: nowrap; }
.s1-sr-val { color: #334155; font-weight: 600; white-space: nowrap; }
.s1-sr-val.s1-active { color: #10b981; }
.s1-sr-val.s1-warn { color: #f59e0b; }

.s1-launch-btn {
  padding: 10px 20px; border-radius: 24px;
  background: linear-gradient(135deg, #6366f1, #0ea5e9);
  border: none; color: #fff;
  cursor: pointer; font-size: 12px; font-weight: 700;
  display: flex; align-items: center; gap: 6px;
  box-shadow: 0 4px 14px rgba(99,102,241,0.35);
  transition: all 0.2s; white-space: nowrap; flex-shrink: 0;
}
.s1-launch-btn:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(99,102,241,0.45); }

/* ── Layer Bar ── */
.s1-layer-bar {
  display: flex; align-items: center; gap: 0;
  background: #ffffff;
  border: 1px solid #e2e8f0; border-radius: 14px; padding: 16px 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}
.s1-layer-card { flex: 1; display: flex; align-items: center; gap: 12px; padding: 8px 12px; }
.s1-lc-badge {
  width: 36px; height: 36px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  font-size: 11px; font-weight: 800; flex-shrink: 0; letter-spacing: 0.5px;
}
.s1-lc-badge.l1 { background: #fee2e2; color: #dc2626; border: 1px solid #fca5a5; }
.s1-lc-badge.l2 { background: #fef3c7; color: #d97706; border: 1px solid #fcd34d; }
.s1-lc-badge.l3 { background: #ede9fe; color: #7c3aed; border: 1px solid #c4b5fd; }
.s1-lc-body { display: flex; flex-direction: column; gap: 2px; }
.s1-lc-title { font-size: 13px; font-weight: 700; color: #1e293b; }
.s1-lc-sub { font-size: 11px; color: #64748b; }
.s1-lc-stats { font-size: 10px; color: #94a3b8; margin-top: 2px; }
.s1-layer-arrow { display: flex; align-items: center; padding: 0 8px; flex-shrink: 0; }

/* ── Main Layout ── */
.s1-main-layout { display: flex; gap: 16px; align-items: flex-start; }
.s1-main-col { flex: 1; display: flex; flex-direction: column; gap: 16px; min-width: 0; }
.s1-sidebar { width: 300px; flex-shrink: 0; display: flex; flex-direction: column; gap: 16px; }

/* ── Card ── */
.s1-card {
  background: #ffffff; border: 1px solid #e2e8f0; border-radius: 14px; padding: 18px 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}
.s1-card-header {
  display: flex; align-items: center; gap: 8px;
  margin-bottom: 12px;
}
.s1-card-icon-wrap {
  width: 28px; height: 28px; border-radius: 8px;
  background: #eef2ff; border: 1px solid #c7d2fe;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.s1-card-title { font-size: 15px; font-weight: 700; color: #1e293b; flex: 1; }
.s1-card-badge {
  font-size: 10px; padding: 2px 8px; border-radius: 12px;
  background: linear-gradient(135deg, #eef2ff, #e0e7ff);
  color: #4f46e5; font-weight: 600; border: 1px solid #c7d2fe;
}
.s1-card-badge.s1-badge-green { background: #f0fdf4; color: #166534; border-color: #bbf7d0; }
.s1-card-desc { font-size: 12px; color: #64748b; margin: -4px 0 14px; line-height: 1.5; }
.s1-card-desc-small { font-size: 10px; color: #94a3b8; }

/* Learning Path */
.s1-path-steps { display: flex; flex-direction: column; gap: 0; }
.s1-path-item {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 12px; border-radius: 10px;
  transition: background 0.2s;
}
.s1-path-item.active { background: #f8fafc; }
.s1-path-item:hover { background: #f8fafc; }
.s1-path-circle {
  width: 28px; height: 28px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.s1-path-info { flex: 1; }
.s1-path-title { font-size: 13px; font-weight: 600; }
.s1-path-sub { font-size: 11px; color: #64748b; margin-top: 2px; }
.s1-path-mins { font-size: 10px; color: #94a3b8; white-space: nowrap; flex-shrink: 0; }
.s1-path-connector { height: 1px; background: #f1f5f9; margin: 0 12px; border: none; border-top: 1px dashed #e2e8f0; }
.s1-path-footer {
  display: flex; align-items: center; gap: 16px; margin-top: 12px;
  padding-top: 12px; border-top: 1px solid #f1f5f9;
  font-size: 12px; color: #64748b;
}
.s1-start-btn {
  margin-left: auto; padding: 8px 18px; border-radius: 20px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border: none; color: white; font-size: 12px; font-weight: 600;
  cursor: pointer; transition: all 0.2s;
  box-shadow: 0 2px 8px rgba(99,102,241,0.3);
}
.s1-start-btn:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(99,102,241,0.4); }

/* Training List */
.s1-train-list { display: flex; flex-direction: column; gap: 10px; }
.s1-train-item {
  display: flex; align-items: center; gap: 10px;
  padding: 10px; border-radius: 10px; border: 1px solid #f1f5f9;
  cursor: pointer; transition: all 0.2s;
}
.s1-train-item:hover { background: #f8fafc; border-color: #e2e8f0; transform: translateX(2px); }
.s1-train-icon { font-size: 20px; flex-shrink: 0; }
.s1-train-info { flex: 1; min-width: 0; }
.s1-train-title { font-size: 12px; font-weight: 600; color: #1e293b; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.s1-train-sub { font-size: 10px; color: #64748b; margin-top: 2px; line-height: 1.3; }
.s1-train-meta { display: flex; align-items: center; gap: 8px; margin-top: 4px; }
.s1-train-type { font-size: 9px; padding: 1px 6px; border-radius: 8px; background: #eef2ff; color: #4f46e5; font-weight: 600; }
.s1-train-mins { font-size: 9px; color: #94a3b8; }
.s1-train-rate { display: flex; flex-direction: column; align-items: center; gap: 3px; flex-shrink: 0; width: 40px; }
.s1-rate-num { font-size: 11px; font-weight: 700; color: #1e293b; }
.s1-rate-bar { width: 100%; height: 3px; background: #f1f5f9; border-radius: 3px; overflow: hidden; }
.s1-rate-fill { height: 100%; border-radius: 3px; transition: width 0.5s; }

/* History List */
.s1-view-all { margin-left: auto; font-size: 11px; color: #6366f1; background: none; border: none; cursor: pointer; font-weight: 600; }
.s1-history-list { display: flex; flex-direction: column; gap: 8px; }
.s1-history-item { display: flex; align-items: center; gap: 10px; padding: 8px 10px; border-radius: 8px; transition: background 0.2s; cursor: pointer; }
.s1-history-item:hover { background: #f8fafc; }
.s1-hi-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.s1-hi-info { flex: 1; }
.s1-hi-title { font-size: 12px; font-weight: 600; color: #1e293b; }
.s1-hi-time { font-size: 10px; color: #94a3b8; margin-top: 2px; }
.s1-hi-count { font-size: 10px; padding: 2px 8px; border-radius: 10px; font-weight: 600; flex-shrink: 0; }

/* Path card specific */
.s1-path-card { padding-bottom: 16px; }

/* Scheme switcher */
.s1-scheme-switcher {
  display: flex; align-items: center; gap: 10px;
  padding: 8px 12px; background: rgba(255,255,255,0.8); backdrop-filter: blur(8px);
  border: 1px solid #e0e7ff; border-radius: 12px;
}
.s1-ss-label { font-size: 11px; color: #94a3b8; font-weight: 600; white-space: nowrap; }
.s1-ss-tabs { display: flex; gap: 4px; flex-wrap: wrap; }
.s1-ss-tab {
  padding: 5px 12px; border-radius: 18px; background: transparent;
  border: 1px solid #e2e8f0; color: #64748b; font-size: 11px; font-weight: 600;
  cursor: pointer; transition: all 0.2s;
}
.s1-ss-tab:hover { background: #f1f5f9; color: #334155; border-color: #cbd5e1; }
.s1-ss-tab.active { background: linear-gradient(135deg, #6366f1, #0ea5e9); border-color: transparent; color: white; box-shadow: 0 2px 8px rgba(99,102,241,0.3); }
</style>
