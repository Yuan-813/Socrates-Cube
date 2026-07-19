<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useSimulatorStore } from '@/stores/simulatorStore'
import StateMachinePanel from '@/components/StateMachinePanel.vue'
import SimulationParams from '@/components/SimulationParams.vue'

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
    { from: 'client', to: 'server', flags: ['SYN'], seq: 100, ack: 0, clientState: 'SYN_SENT', serverState: 'LISTEN', desc: '客户端发送同步请求，初始序列号 ISN=100' },
    { from: 'server', to: 'client', flags: ['SYN','ACK'], seq: 200, ack: 101, clientState: 'SYN_SENT', serverState: 'SYN_RCVD', desc: '服务端确认并同步，分配初始序列号 ISN=200' },
    { from: 'client', to: 'server', flags: ['ACK'], seq: 101, ack: 201, clientState: 'ESTABLISHED', serverState: 'ESTABLISHED', desc: '客户端确认，双方进入 ESTABLISHED 状态，连接建立完成' },
  ],
  four_way_wavehand: [
    { from: 'client', to: 'server', flags: ['FIN','ACK'], seq: 500, ack: 400, clientState: 'FIN_WAIT_1', serverState: 'ESTABLISHED', desc: '客户端发起关闭请求，发送 FIN+ACK' },
    { from: 'server', to: 'client', flags: ['ACK'], seq: 400, ack: 501, clientState: 'FIN_WAIT_2', serverState: 'CLOSE_WAIT', desc: '服务端确认收到 FIN，进入 CLOSE_WAIT' },
    { from: 'server', to: 'client', flags: ['FIN','ACK'], seq: 401, ack: 501, clientState: 'TIME_WAIT', serverState: 'LAST_ACK', desc: '服务端发送 FIN，请求关闭连接' },
    { from: 'client', to: 'server', flags: ['ACK'], seq: 501, ack: 402, clientState: 'CLOSED', serverState: 'CLOSED', desc: '客户端最后确认，等待 2MSL 后关闭' },
  ],
  sliding_window: [
    { from: 'client', to: 'server', flags: ['ACK'], seq: 1000, ack: 1, clientState: 'ESTABLISHED', serverState: 'ESTABLISHED', desc: 'ACK 确认，窗口大小通告 win=4096', dataLen: 0 },
    { from: 'client', to: 'server', flags: ['PSH','ACK'], seq: 1000, ack: 1, clientState: 'ESTABLISHED', serverState: 'ESTABLISHED', desc: '客户端发送数据段 #1，长度 1024 字节', dataLen: 1024 },
    { from: 'client', to: 'server', flags: ['PSH','ACK'], seq: 2024, ack: 1, clientState: 'ESTABLISHED', serverState: 'ESTABLISHED', desc: '客户端发送数据段 #2，长度 1024 字节（无需等待确认）', dataLen: 1024 },
    { from: 'server', to: 'client', flags: ['ACK'], seq: 1, ack: 2024, clientState: 'ESTABLISHED', serverState: 'ESTABLISHED', desc: '服务端累积确认收到前两个段，窗口减小', dataLen: 0 },
    { from: 'client', to: 'server', flags: ['PSH','ACK'], seq: 3048, ack: 1, clientState: 'ESTABLISHED', serverState: 'ESTABLISHED', desc: '客户端发送数据段 #3，长度 1024 字节', dataLen: 1024 },
    { from: 'server', to: 'client', flags: ['ACK'], seq: 1, ack: 4072, clientState: 'ESTABLISHED', serverState: 'ESTABLISHED', desc: '服务端确认所有数据，通告窗口 win=2048', dataLen: 0 },
  ],
  http_request: [
    { from: 'client', to: 'server', flags: ['SYN'], seq: 100, ack: 0, clientState: 'SYN_SENT', serverState: 'LISTEN', desc: 'Step 1: 建立 TCP 连接 — 客户端发送 SYN' },
    { from: 'server', to: 'client', flags: ['SYN','ACK'], seq: 200, ack: 101, clientState: 'SYN_SENT', serverState: 'SYN_RCVD', desc: 'Step 2: 服务端回复 SYN+ACK' },
    { from: 'client', to: 'server', flags: ['ACK'], seq: 101, ack: 201, clientState: 'ESTABLISHED', serverState: 'ESTABLISHED', desc: 'Step 3: 客户端确认，TCP 连接建立' },
    { from: 'client', to: 'server', flags: ['PSH','ACK'], seq: 101, ack: 201, clientState: 'ESTABLISHED', serverState: 'ESTABLISHED', desc: 'Step 4: 客户端发送 HTTP GET 请求报文', dataLen: 128 },
    { from: 'server', to: 'client', flags: ['ACK'], seq: 201, ack: 229, clientState: 'ESTABLISHED', serverState: 'ESTABLISHED', desc: 'Step 5: 服务端确认收到请求', dataLen: 0 },
    { from: 'server', to: 'client', flags: ['PSH','ACK'], seq: 201, ack: 229, clientState: 'ESTABLISHED', serverState: 'ESTABLISHED', desc: 'Step 6: 服务端发送 HTTP 200 OK 响应（HTML 内容）', dataLen: 2048 },
    { from: 'client', to: 'server', flags: ['ACK'], seq: 229, ack: 2249, clientState: 'ESTABLISHED', serverState: 'ESTABLISHED', desc: 'Step 7: 客户端确认收到响应数据', dataLen: 0 },
    { from: 'client', to: 'server', flags: ['FIN','ACK'], seq: 229, ack: 2249, clientState: 'FIN_WAIT_1', serverState: 'CLOSE_WAIT', desc: 'Step 8: 客户端发送 FIN 关闭连接' },
    { from: 'server', to: 'client', flags: ['ACK'], seq: 2249, ack: 230, clientState: 'FIN_WAIT_2', serverState: 'LAST_ACK', desc: 'Step 9: 服务端确认 FIN' },
    { from: 'server', to: 'client', flags: ['FIN','ACK'], seq: 2249, ack: 230, clientState: 'TIME_WAIT', serverState: 'LAST_ACK', desc: 'Step 10: 服务端发送 FIN' },
    { from: 'client', to: 'server', flags: ['ACK'], seq: 230, ack: 2250, clientState: 'CLOSED', serverState: 'CLOSED', desc: 'Step 11: 客户端最后确认，连接关闭' },
  ],
  http_encapsulation: [
    { from: 'client', to: 'server', flags: ['APP'], seq: 0, ack: 0, clientState: '应用层', serverState: '应用层', desc: '应用层：生成 HTTP 请求报文（Method + URL + Headers + Body）' },
    { from: 'client', to: 'server', flags: ['TCP'], seq: 0, ack: 0, clientState: '传输层', serverState: '传输层', desc: '传输层：添加 TCP 头部（源端口:49152 → 目的端口:80）' },
    { from: 'client', to: 'server', flags: ['IP'], seq: 0, ack: 0, clientState: '网络层', serverState: '网络层', desc: '网络层：添加 IP 头部（源IP:192.168.1.100 → 目的IP:93.184.216.34）' },
    { from: 'client', to: 'server', flags: ['ETH'], seq: 0, ack: 0, clientState: '数据链路层', serverState: '数据链路层', desc: '数据链路层：添加以太网帧头（源MAC → 目的MAC）' },
    { from: 'client', to: 'server', flags: ['PHY'], seq: 0, ack: 0, clientState: '物理层', serverState: '物理层', desc: '物理层：转换为比特流在物理介质上传输' },
    { from: 'server', to: 'client', flags: ['DE-CAP'], seq: 0, ack: 0, clientState: '物理层→应用层', serverState: '接收完成', desc: '服务端逐层解封装：物理层→数据链路层→网络层→传输层→应用层' },
  ],
  dns_resolution: [
    { from: 'client', to: 'server', flags: ['QUERY'], seq: 1, ack: 0, clientState: '发起查询', serverState: '本地DNS', desc: '客户端向本地 DNS 发起递归查询：www.example.com → ?' },
    { from: 'server', to: 'client', flags: ['ITER'], seq: 2, ack: 1, clientState: '等待', serverState: '根服务器', desc: '本地 DNS 向根服务器迭代查询，获得 .com TLD 地址' },
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

// 动画状态
let animId = 0
const stepProgress = ref(0)
const isInTransition = ref(false)

// 弹窗状态
const detailVisible = ref(false)
const detailStep = ref<SimStep | null>(null)
const detailStepIndex = ref(0)

function openDetail(index: number) {
  const steps = packetSteps.value
  if (index >= 0 && index < steps.length) {
    detailStepIndex.value = index
    detailStep.value = steps[index]
    detailVisible.value = true
  }
}

function getHostX(canvasW: number, host: 'client' | 'server') {
  return host === 'client' ? 120 : canvasW - 120
}

function drawHost(ctx: CanvasRenderingContext2D, x: number, y: number, name: string, state: string, color: string) {
  const w = 120, h = 110
  const rx = x - w / 2, ry = y - h / 2

  // 主机框背景
  const grad = ctx.createLinearGradient(rx, ry, rx, ry + h)
  grad.addColorStop(0, '#1e293b')
  grad.addColorStop(1, '#0f172a')
  ctx.fillStyle = grad
  ctx.beginPath()
  ctx.roundRect(rx, ry, w, h, 10)
  ctx.fill()

  // 边框
  ctx.strokeStyle = color
  ctx.lineWidth = 2
  ctx.beginPath()
  ctx.roundRect(rx, ry, w, h, 10)
  ctx.stroke()

  // 顶部小灯
  ctx.fillStyle = color
  ctx.beginPath()
  ctx.arc(x, ry + 8, 4, 0, Math.PI * 2)
  ctx.fill()
  // 发光效果
  ctx.shadowColor = color
  ctx.shadowBlur = 10
  ctx.beginPath()
  ctx.arc(x, ry + 8, 4, 0, Math.PI * 2)
  ctx.fill()
  ctx.shadowBlur = 0

  // 名称
  ctx.fillStyle = '#e2e8f0'
  ctx.font = 'bold 13px sans-serif'
  ctx.textAlign = 'center'
  ctx.fillText(name, x, y - 14)

  // 分隔线
  ctx.strokeStyle = 'rgba(148,163,184,0.2)'
  ctx.lineWidth = 1
  ctx.beginPath()
  ctx.moveTo(rx + 16, y - 2)
  ctx.lineTo(rx + w - 16, y - 2)
  ctx.stroke()

  // 状态
  ctx.fillStyle = color
  ctx.font = 'bold 11px "JetBrains Mono", monospace'
  ctx.fillText(state, x, y + 18)

  // 端口
  ctx.fillStyle = '#64748b'
  ctx.font = '10px sans-serif'
  ctx.fillText('port: 80', x, y + 36)
}

function drawPacket(ctx: CanvasRenderingContext2D, x: number, y: number, step: SimStep, progress: number) {
  const size = 32
  const rx = x - size / 2, ry = y - size / 2

  // 外发光
  if (progress > 0 && progress < 1) {
    ctx.shadowColor = 'rgba(245,158,11,0.6)'
    ctx.shadowBlur = 16
  }

  // 包体
  const gradient = ctx.createLinearGradient(rx, ry, rx + size, ry + size)
  gradient.addColorStop(0, '#f59e0b')
  gradient.addColorStop(1, '#ef4444')
  ctx.fillStyle = gradient
  ctx.beginPath()
  ctx.roundRect(rx, ry, size, size, 8)
  ctx.fill()
  ctx.shadowBlur = 0

  // 发光拖尾
  if (progress > 0 && progress < 1) {
    const tailLen = 50 * (1 - Math.abs(progress - 0.5) * 2)
    const tailDir = step.from === 'client' ? 1 : -1
    const gradient2 = ctx.createLinearGradient(x - tailLen * tailDir, y, x, y)
    gradient2.addColorStop(0, 'rgba(245,158,11,0)')
    gradient2.addColorStop(1, 'rgba(245,158,11,0.5)')
    ctx.fillStyle = gradient2
    ctx.fillRect(x - tailLen * tailDir, y - 2, tailLen * tailDir, 4)
  }

  // 文字
  ctx.fillStyle = '#fff'
  ctx.font = 'bold 9px sans-serif'
  ctx.textAlign = 'center'
  const label = step.flags.length > 2 ? step.flags.slice(0,2).join('|') + '..' : step.flags.join('|')
  ctx.fillText(label, x, y + 3)
}

function drawArrowLine(ctx: CanvasRenderingContext2D, x1: number, y1: number, x2: number, y2: number, color: string, dashed = false) {
  ctx.strokeStyle = color
  ctx.lineWidth = 2
  if (dashed) ctx.setLineDash([6, 4])
  ctx.beginPath()
  ctx.moveTo(x1, y1)
  ctx.lineTo(x2, y2)
  ctx.stroke()
  if (dashed) ctx.setLineDash([])

  // 箭头
  const angle = Math.atan2(y2 - y1, x2 - x1)
  ctx.beginPath()
  ctx.moveTo(x2, y2)
  ctx.lineTo(x2 - 10 * Math.cos(angle - 0.5), y2 - 10 * Math.sin(angle - 0.5))
  ctx.lineTo(x2 - 10 * Math.cos(angle + 0.5), y2 - 10 * Math.sin(angle + 0.5))
  ctx.fillStyle = color
  ctx.fill()
}

function drawScene() {
  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  if (!ctx) return

  const W = canvas.width / window.devicePixelRatio
  const H = canvas.height / window.devicePixelRatio
  const cy = H / 2 + 10

  ctx.clearRect(0, 0, canvas.width, canvas.height)
  ctx.fillStyle = '#0b1120'
  ctx.fillRect(0, 0, canvas.width, canvas.height)

  // 网格背景
  ctx.strokeStyle = 'rgba(30,41,59,0.5)'
  ctx.lineWidth = 0.5
  for (let i = 0; i < W; i += 40) {
    ctx.beginPath(); ctx.moveTo(i, 0); ctx.lineTo(i, H); ctx.stroke()
  }
  for (let i = 0; i < H; i += 40) {
    ctx.beginPath(); ctx.moveTo(0, i); ctx.lineTo(W, i); ctx.stroke()
  }

  // 场景标题
  const scenarioInfo = scenarios.find(s => s.value === store.scenario)
  if (scenarioInfo) {
    ctx.fillStyle = '#94a3b8'
    ctx.font = '11px sans-serif'
    ctx.textAlign = 'left'
    ctx.fillText(`${scenarioInfo.label} — ${scenarioInfo.desc}`, 20, 24)
  }

  const steps = packetSteps.value
  const current = store.currentStep
  const clientX = getHostX(W, 'client')
  const serverX = getHostX(W, 'server')

  // 获取两端当前状态
  let clientState = store.scenario === 'three_way_handshake' ? 'CLOSED' : 'ESTABLISHED'
  let serverState = store.scenario === 'three_way_handshake' ? 'LISTEN' : 'ESTABLISHED'
  for (let i = 0; i < Math.min(current, steps.length); i++) {
    clientState = steps[i].clientState
    serverState = steps[i].serverState
  }

  // 绘制主机
  drawHost(ctx, clientX, cy, 'Client', clientState, '#3b82f6')
  drawHost(ctx, serverX, cy, 'Server', serverState, '#10b981')

  // 中央连接线（虚线）
  ctx.strokeStyle = 'rgba(148,163,184,0.15)'
  ctx.lineWidth = 1
  ctx.setLineDash([8, 6])
  ctx.beginPath()
  ctx.moveTo(clientX + 60, cy)
  ctx.lineTo(serverX - 60, cy)
  ctx.stroke()
  ctx.setLineDash([])

  // 已完成的步骤用虚线标注
  const lineY = cy
  const maxArc = 70
  for (let i = 0; i < Math.min(current, steps.length); i++) {
    const step = steps[i]
    const fromX = getHostX(W, step.from)
    const toX = getHostX(W, step.to)
    const midX = (fromX + toX) / 2
    const arcOffset = Math.min(i * 18, maxArc)
    const midY = lineY - 40 - arcOffset

    ctx.strokeStyle = 'rgba(148,163,184,0.25)'
    ctx.lineWidth = 1
    ctx.setLineDash([4, 4])
    ctx.beginPath()
    ctx.moveTo(fromX, lineY)
    ctx.quadraticCurveTo(midX, midY, toX, lineY)
    ctx.stroke()
    ctx.setLineDash([])

    // 完成标记小圆点
    ctx.fillStyle = 'rgba(148,163,184,0.5)'
    ctx.beginPath()
    ctx.arc(midX, midY, 3, 0, Math.PI * 2)
    ctx.fill()

    // 步骤标签
    ctx.fillStyle = '#64748b'
    ctx.font = '10px sans-serif'
    ctx.textAlign = 'center'
    ctx.fillText(`#${i + 1} ${step.flags.join('+')}`, midX, midY - 8)
  }

  // 当前正在进行的步骤：绘制动画包
  if (isInTransition.value && current < steps.length) {
    const step = steps[current]
    const fromX = getHostX(W, step.from)
    const toX = getHostX(W, step.to)
    const packetX = fromX + (toX - fromX) * stepProgress.value
    const arcOffset = Math.min(current * 18, maxArc)
    const packetY = lineY - 30 - arcOffset * Math.sin(Math.PI * stepProgress.value)

    // 飞行线
    drawArrowLine(ctx, fromX, packetY, packetX, packetY, '#f59e0b')

    // 包
    drawPacket(ctx, packetX, packetY, step, stepProgress.value)

    // 提示文本
    if (stepProgress.value > 0.3 && stepProgress.value < 0.8) {
      ctx.fillStyle = 'rgba(245,158,11,0.8)'
      ctx.font = '10px sans-serif'
      ctx.textAlign = 'center'
      ctx.fillText(step.flags.join('+'), packetX, packetY - 22)
    }
  }

  // 底部图例
  ctx.fillStyle = '#475569'
  ctx.font = '10px sans-serif'
  ctx.textAlign = 'right'
  ctx.fillText('← 点击步骤可查看报文详情', W - 20, H - 14)
}

function tick() {
  if (!store.isPlaying) {
    animId = requestAnimationFrame(tick)
    drawScene()
    return
  }

  const steps = packetSteps.value
  if (store.currentStep >= steps.length) {
    store.pause()
    animId = requestAnimationFrame(tick)
    drawScene()
    return
  }

  if (!isInTransition.value) {
    isInTransition.value = true
    stepProgress.value = 0
  }

  // 速度控制：speed 越大，progress 增量越大
  const delta = 0.008 * store.speed
  stepProgress.value += delta

  if (stepProgress.value >= 1) {
    stepProgress.value = 0
    isInTransition.value = false
    store.currentStep++

    if (store.currentStep >= steps.length) {
      store.pause()
    }
  }

  drawScene()
  animId = requestAnimationFrame(tick)
}

function handleCanvasClick(e: MouseEvent) {
  const canvas = canvasRef.value
  if (!canvas) return
  const rect = canvas.getBoundingClientRect()
  const x = (e.clientX - rect.left) * (canvas.width / rect.width)
  const y = (e.clientY - rect.top) * (canvas.height / rect.height)
  const W = canvas.width
  const H = canvas.height
  const dpr = window.devicePixelRatio
  const cy = (H / dpr / 2 + 10) * dpr

  const steps = packetSteps.value
  const current = store.currentStep
  const maxArc = 70

  // 检测点击是否命中已完成步骤的标记
  for (let i = 0; i < Math.min(current, steps.length); i++) {
    const step = steps[i]
    const fromX = getHostX(W / dpr, step.from) * dpr
    const toX = getHostX(W / dpr, step.to) * dpr
    const midX = ((fromX + toX) / 2)
    const arcOffset = Math.min(i * 18, maxArc)
    const midY = (cy / dpr - 40 - arcOffset) * dpr

    const dx = x - midX
    const dy = y - midY
    if (Math.sqrt(dx * dx + dy * dy) < 24 * dpr) {
      openDetail(i)
      return
    }
  }

  // 检测是否命中当前动画中的包
  if (isInTransition.value && current < steps.length) {
    const step = steps[current]
    const fromX = getHostX(W / dpr, step.from) * dpr
    const toX = getHostX(W / dpr, step.to) * dpr
    const packetX = fromX + (toX - fromX) * stepProgress.value
    const arcOffset = Math.min(current * 18, maxArc)
    const packetY = (cy / dpr - 30 - arcOffset * Math.sin(Math.PI * stepProgress.value)) * dpr
    const dx = x - packetX
    const dy = y - packetY
    if (Math.sqrt(dx * dx + dy * dy) < 24 * dpr) {
      openDetail(current)
      return
    }
  }
}

onMounted(() => {
  const canvas = canvasRef.value
  if (canvas) {
    const resize = () => {
      const rect = canvas.parentElement!.getBoundingClientRect()
      const dpr = window.devicePixelRatio
      canvas.width = rect.width * dpr
      canvas.height = rect.height * dpr
      canvas.style.width = rect.width + 'px'
      canvas.style.height = rect.height + 'px'
      const ctx = canvas.getContext('2d')
      if (ctx) ctx.scale(dpr, dpr)
    }
    resize()
    window.addEventListener('resize', resize)
    canvas.addEventListener('click', handleCanvasClick)
    animId = requestAnimationFrame(tick)

    onUnmounted(() => {
      window.removeEventListener('resize', resize)
      canvas.removeEventListener('click', handleCanvasClick)
      cancelAnimationFrame(animId)
    })
  }
})

onUnmounted(() => {
  cancelAnimationFrame(animId)
})

const isFullscreen = ref(false)

function handlePrevStep() {
  if (store.currentStep > 0) {
    store.currentStep--
    stepProgress.value = 0
    isInTransition.value = false
  }
}

function handleProgressChange(val: number) {
  store.currentStep = val
  stepProgress.value = 0
  isInTransition.value = false
}

function toggleFullscreen() {
  const el = playerRootRef.value
  if (!el) {
    isFullscreen.value = !isFullscreen.value
    return
  }
  if (!document.fullscreenElement) {
    el.requestFullscreen?.().then(() => { isFullscreen.value = true }).catch(() => {
      isFullscreen.value = !isFullscreen.value
    })
  } else {
    document.exitFullscreen?.().then(() => { isFullscreen.value = false }).catch(() => {
      isFullscreen.value = false
    })
  }
}

function handlePlay() {
  if (store.currentStep >= packetSteps.value.length) {
    store.reset()
  }
  store.play()
}

function handlePause() {
  store.pause()
}

function handleRerunParams(params: { windowSize: number; rttDelay: number; packetLossRate: number }) {
  handleReset()
  store.speed = Math.max(0.5, Math.min(3, 100 / Math.max(params.rttDelay, 20)))
}

function handleReset() {
  store.reset()
  stepProgress.value = 0
  isInTransition.value = false
}

function handleStep() {
  if (store.currentStep < packetSteps.value.length) {
    store.currentStep++
    stepProgress.value = 0
    isInTransition.value = false
  }
}

function changeScenario(val: string) {
  store.setScenario(val)
  stepProgress.value = 0
  isInTransition.value = false
}

const currentPacket = computed(() => {
  const steps = packetSteps.value
  const idx = store.currentStep
  if (isInTransition.value && idx < steps.length) {
    return steps[idx]
  }
  if (idx > 0 && idx <= steps.length) {
    return steps[idx - 1]
  }
  return null
})

const clientState = computed(() => {
  const steps = packetSteps.value
  const idx = Math.min(store.currentStep, steps.length)
  return idx > 0 ? steps[idx - 1].clientState : (store.scenario === 'three_way_handshake' ? 'CLOSED' : 'ESTABLISHED')
})

const serverState = computed(() => {
  const steps = packetSteps.value
  const idx = Math.min(store.currentStep, steps.length)
  return idx > 0 ? steps[idx - 1].serverState : (store.scenario === 'three_way_handshake' ? 'LISTEN' : 'ESTABLISHED')
})
</script>

<template>
  <div ref="playerRootRef" class="simulator-player" :class="{ 'is-fullscreen': isFullscreen }">
    <!-- 工具栏 -->
    <div class="simulator-toolbar">
      <el-select
        :model-value="store.scenario"
        placeholder="选择仿真场景"
        style="width: 220px"
        @change="changeScenario"
      >
        <el-option
          v-for="s in scenarios"
          :key="s.value"
          :label="s.label"
          :value="s.value"
        >
          <div style="display: flex; align-items: center; gap: 8px">
            <span>{{ s.label }}</span>
            <el-tag size="small" type="info" style="margin-left: auto">{{ s.desc }}</el-tag>
          </div>
        </el-option>
      </el-select>

      <div class="controls">
        <el-button
          :type="store.isPlaying ? 'warning' : 'primary'"
          :icon="store.isPlaying ? 'VideoPause' : 'VideoPlay'"
          @click="store.isPlaying ? handlePause() : handlePlay()"
        >
          {{ store.isPlaying ? '暂停' : '播放' }}
        </el-button>
        <el-button icon="DArrowLeft" @click="handlePrevStep" :disabled="store.currentStep <= 0">上一步</el-button>
        <el-button icon="DArrowRight" @click="handleStep" :disabled="store.currentStep >= packetSteps.length">步进</el-button>
        <el-button icon="RefreshRight" @click="handleReset">重置</el-button>
        <el-button :icon="isFullscreen ? 'FullScreen' : 'FullScreen'" @click="toggleFullscreen" size="small">
          {{ isFullscreen ? '退出全屏' : '全屏' }}
        </el-button>
      </div>

      <div class="step-info">
        <span class="text-sm text-slate-500 font-mono">
          步骤 {{ store.currentStep }} / {{ packetSteps.length }}
        </span>
        <el-slider
          :model-value="store.currentStep"
          :min="0"
          :max="packetSteps.length"
          :step="1"
          style="width: 120px"
          @update:model-value="handleProgressChange"
          :show-tooltip="true"
          :format-tooltip="(val: number) => `步骤 ${val}`"
        />
        <el-divider direction="vertical" />
        <el-slider
          v-model="store.speed"
          :min="0.5"
          :max="3"
          :step="0.5"
          style="width: 80px"
          :show-tooltip="true"
          :format-tooltip="(val: number) => `${val}x 速度`"
        />
        <span class="text-xs text-slate-400">{{ store.speed }}x</span>
      </div>
    </div>

    <div class="simulator-body">
      <!-- Canvas 动画区 -->
      <div class="canvas-col">
        <div class="canvas-wrapper" @click="handleCanvasClick">
          <canvas ref="canvasRef" class="simulator-canvas" />
          <div class="canvas-hint">
            <el-icon><Pointer /></el-icon>
            点击报文或节点查看详情
          </div>
        </div>
      </div>

      <!-- 右侧面板 -->
      <div class="side-panel">
        <StateMachinePanel
          :client-state="clientState"
          :server-state="serverState"
          :scenario="store.scenario"
        />

        <SimulationParams @rerun="handleRerunParams" />

        <!-- 步骤时间线 -->
        <div class="steps-card">
          <h4 class="panel-title">
            <el-icon><List /></el-icon>
            步骤详情
          </h4>
          <div class="steps-list">
            <div
              v-for="(step, idx) in packetSteps"
              :key="idx"
              class="step-row"
              :class="{ done: idx < store.currentStep, current: idx === store.currentStep && isInTransition, pending: idx > store.currentStep }"
              @click="openDetail(idx)"
            >
              <div class="step-num">{{ (idx as number) + 1 }}</div>
              <div class="step-body">
                <div class="step-flags">
                  <el-tag size="small" :type="idx < store.currentStep ? 'success' : idx === store.currentStep ? 'warning' : 'info'">
                    {{ step.flags.join('+') }}
                  </el-tag>
                  <span class="step-direction">
                    <el-icon><ArrowRight v-if="step.from === 'client'" /><Back v-else /></el-icon>
                    {{ step.from === 'client' ? 'C→S' : 'S→C' }}
                  </span>
                </div>
                <div class="step-desc">{{ step.desc }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部状态栏 -->
    <div class="status-panel">
      <div class="status-item">
        <span class="status-label">Client 状态</span>
        <el-tag type="primary" effect="dark">{{ clientState }}</el-tag>
      </div>
      <div class="status-item">
        <span class="status-label">Server 状态</span>
        <el-tag type="success" effect="dark">{{ serverState }}</el-tag>
      </div>
      <div class="status-item">
        <span class="status-label">报文标志</span>
        <el-tag v-if="currentPacket" type="warning" effect="dark">
          {{ currentPacket.flags.join('+') }}
        </el-tag>
        <el-tag v-else type="info">-</el-tag>
      </div>
      <div class="status-item">
        <span class="status-label">SEQ / ACK</span>
        <span v-if="currentPacket" class="font-mono text-sm text-slate-600">
          seq={{ currentPacket.seq }} ack={{ currentPacket.ack }}
        </span>
        <span v-else class="text-sm text-slate-400">-</span>
      </div>
      <div class="status-item" v-if="currentPacket && currentPacket.dataLen !== undefined">
        <span class="status-label">数据长度</span>
        <span class="font-mono text-sm text-slate-600">{{ currentPacket.dataLen }} B</span>
      </div>
    </div>

    <!-- 报文详情弹窗 -->
    <el-dialog v-model="detailVisible" title="报文详情" width="500px" destroy-on-close>
      <div v-if="detailStep" class="packet-detail">
        <div class="detail-header">
          <el-tag size="large" type="warning" effect="dark">{{ detailStep.flags.join('+') }}</el-tag>
          <span class="detail-step-num">步骤 {{ (detailStepIndex as number) + 1 }} / {{ packetSteps.length }}</span>
        </div>

        <div class="detail-section">
          <h5 class="detail-label">传输方向</h5>
          <div class="detail-value direction-row">
            <el-tag :type="detailStep.from === 'client' ? 'primary' : 'success'">{{ detailStep.from.toUpperCase() }}</el-tag>
            <el-icon class="mx-2"><Right /></el-icon>
            <el-tag :type="detailStep.to === 'client' ? 'primary' : 'success'">{{ detailStep.to.toUpperCase() }}</el-tag>
          </div>
        </div>

        <div class="detail-section">
          <h5 class="detail-label">TCP 头部</h5>
          <div class="tcp-header-grid">
            <div class="tcp-field">
              <span class="field-label">Sequence Number</span>
              <span class="field-value font-mono">{{ detailStep.seq }}</span>
            </div>
            <div class="tcp-field">
              <span class="field-label">Acknowledgment</span>
              <span class="field-value font-mono">{{ detailStep.ack }}</span>
            </div>
            <div class="tcp-field">
              <span class="field-label">Flags</span>
              <span class="field-value">
                <el-tag v-for="f in detailStep.flags" :key="f" size="small" type="warning" class="mr-1">{{ f }}</el-tag>
              </span>
            </div>
            <div class="tcp-field" v-if="detailStep.dataLen !== undefined">
              <span class="field-label">Data Length</span>
              <span class="field-value font-mono">{{ detailStep.dataLen }} bytes</span>
            </div>
          </div>
        </div>

        <div class="detail-section">
          <h5 class="detail-label">状态变迁</h5>
          <div class="state-transition">
            <div class="state-box">
              <div class="state-title">Client</div>
              <el-tag size="small" type="primary">{{ detailStep.clientState }}</el-tag>
            </div>
            <el-icon class="transition-arrow"><Right /></el-icon>
            <div class="state-box">
              <div class="state-title">Server</div>
              <el-tag size="small" type="success">{{ detailStep.serverState }}</el-tag>
            </div>
          </div>
        </div>

        <div class="detail-section">
          <h5 class="detail-label">说明</h5>
          <p class="detail-desc">{{ detailStep.desc }}</p>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<style scoped>
.simulator-player {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.simulator-toolbar {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
  padding: 12px 16px;
  background-color: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.controls {
  display: flex;
  gap: 8px;
}

.step-info {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-left: auto;
}

/* 主体双栏布局 */
.simulator-body {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 16px;
}

.canvas-col {
  min-width: 0;
}

.canvas-wrapper {
  position: relative;
  width: 100%;
  height: 460px;
  background-color: #0b1120;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid #1e293b;
  cursor: pointer;
}

.canvas-wrapper:hover .canvas-hint {
  opacity: 1;
}

.canvas-hint {
  position: absolute;
  bottom: 12px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  background-color: rgba(15,23,42,0.8);
  border-radius: 20px;
  color: #94a3b8;
  font-size: 12px;
  opacity: 0;
  transition: opacity 0.3s;
  pointer-events: none;
  backdrop-filter: blur(4px);
}

.simulator-canvas {
  width: 100%;
  height: 100%;
  display: block;
}

/* 侧面板 */
.side-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-height: 460px;
  overflow-y: auto;
}

.panel-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 12px;
}

.state-machine-card,
.steps-card {
  background-color: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 14px;
}

/* 状态机节点 */
.state-diagram {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.state-node {
  padding: 6px 10px;
  border-radius: 6px;
  border: 1.5px solid #e2e8f0;
  background-color: #f8fafc;
  transition: all 0.2s;
  font-size: 12px;
}

.state-node.active {
  font-weight: 600;
  box-shadow: 0 2px 6px rgba(0,0,0,0.08);
}

.state-name {
  font-weight: 500;
}

.state-role {
  font-size: 10px;
  color: #94a3b8;
  margin-top: 2px;
}

/* 步骤列表 */
.steps-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.step-row {
  display: flex;
  gap: 10px;
  padding: 10px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s;
  border: 1px solid transparent;
}

.step-row:hover {
  background-color: #f1f5f9;
}

.step-row.done {
  opacity: 0.7;
}

.step-row.current {
  background-color: #fffbeb;
  border-color: #fcd34d;
}

.step-row.pending {
  opacity: 0.45;
}

.step-num {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background-color: #e2e8f0;
  color: #64748b;
  font-size: 11px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 2px;
}

.step-row.done .step-num {
  background-color: #d1fae5;
  color: #059669;
}

.step-row.current .step-num {
  background-color: #fde68a;
  color: #b45309;
}

.step-body {
  flex: 1;
  min-width: 0;
}

.step-flags {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.step-direction {
  display: flex;
  align-items: center;
  gap: 2px;
  font-size: 11px;
  color: #94a3b8;
}

.step-desc {
  font-size: 12px;
  color: #475569;
  line-height: 1.4;
  display: -webkit-box;
  line-clamp: 2;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* 底部状态栏 */
.status-panel {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
  padding: 12px 16px;
  background-color: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.status-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.status-label {
  font-size: 12px;
  color: #64748b;
}

/* 报文详情弹窗 */
.packet-detail {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.detail-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.detail-step-num {
  font-size: 13px;
  color: #94a3b8;
}

.detail-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.detail-label {
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin: 0;
}

.detail-value {
  font-size: 14px;
  color: #1e293b;
}

.direction-row {
  display: flex;
  align-items: center;
}

.tcp-header-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.tcp-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 10px;
  background-color: #f8fafc;
  border-radius: 6px;
}

.field-label {
  font-size: 11px;
  color: #94a3b8;
}

.field-value {
  font-size: 14px;
  color: #1e293b;
  font-weight: 500;
}

.state-transition {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px;
  background-color: #f8fafc;
  border-radius: 8px;
}

.state-box {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.state-title {
  font-size: 12px;
  color: #64748b;
}

.transition-arrow {
  color: #94a3b8;
}

.detail-desc {
  font-size: 13px;
  color: #475569;
  line-height: 1.6;
  margin: 0;
  padding: 12px;
  background-color: #f8fafc;
  border-radius: 6px;
}

.mx-2 {
  margin: 0 8px;
}

.mr-1 {
  margin-right: 4px;
}

/* 响应式 */
@media (max-width: 1024px) {
  .simulator-body {
    grid-template-columns: 1fr;
  }
  .side-panel {
    max-height: none;
    flex-direction: row;
    overflow-x: auto;
  }
  .state-machine-card,
  .steps-card {
    min-width: 280px;
    flex: 1;
  }
}

@media (max-width: 768px) {
  .status-panel {
    grid-template-columns: repeat(2, 1fr);
  }
  .step-info {
    margin-left: 0;
    width: 100%;
  }
  .canvas-wrapper {
    height: 360px;
  }
  .tcp-header-grid {
    grid-template-columns: 1fr;
  }
}
</style>
