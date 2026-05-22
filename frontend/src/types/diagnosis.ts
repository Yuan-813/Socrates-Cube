export type ErrorType = 'layer_misplacement' | 'missing_dependency' | 'state_confusion' | 'format_error' | 'unknown'

export interface SurfaceError {
  error_type: ErrorType
  error_description: string
  student_quote: string
}

export interface RootCause {
  weak_knowledge: string
  confidence: number
  evidence: string[]
}

export interface MisconceptionPattern {
  pattern_id: string
  pattern_name: string
  frequency: number
  related_knowledge: string[]
}

export interface DiagnosisDetail {
  diagnosisId: string
  sessionId: string
  trigger: string
  surfaceError: SurfaceError
  rootCause: RootCause
  misconceptionPattern: MisconceptionPattern
  suggestedResourceTypes: string[]
}
