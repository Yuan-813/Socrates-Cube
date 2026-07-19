<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/userStore'
import axios from 'axios'

const router = useRouter()
const userStore = useUserStore()
const currentStep = ref(0)
const answers = ref<Record<string, string | string[]>>({})
const isSubmitting = ref(false)
const submitError = ref('')
const bgCanvasRef = ref<HTMLCanvasElement | null>(null)
let bgAnimId: number | null = null

const steps = [
  {
    id: 'identity', title: '选择你的学习身份', subtitle: '不同的身份将获得不同的学习体验和资源推荐',
    type: 'single_choice',
    options: [
      { value: 'student_undergrad', label: '网络专业本科生', icon: '🎓', desc: '系统学习网络基础，构建扎实知识体系', tags: ['课程学习', '基础夯实'] },
      { value: 'student_grad', label: '研究生', icon: '🔬', desc: '深研网络前沿，科研探索与突破', tags: ['科研探索', '深度学习'] },
      { value: 'professional', label: '网络工程师', icon: '💼', desc: '强化实战能力，解决工程难题', tags: ['实践提升', '问题解决'] },
      { value: 'self_learner', label: '认证备考者', icon: '🏆', desc: '高效备考，攻克HCIA/CCNA认证', tags: ['考试导向', '高效通过'] },
    ],
  },
  {
    id: 'goal', title: '你的主要学习目标', subtitle: '告诉我你最想实现的目标，可以多选',
    type: 'multi_choice',
    options: [
      { value: 'exam', label: '期末考试', icon: '📝', desc: '冲击期末高分', tags: ['应试', '高分'] },
      { value: 'hcia', label: '华为HCIA认证', icon: '🏅', desc: 'HCIA-Datacom/RS备考', tags: ['认证', '华为'] },
      { value: 'ccna', label: '思科CCNA认证', icon: '🌐', desc: '思科网络工程师认证', tags: ['认证', '思科'] },
      { value: 'job', label: '求职备战', icon: '🏢', desc: '大厂技术求职面试', tags: ['求职', '面试'] },
      { value: 'interest', label: '兴趣探索', icon: '🔍', desc: '拓展技术边界', tags: ['探索', '深度'] },
    ],
  },
  {
    id: 'level', title: '当前计算机网络基础', subtitle: '帮助我为你匹配最合适的学习起点',
    type: 'single_choice',
    options: [
      { value: 'zero', label: '零基础入门', icon: '🌱', desc: '全新起点，从零出发', tags: ['基础', '入门'] },
      { value: 'basic', label: '了解基础概念', icon: '🌿', desc: '略懂TCP/IP与OSI模型', tags: ['初级', '概念'] },
      { value: 'intermediate', label: '有一定基础', icon: '🌳', desc: '有积累，需深化机制理解', tags: ['中级', '深化'] },
      { value: 'advanced', label: '有工作经验', icon: '🌲', desc: '丰富的实战运维经验', tags: ['高级', '实战'] },
    ],
  },
  {
    id: 'target_job', title: '你的目标方向', subtitle: 'AI将为你规划最匹配的技术成长路径',
    type: 'single_choice',
    options: [
      { value: 'network_engineer', label: '网络工程师', icon: '🔌', desc: '路由交换与网络规划', tags: ['路由', '交换'] },
      { value: 'cloud_engineer', label: '云计算工程师', icon: '☁️', desc: 'SDN、容器与云网络', tags: ['云原生', 'SDN'] },
      { value: 'security_engineer', label: '网络安全工程师', icon: '🛡️', desc: '防火墙与渗透防护', tags: ['安全', '防护'] },
      { value: 'developer', label: '后端/全栈开发', icon: '💻', desc: '网络原理赋能开发', tags: ['开发', '全栈'] },
      { value: 'other', label: '其他/暂未确定', icon: '🎯', desc: '夯实基础，方向待定', tags: ['通用', '基础'] },
    ],
  },
  {
    id: 'learning_style', title: '你的学习风格', subtitle: '个性化的学习方式让效率翻倍',
    type: 'single_choice',
    options: [
      { value: 'visual', label: '图表与视频', icon: '🎬', desc: '可视化演示，直观理解', tags: ['直观', '动态'] },
      { value: 'practical', label: '动手实验', icon: '⌨️', desc: '代码实验与网络配置', tags: ['实操', '动手'] },
      { value: 'textual', label: '系统文字', icon: '📖', desc: '系统讲解与RFC深读', tags: ['严谨', '系统'] },
      { value: 'mixed', label: '多元结合', icon: '🔀', desc: '多元融合，灵活高效', tags: ['灵活', '全面'] },
    ],
  },
]

const stepLabels = [
  { num: 1, label: '认识你', sub: '身份画像' },
  { num: 2, label: '了解你', sub: '学习目标' },
  { num: 3, label: '测试你', sub: '能力摸底' },
  { num: 4, label: '分析你', sub: '知识薄弱点' },
  { num: 5, label: '定制你', sub: 'AI学习路径' },
]

const initBars = [
  { icon: '🕸', label: '知识图谱加载中', pct: 85 },
  { icon: '👤', label: '学习画像分析中', pct: 72 },
  { icon: '🧠', label: '能力模型匹配中', pct: 90 },
  { icon: '🎯', label: '学习路径规划中', pct: 65 },
]

const floatingTags = [
  { text: 'TCP/IP', top: '18%', left: '8%' },
  { text: 'HTTP', top: '12%', left: '62%' },
  { text: '路由交换', top: '30%', left: '68%' },
  { text: '数据链路层', top: '50%', left: '5%' },
  { text: '传输层', top: '65%', left: '12%' },
  { text: '应用层', top: '65%', left: '60%' },
  { text: '网络安全', top: '42%', left: '72%' },
  { text: '云计算', top: '78%', left: '58%' },
]

const techModules = [
  { icon: '🤖', en: '多智能体协同', cn: '教授/工程师/同伴陪伴学习' },
  { icon: '🕸', en: '知识图谱驱动', cn: '构建完整的网络知识体系' },
  { icon: '📈', en: 'AI 自适应学习', cn: '动态调整学习内容和难度' },
  { icon: '🔧', en: '真实场景实践', cn: '实验/仿真/项目实战训练' },
]

const currentStepData = computed(() => steps[currentStep.value])
const isLastStep = computed(() => currentStep.value === steps.length - 1)

function selectOption(stepId: string, value: string, isMulti: boolean) {
  if (isMulti) {
    const cur = (answers.value[stepId] as string[]) || []
    const idx = cur.indexOf(value)
    answers.value[stepId] = idx >= 0 ? cur.filter(v => v !== value) : [...cur, value]
  } else {
    answers.value[stepId] = value
  }
}
function isSelected(stepId: string, value: string) {
  const a = answers.value[stepId]
  return Array.isArray(a) ? a.includes(value) : a === value
}
function canNext() {
  const a = answers.value[currentStepData.value.id]
  if (!a) return false
  return Array.isArray(a) ? a.length > 0 : Boolean(a)
}
function nextStep() {
  if (!canNext()) return
  if (isLastStep.value) submitOnboarding()
  else currentStep.value++
}
function prevStep() { if (currentStep.value > 0) currentStep.value-- }

async function submitOnboarding() {
  isSubmitting.value = true; submitError.value = ''
  try {
    await axios.post(`/api/v1/onboarding/submit/${userStore.userId}`, { user_id: userStore.userId, answers: answers.value })
    localStorage.setItem(`onboarded_${userStore.userId}`, 'true')
    await userStore.fetchProfile()
    router.push('/')
  } catch (e: unknown) {
    submitError.value = e instanceof Error ? e.message : '提交失败，请重试'
  } finally { isSubmitting.value = false }
}

function initBgCanvas() {
  const cv = bgCanvasRef.value; if (!cv) return
  const ctx = cv.getContext('2d') as CanvasRenderingContext2D; if (!ctx) return
  let w = cv.width = cv.offsetWidth; let h = cv.height = cv.offsetHeight
  const ns: {x:number;y:number;vx:number;vy:number;r:number;hue:number}[] = []
  for (let i = 0; i < 50; i++) ns.push({x:Math.random()*w,y:Math.random()*h,vx:(Math.random()-.5)*.3,vy:(Math.random()-.5)*.3,r:1+Math.random()*1.8,hue:200+Math.random()*70})
  function draw() {
    ctx.clearRect(0,0,w,h)
    for (const n of ns){n.x+=n.vx;n.y+=n.vy;if(n.x<0||n.x>w)n.vx*=-1;if(n.y<0||n.y>h)n.vy*=-1}
    for (let i=0;i<ns.length;i++) for (let j=i+1;j<ns.length;j++){const dx=ns[i].x-ns[j].x,dy=ns[i].y-ns[j].y,d=Math.sqrt(dx*dx+dy*dy);if(d<120){ctx.strokeStyle=`rgba(100,170,255,${(1-d/120)*.18})`;ctx.lineWidth=.6;ctx.beginPath();ctx.moveTo(ns[i].x,ns[i].y);ctx.lineTo(ns[j].x,ns[j].y);ctx.stroke()}}
    for (const n of ns){ctx.beginPath();ctx.arc(n.x,n.y,n.r,0,Math.PI*2);ctx.fillStyle=`hsla(${n.hue},70%,65%,.5)`;ctx.fill()}
    bgAnimId = requestAnimationFrame(draw)
  }
  draw()
  new ResizeObserver(()=>{w=cv.width=cv.offsetWidth;h=cv.height=cv.offsetHeight}).observe(cv)
}

onMounted(() => nextTick(initBgCanvas))
onUnmounted(() => { if (bgAnimId) cancelAnimationFrame(bgAnimId) })
</script>

<template>
  <div class="ob1-page">
    <canvas ref="bgCanvasRef" class="bg-cv"></canvas>

    <!-- Protocol text bg -->
    <div class="proto-bg" aria-hidden="true">
      <span style="top:5%;left:3%">TCP</span><span style="top:18%;right:5%">HTTP/2</span>
      <span style="top:40%;left:1%">BGP</span><span style="bottom:20%;left:8%">UDP</span>
      <span style="top:12%;left:28%">TLS</span><span style="bottom:28%;right:3%">DNS</span>
      <span style="top:55%;right:15%">OSPF</span><span style="bottom:8%;right:18%">IPv6</span>
    </div>

    <!-- Header bar -->
    <header class="ob1-header">
      <div class="logo">
        <span class="lhex">⬡</span>
        <span class="lname">Socrates Cube</span>
        <span class="ltag">AI-Native Network Learning Space</span>
      </div>
      <button class="skip-btn" @click="router.push('/')">跳过引导 →</button>
    </header>

    <!-- Main -->
    <main class="ob1-main">

      <!-- LEFT: Alice + description -->
      <div class="ob1-left">
        <div class="greeting-block">
          <h1 class="greet-title">你好，未来的网络工程师！<span>👋</span></h1>
          <p class="greet-sub">让我们一起开启你的<strong>专属学习之旅</strong></p>
        </div>

        <div class="alice-scene">
          <!-- Floating protocol tags -->
          <div
            v-for="t in floatingTags" :key="t.text"
            class="ftag"
            :style="`top:${t.top};left:${t.left}`"
          >{{ t.text }}</div>

          <!-- Background glow halo -->
          <div class="alice-halo"></div>

          <!-- Orbital rings (planet-style) -->
          <div class="alice-ring r1"></div>
          <div class="alice-ring r2"></div>

          <!-- Energy platform at feet -->
          <div class="alice-platform"></div>

          <!-- Alice full-body (NO circle crop, soft mask) -->
          <img src="/images/virtual_teacher.png" alt="Alice" class="alice-img" />

          <!-- Speech bubble: compact overlay on lower body -->
          <div class="alice-speech">
            <div class="as-head">
              <span class="as-badge">AI</span>
              <span class="as-name">我是 <strong>Alice</strong></span>
              <span class="as-role">你的 AI 学习助手</span>
            </div>
            <p class="as-body">根据你的目标，生成专属成长路径。</p>
          </div>
        </div>

        <!-- AI init bars -->
        <div class="init-wrap">
          <div class="init-label">AI 正在为你初始化学习空间...</div>
          <div class="init-bars">
            <div class="ibar" v-for="b in initBars" :key="b.label">
              <span class="ib-ic">{{ b.icon }}</span>
              <div class="ib-body">
                <div class="ib-name">{{ b.label }}</div>
                <div class="ib-track"><div class="ib-fill" :style="`width:${b.pct}%`"></div></div>
              </div>
              <span class="ib-pct">{{ b.pct }}%</span>
            </div>
          </div>
        </div>
      </div>

      <!-- RIGHT: Step indicator + Options -->
      <div class="ob1-right">

        <!-- Step circles -->
        <div class="step-dots">
          <template v-for="(sl, i) in stepLabels" :key="sl.num">
            <div class="sd" :class="{active: currentStep === i, done: currentStep > i}">{{ sl.num }}</div>
            <div v-if="i < stepLabels.length - 1" class="sd-line" :class="{active: currentStep > i}"></div>
          </template>
        </div>
        <div class="step-hint">第{{ currentStep + 1 }}步（共{{ steps.length }}步）</div>

        <!-- Card -->
        <div class="ob1-card">
          <Transition name="sf" mode="out-in">
            <div :key="currentStep">
              <h2 class="card-title">{{ currentStepData.title }}</h2>
              <p class="card-sub">{{ currentStepData.subtitle }}</p>

              <div class="opts-grid" :class="{multi: currentStepData.type === 'multi_choice'}">
                <button
                  v-for="opt in currentStepData.options" :key="opt.value"
                  class="opt-card" :class="{sel: isSelected(currentStepData.id, opt.value)}"
                  @click="selectOption(currentStepData.id, opt.value, currentStepData.type === 'multi_choice')"
                >
                  <div class="oc-icon">{{ opt.icon }}</div>
                  <div class="oc-body">
                    <div class="oc-label">{{ opt.label }}</div>
                    <div class="oc-desc">{{ opt.desc }}</div>
                    <div class="oc-tags">
                      <span v-for="tag in opt.tags" :key="tag" class="oc-tag">{{ tag }}</span>
                    </div>
                  </div>
                  <div class="oc-check" v-if="isSelected(currentStepData.id, opt.value)">✓</div>
                </button>
              </div>

              <p v-if="currentStepData.type === 'multi_choice'" class="multi-hint">可以选择多个目标</p>
            </div>
          </Transition>

          <p v-if="submitError" class="err-msg">{{ submitError }}</p>

          <div class="act-row">
            <button v-if="currentStep > 0" class="btn-back" @click="prevStep">← 上一步</button>
            <button class="btn-next" :class="{submit: isLastStep}" :disabled="!canNext() || isSubmitting" @click="nextStep">
              <span v-if="isSubmitting">生成中...</span>
              <span v-else-if="isLastStep">生成我的AI学习档案 ✨</span>
              <span v-else>下一步 →</span>
            </button>
          </div>

          <p class="privacy-note">🔒 信息仅用于个性化学习推荐，严格保护隐私</p>
        </div>
      </div>
    </main>

    <!-- Bottom step labels + tech bar (unified) -->
    <div class="bottom-bar">
      <div class="step-labels">
        <div class="sl-title">五步学习旅程</div>
        <div v-for="(sl, i) in stepLabels" :key="sl.num" class="sl-item" :class="{active: currentStep + 1 === sl.num, done: currentStep + 1 > sl.num}">
          <div class="sl-num">{{ sl.num }}</div>
          <div>
            <div class="sl-label">{{ sl.label }}</div>
            <div class="sl-sub">{{ sl.sub }}</div>
          </div>
          <div class="sl-arrow" v-if="i < stepLabels.length - 1">→</div>
        </div>
      </div>
      <div class="tm-sep"></div>
      <div class="tech-row">
        <div class="tm" v-for="t in techModules" :key="t.en">
          <span class="tm-ic">{{ t.icon }}</span>
          <div><div class="tm-en">{{ t.en }}</div><div class="tm-cn">{{ t.cn }}</div></div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.ob1-page { min-height:100vh; background:radial-gradient(ellipse at 30% 40%,#0d1a3a 0%,#060d1f 60%,#030812 100%); font-family:'Inter','PingFang SC',system-ui,sans-serif; color:#f1f5f9; display:flex; flex-direction:column; position:relative; overflow:hidden; }
.bg-cv { position:fixed; inset:0; width:100%; height:100%; z-index:0; pointer-events:none; }
.proto-bg { position:fixed; inset:0; z-index:1; pointer-events:none; }
.proto-bg span { position:absolute; font-family:monospace; font-size:12px; font-weight:800; letter-spacing:2px; color:rgba(100,170,255,.06); }

/* Header */
.ob1-header { position:relative; z-index:10; display:flex; align-items:center; justify-content:space-between; padding:14px 40px; border-bottom:1px solid rgba(255,255,255,.04); background:rgba(3,8,20,.55); backdrop-filter:blur(12px); }
.logo { display:flex; align-items:center; gap:10px; }
.lhex { font-size:20px; color:#60a5fa; filter:drop-shadow(0 0 10px rgba(96,165,250,.8)); }
.lname { font-size:16px; font-weight:800; background:linear-gradient(90deg,#e2e8f0 0%,#a5b4fc 60%,#60a5fa 100%); -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent; filter:drop-shadow(0 0 12px rgba(96,165,250,.3)); letter-spacing:-.3px; }
.ltag { font-size:11px; color:rgba(148,163,184,.45); margin-left:4px; letter-spacing:.05em; }
.skip-btn { background:none; border:1px solid rgba(255,255,255,.1); border-radius:8px; padding:7px 16px; font-size:12px; color:rgba(148,163,184,.7); cursor:pointer; font-family:inherit; transition:all .2s; }
.skip-btn:hover { border-color:rgba(96,165,250,.4); color:#60a5fa; }

/* Main */
.ob1-main { position:relative; z-index:5; flex:1; display:grid; grid-template-columns:1fr 480px; gap:32px; padding:24px 40px 16px; align-items:start; }

/* LEFT */
.ob1-left { display:flex; flex-direction:column; gap:16px; }
.greeting-block { min-height:0; }
.greet-title { font-size:36px; font-weight:900; margin:0 0 8px; background:linear-gradient(100deg,#60a5fa 0%,#a78bfa 45%,#f472b6 100%); -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent; filter:drop-shadow(0 0 20px rgba(96,165,250,.3)); }
.greet-title span { -webkit-text-fill-color:initial; }
.greet-sub { font-size:15px; color:rgba(148,163,184,.75); margin:0; }
.greet-sub strong { color:rgba(196,181,253,.9); }

/* Alice scene — full-body mode */
.alice-scene { position:relative; height:390px; overflow:visible; }

/* Background glow halo */
.alice-halo { position:absolute; width:300px; height:300px; border-radius:50%; top:55%; left:50%; transform:translate(-50%,-65%); background:radial-gradient(circle,rgba(80,140,255,.2) 0%,rgba(96,165,250,.08) 40%,transparent 70%); animation:hpulse 3.5s ease-in-out infinite; z-index:1; pointer-events:none; }
@keyframes hpulse { 0%,100%{transform:translate(-50%,-65%) scale(.95);opacity:.7}50%{transform:translate(-50%,-65%) scale(1.05);opacity:1} }

/* Orbital rings */
.alice-ring { position:absolute; border-radius:50%; left:50%; border:1.5px solid rgba(100,180,255,.22); animation:rpulse 4.5s ease-in-out infinite; pointer-events:none; z-index:2; }
.r1 { width:240px; height:58px; top:72%; transform:translate(-50%,-50%) rotateX(0deg); animation-delay:0s; }
.r2 { width:320px; height:78px; top:73%; transform:translate(-50%,-50%); border-color:rgba(160,100,255,.15); animation-delay:2.2s; }
@keyframes rpulse { 0%,100%{opacity:.25}50%{opacity:.65} }

/* Energy platform glow at feet */
.alice-platform { position:absolute; bottom:58px; left:50%; transform:translateX(-50%); width:200px; height:18px; background:radial-gradient(ellipse at center,rgba(96,165,250,.65) 0%,transparent 70%); filter:blur(7px); border-radius:50%; z-index:2; pointer-events:none; }

/* Alice image — full body, NO circular crop, soft bottom fade */
.alice-img { position:absolute; bottom:54px; left:50%; transform:translateX(-50%); z-index:3; width:240px; height:300px; object-fit:cover; object-position:top center; -webkit-mask-image:linear-gradient(to bottom, black 0%, black 62%, transparent 90%); mask-image:linear-gradient(to bottom, black 0%, black 62%, transparent 90%); filter:drop-shadow(0 -4px 22px rgba(96,165,250,.5)) drop-shadow(0 0 40px rgba(80,140,255,.25)); }

/* Speech bubble — compact overlay */
.alice-speech { position:absolute; bottom:0; left:4px; right:4px; background:rgba(4,9,22,.86); border:1px solid rgba(96,165,250,.3); border-radius:14px; padding:10px 14px; backdrop-filter:blur(20px); z-index:5; box-shadow:0 -4px 20px rgba(0,0,0,.35); }
.as-head { display:flex; align-items:center; gap:7px; margin-bottom:4px; flex-wrap:wrap; }
.as-badge { font-size:9px; font-weight:800; background:linear-gradient(90deg,#6366f1,#22d3ee); color:#fff; border-radius:4px; padding:2px 7px; letter-spacing:.5px; flex-shrink:0; }
.as-name { font-size:14px; font-weight:700; color:rgba(226,232,240,.95); }
.as-name strong { color:#60a5fa; }
.as-role { font-size:11px; color:rgba(148,163,184,.6); margin-left:2px; }
.as-body { font-size:11.5px; color:rgba(203,213,225,.82); margin:0; line-height:1.55; }
.ftag { position:absolute; font-size:11px; font-weight:700; color:rgba(96,165,250,.8); background:rgba(96,165,250,.1); border:1px solid rgba(96,165,250,.25); border-radius:6px; padding:3px 9px; letter-spacing:.05em; white-space:nowrap; animation:fdrift 6s ease-in-out infinite; animation-delay:calc(var(--i,0)*-.8s); }
.ftag:nth-child(1){--i:0}.ftag:nth-child(2){--i:1}.ftag:nth-child(3){--i:2}.ftag:nth-child(4){--i:3}.ftag:nth-child(5){--i:4}.ftag:nth-child(6){--i:5}.ftag:nth-child(7){--i:6}.ftag:nth-child(8){--i:7}
@keyframes fdrift { 0%,100%{transform:translateY(0)}50%{transform:translateY(-6px)} }

/* Init bars — lower visual weight, subtle */
.init-wrap { opacity:.7; }
.init-label { font-size:10px; color:rgba(148,163,184,.45); margin-bottom:6px; }
.init-bars { display:grid; grid-template-columns:1fr 1fr; gap:7px; }
.ibar { display:flex; align-items:center; gap:8px; background:rgba(255,255,255,.03); border:1px solid rgba(255,255,255,.06); border-radius:10px; padding:8px 10px; }
.ib-ic { font-size:14px; flex-shrink:0; }
.ib-body { flex:1; min-width:0; }
.ib-name { font-size:10px; color:rgba(148,163,184,.7); margin-bottom:4px; }
.ib-track { height:4px; background:rgba(255,255,255,.08); border-radius:2px; overflow:hidden; }
.ib-fill { height:100%; background:linear-gradient(90deg,#6366f1,#22d3ee); border-radius:2px; transition:width 1s ease; }
.ib-pct { font-size:10px; font-weight:700; color:#60a5fa; font-family:monospace; flex-shrink:0; }

/* RIGHT */
.ob1-right { display:flex; flex-direction:column; gap:12px; }
.step-dots { display:flex; align-items:center; padding:4px 0; }
.sd { width:34px; height:34px; border-radius:50%; border:2px solid rgba(255,255,255,.15); display:flex; align-items:center; justify-content:center; font-size:13px; font-weight:700; color:rgba(148,163,184,.5); flex-shrink:0; transition:all .3s; }
.sd.active { border-color:#7c3aed; background:#7c3aed; color:white; box-shadow:0 0 12px rgba(124,58,237,.5); }
.sd.done { border-color:#4ade80; background:rgba(74,222,128,.15); color:#4ade80; }
.sd-line { flex:1; height:2px; background:rgba(255,255,255,.1); transition:background .3s; }
.sd-line.active { background:linear-gradient(90deg,rgba(74,222,128,.5),rgba(124,58,237,.3)); }
.step-hint { font-size:11px; color:rgba(148,163,184,.55); }

/* Card */
.ob1-card { background:rgba(6,12,28,.75); border:1px solid rgba(255,255,255,.08); border-radius:20px; padding:24px 22px; backdrop-filter:blur(22px); box-shadow:0 20px 60px rgba(0,0,0,.5); }
.card-title { font-size:18px; font-weight:800; color:#f1f5f9; margin:0 0 4px; }
.card-sub { font-size:12px; color:rgba(148,163,184,.65); margin:0 0 16px; }
.opts-grid { display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-bottom:12px; }
.opts-grid.multi { grid-template-columns:1fr; }
.opt-card { display:grid; grid-template-columns:44px 1fr auto; align-items:start; gap:10px; padding:12px 14px; background:rgba(255,255,255,.03); border:1.5px solid rgba(255,255,255,.07); border-radius:14px; cursor:pointer; text-align:left; transition:all .2s; font-family:inherit; }
.opt-card:hover { background:rgba(99,102,241,.08); border-color:rgba(99,102,241,.35); }
.opt-card.sel { background:rgba(99,102,241,.14); border-color:rgba(99,102,241,.7); box-shadow:0 0 15px rgba(99,102,241,.15); }
.oc-icon { font-size:28px; line-height:1; }
.oc-label { font-size:13px; font-weight:700; color:rgba(226,232,240,.95); margin-bottom:3px; }
.oc-desc { font-size:11px; color:rgba(148,163,184,.65); line-height:1.4; margin-bottom:6px; }
.oc-tags { display:flex; gap:4px; flex-wrap:wrap; }
.oc-tag { font-size:9px; font-weight:600; color:rgba(96,165,250,.8); background:rgba(96,165,250,.1); border:1px solid rgba(96,165,250,.2); border-radius:4px; padding:2px 6px; }
.oc-check { color:#4ade80; font-size:14px; font-weight:700; margin-top:2px; }
.multi-hint { font-size:11px; color:rgba(148,163,184,.5); text-align:center; margin:-4px 0 8px; }
.err-msg { color:#fca5a5; font-size:12px; text-align:center; margin:6px 0; }
.act-row { display:flex; gap:10px; margin-top:4px; }
.btn-back { padding:11px 18px; border:1px solid rgba(255,255,255,.1); border-radius:11px; background:rgba(255,255,255,.04); color:rgba(148,163,184,.75); font-size:13px; cursor:pointer; font-family:inherit; transition:all .2s; }
.btn-back:hover { background:rgba(255,255,255,.08); }
.btn-next { flex:1; padding:13px; background:linear-gradient(135deg,#7c3aed 0%,#6366f1 50%,#0891b2 100%); border:none; border-radius:11px; color:white; font-size:14px; font-weight:700; cursor:pointer; transition:all .3s; font-family:inherit; }
.btn-next:hover:not(:disabled) { transform:translateY(-1px); box-shadow:0 8px 28px rgba(99,102,241,.45); }
.btn-next:disabled { opacity:.45; cursor:not-allowed; }
.btn-next.submit { background:linear-gradient(135deg,#7c3aed,#a855f7,#ec4899); }
.privacy-note { text-align:center; font-size:10px; color:rgba(148,163,184,.45); margin:10px 0 0; }

/* Bottom unified bar */
.bottom-bar { position:relative; z-index:10; background:rgba(3,8,20,.72); border-top:1px solid rgba(255,255,255,.05); backdrop-filter:blur(14px); }
.step-labels { display:flex; align-items:center; padding:8px 32px; gap:0; border-bottom:1px solid rgba(255,255,255,.04); }
.sl-title { font-size:10px; font-weight:700; color:rgba(96,165,250,.6); letter-spacing:2px; text-transform:uppercase; padding-right:20px; border-right:1px solid rgba(255,255,255,.06); margin-right:12px; white-space:nowrap; }
.sl-item { display:flex; align-items:center; gap:7px; flex:1; position:relative; }
.sl-arrow { color:rgba(255,255,255,.12); font-size:12px; }
.sl-item.done .sl-num { background:#4ade80; color:#030812; }
.sl-item.active .sl-num { background:#7c3aed; box-shadow:0 0 10px rgba(124,58,237,.5); }
.sl-num { width:22px; height:22px; border-radius:50%; background:rgba(255,255,255,.08); display:flex; align-items:center; justify-content:center; font-size:11px; font-weight:700; color:rgba(226,232,240,.8); flex-shrink:0; transition:all .3s; }
.sl-label { font-size:11px; font-weight:700; color:rgba(226,232,240,.75); }
.sl-sub { font-size:9px; color:rgba(148,163,184,.45); }
.tm-sep { height:0; }
.tech-row { display:flex; justify-content:center; padding:6px 32px; }
.tm { display:flex; align-items:center; gap:8px; padding:4px 20px; border-right:1px solid rgba(255,255,255,.04); }
.tm:last-child { border-right:none; }
.tm-ic { font-size:16px; opacity:.75; }
.tm-en { font-size:11px; font-weight:700; color:rgba(226,232,240,.7); }
.tm-cn { font-size:9px; color:rgba(148,163,184,.4); }

/* Transition */
.sf-enter-active,.sf-leave-active { transition:opacity .2s,transform .2s; }
.sf-enter-from { opacity:0; transform:translateX(16px); }
.sf-leave-to { opacity:0; transform:translateX(-16px); }

@media (max-width:1100px) {
  .ob1-main { grid-template-columns:1fr; }
  .ob1-left { display:none; }
  .tm { padding:6px 12px; }
}
</style>
