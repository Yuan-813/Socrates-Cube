import apiClient from './client'

export interface HealthStatus {
  status: string
  version: string
}

export async function checkHealth(): Promise<HealthStatus> {
  try {
    const response = await apiClient.get<HealthStatus>('/health')
    return response.data
  } catch (error) {
    // 捕获异常，返回一个友好的失败状态，避免控制台向外抛出未捕获错误
    return { status: '未连接', version: '' }
  }
}
