export type SSEEventType =
  | 'agent_start'
  | 'agent_end'
  | 'tool_call'
  | 'token'
  | 'diagnosis'
  | 'resource'
  | 'path_update'
  | 'state_change'
  | 'challenger'
  | 'scope_notice'
  | 'intervention_suggested'
  | 'kg_nodes'
  | 'rl_update'
  | 'persona_set'
  | 'done'
  | 'error'

export interface ScopeNoticePayload {
  title?: string
  description?: string
}

export interface ChallengerPayload {
  status: 'active' | 'continue' | 'completed'
  session_id?: string
  round?: number
  max_rounds?: number
  question?: string
  question_type?: string
  topic?: string
  feedback?: string
  is_correct?: boolean
  understanding_level?: string
  understanding_score?: number
  suggestions?: string[]
  correct_count?: number
  total_rounds?: number
}

export interface SSEPayload {
  event: SSEEventType
  agent_name: string
  data: unknown
  timestamp: string
}