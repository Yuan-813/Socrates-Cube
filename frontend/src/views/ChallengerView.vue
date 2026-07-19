<script setup lang="ts">
import ChallengerPanel from '@/components/ChallengerPanel.vue'
import ChallengerQuizCard from '@/components/ChallengerQuizCard.vue'
import { useChatStore } from '@/stores/chatStore'
import { computed } from 'vue'

const chatStore = useChatStore()
const hasActiveChallenge = computed(() =>
  chatStore.lastChallenger !== null && chatStore.lastChallenger?.status !== 'completed'
)
</script>

<template>
  <div class="space-y-5">
    <!-- 页面头部信息条 -->
    <div class="feature-header">
      <div class="feature-header-inner">
        <div class="feature-icon-wrap">
          <span class="feature-icon">⚡</span>
        </div>
        <div>
          <h2 class="feature-title">概念挑战者</h2>
          <p class="feature-desc">
            AI 主动挑战你对计算机网络概念的理解，通过判断陈述正误来识别并纠正常见误解
          </p>
        </div>
        <div class="feature-tips">
          <div class="tip-item">
            <span class="tip-dot tip-green"></span>
            <span>判断陈述正误</span>
          </div>
          <div class="tip-item">
            <span class="tip-dot tip-blue"></span>
            <span>分析误解原因</span>
          </div>
          <div class="tip-item">
            <span class="tip-dot tip-purple"></span>
            <span>固化正确认知</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 当前对话活跃的自适应检验题（若存在） -->
    <div v-if="hasActiveChallenge" class="card border-l-4 border-indigo-400">
      <div class="flex items-center gap-2 mb-3">
        <span class="text-sm font-semibold text-indigo-700">💬 对话驱动自适应检验</span>
        <el-tag size="small" type="warning" effect="plain">AI 根据诊断结果生成</el-tag>
      </div>
      <ChallengerQuizCard />
    </div>

    <!-- 标准模式：预设题库 -->
    <div class="card">
      <ChallengerPanel />
    </div>
  </div>
</template>

<style scoped>
.feature-header {
  background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
  border: 1px solid #fde68a;
  border-radius: 14px;
  padding: 20px 24px;
}
.feature-header-inner {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  flex-wrap: wrap;
}
.feature-icon-wrap {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #f59e0b, #ef4444);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 4px 12px rgba(245, 158, 11, 0.3);
}
.feature-icon { font-size: 22px; }
.feature-title {
  margin: 0 0 4px;
  font-size: 18px;
  font-weight: 700;
  color: #92400e;
}
.feature-desc {
  margin: 0;
  font-size: 13px;
  color: #b45309;
  line-height: 1.5;
  max-width: 500px;
}
.feature-tips {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-left: auto;
  flex-wrap: wrap;
}
.tip-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #78716c;
}
.tip-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.tip-green { background: #22c55e; }
.tip-blue { background: #3b82f6; }
.tip-purple { background: #8b5cf6; }
</style>
