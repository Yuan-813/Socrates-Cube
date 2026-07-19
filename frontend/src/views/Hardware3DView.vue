<script setup lang="ts">
import { ref, onMounted, onUnmounted, reactive } from 'vue'

// Three.js 动态导入（避免 SSR 问题）
const canvasRef = ref<HTMLCanvasElement | null>(null)
const loadError = ref('')
const isLoading = ref(true)
const selectedDevice = ref<string | null>(null)

// 设备信息
interface Device3D {
  id: string
  name: string
  icon: string
  color: number
  desc: string
  ports: string[]
}

const devices: Device3D[] = [
  {
    id: 'router',
    name: '路由器',
    icon: '🔀',
    color: 0x4f46e5,
    desc: '负责不同网络间的数据包转发，实现 IP 路由选择。工作在网络层（OSI 第三层）。',
    ports: ['WAN x1', 'LAN x4', 'Console x1'],
  },
  {
    id: 'switch',
    name: '交换机',
    icon: '🔌',
    color: 0x059669,
    desc: '在同一局域网内转发数据帧，基于 MAC 地址学习。工作在数据链路层（OSI 第二层）。',
    ports: ['Ethernet x24', 'SFP x2', 'Console x1'],
  },
  {
    id: 'server',
    name: '服务器',
    icon: '🖥️',
    color: 0xdc2626,
    desc: '提供计算、存储和网络服务的高性能主机。可运行 Web/DNS/DHCP 等各类网络服务。',
    ports: ['NIC x2', 'USB x4', 'Power x2'],
  },
  {
    id: 'firewall',
    name: '防火墙',
    icon: '🛡️',
    color: 0xd97706,
    desc: '监控和控制进出网络的数据包，按安全策略允许或拒绝流量。是网络安全的第一道防线。',
    ports: ['Inside x1', 'Outside x1', 'DMZ x1'],
  },
]

const selectedDeviceData = ref<Device3D | null>(null)

// Three.js 场景相关变量（存储在 reactive 对象中避免 Vue 响应式追踪导致问题）
const threeCtx: {
  renderer: unknown
  scene: unknown
  camera: unknown
  cube: unknown
  animId: number | null
  particles: unknown[]
} = reactive({
  renderer: null,
  scene: null,
  camera: null,
  cube: null,
  animId: null,
  particles: [],
})

async function initThree() {
  if (!canvasRef.value) return
  try {
    const THREE = await import('three')

    // 创建渲染器
    const renderer = new THREE.WebGLRenderer({
      canvas: canvasRef.value,
      antialias: true,
      alpha: true,
    })
    renderer.setSize(canvasRef.value.clientWidth, canvasRef.value.clientHeight)
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    renderer.setClearColor(0x0a0f1e, 1)

    // 场景
    const scene = new THREE.Scene()

    // 摄像机
    const camera = new THREE.PerspectiveCamera(
      60,
      canvasRef.value.clientWidth / canvasRef.value.clientHeight,
      0.1,
      100,
    )
    camera.position.set(0, 2, 6)
    camera.lookAt(0, 0, 0)

    // 光源
    const ambientLight = new THREE.AmbientLight(0x404080, 2)
    scene.add(ambientLight)
    const dirLight = new THREE.DirectionalLight(0x6699ff, 3)
    dirLight.position.set(5, 8, 5)
    scene.add(dirLight)
    const pointLight = new THREE.PointLight(0x4f46e5, 4, 20)
    pointLight.position.set(-3, 3, 3)
    scene.add(pointLight)

    // 主设备模型（路由器 - 默认）
    const deviceGroup = new THREE.Group()

    // 机箱主体
    const boxGeo = new THREE.BoxGeometry(3, 0.6, 1.6)
    const boxMat = new THREE.MeshPhongMaterial({
      color: 0x1a2035,
      specular: 0x334466,
      shininess: 80,
    })
    const box = new THREE.Mesh(boxGeo, boxMat)
    deviceGroup.add(box)

    // 面板灯（LED 矩阵）
    for (let i = 0; i < 8; i++) {
      const ledGeo = new THREE.SphereGeometry(0.04, 8, 8)
      const hue = (i / 8) * 0.3 + 0.6
      const ledMat = new THREE.MeshBasicMaterial({ color: new THREE.Color().setHSL(hue, 1, 0.5) })
      const led = new THREE.Mesh(ledGeo, ledMat)
      led.position.set(-1.2 + i * 0.35, 0.32, 0.6)
      deviceGroup.add(led)
    }

    // 端口孔（RJ45）
    for (let i = 0; i < 4; i++) {
      const portGeo = new THREE.BoxGeometry(0.2, 0.15, 0.02)
      const portMat = new THREE.MeshPhongMaterial({ color: 0x223355 })
      const port = new THREE.Mesh(portGeo, portMat)
      port.position.set(-0.7 + i * 0.45, -0.05, 0.81)
      deviceGroup.add(port)
    }

    // 散热槽纹理
    for (let i = 0; i < 6; i++) {
      const slotGeo = new THREE.BoxGeometry(0.02, 0.4, 1.4)
      const slotMat = new THREE.MeshPhongMaterial({ color: 0x0d1525 })
      const slot = new THREE.Mesh(slotGeo, slotMat)
      slot.position.set(1.0 + i * 0.16, 0.02, 0)
      deviceGroup.add(slot)
    }

    scene.add(deviceGroup)
    threeCtx.cube = deviceGroup as unknown

    // 粒子（报文流动）
    const particleCount = 80
    const particleGeo = new THREE.BufferGeometry()
    const positions = new Float32Array(particleCount * 3)
    const particleData: Array<{ x: number; y: number; z: number; vx: number; vy: number; vz: number; life: number }> = []

    for (let i = 0; i < particleCount; i++) {
      const angle = (i / particleCount) * Math.PI * 2
      const r = 1.8 + Math.random() * 1.5
      particleData.push({
        x: Math.cos(angle) * r,
        y: (Math.random() - 0.5) * 2,
        z: Math.sin(angle) * r,
        vx: -Math.sin(angle) * 0.02,
        vy: (Math.random() - 0.5) * 0.01,
        vz: Math.cos(angle) * 0.02,
        life: Math.random(),
      })
      positions[i * 3] = particleData[i].x
      positions[i * 3 + 1] = particleData[i].y
      positions[i * 3 + 2] = particleData[i].z
    }
    particleGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3))
    const particleMat = new THREE.PointsMaterial({
      color: 0x64b5f6,
      size: 0.06,
      transparent: true,
      opacity: 0.8,
    })
    const particles = new THREE.Points(particleGeo, particleMat)
    scene.add(particles)

    // 网格地面
    const gridHelper = new THREE.GridHelper(10, 20, 0x1a2a4a, 0x0d1525)
    gridHelper.position.y = -0.8
    scene.add(gridHelper)

    // 连接线（拓扑）
    const lineMat = new THREE.LineBasicMaterial({ color: 0x4f6a9e, transparent: true, opacity: 0.4 })
    for (let i = 0; i < 6; i++) {
      const angle = (i / 6) * Math.PI * 2
      const r = 3.5
      const points = [
        new THREE.Vector3(0, 0, 0),
        new THREE.Vector3(Math.cos(angle) * r, (Math.random() - 0.5) * 1.5, Math.sin(angle) * r),
      ]
      const lineGeo = new THREE.BufferGeometry().setFromPoints(points)
      scene.add(new THREE.Line(lineGeo, lineMat))
    }

    threeCtx.renderer = renderer as unknown
    threeCtx.scene = scene as unknown
    threeCtx.camera = camera as unknown

    // 动画循环
    let t = 0
    const animate = () => {
      threeCtx.animId = requestAnimationFrame(animate)
      t += 0.01

      // 设备旋转
      if (deviceGroup) {
        deviceGroup.rotation.y = Math.sin(t * 0.3) * 0.4
        deviceGroup.rotation.x = Math.sin(t * 0.2) * 0.08
        deviceGroup.position.y = Math.sin(t * 0.5) * 0.1
      }

      // 粒子更新
      const posArr = particleGeo.attributes.position.array as Float32Array
      for (let i = 0; i < particleCount; i++) {
        const p = particleData[i]
        p.life += 0.005
        if (p.life > 1) {
          p.life = 0
          const angle = Math.random() * Math.PI * 2
          const r = 1.8 + Math.random() * 1.5
          p.x = Math.cos(angle) * r
          p.y = (Math.random() - 0.5) * 2
          p.z = Math.sin(angle) * r
          p.vx = -Math.sin(angle) * 0.025
          p.vz = Math.cos(angle) * 0.025
        }
        p.x += p.vx
        p.y += p.vy
        p.z += p.vz
        posArr[i * 3] = p.x
        posArr[i * 3 + 1] = p.y
        posArr[i * 3 + 2] = p.z
      }
      particleGeo.attributes.position.needsUpdate = true

      // LED 闪烁
      deviceGroup.children.forEach((child, i) => {
        const c = child as { isMesh?: boolean; material?: { opacity: number; transparent: boolean } }
        if (i > 0 && i <= 8 && c.isMesh && c.material) {
          c.material.opacity = 0.5 + 0.5 * Math.sin(t * 4 + i)
          c.material.transparent = true
        }
      })

      renderer.render(scene, camera)
    }
    animate()

    isLoading.value = false

  } catch (e: unknown) {
    loadError.value = `Three.js 加载失败：${e instanceof Error ? e.message : String(e)}`
    isLoading.value = false
  }
}

function selectDevice(device: Device3D) {
  selectedDevice.value = device.id
  selectedDeviceData.value = device
}

// 窗口大小自适应
function onResize() {
  if (!canvasRef.value || !threeCtx.renderer || !threeCtx.camera) return
  const w = canvasRef.value.clientWidth
  const h = canvasRef.value.clientHeight
  ;(threeCtx.camera as { aspect: number; updateProjectionMatrix: () => void }).aspect = w / h
  ;(threeCtx.camera as { aspect: number; updateProjectionMatrix: () => void }).updateProjectionMatrix()
  ;(threeCtx.renderer as { setSize: (w: number, h: number) => void }).setSize(w, h)
}

onMounted(() => {
  initThree()
  window.addEventListener('resize', onResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', onResize)
  if (threeCtx.animId !== null) cancelAnimationFrame(threeCtx.animId)
  ;(threeCtx.renderer as { dispose?: () => void } | null)?.dispose?.()
})
</script>

<template>
  <div class="hw3d-page">
    <!-- 标题 -->
    <div class="hw3d-header">
      <h2 class="hw3d-title">🖥️ 3D 硬件可视化</h2>
      <p class="hw3d-subtitle">交互式网络设备三维展示，报文流动粒子动画，实时学习硬件原理</p>
    </div>

    <!-- 主区域 -->
    <div class="hw3d-main">
      <!-- 3D 渲染画布 -->
      <div class="canvas-wrapper">
        <div v-if="isLoading" class="loading-overlay">
          <div class="loading-spinner"></div>
          <p>加载 Three.js 渲染引擎...</p>
        </div>
        <div v-if="loadError" class="error-overlay">
          <p>{{ loadError }}</p>
          <p class="text-sm mt-1">请运行 <code>npm install three</code> 安装依赖</p>
        </div>
        <canvas ref="canvasRef" class="hw3d-canvas"></canvas>

        <!-- 覆盖标签 -->
        <div class="canvas-overlay-label">
          <span class="label-dot"></span>
          实时粒子报文流动
        </div>
      </div>

      <!-- 右侧控制面板 -->
      <div class="hw3d-panel">
        <h3 class="panel-title">设备选择</h3>
        <div class="device-list">
          <button
            v-for="d in devices"
            :key="d.id"
            class="device-btn"
            :class="{ active: selectedDevice === d.id }"
            @click="selectDevice(d)"
          >
            <span class="device-icon">{{ d.icon }}</span>
            <div>
              <div class="device-name">{{ d.name }}</div>
            </div>
          </button>
        </div>

        <!-- 设备详情 -->
        <Transition name="fade">
          <div v-if="selectedDeviceData" class="device-detail">
            <div class="detail-header">
              <span>{{ selectedDeviceData.icon }}</span>
              <span class="detail-name">{{ selectedDeviceData.name }}</span>
            </div>
            <p class="detail-desc">{{ selectedDeviceData.desc }}</p>
            <div class="detail-ports">
              <div class="ports-title">端口配置</div>
              <div class="ports-list">
                <span v-for="port in selectedDeviceData.ports" :key="port" class="port-tag">
                  {{ port }}
                </span>
              </div>
            </div>
          </div>
        </Transition>

        <!-- 知识点说明 -->
        <div class="knowledge-box">
          <h4 class="knowledge-title">📡 网络拓扑知识</h4>
          <ul class="knowledge-list">
            <li>蓝色粒子 = 数据包流动路径</li>
            <li>网格线 = 逻辑拓扑连接</li>
            <li>LED 灯 = 接口状态指示</li>
            <li>旋转模型可 360° 观察设备</li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.hw3d-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
  height: 100%;
}

.hw3d-header {
  background: white;
  border-radius: 14px;
  padding: 18px 22px;
  border: 1px solid #e8eef8;
}

.hw3d-title {
  font-size: 18px;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 6px;
}

.hw3d-subtitle {
  font-size: 13px;
  color: #64748b;
  margin: 0;
}

.hw3d-main {
  display: flex;
  gap: 16px;
  flex: 1;
  min-height: 500px;
}

.canvas-wrapper {
  flex: 1;
  position: relative;
  background: #0a0f1e;
  border-radius: 14px;
  overflow: hidden;
  min-height: 480px;
}

.hw3d-canvas {
  width: 100%;
  height: 100%;
  display: block;
}

.loading-overlay,
.error-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #94a3b8;
  font-size: 14px;
  background: rgba(10, 15, 30, 0.9);
  z-index: 10;
}

.loading-spinner {
  width: 36px;
  height: 36px;
  border: 3px solid rgba(99, 102, 241, 0.3);
  border-top-color: #6366f1;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: 12px;
}

.canvas-overlay-label {
  position: absolute;
  bottom: 16px;
  left: 16px;
  background: rgba(99, 102, 241, 0.2);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(99, 102, 241, 0.4);
  color: #a5b4fc;
  font-size: 11px;
  padding: 5px 10px;
  border-radius: 20px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.label-dot {
  width: 6px;
  height: 6px;
  background: #60a5fa;
  border-radius: 50%;
  animation: pulse 1.5s infinite;
}

/* 右侧面板 */
.hw3d-panel {
  width: 240px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  flex-shrink: 0;
}

.panel-title {
  font-size: 13px;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 4px;
}

.device-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  background: white;
  border-radius: 12px;
  padding: 10px;
  border: 1px solid #e8eef8;
}

.device-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 10px;
  border: 2px solid transparent;
  border-radius: 8px;
  background: #f8fafc;
  cursor: pointer;
  transition: all 0.18s;
  text-align: left;
}

.device-btn:hover { border-color: #c7d2fe; background: #f0f4ff; }
.device-btn.active { border-color: #6366f1; background: #eef2ff; }

.device-icon { font-size: 20px; }
.device-name { font-size: 12px; font-weight: 600; color: #1e293b; }

/* 设备详情 */
.device-detail {
  background: white;
  border-radius: 12px;
  padding: 12px;
  border: 1px solid #e8eef8;
}

.detail-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  margin-bottom: 8px;
}

.detail-name { font-weight: 700; color: #1e293b; }

.detail-desc {
  font-size: 11px;
  color: #64748b;
  line-height: 1.6;
  margin: 0 0 10px;
}

.ports-title { font-size: 10px; font-weight: 600; color: #6366f1; margin-bottom: 6px; }
.ports-list { display: flex; flex-wrap: wrap; gap: 4px; }
.port-tag {
  font-size: 10px;
  background: #f1f5f9;
  color: #475569;
  padding: 2px 7px;
  border-radius: 4px;
}

/* 知识点 */
.knowledge-box {
  background: linear-gradient(135deg, #1e1e3e, #0f172a);
  border-radius: 12px;
  padding: 12px;
  border: 1px solid #2d3a5e;
}

.knowledge-title { font-size: 12px; font-weight: 700; color: #a5b4fc; margin: 0 0 8px; }
.knowledge-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.knowledge-list li { font-size: 11px; color: #6b7fa3; }

/* 过渡 */
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

@keyframes spin { to { transform: rotate(360deg); } }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
</style>
