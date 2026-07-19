<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

const schemes = [
  {
    id: 's1',
    label: '方案一',
    desc: '明亮 AI 知识星图',
    icon: '☀️',
    route: '/path-s1',
    badge: '明亮玻璃',
    color: 'from-blue-500 to-indigo-500',
    preview: '浅蓝白背景 · 知识图谱 + Alice AI解释 · 资源推荐',
  },
  {
    id: 's2',
    label: '方案二',
    desc: '赛博全息星轨',
    icon: '🌌',
    route: '/path-s2',
    badge: '暗黑科幻',
    color: 'from-cyan-500 to-blue-600',
    preview: '深空背景 · S形星轨路径 · 发光节点 · 呼吸动效',
  },
  {
    id: 's3',
    label: '方案三',
    desc: '深海蓝融合方案',
    icon: '🔮',
    route: '/path-s3',
    badge: '融合推荐',
    color: 'from-purple-500 to-cyan-500',
    preview: '玻璃拟态 · 知识星图 + 侧板详情 · 流动粒子动效',
  },
]
</script>

<template>
  <div class="space-y-6">
    <!-- 方案选择中心 -->
    <div class="card">
      <h2 class="section-title">学习路径 · 三大视觉方案</h2>
      <p class="section-desc mt-1">选择你偏好的视觉风格，点击进入对应方案体验</p>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mt-5">
        <button
          v-for="s in schemes"
          :key="s.id"
          class="group relative overflow-hidden rounded-2xl border p-5 text-left transition-all hover:-translate-y-1 hover:shadow-lg"
          :class="s.id === 's3' ? 'border-purple-200 bg-purple-50/50 hover:border-purple-400' : 'border-gray-100 bg-white hover:border-blue-200'"
          @click="router.push(s.route)"
        >
          <!-- Badge -->
          <span class="absolute right-3 top-3 rounded-full px-2 py-0.5 text-[10px] font-semibold text-white bg-gradient-to-r"
            :class="s.color">
            {{ s.badge }}
          </span>

          <!-- Icon -->
          <div class="text-4xl mb-3">{{ s.icon }}</div>

          <!-- Title -->
          <h3 class="font-bold text-gray-900 text-base">{{ s.label }}</h3>
          <p class="text-sm font-medium mt-0.5" :class="s.id === 's3' ? 'text-purple-600' : 'text-blue-600'">
            {{ s.desc }}
          </p>
          <p class="text-xs text-gray-400 mt-2 leading-5">{{ s.preview }}</p>

          <!-- 进入箭头 -->
          <div class="mt-4 flex items-center text-xs font-semibold gap-1"
            :class="s.id === 's3' ? 'text-purple-500' : 'text-blue-500'">
            点击进入 <span class="group-hover:translate-x-1 transition-transform inline-block">→</span>
          </div>
        </button>
      </div>
    </div>
  </div>
</template>
