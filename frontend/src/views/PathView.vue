<script setup lang="ts">
import { onMounted } from 'vue'
import PathTimeline from '@/components/path/PathTimeline.vue'
import PathReasonModal from '@/components/path/PathReasonModal.vue'
import { usePathStore } from '@/stores/pathStore'
import { useUserStore } from '@/stores/userStore'

const pathStore = usePathStore()
const userStore = useUserStore()

onMounted(() => {
  userStore.fetchProfile()
  pathStore.fetchPath()
})

function closeModal() {
  pathStore.selectNode(null as any)
}
</script>

<template>
  <div class="space-y-6">
    <div class="card">
      <div class="flex items-center justify-between mb-4">
        <div>
          <h2 class="section-title">可解释学习路径</h2>
          <p class="section-desc">基于知识图谱依赖关系与诊断结果动态规划的学习路线</p>
        </div>
        <div v-if="pathStore.path" class="text-right">
          <div class="text-2xl font-bold text-indigo-600">{{ pathStore.progressPercent }}%</div>
          <div class="text-xs text-gray-400">{{ pathStore.completedCount }}/{{ pathStore.totalCount }} 完成</div>
        </div>
      </div>
      <PathTimeline />
    </div>

    <!-- 节点详情弹窗 -->
    <PathReasonModal
      :node="pathStore.selectedNode"
      :visible="!!pathStore.selectedNode"
      @close="closeModal"
    />
  </div>
</template>
