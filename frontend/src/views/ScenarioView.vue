<script setup lang="ts">
import { ref, computed } from 'vue'
import { useUserStore } from '@/stores/userStore'

const userStore = useUserStore()

// ── 场景定义 ──────────────────────────────────────────────────────────────────
const SCENARIOS = [
  {
    id: 'isp_fault',
    title: '运营商网络故障排查',
    description: '用户上报网络中断，IT 经理与网络工程师协同排查 BGP 路由黑洞问题',
    roles: ['甲方IT经理', '乙方网络工程师'],
    topic: 'BGP路由故障排查',
    theme: 'BGP 路由故障 · 企业网络运维实战',
    difficulty: '中级',
    icon: '🔧',
    color: 'from-orange-500 to-red-500',
    stage: '（网络运维中心）',
  },
  {
    id: 'datacenter_design',
    title: '数据中心网络设计评审',
    description: '架构师向客户团队提案三层数据中心组网方案，你需要理解并提出问题',
    roles: ['网络架构师', '客户IT总监'],
    topic: '数据中心三层组网架构',
    theme: '数据中心三层架构 · 组网方案设计',
    difficulty: '进阶',
    icon: '🏗️',
    color: 'from-blue-500 to-indigo-600',
    stage: '（会议室）',
  },
  {
    id: 'security_incident',
    title: 'DDoS攻击应急响应',
    description: '企业遭受大规模 DDoS 攻击，安全团队实时响应并与 ISP 协调清洗',
    roles: ['安全工程师', 'ISP客服专员'],
    topic: 'DDoS攻击防护与清洗',
    theme: 'DDoS 攻击防护 · 安全应急响应',
    difficulty: '进阶',
    icon: '🛡️',
    color: 'from-red-500 to-pink-600',
    stage: '（安全运营中心）',
  },
  {
    id: 'hcia_mock',
    title: 'HCIA认证备考答疑',
    description: '考证冲刺阶段，学长帮你梳理 OSPF 路由协议的核心考点',
    roles: ['备考学长', '学员'],
    topic: 'OSPF协议核心考点',
    theme: 'OSPF 路由协议 · HCIA 备考冲刺',
    difficulty: '入门',
    icon: '📋',
    color: 'from-emerald-500 to-teal-600',
    stage: '（学习室）',
  },
  {
    id: 'wireshark_lab',
    title: 'Wireshark 抓包分析实战',
    description: '安全工程师展示使用 Wireshark 分析 TCP 三次握手、TLS 加密过程与 HTTP 包结构',
    roles: ['安全工程师', '实习生'],
    topic: 'Wireshark抓包分析与TCP/TLS协议',
    theme: 'Wireshark 抓包 · TCP/TLS 协议分析',
    difficulty: '中级',
    icon: '🔎',
    color: 'from-violet-500 to-purple-600',
    stage: '（实验室）',
  },
  {
    id: 'sdn_design',
    title: 'SDN/NFV 方案评审',
    description: '网络架构师展示基于 OpenFlow 的 SDN 改造方案，客户团队提问并评估实施风险',
    roles: ['网络架构师', '客户CTO'],
    topic: 'SDN/NFV与OpenFlow架构',
    theme: 'SDN/NFV 改造 · OpenFlow 架构设计',
    difficulty: '进阶',
    icon: '🖧',
    color: 'from-cyan-500 to-blue-600',
    stage: '（技术评审会议室）',
  },
  {
    id: 'socrates_tcp',
    title: '苏格拉底 TCP 引导式诊断',
    description: '苏格拉底老师通过追问引导你发现 TCP 三次握手的深层机制，揭示序列号、半连接队列与拥塞控制的认知盲区',
    roles: ['苏格拉底老师', '学员'],
    topic: 'TCP三次握手与协议机制',
    theme: 'TCP 握手深度解析 · 苏格拉底式引导教学',
    difficulty: '中级',
    icon: '🏛️',
    color: 'from-cyan-500 to-teal-600',
    stage: '（网络控制中心）',
  },
]

// ── 角色 → 图片 映射 ─────────────────────────────────────────────────────────
function getCharacterImg(role: string): string {
  if (role.includes('苏格拉底')) return '/images/virtual_teacher.png'
  if (role.includes('架构师') || role.includes('工程师')) return '/images/characters/engineer.png'
  if (role.includes('经理') || role.includes('总监') || role.includes('CTO')) return '/images/characters/manager.png'
  if (role.includes('安全') || role.includes('ISP')) return '/images/characters/security.png'
  return '/images/characters/student.png'
}

// ── 类型 ─────────────────────────────────────────────────────────────────────
type Phase = 'select' | 'immersive'

interface ScriptStep {
  id: string
  character: string
  stage: string
  text: string
  type: 'dialog' | 'quiz'
  options?: string[]
  answer?: string
}

// ── State ─────────────────────────────────────────────────────────────────────
const phase           = ref<Phase>('select')
const selectedScenario = ref<typeof SCENARIOS[0] | null>(null)
const script          = ref<ScriptStep[]>([])
const currentStep     = ref(0)
const isLoadingScript = ref(false)
const quizAnswered    = ref<string | null>(null)
const quizCorrect     = ref<boolean | null>(null)

// ── Computed ──────────────────────────────────────────────────────────────────
const step = computed(() => script.value[currentStep.value] ?? null)
const totalSteps = computed(() => script.value.length)
const characterImg = computed(() =>
  step.value ? getCharacterImg(step.value.character) : ''
)
const isLast = computed(() => currentStep.value >= totalSteps.value - 1)

// canNext 逻辑已内联到模板 v-if 判断中

// ── Methods ───────────────────────────────────────────────────────────────────
async function selectScenario(s: typeof SCENARIOS[0]) {
  selectedScenario.value = s
  phase.value = 'immersive'
  await loadScript(s)
}

async function loadScript(s: typeof SCENARIOS[0]) {
  isLoadingScript.value = true
  script.value = []
  currentStep.value = 0
  quizAnswered.value = null

  const systemPrompt = `你是一个情景教学剧本生成器。请为以下网络技术教学情景生成一个结构化剧本。
场景：${s.title}
主题：${s.topic}
角色：${s.roles.join('、')}
背景：${s.stage}

要求：
- 生成 12-16 步对话，交替展示两个角色的对话
- 每隔 4-5 步插入一道考察题（type: quiz），考察关键知识点
- 对话要口语化、专业准确，每句2-4句话
- 场景说明用中文括号，如"（机房内）"
- 严格输出 JSON 数组，每项格式：
  {"character":"角色名","stage":"场景说明","text":"对话内容","type":"dialog"}
  或
  {"character":"考察题","stage":"","text":"题目内容","type":"quiz","options":["选项A","选项B","选项C"]}
- 只输出 JSON 数组，不加任何其他内容`

  try {
    const r = await fetch('/api/v1/chat/message', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: `scenario_${s.id}_${Date.now()}`,
        user_id: userStore.userId,
        message: systemPrompt,
        agent_persona: 'expert',
      }),
    })
    const data = await r.json()
    const raw = data.reply || '[]'

    // 提取 JSON
    const match = raw.match(/\[[\s\S]*\]/)
    if (match) {
      const parsed: Omit<ScriptStep, 'id'>[] = JSON.parse(match[0])
      script.value = parsed.map((s, i) => ({ ...s, id: `step-${i}` }))
    }
  } catch {/* ignore */}

  // 保底：生成默认剧本
  if (script.value.length < 3) {
    script.value = buildFallbackScript(s)
  }

  isLoadingScript.value = false
}

function buildFallbackScript(s: typeof SCENARIOS[0]): ScriptStep[] {
  // 苏格拉底场景专属保底剧本
  if (s.id === 'socrates_tcp') {
    return [
      { id: 's0', character: '苏格拉底老师', stage: s.stage, text: '我想问你一个问题：TCP 三次握手中，客户端发送的第一个 SYN 包的序列号是多少？你知道吗？', type: 'dialog' },
      { id: 's1', character: '学员', stage: s.stage, text: '应该是 0 吧？连接开始时从 0 开始计数。', type: 'dialog' },
      { id: 's2', character: '苏格拉底老师', stage: s.stage, text: '很有趣的猜测。但 RFC 9293 说：序列号是随机生成的（ISN）。这个设计是为什么？如果从 0 开始，会有什么问题？', type: 'dialog' },
      { id: 's3', character: '学员', stage: s.stage, text: '如果从 0 开始…也许与之前残留的旧连接包混淆？', type: 'dialog' },
      { id: 's4', character: '苏格拉底老师', stage: s.stage, text: '正是如此！这就是“过期段 TCP 包巧合此起”的根源。现在评估一下你对序列号的理解。', type: 'dialog' },
      { id: 'sq0', character: '考察题', stage: '', text: 'TCP ISN（初始序列号）随机化的主要目的是？', type: 'quiz', options: ['防止旧连接残留包干扰新连接', '加快三次握手速度', '减少拥塞窗口大小'] },
      { id: 's5', character: '苏格拉底老师', stage: s.stage, text: '再问你一个：服务端收到 SYN 包后，会建立什么数据结构？它马上就认为连接建立了吗？', type: 'dialog' },
      { id: 's6', character: '学员', stage: s.stage, text: '不是就建立了吧？服务端回了 SYN+ACK 就表示连接好了。', type: 'dialog' },
      { id: 's7', character: '苏格拉底老师', stage: s.stage, text: '注意！服务端此刻建立的是「半连接」(SYN_RCVD)，存入半连接队列。只有收到第三个 ACK，才进入 ESTABLISHED 状态。这个区别至关重要！', type: 'dialog' },
      { id: 's8', character: '学员', stage: s.stage, text: '原来如此！所以 SYN Flood 攻击就是利用大量 SYN 塑满半连接队列，让服务端资源耗尽。', type: 'dialog' },
      { id: 'sq1', character: '考察题', stage: '', text: 'SYN Flood 攻击的核心原理是？', type: 'quiz', options: ['塑满半连接队列消耗服务端资源', '伪造 ACK 数据包重放', '占用全部带宽导致拥塞'] },
      { id: 's9', character: '苏格拉底老师', stage: s.stage, text: '非常好！你已经触及了问题的本质。现在让我们谈谈拥塞控制——慢启动、拥塞避免算法。你认为当网络拥塞时，发送方应如何感知？', type: 'dialog' },
      { id: 's10', character: '学员', stage: s.stage, text: '也许通过丢包？超时重传？', type: 'dialog' },
      { id: 's11', character: '苏格拉底老师', stage: s.stage, text: '正确！TCP 用丢包作为拥塞信号，不需要其他反馈机制。这让 TCP 在各种网络璯境下都能自适应。记住：个人科学日报也是这样——既要对失败敏感，也要在成功时扫荷加速。', type: 'dialog' },
      { id: 'sq2', character: '考察题', stage: '', text: 'TCP 慢启动阶段，拥塞窗口的如何变化？', type: 'quiz', options: ['每收到一个 ACK，拥塞窗口翻倍', '每收到一个 ACK，拥塞窗口 +1', '拥塞窗口保持不变，直到超时'] },
      { id: 's12', character: '苏格拉底老师', stage: s.stage, text: '你现在已经理解了 TCP 三次握手的核心词汇：不仅是“三次握手廻就建立连接”，而是“双方同步序列号、确认双向信道可靠性”的精密设计。这就是苏格拉底式教学的刀9道：不告诉你答案，而是带你自己发现真相。', type: 'dialog' },
    ]
  }

  const [r0, r1] = s.roles
  return [
    { id: 'f0', character: r0, stage: s.stage, text: `好的，我们今天来讨论「${s.topic}」的实际应用场景。`, type: 'dialog' },
    { id: 'f1', character: r1, stage: s.stage, text: `了解，${s.topic}在实际工程中确实是核心知识点，我来分析一下...`, type: 'dialog' },
    { id: 'f2', character: r0, stage: s.stage, text: `首先我们需要理解基本原理，然后结合具体案例来看。`, type: 'dialog' },
    { id: 'f3', character: '考察题', stage: '', text: `关于「${s.topic}」，下列说法正确的是？`, type: 'quiz', options: ['理解数据包转发过程', '忽略网络分层结构', '只关注物理连接'] },
    { id: 'f4', character: r1, stage: s.stage, text: `非常好。接下来我们看具体的配置步骤和注意事项。`, type: 'dialog' },
    { id: 'f5', character: r0, stage: s.stage, text: `这个案例很典型，在实际工程项目中这类问题经常出现，需要系统化解决。`, type: 'dialog' },
    { id: 'f6', character: r1, stage: s.stage, text: `总结一下今天的重点：掌握原理、熟悉配置、结合实践，这是学好网络技术的关键。`, type: 'dialog' },
  ]
}

function goNext() {
  if (isLast.value) return
  quizAnswered.value = null
  quizCorrect.value = null
  currentStep.value++
}

function answerQuiz(option: string) {
  if (quizAnswered.value) return
  quizAnswered.value = option
  // 第一个选项视为正确答案（简单演示）
  quizCorrect.value = option === step.value?.options?.[0]
}

function exitImmersive() {
  phase.value = 'select'
  selectedScenario.value = null
  script.value = []
  currentStep.value = 0
}
</script>

<template>
  <!-- ======================================================= -->
  <!-- 场景选择界面                                              -->
  <!-- ======================================================= -->
  <template v-if="phase === 'select'">
    <div class="space-y-5">
      <div class="card">
        <h2 class="section-title">🎭 情景化角色对话</h2>
        <p class="section-desc">
          通过真实业务场景对话，沉浸式理解网络技术——观摩专家对话，在视觉小说式叙事中掌握核心知识
        </p>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div
          v-for="s in SCENARIOS"
          :key="s.id"
          class="scenario-card cursor-pointer"
          @click="selectScenario(s)"
        >
          <div :class="`bg-gradient-to-br ${s.color} p-4 rounded-xl text-white mb-3`">
            <div class="text-3xl mb-2">{{ s.icon }}</div>
            <h3 class="font-bold text-base">{{ s.title }}</h3>
            <p class="text-white/80 text-xs mt-1">{{ s.description }}</p>
          </div>
          <div class="space-y-2 px-1">
            <div class="flex items-center gap-2 text-xs text-gray-500">
              <span class="font-medium text-gray-600">角色：</span>
              <span v-for="r in s.roles" :key="r" class="bg-gray-100 px-2 py-0.5 rounded-full">{{ r }}</span>
            </div>
            <div class="flex items-center justify-between text-xs">
              <span class="text-gray-400">主题：{{ s.topic }}</span>
              <span class="px-2 py-0.5 rounded-full text-xs font-medium"
                :class="s.difficulty === '入门' ? 'bg-emerald-50 text-emerald-600'
                  : s.difficulty === '中级' ? 'bg-amber-50 text-amber-600'
                  : 'bg-red-50 text-red-600'">
                {{ s.difficulty }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </template>

  <!-- ======================================================= -->
  <!-- 沉浸式视觉小说界面                                         -->
  <!-- ======================================================= -->
  <Teleport to="body">
    <Transition name="imm-fade">
      <div v-if="phase === 'immersive' && selectedScenario" class="imm-root">

        <!-- ── 背景层：深色科技感服务器机房 ──────────────────────── -->
        <div class="imm-bg">
          <!-- 网格纹理 -->
          <svg class="imm-grid" xmlns="http://www.w3.org/2000/svg" width="100%" height="100%">
            <defs>
              <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(100,130,200,0.08)" stroke-width="1"/>
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#grid)"/>
          </svg>
          <!-- 顶部光晕 -->
          <div class="imm-glow-top"/>
          <!-- 右侧机柜装饰 -->
          <div class="imm-rack-right">
            <div v-for="i in 14" :key="i" class="imm-rack-unit" :style="{ animationDelay: (i * 0.3) + 's' }"/>
          </div>
          <!-- 左侧装饰线路 -->
          <div class="imm-wires"/>
        </div>

        <!-- ── 关闭按钮 ─────────────────────────────────────────── -->
        <button class="imm-close" @click="exitImmersive">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
            <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>

        <!-- ── 场景名 + 进度（顶部）──────────────────────────────── -->
        <div class="imm-topbar">
          <span class="imm-scene-tag">{{ selectedScenario.icon }} {{ selectedScenario.title }}</span>
          <span class="imm-diff-tag"
            :class="selectedScenario.difficulty === '入门' ? 'green' : selectedScenario.difficulty === '中级' ? 'amber' : 'red'">
            {{ selectedScenario.difficulty }}
          </span>
        </div>

        <!-- ── 人物区 ───────────────────────────────────────────── -->
        <div class="imm-character-area">
          <!-- Loading 时显示骨架 -->
          <Transition name="char-fade" mode="out-in">
            <div v-if="isLoadingScript" key="loading" class="imm-loading-char">
              <div class="imm-char-skeleton"/>
              <p class="imm-loading-text">剧本生成中…</p>
            </div>
            <img
              v-else-if="step && characterImg"
              :key="step.id + characterImg"
              :src="characterImg"
              :alt="step.character"
              class="imm-char-img"
            />
          </Transition>
        </div>

        <!-- ── 底部对话面板 ──────────────────────────────────────── -->
        <div class="imm-dialogue-panel">

          <!-- 普通对话 -->
          <template v-if="step && step.type === 'dialog'">
            <div class="imm-dialogue-inner">
              <!-- 角色名行 -->
              <div class="imm-role-row">
                <span class="imm-role-bar"/>
                <span class="imm-role-name">{{ step.character }}</span>
              </div>
              <!-- 对话内容 -->
              <Transition name="text-slide" mode="out-in">
                <p :key="step.id" class="imm-text">
                  <span v-if="step.stage" class="imm-stage">{{ step.stage }}</span>
                  {{ step.text }}
                </p>
              </Transition>
            </div>

            <!-- 底部导航栏 -->
            <div class="imm-nav">
              <div class="imm-theme-title">── {{ selectedScenario.theme }} ──</div>
              <div class="imm-progress-info">
                <span class="imm-progress-num">{{ currentStep + 1 }}/{{ totalSteps }}</span>
                <div class="imm-progress-dots">
                  <span v-for="i in Math.min(totalSteps, 12)" :key="i"
                    class="imm-dot" :class="{ active: i - 1 === currentStep }"/>
                </div>
              </div>
              <button
                class="imm-next-btn"
                :disabled="isLast"
                @click="goNext"
              >
                {{ isLast ? '结束' : '下一步' }}
              </button>
            </div>
          </template>

          <!-- 考察题 -->
          <template v-else-if="step && step.type === 'quiz'">
            <div class="imm-quiz-inner">
              <div class="imm-quiz-header">
                <span class="imm-quiz-icon">💡</span>
                <span class="imm-quiz-label">随堂考察</span>
              </div>
              <Transition name="text-slide" mode="out-in">
                <p :key="step.id" class="imm-quiz-text">{{ step.text }}</p>
              </Transition>
              <div class="imm-quiz-options">
                <button
                  v-for="(opt, idx) in step.options"
                  :key="opt"
                  class="imm-quiz-opt"
                  :class="{
                    'answered': quizAnswered === opt,
                    'correct': quizAnswered === opt && quizCorrect,
                    'wrong': quizAnswered === opt && !quizCorrect,
                    'disabled': !!quizAnswered,
                  }"
                  :disabled="!!quizAnswered"
                  @click="answerQuiz(opt)"
                >
                  <span class="imm-opt-letter">{{ String.fromCharCode(65 + idx) }}</span>
                  {{ opt }}
                </button>
              </div>
              <div v-if="quizAnswered" class="imm-quiz-feedback">
                <span v-if="quizCorrect" class="correct-fb">✅ 回答正确！理解到位，继续加油！</span>
                <span v-else class="wrong-fb">❌ 再想想，正确答案是「{{ step.options?.[0] }}」</span>
              </div>
            </div>

            <!-- 底部导航栏 -->
            <div class="imm-nav">
              <div class="imm-theme-title">── {{ selectedScenario.theme }} ──</div>
              <div class="imm-progress-info">
                <span class="imm-progress-num">{{ currentStep + 1 }}/{{ totalSteps }}</span>
                <div class="imm-progress-dots">
                  <span v-for="i in Math.min(totalSteps, 12)" :key="i"
                    class="imm-dot" :class="{ active: i - 1 === currentStep }"/>
                </div>
              </div>
              <button
                class="imm-next-btn"
                :disabled="!quizAnswered || isLast"
                @click="goNext"
              >
                {{ isLast ? '结束' : '下一步' }}
              </button>
            </div>
          </template>

          <!-- 加载中占位 -->
          <div v-else-if="isLoadingScript" class="imm-skeleton-panel">
            <div class="imm-skel-line w-1/4"/>
            <div class="imm-skel-line w-full mt-2"/>
            <div class="imm-skel-line w-5/6 mt-1"/>
          </div>

          <!-- 结束 -->
          <div v-else-if="isLast && step" class="imm-end">
            <p class="imm-end-text">🎉 场景对话结束！</p>
            <p class="imm-end-sub">你已完成「{{ selectedScenario.title }}」情景学习</p>
            <button class="imm-next-btn mt-3" @click="exitImmersive">返回场景选择</button>
          </div>

        </div><!-- /imm-dialogue-panel -->

      </div><!-- /imm-root -->
    </Transition>
  </Teleport>
</template>

<style scoped>
/* ── 场景卡片（选择界面）─────────────────────────────── */
.scenario-card {
  border: 1px solid #e8eef8;
  border-radius: 16px;
  padding: 16px;
  transition: all 0.2s;
  background: white;
}
.scenario-card:hover {
  border-color: #c7d2fe;
  box-shadow: 0 6px 20px rgba(99,102,241,0.12);
  transform: translateY(-3px);
}

/* ═══════════════════════════════════════════════════════
   沉浸式界面
═══════════════════════════════════════════════════════ */

/* ── 根容器 ──────────────────────────────────────────── */
.imm-root {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #0a0e1a;
  font-family: inherit;
}

/* ── 背景层 ──────────────────────────────────────────── */
.imm-bg {
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
}
.imm-grid {
  position: absolute;
  inset: 0;
}
/* 顶部蓝紫色光晕 */
.imm-glow-top {
  position: absolute;
  top: -20%;
  left: 50%;
  transform: translateX(-50%);
  width: 70%;
  height: 55%;
  background: radial-gradient(ellipse, rgba(60,80,180,0.22) 0%, transparent 70%);
}
/* 右侧机柜模拟 */
.imm-rack-right {
  position: absolute;
  right: 6vw;
  top: 10%;
  bottom: 28%;
  width: 48px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  justify-content: center;
}
.imm-rack-unit {
  height: 18px;
  background: linear-gradient(90deg, #1a2a3a, #0d1a26);
  border: 1px solid #2a3a4a;
  border-radius: 2px;
  position: relative;
  overflow: hidden;
}
.imm-rack-unit::after {
  content: '';
  position: absolute;
  left: 8px; top: 50%; transform: translateY(-50%);
  width: 6px; height: 6px;
  border-radius: 50%;
  background: #22c55e;
  box-shadow: 0 0 6px #22c55e;
  animation: blink 2s infinite;
}
.imm-rack-unit:nth-child(3n)::after { background: #f59e0b; box-shadow: 0 0 6px #f59e0b; }
.imm-rack-unit:nth-child(5n)::after { background: #3b82f6; box-shadow: 0 0 6px #3b82f6; }
@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}
/* 左侧电路线装饰 */
.imm-wires {
  position: absolute;
  left: 4vw;
  top: 15%;
  bottom: 30%;
  width: 2px;
  background: linear-gradient(to bottom, transparent, rgba(60,100,220,0.3), rgba(60,100,220,0.15), transparent);
}
.imm-wires::before {
  content: '';
  position: absolute;
  left: 12px;
  top: 20%;
  height: 60%;
  width: 2px;
  background: linear-gradient(to bottom, transparent, rgba(100,60,220,0.25), transparent);
}

/* ── 关闭按钮 ─────────────────────────────────────────── */
.imm-close {
  position: absolute;
  top: 16px; right: 16px;
  z-index: 10;
  width: 34px; height: 34px;
  border-radius: 50%;
  background: rgba(255,255,255,0.12);
  border: 1px solid rgba(255,255,255,0.15);
  color: #fff;
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: background 0.15s;
  backdrop-filter: blur(4px);
}
.imm-close:hover { background: rgba(255,255,255,0.22); }

/* ── 顶部场景标签 ─────────────────────────────────────── */
.imm-topbar {
  position: absolute;
  top: 16px; left: 16px;
  z-index: 10;
  display: flex;
  align-items: center;
  gap: 8px;
}
.imm-scene-tag {
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.12);
  color: rgba(255,255,255,0.75);
  font-size: 12px;
  padding: 4px 12px;
  border-radius: 20px;
  backdrop-filter: blur(4px);
}
.imm-diff-tag {
  font-size: 11px;
  padding: 3px 9px;
  border-radius: 12px;
  font-weight: 600;
}
.imm-diff-tag.green  { background: rgba(34,197,94,0.15); color: #4ade80; border: 1px solid rgba(34,197,94,0.2); }
.imm-diff-tag.amber  { background: rgba(245,158,11,0.15); color: #fbbf24; border: 1px solid rgba(245,158,11,0.2); }
.imm-diff-tag.red    { background: rgba(239,68,68,0.15); color: #f87171; border: 1px solid rgba(239,68,68,0.2); }

/* ── 人物区 ───────────────────────────────────────────── */
.imm-character-area {
  flex: 1;
  position: relative;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  padding-bottom: 0;
  min-height: 0;
}
.imm-char-img {
  max-height: 100%;
  width: auto;
  max-width: 380px;
  object-fit: contain;
  object-position: bottom;
  filter: drop-shadow(0 8px 32px rgba(0,0,0,0.6));
  transform-origin: bottom center;
}
.imm-loading-char {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding-bottom: 40px;
}
.imm-char-skeleton {
  width: 160px; height: 320px;
  background: linear-gradient(135deg, rgba(255,255,255,0.04), rgba(255,255,255,0.02));
  border-radius: 12px;
  animation: pulse 1.4s infinite;
}
.imm-loading-text { color: rgba(255,255,255,0.4); font-size: 13px; }
@keyframes pulse { 0%,100%{opacity:0.5} 50%{opacity:1} }

/* ── 底部对话面板 ─────────────────────────────────────── */
.imm-dialogue-panel {
  flex-shrink: 0;
  background: #f5efe5;
  /* 顶部圆角 */
  border-radius: 20px 20px 0 0;
  min-height: 230px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 -4px 24px rgba(0,0,0,0.3);
  position: relative;
  z-index: 5;
}

/* 普通对话内容 */
.imm-dialogue-inner {
  padding: 20px 24px 8px;
  flex: 1;
}
.imm-role-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.imm-role-bar {
  width: 3px;
  height: 18px;
  background: #8b6a3e;
  border-radius: 2px;
  flex-shrink: 0;
}
.imm-role-name {
  font-size: 15px;
  font-weight: 700;
  color: #3d2b1a;
}
.imm-text {
  font-size: 14px;
  color: #4a3728;
  line-height: 1.75;
  margin: 0;
}
.imm-stage {
  color: #8b6a3e;
  font-style: italic;
  margin-right: 4px;
  font-size: 13px;
}

/* 考察题内容 */
.imm-quiz-inner {
  padding: 16px 20px 8px;
  flex: 1;
}
.imm-quiz-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
}
.imm-quiz-icon { font-size: 16px; }
.imm-quiz-label {
  font-size: 12px;
  font-weight: 700;
  color: #c47d18;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.imm-quiz-text {
  font-size: 14px;
  color: #3d2b1a;
  font-weight: 600;
  margin: 0 0 12px;
  line-height: 1.6;
}
.imm-quiz-options {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.imm-quiz-opt {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 8px 14px;
  background: rgba(255,255,255,0.7);
  border: 1.5px solid #d4b896;
  border-radius: 10px;
  font-size: 13px;
  color: #4a3728;
  cursor: pointer;
  transition: all 0.15s;
  text-align: left;
}
.imm-quiz-opt:hover:not(.disabled) {
  background: rgba(255,255,255,0.95);
  border-color: #8b6a3e;
}
.imm-quiz-opt.correct { background: #dcfce7; border-color: #22c55e; color: #15803d; }
.imm-quiz-opt.wrong   { background: #fee2e2; border-color: #ef4444; color: #b91c1c; }
.imm-quiz-opt.disabled:not(.answered) { opacity: 0.5; }
.imm-opt-letter {
  width: 22px; height: 22px;
  border-radius: 50%;
  background: #e5d0b8;
  display: flex; align-items: center; justify-content: center;
  font-size: 11px; font-weight: 700; color: #7a5230;
  flex-shrink: 0;
}
.imm-quiz-feedback {
  margin-top: 8px;
  font-size: 12.5px;
  padding: 6px 12px;
  border-radius: 8px;
}
.correct-fb { color: #15803d; background: #dcfce7; padding: 4px 10px; border-radius: 6px; display: inline-block; }
.wrong-fb   { color: #b91c1c; background: #fee2e2; padding: 4px 10px; border-radius: 6px; display: inline-block; }

/* ── 底部导航 ─────────────────────────────────────────── */
.imm-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 20px 14px;
  border-top: 1px solid rgba(139,106,62,0.15);
  gap: 8px;
}
.imm-theme-title {
  font-size: 12px;
  font-weight: 700;
  color: #e53e3e;
  letter-spacing: 0.03em;
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.imm-progress-info {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}
.imm-progress-num {
  font-size: 12px;
  color: #8b6a3e;
  font-weight: 600;
}
.imm-progress-dots {
  display: flex;
  gap: 3px;
}
.imm-dot {
  width: 5px; height: 5px;
  border-radius: 50%;
  background: #d4b896;
  transition: background 0.2s, transform 0.2s;
}
.imm-dot.active {
  background: #8b6a3e;
  transform: scale(1.4);
}

.imm-next-btn {
  background: #8b4513;
  color: #fff;
  border: none;
  border-radius: 20px;
  padding: 8px 22px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  transition: background 0.15s, transform 0.1s;
  flex-shrink: 0;
}
.imm-next-btn:hover:not(:disabled) {
  background: #a0522d;
  transform: translateY(-1px);
}
.imm-next-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

/* 骨架占位 */
.imm-skeleton-panel {
  padding: 20px 24px;
}
.imm-skel-line {
  height: 14px;
  background: linear-gradient(90deg, #e8d8c4 25%, #f0e4d4 50%, #e8d8c4 75%);
  background-size: 200% 100%;
  border-radius: 7px;
  animation: shimmer 1.2s infinite;
}
@keyframes shimmer { to { background-position: -200% 0; } }

/* 结束画面 */
.imm-end {
  padding: 24px;
  text-align: center;
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.imm-end-text { font-size: 18px; font-weight: 700; color: #3d2b1a; margin: 0; }
.imm-end-sub  { font-size: 13px; color: #8b6a3e; margin: 6px 0 0; }

/* ── 过渡动画 ─────────────────────────────────────────── */
.imm-fade-enter-active,
.imm-fade-leave-active { transition: opacity 0.35s ease; }
.imm-fade-enter-from,
.imm-fade-leave-to    { opacity: 0; }

.char-fade-enter-active { transition: opacity 0.4s ease, transform 0.4s ease; }
.char-fade-leave-active { transition: opacity 0.2s ease; }
.char-fade-enter-from   { opacity: 0; transform: translateY(20px); }
.char-fade-leave-to     { opacity: 0; }

.text-slide-enter-active { transition: opacity 0.3s ease, transform 0.3s ease; }
.text-slide-leave-active { transition: opacity 0.15s ease; }
.text-slide-enter-from   { opacity: 0; transform: translateY(8px); }
.text-slide-leave-to     { opacity: 0; }
</style>
