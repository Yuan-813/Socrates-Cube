<script setup lang="ts">
import { computed } from 'vue'
import { useAssistantStore } from '@/stores/assistantStore'

const assistantStore = useAssistantStore()
const pathNodes = computed(() => assistantStore.learningPath)

const statusConfig = {
  completed: { color: '#10b981', icon: 'Check', label: '已完成' },
  current: { color: '#3b82f6', icon: 'Loading', label: '进行中' },
  locked: { color: '#94a3b8', icon: 'Lock', label: '待解锁' },
}
</script>

<template>
  <div v-if="pathNodes.length" class="path-timeline">
    <div class="timeline-container">
      <div
        v-for="(node, index) in pathNodes"
        :key="node.id"
        class="timeline-item"
        :class="node.status"
      >
        <!-- 时间线连接 -->
        <div class="timeline-connector" v-if="index !== pathNodes.length - 1"></div>
        
        <!-- 节点图标 -->
        <div
          class="timeline-dot"
          :style="{ backgroundColor: statusConfig[node.status].color + '20', borderColor: statusConfig[node.status].color }"
        >
          <el-icon :size="18" :color="statusConfig[node.status].color">
            <component :is="statusConfig[node.status].icon" />
          </el-icon>
        </div>

        <!-- 节点内容 -->
        <div class="timeline-content">
          <div class="node-header">
            <h4 class="node-title">{{ node.title }}</h4>
            <el-tag 
              :type="node.status === 'completed' ? 'success' : node.status === 'current' ? 'primary' : 'info'"
              size="small" 
              :effect="node.status === 'locked' ? 'plain' : 'light'"
            >
              {{ statusConfig[node.status].label }}
            </el-tag>
          </div>
          <div class="node-meta">
            <span class="text-sm text-slate-500">
              <el-icon class="mr-1"><Timer /></el-icon>
              预计 {{ node.estimatedTime }} 分钟
            </span>
          </div>
          <div v-if="node.reason" class="node-reason">
            <el-icon color="#3b82f6" class="mt-1"><InfoFilled /></el-icon>
            <span class="text-sm text-slate-600">{{ node.reason }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 路径统计 -->
    <div class="path-stats">
      <div class="stat-item">
        <div class="stat-value">{{ pathNodes.filter(n => n.status === 'completed').length }}</div>
        <div class="stat-label">已完成</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">{{ pathNodes.filter(n => n.status === 'current').length }}</div>
        <div class="stat-label">进行中</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">{{ pathNodes.filter(n => n.status === 'locked').length }}</div>
        <div class="stat-label">待解锁</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">
          {{ Math.round((pathNodes.filter(n => n.status === 'completed').length / pathNodes.length) * 100) }}%
        </div>
        <div class="stat-label">总进度</div>
      </div>
    </div>
  </div>
  <app-empty v-else description="等待对话后生成学习路径建议" />
</template>

<style scoped>
.path-timeline {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.timeline-container {
  position: relative;
  padding-left: 24px;
}

.timeline-item {
  position: relative;
  padding-bottom: 32px;
  display: flex;
  gap: 16px;
}

.timeline-item:last-child {
  padding-bottom: 0;
}

.timeline-connector {
  position: absolute;
  left: 19px;
  top: 40px;
  width: 2px;
  height: calc(100% - 40px);
  background-color: #e2e8f0;
}

.timeline-item.completed .timeline-connector {
  background-color: #10b981;
}

.timeline-dot {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid;
  flex-shrink: 0;
  background-color: #fff;
}

.timeline-content {
  flex: 1;
  background-color: #f8fafc;
  border-radius: 10px;
  padding: 16px;
  border: 1px solid #e2e8f0;
}

.timeline-item.current .timeline-content {
  border-color: #3b82f6;
  background-color: #eff6ff;
}

.node-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.node-title {
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
}

.node-meta {
  margin-bottom: 8px;
}

.node-reason {
  display: flex;
  align-items: flex-start;
  gap: 4px;
  padding: 8px 12px;
  background-color: #fff;
  border-radius: 6px;
  border-left: 3px solid #3b82f6;
}

.path-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.stat-item {
  background-color: #f8fafc;
  border-radius: 10px;
  padding: 16px;
  text-align: center;
  border: 1px solid #e2e8f0;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #1e293b;
}

.stat-label {
  font-size: 12px;
  color: #64748b;
  margin-top: 4px;
}

.mr-1 {
  margin-right: 4px;
}

@media (max-width: 640px) {
  .path-stats {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
