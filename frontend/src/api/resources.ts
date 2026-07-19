import apiClient from './client'
import type { LearningResource, ResourceType } from '../types'

export const resourcesApi = {
  list(limit = 20): Promise<LearningResource[]> {
    return apiClient
      .get('/api/v1/resources/', { params: { limit } })
      .then((r) => r.data?.items ?? [])
  },
  generate(params: {
    knowledge_point: string
    resource_type?: ResourceType | 'all'
    difficulty?: number
    session_id?: string
  }): Promise<LearningResource> {
    return apiClient
      .post('/api/v1/resources/generate', params)
      .then((r) => r.data)
  },
}
