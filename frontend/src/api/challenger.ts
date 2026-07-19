import apiClient from './client'
import type { ChallengerPayload, DiagnosisResult } from '@/types'

export interface ChallengerStartResponse {
  status: string
  challenge: ChallengerPayload
}

export interface ChallengerEvaluateResponse {
  status: string
  result: ChallengerPayload
}

export const challengerApi = {
  async start(
    sessionId: string,
    userId: string,
    diagnosis?: DiagnosisResult | null,
  ): Promise<ChallengerPayload> {
    const { data } = await apiClient.post<ChallengerStartResponse>('/api/v1/challenger/start', {
      session_id: sessionId,
      user_id: userId,
      diagnosis: diagnosis ?? undefined,
    })
    return data.challenge
  },

  async evaluate(sessionId: string, userAnswer: string): Promise<ChallengerPayload> {
    const { data } = await apiClient.post<ChallengerEvaluateResponse>('/api/v1/challenger/evaluate', {
      session_id: sessionId,
      user_answer: userAnswer,
    })
    return data.result
  },
}
