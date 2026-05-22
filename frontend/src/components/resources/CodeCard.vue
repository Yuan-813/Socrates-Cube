<script setup lang="ts">
import { ref } from 'vue'
import type { CodeResource } from '@/types/resource'

defineProps<{ resource: CodeResource }>()
const copied = ref(false)

function copyCode(code: string) {
  navigator.clipboard.writeText(code).then(() => {
    copied.value = true
    setTimeout(() => copied.value = false, 1500)
  })
}
</script>

<template>
  <div class="resource-card code-card">
    <div class="card-header">
      <span class="card-icon">💻</span>
      <span class="card-title">{{ resource.title }}</span>
      <span class="lang-tag">{{ resource.language }}</span>
      <el-button link size="small" @click="copyCode(resource.code)">
        {{ copied ? '已复制' : '复制' }}
      </el-button>
    </div>
    <pre class="code-block"><code>{{ resource.code }}</code></pre>
    <p class="code-explanation">{{ resource.explanation }}</p>
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
  margin-bottom: 10px;
}
.card-title {
  font-weight: 600;
  flex: 1;
}
.lang-tag {
  font-size: 12px;
  color: #64748b;
  background: #f1f5f9;
  padding: 2px 8px;
  border-radius: 4px;
}
.code-block {
  background: #1e293b;
  color: #e2e8f0;
  padding: 14px;
  border-radius: 8px;
  overflow-x: auto;
  font-size: 13px;
  line-height: 1.6;
  margin: 0 0 10px;
}
.code-explanation {
  font-size: 13px;
  color: #475569;
  line-height: 1.6;
}
</style>
