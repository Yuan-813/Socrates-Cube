<script setup lang="ts">
import { ref, onMounted } from 'vue'
import ChatPanel from '@/components/ChatPanel.vue'
import ResourceTabBar from '@/components/resources/ResourceTabBar.vue'
import PathTimeline from '@/components/path/PathTimeline.vue'
import ProfileRadar from '@/components/ProfileRadar.vue'
import AgentLogPanel from '@/components/AgentLogPanel.vue'
import { useChatStore } from '@/stores/chatStore'
import { useUserStore } from '@/stores/userStore'
import { usePathStore } from '@/stores/pathStore'

const chatStore = useChatStore()
const userStore = useUserStore()
const pathStore = usePathStore()

const rightTab = ref<'profile' | 'resources' | 'path' | 'logs'>('profile')

onMounted(() => {
  if (!chatStore.currentSession) {
    chatStore.createSession('新会话')
  }
  userStore.fetchProfile()
  pathStore.fetchPath()
})
</script>

<template>
  <div class="h-full flex gap-4">
    <!-- 左侧对话区 -->
    <div class="flex-1 min-w-0">
      <ChatPanel />
    </div>

    <!-- 右侧面板 -->
    <div class="w-80 shrink-0 flex flex-col gap-3">
      <!-- Tab 切换 -->
      <div class="flex gap-1 bg-gray-100 rounded-xl p-1">
        <button
          v-for="tab in [{ key: 'profile', label: '画像' }, { key: 'resources', label: '资源' }, { key: 'path', label: '路径' }, { key: 'logs', label: '日志' }]"
          :key="tab.key"
          class="flex-1 text-xs py-1 rounded-lg font-medium transition-all"
          :class="rightTab === tab.key ? 'bg-white shadow text-indigo-600' : 'text-gray-500 hover:text-gray-700'"
          @click="rightTab = (tab.key as typeof rightTab)"
        >
          {{ tab.label }}
        </button>
      </div>

      <!-- 内容区 -->
      <div class="flex-1 overflow-hidden">
        <ProfileRadar v-if="rightTab === 'profile'" />
        <ResourceTabBar v-else-if="rightTab === 'resources'" />
        <PathTimeline v-else-if="rightTab === 'path'" />
        <AgentLogPanel v-else />
      </div>
    </div>
  </div>
</template>
