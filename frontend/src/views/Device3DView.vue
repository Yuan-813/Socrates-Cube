<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import * as THREE from 'three'

// ── 设备数据定义 ──────────────────────────────────────────────────────
const DEVICES = [
  {
    id: 'router',
    name: '路由器（Router）',
    color: 0x3b82f6,
    shape: 'box',
    dims: [1.6, 0.3, 1.0],
    description: '工作于 OSI 第三层（网络层 Network Layer）。基于 IP 路由表（Routing Table）进行跪网段转发，支持 OSPF/BGP/RIP 等动态路由协议。NAT（网络地址转换）是家用路由器的核心功能，将内网私有 IP 映射到公网地址。',
    ports: ['WAN口 × 1（GE0/0/0）', 'LAN口 × 4（GE0/0/1–4）', '管理口 × 1（Console RS-232）', 'USB × 1'],
    rfc: 'RFC 791 (IPv4) / RFC 4271 (BGP)',
    osi_layer: 'L3 网络层',
    highlight: '#3b82f6',
    icon: '🌐',
  },
  {
    id: 'switch',
    name: '交换机（Switch）',
    color: 0x10b981,
    shape: 'box',
    dims: [2.0, 0.2, 1.2],
    description: '工作于 OSI 第二层（数据链路层 Data Link Layer）。基于 MAC 地址表 CAM 进行帧转发，支持 802.1Q VLAN 隔离、802.1D STP 成环防止、802.3ad LACP 链路聚合。',
    ports: ['24 × GE 电口（RJ45 1000BASE-T）', '4 × SFP+ 光口（10G）', '管理口 × 1（MGMT RJ45）', '堆叠口 × 2（Stack 40G）'],
    rfc: 'IEEE 802.1Q (VLAN) / IEEE 802.3 (Ethernet)',
    osi_layer: 'L2 数据链路层',
    highlight: '#10b981',
    icon: '🔀',
  },
  {
    id: 'firewall',
    name: '防火墙（Firewall）',
    color: 0xef4444,
    shape: 'box',
    dims: [1.8, 0.35, 1.1],
    description: '工作于 OSI L3–L7 多层。综合 ACL 访问控制列表、状态检测（SPI）、深度包检测（DPI）过滤流量，防止 DDoS、SQL注入、XSS 攻击，保护内网安全边界。',
    ports: ['WAN口 × 2（eth0/eth1 GE）', 'LAN口 × 4（eth2–5）', 'DMZ口 × 1（eth6）', 'HA 心跳口 × 1'],
    rfc: 'RFC 3511 (Firewall Benchmarking)',
    osi_layer: 'L3–L7 多层检测',
    highlight: '#ef4444',
    icon: '🛡️',
  },
  {
    id: 'ap',
    name: '无线 AP（Access Point）',
    color: 0x8b5cf6,
    shape: 'cylinder',
    dims: [0.6, 0.1, 32],
    description: '工作于 OSI L1–L2，将有线以太网转为 IEEE 802.11ax（Wi-Fi 6）无线信号。支持 OFDMA 多用户并发、MU-MIMO 8×8、TWT 省电模式，2.4GHz/5GHz/6GHz 三频高速接入。',
    ports: ['PoE+ 以太网口 × 1（802.3at）', '2.4GHz 天线 ×2（2x2 MIMO）', '5GHz 天线 ×4Ｈ4x4 MIMO）', '6GHz 天线 ×2（Wi-Fi 6E）'],
    rfc: 'IEEE 802.11ax (Wi-Fi 6) / 802.3at (PoE+)',
    osi_layer: 'L1–L2 物理+链路层',
    highlight: '#8b5cf6',
    icon: '📡',
  },
]

const selectedDevice = ref<typeof DEVICES[0] | null>(null)
const containerRef = ref<HTMLDivElement | null>(null)
const canvasRef = ref<HTMLCanvasElement | null>(null)

let renderer: THREE.WebGLRenderer | null = null
let scene: THREE.Scene | null = null
let camera: THREE.PerspectiveCamera | null = null
let meshes: Map<string, THREE.Mesh> = new Map()
let animFrameId = 0
let isDragging = false
let prevMouse = { x: 0, y: 0 }
let rotX = 0.3, rotY = 0.5

function initThree() {
  if (!canvasRef.value) return

  const w = canvasRef.value.clientWidth || 600
  const h = canvasRef.value.clientHeight || 400

  renderer = new THREE.WebGLRenderer({ canvas: canvasRef.value, antialias: true, alpha: true })
  renderer.setSize(w, h)
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  renderer.setClearColor(0xf8faff, 1)

  scene = new THREE.Scene()
  camera = new THREE.PerspectiveCamera(45, w / h, 0.1, 100)
  camera.position.set(0, 3, 6)
  camera.lookAt(0, 0, 0)

  // 光源
  const ambient = new THREE.AmbientLight(0xffffff, 0.6)
  const dirLight = new THREE.DirectionalLight(0xffffff, 0.9)
  dirLight.position.set(5, 8, 5)
  scene.add(ambient, dirLight)

  // 网格底板
  const gridHelper = new THREE.GridHelper(10, 20, 0xe2e8f0, 0xf1f5f9)
  scene.add(gridHelper)

  // 创建设备模型
  const positions = [
    new THREE.Vector3(-2.5, 0, 0),
    new THREE.Vector3(0.5, 0, 0),
    new THREE.Vector3(0.5, 0, 2.5),
    new THREE.Vector3(-2.5, 0, 2.5),
  ]

  DEVICES.forEach((dev, i) => {
    let geometry: THREE.BufferGeometry
    if (dev.shape === 'cylinder') {
      geometry = new THREE.CylinderGeometry(dev.dims[0], dev.dims[0], dev.dims[1], dev.dims[2])
    } else {
      geometry = new THREE.BoxGeometry(...(dev.dims as [number, number, number]))
    }
    const material = new THREE.MeshPhongMaterial({
      color: dev.color,
      shininess: 80,
      specular: 0x222244,
    })
    const mesh = new THREE.Mesh(geometry, material)
    mesh.position.copy(positions[i])
    mesh.position.y = dev.dims[1] / 2
    mesh.userData = { deviceId: dev.id }
    scene!.add(mesh)
    meshes.set(dev.id, mesh)

    // 连线 LED 指示灯（小球）
    const ledGeo = new THREE.SphereGeometry(0.04, 8, 8)
    const ledMat = new THREE.MeshBasicMaterial({ color: 0x22c55e })
    for (let l = 0; l < 4; l++) {
      const led = new THREE.Mesh(ledGeo, ledMat)
      led.position.set(
        positions[i].x + (l - 1.5) * 0.25,
        dev.dims[1] + 0.02,
        positions[i].z + dev.dims[2] / 2 * 0.8
      )
      scene!.add(led)
    }
  })

  // 连接线（Ethernet 链路）
  const lineMat = new THREE.LineBasicMaterial({ color: 0xc7d2fe, linewidth: 2 })
  const linkPairs = [[0, 1], [1, 2], [2, 3], [3, 0]]
  linkPairs.forEach(([a, b]) => {
    const start = positions[a].clone()
    const end = positions[b].clone()
    start.y = 0.15; end.y = 0.15
    const geo = new THREE.BufferGeometry().setFromPoints([start, end])
    scene!.add(new THREE.Line(geo, lineMat))
  })

  animate()
}

function animate() {
  animFrameId = requestAnimationFrame(animate)
  if (!renderer || !scene || !camera) return

  // 自动慢速旋转
  if (!isDragging) rotY += 0.003

  // 旋转整个场景的替代方法：使用 camera 轨道
  const radius = 7
  camera.position.x = radius * Math.sin(rotY) * Math.cos(rotX)
  camera.position.y = radius * Math.sin(rotX) + 2
  camera.position.z = radius * Math.cos(rotY) * Math.cos(rotX)
  camera.lookAt(0, 0.5, 0)

  renderer.render(scene, camera)
}

function onCanvasMouseDown(e: MouseEvent) {
  isDragging = true
  prevMouse = { x: e.clientX, y: e.clientY }
}

function onCanvasMouseMove(e: MouseEvent) {
  if (!isDragging) return
  const dx = e.clientX - prevMouse.x
  const dy = e.clientY - prevMouse.y
  rotY += dx * 0.008
  rotX = Math.max(-0.4, Math.min(0.6, rotX + dy * 0.008))
  prevMouse = { x: e.clientX, y: e.clientY }
}

function onCanvasMouseUp() { isDragging = false }

function onCanvasClick(e: MouseEvent) {
  if (!renderer || !scene || !camera || !canvasRef.value) return
  const rect = canvasRef.value.getBoundingClientRect()
  const mouse = new THREE.Vector2(
    ((e.clientX - rect.left) / rect.width) * 2 - 1,
    -((e.clientY - rect.top) / rect.height) * 2 + 1,
  )
  const raycaster = new THREE.Raycaster()
  raycaster.setFromCamera(mouse, camera)
  const intersects = raycaster.intersectObjects(scene.children)
  if (intersects.length > 0) {
    const obj = intersects[0].object
    const devId = obj.userData?.deviceId as string
    if (devId) {
      const dev = DEVICES.find(d => d.id === devId)
      selectedDevice.value = dev || null
      // 高亮被点击设备
      meshes.forEach((mesh, id) => {
        const mat = mesh.material as THREE.MeshPhongMaterial
        const d = DEVICES.find(x => x.id === id)!
        mat.color.setHex(id === devId ? 0xffffff : d.color)
        mat.emissive.setHex(id === devId ? d.color : 0x000000)
        mat.emissiveIntensity = id === devId ? 0.4 : 0
      })
    }
  }
}

function handleResize() {
  if (!renderer || !camera || !canvasRef.value) return
  const w = canvasRef.value.clientWidth
  const h = canvasRef.value.clientHeight
  renderer.setSize(w, h)
  camera.aspect = w / h
  camera.updateProjectionMatrix()
}

onMounted(() => {
  initThree()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  cancelAnimationFrame(animFrameId)
  renderer?.dispose()
  window.removeEventListener('resize', handleResize)
})
</script>

<template>
  <div class="space-y-5">

    <!-- 标题 -->
    <div class="card">
      <h2 class="section-title">🖥️ 3D 网络设备可视化</h2>
      <p class="section-desc">点击设备查看详情，拖拽旋转视角，深入了解各设备的接口与工作原理</p>
    </div>

    <!-- Three.js 画布 + 设备信息 -->
    <div class="flex flex-col lg:flex-row gap-4">

      <!-- 3D 场景 -->
      <div class="flex-1 card p-0 overflow-hidden" ref="containerRef">
        <div class="bg-gradient-to-b from-blue-50/50 to-white px-4 pt-3 pb-1 border-b border-gray-100">
          <p class="text-xs text-gray-400">点击设备 → 查看详情 &nbsp;|&nbsp; 拖拽 → 旋转视角</p>
        </div>
        <canvas
          ref="canvasRef"
          class="w-full block"
          style="height: 380px; cursor: grab;"
          @mousedown="onCanvasMouseDown"
          @mousemove="onCanvasMouseMove"
          @mouseup="onCanvasMouseUp"
          @mouseleave="onCanvasMouseUp"
          @click="onCanvasClick"
        />
        <!-- 图例 -->
        <div class="px-4 pb-3 flex flex-wrap gap-3">
          <div v-for="dev in DEVICES" :key="dev.id"
            class="flex items-center gap-1.5 text-xs text-gray-500 cursor-pointer hover:text-gray-700 transition-colors"
            @click="selectedDevice = dev">
            <span class="text-base">{{ dev.icon }}</span>
            <span>{{ dev.name.split('（')[0] }}</span>
          </div>
        </div>
      </div>

      <!-- 设备详情面板 -->
      <div class="lg:w-72 card">
        <div v-if="!selectedDevice" class="flex flex-col items-center justify-center h-64 text-gray-300">
          <div class="text-6xl mb-3">🖱️</div>
          <p class="text-sm text-center">点击 3D 场景中的<br>任意设备查看详情</p>
        </div>
        <div v-else class="space-y-4">
          <div class="flex items-center gap-3">
            <span class="text-3xl">{{ selectedDevice.icon }}</span>
            <div>
              <h3 class="font-semibold text-gray-800 text-sm">{{ selectedDevice.name }}</h3>
              <div class="flex items-center gap-2 mt-1">
                <div class="w-16 h-1 rounded-full" :style="{ backgroundColor: selectedDevice.highlight }"></div>
                <span class="text-xs font-mono px-2 py-0.5 rounded-full text-white text-[10px]" :style="{ backgroundColor: selectedDevice.highlight }">{{ selectedDevice.osi_layer }}</span>
              </div>
            </div>
          </div>

          <div class="bg-gray-50 rounded-xl p-3">
            <p class="text-xs font-medium text-gray-500 mb-1">工作原理</p>
            <p class="text-sm text-gray-700 leading-relaxed">{{ selectedDevice.description }}</p>
          </div>

          <div>
            <p class="text-xs font-medium text-gray-500 mb-2">接口说明</p>
            <div class="space-y-1.5">
              <div v-for="port in selectedDevice.ports" :key="port"
                class="flex items-center gap-2 text-xs">
                <span class="w-2 h-2 rounded-full shrink-0" :style="{ backgroundColor: selectedDevice.highlight }"></span>
                <span class="text-gray-600 font-mono">{{ port }}</span>
              </div>
            </div>
          </div>

          <div class="pt-2 border-t border-gray-100">
            <p class="text-xs font-medium text-gray-400 mb-1">参考标准</p>
            <p class="text-xs text-indigo-500 font-mono">{{ selectedDevice.rfc }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 网络拓扑说明卡片 -->
    <div class="card">
      <h3 class="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
        <span>📊</span> 当前拓扑说明
      </h3>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div v-for="dev in DEVICES" :key="dev.id"
          class="flex flex-col items-center text-center p-3 bg-gray-50 rounded-xl cursor-pointer hover:bg-indigo-50 transition-colors"
          @click="selectedDevice = dev">
          <span class="text-2xl mb-1">{{ dev.icon }}</span>
          <span class="text-xs font-medium text-gray-700">{{ dev.name.split('（')[0] }}</span>
          <span class="text-xs text-gray-400 mt-0.5">{{ dev.ports.length }} 个接口</span>
        </div>
      </div>
      <p class="text-xs text-gray-400 mt-3">典型办公网络拓扑：Internet → 路由器（NAT/网关）→ 防火墙（ACL安全策略）→ 交换机（VLAN广播域隔离）→ AP（802.11ax无线接入），四设备通过以太网连接，覆盖 OSI L1–L7 全层。</p>
    </div>

  </div>
</template>
