<script setup lang="ts">
import { computed } from 'vue'
import { useAssistantStore } from '@/stores/assistantStore'

const assistantStore = useAssistantStore()

const topDimensions = computed(() => assistantStore.profile?.dimensions.slice(0, 4) || [])
const recentLogs = computed(() => assistantStore.logs.slice(0, 5))
const currentPathNode = computed(() => assistantStore.learningPath.find((item) => item.status === 'current') || null)
</script>

<template>
  <div class="workspace-panel">
    <div class="workspace-header">
      <div>
        <h3 class="workspace-title">联调工作台</h3>
        <p class="workspace-desc">实时查看画像、诊断、日志和仿真提示</p>
      </div>
      <el-tag :type="assistantStore.isMockMode ? 'warning' : 'success'" effect="light">
        {{ assistantStore.isMockMode ? 'Mock 模式' : 'Real 模式' }}
      </el-tag>
    </div>

    <div class="workspace-section">
      <div class="section-title-row">
        <span class="section-title">连接状态</span>
        <el-tag :type="assistantStore.connectionStatus === 'error' ? 'danger' : assistantStore.connectionStatus === 'streaming' ? 'primary' : 'info'" effect="light">
          {{ assistantStore.connectionStatus }}
        </el-tag>
      </div>
      <p class="section-text" v-if="assistantStore.lastError">{{ assistantStore.lastError }}</p>
      <p class="section-text" v-else>当前支持聊天主链路、联动摘要展示和 mock / real 切换。</p>
    </div>

    <div class="workspace-section">
      <div class="section-title-row">
        <span class="section-title">学习画像摘要</span>
        <span class="section-extra">{{ assistantStore.profile?.cognitiveStyle || 'textual' }}</span>
      </div>
      <div v-if="topDimensions.length" class="dimension-list">
        <div v-for="dimension in topDimensions" :key="dimension.name" class="dimension-item">
          <div class="dimension-meta">
            <span class="dimension-name">{{ dimension.label }}</span>
            <span class="dimension-level">Lv.{{ dimension.level }}</span>
          </div>
          <el-progress :percentage="dimension.level * 20" :show-text="false" :stroke-width="6" />
          <p class="dimension-desc">{{ dimension.description }}</p>
        </div>
      </div>
      <app-empty v-else description="等待对话后生成画像摘要" />
    </div>

    <div class="workspace-section">
      <div class="section-title-row">
        <span class="section-title">诊断结果</span>
        <el-tag v-if="assistantStore.diagnosis" type="danger" effect="light">{{ assistantStore.diagnosis.surfaceError }}</el-tag>
      </div>
      <template v-if="assistantStore.diagnosis">
        <p class="section-text"><strong>触发：</strong>{{ assistantStore.diagnosis.trigger }}</p>
        <p class="section-text"><strong>根因：</strong>{{ assistantStore.diagnosis.rootCause.weakKnowledge }}</p>
        <p class="section-text"><strong>模式：</strong>{{ assistantStore.diagnosis.misconceptionPattern }}</p>
      </template>
      <app-empty v-else description="等待诊断结果" />
    </div>

    <div class="workspace-section">
      <div class="section-title-row">
        <span class="section-title">Agent 日志</span>
        <span class="section-extra">{{ recentLogs.length }} 条</span>
      </div>
      <div v-if="recentLogs.length" class="log-list">
        <div v-for="log in recentLogs" :key="log.logId" class="log-item">
          <div class="log-head">
            <span class="log-agent">{{ log.agentName }}</span>
            <span class="log-time">{{ log.timestamp }}</span>
          </div>
          <div class="log-body">{{ log.action }} · {{ log.result }}</div>
        </div>
      </div>
      <app-empty v-else description="等待联调日志" />
    </div>

    <div class="workspace-section">
      <div class="section-title-row">
        <span class="section-title">学习路径与仿真</span>
      </div>
      <p class="section-text"><strong>当前节点：</strong>{{ currentPathNode?.title || '等待规划结果' }}</p>
      <p class="section-text"><strong>仿真提示：</strong>{{ assistantStore.simulatorSummary }}</p>
      <div class="resource-tags" v-if="assistantStore.resources.length">
        <el-tag v-for="resource in assistantStore.resources.slice(0, 4)" :key="resource.id" size="small" effect="plain">
          {{ resource.title }}
        </el-tag>
      </div>
    </div>
  </div>
</template>

<style scoped>
.workspace-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.workspace-header,
.workspace-section {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 14px;
}

.workspace-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.workspace-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #0f172a;
}

.workspace-desc {
  margin: 4px 0 0;
  font-size: 12px;
  color: #64748b;
}

.section-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 10px;
}

.section-title {
  font-size: 13px;
  font-weight: 600;
  color: #334155;
}

.section-extra {
  font-size: 12px;
  color: #94a3b8;
}

.section-text {
  margin: 0 0 8px;
  font-size: 13px;
  line-height: 1.6;
  color: #475569;
}

.dimension-list,
.log-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.dimension-item,
.log-item {
  border-radius: 10px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  padding: 10px;
}

.dimension-meta,
.log-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
}

.dimension-name,
.log-agent {
  font-size: 13px;
  font-weight: 600;
  color: #1e293b;
}

.dimension-level,
.log-time {
  font-size: 12px;
  color: #94a3b8;
}

.dimension-desc,
.log-body {
  margin: 8px 0 0;
  font-size: 12px;
  line-height: 1.5;
  color: #64748b;
}

.resource-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}
</style>
