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
  misconception_id?: string
  knowledge_node_ids?: string[]
  acu_ids?: string[]
  recommended_interventions?: InterventionRecommendation[]
}

export interface InterventionRecommendation {
  type: 'simulation' | 'exercise' | 'challenge' | 'doc'
  id: string | null
  label: string
  description: string
  rationale: string
  priority?: number
}