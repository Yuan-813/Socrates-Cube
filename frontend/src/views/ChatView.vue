<script setup lang="ts">
import { onMounted, ref } from 'vue'
import AgentLogPanel from '@/components/AgentLogPanel.vue'
import AgentStatusBar from '@/components/AgentStatusBar.vue'
import ChatPanel from '@/components/ChatPanel.vue'
import PathTimeline from '@/components/path/PathTimeline.vue'
import ProfileRadar from '@/components/ProfileRadar.vue'
import ResourceTabBar from '@/components/resources/ResourceTabBar.vue'
import { useChatStore } from '@/stores/chatStore'
import { usePathStore } from '@/stores/pathStore'
import { useUserStore } from '@/stores/userStore'

const chatStore = useChatStore()
const userStore = useUserStore()
const pathStore = usePathStore()

const rightTab = ref<'profile' | 'resources' | 'path' | 'logs'>('profile')

onMounted(() => {
  if (!chatStore.currentSession) {
    chatStore.createSession('新会话')
  }
  userStore.fetchProfile()
  pathStore.fetchPath(userStore.userId)
})
</script>

<template>
  <div class="flex h-full gap-4">
    <div class="flex min-w-0 flex-1 flex-col gap-3">
      <AgentStatusBar />
      <ChatPanel />
    </div>

    <div class="flex w-80 shrink-0 flex-col gap-3">
      <div class="flex gap-1 rounded-lg bg-gray-100 p-1">
        <button
          v-for="tab in [
            { key: 'profile', label: '画像' },
            { key: 'resources', label: '资源' },
            { key: 'path', label: '路径' },
            { key: 'logs', label: '日志' },
          ]"
          :key="tab.key"
          class="flex-1 rounded-md py-1 text-xs font-medium transition-colors"
          :class="rightTab === tab.key ? 'bg-white text-sky-700 shadow-sm' : 'text-gray-500 hover:text-gray-700'"
          @click="rightTab = (tab.key as typeof rightTab)"
        >
          {{ tab.label }}
        </button>
      </div>

      <div class="min-h-0 flex-1 overflow-hidden">
        <ProfileRadar v-if="rightTab === 'profile'" />
        <ResourceTabBar v-else-if="rightTab === 'resources'" />
        <PathTimeline v-else-if="rightTab === 'path'" />
        <AgentLogPanel v-else />
      </div>
    </div>
  </div>
</template>
