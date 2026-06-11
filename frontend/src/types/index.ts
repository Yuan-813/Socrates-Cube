// ──────────────────────────────────────────────────────
// 学生画像
// ──────────────────────────────────────────────────────
export interface StudentProfile {
  userId?: string
  updatedAt?: string
  dimensions?: Array<{ name: string; label: string; level: number; description: string }>
  cognitiveStyle?: string
  learningProgress?: Record<string, unknown>
  commonMistakes?: Record<string, unknown>
  // 8维能力评分 (0.1 ~ 1.0)
  conceptual_understanding: number
  protocol_analysis: number
  calculation_ability: number
  error_diagnosis: number
  system_design: number
  knowledge_connection: number
  expression_clarity: number
  self_correction: number
  // 知识点掌握度映射
  mastery_map: Record<string, number>
  weak_points: string[]
  strong_points: string[]
  turn_count: number
}

export const PROFILE_DIMENSION_LABELS: Record<string, string> = {
  conceptual_understanding: '概念理解',
  protocol_analysis: '协议分析',
  calculation_ability: '计算能力',
  error_diagnosis: '错误诊断',
  system_design: '系统设计',
  knowledge_connection: '知识迁移',
  expression_clarity: '表达清晰',
  self_correction: '自我纠错',
}

// ──────────────────────────────────────────────────────
// 诊断结果
// ──────────────────────────────────────────────────────
export interface DiagnosisResult {
  diagnosisId?: string
  sessionId?: string
  trigger?: string
  surfaceError?: string
  rootCause?: {
    weakKnowledge: string
    confidence: number
    evidence: string[]
  }
  misconceptionPattern?: string
  suggestedResourceTypes?: string[]
  is_correct?: boolean
  confidence?: number
  surface_error?: string | null
  error_type?: 'factual' | 'conceptual' | 'calculation' | 'none' | string
  root_causes?: string[]
  missing_prerequisites?: string[]
  pattern?: string | null
  intervention_suggestion?: string
  related_node_ids?: string[]
}

// ──────────────────────────────────────────────────────
// 学习资源
// ──────────────────────────────────────────────────────
export type ResourceType = 'doc' | 'exercise' | 'code'

export interface LearningResource {
  id?: string
  type?: string
  difficulty?: number
  tags?: string[]
  resource_id?: string
  resource_type?: ResourceType
  knowledge_point?: string
  title: string
  content: string
  metadata?: Record<string, unknown>
  created_at?: string
}

// ──────────────────────────────────────────────────────
// 学习路径
// ──────────────────────────────────────────────────────
export type PathNodeStatus = 'completed' | 'in_progress' | 'pending' | 'locked'

export interface LearningPathNode {
  id: string
  title: string
  status: 'completed' | 'current' | 'locked'
  estimatedTime: number
  reason?: string
}

export interface PathNode {
  node_id: string
  node_name: string
  type: string
  chapter: string
  difficulty: number
  estimated_time: number
  recommendation_reason: string
  reason_sources: string[]
  suggested_resources: ResourceType[]
  prerequisites: string[]
  prerequisites_met: boolean
  status: PathNodeStatus
  current_mastery: number
  is_target: boolean
}

export interface LearningPath {
  path_id: string
  user_id: string
  title: string
  description: string
  total_estimated_time: number
  nodes: PathNode[]
  generated_at: string
}

// ──────────────────────────────────────────────────────
// 代理日志
// ──────────────────────────────────────────────────────
export interface AgentLog {
  logId?: string
  sessionId?: string
  agentName?: string
  log_id?: string
  session_id?: string
  agent_name?: string
  action: string
  state: string
  timestamp: string
  result: string
}

// ──────────────────────────────────────────────────────
// SSE 事件
// ──────────────────────────────────────────────────────
export type SSEEventType =
  | 'agent_start'
  | 'agent_end'
  | 'tool_call'
  | 'token'
  | 'diagnosis'
  | 'resource'
  | 'path_update'
  | 'done'
  | 'error'

export interface SSEPayload {
  event: SSEEventType
  agent_name: string
  data: unknown
  timestamp: string
}

// ──────────────────────────────────────────────────────
// 聊天消息
// ──────────────────────────────────────────────────────
export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  isStreaming?: boolean
  diagnosisResult?: DiagnosisResult
}
