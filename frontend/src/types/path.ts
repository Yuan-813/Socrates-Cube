export type PathNodeStatus = 'completed' | 'current' | 'locked'
export type PathNodeType = 'concept' | 'protocol' | 'process' | 'format' | 'mechanism'

export interface PathNode {
  id: string
  title: string
  description: string
  status: PathNodeStatus
  type: PathNodeType
  difficulty: number
  estimated_time: number
  prerequisites: string[]
  knowledge_id: string
}

export interface LearningPath {
  path_id: string
  user_id: string
  title: string
  nodes: PathNode[]
  created_at: string
  updated_at: string
}
