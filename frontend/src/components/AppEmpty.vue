<script setup lang="ts">
interface Props {
  title?: string
  description?: string
  icon?: string
  actionText?: string
}

withDefaults(defineProps<Props>(), {
  title: '暂无数据',
  description: '当前没有可展示的内容',
  icon: 'Box',
  actionText: '',
})

const emit = defineEmits<{
  action: []
}>()

function handleAction() {
  emit('action')
}
</script>

<template>
  <div class="app-empty">
    <el-icon :size="64" class="empty-icon"><component :is="icon" /></el-icon>
    <h3 class="empty-title">{{ title }}</h3>
    <p class="empty-desc">{{ description }}</p>
    <el-button v-if="actionText" type="primary" plain @click="handleAction">
      {{ actionText }}
    </el-button>
    <slot />
  </div>
</template>

<style scoped>
.app-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
}

.empty-icon {
  color: #cbd5e1;
  margin-bottom: 16px;
}

.empty-title {
  font-size: 16px;
  font-weight: 500;
  color: #475569;
  margin-bottom: 8px;
}

.empty-desc {
  font-size: 14px;
  color: #94a3b8;
}
</style>
