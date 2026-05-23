<script setup lang="ts">
import { ref, computed } from 'vue'

interface ChallengeRound {
  id: number
  topic: string
  statement: string
  isCorrect: boolean
  misconception: string
  truth: string
  explanation: string
}

const rounds: ChallengeRound[] = [
  {
    id: 1,
    topic: 'TCP 可靠性',
    statement: 'TCP 协议通过三次握手建立连接后，就不会再丢失任何数据包了，因为连接已经建立。',
    isCorrect: false,
    misconception: '认为建立连接后就不会丢包',
    truth: 'TCP 的可靠性通过序列号、确认应答和重传机制实现，连接建立后仍可能丢包，只是 TCP 会自动重传。',
    explanation: '三次握手仅用于同步初始序列号和分配资源，数据传输阶段的可靠性依赖于 ACK、超时重传、滑动窗口等机制。'
  },
  {
    id: 2,
    topic: 'UDP vs TCP',
    statement: 'UDP 比 TCP 快是因为 UDP 的头部比 TCP 小，所以传输效率更高。',
    isCorrect: false,
    misconception: '将速度快完全归因于头部大小',
    truth: 'UDP 快的主要原因是无连接、无握手、无拥塞控制、无重传，头部小只是次要因素。',
    explanation: 'UDP 省去连接建立、流量控制、拥塞控制等机制，减少了延迟和状态维护开销，而不仅仅是头部大小的差异。'
  },
  {
    id: 3,
    topic: '三次握手',
    statement: 'TCP 三次握手中，第三次握手（ACK）丢失的话，连接仍然可以正常建立，因为服务端已经发送了 SYN+ACK。',
    isCorrect: false,
    misconception: '认为服务端发出 SYN+ACK 即算连接建立',
    truth: '第三次 ACK 丢失会导致服务端重传 SYN+ACK，直到超时或收到 ACK。连接必须双方都确认才建立。',
    explanation: 'TCP 是全双工连接，必须双方都进入 ESTABLISHED 状态。服务端没收到第三次 ACK 时仍处于 SYN_RCVD 状态。'
  },
  {
    id: 4,
    topic: 'IP 地址与 MAC',
    statement: '在同一个局域网内，数据帧通过目的 IP 地址直接找到目标主机。',
    isCorrect: false,
    misconception: '混淆网络层和数据链路层',
    truth: '局域网内通过 MAC 地址寻址，需要 ARP 协议将 IP 解析为 MAC，数据帧头部只包含 MAC 地址。',
    explanation: 'IP 地址用于网络层路由，MAC 地址用于数据链路层局域网内寻址。发送方通过 ARP 请求获取目标 MAC 后才能封装以太网帧。'
  },
  {
    id: 5,
    topic: '子网掩码',
    statement: '子网掩码 255.255.255.0 表示网络部分占 24 位，主机部分占 8 位，因此这个子网最多可以有 256 台主机。',
    isCorrect: false,
    misconception: '忽略网络地址和广播地址',
    truth: '8 位主机号最多有 2^8 - 2 = 254 个可用主机地址，要减去全 0（网络地址）和全 1（广播地址）。',
    explanation: '主机号全 0 表示网络本身，全 1 表示广播地址，这两个地址不能分配给主机使用。'
  },
  {
    id: 6,
    topic: 'HTTP 与 TCP',
    statement: 'HTTP/1.1 的持久连接（Keep-Alive）意味着一个 TCP 连接上可以同时传输多个请求和响应，且这些请求可以并行发送。',
    isCorrect: false,
    misconception: '混淆持久连接和流水线/多路复用',
    truth: 'HTTP/1.1 Keep-Alive 允许复用连接串行发送请求，但同一时刻只能有一个请求在传输（队头阻塞）。并行需要 HTTP/2 的多路复用。',
    explanation: 'HTTP/1.1 持久连接解决了重复建立 TCP 连接的开销，但请求仍是串行的。HTTP/2 通过二进制分帧和流多路复用才实现了真正的并行传输。'
  }
]

const currentIndex = ref(0)
const userJudgment = ref<'correct' | 'incorrect' | null>(null)
const userExplanation = ref('')
const showResult = ref(false)
const score = ref(0)
const streak = ref(0)
const maxStreak = ref(0)
const history = ref<{ round: number; correct: boolean }[]>([])

const currentRound = computed(() => rounds[currentIndex.value])
const totalRounds = rounds.length
const isFinished = computed(() => currentIndex.value >= totalRounds)

const progressPercent = computed(() => {
  if (isFinished.value) return 100
  return ((currentIndex.value) / totalRounds) * 100
})

function judge(correct: boolean) {
  userJudgment.value = correct ? 'correct' : 'incorrect'
}

function submitAnswer() {
  if (!userJudgment.value) return
  const isUserCorrect = (userJudgment.value === 'correct') === currentRound.value.isCorrect
  if (isUserCorrect) {
    score.value++
    streak.value++
    if (streak.value > maxStreak.value) maxStreak.value = streak.value
  } else {
    streak.value = 0
  }
  history.value.push({ round: currentRound.value.id, correct: isUserCorrect })
  showResult.value = true
}

function nextRound() {
  currentIndex.value++
  userJudgment.value = null
  userExplanation.value = ''
  showResult.value = false
}

function resetAll() {
  currentIndex.value = 0
  userJudgment.value = null
  userExplanation.value = ''
  showResult.value = false
  score.value = 0
  streak.value = 0
  maxStreak.value = 0
  history.value = []
}
</script>

<template>
  <div class="challenger-panel">
    <!-- 头部统计 -->
    <div class="challenger-header">
      <div class="header-left">
        <h3 class="challenger-title">
          <el-icon class="challenger-icon"><WarningFilled /></el-icon>
          Misconception Challenger
        </h3>
        <p class="challenger-subtitle">识别网络概念中的常见误解，纠正错误认知</p>
      </div>
      <div class="header-stats">
        <div class="stat-box">
          <span class="stat-num">{{ score }}</span>
          <span class="stat-label">正确</span>
        </div>
        <div class="stat-box">
          <span class="stat-num">{{ totalRounds - score }}</span>
          <span class="stat-label">错误</span>
        </div>
        <div class="stat-box">
          <span class="stat-num">{{ streak }}</span>
          <span class="stat-label">连胜</span>
        </div>
        <div class="stat-box">
          <span class="stat-num">{{ maxStreak }}</span>
          <span class="stat-label">最高连胜</span>
        </div>
      </div>
    </div>

    <!-- 进度条 -->
    <div class="progress-bar" v-if="!isFinished">
      <div class="progress-track">
        <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
      </div>
      <span class="progress-text">{{ currentIndex + 1 }} / {{ totalRounds }}</span>
    </div>

    <!-- 挑战内容 -->
    <div v-if="!isFinished" class="challenge-card">
      <!-- 主题标签 -->
      <div class="challenge-topic">
        <el-tag size="large" type="danger" effect="dark">
          <el-icon><Lightning /></el-icon>
          {{ currentRound.topic }}
        </el-tag>
        <span class="challenge-id">Challenge #{{ currentRound.id }}</span>
      </div>

      <!-- AI 陈述 -->
      <div class="challenge-statement">
        <div class="statement-label">
          <el-icon><ChatDotRound /></el-icon>
          Challenger 的陈述
        </div>
        <div class="statement-bubble">
          <p>{{ currentRound.statement }}</p>
        </div>
      </div>

      <!-- 用户判断区 -->
      <div v-if="!showResult" class="judgment-area">
        <p class="judgment-prompt">这个陈述是正确还是错误的？</p>
        <div class="judgment-buttons">
          <el-button
            size="large"
            :type="userJudgment === 'correct' ? 'success' : 'default'"
            @click="judge(true)"
          >
            <el-icon><CircleCheck /></el-icon>
            正确
          </el-button>
          <el-button
            size="large"
            :type="userJudgment === 'incorrect' ? 'danger' : 'default'"
            @click="judge(false)"
          >
            <el-icon><CircleClose /></el-icon>
            错误
          </el-button>
        </div>

        <!-- 解释输入 -->
        <div v-if="userJudgment === 'incorrect'" class="explanation-input">
          <el-alert type="info" :closable="false" class="mb-3">
            你认为这个陈述哪里错了？请用你自己的话简要说明。
          </el-alert>
          <el-input
            v-model="userExplanation"
            type="textarea"
            :rows="3"
            placeholder="输入你对该陈述错误的解释..."
            resize="none"
          />
        </div>

        <div v-if="userJudgment === 'correct' && !currentRound.isCorrect" class="explanation-input">
          <el-alert type="warning" :closable="false" class="mb-3">
            你选择了"正确"，请确认你真的认为这个陈述没有问题。
          </el-alert>
        </div>

        <el-button
          v-if="userJudgment"
          type="primary"
          size="large"
          class="submit-btn"
          @click="submitAnswer"
        >
          提交判断
        </el-button>
      </div>

      <!-- 结果反馈 -->
      <div v-else class="result-feedback">
        <el-divider />

        <div class="result-banner" :class="history[history.length - 1]?.correct ? 'success' : 'fail'">
          <el-icon size="32">
            <CircleCheck v-if="history[history.length - 1]?.correct" />
            <CircleClose v-else />
          </el-icon>
          <div class="result-text">
            <h4>{{ history[history.length - 1]?.correct ? '判断正确！' : '判断错误' }}</h4>
            <p v-if="!history[history.length - 1]?.correct">
              正确答案是：{{ currentRound.isCorrect ? '正确' : '错误' }}
            </p>
          </div>
        </div>

        <div class="truth-card">
          <h5><el-icon><InfoFilled /></el-icon> 常见误解</h5>
          <p>{{ currentRound.misconception }}</p>
        </div>

        <div class="truth-card truth">
          <h5><el-icon><Check /></el-icon> 事实真相</h5>
          <p>{{ currentRound.truth }}</p>
        </div>

        <div class="truth-card explanation">
          <h5><el-icon><Reading /></el-icon> 深度解析</h5>
          <p>{{ currentRound.explanation }}</p>
        </div>

        <div v-if="userExplanation" class="truth-card user-exp">
          <h5><el-icon><UserFilled /></el-icon> 你的解释</h5>
          <p>{{ userExplanation }}</p>
        </div>

        <el-button type="primary" size="large" class="next-btn" @click="nextRound">
          {{ currentIndex < totalRounds - 1 ? '下一题' : '查看总结' }}
          <el-icon class="ml-1"><ArrowRight /></el-icon>
        </el-button>
      </div>
    </div>

    <!-- 完成总结 -->
    <div v-else class="challenge-summary">
      <div class="summary-card">
        <el-icon size="48" color="#3b82f6"><Trophy /></el-icon>
        <h3>挑战完成！</h3>
        <div class="summary-score">
          <span class="score-num">{{ score }}</span>
          <span class="score-total">/ {{ totalRounds }}</span>
        </div>
        <p class="summary-rate">正确率 {{ Math.round((score / totalRounds) * 100) }}%</p>

        <div class="summary-details">
          <div class="summary-item">
            <span>最高连胜</span>
            <strong>{{ maxStreak }}</strong>
          </div>
          <div class="summary-item">
            <span>总题数</span>
            <strong>{{ totalRounds }}</strong>
          </div>
        </div>

        <!-- 每题回顾 -->
        <div class="history-list">
          <div
            v-for="item in history"
            :key="item.round"
            class="history-dot"
            :class="{ correct: item.correct }"
          >
            {{ item.round }}
          </div>
        </div>

        <el-button type="primary" size="large" @click="resetAll">
          <el-icon><RefreshRight /></el-icon>
          再来一轮
        </el-button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.challenger-panel {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.challenger-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 16px;
  padding: 16px 20px;
  background-color: #eff6ff;
  border-radius: 12px;
  border: 1px solid #bfdbfe;
}

.challenger-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 700;
  color: #1e40af;
  margin: 0;
}

.challenger-icon {
  color: #3b82f6;
}

.challenger-subtitle {
  font-size: 13px;
  color: #2563eb;
  margin: 4px 0 0;
}

.header-stats {
  display: flex;
  gap: 16px;
}

.stat-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 50px;
}

.stat-num {
  font-size: 22px;
  font-weight: 700;
  color: #1e293b;
}

.stat-label {
  font-size: 11px;
  color: #64748b;
}

/* 进度条 */
.progress-bar {
  display: flex;
  align-items: center;
  gap: 12px;
}

.progress-track {
  flex: 1;
  height: 6px;
  background-color: #e2e8f0;
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background-color: #3b82f6;
  border-radius: 3px;
  transition: width 0.4s ease;
}

.progress-text {
  font-size: 13px;
  color: #64748b;
  font-weight: 500;
  white-space: nowrap;
}

/* 挑战卡片 */
.challenge-card {
  background-color: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.challenge-topic {
  display: flex;
  align-items: center;
  gap: 12px;
}

.challenge-id {
  font-size: 13px;
  color: #94a3b8;
  font-weight: 500;
}

/* 陈述气泡 */
.challenge-statement {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.statement-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: #64748b;
}

.statement-bubble {
  background-color: #f1f5f9;
  border-left: 4px solid #3b82f6;
  border-radius: 0 10px 10px 0;
  padding: 18px 20px;
}

.statement-bubble p {
  margin: 0;
  font-size: 15px;
  line-height: 1.7;
  color: #1e293b;
}

/* 判断区 */
.judgment-area {
  display: flex;
  flex-direction: column;
  gap: 16px;
  align-items: center;
  padding: 8px 0;
}

.judgment-prompt {
  font-size: 15px;
  font-weight: 600;
  color: #334155;
  margin: 0;
}

.judgment-buttons {
  display: flex;
  gap: 16px;
}

.judgment-buttons .el-button {
  min-width: 140px;
  font-size: 15px;
}

.explanation-input {
  width: 100%;
  max-width: 600px;
}

.mb-3 {
  margin-bottom: 12px;
}

.submit-btn {
  min-width: 180px;
}

/* 结果反馈 */
.result-feedback {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.result-banner {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px 20px;
  border-radius: 10px;
}

.result-banner.success {
  background-color: #ecfdf5;
  border: 1px solid #a7f3d0;
  color: #059669;
}

.result-banner.fail {
  background-color: #fef2f2;
  border: 1px solid #fecaca;
  color: #dc2626;
}

.result-text h4 {
  margin: 0 0 4px;
  font-size: 16px;
}

.result-text p {
  margin: 0;
  font-size: 13px;
  opacity: 0.8;
}

.truth-card {
  padding: 14px 18px;
  border-radius: 8px;
  background-color: #f8fafc;
  border: 1px solid #e2e8f0;
}

.truth-card h5 {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: #64748b;
  margin: 0 0 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.truth-card p {
  margin: 0;
  font-size: 14px;
  line-height: 1.6;
  color: #334155;
}

.truth-card.truth {
  background-color: #ecfdf5;
  border-color: #a7f3d0;
}

.truth-card.truth h5 {
  color: #059669;
}

.truth-card.explanation {
  background-color: #eff6ff;
  border-color: #bfdbfe;
}

.truth-card.explanation h5 {
  color: #2563eb;
}

.truth-card.user-exp {
  background-color: #fdf4ff;
  border-color: #e9d5ff;
}

.truth-card.user-exp h5 {
  color: #7c3aed;
}

.next-btn {
  align-self: flex-end;
  min-width: 140px;
}

.ml-1 {
  margin-left: 4px;
}

/* 总结页 */
.challenge-summary {
  display: flex;
  justify-content: center;
  padding: 40px 0;
}

.summary-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  background-color: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  padding: 40px 48px;
  text-align: center;
  max-width: 420px;
  width: 100%;
}

.summary-card h3 {
  margin: 0;
  font-size: 20px;
  color: #1e293b;
}

.summary-score {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.score-num {
  font-size: 48px;
  font-weight: 800;
  color: #3b82f6;
}

.score-total {
  font-size: 24px;
  color: #94a3b8;
  font-weight: 600;
}

.summary-rate {
  margin: 0;
  font-size: 15px;
  color: #64748b;
}

.summary-details {
  display: flex;
  gap: 32px;
  padding: 16px 0;
  border-top: 1px solid #f1f5f9;
  border-bottom: 1px solid #f1f5f9;
  width: 100%;
  justify-content: center;
}

.summary-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.summary-item span {
  font-size: 12px;
  color: #94a3b8;
}

.summary-item strong {
  font-size: 20px;
  color: #1e293b;
}

.history-list {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: center;
}

.history-dot {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 600;
  background-color: #f1f5f9;
  color: #64748b;
}

.history-dot.correct {
  background-color: #d1fae5;
  color: #059669;
}

@media (max-width: 768px) {
  .challenger-header {
    flex-direction: column;
    align-items: flex-start;
  }
  .header-stats {
    width: 100%;
    justify-content: space-around;
  }
  .judgment-buttons {
    flex-direction: column;
    width: 100%;
  }
  .judgment-buttons .el-button {
    width: 100%;
  }
  .summary-card {
    padding: 32px 24px;
    margin: 0 12px;
  }
}
</style>
