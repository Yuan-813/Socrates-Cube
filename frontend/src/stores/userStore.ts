import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { StudentProfile } from '../types'
import apiClient from '../api/client'

const PROFILE_DIMS = [
  'conceptual_understanding',
  'protocol_analysis',
  'calculation_ability',
  'error_diagnosis',
  'system_design',
  'knowledge_connection',
  'expression_clarity',
  'self_correction',
] as const

const defaultProfile = (): StudentProfile => ({
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
})

export const useUserStore = defineStore('user', () => {
  const userId = ref<string>('student-001')
  const username = ref<string>('学生用户')
  const isLoggedIn = ref<boolean>(true)
  const profile = ref<StudentProfile>(defaultProfile())
  const demoMode = ref<boolean>(false)
  const manualRead = ref<boolean>(false)
  /** 学生综合掌握度历史（最近12次，每次 ProfilerAgent 更新后记录一个快照）
   *  这才是“能力成长曲线”的真正数据源，区别于 chatStore.confidenceHistory（AI 诊断自信度） */
  const masteryHistory = ref<number[]>([])

  /** 8维评分数组（供 ECharts 雷达图使用） */
  const radarScores = computed(() =>
    PROFILE_DIMS.map(dim => Math.round(profile.value[dim] * 100)),
  )

  /** 整体掌握度百分比（8维均值） */
  const profileCompleteness = computed(() => {
    const avg = PROFILE_DIMS.reduce((sum, d) => sum + profile.value[d], 0) / PROFILE_DIMS.length
    return Math.round(avg * 100)
  })

  async function fetchProfile() {
    try {
      const resp = await apiClient.get(`/api/v1/profile/${userId.value}`)
      // profile 响应识别：新格式 { success, data: { profile } }，旧格式 { profile }
      const payload = resp.data?.data ?? resp.data
      if (payload?.profile) {
        profile.value = { ...defaultProfile(), ...payload.profile }
      }
    } catch {
      // 保留本地默认值
    }
  }

  /** 从 SSE agent_end(Profiler) 事件更新画像 */
  function updateFromSSE(partial: Partial<StudentProfile>) {
    profile.value = { ...profile.value, ...partial }
    // 每次画像被 ProfilerAgent 更新，记录一个综合掌握度快照（这才是能力曲线的真正含义）
    const mastery = Math.round(
      PROFILE_DIMS.reduce((sum, d) => sum + profile.value[d], 0) / PROFILE_DIMS.length * 100
    )
    masteryHistory.value.push(mastery)
    if (masteryHistory.value.length > 12) {
      masteryHistory.value = masteryHistory.value.slice(-12)
    }
  }

  function setUser(id: string, name: string) {
    userId.value = id
    username.value = name
    isLoggedIn.value = true
  }

  return {
    userId,
    username,
    isLoggedIn,
    profile,
    demoMode,
    manualRead,
    radarScores,
    profileCompleteness,
    masteryHistory,
    fetchProfile,
    updateFromSSE,
    setUser,
  }
}, {
  persist: true,
})
