import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { LearningResource, ResourceType } from '../types'
import { resourcesApi } from '../api/resources'

export const useResourceStore = defineStore('resource', () => {
  const resources = ref<LearningResource[]>([])
  const activeTab = ref<ResourceType>('doc')
  const loading = ref(false)
  const error = ref<string | null>(null)

  const docResources = computed(() =>
    resources.value.filter(r => r.resource_type === 'doc'),
  )
  const exerciseResources = computed(() =>
    resources.value.filter(r => r.resource_type === 'exercise'),
  )
  const codeResources = computed(() =>
    resources.value.filter(r => r.resource_type === 'code'),
  )

  function addResource(res: LearningResource) {
    // 避免重复
    if (!resources.value.find(r => r.resource_id === res.resource_id)) {
      resources.value.unshift(res)
    }
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

  function clearSession() {
    resources.value = []
  }

  return {
    resources,
    activeTab,
    loading,
    error,
    docResources,
    exerciseResources,
    codeResources,
    addResource,
    generateResource,
    clearSession,
  }
})
