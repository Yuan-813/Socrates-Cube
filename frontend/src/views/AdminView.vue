<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useAuthStore } from '@/stores/authStore'
import { adminApi } from '@/api/admin'
import type { AdminUserItem, SystemStats, LogItem } from '@/api/admin'
import * as echarts from 'echarts'
import { ElMessage, ElMessageBox } from 'element-plus'

const authStore = useAuthStore()
const activeTab = ref<'overview' | 'users' | 'logs'>('overview')

// ── 系统概览 ──────────────────────────────────────────
const sysStats = ref<SystemStats | null>(null)
const statsLoading = ref(false)
const growthChartRef = ref<HTMLDivElement | null>(null)

const statCards = computed(() => {
  const s = sysStats.value
  if (!s) return []
  return [
    { label: '注册用户总数', value: s.total_users, icon: '👥', color: '#3b82f6', bg: '#eff6ff' },
    { label: '今日活跃用户', value: s.active_today, icon: '🔥', color: '#ef4444', bg: '#fef2f2' },
    { label: '总对话会话数', value: s.total_sessions, icon: '💬', color: '#8b5cf6', bg: '#faf5ff' },
    { label: '诊断评估总次数', value: s.total_diagnoses, icon: '🔍', color: '#f59e0b', bg: '#fffbeb' },
    { label: '平均知识掌握度', value: `${s.avg_mastery}%`, icon: '📊', color: '#10b981', bg: '#f0fdf4' },
    { label: '知识图谱节点数', value: s.knowledge_nodes_count, icon: '🌐', color: '#06b6d4', bg: '#ecfeff' },
  ]
})

async function loadStats() {
  statsLoading.value = true
  try {
    sysStats.value = await adminApi.getStats()
    setTimeout(renderGrowthChart, 100)
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '加载统计数据失败，请确认管理员权限')
  } finally {
    statsLoading.value = false
  }
}

function renderGrowthChart() {
  if (!growthChartRef.value || !sysStats.value) return
  const chart = echarts.init(growthChartRef.value)
  const daily = sysStats.value.daily_new_users

  chart.setOption({
    tooltip: { trigger: 'axis', formatter: '{b}<br/>新增用户：{c}' },
    grid: { left: 40, right: 16, top: 16, bottom: 30 },
    xAxis: {
      type: 'category',
      data: daily.map(d => d.date),
      axisLabel: { fontSize: 11, color: '#94a3b8' },
      axisLine: { lineStyle: { color: '#e2e8f0' } },
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
      axisLabel: { fontSize: 11, color: '#94a3b8' },
      splitLine: { lineStyle: { color: '#f1f5f9', type: 'dashed' } },
    },
    series: [{
      type: 'bar',
      data: daily.map(d => d.count),
      barMaxWidth: 40,
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: '#6366f1' },
          { offset: 1, color: '#3b82f6' },
        ]),
        borderRadius: [6, 6, 0, 0],
      },
    }],
  })
  window.addEventListener('resize', () => chart.resize())
}

// ── 用户管理 ──────────────────────────────────────────
const users = ref<AdminUserItem[]>([])
const userTotal = ref(0)
const userPage = ref(1)
const userPageSize = 20
const userLoading = ref(false)
const searchKeyword = ref('')

const roleOptions = [
  { label: '学生', value: 'student' },
  { label: '专业人士', value: 'professional' },
  { label: '自学者', value: 'self_learner' },
  { label: '求职者', value: 'job_seeker' },
  { label: '管理员', value: 'admin' },
]

const roleTagMap: Record<string, string> = {
  student: 'primary',
  professional: 'success',
  self_learner: 'warning',
  job_seeker: 'info',
  admin: 'danger',
  teacher: 'success',
}
void roleTagMap // suppress unused warning

async function loadUsers() {
  userLoading.value = true
  try {
    const result = await adminApi.listUsers(userPage.value, userPageSize, searchKeyword.value || undefined)
    users.value = result.items
    userTotal.value = result.total
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '加载用户列表失败')
  } finally {
    userLoading.value = false
  }
}

async function handleRoleChange(user: AdminUserItem, newRole: string) {
  try {
    await ElMessageBox.confirm(`确认将 "${user.username}" 的角色修改为 "${newRole}" 吗？`, '确认修改', {
      type: 'warning',
      confirmButtonText: '确认',
      cancelButtonText: '取消',
    })
    await adminApi.updateUserRole(user.id, newRole)
    user.role_type = newRole
    ElMessage.success('角色修改成功')
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error(e?.response?.data?.detail || '修改失败')
    }
  }
}

function handleSearch() {
  userPage.value = 1
  loadUsers()
}

// ── 系统日志 ──────────────────────────────────────────
const logs = ref<LogItem[]>([])
const logTotal = ref(0)
const logPage = ref(1)
const logLoading = ref(false)

async function loadLogs() {
  logLoading.value = true
  try {
    const result = await adminApi.getLogs(logPage.value, 50)
    logs.value = result.items
    logTotal.value = result.total
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '加载日志失败')
  } finally {
    logLoading.value = false
  }
}

// ── Tab 切换 ──────────────────────────────────────────
function switchTab(tab: typeof activeTab.value) {
  activeTab.value = tab
  if (tab === 'overview' && !sysStats.value) loadStats()
  if (tab === 'users' && users.value.length === 0) loadUsers()
  if (tab === 'logs' && logs.value.length === 0) loadLogs()
}

onMounted(() => {
  loadStats()
})
</script>

<template>
  <div class="admin-view">
    <!-- 页头 -->
    <div class="admin-header">
      <div>
        <h2 class="admin-title">管理后台</h2>
        <p class="admin-sub">系统管理与数据分析中心 · 管理员专属</p>
      </div>
      <div class="admin-role-badge">
        <el-icon size="14"><Setting /></el-icon>
        {{ authStore.user?.roleType === 'admin' ? '管理员' : '当前账号无管理权限' }}
      </div>
    </div>

    <!-- Tab 切换 -->
    <div class="admin-tabs">
      <button
        v-for="tab in [
          { key: 'overview', label: '系统概览', icon: '📊' },
          { key: 'users', label: '用户管理', icon: '👥' },
          { key: 'logs', label: '系统日志', icon: '📋' },
        ]"
        :key="tab.key"
        class="admin-tab"
        :class="{ active: activeTab === tab.key }"
        @click="switchTab(tab.key as any)"
      >
        {{ tab.icon }} {{ tab.label }}
      </button>
    </div>

    <!-- Tab 内容：系统概览 -->
    <div v-if="activeTab === 'overview'">
      <div v-if="statsLoading" class="loading-wrap">
        <el-icon class="rotating" size="24" color="#6366f1"><Loading /></el-icon>
        <span>加载中...</span>
      </div>
      <template v-else-if="sysStats">
        <!-- 6块统计卡片 -->
        <div class="stat-grid">
          <div
            v-for="card in statCards"
            :key="card.label"
            class="stat-card"
            :style="{ background: card.bg }"
          >
            <div class="stat-icon" :style="{ background: card.color + '22' }">{{ card.icon }}</div>
            <div class="stat-body">
              <div class="stat-value" :style="{ color: card.color }">{{ card.value }}</div>
              <div class="stat-label">{{ card.label }}</div>
            </div>
          </div>
        </div>

        <!-- 用户增长折线图 -->
        <div class="chart-card">
          <div class="chart-head">
            <span class="chart-title">📈 近 7 天新增用户趋势</span>
            <button class="refresh-btn" @click="loadStats">
              <el-icon><Refresh /></el-icon> 刷新
            </button>
          </div>
          <div ref="growthChartRef" style="height: 220px;" />
        </div>
      </template>
    </div>

    <!-- Tab 内容：用户管理 -->
    <div v-if="activeTab === 'users'" class="users-panel">
      <div class="users-toolbar">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索用户名或邮箱..."
          style="width: 240px;"
          clearable
          @keyup.enter="handleSearch"
          @clear="handleSearch"
        >
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <button class="refresh-btn" @click="handleSearch">搜索</button>
        <span class="total-label">共 {{ userTotal }} 名用户</span>
      </div>

      <el-table
        :data="users"
        v-loading="userLoading"
        border
        stripe
        style="width: 100%"
        :header-cell-style="{ background: '#f8faff', fontWeight: '700', fontSize: '13px' }"
      >
        <el-table-column label="用户名" prop="username" min-width="120" />
        <el-table-column label="邮箱" prop="email" min-width="180">
          <template #default="{ row }">{{ row.email || '—' }}</template>
        </el-table-column>
        <el-table-column label="手机" prop="phone" width="120">
          <template #default="{ row }">{{ row.phone || '—' }}</template>
        </el-table-column>
        <el-table-column label="角色" prop="role_type" width="180">
          <template #default="{ row }">
            <el-select
              :model-value="row.role_type"
              size="small"
              @change="(val: string) => handleRoleChange(row, val)"
              style="width: 140px;"
            >
              <el-option
                v-for="opt in roleOptions"
                :key="opt.value"
                :label="opt.label"
                :value="opt.value"
              />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="已引导" prop="onboarded" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.onboarded ? 'success' : 'info'" size="small">
              {{ row.onboarded ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="注册时间" prop="create_time" width="160" />
        <el-table-column label="用户ID" prop="id" min-width="140">
          <template #default="{ row }">
            <span style="font-family: monospace; font-size: 11px; color: #94a3b8;">{{ row.id }}</span>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="userPage"
          :page-size="userPageSize"
          :total="userTotal"
          layout="prev, pager, next, total"
          @current-change="loadUsers"
        />
      </div>
    </div>

    <!-- Tab 内容：系统日志 -->
    <div v-if="activeTab === 'logs'" class="logs-panel">
      <div class="users-toolbar">
        <span class="total-label">共 {{ logTotal }} 条日志</span>
        <button class="refresh-btn" @click="loadLogs">
          <el-icon><Refresh /></el-icon> 刷新
        </button>
      </div>

      <el-table
        :data="logs"
        v-loading="logLoading"
        border
        stripe
        style="width: 100%"
        :header-cell-style="{ background: '#f8faff', fontWeight: '700', fontSize: '13px' }"
      >
        <el-table-column label="时间" prop="timestamp" width="170" />
        <el-table-column label="Agent" prop="agent_name" width="140">
          <template #default="{ row }">
            <el-tag type="primary" size="small">{{ row.agent_name }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="动作" prop="action" width="140">
          <template #default="{ row }">
            <span style="font-family: monospace; font-size: 12px; color: #475569;">{{ row.action }}</span>
          </template>
        </el-table-column>
        <el-table-column label="会话ID" prop="session_id" min-width="160">
          <template #default="{ row }">
            <span style="font-family: monospace; font-size: 11px; color: #94a3b8;">{{ row.session_id }}</span>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="logPage"
          :page-size="50"
          :total="logTotal"
          layout="prev, pager, next, total"
          @current-change="loadLogs"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.admin-view {
  display: flex;
  flex-direction: column;
  gap: 18px;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
}

.admin-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
}

.admin-title {
  font-size: 20px;
  font-weight: 800;
  color: #1e293b;
  letter-spacing: -0.5px;
  margin-bottom: 4px;
}

.admin-sub {
  font-size: 13px;
  color: #64748b;
}

.admin-role-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: 20px;
  background: linear-gradient(135deg, #fef3c7, #fde68a);
  color: #92400e;
  font-size: 12px;
  font-weight: 700;
  border: 1px solid #fcd34d;
}

/* Tabs */
.admin-tabs {
  display: flex;
  gap: 6px;
  background: #f8faff;
  border-radius: 12px;
  padding: 4px;
  border: 1px solid #e8eef8;
}

.admin-tab {
  flex: 1;
  padding: 10px 16px;
  border-radius: 9px;
  border: none;
  background: transparent;
  color: #64748b;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.admin-tab:hover { color: #6366f1; background: rgba(99,102,241,0.06); }

.admin-tab.active {
  background: white;
  color: #6366f1;
  box-shadow: 0 2px 8px rgba(99,102,241,0.12);
}

/* Loading */
.loading-wrap {
  height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: #94a3b8;
  font-size: 14px;
}

@keyframes spin { to { transform: rotate(360deg); } }
.rotating { animation: spin 1s linear infinite; }

/* Stat Grid */
.stat-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
  margin-bottom: 16px;
}

.stat-card {
  border-radius: 14px;
  padding: 18px;
  border: 1px solid #e8eef8;
  display: flex;
  align-items: center;
  gap: 14px;
  box-shadow: 0 2px 6px rgba(0,0,0,0.03);
  transition: all 0.2s;
}

.stat-card:hover { transform: translateY(-2px); box-shadow: 0 6px 16px rgba(0,0,0,0.07); }

.stat-icon {
  width: 44px; height: 44px;
  border-radius: 11px;
  display: flex; align-items: center; justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
}

.stat-value {
  font-size: 24px;
  font-weight: 800;
  line-height: 1;
  letter-spacing: -0.5px;
}

.stat-label {
  font-size: 12px;
  color: #64748b;
  margin-top: 4px;
  font-weight: 500;
}

/* Chart card */
.chart-card {
  background: white;
  border-radius: 16px;
  border: 1px solid #e8eef8;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

.chart-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}

.chart-title {
  font-size: 14px;
  font-weight: 700;
  color: #1e293b;
}

.refresh-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 6px 14px;
  border: 1.5px solid #e2e8f0;
  border-radius: 8px;
  background: white;
  color: #64748b;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.refresh-btn:hover { border-color: #6366f1; color: #6366f1; }

/* Users / Logs panel */
.users-panel, .logs-panel {
  background: white;
  border-radius: 16px;
  border: 1px solid #e8eef8;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

.users-toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
  flex-wrap: wrap;
}

.total-label {
  font-size: 13px;
  color: #64748b;
  margin-left: auto;
}

.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 14px;
}

@media (max-width: 768px) {
  .stat-grid { grid-template-columns: 1fr 1fr; }
}
</style>
