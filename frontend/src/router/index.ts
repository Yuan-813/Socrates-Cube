import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  // ── 公开路由（无需登录）──────────────────────────────────────────
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginViewScheme2.vue'),
    meta: { title: '登录 / 注册', public: true },
  },
  {
    path: '/auth/:provider/callback',
    name: 'OAuthCallback',
    component: () => import('@/views/OAuthCallbackView.vue'),
    meta: { title: 'OAuth 登录中', public: true },
  },
  {
    path: '/onboarding',
    name: 'Onboarding',
    component: () => import('@/views/OnboardingScheme1.vue'),
    meta: { title: 'AI引导初始化', skipOnboarding: true, public: true },
  },
  {
    path: '/welcome',
    name: 'Welcome',
    component: () => import('@/views/WelcomeView.vue'),
    meta: { title: '欢迎指南', skipOnboarding: true },
  },
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/HomeView.vue'),
    meta: { title: '系统首页' },
  },
  {
    path: '/chat',
    name: 'Chat',
    component: () => import('@/views/ChatViewScheme1.vue'),
    meta: { title: '智能对话' },
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/views/ProfileView.vue'),
    meta: { title: '能力画像' },
  },
  {
    path: '/simulator',
    name: 'Simulator',
    component: () => import('@/views/SimulatorViewScheme3.vue'),
    meta: { title: '协议仿真' },
  },
  {
    path: '/diagnosis',
    name: 'Diagnosis',
    component: () => import('@/views/DiagnosisViewScheme1.vue'),
    meta: { title: '诊断面板' },
  },
  {
    path: '/resources',
    name: 'Resources',
    component: () => import('@/views/ResourcesViewScheme1.vue'),
    meta: { title: '学习资源' },
  },
  {
    path: '/path',
    name: 'Path',
    component: () => import('@/views/PathViewScheme1.vue'),
    meta: { title: '学习路径' },
  },
  {
    path: '/logs',
    name: 'Logs',
    component: () => import('@/views/LogsView.vue'),
    meta: { title: 'Agent日志' },
  },
  {
    path: '/challenger',
    name: 'Challenger',
    component: () => import('@/views/ChallengerView.vue'),
    meta: { title: '概念挑战' },
  },
  {
    path: '/challenger/scheme3',
    name: 'ChallengerScheme3',
    component: () => import('@/views/ChallengerViewScheme3.vue'),
    meta: { title: '概念挑战 方案三' },
  },
  {
    path: '/career',
    name: 'Career',
    component: () => import('@/views/CareerView.vue'),
    meta: { title: '职业导航' },
  },
  {
    path: '/exam',
    name: 'Exam',
    component: () => import('@/views/ExamView.vue'),
    meta: { title: '证书模拟考试' },
  },
  {
    path: '/interview',
    name: 'Interview',
    component: () => import('@/views/InterviewView.vue'),
    meta: { title: 'AI面试模拟' },
  },
  {
    path: '/bookshelf',
    name: 'Bookshelf',
    component: () => import('@/views/BookshelfView.vue'),
    meta: { title: 'PDF智能知识库' },
  },
  {
    path: '/scenario',
    name: 'Scenario',
    component: () => import('@/views/ScenarioView.vue'),
    meta: { title: '情景化角色对话' },
  },
  {
    path: '/device3d',
    name: 'Device3D',
    component: () => import('@/views/Hardware3DViewScheme2.vue'),
    meta: { title: '3D 硬件全息可视化实验室' },
  },
  {
    path: '/hardware3d',
    name: 'Hardware3D',
    component: () => import('@/views/Hardware3DViewScheme2.vue'),
    meta: { title: '3D 硬件全息可视化实验室' },
  },
  {
    path: '/lesson',
    name: 'Lesson',
    component: () => import('@/views/LessonView.vue'),
    meta: { title: '互动课堂' },
  },
  {
    path: '/bookhouse',
    name: 'BookHouse',
    component: () => import('@/views/BookHouseScheme3.vue'),
    meta: { title: '教材书库' },
  },
  {
    path: '/bookhouse/:id/read',
    name: 'BookReader',
    component: () => import('@/views/BookReaderView.vue'),
    meta: { title: '阅读原文' },
  },
  {
    path: '/video-gen',
    name: 'VideoGen',
    component: () => import('@/views/VideoGenView.vue'),
    meta: { title: 'AI视频生成' },
  },
  {
    path: '/kg-assist',
    name: 'AIKGAssist',
    component: () => import('@/views/AIKGView.vue'),
    meta: { title: 'AI图谱助手' },
  },
  // ── 新增功能页面 ────────────────────────────────────────
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/DashboardView.vue'),
    meta: { title: '学习数据统计' },
  },
  {
    path: '/admin',
    name: 'Admin',
    component: () => import('@/views/AdminView.vue'),
    meta: { title: '管理后台', requireAdmin: true },
  },
  {
    path: '/manual',
    name: 'Manual',
    component: () => import('@/views/UserManualView.vue'),
    meta: { title: '使用手册', skipOnboarding: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

/**
 * 路由守卫：双层拦截
 *  1. 未登录 → /login
 *  2. 已登录但未完成 AI 引导 → /onboarding
 */
router.beforeEach((to) => {
  // 公开路由直接放行
  if (to.meta.public || to.path === '/login') return true

  // 从 pinia-plugin-persistedstate 的 localStorage 读取 auth 状态
  let isLoggedIn = false
  let userId = 'student-001'
  try {
    const raw = localStorage.getItem('auth')
    if (raw) {
      const parsed = JSON.parse(raw)
      isLoggedIn = !!(parsed.token && parsed.user)
      userId = parsed.user?.userId || userId
    }
  } catch { /* ignore */ }

  // 未登录 → 跳转到登录页
  if (!isLoggedIn) {
    return { path: '/login' }
  }

  // 管理员专属页面权限检查
  if (to.meta.requireAdmin) {
    let roleType = 'student'
    try {
      const raw = localStorage.getItem('auth')
      if (raw) {
        const parsed = JSON.parse(raw)
        roleType = parsed.user?.roleType || 'student'
      }
    } catch { /* ignore */ }
    if (roleType !== 'admin') {
      return { path: '/' }
    }
  }

  // 已登录但尚未完成 AI 画像引导 → 引导页
  // skipOnboarding 标记的路由（如 /onboarding 本身）跳过此检查
  if (!to.meta.skipOnboarding) {
    const onboarded = localStorage.getItem(`onboarded_${userId}`)
      || localStorage.getItem('onboarding_done')  // 兼容旧 key
    if (!onboarded && to.path !== '/onboarding') {
      return { path: '/onboarding' }
    }
  }

  return true
})

export default router
