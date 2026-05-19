<script setup lang="ts">
import { onMounted } from 'vue'
import AssistantWorkspace from '@/components/AssistantWorkspace.vue'
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
  <div class="chat-workspace">
    <div class="chat-main">
      <ChatPanel />
    </div>
    <aside class="chat-sidebar">
      <AssistantWorkspace />
    </aside>
  </div>
</template>

<style scoped>
.chat-workspace {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 360px;
  gap: 16px;
  align-items: start;
}

.chat-main,
.chat-sidebar {
  min-width: 0;
}

@media (max-width: 1200px) {
  .chat-workspace {
    grid-template-columns: 1fr;
  }
}
</style>
