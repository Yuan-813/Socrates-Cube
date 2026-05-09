<script setup lang="ts">
import { onMounted } from 'vue'
import ChatPanel from '@/components/ChatPanel.vue'
import { useChatStore } from '@/stores/chatStore'

const chatStore = useChatStore()

onMounted(() => {
  if (!chatStore.currentSession) {
    chatStore.createSession('新会话')
  }
})
</script>

<template>
  <div class="h-full">
    <ChatPanel />
  </div>
</template>
