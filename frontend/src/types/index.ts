export interface StudentProfile {
  userId: string
  updatedAt: string
  dimensions: ProfileDimension[]
  cognitiveStyle: 'visual' | 'textual' | 'practical'
  learningProgress: {
    completedTopics: string[]
    currentTopic: string
    completionRate: number
  }
  commonMistakes: {
    types: string[]
    frequency: Record<string, number>
  }
}

export interface ProfileDimension {
  name: string
  label: string
  level: number
  description: string
}

export interface DiagnosisResult {
  diagnosisId: string
  sessionId: string
  trigger: string
  surfaceError: string
  rootCause: {
    weakKnowledge: string
    confidence: number
    evidence: string[]
  }
  misconceptionPattern: string
  suggestedResourceTypes: string[]
}

export interface LearningResource {
  id: string
  title: string
  type: 'document' | 'mindmap' | 'quiz' | 'code' | 'video'
  content: string
  difficulty: number
  tags: string[]
}

export interface LearningPathNode {
  id: string
  title: string
  status: 'completed' | 'current' | 'locked'
  reason?: string
  estimatedTime: number
}

export interface AgentLog {
  logId: string
  sessionId: string
  agentName: string
  action: string
  state: string
  timestamp: string
  result: string
}
