import apiClient from './client'
import type { LearningResource, ResourceType } from '../types'

export const resourcesApi = {
  generate(params: {
    knowledge_point: string
    resource_type?: ResourceType
    difficulty?: number
    session_id?: string
  }): Promise<LearningResource> {
    return apiClient
      .post('/api/v1/resources/generate', params)
      .then((r) => r.data)
  },
}
