import apiClient from './client'
import type { AgentLog } from '../types'

export interface SessionLogsResponse {
  session_id: string
  logs: Array<{
    log_id: string
    agent_name: string
    action: string
    state: Record<string, unknown> | string
    result: Record<string, unknown> | string
    timestamp: string
  }>
}

function formatField(value: unknown): string {
  if (value == null) return ''
  if (typeof value === 'string') return value
  try {
    return JSON.stringify(value, null, 0)
  } catch {
    return String(value)
  }
}

export function mapApiLog(raw: SessionLogsResponse['logs'][number], sessionId = ''): AgentLog {
  const stateObj = typeof raw.state === 'object' && raw.state ? raw.state : {}
  const resultText = formatField(raw.result)
  const action = raw.action || 'execute'
  const inputPreview = formatField((stateObj as Record<string, unknown>).input)
  return {
    log_id: raw.log_id,
    session_id: sessionId,
    agent_name: raw.agent_name,
    action,
    state: inputPreview || formatField(raw.state),
    result: resultText,
    timestamp: raw.timestamp,
  }
}

export const logsApi = {
  async getSessionLogs(sessionId: string): Promise<AgentLog[]> {
    const resp = await apiClient.get<SessionLogsResponse>(`/api/v1/logs/session/${sessionId}`)
    return (resp.data.logs || []).map((item) => mapApiLog(item, resp.data.session_id))
  },
}
