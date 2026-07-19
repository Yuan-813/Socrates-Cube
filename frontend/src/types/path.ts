export type PathNodeStatus = 'completed' | 'in_progress' | 'pending' | 'locked'

/** 路径推荐理由的三维来源（与后端 path_planner._build_3d_reasons 一致） */
export interface PathReasonSources {
  graph_dependency?: string
  diagnosis_result?: string
  cognitive_style?: string
}

export interface LearningPathNode {
  id: string
  title: string
  status: 'completed' | 'current' | 'locked' | 'pending' | 'in_progress'
  estimatedTime: number
  reason?: string
  reason_sources?: PathReasonSources
}

export interface PathNode {
  node_id: string
  node_name: string
  type: string
  chapter: string
  difficulty: number
  estimated_time: number
  recommendation_reason: string
  reason_sources: PathReasonSources
  suggested_resources: string[]
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

export function hasPathReasonSources(
  sources: PathReasonSources | undefined,
): sources is PathReasonSources {
  if (!sources) return false
  return Boolean(
    sources.graph_dependency || sources.diagnosis_result || sources.cognitive_style,
  )
}
