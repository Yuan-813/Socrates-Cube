<script setup lang="ts">
import { computed, onMounted } from 'vue'
import ProfileRadar from '@/components/ProfileRadar.vue'
import { useAssistantStore } from '@/stores/assistantStore'
import { fetchProfile } from '@/api/profile'

const assistantStore = useAssistantStore()

onMounted(async () => {
  const profile = await fetchProfile('demo-user')
  if (profile) {
    assistantStore.setProfile(profile)
  }
})

const profileMeta = computed(() => {
  if (!assistantStore.profile) return null

  return {
    userId: assistantStore.profile.userId,
    cognitiveStyle: assistantStore.profile.cognitiveStyle,
    updatedAt: assistantStore.profile.updatedAt,
  }
})
</script>

<template>
  <div class="space-y-6">
    <div class="card">
      <h2 class="section-title">学生能力画像</h2>
      <p class="section-desc">基于对话交互自动构建的8维协议能力评估</p>
      <div v-if="profileMeta" class="profile-meta">
        <el-tag type="primary" effect="light">用户：{{ profileMeta.userId }}</el-tag>
        <el-tag type="success" effect="light">风格：{{ profileMeta.cognitiveStyle }}</el-tag>
        <span class="profile-time">最近更新：{{ profileMeta.updatedAt }}</span>
      </div>
      <ProfileRadar />
    </div>
  </div>
</template>

<style scoped>
.profile-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 16px;
}

.profile-time {
  font-size: 12px;
  color: #94a3b8;
}
</style>
