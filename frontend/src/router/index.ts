import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/HomeView.vue'),
    meta: { title: '系统首页' },
  },
  {
    path: '/chat',
    name: 'Chat',
    component: () => import('@/views/ChatView.vue'),
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
    component: () => import('@/views/SimulatorView.vue'),
    meta: { title: '协议仿真' },
  },
  {
    path: '/diagnosis',
    name: 'Diagnosis',
    component: () => import('@/views/DiagnosisView.vue'),
    meta: { title: '诊断面板' },
  },
  {
    path: '/resources',
    name: 'Resources',
    component: () => import('@/views/ResourcesView.vue'),
    meta: { title: '学习资源' },
  },
  {
    path: '/path',
    name: 'Path',
    component: () => import('@/views/PathView.vue'),
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
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
