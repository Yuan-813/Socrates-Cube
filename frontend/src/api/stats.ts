import apiClient from './client'

export interface StatsSummary {
  user_id: string
  total_sessions: number
  total_messages: number
  learning_days: number
  overall_mastery: number
  mastery_history: number[]
  radar_scores: number[]
  radar_dims: string[]
  weak_points: string[]
  assessment_count: number
  diagnosis_avg_score: number
  score_trend: { score: number; node_id: string; time: string }[]
  chapter_progress: number
  knowledge_nodes_count: number
}

export const statsApi = {
  async getSummary(userId: string): Promise<StatsSummary> {
    const { data } = await apiClient.get<StatsSummary>('/api/v1/stats/summary', {
      params: { user_id: userId },
    })
    return data
  },
}
