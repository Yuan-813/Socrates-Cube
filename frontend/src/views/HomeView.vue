<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { checkHealth } from '@/api/health'

const router = useRouter()
const backendStatus = ref<string>('检测中...')
const backendVersion = ref<string>('')

onMounted(async () => {
  try {
    const data = await checkHealth()
    backendStatus.value = data.status
    backendVersion.value = data.version
  } catch (e) {
    backendStatus.value = '未连接'
  }
})

const stats = ref([
  { label: '已完成知识点', value: '12', total: '48', color: 'blue', percent: 25, icon: 'Collection' },
  { label: '能力画像维度', value: '8', total: '8', color: 'emerald', percent: 60, icon: 'TrendCharts' },
  { label: '学习时长', value: '3.5', total: '小时', color: 'amber', percent: 40, icon: 'Timer' },
  { label: '诊断记录', value: '5', total: '次', color: 'rose', percent: 80, icon: 'FirstAidKit' },
])

const quickActions = [
  { title: '智能对话', desc: '与AI教练进行交互式学习', icon: 'ChatRound', color: '#3b82f6', bg: '#eff6ff', path: '/chat' },
  { title: '协议仿真', desc: '可视化TCP/IP协议交互过程', icon: 'VideoPlay', color: '#10b981', bg: '#ecfdf5', path: '/simulator' },
  { title: '能力画像', desc: '查看个人协议能力雷达图', icon: 'UserFilled', color: '#8b5cf6', bg: '#f5f3ff', path: '/profile' },
  { title: '认知诊断', desc: '三层诊断引擎分析理解误区', icon: 'FirstAidKit', color: '#f59e0b', bg: '#fffbeb', path: '/diagnosis' },
]

const recentActivity = ref([
  { time: '14:32', title: '完成"TCP报文格式"学习', type: 'study', tag: '已完成' },
  { time: '14:15', title: 'AI教练诊断：层次穿越型误解', type: 'diagnosis', tag: '诊断' },
  { time: '13:50', title: '观看"三次握手仿真"演示', type: 'simulator', tag: '仿真' },
  { time: '10:20', title: '生成协议流程练习题 5 道', type: 'resource', tag: '资源' },
])

function goTo(path: string) {
  router.push(path)
}

function getTagType(type: string) {
  const map: Record<string, string> = { study: 'success', diagnosis: 'warning', simulator: 'primary', resource: 'info' }
  return map[type] || 'info'
}
</script>

<template>
  <div class="space-y-6">
    <!-- 顶部欢迎区 -->
    <div class="card welcome-card">
      <div class="welcome-content">
        <div>
          <h2 class="section-title">欢迎使用 Socrates Cube</h2>
          <p class="section-desc">
            基于大模型的计算机网络协议误解诊断与个性化学习多智能体系统
          </p>
        </div>
        <div class="status-badge" :class="{ online: backendStatus === 'ok' }">
          <div class="status-dot" />
          <span>{{ backendStatus === 'ok' ? '系统运行中' : backendStatus }}</span>
          <span v-if="backendVersion" class="version">v{{ backendVersion }}</span>
        </div>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <div v-for="s in stats" :key="s.label" class="stat-card" :style="{ '--accent': s.color }">
        <div class="stat-icon" :style="{ backgroundColor: s.bg }">
          <el-icon :size="22" :color="s.color"><component :is="s.icon" /></el-icon>
        </div>
        <div class="stat-body">
          <div class="stat-value" :style="{ color: s.color }">{{ s.value }}</div>
          <div class="stat-label">{{ s.label }}</div>
          <div class="stat-bar">
            <div class="stat-fill" :style="{ width: s.percent + '%', backgroundColor: s.color }" />
          </div>
        </div>
      </div>
    </div>

    <!-- 快速操作 & 最近活动 -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- 快速操作 -->
      <div class="lg:col-span-2">
        <div class="card">
          <div class="flex items-center justify-between mb-4">
            <h3 class="font-semibold text-slate-800">快速操作</h3>
            <el-tag size="small" type="info">4 个入口</el-tag>
          </div>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div
              v-for="action in quickActions"
              :key="action.title"
              class="action-card"
              @click="goTo(action.path)"
            >
              <div class="action-icon" :style="{ backgroundColor: action.bg, color: action.color }">
                <el-icon size="24"><component :is="action.icon" /></el-icon>
              </div>
              <div class="action-body">
                <div class="action-title">{{ action.title }}</div>
                <div class="action-desc">{{ action.desc }}</div>
              </div>
              <el-icon class="action-arrow" size="16" color="#cbd5e1"><ArrowRight /></el-icon>
            </div>
          </div>
        </div>
      </div>

      <!-- 最近活动 -->
      <div class="card">
        <div class="flex items-center justify-between mb-4">
          <h3 class="font-semibold text-slate-800">最近活动</h3>
          <el-tag size="small" type="info">今日</el-tag>
        </div>
        <div class="activity-list">
          <div v-for="(act, i) in recentActivity" :key="i" class="activity-item">
            <div class="activity-time">{{ act.time }}</div>
            <div class="activity-body">
              <div class="activity-title">{{ act.title }}</div>
              <el-tag size="small" :type="getTagType(act.type)">{{ act.tag }}</el-tag>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 顶部欢迎区 - 增强渐变和质感 */
.welcome-card {
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
  color: white;
  border: none;
  position: relative;
  overflow: hidden;
  padding: 36px 32px;
  border-radius: 16px;
  box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.3);
}

.welcome-card::after {
  content: '';
  position: absolute;
  top: -50%;
  right: -10%;
  width: 50%;
  height: 200%;
  background: radial-gradient(circle, rgba(59,130,246,0.15) 0%, transparent 70%);
  transform: rotate(30deg);
  pointer-events: none;
}

.welcome-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  position: relative;
  z-index: 1;
}

.welcome-card .section-title {
  color: white;
  margin-bottom: 12px;
  font-size: 26px;
  letter-spacing: 0.5px;
}

.welcome-card .section-desc {
  color: #94a3b8;
  font-size: 15px;
  max-width: 600px;
}

/* 状态指示器 */
.status-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background-color: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(8px);
  border-radius: 20px;
  font-size: 13px;
  color: #e2e8f0;
  border: 1px solid rgba(255,255,255,0.05);
}

.status-badge.online {
  color: #a7f3d0;
  background-color: rgba(16, 185, 129, 0.15);
  border-color: rgba(16, 185, 129, 0.2);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: #64748b;
}

.online .status-dot {
  background-color: #10b981;
  box-shadow: 0 0 10px #10b981;
  animation: pulse-dot 2s infinite;
}

@keyframes pulse-dot {
  0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.4); }
  70% { box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }
  100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
}

.version {
  margin-left: 4px;
  padding-left: 12px;
  border-left: 1px solid rgba(255,255,255,0.2);
  color: #94a3b8;
  font-family: monospace;
}

/* 统计卡片 - 增加卡片轻盈感 */
.stat-card {
  background-color: white;
  border-radius: 16px;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  border: 1px solid #f1f5f9;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02), 0 2px 4px -1px rgba(0, 0, 0, 0.02);
  transition: transform 0.2s, box-shadow 0.2s;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -2px rgba(0, 0, 0, 0.03);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-body {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-value {
  font-size: 28px;
  font-weight: 800;
  line-height: 1;
}

.stat-label {
  font-size: 13px;
  color: #64748b;
  font-weight: 500;
}

.stat-bar {
  height: 4px;
  background-color: #f1f5f9;
  border-radius: 2px;
  margin-top: 8px;
  overflow: hidden;
}

.stat-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 1s cubic-bezier(0.4, 0, 0.2, 1);
}

/* 快速操作网格 */
.action-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background-color: #fff;
  border: 1px solid #f1f5f9;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.action-card:hover {
  background-color: #f8fafc;
  border-color: #e2e8f0;
  transform: scale(1.01);
}

.action-card:hover .action-arrow {
  color: #3b82f6;
  transform: translateX(4px);
}

.action-icon {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.action-body {
  flex: 1;
  min-width: 0;
}

.action-title {
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 4px;
}

.action-desc {
  font-size: 12px;
  color: #64748b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.action-arrow {
  transition: all 0.2s;
}

/* 最近活动时间线 */
.activity-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding-left: 8px;
  position: relative;
}

.activity-list::before {
  content: '';
  position: absolute;
  left: 12px;
  top: 8px;
  bottom: 8px;
  width: 2px;
  background-color: #e2e8f0;
}

.activity-item {
  display: flex;
  gap: 16px;
  position: relative;
  z-index: 1;
}

.activity-time {
  font-size: 12px;
  font-weight: 600;
  color: #94a3b8;
  width: 45px;
  flex-shrink: 0;
  text-align: right;
  padding-top: 2px;
}

.activity-body {
  flex: 1;
  background-color: #f8fafc;
  padding: 12px 16px;
  border-radius: 8px;
  border: 1px solid #f1f5f9;
  position: relative;
}

.activity-body::before {
  content: '';
  position: absolute;
  left: -21px;
  top: 14px;
  width: 10px;
  height: 10px;
  background-color: #fff;
  border: 2px solid #cbd5e1;
  border-radius: 50%;
}

.activity-title {
  font-size: 13px;
  color: #334155;
  margin-bottom: 8px;
  line-height: 1.4;
}

@media (max-width: 640px) {
  .welcome-content {
    flex-direction: column;
    gap: 16px;
  }
}
</style>
