import apiClient from './client'

export interface AdminUserItem {
  id: string
  username: string
  email: string | null
  phone: string | null
  role_type: string
  onboarded: boolean
  create_time: string | null
}

export interface PagedUsers {
  total: number
  page: number
  size: number
  items: AdminUserItem[]
}

export interface SystemStats {
  total_users: number
  active_today: number
  total_sessions: number
  total_diagnoses: number
  avg_mastery: number
  knowledge_nodes_count: number
  daily_new_users: { date: string; count: number }[]
}

export interface LogItem {
  log_id: string
  session_id: string
  agent_name: string
  action: string
  timestamp: string
}

export interface PagedLogs {
  total: number
  page: number
  size: number
  items: LogItem[]
}

export const adminApi = {
  async listUsers(page = 1, size = 20, keyword?: string): Promise<PagedUsers> {
    const { data } = await apiClient.get<PagedUsers>('/api/v1/admin/users', {
      params: { page, size, keyword: keyword || undefined },
    })
    return data
  },

  async getStats(): Promise<SystemStats> {
    const { data } = await apiClient.get<SystemStats>('/api/v1/admin/stats')
    return data
  },

  async updateUserRole(userId: string, roleType: string): Promise<void> {
    await apiClient.put(`/api/v1/admin/users/${userId}/role`, { role_type: roleType })
  },

  async getLogs(page = 1, size = 50): Promise<PagedLogs> {
    const { data } = await apiClient.get<PagedLogs>('/api/v1/admin/logs', {
      params: { page, size },
    })
    return data
  },
}
