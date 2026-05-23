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
  <div class="chat-full">
    <ChatPanel />
  </div>
</template>

<style scoped>
.chat-full {
  width: 100%;
  max-width: 900px;
  margin: 0 auto;
}
</style>
