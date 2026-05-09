<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const isCollapsed = ref(false)
const isMobile = ref(false)
const sidebarOpen = ref(false)

const menuItems = [
  { path: '/', label: '系统首页', icon: 'HomeFilled' },
  { path: '/chat', label: '智能对话', icon: 'ChatRound' },
  { path: '/challenger', label: '概念挑战', icon: 'WarningFilled' },
  { path: '/profile', label: '能力画像', icon: 'UserFilled' },
  { path: '/simulator', label: '协议仿真', icon: 'VideoPlay' },
  { path: '/diagnosis', label: '诊断面板', icon: 'FirstAidKit' },
  { path: '/resources', label: '学习资源', icon: 'Collection' },
  { path: '/path', label: '学习路径', icon: 'MapLocation' },
  { path: '/logs', label: 'Agent日志', icon: 'List' },
]

const activePath = computed(() => route.path)

function checkMobile() {
  isMobile.value = window.innerWidth < 768
  if (!isMobile.value) {
    sidebarOpen.value = false
  }
}

function toggleSidebar() {
  sidebarOpen.value = !sidebarOpen.value
}

function closeSidebar() {
  sidebarOpen.value = false
}

onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
})
</script>

<template>
  <div class="app-layout">
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
      <div class="sidebar-header">
        <div class="logo">
          <el-icon size="28" color="#fff"><ElementPlus /></el-icon>
          <span v-if="!isCollapsed || isMobile" class="logo-text">Socrates Cube</span>
        </div>
        <el-button
          v-if="!isMobile"
          class="collapse-btn"
          text
          :icon="isCollapsed ? 'Expand' : 'Fold'"
          @click="isCollapsed = !isCollapsed"
        />
        <el-button
          v-else
          class="collapse-btn"
          text
          icon="Close"
          @click="closeSidebar"
        />
      </div>

      <nav class="sidebar-nav">
        <router-link
          v-for="item in menuItems"
          :key="item.path"
          :to="item.path"
          class="nav-item"
          :class="{ active: activePath === item.path }"
          @click="isMobile && closeSidebar()"
        >
          <el-icon size="20"><component :is="item.icon" /></el-icon>
          <span v-if="!isCollapsed || isMobile" class="nav-label">{{ item.label }}</span>
        </router-link>
      </nav>
    </aside>

    <!-- 主内容区 -->
    <main class="main-content">
      <header class="top-bar">
        <div class="top-bar-left">
          <el-button
            v-if="isMobile"
            class="mobile-menu-btn"
            text
            icon="Menu"
            @click="toggleSidebar"
          />
          <h2 class="page-title">{{ route.meta?.title || '系统首页' }}</h2>
        </div>
        <div class="user-info">
          <el-avatar :size="32" icon="UserFilled" />
          <span class="username">学生用户</span>
        </div>
      </header>
      <div class="page-content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </div>
    </main>
  </div>
</template>

<style scoped>
.app-layout {
  display: flex;
  height: 100vh;
  background-color: #f8fafc;
}

.sidebar {
  width: 240px;
  background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
  color: #fff;
  display: flex;
  flex-direction: column;
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  flex-shrink: 0;
  box-shadow: 4px 0 24px rgba(0,0,0,0.05);
  z-index: 20;
}

.sidebar.collapsed {
  width: 72px;
}

.sidebar-header {
  padding: 20px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid rgba(255,255,255,0.05);
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  overflow: hidden;
}

.logo-text {
  font-size: 17px;
  font-weight: 700;
  white-space: nowrap;
  color: #fff;
  letter-spacing: -0.5px;
}

.collapse-btn {
  color: #94a3b8;
  padding: 4px;
}

.collapse-btn:hover {
  color: #fff;
}

.sidebar-nav {
  flex: 1;
  padding: 12px 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 8px;
  color: #94a3b8;
  text-decoration: none;
  transition: all 0.2s;
  white-space: nowrap;
}

.nav-item:hover {
  background-color: #334155;
  color: #fff;
}

.nav-item.active {
  background-color: #2563eb;
  color: #fff;
}

.nav-label {
  font-size: 14px;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background-color: #f1f5f9; /* 稍微深一点的背景色衬托白卡片 */
}

.top-bar {
  height: 60px;
  background-color: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(226, 232, 240, 0.8);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  flex-shrink: 0;
  z-index: 10;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  color: #0f172a;
  letter-spacing: -0.5px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.username {
  font-size: 14px;
  color: #475569;
}

.top-bar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.mobile-menu-btn {
  color: #475569;
  padding: 4px;
}

.sidebar-overlay {
  position: fixed;
  inset: 0;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: 99;
}

/* 页面过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 移动端适配 */
@media (max-width: 767px) {
  .sidebar {
    position: fixed;
    left: 0;
    top: 0;
    bottom: 0;
    z-index: 100;
    width: 220px;
    transition: transform 0.3s ease;
  }

  .sidebar.mobile-hidden {
    transform: translateX(-100%);
  }

  .sidebar.mobile-open {
    transform: translateX(0);
  }

  .page-content {
    padding: 16px;
  }

  .top-bar {
    padding: 0 16px;
  }
}

.page-content {
  flex: 1;
  overflow: auto;
  padding: 24px;
}
</style>
