export type ResourceType = 'doc' | 'exercise' | 'code' | 'mindmap' | 'script' | 'infographic'

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
  /** 诊断驱动生成（由 generate_from_diagnosis 产生） */
  diagnosis_driven?: boolean
  /** 资源选择策略说明 */
  strategy_reason?: string
  /** 关联误解 ID */
  misconception_id?: string
}