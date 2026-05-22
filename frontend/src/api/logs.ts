import apiClient from './client'
import type { AgentLog } from '@/types'

export interface SessionLogsResponse {
  session_id: string
  logs: Array<{
    log_id: string
    agent_name: string
    action: string
    timestamp: string
    result: string | null
  }>
  total: number
}

function mapLog(l: SessionLogsResponse['logs'][0]): AgentLog {
  return {
    logId: l.log_id,
    sessionId: '',
    agentName: l.agent_name,
    action: l.action,
    state: '',
    timestamp: l.timestamp,
    result: l.result || '',
  }
}

export async function fetchSessionLogs(sessionId: string): Promise<AgentLog[]> {
  try {
    const res = await apiClient.get<SessionLogsResponse>(`/v1/logs/session/${sessionId}`)
    return res.data.logs.map(mapLog)
  } catch {
    console.warn('[logs] 获取会话日志失败，使用当前 SSE 日志')
    return []
  }
}
