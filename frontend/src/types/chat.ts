import type { DiagnosisResult } from './diagnosis'

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  isStreaming?: boolean
  diagnosisResult?: DiagnosisResult
}