import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { LearningResource, ResourceType } from '../types'
import { resourcesApi } from '../api/resources'

export const useResourceStore = defineStore('resource', () => {
  const resources = ref<LearningResource[]>([])
  const activeTab = ref<ResourceType>('doc')
  const loading = ref(false)
  const error = ref<string | null>(null)
  const generationProgress = ref<{ current: number; total: number; currentType: string }>({
    current: 0,
    total: 5,
    currentType: '',
  })

  const docResources = computed(() =>
    resources.value.filter(r => r.resource_type === 'doc'),
  )
  const exerciseResources = computed(() =>
    resources.value.filter(r => r.resource_type === 'exercise'),
  )
  const codeResources = computed(() =>
    resources.value.filter(r => r.resource_type === 'code'),
  )
  const mindmapResources = computed(() =>
    resources.value.filter(r => r.resource_type === 'mindmap'),
  )
  const scriptResources = computed(() =>
    resources.value.filter(r => r.resource_type === 'script'),
  )

  function addResource(res: LearningResource) {
    // 避免重复
    if (!resources.value.find(r => r.resource_id === res.resource_id)) {
      resources.value.unshift(res)
    }
  }

  function updateGenerationProgress(currentType: string, current: number, total: number) {
    generationProgress.value = { currentType, current, total }
  }

  async function generateResource(
    knowledgePoint: string,
    type: ResourceType = 'doc',
    difficulty = 3,
  ) {
    loading.value = true
    error.value = null
    try {
      const res = await resourcesApi.generate({
        knowledge_point: knowledgePoint,
        resource_type: type,
        difficulty,
      })
      addResource(res)
      activeTab.value = type
      return res
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : '资源生成失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function loadRecent(limit = 20) {
    if (resources.value.length > 0) return // 已有数据则跳过
    loading.value = true
    try {
      const items = await resourcesApi.list(limit)
      items.forEach(item => addResource(item))
    } catch {
      // 后端不可用时静默失败
    } finally {
      loading.value = false
    }
  }

  async function generateAll(knowledgePoint: string, diff = 3) {
    const types: ResourceType[] = ['doc', 'exercise', 'code', 'mindmap', 'script']
    loading.value = true
    error.value = null
    try {
      for (let i = 0; i < types.length; i++) {
        updateGenerationProgress(types[i], i, types.length)
        const res = await resourcesApi.generate({
          knowledge_point: knowledgePoint,
          resource_type: types[i],
          difficulty: diff,
        })
        addResource(res)
        activeTab.value = types[i]
      }
      updateGenerationProgress('', types.length, types.length)
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : '资源生成失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  function clearSession() {
    resources.value = []
    generationProgress.value = { current: 0, total: 5, currentType: '' }
  }

  return {
    resources,
    activeTab,
    loading,
    error,
    generationProgress,
    docResources,
    exerciseResources,
    codeResources,
    mindmapResources,
    scriptResources,
    addResource,
    updateGenerationProgress,
    generateResource,
    generateAll,
    loadRecent,
    clearSession,
  }
}, {
  // 只持久化 activeTab：选项卡状态在刷新后保留
  // resources 数据量大且可重新拉取，不常驻就内存
  persist: {
    paths: ['activeTab'],
  },
})
