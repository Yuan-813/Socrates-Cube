<script setup lang="ts">
import { computed, ref } from 'vue'
import { useAssistantStore } from '@/stores/assistantStore'

const assistantStore = useAssistantStore()
const resources = computed(() => assistantStore.resources)

const filterType = ref('')

const typeIcons: Record<string, string> = {
  document: 'Document',
  mindmap: 'Share',
  quiz: 'EditPen',
  code: 'Code',
  video: 'VideoPlay',
}

const typeLabels: Record<string, string> = {
  document: '讲解文档',
  mindmap: '思维导图',
  quiz: '练习题',
  code: '代码案例',
  video: '视频/动画',
}

const typeColors: Record<string, string> = {
  document: '#3b82f6',
  mindmap: '#8b5cf6',
  quiz: '#f59e0b',
  code: '#10b981',
  video: '#ef4444',
}

const filteredResources = computed(() => {
  if (!filterType.value) return resources.value
  return resources.value.filter((r) => r.type === filterType.value)
})
</script>

<template>
  <div class="resource-cards">
    <!-- 筛选栏 -->
    <div class="resource-filters">
      <div class="filter-left">
        <el-radio-group v-model="filterType" size="small">
          <el-radio-button value="">全部</el-radio-button>
          <el-radio-button v-for="type in Object.keys(typeLabels)" :key="type" :value="type">
            {{ typeLabels[type] }}
          </el-radio-button>
        </el-radio-group>
      </div>
      <div class="filter-count">
        共 {{ filteredResources.length }} 个资源
      </div>
    </div>

    <!-- 资源网格 -->
    <div v-if="filteredResources.length" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div
        v-for="res in filteredResources"
        :key="res.id"
        class="resource-card"
      >
        <div class="resource-header">
          <div
            class="resource-icon"
            :style="{ backgroundColor: typeColors[res.type] + '20', color: typeColors[res.type] }"
          >
            <el-icon size="20"><component :is="typeIcons[res.type]" /></el-icon>
          </div>
          <div class="resource-meta">
            <div class="resource-type" :style="{ color: typeColors[res.type] }">
              {{ typeLabels[res.type] }}
            </div>
            <div class="resource-difficulty">
              <el-rate :model-value="res.difficulty" :max="5" disabled show-score text-color="#94a3b8" />
            </div>
          </div>
        </div>

        <h4 class="resource-title">{{ res.title }}</h4>
        <p class="resource-desc">{{ res.content }}</p>

        <div class="resource-tags">
          <el-tag v-for="tag in res.tags" :key="tag" size="small" type="info">
            {{ tag }}
          </el-tag>
        </div>

        <div class="resource-actions">
          <el-button type="primary" size="small" text>
            <el-icon class="mr-1"><View /></el-icon>
            查看
          </el-button>
          <el-button size="small" text>
            <el-icon class="mr-1"><Star /></el-icon>
            收藏
          </el-button>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else class="resource-empty">
      <AppEmpty
        title="暂无联动资源"
        description="先去聊天页发起一次对话，系统会同步资源推荐结果"
        icon="Filter"
      />
    </div>
  </div>
</template>

<style scoped>
.resource-filters {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  padding: 8px 0;
  margin-bottom: 16px;
}

.filter-left {
  overflow-x: auto;
  padding-bottom: 4px;
}

.filter-count {
  font-size: 13px;
  color: #94a3b8;
  white-space: nowrap;
}

.resource-empty {
  padding: 40px 0;
}

.resource-card {
  background-color: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 20px;
  transition: all 0.2s;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.resource-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  border-color: #cbd5e1;
}

.resource-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.resource-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.resource-meta {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.resource-type {
  font-size: 12px;
  font-weight: 500;
}

.resource-difficulty :deep(.el-rate__icon) {
  font-size: 12px;
  margin-right: 2px;
}

.resource-title {
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
  line-height: 1.4;
}

.resource-desc {
  font-size: 13px;
  color: #64748b;
  line-height: 1.5;
  flex: 1;
}

.resource-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.resource-actions {
  display: flex;
  gap: 8px;
  padding-top: 8px;
  border-top: 1px solid #f1f5f9;
}

.mr-1 {
  margin-right: 4px;
}
</style>
