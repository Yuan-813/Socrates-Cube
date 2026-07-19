<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import DiagnosisPanel from '@/components/DiagnosisPanel.vue'
import ZhiWenSuYuanModal from '@/components/ZhiWenSuYuanModal.vue'

const showZhiWen = ref(false)
const router = useRouter()

const schemes = [
  { path: '/diagnosis',      label: '原始版',  icon: '📋' },
  { path: '/diagnosis-s1',   label: '方案一',  icon: '☀️' },
  { path: '/diagnosis-s2',   label: '方案二',  icon: '🌌' },
  { path: '/diagnosis-s3',   label: '方案三',  icon: '✨' },
]
</script>

<template>
  <div class="space-y-6">
    <!-- 方案切换导航 -->
    <div class="scheme-switcher">
      <span class="scheme-label">UI 方案对比</span>
      <div class="scheme-tabs">
        <button
          v-for="s in schemes" :key="s.path"
          class="scheme-tab"
          :class="{ active: s.path === '/diagnosis' }"
          @click="router.push(s.path)"
        >
          {{ s.icon }} {{ s.label }}
        </button>
      </div>
    </div>

    <!-- ── 智问源 Banner ── -->
    <div class="zysy-banner" @click="showZhiWen = true">
      <div class="zysy-banner-left">
        <div class="zysy-banner-logo">
          <svg width="24" height="24" viewBox="0 0 28 28">
            <circle cx="14" cy="14" r="3.5" fill="#00C8FF"/>
            <circle cx="4"  cy="7"  r="2.2" fill="#00C8FF" opacity="0.75"/>
            <circle cx="24" cy="7"  r="2.2" fill="#00C8FF" opacity="0.75"/>
            <circle cx="4"  cy="21" r="2.2" fill="#00C8FF" opacity="0.75"/>
            <circle cx="24" cy="21" r="2.2" fill="#00C8FF" opacity="0.75"/>
            <line x1="14" y1="14" x2="4"  y2="7"  stroke="#00C8FF" stroke-width="1.2" opacity="0.55"/>
            <line x1="14" y1="14" x2="24" y2="7"  stroke="#00C8FF" stroke-width="1.2" opacity="0.55"/>
            <line x1="14" y1="14" x2="4"  y2="21" stroke="#00C8FF" stroke-width="1.2" opacity="0.55"/>
            <line x1="14" y1="14" x2="24" y2="21" stroke="#00C8FF" stroke-width="1.2" opacity="0.55"/>
          </svg>
        </div>
        <div>
          <div class="zysy-banner-title">智问源</div>
          <div class="zysy-banner-sub">AI 深度诊断 · 精析协议真知 · 点击启动</div>
        </div>
      </div>
      <div class="zysy-banner-right">
        <span class="zysy-banner-desc">TCP/IP · TLS · HTTP/3 · QUIC · DNS · IPv6</span>
        <button class="zysy-launch-btn" @click.stop="showZhiWen = true">
          <svg width="12" height="12" viewBox="0 0 14 14">
            <path d="M7,0.5 L8.8,5.2 L13.5,7 L8.8,8.8 L7,13.5 L5.2,8.8 L0.5,7 L5.2,5.2 Z" fill="#00C8FF"/>
          </svg>
          启动诊断
        </button>
      </div>
    </div>

    <!-- ── 三层引擎条 ── -->
    <div class="diagnosis-engine-bar">
      <div class="engine-step">
        <div class="step-icon">L1</div>
        <div class="step-info">
          <div class="step-name">表面错误识别</div>
          <div class="step-desc">9种错误类型 · 6种 RFC 标准</div>
        </div>
      </div>
      <div class="engine-arrow">→</div>
      <div class="engine-step">
        <div class="step-icon">L2</div>
        <div class="step-info">
          <div class="step-name">根因溯源分析</div>
          <div class="step-desc">20 KP 节点 · 48 ACU 认知单元</div>
        </div>
      </div>
      <div class="engine-arrow">→</div>
      <div class="engine-step">
        <div class="step-icon">L3</div>
        <div class="step-info">
          <div class="step-name">误区模式匹配</div>
          <div class="step-desc">8种误区模式 · 150+ 误解条目</div>
        </div>
      </div>
    </div>

    <div class="card">
      <h2 class="section-title">认知诊断报告</h2>
      <p class="section-desc">三层诊断引擎：表面错误识别 → 根因溯源分析 → 误解模式匹配，基于谢希仁《计算机网络》第8版 &amp; IETF RFC 标准体系</p>
      <DiagnosisPanel />
    </div>

    <!-- 智问源弹窗 -->
    <ZhiWenSuYuanModal :visible="showZhiWen" @close="showZhiWen = false" />

  </div>
</template>

<style scoped>
/* 方案切换导航 */
.scheme-switcher {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
}
.scheme-label { font-size: 11px; color: #94a3b8; font-weight: 600; white-space: nowrap; }
.scheme-tabs { display: flex; gap: 4px; flex-wrap: wrap; }
.scheme-tab {
  padding: 6px 14px; border-radius: 20px;
  background: transparent; border: 1px solid #e2e8f0;
  color: #64748b; font-size: 11px; font-weight: 600;
  cursor: pointer; transition: all 0.2s;
}
.scheme-tab:hover { background: #f1f5f9; border-color: #cbd5e1; color: #334155; }
.scheme-tab.active { background: #6366f1; border-color: #6366f1; color: white; box-shadow: 0 2px 8px rgba(99,102,241,0.3); }

/* 已有样式 */
.diagnosis-engine-bar {
  display: flex; align-items: center; gap: 0;
  background: linear-gradient(135deg, #1e293b 0%, #1e3a5f 100%);
  border-radius: 12px; padding: 14px 20px;
  box-shadow: 0 4px 16px rgba(79,70,229,0.2);
}
.engine-step { flex: 1; display: flex; align-items: center; gap: 10px; }
.step-icon {
  width: 36px; height: 36px; border-radius: 8px;
  background: rgba(99,102,241,0.3); border: 1px solid rgba(99,102,241,0.5);
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 800; color: #a5b4fc; flex-shrink: 0;
}
.step-name  { font-size: 12px; font-weight: 700; color: #e2e8f0; margin-bottom: 2px; }
.step-desc  { font-size: 10px; color: #94a3b8; }
.engine-arrow { color: #4f46e5; font-size: 18px; font-weight: bold; padding: 0 12px; flex-shrink: 0; }

/* 智问源入口 Banner */
.zysy-banner {
  display: flex; align-items: center; justify-content: space-between;
  background: linear-gradient(135deg, #07101E 0%, #0B1828 100%);
  border: 1px solid #1E3A58; border-radius: 12px;
  padding: 14px 20px; cursor: pointer;
  box-shadow: 0 0 0 1px rgba(0,200,255,0.1), 0 4px 20px rgba(0,0,0,0.3);
  transition: all 0.2s;
  position: relative; overflow: hidden;
}
.zysy-banner::before {
  content: '';
  position: absolute; top: 0; left: 0; right: 0; height: 1px;
  background: linear-gradient(90deg, transparent, rgba(0,200,255,0.5), transparent);
}
.zysy-banner:hover {
  border-color: rgba(0,200,255,0.45);
  box-shadow: 0 0 24px rgba(0,200,255,0.12), 0 4px 20px rgba(0,0,0,0.3);
  transform: translateY(-1px);
}
.zysy-banner-left { display: flex; align-items: center; gap: 14px; }
.zysy-banner-logo {
  width: 44px; height: 44px; border-radius: 10px;
  background: linear-gradient(135deg, #002B40, #004D66);
  border: 1.5px solid #00C8FF;
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 0 14px rgba(0,200,255,0.3); flex-shrink: 0;
  animation: banner-pulse 2.4s ease-in-out infinite;
}
.zysy-banner-title {
  font-family: 'Courier New', monospace;
  font-size: 18px; font-weight: 800; color: #fff;
  letter-spacing: 3px;
  text-shadow: 0 0 16px rgba(0,200,255,0.4);
}
.zysy-banner-sub { font-size: 11px; color: #5E88B0; margin-top: 2px; letter-spacing: 1px; }
.zysy-banner-right { display: flex; align-items: center; gap: 14px; }
.zysy-banner-desc { font-size: 11px; color: #344D6A; letter-spacing: 0.5px; }
.zysy-launch-btn {
  padding: 8px 20px; border-radius: 20px;
  background: linear-gradient(135deg, #004D6A, #006E8F);
  border: 1px solid #00C8FF; color: #fff;
  cursor: pointer; font-size: 12px; font-weight: 600;
  display: flex; align-items: center; gap: 6px;
  box-shadow: 0 0 12px rgba(0,200,255,0.2);
  transition: all 0.2s; white-space: nowrap;
}
.zysy-launch-btn:hover {
  box-shadow: 0 0 20px rgba(0,200,255,0.4);
  transform: translateY(-1px);
}
@keyframes banner-pulse {
  0%,100% { box-shadow: 0 0 10px rgba(0,200,255,0.3); }
  50%      { box-shadow: 0 0 20px rgba(0,200,255,0.6); }
}
</style>
