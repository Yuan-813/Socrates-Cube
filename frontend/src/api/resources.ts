import apiClient from './client'
import type { AnyResource } from '@/types/resource'

export const resourcesApi = {
  getBySession: (sessionId: string) =>
    apiClient.get<AnyResource[]>('/v1/resources', { params: { session_id: sessionId } }),

  getById: (resourceId: string) =>
    apiClient.get<AnyResource>(`/v1/resources/${resourceId}`),
}
