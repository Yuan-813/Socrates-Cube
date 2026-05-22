import { ref } from 'vue'
import { defineStore } from 'pinia'
import type { AnyResource } from '@/types/resource'

export const useResourceStore = defineStore('resources', () => {
  const resources = ref<AnyResource[]>([])
  const activeTab = ref<string>('doc')
  const isLoading = ref(false)

  function addResource(resource: AnyResource) {
    resources.value.push(resource)
    activeTab.value = resource.resource_type
  }

  function setResources(list: AnyResource[]) {
    resources.value = list
  }

  function clearSession() {
    resources.value = []
    activeTab.value = 'doc'
  }

  return { resources, activeTab, isLoading, addResource, setResources, clearSession }
})
