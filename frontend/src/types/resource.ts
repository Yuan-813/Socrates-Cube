export type ResourceType = 'doc' | 'exercise' | 'code' | 'mindmap' | 'script'

export interface BaseResource {
  id: string
  resource_type: ResourceType
  title: string
  knowledge_point: string
  difficulty: number
  tags: string[]
  created_at: string
}

export interface DocResource extends BaseResource {
  resource_type: 'doc'
  content: string
  reading_time: number
  source_references: string[]
}

export interface ExerciseOption {
  label: string
  text: string
}

export interface ExerciseResource extends BaseResource {
  resource_type: 'exercise'
  exercise_type: 'choice' | 'fill_blank' | 'scenario' | 'packet_analysis'
  question: string
  options?: ExerciseOption[]
  correct_answer: string
  explanation: string
  targeted_misconception?: string
}

export interface CodeResource extends BaseResource {
  resource_type: 'code'
  language: string
  code: string
  explanation: string
  expected_output?: string
  runnable: boolean
}

export interface MindmapResource extends BaseResource {
  resource_type: 'mindmap'
  nodes: Array<{
    id: string
    label: string
    parent_id?: string
    level: number
  }>
}

export interface ScriptResource extends BaseResource {
  resource_type: 'script'
  scenes: Array<{
    scene_id: string
    description: string
    duration: number
  }>
}

export type AnyResource = DocResource | ExerciseResource | CodeResource | MindmapResource | ScriptResource
