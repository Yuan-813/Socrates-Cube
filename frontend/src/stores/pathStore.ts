import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { LearningPath, PathNode, PathNodeStatus } from '../types'
import { pathApi } from '../api/path'

export const usePathStore = defineStore('path', () => {
  const path = ref<LearningPath | null>(null)
  const selectedNode = ref<PathNode | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const completedCount = computed(() =>
    path.value?.nodes.filter(n => n.status === 'completed').length ?? 0,
  )

  const totalCount = computed(() => path.value?.nodes.length ?? 0)

  const progressPercent = computed(() =>
    totalCount.value > 0
      ? Math.round((completedCount.value / totalCount.value) * 100)
      : 0,
  )

  async function fetchPath(userId: string) {
    loading.value = true
    error.value = null
    try {
      path.value = await pathApi.getUserPath(userId)
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : '路径加载失败'
    } finally {
      loading.value = false
    }
  }

  /** 从 SSE path_update 事件直接更新路径 */
  function updateFromSSE(newPath: LearningPath) {
    path.value = newPath
  }

  async function markNodeCompleted(userId: string, nodeId: string, mastery = 0.9) {
    if (!path.value) return
    const node = path.value.nodes.find(n => n.node_id === nodeId)
    if (!node) return

    node.status = 'completed' as PathNodeStatus
    node.current_mastery = mastery

    // 解锁依赖于此节点的后续节点
    path.value.nodes.forEach(n => {
      if (n.status === 'locked' && n.prerequisites.every(pid => {
        const prereqNode = path.value!.nodes.find(x => x.node_id === pid)
        return !prereqNode || prereqNode.status === 'completed'
      })) {
        n.status = 'pending'
        n.prerequisites_met = true
      }
    })

    try {
      await pathApi.updateProgress(userId, nodeId, 'completed', mastery)
    } catch {
      // 乐观更新，API 失败不回滚
    }
  }

  function selectNode(node: PathNode | null) {
    selectedNode.value = node
  }

  return {
    path,
    selectedNode,
    loading,
    error,
    completedCount,
    totalCount,
    progressPercent,
    fetchPath,
    updateFromSSE,
    markNodeCompleted,
    selectNode,
  }
})
