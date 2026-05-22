import apiClient from './client'
import type { LearningPath } from '@/types/path'

export const pathApi = {
  getUserPath: (userId: string) =>
    apiClient.get<LearningPath>(`/v1/path/${userId}`),

  updateProgress: (userId: string, nodeId: string, status: string) =>
    apiClient.post(`/v1/path/${userId}/progress`, { node_id: nodeId, status }),
}
