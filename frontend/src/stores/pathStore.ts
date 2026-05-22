import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { pathApi } from '@/api/path'
import type { LearningPath, PathNode } from '@/types/path'

export const usePathStore = defineStore('path', () => {
  const path = ref<LearningPath | null>(null)
  const selectedNode = ref<PathNode | null>(null)

  const completedCount = computed(() =>
    path.value?.nodes.filter(n => n.status === 'completed').length ?? 0
  )

  const currentNode = computed(() =>
    path.value?.nodes.find(n => n.status === 'current') || null
  )

  async function fetchPath(userId: string) {
    try {
      const res = await pathApi.getUserPath(userId)
      path.value = res.data
    } catch (e) {
      console.warn('学习路径获取失败')
    }
  }

  function updateFromSSE(pathData: LearningPath) {
    path.value = pathData
  }

  function selectNode(node: PathNode) {
    selectedNode.value = node
  }

  return { path, selectedNode, completedCount, currentNode, fetchPath, updateFromSSE, selectNode }
})
