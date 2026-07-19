<script setup lang="ts">
import { computed, ref } from 'vue'
import { challengerApi } from '@/api/challenger'
import { useChatStore } from '@/stores/chatStore'
import { useUserStore } from '@/stores/userStore'

const chatStore = useChatStore()
const userStore = useUserStore()

const answer = ref('')
const submitting = ref(false)
const localFeedback = ref<string | null>(null)
const errorMsg = ref<string | null>(null)   // 独立的错误消息状态
const lastIsCorrect = ref<boolean | null>(null) // 最近一次回答的正确性

const payload = computed(() => chatStore.lastChallenger)
const isActive = computed(() => payload.value?.status === 'active' || payload.value?.status === 'continue')
const isCompleted = computed(() => payload.value?.status === 'completed')

/** 用户输入时清除错误信息 */
function onAnswerInput() {
  if (errorMsg.value) errorMsg.value = null
}

async function submitAnswer() {
  if (!answer.value.trim() || submitting.value || !chatStore.currentSession) return
  submitting.value = true
  localFeedback.value = null
  errorMsg.value = null
  lastIsCorrect.value = null
  try {
    const result = await challengerApi.evaluate(
      chatStore.currentSession.sessionId,
      answer.value.trim(),
    )
    chatStore.setChallengerPayload(result)
    localFeedback.value = result.feedback ?? null
    lastIsCorrect.value = result.is_correct ?? null
    if (result.status !== 'completed') {
      answer.value = ''
    }
  } catch (err) {
    // 错误信息独立显示，不与正常反馈混用
    errorMsg.value = err instanceof Error ? err.message : '提交失败，请重试'
  } finally {
    submitting.value = false
  }
}

async function startManualChallenge() {
  if (!chatStore.currentSession || submitting.value) return
  submitting.value = true
  errorMsg.value = null
  try {
    const result = await challengerApi.start(
      chatStore.currentSession.sessionId,
      userStore.userId,
      chatStore.lastDiagnosis,
    )
    chatStore.setChallengerPayload(result)
    answer.value = ''
    localFeedback.value = null
    lastIsCorrect.value = null
  } catch (err) {
    errorMsg.value = err instanceof Error ? err.message : '无法启动检验，请检查网络连接后重试'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <section class="challenger-quiz-card">
    <div class="card-header">
      <div>
        <h4 class="card-title">
          <el-icon><WarningFilled /></el-icon>
          Challenger 误解检验
        </h4>
        <p class="card-subtitle">针对诊断结果的自适应追问，验证理解深度</p>
      </div>
      <el-button
        v-if="!payload"
        size="small"
        type="primary"
        plain
        :loading="submitting"
        @click="startManualChallenge"
      >
        开始检验
      </el-button>
    </div>

    <!-- 错误提示：独立显示，样式明确区分（不与正常反馈混用） -->
    <el-alert
      v-if="errorMsg"
      :title="errorMsg"
      type="warning"
      show-icon
      :closable="true"
      @close="errorMsg = null"
      class="quiz-error-alert"
    />

    <div v-if="!payload && !errorMsg" class="empty-hint">
      对话触发诊断后，系统将自动推送检验题；也可手动开始。
    </div>

    <template v-if="payload">
      <div v-if="payload.round" class="round-meta">
        <el-tag size="small" type="primary" effect="plain">
          第 {{ payload.round }}/{{ payload.max_rounds ?? 5 }} 轮
        </el-tag>
        <el-tag v-if="payload.topic" size="small" effect="plain">{{ payload.topic }}</el-tag>
      </div>

      <div v-if="payload.question && isActive" class="question-box">
        <p class="question-text">{{ payload.question }}</p>
        <el-input
          v-model="answer"
          type="textarea"
          :rows="3"
          placeholder="写下你的判断或解释..."
          :disabled="submitting"
          @input="onAnswerInput"
        />
        <el-button
          type="primary"
          size="small"
          :loading="submitting"
          :disabled="!answer.trim()"
          @click="submitAnswer"
        >
          {{ submitting ? '评估中...' : '提交回答' }}
        </el-button>
      </div>

      <!-- 正常反馈区域：仅在成功获取结果后显示 -->
      <div v-if="(localFeedback || payload.feedback) && !errorMsg" class="feedback-box"
        :class="{ 'feedback-correct': lastIsCorrect === true, 'feedback-incorrect': lastIsCorrect === false }">
        <div class="feedback-header">
          <span class="feedback-label">
            <span v-if="lastIsCorrect === true">✅ 回答正确</span>
            <span v-else-if="lastIsCorrect === false">💡 AI 反馈</span>
            <span v-else>反馈</span>
          </span>
        </div>
        <p class="feedback-text">{{ localFeedback || payload.feedback }}</p>
      </div>

      <!-- 完成评估区域 -->
      <div v-if="isCompleted" class="assessment-box">
        <div class="assessment-header">
          <span class="assessment-icon">🎓</span>
          <span class="assessment-title">检验完成</span>
        </div>
        <div class="assessment-score">
          理解评估：<strong class="level-badge">{{ payload.understanding_level }}</strong>
          <span v-if="payload.understanding_score != null" class="score-num">{{ payload.understanding_score }} 分</span>
        </div>
        <ul v-if="payload.suggestions?.length" class="suggestion-list">
          <li v-for="(item, idx) in payload.suggestions" :key="idx">{{ item }}</li>
        </ul>
      </div>
    </template>
  </section>
</template>

<style scoped>
.challenger-quiz-card {
  margin-top: 12px;
  padding: 14px;
  border-radius: 12px;
  border: 1px solid #e0e7ff;
  background: linear-gradient(135deg, #f5f3ff, #eff6ff);
}

.card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #3730a3;
}

.card-subtitle {
  margin: 4px 0 0;
  font-size: 12px;
  color: #6366f1;
}

.quiz-error-alert {
  margin-bottom: 10px;
  border-radius: 8px;
}

.empty-hint {
  font-size: 12px;
  color: #6366f1;
  line-height: 1.5;
  padding: 8px 0;
}

.round-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 10px;
}

.question-box {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.question-text {
  margin: 0;
  font-size: 13px;
  line-height: 1.6;
  color: #1e1b4b;
  background: rgba(255,255,255,0.8);
  border-left: 3px solid #6366f1;
  padding: 10px 12px;
  border-radius: 0 8px 8px 0;
}

/* 反馈框：正常状态（默认靛蓝） */
.feedback-box {
  margin-top: 10px;
  padding: 10px 12px;
  border-radius: 8px;
  background: #f5f3ff;
  border: 1px solid #c7d2fe;
  font-size: 12px;
  color: #312e81;
}

/* 回答正确时：绿色反馈 */
.feedback-box.feedback-correct {
  background: #f0fdf4;
  border-color: #86efac;
  color: #166534;
}

/* 回答有待改进时：橙色/黄色反馈（不是红色，避免引起误解） */
.feedback-box.feedback-incorrect {
  background: #fffbeb;
  border-color: #fde68a;
  color: #92400e;
}

.feedback-header {
  margin-bottom: 6px;
}

.feedback-label {
  font-size: 12px;
  font-weight: 600;
}

.feedback-correct .feedback-label { color: #15803d; }
.feedback-incorrect .feedback-label { color: #b45309; }
.feedback-box:not(.feedback-correct):not(.feedback-incorrect) .feedback-label { color: #4338ca; }

.feedback-text {
  margin: 0;
  line-height: 1.6;
}

/* 完成评估框 */
.assessment-box {
  margin-top: 10px;
  padding: 12px;
  border-radius: 8px;
  background: #ecfdf5;
  border: 1px solid #86efac;
}

.assessment-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
}

.assessment-title {
  font-size: 13px;
  font-weight: 600;
  color: #15803d;
}

.assessment-score {
  font-size: 13px;
  color: #166534;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.level-badge {
  display: inline-block;
  padding: 1px 8px;
  background: #bbf7d0;
  border-radius: 12px;
  color: #14532d;
  font-size: 12px;
}

.score-num {
  font-size: 12px;
  color: #166534;
  background: #dcfce7;
  border-radius: 10px;
  padding: 1px 7px;
}

.suggestion-list {
  margin: 8px 0 0;
  padding-left: 18px;
  font-size: 12px;
  color: #15803d;
  line-height: 1.6;
}
</style>
