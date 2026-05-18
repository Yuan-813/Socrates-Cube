import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import type { AgentLog, DiagnosisResult, LearningPathNode, LearningResource, StudentProfile } from '@/types'

export const useAssistantStore = defineStore('assistant', () => {
  const mode = ref<'mock' | 'real'>('mock')
  const connectionStatus = ref<'idle' | 'connecting' | 'streaming' | 'error'>('idle')
  const lastError = ref<string>('')
  const profile = ref<StudentProfile | null>(null)
  const diagnosis = ref<DiagnosisResult | null>(null)
  const resources = ref<LearningResource[]>([])
  const learningPath = ref<LearningPathNode[]>([])
  const logs = ref<AgentLog[]>([])
  const simulatorSummary = ref<string>('等待触发协议仿真')

  const isMockMode = computed(() => mode.value === 'mock')

  function setMode(value: 'mock' | 'real') {
    mode.value = value
  }

  function setConnectionStatus(value: 'idle' | 'connecting' | 'streaming' | 'error') {
    connectionStatus.value = value
  }

  function setLastError(message: string) {
    lastError.value = message
  }

  function appendLog(log: AgentLog) {
    logs.value.unshift(log)
  }

  function resetRuntimeState() {
    connectionStatus.value = 'idle'
    lastError.value = ''
  }

  function setProfile(value: StudentProfile | null) {
    profile.value = value
  }

  function setDiagnosis(value: DiagnosisResult | null) {
    diagnosis.value = value
  }

  function setResources(value: LearningResource[]) {
    resources.value = value
  }

  function setLearningPath(value: LearningPathNode[]) {
    learningPath.value = value
  }

  function setLogs(value: AgentLog[]) {
    logs.value = value
  }

  function setSimulatorSummary(value: string) {
    simulatorSummary.value = value
  }

  return {
    mode,
    connectionStatus,
    lastError,
    profile,
    diagnosis,
    resources,
    learningPath,
    logs,
    simulatorSummary,
    isMockMode,
    setMode,
    setConnectionStatus,
    setLastError,
    appendLog,
    resetRuntimeState,
    setProfile,
    setDiagnosis,
    setResources,
    setLearningPath,
    setLogs,
    setSimulatorSummary,
  }
}, {
  persist: true,
})
