<script setup lang="ts">
interface Props {
  title?: string
  description?: string
}

withDefaults(defineProps<Props>(), {
  title: '超出服务范围',
  description: '本系统专注于计算机网络协议学习，暂不支持此领域的问题。',
})
</script>

<template>
  <div class="scope-notice">
    <el-icon :size="20" class="scope-icon"><InfoFilled /></el-icon>
    <div class="scope-body">
      <span class="scope-title">{{ title }}</span>
      <span class="scope-desc">{{ description }}</span>
    </div>
  </div>
</template>

<style scoped>
.scope-notice {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px 16px;
  background-color: #fef3c7;
  border: 1px solid #fde68a;
  border-radius: 10px;
  margin: 8px 0;
}

.scope-icon {
  color: #f59e0b;
  flex-shrink: 0;
  margin-top: 1px;
}

.scope-body {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.scope-title {
  font-size: 13px;
  font-weight: 600;
  color: #92400e;
}

.scope-desc {
  font-size: 12px;
  color: #b45309;
}
</style>
