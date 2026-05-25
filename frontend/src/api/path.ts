import apiClient from './client'
import type { LearningPath } from '../types'

export const pathApi = {
  getUserPath(userId: string): Promise<LearningPath> {
    return apiClient.get(`/api/v1/path/${userId}`).then((r) => r.data)
  },

  planPath(params: {
    user_id?: string
    target_node_ids?: string[]
    max_nodes?: number
  }): Promise<LearningPath> {
    const { user_id = 'student-001', ...body } = params
    return apiClient
      .post(`/api/v1/path/plan?user_id=${user_id}`, body)
      .then((r) => r.data)
  },

  updateProgress(
    userId: string,
    nodeId: string,
    status: string,
    mastery?: number,
  ): Promise<void> {
    return apiClient
      .post(`/api/v1/path/${userId}/progress`, { node_id: nodeId, status, mastery })
      .then(() => undefined)
  },
}
