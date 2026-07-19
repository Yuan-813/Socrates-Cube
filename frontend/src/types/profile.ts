export interface StudentProfile {
  userId?: string
  updatedAt?: string
  dimensions?: Array<{ name: string; label: string; level: number; description: string }>
  cognitiveStyle?: string
  learningProgress?: Record<string, unknown>
  commonMistakes?: Record<string, unknown>
  conceptual_understanding: number
  protocol_analysis: number
  calculation_ability: number
  error_diagnosis: number
  system_design: number
  knowledge_connection: number
  expression_clarity: number
  self_correction: number
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

export const PROFILE_DIMENSION_ICONS: Record<string, string> = {
  conceptual_understanding: '💡',
  protocol_analysis: '🔬',
  calculation_ability: '🔢',
  error_diagnosis: '🩺',
  system_design: '🏗️',
  knowledge_connection: '🔗',
  expression_clarity: '🗣️',
  self_correction: '🔄',
}

/** 各维度的评价说明与评判标准 */
export const PROFILE_DIMENSION_DESCRIPTIONS: Record<string, { desc: string; criteria: string }> = {
  conceptual_understanding: {
    desc: '对网络协议核心概念的理解深度，包括协议定义、功能边界及层次关系',
    criteria: '≥80 优秀：准确解释概念及边界 / 60-79 良好：理解基本概念 / 40-59 中等：部分存在混淆 / <40 薄弱：概念理解较弱',
  },
  protocol_analysis: {
    desc: '分析协议报文格式、字段含义及协议交互流程的能力',
    criteria: '≥80 优秀：精准解析报文字段与流程 / 60-79 良好：理解主要字段 / 40-59 中等：分析不完整 / <40 薄弱：缺乏分析能力',
  },
  calculation_ability: {
    desc: '子网计算、时延带宽计算、序列号推导等数值计算的准确性',
    criteria: '≥80 优秀：计算准确无误 / 60-79 良好：方法正确偶有失误 / 40-59 中等：方法部分有误 / <40 薄弱：计算能力较弱',
  },
  error_diagnosis: {
    desc: '识别和定位网络故障原因、协议错误类型的诊断能力',
    criteria: '≥80 优秀：快速准确定位问题 / 60-79 良好：能识别常见错误 / 40-59 中等：诊断能力有限 / <40 薄弱：难以识别错误',
  },
  system_design: {
    desc: '设计网络架构、合理选择协议方案的综合工程能力',
    criteria: '≥80 优秀：设计合理完整 / 60-79 良好：基本思路正确 / 40-59 中等：设计有缺陷 / <40 薄弱：设计能力不足',
  },
  knowledge_connection: {
    desc: '将不同协议概念关联迁移的能力，识别知识间依赖关系',
    criteria: '≥80 优秀：能跨层次关联知识 / 60-79 良好：理解基本依赖关系 / 40-59 中等：迁移能力有限 / <40 薄弱：知识较为孤立',
  },
  expression_clarity: {
    desc: '用准确专业术语清晰表达协议机制和概念的能力',
    criteria: '≥80 优秀：表达准确清晰专业 / 60-79 良好：表达基本清楚 / 40-59 中等：表达有混淆 / <40 薄弱：表达不清',
  },
  self_correction: {
    desc: '接受反馈提示后自主纠正错误认知的修正能力',
    criteria: '≥80 优秀：迅速准确自我纠正 / 60-79 良好：能纠正主要错误 / 40-59 中等：纠正能力有限 / <40 薄弱：难以自我修正',
  },
}