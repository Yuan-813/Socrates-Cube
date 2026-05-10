export type SSEEventType =
  | 'agent_start'
  | 'token'
  | 'agent_end'
  | 'profile_update'
  | 'diagnosis'
  | 'simulator'
  | 'resource'
  | 'path_update'
  | 'error'
  | 'done'

export interface SSEEvent<T = unknown> {
  event: SSEEventType
  agent_name?: string
  data: T
  timestamp?: string
}

export interface ChatStreamPayload {
  session_id: string
  user_id: string
  message: string
  history?: Array<{
    role: 'user' | 'assistant'
    content: string
  }>
}
