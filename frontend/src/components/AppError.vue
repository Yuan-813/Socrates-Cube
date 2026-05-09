<script setup lang="ts">
interface Props {
  title?: string
  description?: string
}

withDefaults(defineProps<Props>(), {
  title: '出错了',
  description: '请求失败，请稍后重试',
})

const emit = defineEmits<{
  retry: []
}>()

function handleRetry() {
  emit('retry')
}
</script>

<template>
  <div class="app-error">
    <el-icon :size="64" class="error-icon"><WarningFilled /></el-icon>
    <h3 class="error-title">{{ title }}</h3>
    <p class="error-desc">{{ description }}</p>
    <el-button type="primary" @click="handleRetry">
      <el-icon class="mr-1"><Refresh /></el-icon>
      重新加载
    </el-button>
  </div>
</template>

<style scoped>
.app-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
}

.error-icon {
  color: #f87171;
  margin-bottom: 16px;
}

.error-title {
  font-size: 16px;
  font-weight: 500;
  color: #475569;
  margin-bottom: 8px;
}

.error-desc {
  font-size: 14px;
  color: #94a3b8;
  margin-bottom: 16px;
}

.mr-1 {
  margin-right: 4px;
}
</style>
