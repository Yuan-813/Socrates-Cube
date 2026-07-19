<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, onErrorCaptured } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/userStore'
import { useAuthStore } from '@/stores/authStore'
import OnboardingGuide from '@/components/OnboardingGuide.vue'
import RoleSelector from '@/components/RoleSelector.vue'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const isCollapsed = ref(false)
const isMobile = ref(false)
const sidebarOpen = ref(false)
const userStore = useUserStore()
const authStore = useAuthStore()

/**
 * 组件级错误边界：捕获子组件树中的渲染异常
 * 正确用法：从 vue 导入 onErrorCaptured 并调用，而非定义一个同名的普通函数
 */
onErrorCaptured((err: Error, _instance, info: string) => {
  console.error('[App Error Boundary]', { err, info })
  ElMessage.error({
    message: `模块加载异常：${err.message}。若问题持续请刷新页面。`,
    duration: 6000,
    showClose: true,
  })
  // 返回 false 表示异常已被处理，阻止向上传播
  return false
})

// 登录页 / onboarding 隐藏全局布局，全屏独立渲染
const isLoginPage = computed(() =>
  route.path === '/login' ||
  route.path === '/onboarding'
)

// 首次登录引导弹窗
const showOnboarding = ref(false)
const showRoleSelector = ref(false)

function handleOnboardingDone() {
  showOnboarding.value = false
  // 如果还没有角色，弹出角色选择
  if (!authStore.user?.roleType || authStore.user.roleType === 'student') {
    showRoleSelector.value = true
  }
}

function handleRoleDone() {
  showRoleSelector.value = false
}

interface MenuItem {
  path: string
  label: string
  icon: string
}

interface MenuGroup {
  type: 'standalone' | 'group'
  title?: string
  icon?: string
  items: MenuItem[]
}

const menuGroups: MenuGroup[] = [
  { type: 'standalone', items: [{ path: '/', label: '系统首页', icon: 'HomeFilled' }] },
  {
    type: 'group',
    title: '核心学习',
    icon: 'Reading',
    items: [
      { path: '/chat', label: '智能对话', icon: 'ChatRound' },
      { path: '/diagnosis', label: '诊断面板', icon: 'FirstAidKit' },
      { path: '/profile', label: '能力画像', icon: 'UserFilled' },
      { path: '/path', label: '学习路径', icon: 'MapLocation' },
    ],
  },
  {
    type: 'group',
    title: '知识与资源',
    icon: 'FolderOpened',
    items: [
      { path: '/resources', label: '学习资源', icon: 'Collection' },
      { path: '/bookhouse', label: '教材书库', icon: 'Notebook' },
      { path: '/bookshelf', label: 'PDF知识库', icon: 'Reading' },
      { path: '/scenario', label: '情景对话', icon: 'ChatDotSquare' },
      { path: '/kg-assist', label: 'AI图谱助手', icon: 'Share' },
    ],
  },
  {
    type: 'group',
    title: '教学工具',
    icon: 'SetUp',
    items: [
      { path: '/challenger', label: '概念挑战', icon: 'WarningFilled' },
      { path: '/simulator', label: '协议仿真', icon: 'VideoPlay' },
      { path: '/device3d', label: '3D设备', icon: 'Monitor' },
      { path: '/lesson', label: '互动课堂', icon: 'Film' },
      { path: '/video-gen', label: 'AI视频生成', icon: 'VideoCamera' },
    ],
  },
  {
    type: 'group',
    title: '评测与发展',
    icon: 'DataAnalysis',
    items: [
      { path: '/exam', label: '证书考试', icon: 'EditPen' },
      { path: '/interview', label: 'AI面试', icon: 'Briefcase' },
      { path: '/career', label: '职业规划', icon: 'Promotion' },
      { path: '/dashboard', label: '学习统计', icon: 'TrendCharts' },
    ],
  },
]

// Agent日志：独立于可滚动区域，固定显示在侧边栏底部
const logMenuItem = { path: '/logs', label: 'Agent日志', icon: 'List' }

const activePath = computed(() => route.path)

// 分组展开状态，默认全部折叠
const expandedGroups = ref<Record<number, boolean>>({})
menuGroups.forEach((group, idx) => {
  if (group.type === 'group') {
    expandedGroups.value[idx] = false
  }
})

// 手风琴模式：展开一个，自动收起其他
function toggleGroup(idx: number) {
  const willOpen = !expandedGroups.value[idx]
  menuGroups.forEach((g, i) => {
    if (g.type === 'group') expandedGroups.value[i] = false
  })
  expandedGroups.value[idx] = willOpen
}

// 自动展开当前路由所在的分组
function expandActiveGroup() {
  menuGroups.forEach((group, idx) => {
    if (group.type === 'group' && group.items?.some(item => item.path === activePath.value)) {
      menuGroups.forEach((g, i) => { if (g.type === 'group') expandedGroups.value[i] = false })
      expandedGroups.value[idx] = true
    }
  })
}

watch(activePath, expandActiveGroup)

function checkMobile() {
  isMobile.value = window.innerWidth < 768
  if (!isMobile.value) sidebarOpen.value = false
}

function toggleSidebar() {
  sidebarOpen.value = !sidebarOpen.value
}

function closeSidebar() {
  sidebarOpen.value = false
}

function toggleDemoMode() {
  userStore.demoMode = !userStore.demoMode
}

function handleKeydown(e: KeyboardEvent) {
  if (e.ctrlKey && e.shiftKey && e.key === 'D') {
    e.preventDefault()
    toggleDemoMode()
  }
  if (e.ctrlKey && e.shiftKey && e.key === 'C') {
    e.preventDefault()
    window.dispatchEvent(new CustomEvent('clear-chat'))
  }
}

/* 悬浮快捷入口 */
const fabOpen = ref(false)
const fabItems = [
  { path: '/chat',      label: '智能对话', icon: '💬', color: 'linear-gradient(135deg,#3b82f6,#6366f1)' },
  { path: '/resources', label: '生成资源', icon: '🎨', color: 'linear-gradient(135deg,#10b981,#06b6d4)' },
  { path: '/simulator', label: '协议仿真', icon: '🎬', color: 'linear-gradient(135deg,#ec4899,#8b5cf6)' },
  { path: '/profile',   label: '学习画像', icon: '📊', color: 'linear-gradient(135deg,#8b5cf6,#ec4899)' },
  { path: '/diagnosis', label: '诊断面板', icon: '🔍', color: 'linear-gradient(135deg,#ef4444,#f97316)' },
]
function goFab(path: string) {
  router.push(path)
  fabOpen.value = false
}

onMounted(() => {
  authStore.restoreToken()
  checkMobile()
  window.addEventListener('resize', checkMobile)
  window.addEventListener('keydown', handleKeydown)
  // 自动展开当前路由对应的分组
  expandActiveGroup()
  // 首次登录弹出引导
  if (authStore.isLoggedIn && authStore.user?.isFirstLogin === 1) {
    showOnboarding.value = true
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
  window.removeEventListener('keydown', handleKeydown)
})
</script>

<template>
  <!-- 登录页：无徧边栏 / 顶栏，直接渲染路由视图 -->
  <router-view v-if="isLoginPage" />

  <!-- 主应用布局 -->
  <div v-else class="app-layout">
    <!-- 移动端遮罩 -->
    <div
      v-if="isMobile && sidebarOpen"
      class="sidebar-overlay"
      @click="closeSidebar"
    />

    <!-- 侧边栏 -->
    <aside
      class="sidebar"
      :class="{
        collapsed: isCollapsed && !isMobile,
        'mobile-open': isMobile && sidebarOpen,
        'mobile-hidden': isMobile && !sidebarOpen,
      }"
    >
      <!-- Logo区域 -->
      <div class="sidebar-header">
        <div class="logo">
          <div class="logo-icon">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
              <path d="M12 2L2 7l10 5 10-5-10-5z" fill="rgba(255,255,255,0.9)"/>
              <path d="M2 17l10 5 10-5" stroke="rgba(255,255,255,0.7)" stroke-width="2" stroke-linecap="round"/>
              <path d="M2 12l10 5 10-5" stroke="rgba(255,255,255,0.85)" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </div>
          <div v-if="!isCollapsed || isMobile" class="logo-text-group">
            <span class="logo-text">Socrates Cube</span>
            <span class="logo-sub">AI 学习系统</span>
          </div>
        </div>
        <button
          v-if="!isMobile"
          class="collapse-btn"
          @click="isCollapsed = !isCollapsed"
          :title="isCollapsed ? '展开菜单' : '收起菜单'"
        >
          <el-icon size="16"><component :is="isCollapsed ? 'Expand' : 'Fold'" /></el-icon>
        </button>
        <button
          v-else
          class="collapse-btn"
          @click="closeSidebar"
        >
          <el-icon size="16"><Close /></el-icon>
        </button>
      </div>

      <!-- 导航菜单 -->
      <nav class="sidebar-nav">
        <template v-for="(group, gIdx) in menuGroups" :key="gIdx">
          <!-- standalone 菜单项直接渲染 -->
          <template v-if="group.type === 'standalone'">
            <router-link
              v-for="item in group.items"
              :key="item.path"
              :to="item.path"
              class="nav-item"
              :class="{ active: activePath === item.path }"
              @click="isMobile && closeSidebar()"
            >
              <div class="nav-icon-wrap">
                <el-icon size="18"><component :is="item.icon" /></el-icon>
              </div>
              <span v-if="!isCollapsed || isMobile" class="nav-label">{{ item.label }}</span>
              <div v-if="activePath === item.path && (!isCollapsed || isMobile)" class="nav-active-dot" />
            </router-link>
          </template>

          <!-- group 类型：可折叠分组 -->
          <template v-if="group.type === 'group'">
            <!-- 分组标题（可点击展开/折叠） -->
            <div
              v-if="!isCollapsed || isMobile"
              class="menu-group-title"
              @click="toggleGroup(gIdx)"
            >
              <div class="nav-icon-wrap">
                <el-icon size="18"><component :is="group.icon" /></el-icon>
              </div>
              <span class="group-title-text">{{ group.title }}</span>
              <span class="group-arrow" :class="{ expanded: expandedGroups[gIdx] }">
                <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                  <path d="M4.5 2.5L8 6L4.5 9.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </span>
            </div>
            <!-- 折叠态分组间距 -->
            <div v-if="isCollapsed && !isMobile" class="menu-group-spacer" />
            <!-- 子菜单项容器（带折叠动画） -->
            <div class="group-items" :class="{ collapsed: !expandedGroups[gIdx] && (!isCollapsed || isMobile) }">
              <router-link
                v-for="item in group.items"
                :key="item.path"
                :to="item.path"
                class="nav-item"
                :class="{ active: activePath === item.path }"
                @click="isMobile && closeSidebar()"
              >
                <div class="nav-icon-wrap">
                  <el-icon size="18"><component :is="item.icon" /></el-icon>
                </div>
                <span v-if="!isCollapsed || isMobile" class="nav-label">{{ item.label }}</span>
                <div v-if="activePath === item.path && (!isCollapsed || isMobile)" class="nav-active-dot" />
              </router-link>
            </div>
          </template>
        </template>
      </nav>

      <!-- Agent日志：独立固定在底部，不参与 nav 滚动区域 -->
      <router-link
        to="/manual"
        class="nav-item sidebar-log-item"
        :class="{ active: activePath === '/manual' }"
        @click="isMobile && closeSidebar()"
      >
        <div class="nav-icon-wrap">
          <el-icon size="18"><QuestionFilled /></el-icon>
        </div>
        <span v-if="!isCollapsed || isMobile" class="nav-label">使用手册</span>
        <div v-if="activePath === '/manual' && (!isCollapsed || isMobile)" class="nav-active-dot" />
      </router-link>

      <!-- 管理后台（仅 admin 见） -->
      <router-link
        v-if="authStore.user?.roleType === 'admin'"
        to="/admin"
        class="nav-item sidebar-log-item"
        :class="{ active: activePath === '/admin' }"
        @click="isMobile && closeSidebar()"
      >
        <div class="nav-icon-wrap">
          <el-icon size="18"><Setting /></el-icon>
        </div>
        <span v-if="!isCollapsed || isMobile" class="nav-label">管理后台</span>
        <div v-if="activePath === '/admin' && (!isCollapsed || isMobile)" class="nav-active-dot" />
      </router-link>

      <router-link
        to="/logs"
        class="nav-item sidebar-log-item"
        :class="{ active: activePath === logMenuItem.path }"
        @click="isMobile && closeSidebar()"
      >
        <div class="nav-icon-wrap">
          <el-icon size="18"><component :is="logMenuItem.icon" /></el-icon>
        </div>
        <span v-if="!isCollapsed || isMobile" class="nav-label">{{ logMenuItem.label }}</span>
        <div v-if="activePath === logMenuItem.path && (!isCollapsed || isMobile)" class="nav-active-dot" />
      </router-link>

      <!-- 底部版本信息 -->
      <div v-if="!isCollapsed || isMobile" class="sidebar-footer">
        <div class="sidebar-footer-inner">
          <span class="footer-badge">AI 学习系统</span>
          <span class="footer-version">v1.0.0</span>
        </div>
      </div>
    </aside>

    <!-- 主内容区 -->
    <main class="main-content">
      <!-- 顶部导航栏 -->
      <header class="top-bar">
        <div class="top-bar-left">
          <button
            v-if="isMobile"
            class="mobile-menu-btn"
            @click="toggleSidebar"
          >
            <el-icon size="20"><Menu /></el-icon>
          </button>
          <div class="page-title-wrap">
            <h2 class="page-title">{{ route.meta?.title || '系统首页' }}</h2>
          </div>
          <el-tag v-if="userStore.demoMode" size="small" type="warning" class="demo-badge">
            演示模式
          </el-tag>
        </div>
        <div class="user-info" @click="router.push('/profile')" title="查看我的画像">
          <div class="user-avatar">
            <el-icon size="16" color="#3b82f6"><UserFilled /></el-icon>
          </div>
          <span class="username">{{ authStore.user?.username || userStore.username }}</span>
          <el-icon size="12" color="#94a3b8"><ArrowRight /></el-icon>
        </div>
      </header>

      <!-- 页面内容 -->
      <div class="page-content" :class="{ 'demo-mode': userStore.demoMode }">
        <router-view v-slot="{ Component }">
          <transition name="fade-slide" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </div>
    </main>

    <!-- ⚡ 悬浮快捷入口 -->
    <div class="fab-wrap">
      <div class="fab-menu" :class="{ open: fabOpen }">
        <button
          v-for="item in fabItems"
          :key="item.path"
          class="fab-item"
          :style="{ background: item.color }"
          :title="item.label"
          @click="goFab(item.path)"
        >
          <span class="fab-item-icon">{{ item.icon }}</span>
          <span class="fab-item-label">{{ item.label }}</span>
        </button>
      </div>
      <button
        class="fab-main"
        :class="{ open: fabOpen }"
        @click="fabOpen = !fabOpen"
        title="快捷入口"
      >
        <el-icon size="22"><component :is="fabOpen ? 'Close' : 'Grid'" /></el-icon>
      </button>
    </div>
  </div>

  <!-- 首次登录引导弹窗（全局浮层） -->
  <OnboardingGuide v-if="showOnboarding" @done="handleOnboardingDone" />
  <RoleSelector v-if="showRoleSelector" @done="handleRoleDone" />
</template>

<style scoped>
/* ============================================
   整体布局
   ============================================ */
.app-layout {
  display: flex;
  height: 100vh;
  background-color: #f8faff;
  overflow: hidden;
}

/* ============================================
   侧边栏 — 蓝紫渐变
   ============================================ */
.sidebar {
  width: 232px;
  background: linear-gradient(180deg, #1e40af 0%, #3730a3 50%, #4c1d95 100%);
  color: #fff;
  display: flex;
  flex-direction: column;
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  flex-shrink: 0;
  box-shadow: 4px 0 20px rgba(59, 130, 246, 0.15);
  z-index: 20;
  position: relative;
}

/* 侧边栏装饰光效 */
.sidebar::before {
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  width: 1px;
  height: 100%;
  background: linear-gradient(180deg,
    transparent 0%,
    rgba(255,255,255,0.15) 30%,
    rgba(255,255,255,0.1) 70%,
    transparent 100%
  );
}

.sidebar.collapsed {
  width: 68px;
}

/* ============================================
   Logo 区域
   ============================================ */
.sidebar-header {
  padding: 18px 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  flex-shrink: 0;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  overflow: hidden;
  flex: 1;
}

.logo-icon {
  width: 36px;
  height: 36px;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  border: 1px solid rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(8px);
}

.logo-text-group {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.logo-text {
  font-size: 15px;
  font-weight: 700;
  color: #fff;
  white-space: nowrap;
  letter-spacing: -0.3px;
  line-height: 1.2;
}

.logo-sub {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.6);
  white-space: nowrap;
  letter-spacing: 0.5px;
  margin-top: 1px;
}

.collapse-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: rgba(255, 255, 255, 0.5);
  padding: 6px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  flex-shrink: 0;
}

.collapse-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

/* ============================================
   导航菜单
   ============================================ */
.sidebar-nav {
  flex: 1;
  min-height: 0;
  padding: 10px 8px;
  display: flex;
  flex-direction: column;
  gap: 0;
  overflow-y: auto;
  overflow-x: hidden;
}

.sidebar-nav::-webkit-scrollbar {
  width: 4px;
}
.sidebar-nav::-webkit-scrollbar-track {
  background: transparent;
}
.sidebar-nav::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 2px;
}
.sidebar-nav::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.35);
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 10px;
  color: rgba(255, 255, 255, 0.65);
  text-decoration: none;
  transition: all 0.2s;
  white-space: nowrap;
  position: relative;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.nav-item.active {
  background: rgba(255, 255, 255, 0.18);
  color: #fff;
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.12),
              0 2px 8px rgba(0,0,0,0.15);
}

.nav-icon-wrap {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  flex-shrink: 0;
  transition: background 0.2s;
}

.nav-item.active .nav-icon-wrap {
  background: rgba(255, 255, 255, 0.15);
}

.nav-label {
  font-size: 13.5px;
  font-weight: 500;
  flex: 1;
}

.nav-active-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #fff;
  opacity: 0.8;
  flex-shrink: 0;
}

/* 分组标题 */
.menu-group-title {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 10px;
  color: rgba(255, 255, 255, 0.65);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  user-select: none;
  transition: all 0.2s;
  margin-top: 0;
  position: relative;
  z-index: 1;
}
.menu-group-title:hover {
  color: rgba(255, 255, 255, 0.9);
  background: rgba(255, 255, 255, 0.06);
}
.group-title-text {
  flex: 1;
}
.group-arrow {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  color: rgba(255, 255, 255, 0.4);
  transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}
.group-arrow.expanded {
  transform: rotate(90deg);
}
.group-items .nav-item {
  padding-left: 22px;
}
.group-items {
  overflow: hidden;
  max-height: 500px;
  transition: max-height 0.35s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  z-index: 0;
}
.group-items.collapsed {
  max-height: 0;
}

/* Agent日志：固定在底部，独立于滚动区域 */
.sidebar-log-item {
  flex-shrink: 0;
  margin: 0 8px 4px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  padding-top: 6px;
}

/* 折叠态分组分隔 */
.menu-group-spacer {
  height: 1px;
  margin: 8px 12px;
  background: rgba(255, 255, 255, 0.08);
}

/* ============================================
   侧边栏底部
   ============================================ */
.sidebar-footer {
  padding: 12px 14px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  flex-shrink: 0;
}

.sidebar-footer-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.footer-badge {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.6);
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  padding: 2px 7px;
  font-weight: 500;
  letter-spacing: 0.3px;
}

.footer-version {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.4);
  font-family: monospace;
}

/* ============================================
   主内容区
   ============================================ */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}

/* ============================================
   顶部导航栏
   ============================================ */
.top-bar {
  height: 58px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid #e8eef8;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  flex-shrink: 0;
  z-index: 10;
  box-shadow: 0 1px 4px rgba(59, 130, 246, 0.06);
}

.top-bar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-title-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
}

.page-title {
  font-size: 17px;
  font-weight: 600;
  color: #1e293b;
  letter-spacing: -0.3px;
}

.mobile-menu-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: #64748b;
  padding: 6px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.mobile-menu-btn:hover {
  background: #f1f5f9;
  color: #1e293b;
}

.demo-badge {
  font-size: 11px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  border-radius: 20px;
  background: #f0f4ff;
  border: 1px solid #dbeafe;
  cursor: pointer;
  transition: all 0.2s;
}

.user-info:hover {
  background: #dbeafe;
}

.user-avatar {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: #bfdbfe;
  display: flex;
  align-items: center;
  justify-content: center;
}

.username {
  font-size: 13px;
  color: #3b82f6;
  font-weight: 600;
}

/* ============================================
   页面内容区
   ============================================ */
.page-content {
  flex: 1;
  overflow: auto;
  padding: 24px;
  background: #f8faff;
}

.demo-mode {
  font-size: 15px;
}

/* ============================================
   页面过渡动画
   ============================================ */
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: opacity 0.22s ease, transform 0.22s ease;
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateY(6px);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

/* ============================================
   移动端遮罩
   ============================================ */
.sidebar-overlay {
  position: fixed;
  inset: 0;
  background-color: rgba(15, 23, 42, 0.45);
  z-index: 99;
  backdrop-filter: blur(2px);
}

/* ============================================
   响应式
   ============================================ */
@media (max-width: 1280px) {
  .sidebar { width: 200px; }
  .page-content { padding: 18px; }
}

@media (max-width: 767px) {
  .sidebar {
    position: fixed;
    left: 0;
    top: 0;
    bottom: 0;
    z-index: 100;
    width: 220px !important;
    transition: transform 0.3s ease;
  }

  .sidebar.mobile-hidden {
    transform: translateX(-100%);
  }

  .sidebar.mobile-open {
    transform: translateX(0);
  }

  .page-content { padding: 16px; }
  .top-bar { padding: 0 16px; }
}

/* ============================================
   悬浮快捷入口 FAB
   ============================================ */
.fab-wrap {
  position: fixed;
  bottom: 28px;
  right: 28px;
  z-index: 200;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
}

.fab-menu {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
  pointer-events: none;
  opacity: 0;
  transform: translateY(12px);
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.fab-menu.open {
  pointer-events: auto;
  opacity: 1;
  transform: translateY(0);
}

.fab-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px 8px 12px;
  border: none;
  border-radius: 20px;
  cursor: pointer;
  color: white;
  font-size: 13px;
  font-weight: 600;
  box-shadow: 0 4px 16px rgba(0,0,0,0.18);
  transition: all 0.2s;
  white-space: nowrap;
}

.fab-item:hover {
  transform: translateX(-4px) scale(1.04);
  box-shadow: 0 6px 20px rgba(0,0,0,0.25);
}

.fab-item-icon { font-size: 16px; }
.fab-item-label { font-size: 12px; }

.fab-main {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  border: none;
  background: linear-gradient(135deg, #3b82f6 0%, #6366f1 50%, #8b5cf6 100%);
  color: white;
  cursor: pointer;
  box-shadow: 0 4px 20px rgba(99,102,241,0.45), 0 2px 8px rgba(0,0,0,0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.fab-main::before {
  content: '';
  position: absolute;
  inset: -2px;
  border-radius: 50%;
  background: linear-gradient(135deg, #3b82f6, #8b5cf6, #ec4899, #3b82f6);
  background-size: 300% 300%;
  animation: fabGradient 3s linear infinite;
  z-index: -1;
  opacity: 0.6;
}

@keyframes fabGradient {
  0%   { background-position: 0% 50%; }
  50%  { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

.fab-main:hover {
  transform: scale(1.1);
  box-shadow: 0 6px 28px rgba(99,102,241,0.6);
}

.fab-main.open {
  background: linear-gradient(135deg, #ef4444, #f97316);
  box-shadow: 0 4px 20px rgba(239,68,68,0.4);
}

@media (max-width: 640px) {
  .fab-wrap { bottom: 20px; right: 16px; }
  .fab-item-label { display: none; }
  .fab-item { padding: 10px; border-radius: 50%; }
}
</style>
