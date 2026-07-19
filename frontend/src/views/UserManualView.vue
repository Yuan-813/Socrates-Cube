<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const modules = [
  {
    icon: '🔍',
    title: '智能诊断',
    desc: '三层认知诊断引擎，精准定位概念错误与认知偏差，提供个性化纠错方案',
    tag: '核心功能',
    color: '#ef4444',
    bg: '#fef2f2',
    path: '/diagnosis',
  },
  {
    icon: '💬',
    title: 'AI 智能对话',
    desc: '多 Agent 协同的 AI 辅导助手，结合知识图谱即时回答计算机网络问题',
    tag: '核心功能',
    color: '#3b82f6',
    bg: '#eff6ff',
    path: '/chat',
  },
  {
    icon: '🌐',
    title: '知识图谱',
    desc: '可视化计算机网络知识体系，直观展示概念关联，支持 AI 驱动图谱生成',
    tag: '特色功能',
    color: '#06b6d4',
    bg: '#ecfeff',
    path: '/kg-assist',
  },
  {
    icon: '🎬',
    title: '协议仿真',
    desc: 'TCP 握手、滑动窗口、HTTP 报文等核心协议动态可视化演示，辅助深度理解',
    tag: '特色功能',
    color: '#ec4899',
    bg: '#fdf4ff',
    path: '/simulator',
  },
  {
    icon: '🗺️',
    title: '学习路径',
    desc: '基于知识图谱依赖与个人画像，自动规划个性化学习序列，精准推送资源',
    tag: '核心功能',
    color: '#8b5cf6',
    bg: '#faf5ff',
    path: '/path',
  },
  {
    icon: '📝',
    title: '证书考试',
    desc: 'HCIA-Datacom 等网络认证模拟题库，智能出题、自动阅卷、成绩分析',
    tag: '备考工具',
    color: '#f59e0b',
    bg: '#fffbeb',
    path: '/exam',
  },
]

const steps = [
  { num: '01', title: '注册登录', desc: '使用账号密码、手机验证码或游客模式快速进入系统', icon: '🔑' },
  { num: '02', title: '完成 AI 引导', desc: 'Alice 将引导你完成身份定位、能力测试与兴趣分析，生成专属学习方案', icon: '🤖' },
  { num: '03', title: '开始 AI 诊断', desc: '进入诊断面板，通过问答让 AI 精准识别你的薄弱知识点', icon: '🔍' },
  { num: '04', title: '查看学习路径', desc: '系统基于诊断结果自动生成可视化学习路径，按节点逐步推进', icon: '🗺️' },
]

const faqs = ref([
  {
    q: '如何切换 AI 助手的学习风格？',
    a: '在智能对话页面左下角的 Agent 选择器中，可切换苏格拉底（引导提问）、学术型（深度讲解）、实践型（动手示例）等多种学习风格。',
  },
  {
    q: '我的学习数据是如何计算的？',
    a: 'AI 通过分析你的对话内容、答题情况和诊断结果，综合计算 8 维能力评分，数据会在每次对话后自动更新。',
  },
  {
    q: '协议仿真支持哪些协议？',
    a: '目前支持 TCP 三次握手/四次挥手、滑动窗口与拥塞控制、HTTP/1.1 请求响应，以及 DNS 查询等核心协议的动画演示。',
  },
  {
    q: '如何上传自己的 PDF 教材？',
    a: '进入"PDF 知识库"页面，点击上传按钮选择 PDF 文件。系统会自动提取内容并建立向量索引，之后可以用自然语言对教材内容提问。',
  },
  {
    q: '学习路径如何更新？',
    a: '每次完成诊断或对话后，系统会自动重新评估你的知识状态并更新学习路径。你也可以在路径页面手动刷新或调整优先级。',
  },
  {
    q: '游客模式与注册账号有什么区别？',
    a: '游客模式可以体验全部功能，但学习数据不会持久化保存。注册账号后，你的学习画像、对话记录、诊断结果将永久保留，AI 辅导效果也更精准。',
  },
  {
    q: '如何查看 AI 的推理过程？',
    a: '在 AI 对话时，点击消息右下角的"Agent 执行链路"可以看到 Orchestrator、Profiler、Diagnosis 等各 Agent 的执行状态与输出。',
  },
  {
    q: '能否进行 AI 面试模拟？',
    a: '是的，进入"AI 面试"页面，可以模拟网络工程师技术面试。AI 会针对你的知识薄弱点出题，并给出详细的面试反馈报告。',
  },
])
</script>

<template>
  <div class="manual-view">

    <!-- 页头 Hero -->
    <section class="manual-hero">
      <div class="hero-glow" />
      <div class="hero-content">
        <div class="hero-badge">📖 使用手册</div>
        <h1 class="hero-title">如何使用 <span class="title-highlight">Socrates Cube</span>？</h1>
        <p class="hero-desc">
          全面了解系统的每个功能模块，快速上手 AI 驱动的计算机网络学习体验
        </p>
      </div>
    </section>

    <!-- 功能模块导览 -->
    <section>
      <div class="sec-head">
        <h2 class="sec-title">🧩 功能模块导览</h2>
        <p class="sec-sub">六大核心模块，覆盖学习全流程</p>
      </div>
      <div class="module-grid">
        <div
          v-for="mod in modules"
          :key="mod.title"
          class="module-card"
          :style="{ background: mod.bg }"
          @click="router.push(mod.path)"
        >
          <div class="module-top">
            <div class="module-icon">{{ mod.icon }}</div>
            <span class="module-tag" :style="{ color: mod.color, background: mod.color + '18', border: '1px solid ' + mod.color + '33' }">
              {{ mod.tag }}
            </span>
          </div>
          <h3 class="module-title" :style="{ color: mod.color }">{{ mod.title }}</h3>
          <p class="module-desc">{{ mod.desc }}</p>
          <div class="module-go" :style="{ color: mod.color }">
            立即体验 →
          </div>
        </div>
      </div>
    </section>

    <!-- 快速上手步骤 -->
    <section>
      <div class="sec-head">
        <h2 class="sec-title">🚀 快速上手</h2>
        <p class="sec-sub">4 步开启个性化学习之旅</p>
      </div>
      <div class="steps-row">
        <div
          v-for="(step, idx) in steps"
          :key="step.num"
          class="step-item"
        >
          <div class="step-connector" v-if="idx < steps.length - 1" />
          <div class="step-circle">
            <span class="step-icon">{{ step.icon }}</span>
          </div>
          <div class="step-num">{{ step.num }}</div>
          <div class="step-title">{{ step.title }}</div>
          <div class="step-desc">{{ step.desc }}</div>
        </div>
      </div>
    </section>

    <!-- FAQ -->
    <section>
      <div class="sec-head">
        <h2 class="sec-title">❓ 常见问题</h2>
        <p class="sec-sub">快速解答使用过程中的疑惑</p>
      </div>
      <div class="faq-list">
        <el-collapse accordion>
          <el-collapse-item
            v-for="(faq, idx) in faqs"
            :key="idx"
            :name="idx"
          >
            <template #title>
              <div class="faq-q">
                <span class="faq-q-num">Q{{ idx + 1 }}</span>
                {{ faq.q }}
              </div>
            </template>
            <div class="faq-a">{{ faq.a }}</div>
          </el-collapse-item>
        </el-collapse>
      </div>
    </section>

    <!-- 底部提示 -->
    <div class="manual-footer">
      <div class="footer-tip">
        <el-icon size="16" color="#6366f1"><InfoFilled /></el-icon>
        <span>如遇问题，可在 <router-link to="/chat">AI 对话</router-link> 中直接向 AI 助手提问</span>
      </div>
      <router-link to="/" class="back-home">← 返回首页</router-link>
    </div>

  </div>
</template>

<style scoped>
.manual-view {
  display: flex;
  flex-direction: column;
  gap: 28px;
  max-width: 1100px;
  margin: 0 auto;
  width: 100%;
}

/* Hero */
.manual-hero {
  position: relative;
  background: linear-gradient(135deg, #1e3a8a 0%, #3730a3 50%, #4c1d95 100%);
  border-radius: 20px;
  padding: 48px 40px;
  color: white;
  overflow: hidden;
}

.hero-glow {
  position: absolute;
  top: -60px; right: -60px;
  width: 240px; height: 240px;
  background: radial-gradient(circle, rgba(167,139,250,0.3) 0%, transparent 70%);
  pointer-events: none;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 14px;
  background: rgba(255,255,255,0.12);
  border: 1px solid rgba(255,255,255,0.2);
  border-radius: 20px;
  font-size: 12px;
  color: rgba(255,255,255,0.9);
  margin-bottom: 16px;
}

.hero-title {
  font-size: 32px;
  font-weight: 800;
  margin-bottom: 12px;
  letter-spacing: -0.5px;
}

.title-highlight {
  background: linear-gradient(135deg, #93c5fd, #c4b5fd);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-desc {
  font-size: 14.5px;
  color: rgba(255,255,255,0.75);
  max-width: 560px;
  line-height: 1.7;
}

/* Section */
.sec-head { margin-bottom: 16px; }

.sec-title {
  font-size: 18px;
  font-weight: 800;
  color: #1e293b;
  margin-bottom: 4px;
}

.sec-sub {
  font-size: 13px;
  color: #64748b;
}

/* Module Grid */
.module-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
}

.module-card {
  border-radius: 16px;
  border: 1px solid #e8eef8;
  padding: 20px;
  cursor: pointer;
  transition: all 0.22s;
  box-shadow: 0 2px 6px rgba(0,0,0,0.03);
}

.module-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 28px rgba(0,0,0,0.1);
}

.module-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.module-icon { font-size: 28px; }

.module-tag {
  font-size: 10px;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 6px;
  letter-spacing: 0.3px;
}

.module-title {
  font-size: 15px;
  font-weight: 700;
  margin-bottom: 8px;
}

.module-desc {
  font-size: 12.5px;
  color: #64748b;
  line-height: 1.65;
  margin-bottom: 14px;
}

.module-go {
  font-size: 12px;
  font-weight: 700;
  opacity: 0;
  transform: translateX(-4px);
  transition: all 0.2s;
}

.module-card:hover .module-go {
  opacity: 1;
  transform: translateX(0);
}

/* Steps */
.steps-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  position: relative;
}

.step-item {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  background: white;
  border-radius: 16px;
  border: 1px solid #e8eef8;
  padding: 24px 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  transition: all 0.2s;
}

.step-item:hover { transform: translateY(-3px); box-shadow: 0 8px 20px rgba(0,0,0,0.08); }

.step-connector {
  display: none;
}

.step-circle {
  width: 56px;
  height: 56px;
  background: linear-gradient(135deg, #eff6ff, #f5f3ff);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26px;
  margin-bottom: 10px;
  border: 2px solid #e2e8f0;
}

.step-num {
  font-size: 10px;
  font-weight: 800;
  color: #6366f1;
  letter-spacing: 1px;
  margin-bottom: 4px;
}

.step-title {
  font-size: 14px;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 6px;
}

.step-desc {
  font-size: 12px;
  color: #64748b;
  line-height: 1.6;
}

/* FAQ */
.faq-list {
  background: white;
  border-radius: 16px;
  border: 1px solid #e8eef8;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

.faq-q {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
}

.faq-q-num {
  font-size: 11px;
  font-weight: 700;
  color: #6366f1;
  background: #eff0ff;
  padding: 2px 7px;
  border-radius: 6px;
  flex-shrink: 0;
  letter-spacing: 0.3px;
}

.faq-a {
  font-size: 13.5px;
  color: #475569;
  line-height: 1.75;
  padding: 4px 8px 4px 24px;
}

/* Footer */
.manual-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  background: white;
  border-radius: 14px;
  border: 1px solid #e8eef8;
  flex-wrap: wrap;
  gap: 10px;
}

.footer-tip {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #64748b;
}

.footer-tip a {
  color: #6366f1;
  text-decoration: none;
  font-weight: 600;
}

.back-home {
  font-size: 13px;
  color: #6366f1;
  text-decoration: none;
  font-weight: 600;
  transition: opacity 0.2s;
}

.back-home:hover { opacity: 0.75; }

/* 响应式 */
@media (max-width: 900px) {
  .module-grid { grid-template-columns: 1fr 1fr; }
  .steps-row { grid-template-columns: 1fr 1fr; }
}

@media (max-width: 640px) {
  .module-grid { grid-template-columns: 1fr; }
  .steps-row { grid-template-columns: 1fr; }
  .hero-title { font-size: 24px; }
}
</style>
