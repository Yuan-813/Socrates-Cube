import type { StudentProfile, DiagnosisResult, LearningResource, LearningPathNode, AgentLog } from '@/types'

export const mockProfile: StudentProfile = {
  userId: 'student-001',
  conceptual_understanding: 0.5,
  protocol_analysis: 0.5,
  calculation_ability: 0.5,
  error_diagnosis: 0.5,
  system_design: 0.5,
  knowledge_connection: 0.5,
  expression_clarity: 0.5,
  self_correction: 0.5,
  mastery_map: {},
  weak_points: [],
  strong_points: [],
  turn_count: 0,
  updatedAt: '2024-05-09T14:30:00Z',
  dimensions: [
    { name: 'network_layer', label: '网络分层认知', level: 2, description: '对OSI七层/TCP/IP四层结构掌握度偏低' },
    { name: 'protocol_memory', label: '协议流程记忆', level: 3, description: '三次握手、四次挥手能背诵但理解不深入' },
    { name: 'packet_format', label: '报文格式理解', level: 1, description: '头部字段含义混淆' },
    { name: 'protocol_relation', label: '协议间关系', level: 3, description: 'HTTP-TCP-IP依赖关系基本理解' },
    { name: 'troubleshoot', label: '故障排查逻辑', level: 1, description: '从现象定位根因的推理能力较弱' },
    { name: 'practice', label: '实践操作能力', level: 1, description: 'Wireshark抓包和Socket编程经验不足' },
    { name: 'cognitive', label: '认知风格偏好', level: 4, description: '偏视觉型学习者' },
    { name: 'misconception', label: '常见误解模式', level: 2, description: '当前聚类为"层次穿越型"' },
  ],
  cognitiveStyle: 'visual',
  learningProgress: {
    completedTopics: ['TCP/IP 概述', 'TCP 报文格式'],
    currentTopic: 'TCP 连接管理',
    completionRate: 0.25,
  },
  commonMistakes: {
    types: ['层次穿越', '流程死记', '字段混淆'],
    frequency: { '层次穿越': 5, '流程死记': 3, '字段混淆': 4 },
  },
}

export const mockDiagnosis: DiagnosisResult = {
  diagnosisId: 'diag-001',
  sessionId: 'session-001',
  trigger: '学生回答：HTTP直接基于IP传输',
  surfaceError: '协议层次错位',
  rootCause: {
    weakKnowledge: 'TCP/IP 分层封装机制',
    confidence: 0.92,
    evidence: ['教材第4章第2节', 'RFC 793 摘要段落3'],
  },
  misconceptionPattern: '层次穿越型',
  suggestedResourceTypes: ['分层封装动画', '封装过程代码演示', '对比练习'],
}

export const mockResources: LearningResource[] = [
  { id: 'res-001', title: 'TCP vs UDP 决策指南', type: 'document', content: '详细对比TCP和UDP的适用场景、性能特征及选择策略...', difficulty: 2, tags: ['协议对比', '传输层'] },
  { id: 'res-002', title: 'TCP三次握手思维导图', type: 'mindmap', content: '完整的TCP连接建立流程，包含SYN/ACK标志位详解...', difficulty: 2, tags: ['思维导图', '连接管理'] },
  { id: 'res-003', title: '协议流程填空练习', type: 'quiz', content: '10道精选协议流程题，涵盖握手、挥手、窗口机制...', difficulty: 3, tags: ['练习题', '流程记忆'] },
  { id: 'res-004', title: 'Socket编程实战案例', type: 'code', content: 'Python Socket实现TCP客户端/服务端通信完整代码...', difficulty: 3, tags: ['代码实操', 'Socket'] },
  { id: 'res-005', title: '分层封装动画演示', type: 'video', content: '3分钟动画展示HTTP报文如何被逐层封装为以太网帧...', difficulty: 1, tags: ['视频', '分层封装'] },
]

export const mockPath: LearningPathNode[] = [
  { id: 'n1', title: 'TCP/IP 概述', status: 'completed', estimatedTime: 30 },
  { id: 'n2', title: 'TCP 报文格式', status: 'completed', estimatedTime: 45 },
  { id: 'n3', title: 'TCP 连接管理', status: 'current', reason: '你在连接管理练习中3次混淆SYN/ACK标志位', estimatedTime: 60 },
  { id: 'n4', title: 'TCP 可靠传输', status: 'locked', estimatedTime: 50 },
  { id: 'n5', title: 'TCP 拥塞控制', status: 'locked', estimatedTime: 55 },
  { id: 'n6', title: '综合实践项目', status: 'locked', estimatedTime: 120 },
]

export const mockLogs: AgentLog[] = [
  { logId: 'log-001', sessionId: 's-001', agentName: 'Orchestrator', action: '调度', state: '分析用户意图', timestamp: '2024-05-09 14:32:01', result: '识别为"概念询问"类型' },
  { logId: 'log-002', sessionId: 's-001', agentName: 'Profiler', action: '画像更新', state: '抽取8维特征', timestamp: '2024-05-09 14:32:03', result: '更新"协议流程记忆"维度' },
  { logId: 'log-003', sessionId: 's-001', agentName: 'Retriever', action: '知识检索', state: '三库联合检索', timestamp: '2024-05-09 14:32:05', result: '命中教材第3章+2条误解' },
  { logId: 'log-004', sessionId: 's-001', agentName: 'Diagnosis', action: '认知诊断', state: '三层诊断模型', timestamp: '2024-05-09 14:32:08', result: '发现"层次错位"错误' },
  { logId: 'log-005', sessionId: 's-001', agentName: 'Simulator', action: '仿真触发', state: '分层封装动画', timestamp: '2024-05-09 14:32:10', result: '播放封装过程可视化' },
]
