<script setup lang="ts">
import { computed, ref } from 'vue'
import type { LearningResource } from '@/types'

const resources = ref<LearningResource[]>([
  {
    resource_id: 'res-001',
    title: 'TCP vs UDP 决策指南',
    resource_type: 'doc',
    content: '对比 TCP 和 UDP 的适用场景、可靠性、时延与实现成本。',
    difficulty: 2,
    tags: ['协议对比', '传输层'],
  },
  {
    resource_id: 'res-002',
    title: 'TCP 三次握手练习',
    resource_type: 'exercise',
    content: '围绕 SYN、SYN-ACK、ACK 的作用设计判断题和追问题。',
    difficulty: 3,
    tags: ['练习题', '连接管理'],
  },
  {
    resource_id: 'res-003',
    title: 'Socket 编程示例',
    resource_type: 'code',
    content: '使用 Python Socket 演示 TCP 客户端与服务端通信。',
    difficulty: 3,
    tags: ['代码', 'Socket'],
  },
])

const filterType = ref('')

const typeLabels: Record<string, string> = {
  doc: '讲解文档',
  exercise: '练习题',
  code: '代码案例',
  document: '讲解文档',
  quiz: '练习题',
}

const typeColors: Record<string, string> = {
  doc: '#3b82f6',
  exercise: '#f59e0b',
  code: '#10b981',
  document: '#3b82f6',
  quiz: '#f59e0b',
}

function resourceType(res: LearningResource): string {
  return res.resource_type || res.type || 'doc'
}

function resourceId(res: LearningResource): string {
  return res.resource_id || res.id || res.title
}

const filteredResources = computed(() => {
  if (!filterType.value) return resources.value
  return resources.value.filter(res => resourceType(res) === filterType.value)
})
</script>

<template>
  <div>
    <div class="mb-4 flex flex-wrap items-center justify-between gap-3">
      <el-radio-group v-model="filterType" size="small">
        <el-radio-button value="">全部</el-radio-button>
        <el-radio-button value="doc">文档</el-radio-button>
        <el-radio-button value="exercise">练习</el-radio-button>
        <el-radio-button value="code">代码</el-radio-button>
      </el-radio-group>
      <span class="text-xs text-gray-400">共 {{ filteredResources.length }} 个资源</span>
    </div>

    <div class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
      <article
        v-for="res in filteredResources"
        :key="resourceId(res)"
        class="flex flex-col gap-3 rounded-lg border border-gray-200 bg-white p-5 transition hover:border-gray-300 hover:shadow-sm"
      >
        <div class="flex items-center gap-3">
          <div
            class="flex h-10 w-10 items-center justify-center rounded-lg text-sm font-bold text-white"
            :style="{ backgroundColor: typeColors[resourceType(res)] || '#64748b' }"
          >
            {{ (typeLabels[resourceType(res)] || '资源').slice(0, 1) }}
          </div>
          <div>
            <div class="text-xs font-medium" :style="{ color: typeColors[resourceType(res)] || '#64748b' }">
              {{ typeLabels[resourceType(res)] || resourceType(res) }}
            </div>
            <div class="text-xs text-gray-400">难度 {{ res.difficulty ?? res.metadata?.difficulty ?? 3 }}/5</div>
          </div>
        </div>

        <h4 class="text-sm font-semibold text-gray-900">{{ res.title }}</h4>
        <p class="line-clamp-4 flex-1 text-sm leading-6 text-gray-600">{{ res.content }}</p>

        <div v-if="res.tags?.length" class="flex flex-wrap gap-2">
          <el-tag v-for="tag in res.tags" :key="tag" size="small" type="info">{{ tag }}</el-tag>
        </div>
      </article>
    </div>
  </div>
</template>
