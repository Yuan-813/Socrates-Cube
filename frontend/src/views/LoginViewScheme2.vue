<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import { useUserStore } from '@/stores/userStore'
import { authApi } from '@/api/auth'
import RegisterSuccessNotify from '@/components/RegisterSuccessNotify.vue'
import SplitScreenTransition from '@/components/SplitScreenTransition.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const userStore = useUserStore()

type LoginTab = 'account' | 'phone' | 'guest'
const activeTab = ref<LoginTab>('account')
const accountForm = reactive({ username: '', password: '' })
const registerForm = reactive({ username: '', password: '', confirmPwd: '', email: '' })
const isRegisterMode = ref(false)
const phoneForm = reactive({ phone: '', code: '' })
const otpSent = ref(false)
const otpCountdown = ref(0)
const demoCode = ref('')
const captchaText = ref('')
const captchaInput = ref('')
const canvasRef = ref<HTMLCanvasElement | null>(null)
const bgCanvasRef = ref<HTMLCanvasElement | null>(null)
const kgCanvasRef = ref<HTMLCanvasElement | null>(null)
let bgAnimId: number | null = null
let kgAnimId: number | null = null
const loading = ref(false)
const errorMsg = ref('')
const showTransition = ref(false)
const showRegisterNotify = ref(false)

const featureCards = [
  { icon: '🧠', title: 'AI认知诊断', desc: '从错误回答精准定位知识缺口', stat: '3,247', statLabel: '已分析学习行为' },
  { icon: '🕸', title: '知识图谱推理', desc: '构建你的网络知识关系地图', stat: '1,892', statLabel: '知识节点关联' },
  { icon: '🤖', title: 'Multi-Agent导师', desc: '教授/工程师/同伴三角色协同', stat: '98.3%', statLabel: '诊断精准率' },
]

const techBar = [
  { icon: '🤖', en: 'Multi-Agent', cn: '多智能体协同教学' },
  { icon: '🕸', en: 'Knowledge Graph', cn: '知识图谱驱动推理' },
  { icon: '📚', en: 'RAG', cn: '智能检索增强' },
  { icon: '👤', en: 'Digital Human', cn: 'AI数字导师' },
  { icon: '🎯', en: 'Adaptive Learning', cn: '动态规划成长路径' },
]

const loginTabs = [
  { key: 'account', label: '账号登录' },
  { key: 'phone', label: '手机号' },
  { key: 'guest', label: '游客体验' },
]

// ── Captcha ─────────────────────────────────────────────────────
function generateCaptcha() {
  const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
  captchaText.value = Array.from({ length: 4 }, () => chars[Math.floor(Math.random() * chars.length)]).join('')
  nextTick(() => drawCaptcha())
}
function drawCaptcha() {
  const cv = canvasRef.value; if (!cv) return
  const ctx = cv.getContext('2d'); if (!ctx) return
  cv.width = 90; cv.height = 36
  ctx.fillStyle = '#0a1628'; ctx.fillRect(0, 0, 90, 36)
  for (let i = 0; i < 3; i++) {
    ctx.strokeStyle = `hsla(${220 + Math.random() * 80},60%,60%,0.2)`
    ctx.beginPath(); ctx.moveTo(Math.random() * 90, Math.random() * 36); ctx.lineTo(Math.random() * 90, Math.random() * 36); ctx.stroke()
  }
  captchaText.value.split('').forEach((ch, i) => {
    ctx.save(); ctx.translate(10 + i * 20, 24); ctx.rotate((Math.random() - 0.5) * 0.4)
    ctx.fillStyle = `hsl(${180 + i * 50},80%,65%)`; ctx.font = 'bold 15px monospace'; ctx.fillText(ch, 0, 0); ctx.restore()
  })
}

// ── OTP ─────────────────────────────────────────────────────────
let countdownTimer: ReturnType<typeof setInterval> | null = null
function startCountdown() {
  otpCountdown.value = 60
  countdownTimer = setInterval(() => { otpCountdown.value--; if (otpCountdown.value <= 0) { clearInterval(countdownTimer!); countdownTimer = null } }, 1000)
}
async function handleSendOtp() {
  if (!phoneForm.phone || phoneForm.phone.length < 11) { errorMsg.value = '请输入正确的手机号'; return }
  loading.value = true; errorMsg.value = ''
  try { const res = await authApi.sendOtp(phoneForm.phone); otpSent.value = true; startCountdown(); if (res.demo_code) demoCode.value = res.demo_code }
  catch (e: unknown) { errorMsg.value = e instanceof Error ? e.message : '发送失败' }
  finally { loading.value = false }
}

// ── Login ────────────────────────────────────────────────────────
async function handleLogin() {
  errorMsg.value = ''
  if (activeTab.value === 'account' && !isRegisterMode.value) {
    if (captchaInput.value.toUpperCase() !== captchaText.value) { errorMsg.value = '验证码错误'; generateCaptcha(); captchaInput.value = ''; return }
    if (!accountForm.username || !accountForm.password) { errorMsg.value = '请输入用户名和密码'; return }
  }
  loading.value = true
  try {
    let result: { token: string; user: { userId: string; username: string; roleType: string; isFirstLogin: number } }
    if (activeTab.value === 'phone') { result = await authApi.verifyOtp(phoneForm.phone, phoneForm.code) }
    else if (activeTab.value === 'guest') { result = await authApi.guestLogin() }
    else if (isRegisterMode.value) {
      if (registerForm.password !== registerForm.confirmPwd) { errorMsg.value = '两次密码不一致'; loading.value = false; return }
      result = await authApi.register({ username: registerForm.username, password: registerForm.password, email: registerForm.email || undefined })
      showRegisterNotify.value = true
    } else { result = await authApi.login({ username: accountForm.username, password: accountForm.password }) }
    authStore.login(result.token, result.user); userStore.setUser(result.user.userId, result.user.username)
    showTransition.value = true
  } catch (e: unknown) {
    const errMsg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    errorMsg.value = errMsg || (e instanceof Error ? e.message : '登录失败'); generateCaptcha()
  } finally { loading.value = false }
}

// ── Background ambient canvas ────────────────────────────────────
function initBgAnimation() {
  const cv = bgCanvasRef.value; if (!cv) return
  const ctx = cv.getContext('2d'); if (!ctx) return
  const c = ctx as CanvasRenderingContext2D
  let w = cv.width = cv.offsetWidth; let h = cv.height = cv.offsetHeight
  const ns: { x:number;y:number;vx:number;vy:number;r:number;hue:number }[] = []
  for (let i = 0; i < 40; i++) ns.push({ x: Math.random()*w, y: Math.random()*h, vx: (Math.random()-.5)*.22, vy: (Math.random()-.5)*.22, r: 1+Math.random()*1.2, hue: 200+Math.random()*70 })
  function draw() {
    c.clearRect(0,0,w,h)
    for (const n of ns) { n.x += n.vx; n.y += n.vy; if(n.x<0||n.x>w) n.vx*=-1; if(n.y<0||n.y>h) n.vy*=-1 }
    for (let i=0;i<ns.length;i++) for (let j=i+1;j<ns.length;j++) { const dx=ns[i].x-ns[j].x,dy=ns[i].y-ns[j].y,d=Math.sqrt(dx*dx+dy*dy); if(d<100){c.strokeStyle=`rgba(80,140,255,${(1-d/100)*.12})`;c.lineWidth=.5;c.beginPath();c.moveTo(ns[i].x,ns[i].y);c.lineTo(ns[j].x,ns[j].y);c.stroke()} }
    for (const n of ns) { c.beginPath();c.arc(n.x,n.y,n.r,0,Math.PI*2);c.fillStyle=`hsla(${n.hue},70%,65%,.45)`;c.fill() }
    bgAnimId = requestAnimationFrame(draw)
  }
  draw()
  new ResizeObserver(() => { w=cv.width=cv.offsetWidth; h=cv.height=cv.offsetHeight }).observe(cv)
}

// ── Knowledge Graph canvas ───────────────────────────────────────
interface KGNode { label:string; bx:number; by:number; r:number; color:string; status:'core'|'mastered'|'learning'|'weak'|'unknown' }
const KG_NODES: KGNode[] = [
  { label:'知识\n图谱', bx:0, by:0, r:19, color:'#7c3aed', status:'core' },
  { label:'TCP', bx:-88, by:-48, r:13, color:'#22d3ee', status:'mastered' },
  { label:'HTTP', bx:85, by:-68, r:13, color:'#3b82f6', status:'mastered' },
  { label:'DNS', bx:98, by:58, r:12, color:'#10b981', status:'mastered' },
  { label:'UDP', bx:-98, by:58, r:12, color:'#22d3ee', status:'mastered' },
  { label:'TLS', bx:8, by:118, r:11, color:'#a78bfa', status:'learning' },
  { label:'BGP', bx:50, by:-128, r:10, color:'#f59e0b', status:'weak' },
  { label:'OSPF', bx:-68, by:-122, r:10, color:'#a78bfa', status:'learning' },
  { label:'ARP', bx:-142, by:4, r:9, color:'#22d3ee', status:'mastered' },
  { label:'ICMP', bx:142, by:12, r:9, color:'#a78bfa', status:'learning' },
  { label:'IPv6', bx:58, by:132, r:9, color:'#f59e0b', status:'weak' },
  { label:'QUIC', bx:-50, by:132, r:8, color:'#475569', status:'unknown' },
]
const KG_EDGES = [[0,1],[0,2],[0,3],[0,4],[0,5],[1,4],[2,3],[2,6],[1,7],[0,8],[0,9],[3,10],[5,11]]

function initKGAnimation() {
  const cv = kgCanvasRef.value; if (!cv) return
  const ctx = cv.getContext('2d'); if (!ctx) return
  const c = ctx as CanvasRenderingContext2D
  let W = cv.width = cv.offsetWidth; let H = cv.height = cv.offsetHeight
  let angle = 0; let tick = 0
  const pkts = KG_EDGES.map(() => ({ p: Math.random(), s: .0035+Math.random()*.003 }))

  function ha(hex: string, a: number) {
    const r=parseInt(hex.slice(1,3),16),g=parseInt(hex.slice(3,5),16),b=parseInt(hex.slice(5,7),16)
    return `rgba(${r},${g},${b},${a})`
  }

  function draw() {
    c.clearRect(0,0,W,H)
    angle += .0018; tick += .025
    const cx = W/2, cy = H/2

    const pos = KG_NODES.map((n,i) => {
      if (i===0) return {x:cx,y:cy}
      const co=Math.cos(angle),s=Math.sin(angle)
      return {x: cx + n.bx*co - n.by*s, y: cy + n.bx*s + n.by*co}
    })

    // Edges + packets
    KG_EDGES.forEach(([f,t],i) => {
      const fp=pos[f],tp=pos[t],fn=KG_NODES[f],tn=KG_NODES[t]
      const g=c.createLinearGradient(fp.x,fp.y,tp.x,tp.y)
      g.addColorStop(0,ha(fn.color,.22)); g.addColorStop(1,ha(tn.color,.14))
      c.strokeStyle=g; c.lineWidth=1.2
      c.beginPath(); c.moveTo(fp.x,fp.y); c.lineTo(tp.x,tp.y); c.stroke()
      pkts[i].p += pkts[i].s; if(pkts[i].p>1) pkts[i].p=0
      const px=fp.x+(tp.x-fp.x)*pkts[i].p, py=fp.y+(tp.y-fp.y)*pkts[i].p
      c.beginPath(); c.arc(px,py,2.5,0,Math.PI*2)
      c.fillStyle=fn.color; c.shadowColor=fn.color; c.shadowBlur=8; c.fill(); c.shadowBlur=0
    })

    // Nodes
    KG_NODES.forEach((n,i) => {
      const p=pos[i]
      const pf = n.status==='core' ? 1+.14*Math.sin(tick) : n.status==='learning' ? 1+.06*Math.sin(tick*1.2+i) : 1
      const r = n.r*pf
      c.shadowColor=n.color; c.shadowBlur=n.status==='core'?22:10
      c.beginPath(); c.arc(p.x,p.y,r,0,Math.PI*2)
      c.fillStyle=ha(n.color,.15); c.fill()
      c.strokeStyle=n.color; c.lineWidth=n.status==='core'?2:1.5; c.stroke(); c.shadowBlur=0
      c.fillStyle = n.status==='unknown' ? 'rgba(100,116,139,.55)' : 'rgba(226,232,240,.88)'
      c.font=`bold ${i===0?8:9}px monospace`; c.textAlign='center'; c.textBaseline='middle'
      if(n.label.includes('\n')){ const [a,b]=n.label.split('\n'); c.fillText(a,p.x,p.y-5); c.fillText(b,p.x,p.y+5) }
      else c.fillText(n.label,p.x,p.y)
    })
    kgAnimId = requestAnimationFrame(draw)
  }
  draw()
  new ResizeObserver(() => { W=cv.width=cv.offsetWidth; H=cv.height=cv.offsetHeight }).observe(cv)
}

onMounted(() => {
  generateCaptcha()
  if (authStore.isLoggedIn) router.push(route.query.redirect as string || '/')
  nextTick(() => { initBgAnimation(); initKGAnimation() })
})
onUnmounted(() => {
  if (bgAnimId) cancelAnimationFrame(bgAnimId)
  if (kgAnimId) cancelAnimationFrame(kgAnimId)
  if (countdownTimer) clearInterval(countdownTimer)
})

function handleTransitionDone() {
  if (authStore.user?.isFirstLogin === 1) router.push('/welcome')
  else router.push((route.query.redirect as string) || '/')
}

async function handleOAuthLogin(provider: 'qq'|'wechat') {
  loading.value = true; errorMsg.value = ''
  try {
    const res = await fetch(`/api/v1/auth/oauth/${provider}`); const data = await res.json()
    if (data.redirect_url) window.location.href = data.redirect_url
    else if (data.demo_token) {
      authStore.login(data.demo_token, data.user || {userId:`${provider}_demo`,username:`${provider}演示用户`,roleType:'student',isFirstLogin:0})
      userStore.setUser(data.user?.userId||`${provider}_demo`, data.user?.username||`${provider}演示用户`)
      showTransition.value = true
    } else errorMsg.value = `${provider==='qq'?'QQ':'微信'} 登录暂时不可用`
  } catch (e: unknown) { errorMsg.value = e instanceof Error ? e.message : 'OAuth 登录失败' }
  finally { loading.value = false }
}
</script>

<template>
  <SplitScreenTransition v-if="showTransition" @done="handleTransitionDone" />
  <RegisterSuccessNotify :visible="showRegisterNotify" @close="showRegisterNotify = false" />

  <div class="page">
    <canvas ref="bgCanvasRef" class="bg-cv"></canvas>

    <!-- Protocol background text -->
    <div class="proto-bg" aria-hidden="true">
      <span style="top:6%;left:4%">TCP</span><span style="top:19%;right:7%">HTTP/2</span>
      <span style="top:43%;left:2%">DNS</span><span style="bottom:22%;left:11%">UDP</span>
      <span style="top:13%;left:30%">TLS 1.3</span><span style="bottom:30%;right:4%">BGP</span>
      <span style="top:60%;right:17%">OSPF</span><span style="bottom:8%;right:22%">IPv6</span>
      <span style="top:35%;left:44%">QUIC</span><span style="bottom:46%;left:22%">ARP</span>
    </div>

    <!-- Top bar -->
    <header class="top-bar">
      <div class="logo"><span class="logo-hex">⬡</span><span class="logo-txt">Socrates Cube</span></div>
    </header>

    <!-- Main -->
    <main class="main">

      <!-- ── LEFT PANEL ── -->
      <div class="left">
        <div class="title-blk">
          <h1 class="t-en">Socrates Cube</h1>
          <h2 class="t-cn">苏格拉底方块</h2>
          <p class="t-sub">AI驱动的计算机网络智能学习空间</p>
          <div class="t-line"></div>
        </div>

        <div class="cg">
          <!-- Feature cards -->
          <div class="feat-col">
            <div class="fc" v-for="f in featureCards" :key="f.title">
              <div class="fc-top"><span class="fc-ic">{{f.icon}}</span><span class="fc-ti">{{f.title}}</span></div>
              <p class="fc-desc">{{f.desc}}</p>
              <div class="fc-stat-row"><span class="fc-stat">{{f.stat}}</span><span class="fc-slab">{{f.statLabel}}</span></div>
            </div>
          </div>

          <!-- KG Canvas -->
          <div class="kg-wrap">
            <canvas ref="kgCanvasRef" class="kg-cv"></canvas>

            <!-- CSS 3D Cube hero -->
            <div class="cube-rig">
              <div class="cube-persp">
                <div class="cube">
                  <div class="cf cf-f">TCP</div>
                  <div class="cf cf-b">OSL</div>
                  <div class="cf cf-r">HTTP</div>
                  <div class="cf cf-l">DNS</div>
                  <div class="cf cf-t"></div>
                  <div class="cf cf-bt"></div>
                </div>
              </div>
              <div class="holo-rings">
                <div class="hr r1"></div>
                <div class="hr r2"></div>
                <div class="hr r3"></div>
              </div>
              <div class="lbeam"></div>
            </div>

            <div class="ll ll-t">路由协议</div>
            <div class="ll ll-l">传输层</div>
            <div class="ll ll-r">应用层</div>
            <div class="ll ll-bl">网络层</div>
            <div class="ll ll-br">数据链路层</div>
          </div>
        </div>

        <!-- Alice anchor -->
        <div class="alice-bar">
          <div class="alice-av">
            <img src="/images/virtual_teacher.png" alt="Alice" />
            <span class="alice-ring"></span>
          </div>
          <div class="alice-bubble">
            <p class="ab-hi">你好，我是 <strong>Alice</strong> 👋</p>
            <p class="ab-sub">你的AI学习助手，随时为你提供帮助！</p>
            <span class="ab-wave">▁▂▃▄▃▂▁▂▃▄▃▂▁</span>
          </div>
        </div>
      </div>

      <!-- ── RIGHT PANEL ── -->
      <div class="right">

        <div class="lcard">
          <h2 class="lc-ti">{{ isRegisterMode ? '创建账号' : '欢迎回来 👋' }}</h2>
          <p class="lc-sub">{{ isRegisterMode ? '注册后开始个性化学习之旅' : '登录你的学习空间，继续探索知识的边界' }}</p>

          <!-- Tabs -->
          <div v-if="!isRegisterMode" class="tabs">
            <button v-for="tab in loginTabs" :key="tab.key" class="tab" :class="{active: activeTab===tab.key}" @click="activeTab=tab.key as LoginTab; errorMsg=''">{{tab.label}}</button>
          </div>

          <div v-if="errorMsg" class="err">⚠ {{errorMsg}}</div>
          <div v-if="demoCode" class="demo-tip">演示验证码：<strong>{{demoCode}}</strong></div>

          <!-- Account / Register -->
          <form v-if="activeTab==='account'" @submit.prevent="handleLogin" class="form">
            <template v-if="isRegisterMode">
              <div class="fi-wrap"><span class="fi">◎</span><input v-model="registerForm.username" type="text" placeholder="设置用户名（2–50字符）" class="inp" required /></div>
              <div class="fi-wrap"><span class="fi">✉</span><input v-model="registerForm.email" type="email" placeholder="邮箱（可选）" class="inp" /></div>
              <div class="fi-wrap"><span class="fi">⬡</span><input v-model="registerForm.password" type="password" placeholder="至少6位密码" class="inp" required /></div>
              <div class="fi-wrap"><span class="fi">⬡</span><input v-model="registerForm.confirmPwd" type="password" placeholder="再次输入密码" class="inp" required /></div>
            </template>
            <template v-else>
              <div class="fi-wrap"><span class="fi">◎</span><input v-model="accountForm.username" type="text" placeholder="请输入用户名或邮箱" class="inp" required autocomplete="username" /></div>
              <div class="fi-wrap"><span class="fi">⬡</span><input v-model="accountForm.password" type="password" placeholder="请输入密码" class="inp" required autocomplete="current-password" /></div>
              <div class="cap-row">
                <div class="fi-wrap cap-f"><span class="fi">✦</span><input v-model="captchaInput" type="text" placeholder="验证码" maxlength="4" class="inp" /></div>
                <canvas ref="canvasRef" width="90" height="36" class="cap-cv" @click="generateCaptcha" title="点击刷新"></canvas>
              </div>
              <div class="rem-row">
                <label class="rem-lbl"><input type="checkbox" class="cb" /><span>记住我</span></label>
                <button type="button" class="forgot">忘记密码?</button>
              </div>
            </template>
            <button type="submit" class="sbtn" :disabled="loading"><span v-if="loading" class="spin"></span><span v-else>{{ isRegisterMode ? '注册并进入' : '立即登录' }}</span></button>
          </form>

          <!-- Phone -->
          <form v-else-if="activeTab==='phone'" @submit.prevent="handleLogin" class="form">
            <div class="fi-wrap"><span class="fi">☎</span><input v-model="phoneForm.phone" type="tel" placeholder="请输入11位手机号" maxlength="11" class="inp" required /></div>
            <div class="otp-row">
              <div class="fi-wrap otp-f"><span class="fi">✦</span><input v-model="phoneForm.code" type="text" placeholder="6位验证码" maxlength="6" class="inp" required /></div>
              <button type="button" class="otp-btn" :disabled="otpCountdown>0||loading" @click="handleSendOtp">{{otpCountdown>0?`${otpCountdown}s`:'获取验证码'}}</button>
            </div>
            <button type="submit" class="sbtn" :disabled="loading||!otpSent"><span v-if="loading" class="spin"></span><span v-else>手机号登录</span></button>
          </form>

          <!-- Guest -->
          <div v-else-if="activeTab==='guest'" class="guest">
            <div class="g-ic">👤</div>
            <p class="g-desc">以游客身份快速体验，学习记录保留至本次会话结束</p>
            <button class="sbtn sbtn-g" :disabled="loading" @click="handleLogin"><span v-if="loading" class="spin"></span><span v-else>立即体验</span></button>
          </div>

          <div class="ftr">
            <span v-if="!isRegisterMode">还没有账号？<button class="lnk" @click="isRegisterMode=true;activeTab='account'">立即注册</button></span>
            <span v-else>已有账号？<button class="lnk" @click="isRegisterMode=false">返回登录</button></span>
          </div>

          <div v-if="!isRegisterMode" class="oauth">
            <div class="odiv"><span class="dl"></span><span class="dt">其他登录方式</span><span class="dl"></span></div>
            <div class="orow">
              <button class="ob" :disabled="loading" @click="handleOAuthLogin('wechat')"><img src="@/assets/icons/wechat.png" alt="微信" /></button>
              <button class="ob" :disabled="loading" @click="handleOAuthLogin('qq')"><img src="@/assets/icons/qq.png" alt="QQ" /></button>
            </div>
          </div>
        </div>

        <!-- AI Init Status -->
        <div class="init-card">
          <div class="ih"><span class="idot"></span><span class="itxt">Socrates AI 正在分析你的学习空间...</span></div>
          <div class="ichecks">
            <div class="ic-item"><span class="ck">✓</span>加载计算机网络知识图谱</div>
            <div class="ic-item"><span class="ck">✓</span>激活多Agent导师系统</div>
            <div class="ic-item"><span class="ck">✓</span>初始化RAG知识检索库</div>
          </div>
          <div class="istats">
            <div class="ist"><span class="isn">3,247</span><span class="isl">学习档案</span></div>
            <div class="ist"><span class="isn">50+</span><span class="isl">错误模式</span></div>
            <div class="ist"><span class="isn">295</span><span class="isl">协议知识库</span></div>
          </div>
        </div>

      </div>
    </main>

    <!-- Tech bar -->
    <footer class="tech-bar">
      <div class="tb-item" v-for="t in techBar" :key="t.en">
        <span class="tb-ic">{{t.icon}}</span>
        <div><div class="tb-en">{{t.en}}</div><div class="tb-cn">{{t.cn}}</div></div>
      </div>
    </footer>
    <div class="s2-footer">© 2025 Socrates Cube：智能学习，因你而变</div>
  </div>
</template>

<style scoped>
/* ── Page ──────────────────────────────────────────────────────── */
.page { min-height:100vh; background:radial-gradient(ellipse at 30% 40%,#0d1a3a 0%,#060d1f 55%,#030812 100%); font-family:'Inter','PingFang SC',system-ui,sans-serif; position:relative; overflow:hidden; display:flex; flex-direction:column; color:#f1f5f9; }
.bg-cv { position:fixed; inset:0; width:100%; height:100%; z-index:0; pointer-events:none; }

/* Protocol bg text */
.proto-bg { position:fixed; inset:0; z-index:1; pointer-events:none; }
.proto-bg span { position:absolute; font-family:monospace; font-size:13px; font-weight:800; letter-spacing:2px; color:rgba(100,170,255,.065); user-select:none; }

/* ── Top bar ───────────────────────────────────────────────────── */
.top-bar { position:relative; z-index:10; display:flex; align-items:center; padding:14px 40px; border-bottom:1px solid rgba(255,255,255,.04); background:rgba(3,8,20,.55); backdrop-filter:blur(12px); }
.logo { display:flex; align-items:center; gap:10px; }
.logo-hex { font-size:20px; color:#60a5fa; filter:drop-shadow(0 0 8px rgba(96,165,250,.6)); }
.logo-txt { font-size:15px; font-weight:700; color:rgba(226,232,240,.9); }

/* ── Main grid ─────────────────────────────────────────────────── */
.main { position:relative; z-index:5; flex:1; display:grid; grid-template-columns:1fr 400px; gap:24px; padding:24px 36px 16px; align-items:start; }

/* ── Left panel ────────────────────────────────────────────────── */
.left { display:flex; flex-direction:column; gap:18px; }

/* Title */
.title-blk { }
.t-en { font-size:50px; font-weight:900; margin:0; line-height:1.05; background:linear-gradient(100deg,#60a5fa 0%,#a78bfa 45%,#f472b6 100%); -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent; animation:tglow 3s ease-in-out infinite; }
@keyframes tglow { 0%,100%{filter:drop-shadow(0 0 18px rgba(96,165,250,.3))} 50%{filter:drop-shadow(0 0 32px rgba(167,139,250,.5))} }
.t-cn { font-size:26px; font-weight:800; margin:4px 0 8px; color:rgba(226,232,240,.95); }
.t-sub { font-size:14px; color:rgba(148,163,184,.7); margin:0 0 12px; }
.t-line { width:56px; height:3px; background:linear-gradient(90deg,#60a5fa,#a78bfa); border-radius:2px; }

/* Content grid: feature-cards + KG canvas */
.cg { display:grid; grid-template-columns:210px 1fr; gap:14px; flex:1; min-height:340px; }

/* Feature cards */
.feat-col { display:flex; flex-direction:column; gap:10px; justify-content:center; }
.fc { background:rgba(255,255,255,.03); border:1px solid rgba(255,255,255,.07); border-left:2px solid rgba(96,165,250,.4); border-radius:14px; padding:14px 16px; backdrop-filter:blur(10px); transition:all .3s; }
.fc:hover { background:rgba(96,165,250,.06); border-left-color:rgba(96,165,250,.8); transform:translateX(3px); }
.fc-top { display:flex; align-items:center; gap:8px; margin-bottom:5px; }
.fc-ic { font-size:18px; filter:drop-shadow(0 0 5px rgba(255,255,255,.15)); }
.fc-ti { font-size:12px; font-weight:700; color:rgba(226,232,240,.9); }
.fc-desc { font-size:11px; color:rgba(148,163,184,.65); line-height:1.5; margin:0 0 8px; }
.fc-stat-row { display:flex; align-items:baseline; gap:5px; }
.fc-stat { font-size:18px; font-weight:900; color:#60a5fa; font-family:monospace; }
.fc-slab { font-size:10px; color:rgba(148,163,184,.55); }

/* KG canvas */
.kg-wrap { position:relative; display:flex; align-items:center; justify-content:center; }
.kg-cv { width:100%; height:340px; display:block; }
.ll { position:absolute; font-size:11px; font-weight:600; color:rgba(96,165,250,.75); background:rgba(96,165,250,.08); border:1px solid rgba(96,165,250,.2); border-radius:6px; padding:3px 8px; white-space:nowrap; letter-spacing:.04em; backdrop-filter:blur(4px); pointer-events:none; }
.ll-t  { top:6%; left:50%; transform:translateX(-50%); }
.ll-l  { top:46%; left:2%; }
.ll-r  { top:46%; right:2%; }
.ll-bl { bottom:10%; left:10%; }
.ll-br { bottom:10%; right:8%; }

/* ── CSS 3D Cube ──────────────────────────────────────────────── */
.cube-rig { position:absolute; top:50%; left:50%; transform:translate(-50%,-56%); display:flex; flex-direction:column; align-items:center; pointer-events:none; z-index:3; }
.cube-persp { width:180px; height:180px; perspective:500px; }
.cube { width:180px; height:180px; position:relative; transform-style:preserve-3d; animation:cubeR 14s linear infinite; }
@keyframes cubeR { from{transform:rotateX(22deg) rotateY(0deg)} to{transform:rotateX(22deg) rotateY(360deg)} }
/* Global cube glow */
.cube::before { content:''; position:absolute; top:50%; left:50%; width:280px; height:280px; transform:translate(-50%,-50%); background:radial-gradient(ellipse,rgba(80,140,255,.14) 0%,transparent 65%); pointer-events:none; }
/* Faces */
.cf { position:absolute; width:180px; height:180px; background:rgba(96,180,255,.05); border:1.5px solid rgba(96,180,255,.55); display:flex; align-items:center; justify-content:center; font-size:22px; font-weight:900; color:rgba(140,215,255,.88); font-family:'SF Mono','JetBrains Mono',monospace; letter-spacing:2px; text-shadow:0 0 18px rgba(100,190,255,.95),0 0 35px rgba(100,190,255,.45); box-shadow:inset 0 0 50px rgba(96,180,255,.06),0 0 20px rgba(96,180,255,.08); }
.cf::after { content:''; position:absolute; width:52%; height:52%; background:rgba(140,70,255,.07); border:1px solid rgba(140,70,255,.32); }
.cf-f  { transform:translateZ(90px); }
.cf-b  { transform:rotateY(180deg) translateZ(90px); }
.cf-r  { transform:rotateY(90deg) translateZ(90px); }
.cf-l  { transform:rotateY(-90deg) translateZ(90px); }
.cf-t  { transform:rotateX(90deg) translateZ(90px); background:rgba(120,70,255,.07); border-color:rgba(130,80,255,.45); }
.cf-bt { transform:rotateX(-90deg) translateZ(90px); background:rgba(120,70,255,.07); border-color:rgba(130,80,255,.45); }
/* Holographic rings */
.holo-rings { position:relative; width:300px; height:45px; margin-top:-18px; }
.hr { position:absolute; left:50%; top:50%; border-radius:50%; border:1px solid rgba(96,180,255,.45); animation:hrp 2.2s ease-in-out infinite; }
.r1 { width:150px; height:38px; transform:translate(-50%,-50%) rotateX(76deg); animation-delay:0s; }
.r2 { width:210px; height:54px; transform:translate(-50%,-50%) rotateX(76deg); animation-delay:.65s; border-color:rgba(96,180,255,.28); }
.r3 { width:272px; height:70px; transform:translate(-50%,-50%) rotateX(76deg); animation-delay:1.3s; border-color:rgba(96,180,255,.15); }
@keyframes hrp { 0%,100%{opacity:.25}50%{opacity:.9} }
/* Light beam below cube */
.lbeam { width:140px; height:75px; margin-top:-22px; background:linear-gradient(to bottom,rgba(80,130,255,.22) 0%,transparent 100%); clip-path:polygon(22% 0%,78% 0%,100% 100%,0% 100%); filter:blur(7px); }

/* Alice bar */
.alice-bar { display:flex; align-items:center; gap:14px; padding:10px 0; }
.alice-av { position:relative; flex-shrink:0; width:60px; height:60px; }
.alice-av img { width:60px; height:60px; border-radius:50%; object-fit:cover; border:2px solid rgba(96,165,250,.4); }
.alice-ring { position:absolute; inset:-4px; border-radius:50%; border:1.5px solid rgba(96,165,250,.3); animation:aring 3s linear infinite; }
@keyframes aring { from{transform:rotate(0);opacity:.8} to{transform:rotate(360deg);opacity:.3} }
.alice-bubble { background:rgba(255,255,255,.03); border:1px solid rgba(255,255,255,.08); border-radius:14px; padding:10px 14px; backdrop-filter:blur(10px); }
.ab-hi { font-size:13px; color:rgba(226,232,240,.9); margin:0 0 3px; }
.ab-hi strong { color:#60a5fa; }
.ab-sub { font-size:11px; color:rgba(148,163,184,.65); margin:0 0 5px; }
.ab-wave { font-size:9px; color:rgba(96,165,250,.4); letter-spacing:1px; }

/* ── Right panel ───────────────────────────────────────────────── */
.right { display:flex; flex-direction:column; gap:12px; }

/* Login card */
.lcard { background:rgba(6,12,28,.72); border:1px solid rgba(255,255,255,.08); border-radius:20px; padding:26px 24px; backdrop-filter:blur(22px); box-shadow:0 20px 60px rgba(0,0,0,.55),0 0 0 1px rgba(255,255,255,.03); }
.lc-ti { font-size:20px; font-weight:800; color:#f1f5f9; margin:0 0 4px; }
.lc-sub { font-size:12px; color:rgba(148,163,184,.65); margin:0 0 16px; line-height:1.5; }

/* Tabs */
.tabs { display:flex; background:rgba(255,255,255,.03); border:1px solid rgba(255,255,255,.05); border-radius:10px; padding:3px; margin-bottom:14px; }
.tab { flex:1; padding:7px 4px; border:none; background:transparent; border-radius:8px; font-size:12px; font-weight:500; color:rgba(148,163,184,.6); cursor:pointer; transition:all .2s; font-family:inherit; }
.tab.active { background:rgba(99,102,241,.18); color:#a5b4fc; font-weight:700; }
.tab:not(.active):hover { color:#cbd5e1; background:rgba(255,255,255,.03); }

.err { background:rgba(239,68,68,.1); border:1px solid rgba(239,68,68,.3); border-radius:9px; padding:8px 12px; font-size:12px; color:#fca5a5; margin-bottom:10px; }
.demo-tip { background:rgba(59,130,246,.1); border:1px solid rgba(59,130,246,.3); border-radius:9px; padding:7px 12px; font-size:12px; color:#93c5fd; margin-bottom:8px; }

/* Form */
.form { display:flex; flex-direction:column; gap:10px; }
.fi-wrap { display:flex; align-items:center; background:rgba(255,255,255,.04); border:1.5px solid rgba(255,255,255,.08); border-radius:11px; transition:all .2s; overflow:hidden; }
.fi-wrap:focus-within { border-color:rgba(99,102,241,.5); box-shadow:0 0 0 3px rgba(99,102,241,.1); background:rgba(255,255,255,.06); }
.fi { padding:0 0 0 12px; font-size:12px; color:rgba(148,163,184,.4); flex-shrink:0; }
.inp { flex:1; padding:11px 12px 11px 8px; border:none; background:transparent; font-size:13px; color:#f1f5f9; outline:none; font-family:inherit; }
.inp::placeholder { color:rgba(148,163,184,.4); }

/* Captcha row */
.cap-row { display:flex; gap:8px; align-items:center; }
.cap-f { flex:1; }
.cap-cv { width:90px; height:36px; border-radius:9px; cursor:pointer; flex-shrink:0; border:1.5px solid rgba(255,255,255,.08); }

/* Remember row */
.rem-row { display:flex; align-items:center; justify-content:space-between; margin-top:-2px; }
.rem-lbl { display:flex; align-items:center; gap:5px; font-size:11px; color:rgba(148,163,184,.6); cursor:pointer; }
.cb { accent-color:#6366f1; }
.forgot { background:none; border:none; font-size:11px; color:rgba(148,163,184,.55); cursor:pointer; font-family:inherit; transition:color .2s; }
.forgot:hover { color:#a5b4fc; }

/* OTP */
.otp-row { display:flex; gap:8px; }
.otp-f { flex:1; }
.otp-btn { padding:11px 10px; background:rgba(99,102,241,.1); border:1.5px solid rgba(99,102,241,.25); border-radius:11px; font-size:11px; color:#a5b4fc; cursor:pointer; white-space:nowrap; font-weight:600; font-family:inherit; transition:all .2s; }
.otp-btn:disabled { opacity:.45; cursor:not-allowed; }
.otp-btn:not(:disabled):hover { background:rgba(99,102,241,.2); }

/* Submit btn */
.sbtn { padding:13px; background:linear-gradient(135deg,#7c3aed 0%,#6366f1 50%,#0891b2 100%); border:none; border-radius:12px; color:white; font-size:14px; font-weight:700; cursor:pointer; display:flex; align-items:center; justify-content:center; gap:8px; position:relative; overflow:hidden; transition:all .3s; font-family:inherit; margin-top:2px; }
.sbtn::before { content:''; position:absolute; top:0; left:-100%; width:100%; height:100%; background:linear-gradient(90deg,transparent,rgba(255,255,255,.12),transparent); transition:left .5s; }
.sbtn:hover:not(:disabled)::before { left:100%; }
.sbtn:hover:not(:disabled) { transform:translateY(-1px); box-shadow:0 8px 28px rgba(99,102,241,.45); }
.sbtn:disabled { opacity:.45; cursor:not-allowed; }
.sbtn-g { background:linear-gradient(135deg,#059669,#10b981) !important; }
.sbtn-g:hover:not(:disabled) { box-shadow:0 8px 28px rgba(16,185,129,.4) !important; }

.spin { width:15px; height:15px; border:2px solid rgba(255,255,255,.3); border-top-color:white; border-radius:50%; animation:sp .7s linear infinite; }
@keyframes sp { to { transform:rotate(360deg); } }

/* Guest */
.guest { text-align:center; padding:10px 0; }
.g-ic { font-size:40px; margin-bottom:10px; }
.g-desc { font-size:13px; color:rgba(148,163,184,.75); line-height:1.6; margin-bottom:18px; }

/* Footer link */
.ftr { margin-top:14px; text-align:center; font-size:12px; color:rgba(148,163,184,.6); }
.lnk { background:none; border:none; color:#60a5fa; font-size:12px; cursor:pointer; font-weight:600; text-decoration:underline; text-underline-offset:2px; font-family:inherit; }
.lnk:hover { color:#93c5fd; }

/* OAuth */
.oauth { margin-top:14px; }
.odiv { display:flex; align-items:center; gap:8px; margin-bottom:10px; }
.dl { flex:1; height:1px; background:rgba(255,255,255,.06); }
.dt { font-size:11px; color:rgba(148,163,184,.4); white-space:nowrap; }
.orow { display:flex; justify-content:center; gap:16px; }
.ob { width:42px; height:42px; border-radius:50%; border:1px solid rgba(255,255,255,.1); background:rgba(255,255,255,.04); cursor:pointer; display:flex; align-items:center; justify-content:center; transition:all .25s; }
.ob img { width:34px; height:34px; border-radius:50%; object-fit:cover; }
.ob:hover:not(:disabled) { transform:translateY(-2px); background:rgba(255,255,255,.09); box-shadow:0 5px 14px rgba(255,255,255,.07); }
.ob:disabled { opacity:.45; cursor:not-allowed; }

/* ── AI Init card ──────────────────────────────────────────────── */
.init-card { background:rgba(6,12,28,.65); border:1px solid rgba(99,102,241,.18); border-radius:16px; padding:14px 18px; backdrop-filter:blur(14px); }
.ih { display:flex; align-items:center; gap:8px; margin-bottom:10px; }
.idot { width:8px; height:8px; border-radius:50%; background:#4ade80; box-shadow:0 0 6px rgba(74,222,128,.7); animation:ipulse 1.5s ease-in-out infinite; }
@keyframes ipulse { 0%,100%{opacity:.7}50%{opacity:1} }
.itxt { font-size:12px; font-weight:600; color:rgba(148,163,184,.8); }
.ichecks { display:flex; flex-direction:column; gap:5px; margin-bottom:12px; }
.ic-item { font-size:11px; color:rgba(148,163,184,.65); display:flex; align-items:center; gap:6px; }
.ck { color:#4ade80; font-size:11px; flex-shrink:0; }
.istats { display:flex; gap:0; border-top:1px solid rgba(255,255,255,.06); padding-top:10px; }
.ist { flex:1; text-align:center; border-right:1px solid rgba(255,255,255,.05); }
.ist:last-child { border-right:none; }
.isn { display:block; font-size:16px; font-weight:900; color:#60a5fa; font-family:monospace; }
.isl { display:block; font-size:10px; color:rgba(148,163,184,.5); margin-top:2px; }

/* ── Tech bar ──────────────────────────────────────────────────── */
.tech-bar { position:relative; z-index:10; display:flex; justify-content:center; padding:10px 36px; background:rgba(3,8,20,.65); border-top:1px solid rgba(255,255,255,.04); backdrop-filter:blur(12px); }
.tb-item { display:flex; align-items:center; gap:10px; padding:7px 22px; border-right:1px solid rgba(255,255,255,.04); transition:background .3s; }
.tb-item:last-child { border-right:none; }
.tb-item:hover { background:rgba(255,255,255,.03); }
.tb-ic { font-size:20px; filter:drop-shadow(0 0 5px rgba(255,255,255,.12)); }
.tb-en { font-size:11px; font-weight:700; color:rgba(226,232,240,.8); }
.tb-cn { font-size:9px; color:rgba(148,163,184,.5); margin-top:1px; }
.s2-footer { text-align:center; font-size:11px; color:rgba(148,163,184,.3); padding:6px; position:relative; z-index:10; }

/* ── Responsive ────────────────────────────────────────────────── */
@media (max-width:1100px) {
  .main { grid-template-columns:1fr; padding:16px 20px; }
  .left { display:none; }
  .tech-bar { flex-wrap:wrap; gap:4px; }
  .tb-item { padding:5px 12px; }
}
@media (max-width:480px) {
  .right { padding:0; }
  .lcard { padding:20px 16px; border-radius:16px; }
}
</style>
