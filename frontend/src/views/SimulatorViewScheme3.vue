<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useSimulatorStore } from '@/stores/simulatorStore'

const store = useSimulatorStore()
const canvasRef = ref<HTMLCanvasElement>()
const playerRootRef = ref<HTMLElement>()

interface SimStep {
  from: 'client' | 'server'
  to: 'client' | 'server'
  flags: string[]
  seq: number
  ack: number
  clientState: string
  serverState: string
  desc: string
  dataLen?: number
}

const scenarios = [
  { label: 'TCP 三次握手', value: 'three_way_handshake', desc: '建立 TCP 连接的标准流程' },
  { label: 'TCP 四次挥手', value: 'four_way_wavehand', desc: '优雅关闭 TCP 连接' },
  { label: 'TCP 滑动窗口', value: 'sliding_window', desc: '连续数据传输与流量控制' },
  { label: 'HTTP 请求响应', value: 'http_request', desc: '应用层请求与响应过程' },
  { label: 'HTTP 分层封装', value: 'http_encapsulation', desc: '数据从上到下逐层封装' },
  { label: 'DNS 解析', value: 'dns_resolution', desc: '域名到IP的解析过程' },
  { label: '拥塞控制', value: 'congestion_control_basic', desc: 'TCP 拥塞窗口变化过程' },
]

const stepsMap: Record<string, SimStep[]> = {
  three_way_handshake: [
    { from: 'client', to: 'server', flags: ['SYN'], seq: 1000, ack: 0, clientState: 'SYN_SENT', serverState: 'LISTEN', desc: '客户端发送连接请求，初始序列号 ISN=1000' },
    { from: 'server', to: 'client', flags: ['SYN', 'ACK'], seq: 2000, ack: 1001, clientState: 'SYN_SENT', serverState: 'SYN_RCVD', desc: '服务端确认并同步，分配初始序列号 ISN=2000' },
    { from: 'client', to: 'server', flags: ['ACK'], seq: 1001, ack: 2001, clientState: 'ESTABLISHED', serverState: 'ESTABLISHED', desc: '客户端确认，双方进入 ESTABLISHED 状态，连接建立完成' },
  ],
  four_way_wavehand: [
    { from: 'client', to: 'server', flags: ['FIN', 'ACK'], seq: 500, ack: 400, clientState: 'FIN_WAIT_1', serverState: 'ESTABLISHED', desc: '客户端发起关闭请求，发送 FIN+ACK' },
    { from: 'server', to: 'client', flags: ['ACK'], seq: 400, ack: 501, clientState: 'FIN_WAIT_2', serverState: 'CLOSE_WAIT', desc: '服务端确认收到 FIN，进入 CLOSE_WAIT' },
    { from: 'server', to: 'client', flags: ['FIN', 'ACK'], seq: 401, ack: 501, clientState: 'TIME_WAIT', serverState: 'LAST_ACK', desc: '服务端发送 FIN，请求关闭连接' },
    { from: 'client', to: 'server', flags: ['ACK'], seq: 501, ack: 402, clientState: 'CLOSED', serverState: 'CLOSED', desc: '客户端最后确认，等待 2MSL 后关闭' },
  ],
  sliding_window: [
    { from: 'client', to: 'server', flags: ['ACK'], seq: 1000, ack: 1, clientState: 'ESTABLISHED', serverState: 'ESTABLISHED', desc: 'ACK 确认，窗口大小通告 win=4096', dataLen: 0 },
    { from: 'client', to: 'server', flags: ['PSH', 'ACK'], seq: 1000, ack: 1, clientState: 'ESTABLISHED', serverState: 'ESTABLISHED', desc: '客户端发送数据段 #1，长度 1024 字节', dataLen: 1024 },
    { from: 'client', to: 'server', flags: ['PSH', 'ACK'], seq: 2024, ack: 1, clientState: 'ESTABLISHED', serverState: 'ESTABLISHED', desc: '客户端发送数据段 #2，长度 1024 字节', dataLen: 1024 },
    { from: 'server', to: 'client', flags: ['ACK'], seq: 1, ack: 2024, clientState: 'ESTABLISHED', serverState: 'ESTABLISHED', desc: '服务端累积确认收到前两个段', dataLen: 0 },
    { from: 'client', to: 'server', flags: ['PSH', 'ACK'], seq: 3048, ack: 1, clientState: 'ESTABLISHED', serverState: 'ESTABLISHED', desc: '客户端发送数据段 #3，长度 1024 字节', dataLen: 1024 },
    { from: 'server', to: 'client', flags: ['ACK'], seq: 1, ack: 4072, clientState: 'ESTABLISHED', serverState: 'ESTABLISHED', desc: '服务端确认所有数据，通告窗口 win=2048', dataLen: 0 },
  ],
  http_request: [
    { from: 'client', to: 'server', flags: ['SYN'], seq: 100, ack: 0, clientState: 'SYN_SENT', serverState: 'LISTEN', desc: '建立 TCP 连接 — 客户端发送 SYN' },
    { from: 'server', to: 'client', flags: ['SYN', 'ACK'], seq: 200, ack: 101, clientState: 'SYN_SENT', serverState: 'SYN_RCVD', desc: '服务端回复 SYN+ACK' },
    { from: 'client', to: 'server', flags: ['ACK'], seq: 101, ack: 201, clientState: 'ESTABLISHED', serverState: 'ESTABLISHED', desc: '客户端确认，TCP 连接建立' },
    { from: 'client', to: 'server', flags: ['PSH', 'ACK'], seq: 101, ack: 201, clientState: 'ESTABLISHED', serverState: 'ESTABLISHED', desc: '客户端发送 HTTP GET 请求报文', dataLen: 128 },
    { from: 'server', to: 'client', flags: ['PSH', 'ACK'], seq: 201, ack: 229, clientState: 'ESTABLISHED', serverState: 'ESTABLISHED', desc: '服务端发送 HTTP 200 OK 响应', dataLen: 2048 },
    { from: 'client', to: 'server', flags: ['ACK'], seq: 229, ack: 2249, clientState: 'ESTABLISHED', serverState: 'ESTABLISHED', desc: '客户端确认收到响应数据', dataLen: 0 },
    { from: 'client', to: 'server', flags: ['FIN', 'ACK'], seq: 229, ack: 2249, clientState: 'FIN_WAIT_1', serverState: 'CLOSE_WAIT', desc: '客户端发送 FIN 关闭连接' },
    { from: 'server', to: 'client', flags: ['ACK'], seq: 2249, ack: 230, clientState: 'FIN_WAIT_2', serverState: 'LAST_ACK', desc: '服务端确认 FIN' },
  ],
  http_encapsulation: [
    { from: 'client', to: 'server', flags: ['APP'], seq: 0, ack: 0, clientState: '应用层', serverState: '应用层', desc: '应用层：HTTP 请求报文生成' },
    { from: 'client', to: 'server', flags: ['TCP'], seq: 0, ack: 0, clientState: '传输层', serverState: '传输层', desc: '传输层：添加 TCP 头部' },
    { from: 'client', to: 'server', flags: ['IP'], seq: 0, ack: 0, clientState: '网络层', serverState: '网络层', desc: '网络层：添加 IP 头部' },
    { from: 'client', to: 'server', flags: ['ETH'], seq: 0, ack: 0, clientState: '数据链路层', serverState: '数据链路层', desc: '数据链路层：添加以太网帧头' },
    { from: 'client', to: 'server', flags: ['PHY'], seq: 0, ack: 0, clientState: '物理层', serverState: '物理层', desc: '物理层：转换为比特流' },
    { from: 'server', to: 'client', flags: ['DE-CAP'], seq: 0, ack: 0, clientState: '物理层→应用层', serverState: '接收完成', desc: '服务端逐层解封装' },
  ],
  dns_resolution: [
    { from: 'client', to: 'server', flags: ['QUERY'], seq: 1, ack: 0, clientState: '发起查询', serverState: '本地DNS', desc: '客户端向本地 DNS 发起递归查询：www.example.com → ?' },
    { from: 'server', to: 'client', flags: ['ITER'], seq: 2, ack: 1, clientState: '等待', serverState: '根服务器', desc: '向根服务器迭代查询，获得 .com TLD 地址' },
    { from: 'server', to: 'client', flags: ['ITER'], seq: 3, ack: 2, clientState: '等待', serverState: 'TLD服务器', desc: '向 .com TLD 查询，获得 example.com 权威 DNS 地址' },
    { from: 'server', to: 'client', flags: ['ITER'], seq: 4, ack: 3, clientState: '等待', serverState: '权威DNS', desc: '向权威 DNS 查询，获得 IP: 93.184.216.34' },
    { from: 'server', to: 'client', flags: ['RESP'], seq: 5, ack: 4, clientState: '解析完成', serverState: '本地DNS', desc: '本地 DNS 返回结果：www.example.com → 93.184.216.34' },
  ],
  congestion_control_basic: [
    { from: 'client', to: 'server', flags: ['SS'], seq: 1, ack: 0, clientState: '慢启动 cwnd=1', serverState: '等待', desc: '慢启动：cwnd=1 MSS，发送1个报文段' },
    { from: 'server', to: 'client', flags: ['ACK'], seq: 1, ack: 1, clientState: '慢启动 cwnd=2', serverState: '确认', desc: '收到ACK，cwnd翻倍：1→2 MSS（指数增长）' },
    { from: 'client', to: 'server', flags: ['SS'], seq: 2, ack: 0, clientState: '慢启动 cwnd=4', serverState: '等待', desc: '发送2段，cwnd→4 MSS' },
    { from: 'client', to: 'server', flags: ['CA'], seq: 4, ack: 0, clientState: '拥塞避免 cwnd=5', serverState: '等待', desc: '达到ssthresh，进入拥塞避免：线性增长' },
    { from: 'server', to: 'client', flags: ['LOSS'], seq: 5, ack: 0, clientState: '丢包！cwnd减半', serverState: '丢包检测', desc: '丢包！ssthresh=cwnd/2，快重传/快恢复' },
    { from: 'client', to: 'server', flags: ['CA'], seq: 6, ack: 0, clientState: '拥塞避免 线性增长', serverState: '恢复', desc: '重新进入拥塞避免，cwnd线性增长' },
  ],
}

const packetSteps = computed(() => stepsMap[store.scenario] || stepsMap.three_way_handshake)
const currentScenario = computed(() => scenarios.find(s => s.value === store.scenario) || scenarios[0])

let animId = 0
const stepProgress = ref(0)
const isInTransition = ref(false)
const detailVisible = ref(false)
const detailStep = ref<SimStep | null>(null)
const detailStepIndex = ref(0)

// UI state
const dropdownOpen = ref(false)
const isFullscreen = ref(false)

// Simulation parameters
const simParams = ref({ windowSize: 4096, rtt: 50, packetLoss: 0 })
const activePreset = ref('默认参数')
const networkQuality = ref('低延迟')

const presets = [
  { label: '默认参数', windowSize: 4096, rtt: 50, packetLoss: 0, speed: 1 },
  { label: '高延迟网络', windowSize: 4096, rtt: 200, packetLoss: 2, speed: 0.7 },
  { label: '高丢包网络', windowSize: 4096, rtt: 100, packetLoss: 15, speed: 0.8 },
  { label: '受限带宽', windowSize: 1024, rtt: 150, packetLoss: 5, speed: 0.6 },
]

function applyPreset(p: typeof presets[0]) {
  simParams.value = { windowSize: p.windowSize, rtt: p.rtt, packetLoss: p.packetLoss }
  activePreset.value = p.label
  store.speed = p.speed
}

function resetParams() {
  applyPreset(presets[0])
}

function setNetworkQuality(q: string) {
  networkQuality.value = q
  if (q === '低延迟') { simParams.value.rtt = 50; simParams.value.packetLoss = 0; store.speed = 1 }
  else if (q === '中延迟') { simParams.value.rtt = 100; simParams.value.packetLoss = 2; store.speed = 0.7 }
  else { simParams.value.rtt = 200; simParams.value.packetLoss = 10; store.speed = 0.5 }
  activePreset.value = ''
}

function toggleFullscreen() {
  const el = playerRootRef.value
  if (!el) return
  if (!document.fullscreenElement) {
    el.requestFullscreen?.().then(() => { isFullscreen.value = true }).catch(() => {})
  } else {
    document.exitFullscreen?.().then(() => { isFullscreen.value = false }).catch(() => {})
  }
}

function openDetail(index: number) {
  const steps = packetSteps.value
  if (index >= 0 && index < steps.length) {
    detailStepIndex.value = index
    detailStep.value = steps[index]
    detailVisible.value = true
  }
}

const initialStates = computed(() => {
  const s = store.scenario
  if (s === 'three_way_handshake') return { client: 'CLOSED', server: 'LISTEN' }
  if (s === 'four_way_wavehand') return { client: 'ESTABLISHED', server: 'ESTABLISHED' }
  if (s === 'http_request') return { client: 'CLOSED', server: 'LISTEN' }
  return { client: 'ESTABLISHED', server: 'ESTABLISHED' }
})

const clientState = computed(() => {
  const steps = packetSteps.value
  const idx = Math.min(store.currentStep, steps.length)
  return idx > 0 ? steps[idx - 1].clientState : initialStates.value.client
})
const serverState = computed(() => {
  const steps = packetSteps.value
  const idx = Math.min(store.currentStep, steps.length)
  return idx > 0 ? steps[idx - 1].serverState : initialStates.value.server
})
const currentPacket = computed(() => {
  const steps = packetSteps.value
  const idx = store.currentStep
  if (isInTransition.value && idx < steps.length) return steps[idx]
  if (idx > 0 && idx <= steps.length) return steps[idx - 1]
  return null
})
const isCompleted = computed(() => store.currentStep >= packetSteps.value.length)
const connectionStatus = computed(() => {
  if (clientState.value === 'ESTABLISHED') return { text: '连接建立中', color: '#2563EB' }
  if (store.currentStep === 0) return { text: '待连接', color: '#f59e0b' }
  if (clientState.value === 'CLOSED' && store.currentStep > 1) return { text: '连接关闭', color: '#ef4444' }
  return { text: '握手中...', color: '#f59e0b' }
})

// ─── Canvas drawing ─────────────────────────────────────────────────────────

function getNodeX(W: number, host: 'client' | 'server') {
  return host === 'client' ? W * 0.25 : W * 0.75
}

function drawFusionNode(
  ctx: CanvasRenderingContext2D, cx: number, cy: number,
  name: string, state: string, ip: string,
  primaryColor: string, glowColor: string
) {
  const WN = 130, HN = 72, rx = cx - WN / 2, ry = cy - HN / 2

  const rad = ctx.createRadialGradient(cx, cy, 10, cx, cy, 80)
  rad.addColorStop(0, glowColor + '22'); rad.addColorStop(1, 'transparent')
  ctx.fillStyle = rad
  ctx.beginPath(); ctx.arc(cx, cy, 80, 0, Math.PI * 2); ctx.fill()

  ctx.shadowColor = glowColor + '88'; ctx.shadowBlur = 16; ctx.shadowOffsetY = 4
  const bg = ctx.createLinearGradient(rx, ry, rx, ry + HN)
  bg.addColorStop(0, '#ffffff'); bg.addColorStop(1, '#f0f7ff')
  ctx.fillStyle = bg; ctx.beginPath(); ;(ctx as any).roundRect(rx, ry, WN, HN, 10); ctx.fill()
  ctx.shadowBlur = 0; ctx.shadowOffsetY = 0

  ctx.strokeStyle = primaryColor; ctx.lineWidth = 2
  ctx.shadowColor = glowColor; ctx.shadowBlur = 10
  ctx.beginPath(); ;(ctx as any).roundRect(rx, ry, WN, HN, 10); ctx.stroke()
  ctx.shadowBlur = 0

  ctx.fillStyle = '#1e293b'; ctx.font = 'bold 13px sans-serif'; ctx.textAlign = 'center'
  ctx.fillText(name, cx, ry + 20)
  ctx.fillStyle = '#94a3b8'; ctx.font = '9px monospace'; ctx.fillText(ip, cx, ry + 33)

  const bW = Math.min(state.length * 6.5 + 14, 112)
  const bX = cx - bW / 2, bY = ry + 40
  ctx.fillStyle = primaryColor + '18'; ctx.beginPath(); ;(ctx as any).roundRect(bX, bY, bW, 18, 4); ctx.fill()
  ctx.fillStyle = primaryColor; ctx.shadowColor = glowColor; ctx.shadowBlur = 6
  ctx.font = 'bold 9px "Courier New", monospace'; ctx.textAlign = 'center'
  ctx.fillText(state, cx, bY + 12); ctx.shadowBlur = 0
}

function drawScene() {
  const canvas = canvasRef.value; if (!canvas) return
  const ctx = canvas.getContext('2d'); if (!ctx) return
  const dpr = window.devicePixelRatio
  const W = canvas.width / dpr, H = canvas.height / dpr
  ctx.clearRect(0, 0, canvas.width, canvas.height)
  ctx.fillStyle = '#f0f4ff'; ctx.fillRect(0, 0, canvas.width, canvas.height)

  ctx.strokeStyle = 'rgba(37,99,235,0.05)'; ctx.lineWidth = 0.5
  for (let i = 0; i < W; i += 40) { ctx.beginPath(); ctx.moveTo(i, 0); ctx.lineTo(i, H); ctx.stroke() }
  for (let i = 0; i < H; i += 40) { ctx.beginPath(); ctx.moveTo(0, i); ctx.lineTo(W, i); ctx.stroke() }

  const steps = packetSteps.value, current = store.currentStep
  const CLIENT_X = getNodeX(W, 'client'), SERVER_X = getNodeX(W, 'server'), NODE_Y = 48
  let curClient = initialStates.value.client, curServer = initialStates.value.server
  for (let i = 0; i < Math.min(current, steps.length); i++) { curClient = steps[i].clientState; curServer = steps[i].serverState }

  drawFusionNode(ctx, CLIENT_X, NODE_Y + 36, 'Client', curClient, '192.168.1.100:54832', '#2563EB', '#60a5fa')
  drawFusionNode(ctx, SERVER_X, NODE_Y + 36, 'Server', curServer, '192.168.1.1:80', '#10b981', '#6ee7b7')

  const NODE_BOTTOM = NODE_Y + 72 + 16
  const FIRST_STEP_Y = NODE_BOTTOM + 20
  const STEP_SPACING = Math.min(72, (H - FIRST_STEP_Y - 50) / Math.max(steps.length, 1))
  const timelineEnd = FIRST_STEP_Y + steps.length * STEP_SPACING + 20

  ctx.shadowColor = '#2563EB55'; ctx.shadowBlur = 6
  ctx.strokeStyle = '#2563EB66'; ctx.lineWidth = 1.5; ctx.setLineDash([5, 5])
  ctx.beginPath(); ctx.moveTo(CLIENT_X, NODE_BOTTOM); ctx.lineTo(CLIENT_X, timelineEnd); ctx.stroke()
  ctx.shadowColor = '#10b98155'; ctx.strokeStyle = '#10b98166'
  ctx.beginPath(); ctx.moveTo(SERVER_X, NODE_BOTTOM); ctx.lineTo(SERVER_X, timelineEnd); ctx.stroke()
  ctx.setLineDash([]); ctx.shadowBlur = 0

  const TAX = 20
  ctx.strokeStyle = '#cbd5e1'; ctx.lineWidth = 1
  ctx.beginPath(); ctx.moveTo(TAX, FIRST_STEP_Y); ctx.lineTo(TAX, timelineEnd); ctx.stroke()
  ctx.fillStyle = '#cbd5e1'
  ctx.beginPath(); ctx.moveTo(TAX, timelineEnd); ctx.lineTo(TAX - 4, timelineEnd - 8); ctx.lineTo(TAX + 4, timelineEnd - 8); ctx.fill()
  ctx.fillStyle = '#94a3b8'; ctx.font = '10px sans-serif'
  ctx.save(); ctx.translate(TAX - 11, (FIRST_STEP_Y + timelineEnd) / 2); ctx.rotate(-Math.PI / 2)
  ctx.textAlign = 'center'; ctx.fillText('时间轴', 0, 0); ctx.restore()

  for (let i = 0; i < Math.min(current, steps.length); i++) {
    const step = steps[i]
    const fromX = getNodeX(W, step.from), toX = getNodeX(W, step.to)
    const startY = FIRST_STEP_Y + i * STEP_SPACING + STEP_SPACING * 0.15
    const endY = FIRST_STEP_Y + i * STEP_SPACING + STEP_SPACING * 0.65
    const midX = (fromX + toX) / 2, midY = (startY + endY) / 2
    const c = step.from === 'client' ? '#2563EB' : '#10b981'
    const g = step.from === 'client' ? '#60a5fa' : '#6ee7b7'

    ctx.shadowColor = g; ctx.shadowBlur = 8
    ctx.strokeStyle = c; ctx.lineWidth = 2
    ctx.beginPath(); ctx.moveTo(fromX, startY); ctx.lineTo(toX, endY); ctx.stroke()
    ctx.shadowBlur = 0

    const angle = Math.atan2(endY - startY, toX - fromX)
    ctx.fillStyle = c; ctx.shadowColor = g; ctx.shadowBlur = 6
    ctx.beginPath(); ctx.moveTo(toX, endY)
    ctx.lineTo(toX - 10 * Math.cos(angle - 0.4), endY - 10 * Math.sin(angle - 0.4))
    ctx.lineTo(toX - 10 * Math.cos(angle + 0.4), endY - 10 * Math.sin(angle + 0.4))
    ctx.fill(); ctx.shadowBlur = 0

    ctx.fillStyle = c; ctx.shadowColor = g; ctx.shadowBlur = 14
    ctx.beginPath(); ctx.arc(midX, midY, 13, 0, Math.PI * 2); ctx.fill(); ctx.shadowBlur = 0
    ctx.fillStyle = '#fff'; ctx.font = 'bold 10px sans-serif'; ctx.textAlign = 'center'
    ctx.fillText(String(i + 1), midX, midY + 4)

    ctx.fillStyle = '#1e293b'; ctx.font = 'bold 11px sans-serif'; ctx.textAlign = 'center'
    ctx.fillText(step.flags.join(' + '), midX, startY - 7)
    if (step.seq > 0) {
      ctx.fillStyle = '#64748b'; ctx.font = '9px "Courier New", monospace'
      const seqTxt = step.ack > 0 ? `Seq = ${step.seq}, Ack = ${step.ack}` : `Seq = ${step.seq}`
      ctx.fillText(seqTxt, midX, endY + 14)
    }
  }

  if (isInTransition.value && current < steps.length) {
    const step = steps[current]
    const fromX = getNodeX(W, step.from), toX = getNodeX(W, step.to)
    const startY = FIRST_STEP_Y + current * STEP_SPACING + STEP_SPACING * 0.15
    const endY = FIRST_STEP_Y + current * STEP_SPACING + STEP_SPACING * 0.65
    const prog = stepProgress.value
    const curX = fromX + (toX - fromX) * prog, curY = startY + (endY - startY) * prog
    const c = step.from === 'client' ? '#2563EB' : '#10b981'
    const g = step.from === 'client' ? '#93c5fd' : '#6ee7b7'

    ctx.shadowColor = g; ctx.shadowBlur = 8; ctx.strokeStyle = c; ctx.lineWidth = 2
    ctx.beginPath(); ctx.moveTo(fromX, startY); ctx.lineTo(curX, curY); ctx.stroke(); ctx.shadowBlur = 0

    const glowGrad = ctx.createRadialGradient(curX, curY, 0, curX, curY, 20)
    glowGrad.addColorStop(0, g + 'cc'); glowGrad.addColorStop(0.5, c + '66'); glowGrad.addColorStop(1, 'transparent')
    ctx.fillStyle = glowGrad; ctx.beginPath(); ctx.arc(curX, curY, 20, 0, Math.PI * 2); ctx.fill()
    ctx.fillStyle = c; ctx.shadowColor = g; ctx.shadowBlur = 20
    ctx.beginPath(); ctx.arc(curX, curY, 9, 0, Math.PI * 2); ctx.fill(); ctx.shadowBlur = 0
    ctx.fillStyle = '#fff'; ctx.font = 'bold 8px sans-serif'; ctx.textAlign = 'center'
    ctx.fillText(step.flags.length > 2 ? step.flags[0] + '..' : step.flags.join('+'), curX, curY + 3)
    ctx.fillStyle = c; ctx.font = 'bold 10px sans-serif'
    ctx.fillText(step.flags.join('+'), curX, curY - 16)
  }

  ctx.fillStyle = '#94a3b8'; ctx.font = '10px sans-serif'; ctx.textAlign = 'center'
  ctx.fillText('点击报文可查看详细信息', W / 2, H - 10)
}

function tick() {
  if (!store.isPlaying) { animId = requestAnimationFrame(tick); drawScene(); return }
  const steps = packetSteps.value
  if (store.currentStep >= steps.length) { store.pause(); animId = requestAnimationFrame(tick); drawScene(); return }
  if (!isInTransition.value) { isInTransition.value = true; stepProgress.value = 0 }
  stepProgress.value += 0.008 * store.speed
  if (stepProgress.value >= 1) {
    stepProgress.value = 0; isInTransition.value = false; store.currentStep++
    if (store.currentStep >= steps.length) store.pause()
  }
  drawScene(); animId = requestAnimationFrame(tick)
}

function handleCanvasClick(e: MouseEvent) {
  const canvas = canvasRef.value; if (!canvas) return
  const rect = canvas.getBoundingClientRect()
  const x = e.clientX - rect.left, y = e.clientY - rect.top
  const dpr = window.devicePixelRatio, W = canvas.width / dpr, H = canvas.height / dpr
  const steps = packetSteps.value, current = store.currentStep
  const NODE_BOTTOM = 48 + 72 + 16, FIRST_STEP_Y = NODE_BOTTOM + 20
  const STEP_SPACING = Math.min(72, (H - FIRST_STEP_Y - 50) / Math.max(steps.length, 1))
  for (let i = 0; i < Math.min(current, steps.length); i++) {
    const step = steps[i], fromX = getNodeX(W, step.from), toX = getNodeX(W, step.to)
    const startY = FIRST_STEP_Y + i * STEP_SPACING + STEP_SPACING * 0.15
    const endY = FIRST_STEP_Y + i * STEP_SPACING + STEP_SPACING * 0.65
    const midX = (fromX + toX) / 2, midY = (startY + endY) / 2
    if (Math.sqrt((x - midX) ** 2 + (y - midY) ** 2) < 20) { openDetail(i); return }
  }
  if (isInTransition.value && current < steps.length) {
    const step = steps[current], fromX = getNodeX(W, step.from), toX = getNodeX(W, step.to)
    const startY = FIRST_STEP_Y + current * STEP_SPACING + STEP_SPACING * 0.15
    const endY = FIRST_STEP_Y + current * STEP_SPACING + STEP_SPACING * 0.65
    const curX = fromX + (toX - fromX) * stepProgress.value
    const curY = startY + (endY - startY) * stepProgress.value
    if (Math.sqrt((x - curX) ** 2 + (y - curY) ** 2) < 20) { openDetail(current); return }
  }
}

onMounted(() => {
  const canvas = canvasRef.value
  if (canvas) {
    const resize = () => {
      const rect = canvas.parentElement!.getBoundingClientRect()
      const dpr = window.devicePixelRatio
      canvas.width = rect.width * dpr; canvas.height = rect.height * dpr
      canvas.style.width = rect.width + 'px'; canvas.style.height = rect.height + 'px'
      const ctx = canvas.getContext('2d'); if (ctx) ctx.scale(dpr, dpr)
    }
    resize(); window.addEventListener('resize', resize)
    canvas.addEventListener('click', handleCanvasClick)
    animId = requestAnimationFrame(tick)
    onUnmounted(() => { window.removeEventListener('resize', resize); canvas.removeEventListener('click', handleCanvasClick); cancelAnimationFrame(animId) })
  }
})
onUnmounted(() => cancelAnimationFrame(animId))

function handlePrevStep() { if (store.currentStep > 0) { store.currentStep--; stepProgress.value = 0; isInTransition.value = false } }
function handleStep() { if (store.currentStep < packetSteps.value.length) { store.currentStep++; stepProgress.value = 0; isInTransition.value = false } }
function handleReset() { store.reset(); stepProgress.value = 0; isInTransition.value = false }
function handlePlay() { if (store.currentStep >= packetSteps.value.length) store.reset(); store.play() }
function changeScenario(val: string) { store.setScenario(val); stepProgress.value = 0; isInTransition.value = false; dropdownOpen.value = false }
function handleProgressChange(val: number) { store.currentStep = val; stepProgress.value = 0; isInTransition.value = false }

const stepClass = (i: number) => {
  if (i < store.currentStep) return 'done'
  if (i === store.currentStep && isInTransition.value) return 'active'
  return 'pending'
}
const flagColors: Record<string, string> = { SYN: '#f59e0b', ACK: '#10b981', FIN: '#ef4444', PSH: '#7c3aed', RST: '#dc2626' }
const flagColor = (f: string) => flagColors[f] || '#64748b'
const clientBadgeColor = computed(() => {
  const s = clientState.value
  if (s === 'ESTABLISHED') return '#2563EB'
  if (s === 'CLOSED' || s === 'TIME_WAIT') return '#64748b'
  return '#2563EB'
})
const serverBadgeColor = computed(() => {
  const s = serverState.value
  if (s === 'LISTEN' || s === 'ESTABLISHED') return '#22c55e'
  if (s === 'CLOSED') return '#64748b'
  return '#10b981'
})
</script>

<template>
  <div ref="playerRootRef" class="s3-root" :class="{ 's3-fullscreen': isFullscreen }">
    <!-- ── Hero Row ── -->
    <div class="s3-hero-row">
      <div class="s3-hero">
        <div class="s3-hero-glow"></div>
        <div class="s3-hero-left">
          <div class="s3-hero-icon">🔬</div>
          <div>
            <div class="s3-hero-title">协议仿真智能实验室</div>
            <div class="s3-hero-sub">可视化探索 TCP/IP 协议运行机制 · AI 驱动分析</div>
          </div>
        </div>
        <div class="s3-hero-badges">
          <div class="s3-badge blue"><span class="sb-dot blue-dot"></span><span>{{ currentScenario.label }}</span></div>
          <div class="s3-badge purple"><span class="sb-dot purple-dot"></span><span>实时模拟</span></div>
          <div class="s3-badge green"><span class="sb-dot green-dot"></span><span>{{ store.speed }}x 正常</span></div>
        </div>
      </div>

      <!-- Stats Card -->
      <div class="s3-stats-card">
        <div class="ssc-title">实时统计</div>
        <div class="ssc-row">
          <div class="ssc-item">
            <div class="ssc-label">往返时延</div>
            <div class="ssc-val">{{ simParams.rtt }}<small>ms</small></div>
          </div>
          <div class="ssc-item">
            <div class="ssc-label">丢包率</div>
            <div class="ssc-val">{{ simParams.packetLoss }}<small>%</small></div>
          </div>
        </div>
        <div class="ssc-status-row">
          <div class="ssc-label">当前状态</div>
          <div class="ssc-status" :style="{ color: connectionStatus.color }">{{ connectionStatus.text }}</div>
        </div>
        <div class="ssc-nq-title">网络质量调节</div>
        <div class="ssc-nq-btns">
          <button :class="{ active: networkQuality === '低延迟' }" @click="setNetworkQuality('低延迟')">低延迟</button>
          <button :class="{ active: networkQuality === '中延迟' }" @click="setNetworkQuality('中延迟')">中延迟</button>
          <button :class="{ active: networkQuality === '高延迟' }" @click="setNetworkQuality('高延迟')">高延迟</button>
        </div>
        <div class="ssc-slider-row">
          <span class="ssc-label">速率 (Packet Loss)</span>
          <span class="ssc-pct">{{ simParams.packetLoss }}%</span>
        </div>
        <input type="range" min="0" max="30" v-model="simParams.packetLoss" class="s3-range" />
        <button class="s3-rerun" @click="handleReset">↺ 重新仿真（应用参数）</button>
      </div>
    </div>

    <!-- ── Toolbar ── -->
    <div class="s3-toolbar">
      <!-- Custom Dropdown -->
      <div class="s3-dropdown" :class="{ open: dropdownOpen }">
        <div class="s3-dropdown-trigger" @click="dropdownOpen = !dropdownOpen">
          <span>{{ currentScenario.label }}</span>
          <span class="dd-arrow">{{ dropdownOpen ? '∧' : '∨' }}</span>
        </div>
        <div v-if="dropdownOpen" class="s3-dropdown-menu">
          <div
            v-for="s in scenarios" :key="s.value"
            class="s3-dropdown-item"
            :class="{ active: s.value === store.scenario }"
            @click="changeScenario(s.value)"
          >
            <span class="ddi-label">{{ s.label }}</span>
            <span class="ddi-desc">{{ s.desc }}</span>
          </div>
        </div>
      </div>

      <button class="s3-btn primary" @click="store.isPlaying ? store.pause() : handlePlay()">
        <span>{{ store.isPlaying ? '⏸' : '▶' }}</span>
        {{ store.isPlaying ? '暂停' : '播放' }}
      </button>
      <button class="s3-btn" @click="handlePrevStep" :disabled="store.currentStep <= 0">« 上一步</button>
      <button class="s3-btn" @click="handleStep" :disabled="store.currentStep >= packetSteps.length">» 步进</button>
      <button class="s3-btn" @click="handleReset">↺ 重置</button>
      <button class="s3-btn" @click="toggleFullscreen">
        <span>{{ isFullscreen ? '⊡' : '⛶' }}</span> {{ isFullscreen ? '退出全屏' : '全屏' }}
      </button>
      <div class="tb3-spacer"></div>
      <span class="tb3-label">步骤 {{ store.currentStep }}/{{ packetSteps.length }}</span>
      <input type="range" min="0" :max="packetSteps.length" :value="store.currentStep" step="1" class="s3-range" style="width:100px"
        @input="(e) => handleProgressChange(Number((e.target as HTMLInputElement).value))" />
      <span class="tb3-sep">|</span>
      <input type="range" min="0.5" max="3" step="0.5" v-model="store.speed" class="s3-range" style="width:70px" />
      <span class="tb3-speed">{{ store.speed }}x</span>
    </div>

    <!-- ── Main Body ── -->
    <div class="s3-body">
      <!-- Canvas -->
      <div class="s3-canvas-area">
        <div class="s3-canvas-header">
          <span class="s3-canvas-bar"></span>
          <span>{{ currentScenario.label }} — {{ currentScenario.desc }}</span>
        </div>
        <div class="s3-canvas-wrap">
          <canvas ref="canvasRef" class="s3-canvas" @click="handleCanvasClick" />
        </div>
      </div>

      <!-- Right Panel -->
      <div class="s3-right">
        <!-- Simulation Params -->
        <div class="sim-params-card">
          <div class="spc-header">
            <span class="spc-title">⚙ 仿真参数调节</span>
            <button class="spc-reset" @click="resetParams">重置默认</button>
          </div>
          <div class="spc-presets">
            <span class="spc-preset-label">快捷预设：</span>
            <div class="spc-preset-btns">
              <button v-for="p in presets" :key="p.label"
                class="spc-preset-btn"
                :class="{ active: activePreset === p.label }"
                @click="applyPreset(p)">{{ p.label }}</button>
            </div>
          </div>

          <div class="spc-param-item">
            <div class="spc-param-row">
              <span class="spc-param-name">窗口大小 (Window Size)</span>
              <span class="spc-param-val">{{ simParams.windowSize }} bytes</span>
            </div>
            <input type="range" min="1024" max="65535" step="512" v-model="simParams.windowSize" class="s3-range spc-range" />
            <div class="spc-hint">控制发送端一次可发送的最大数据量，影响吞吐量与流量控制</div>
          </div>

          <div class="spc-param-item">
            <div class="spc-param-row">
              <span class="spc-param-name">往返延迟 (RTT)</span>
              <span class="spc-param-val">{{ simParams.rtt }} ms</span>
            </div>
            <input type="range" min="0" max="500" step="10" v-model="simParams.rtt" class="s3-range spc-range" />
            <div class="spc-hint">模拟网络传播延迟，RTT 越高窗口利用率越低</div>
          </div>

          <div class="spc-param-item">
            <div class="spc-param-row">
              <span class="spc-param-name">丢包率 (Packet Loss)</span>
              <span class="spc-param-val">{{ simParams.packetLoss }}%</span>
            </div>
            <input type="range" min="0" max="30" step="1" v-model="simParams.packetLoss" class="s3-range spc-range" />
            <div class="spc-hint">模拟网络丢包，触发重传与拥塞控制机制</div>
          </div>

          <button class="spc-rerun" @click="handleReset">↺ 重新仿真（应用参数）</button>
        </div>

        <!-- Steps Timeline -->
        <div class="s3-steps">
          <div class="s3-steps-title">📋 步骤详情</div>
          <div class="s3-steps-list">
            <div v-for="(step, i) in packetSteps" :key="i" class="s3-step" :class="stepClass(i)" @click="openDetail(i)">
              <div class="s3-step-num" :style="{ background: step.from === 'client' ? '#2563EB' : '#10b981' }">{{ i + 1 }}</div>
              <div class="s3-step-body">
                <div class="s3-step-head">
                  <span class="s3-step-flags" :style="{ color: step.from === 'client' ? '#2563EB' : '#10b981' }">{{ step.flags.join(' + ') }}</span>
                  <span class="s3-step-dir">{{ step.from === 'client' ? 'C→S' : 'S→C' }}</span>
                </div>
                <div class="s3-step-desc">{{ step.desc }}</div>
                <div v-if="stepClass(i) !== 'pending'" class="s3-step-fields">
                  <span v-for="f in step.flags" :key="f" class="s3-flag-chip" :style="{ color: flagColor(f), background: flagColor(f) + '18', borderColor: flagColor(f) + '40' }">{{ f }}</span>
                  <span class="s3-seq-chip">Seq:{{ step.seq }}</span>
                  <span v-if="step.ack > 0" class="s3-seq-chip">Ack:{{ step.ack }}</span>
                </div>
              </div>
            </div>
          </div>
          <div v-if="isCompleted && store.scenario === 'three_way_handshake'" class="s3-success">
            <span>✅</span>
            <div><div class="ss-title">连接建立成功！</div><div class="ss-desc">双方进入 ESTABLISHED 状态</div></div>
          </div>
        </div>
      </div>
    </div>

    <!-- ── Packet Inspector（步进同步展示） ── -->
    <div v-if="store.currentStep > 0" class="s3-inspector">
      <div class="si-header">
        <span class="si-icon">📦</span>
        <span>报文详情</span>
        <span class="si-count">{{ store.currentStep }} / {{ packetSteps.length }} 条</span>
      </div>
      <div class="si-table-wrap">
        <table class="si-table">
          <thead>
            <tr>
              <th>#</th>
              <th>报文类型</th>
              <th>方向</th>
              <th>序列号 (Seq)</th>
              <th>确认号 (Ack)</th>
              <th>标志位</th>
              <th>窗口大小</th>
              <th>状态</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(step, i) in packetSteps.slice(0, store.currentStep)"
              :key="i"
              class="si-row"
              :class="step.from === 'client' ? 'tr-client' : 'tr-server'"
              @click="openDetail(i)"
            >
              <td class="si-num">{{ i + 1 }}</td>
              <td class="si-type">{{ step.flags.join('+') }}</td>
              <td class="si-dir">
                <span class="dir-arrow" :class="step.from === 'client' ? 'right' : 'left'">
                  {{ step.from === 'client' ? '→' : '←' }}
                </span>
              </td>
              <td class="mono">{{ step.seq }}</td>
              <td class="mono">{{ step.ack > 0 ? step.ack : '-' }}</td>
              <td>
                <span
                  v-for="f in step.flags" :key="f"
                  class="si-flag"
                  :style="{ color: flagColor(f), background: flagColor(f) + '18' }"
                >{{ f }}</span>
              </td>
              <td class="mono">{{ simParams.windowSize }}</td>
              <td>
                <span class="si-status" :class="step.from === 'client' ? 'sent' : 'recv'">
                  {{ step.from === 'client' ? '已发送' : '已接收' }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ── Bottom Status Bar (图五风格) ── -->
    <div class="s3-status-bar">
      <div class="ssb-item">
        <div class="ssb-label">Client 状态</div>
        <div class="ssb-badge" :style="{ background: clientBadgeColor }">{{ clientState }}</div>
      </div>
      <div class="ssb-item">
        <div class="ssb-label">Server 状态</div>
        <div class="ssb-badge" :style="{ background: serverBadgeColor }">{{ serverState }}</div>
      </div>
      <div class="ssb-item">
        <div class="ssb-label">报文标志</div>
        <div class="ssb-flag-box">{{ currentPacket ? currentPacket.flags.join('+') : '-' }}</div>
      </div>
      <div class="ssb-item">
        <div class="ssb-label">SEQ / ACK</div>
        <div class="ssb-seq">{{ currentPacket ? `${currentPacket.seq} / ${currentPacket.ack > 0 ? currentPacket.ack : '-'}` : '-' }}</div>
      </div>
    </div>

    <!-- ── Packet Detail Dialog (图四风格) ── -->
    <div v-if="detailVisible" class="detail-overlay" @click.self="detailVisible = false">
      <div class="detail-modal">
        <div class="dm-head">
          <div class="dm-flag-badge" :style="{ background: detailStep ? flagColor(detailStep.flags[0]) : '#64748b' }">
            {{ detailStep?.flags.join('+') }}
          </div>
          <span class="dm-step-info">步骤 {{ detailStepIndex + 1 }} / {{ packetSteps.length }}</span>
          <button class="dm-close" @click="detailVisible = false">✕</button>
        </div>

        <div v-if="detailStep">
          <div class="dm-section-title">传输方向</div>
          <div class="dm-direction">
            <span class="dm-dir-badge client">{{ detailStep.from.toUpperCase() }}</span>
            <span class="dm-arrow">→</span>
            <span class="dm-dir-badge server">{{ detailStep.to.toUpperCase() }}</span>
          </div>

          <div class="dm-section-title">TCP 头部</div>
          <div class="dm-tcp-grid">
            <div class="dm-tcp-field">
              <div class="dmtf-label">Sequence Number</div>
              <div class="dmtf-val">{{ detailStep.seq }}</div>
            </div>
            <div class="dm-tcp-field">
              <div class="dmtf-label">Acknowledgment</div>
              <div class="dmtf-val">{{ detailStep.ack }}</div>
            </div>
            <div class="dm-tcp-field full-width">
              <div class="dmtf-label">Flags</div>
              <div class="dmtf-flags">
                <span v-for="f in detailStep.flags" :key="f" class="dmf-chip" :style="{ background: flagColor(f) + '22', color: flagColor(f), border: '1px solid ' + flagColor(f) + '66' }">{{ f }}</span>
              </div>
            </div>
            <div v-if="detailStep.dataLen !== undefined" class="dm-tcp-field">
              <div class="dmtf-label">Data Length</div>
              <div class="dmtf-val">{{ detailStep.dataLen }} bytes</div>
            </div>
          </div>

          <div class="dm-section-title">状态变迁</div>
          <div class="dm-state-row">
            <div class="dm-state-box">
              <div class="dm-state-role">Client</div>
              <div class="dm-state-badge blue">{{ detailStep.clientState }}</div>
            </div>
            <span class="dm-arrow">→</span>
            <div class="dm-state-box">
              <div class="dm-state-role">Server</div>
              <div class="dm-state-badge green">{{ detailStep.serverState }}</div>
            </div>
          </div>

          <div class="dm-section-title">说明</div>
          <div class="dm-desc">{{ detailStep.desc }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.s3-root {
  display: flex; flex-direction: column; gap: 14px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  position: relative;
}
.s3-fullscreen { position: fixed; inset: 0; z-index: 9999; background: #f0f4ff; overflow-y: auto; padding: 16px; }

/* ── Hero ── */
.s3-hero-row { display: flex; gap: 14px; align-items: stretch; }
.s3-hero {
  flex: 1; position: relative; overflow: hidden;
  background: linear-gradient(135deg, #eff6ff 0%, #eef2ff 40%, #f0fdf4 100%);
  border: 1px solid #c7d2fe; border-radius: 16px; padding: 20px 24px;
  display: flex; align-items: center; justify-content: space-between;
}
.s3-hero-glow { position: absolute; width: 200px; height: 200px; background: radial-gradient(circle, rgba(37,99,235,0.12) 0%, transparent 70%); top: -60px; right: 100px; pointer-events: none; }
.s3-hero-left { display: flex; align-items: center; gap: 14px; }
.s3-hero-icon { font-size: 28px; }
.s3-hero-title { font-size: 20px; font-weight: 700; color: #1e293b; }
.s3-hero-sub { font-size: 12px; color: #64748b; margin-top: 2px; }
.s3-hero-badges { display: flex; flex-direction: column; gap: 6px; }
.s3-badge { display: flex; align-items: center; gap: 6px; padding: 4px 12px; border-radius: 20px; font-size: 11px; font-weight: 600; border: 1px solid transparent; }
.s3-badge.blue { background: #eff6ff; border-color: #bfdbfe; color: #2563EB; }
.s3-badge.purple { background: #f5f3ff; border-color: #ddd6fe; color: #7c3aed; }
.s3-badge.green { background: #f0fdf4; border-color: #bbf7d0; color: #059669; }
.sb-dot { width: 6px; height: 6px; border-radius: 50%; }
.blue-dot { background: #2563EB; box-shadow: 0 0 4px #2563EB; }
.purple-dot { background: #7c3aed; }
.green-dot { background: #059669; animation: pulse 2s infinite; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.5} }

/* Stats Card */
.s3-stats-card {
  width: 260px; background: #fff; border: 1px solid #e2e8f0;
  border-radius: 16px; padding: 16px; display: flex; flex-direction: column; gap: 10px;
}
.ssc-title { font-size: 13px; font-weight: 600; color: #1e293b; }
.ssc-row { display: flex; gap: 16px; }
.ssc-item { flex: 1; }
.ssc-label { font-size: 10px; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.5px; }
.ssc-val { font-size: 22px; font-weight: 700; color: #1e293b; line-height: 1.2; }
.ssc-val small { font-size: 12px; font-weight: 400; color: #64748b; }
.ssc-status-row { display: flex; align-items: center; justify-content: space-between; }
.ssc-status { font-size: 14px; font-weight: 600; }
.ssc-nq-title { font-size: 11px; font-weight: 600; color: #475569; }
.ssc-nq-btns { display: flex; gap: 4px; }
.ssc-nq-btns button { flex: 1; font-size: 11px; padding: 4px 0; border: 1px solid #e2e8f0; border-radius: 6px; background: #f8fafc; color: #64748b; cursor: pointer; transition: all 0.2s; }
.ssc-nq-btns button.active, .ssc-nq-btns button:hover { background: #eff6ff; border-color: #93c5fd; color: #2563EB; }
.ssc-slider-row { display: flex; justify-content: space-between; }
.ssc-pct { font-size: 11px; font-weight: 600; color: #2563EB; }
.s3-rerun {
  width: 100%; padding: 9px; background: linear-gradient(135deg, #2563EB, #7c3aed);
  color: #fff; border: none; border-radius: 8px; font-size: 12px; font-weight: 600; cursor: pointer;
}
.s3-rerun:hover { opacity: 0.9; }
.s3-range { width: 100%; accent-color: #2563EB; height: 3px; cursor: pointer; }

/* ── Toolbar ── */
.s3-toolbar {
  display: flex; align-items: center; gap: 8px; padding: 10px 14px;
  background: #fff; border: 1px solid #e2e8f0; border-radius: 10px; flex-wrap: wrap; position: relative;
}
.s3-dropdown { position: relative; min-width: 180px; }
.s3-dropdown-trigger {
  display: flex; align-items: center; justify-content: space-between;
  padding: 7px 12px; border: 1px solid #e2e8f0; border-radius: 8px;
  font-size: 13px; color: #1e293b; background: #f8fafc; cursor: pointer; user-select: none;
  transition: all 0.2s;
}
.s3-dropdown-trigger:hover, .s3-dropdown.open .s3-dropdown-trigger { border-color: #93c5fd; background: #fff; }
.dd-arrow { color: #94a3b8; font-size: 10px; margin-left: 8px; }
.s3-dropdown-menu {
  position: absolute; top: calc(100% + 4px); left: 0; right: 0; z-index: 100;
  background: #fff; border: 1px solid #e2e8f0; border-radius: 10px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.12); overflow: hidden;
}
.s3-dropdown-item {
  display: flex; align-items: center; justify-content: space-between;
  padding: 9px 14px; cursor: pointer; transition: background 0.15s; gap: 8px;
}
.s3-dropdown-item:hover { background: #f8fafc; }
.s3-dropdown-item.active { background: #eff6ff; }
.s3-dropdown-item.active .ddi-label { color: #2563EB; font-weight: 700; }
.ddi-label { font-size: 13px; color: #1e293b; font-weight: 500; white-space: nowrap; }
.ddi-desc { font-size: 11px; color: #94a3b8; background: #f1f5f9; padding: 2px 6px; border-radius: 4px; white-space: nowrap; }
.s3-btn {
  padding: 7px 14px; border: 1px solid #e2e8f0; border-radius: 7px;
  font-size: 12px; font-weight: 500; cursor: pointer; background: #f8fafc; color: #475569; transition: all 0.2s;
  display: flex; align-items: center; gap: 4px;
}
.s3-btn:hover { background: #eff6ff; border-color: #93c5fd; color: #2563EB; }
.s3-btn.primary { background: linear-gradient(135deg, #2563EB, #4f46e5); color: #fff; border: none; box-shadow: 0 2px 8px rgba(37,99,235,0.25); }
.s3-btn.primary:hover { opacity: 0.9; }
.s3-btn:disabled { opacity: 0.35; cursor: not-allowed; }
.tb3-spacer { flex: 1; }
.tb3-label { font-size: 12px; color: #64748b; white-space: nowrap; }
.tb3-sep { color: #e2e8f0; }
.tb3-speed { font-size: 12px; font-weight: 600; color: #2563EB; min-width: 28px; }

/* ── Body ── */
.s3-body { display: grid; grid-template-columns: 1fr 300px; gap: 14px; }
.s3-canvas-area { display: flex; flex-direction: column; }
.s3-canvas-header {
  display: flex; align-items: center; gap: 8px; padding: 10px 14px;
  background: linear-gradient(90deg, #f0f4ff, #f8fafc);
  border: 1px solid #e2e8f0; border-radius: 10px 10px 0 0; border-bottom: none;
  font-size: 12px; font-weight: 600; color: #1e293b;
}
.s3-canvas-bar { width: 3px; height: 14px; background: linear-gradient(180deg, #2563EB, #7c3aed); border-radius: 2px; }
.s3-canvas-wrap {
  flex: 1; height: 440px; background: #f0f4ff;
  border: 1px solid #e2e8f0; border-radius: 0 0 10px 10px; overflow: hidden; cursor: pointer;
}
.s3-canvas { width: 100%; height: 100%; display: block; }

/* ── Right Panel ── */
.s3-right { display: flex; flex-direction: column; gap: 12px; max-height: 520px; overflow-y: auto; }

/* Simulation Params */
.sim-params-card { background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 14px; }
.spc-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; }
.spc-title { font-size: 13px; font-weight: 600; color: #1e293b; }
.spc-reset { background: none; border: none; font-size: 11px; color: #94a3b8; cursor: pointer; }
.spc-reset:hover { color: #2563EB; }
.spc-presets { display: flex; flex-direction: column; gap: 4px; margin-bottom: 10px; }
.spc-preset-label { font-size: 11px; color: #64748b; }
.spc-preset-btns { display: flex; flex-wrap: wrap; gap: 4px; }
.spc-preset-btn { font-size: 11px; padding: 3px 8px; border: 1px solid #e2e8f0; border-radius: 6px; background: #f8fafc; color: #64748b; cursor: pointer; transition: all 0.15s; }
.spc-preset-btn.active, .spc-preset-btn:hover { background: #eff6ff; border-color: #93c5fd; color: #2563EB; font-weight: 600; }
.spc-param-item { margin-bottom: 10px; }
.spc-param-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
.spc-param-name { font-size: 12px; color: #475569; }
.spc-param-val { font-size: 12px; font-weight: 700; color: #2563EB; }
.spc-range { width: 100%; }
.spc-hint { font-size: 10px; color: #94a3b8; line-height: 1.3; margin-top: 3px; }
.spc-rerun {
  width: 100%; padding: 9px; background: linear-gradient(135deg, #2563EB, #7c3aed);
  color: #fff; border: none; border-radius: 8px; font-size: 12px; font-weight: 600; cursor: pointer; margin-top: 4px;
}
.spc-rerun:hover { opacity: 0.9; }

/* Steps */
.s3-steps { background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 12px; }
.s3-steps-title { font-size: 13px; font-weight: 700; color: #1e293b; margin-bottom: 10px; }
.s3-steps-list { display: flex; flex-direction: column; gap: 7px; }
.s3-step { display: flex; gap: 8px; padding: 9px; border-radius: 8px; cursor: pointer; border: 1px solid transparent; transition: all 0.2s; }
.s3-step:hover { background: #f8fafc; border-color: #e2e8f0; }
.s3-step.done { border-left: 3px solid #10b981; background: #f0fdf4; }
.s3-step.active { border-left: 3px solid #2563EB; background: #eff6ff; box-shadow: 0 0 0 2px rgba(37,99,235,0.08); }
.s3-step.pending { opacity: 0.4; }
.s3-step-num { width: 20px; height: 20px; border-radius: 50%; color: #fff; font-size: 10px; font-weight: 700; display: flex; align-items: center; justify-content: center; flex-shrink: 0; margin-top: 1px; }
.s3-step-body { flex: 1; min-width: 0; }
.s3-step-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 3px; }
.s3-step-flags { font-size: 12px; font-weight: 700; }
.s3-step-dir { font-size: 10px; color: #94a3b8; }
.s3-step-desc { font-size: 11px; color: #64748b; line-height: 1.3; margin-bottom: 4px; }
.s3-step-fields { display: flex; flex-wrap: wrap; gap: 3px; }
.s3-flag-chip { font-size: 10px; padding: 1px 5px; border-radius: 3px; border: 1px solid; font-weight: 700; }
.s3-seq-chip { font-size: 9px; padding: 1px 5px; border-radius: 3px; background: #f1f5f9; color: #64748b; font-family: monospace; }
.s3-success { display: flex; align-items: flex-start; gap: 8px; background: #f0fdf4; border: 1px solid #86efac; border-radius: 8px; padding: 10px; margin-top: 8px; font-size: 14px; }
.ss-title { font-weight: 700; font-size: 12px; color: #16a34a; }
.ss-desc { font-size: 10px; color: #4ade80; }

/* ── Bottom Status Bar (图五) ── */
.s3-status-bar {
  display: grid; grid-template-columns: 1fr 1fr 1fr auto;
  gap: 16px; padding: 12px 16px;
  background: #fff; border: 1px solid #e2e8f0; border-radius: 10px; align-items: center;
}
.ssb-item { display: flex; flex-direction: column; gap: 6px; }
.ssb-label { font-size: 12px; color: #64748b; }
.ssb-badge {
  padding: 8px 16px; border-radius: 5px; color: #fff;
  font-size: 13px; font-weight: 700; text-align: center; letter-spacing: 0.5px;
}
.ssb-flag-box {
  padding: 8px 14px; border: 1px solid #e2e8f0; border-radius: 5px;
  font-size: 13px; font-weight: 600; color: #475569; text-align: center; background: #f8fafc;
  min-width: 80px;
}
.ssb-seq { font-size: 13px; font-weight: 600; color: #2563EB; font-family: monospace; white-space: nowrap; }

/* ── Detail Dialog (图四) ── */
.detail-overlay { position: fixed; inset: 0; background: rgba(15,23,42,0.4); z-index: 2000; display: flex; align-items: center; justify-content: center; }
.detail-modal { background: #fff; border-radius: 16px; padding: 24px; width: 520px; max-height: 85vh; overflow-y: auto; box-shadow: 0 24px 64px rgba(0,0,0,0.15); }
.dm-head { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; border-bottom: 1px solid #f1f5f9; padding-bottom: 14px; }
.dm-flag-badge { padding: 5px 14px; border-radius: 6px; color: #fff; font-size: 14px; font-weight: 700; }
.dm-step-info { font-size: 13px; color: #94a3b8; flex: 1; }
.dm-close { background: none; border: none; font-size: 16px; cursor: pointer; color: #94a3b8; margin-left: auto; }
.dm-close:hover { color: #475569; }
.dm-section-title { font-size: 12px; font-weight: 600; color: #475569; text-transform: uppercase; letter-spacing: 0.5px; margin: 14px 0 8px; }
.dm-direction { display: flex; align-items: center; gap: 12px; }
.dm-dir-badge { padding: 5px 16px; border-radius: 6px; font-size: 13px; font-weight: 700; }
.dm-dir-badge.client { background: #eff6ff; color: #2563EB; border: 1px solid #bfdbfe; }
.dm-dir-badge.server { background: #f0fdf4; color: #059669; border: 1px solid #bbf7d0; }
.dm-arrow { color: #94a3b8; font-size: 16px; }
.dm-tcp-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.dm-tcp-field { background: #f8fafc; border-radius: 8px; padding: 12px; border: 1px solid #f1f5f9; }
.dm-tcp-field.full-width { grid-column: span 2; }
.dmtf-label { font-size: 11px; color: #94a3b8; margin-bottom: 6px; }
.dmtf-val { font-size: 15px; color: #1e293b; font-weight: 500; font-family: 'Courier New', monospace; }
.dmtf-flags { display: flex; flex-wrap: wrap; gap: 6px; }
.dmf-chip { padding: 3px 10px; border-radius: 5px; font-size: 12px; font-weight: 700; }
.dm-state-row { display: flex; align-items: center; gap: 16px; background: #f8fafc; border-radius: 8px; padding: 12px 16px; }
.dm-state-box { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 6px; }
.dm-state-role { font-size: 12px; color: #64748b; }
.dm-state-badge { padding: 4px 14px; border-radius: 5px; font-size: 12px; font-weight: 700; }
.dm-state-badge.blue { background: #eff6ff; color: #2563EB; border: 1px solid #bfdbfe; }
.dm-state-badge.green { background: #f0fdf4; color: #059669; border: 1px solid #bbf7d0; }
.dm-desc { background: #f8fafc; border-radius: 8px; padding: 12px; font-size: 13px; color: #475569; line-height: 1.6; border: 1px solid #f1f5f9; }

/* ── Packet Inspector ── */
.s3-inspector { background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden; }
.si-header {
  display: flex; align-items: center; gap: 8px; padding: 10px 16px;
  font-size: 13px; font-weight: 700; color: #1e293b;
  background: linear-gradient(90deg, #f0f4ff, #f8fafc);
  border-bottom: 1px solid #f1f5f9;
}
.si-icon { font-size: 15px; }
.si-count { margin-left: auto; font-size: 11px; color: #94a3b8; font-weight: 400; }
.si-table-wrap { overflow-x: auto; }
.si-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.si-table th {
  padding: 7px 12px; text-align: left; font-size: 10px; font-weight: 600;
  color: #64748b; background: #f8fafc; border-bottom: 1px solid #e2e8f0;
  text-transform: uppercase; letter-spacing: 0.5px;
}
.si-table td { padding: 8px 12px; border-bottom: 1px solid #f8fafc; }
.si-row { cursor: pointer; transition: background 0.15s; }
.si-row:hover td { background: #f0f4ff !important; }
.tr-client td { background: rgba(37,99,235,0.025); }
.tr-server td { background: rgba(16,185,129,0.025); }
.si-num { font-weight: 700; color: #94a3b8; font-size: 11px; width: 28px; }
.si-type { font-weight: 700; font-family: monospace; color: #1e293b; }
.si-dir { width: 40px; text-align: center; }
.dir-arrow { font-size: 14px; font-weight: 700; }
.dir-arrow.right { color: #2563EB; }
.dir-arrow.left { color: #10b981; }
.mono { font-family: 'Courier New', monospace; color: #475569; }
.si-flag {
  display: inline-block; font-size: 10px; padding: 1px 5px; border-radius: 3px;
  margin-right: 3px; font-weight: 700;
}
.si-status { font-size: 11px; padding: 2px 8px; border-radius: 4px; font-weight: 600; }
.si-status.sent { background: #eff6ff; color: #2563EB; }
.si-status.recv { background: #f0fdf4; color: #059669; }
</style>
