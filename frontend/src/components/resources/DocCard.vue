<script setup lang="ts">
import { ref } from 'vue'
import type { DocResource } from '@/types/resource'

const props = defineProps<{ resource: DocResource }>()
const isExpanded = ref(true)
</script>

<template>
  <div class="resource-card doc-card">
    <div class="card-header">
      <span class="card-icon">📄</span>
      <span class="card-title">{{ resource.title }}</span>
      <span class="card-meta">{{ resource.reading_time }}分钟阅读</span>
      <el-button link size="small" @click="isExpanded = !isExpanded">
        {{ isExpanded ? '收起' : '展开' }}
      </el-button>
    </div>
    <div v-show="isExpanded" class="card-body">
      <div class="doc-content">{{ resource.content }}</div>
      <div v-if="resource.source_references?.length" class="doc-source">
        来源：{{ resource.source_references.join('、') }}
      </div>
    </div>
  </div>
</template>

<style scoped>
.resource-card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 14px;
}
.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.card-title {
  font-weight: 600;
  flex: 1;
}
.card-meta {
  font-size: 12px;
  color: #94a3b8;
}
.doc-content {
  font-size: 13px;
  line-height: 1.7;
  color: #475569;
  white-space: pre-wrap;
}
.doc-source {
  margin-top: 8px;
  font-size: 12px;
  color: #94a3b8;
}
</style>
