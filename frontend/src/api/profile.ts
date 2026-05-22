import apiClient from './client'
import type { StudentProfile } from '@/types'

const DIM_MAP: Record<string, { label: string; description: string }> = {
  network_layer_cognition: { label: '网络分层认知', description: '对OSI七层/TCP/IP四层结构的掌握程度' },
  protocol_flow_memory: { label: '协议流程记忆', description: '三次握手、四次挥手等协议流程的记忆与理解' },
  packet_format_understanding: { label: '报文格式理解', description: '各层协议首部字段的含义与作用' },
  protocol_relationship: { label: '协议间关系', description: 'HTTP-TCP-IP等协议之间的依赖与封装关系' },
  fault_diagnosis_logic: { label: '故障排查逻辑', description: '从网络现象定位根因的推理能力' },
  hands_on_ability: { label: '实践操作能力', description: 'Wireshark抓包、Socket编程等实操经验' },
}

export interface ProfileResponse {
  user_id: string
  profile: Record<string, number | null> | null
  message?: string
}

export async function fetchProfile(userId: string): Promise<StudentProfile | null> {
  try {
    const res = await apiClient.get<ProfileResponse>(`/v1/profile/${userId}`)
    const raw = res.data.profile
    if (!raw) return null

    const dimensions = Object.entries(DIM_MAP).map(([key, meta]) => ({
      name: key,
      label: meta.label,
      level: raw[key] != null ? Math.min(5, Math.max(1, Math.round(Number(raw[key])))) : 2,
      description: meta.description,
    }))

    return {
      userId: res.data.user_id,
      updatedAt: new Date().toISOString(),
      dimensions,
      cognitiveStyle: 'visual',
      learningProgress: { completedTopics: [], currentTopic: '', completionRate: 0 },
      commonMistakes: { types: [], frequency: {} },
    }
  } catch {
    console.warn('画像获取失败')
    return null
  }
}

export async function updateProfile(userId: string, profile: Record<string, any>): Promise<void> {
  await apiClient.post(`/v1/profile/${userId}`, profile)
}
