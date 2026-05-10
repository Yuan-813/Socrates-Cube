<script setup lang="ts">
import { computed } from 'vue'
import { useAssistantStore } from '@/stores/assistantStore'

const assistantStore = useAssistantStore()
const diagnosis = computed(() => assistantStore.diagnosis)

const layers = [
  { name: '应用层', desc: 'HTTP / FTP / DNS', color: '#f59e0b' },
  { name: '传输层', desc: 'TCP / UDP', color: '#3b82f6' },
  { name: '网络层', desc: 'IP / ICMP', color: '#10b981' },
  { name: '数据链路层', desc: 'Ethernet / PPP', color: '#8b5cf6' },
]
</script>

<template>
  <div v-if="diagnosis" class="diagnosis-panel space-y-6">
    <!-- 触发信息 -->
    <div class="diagnosis-section">
      <div class="section-header">
        <el-icon size="20" class="text-amber-500"><Warning /></el-icon>
        <span class="font-semibold text-slate-800">诊断触发</span>
      </div>
      <div class="section-body bg-amber-50 border-amber-200">
        <p class="text-slate-700">{{ diagnosis.trigger }}</p>
      </div>
    </div>

    <!-- 三层诊断 -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <!-- 第一层：表面错误 -->
      <div class="diagnosis-card layer-1">
        <div class="card-header">
          <div class="layer-badge">第一层</div>
          <span class="font-medium text-slate-800">表面错误识别</span>
        </div>
        <div class="card-body">
          <el-tag type="danger" size="large" effect="dark">
            {{ diagnosis.surfaceError }}
          </el-tag>
          <p class="text-sm text-slate-600 mt-3">
            系统识别出学生在回答中存在明显的协议层次概念混淆。
          </p>
        </div>
      </div>

      <!-- 第二层：根因溯源 -->
      <div class="diagnosis-card layer-2">
        <div class="card-header">
          <div class="layer-badge">第二层</div>
          <span class="font-medium text-slate-800">根因溯源分析</span>
        </div>
        <div class="card-body">
          <div class="mb-3">
            <span class="text-sm text-slate-500">薄弱知识点：</span>
            <div class="font-semibold text-slate-800 mt-1">{{ diagnosis.rootCause.weakKnowledge }}</div>
          </div>
          <div class="mb-3">
            <span class="text-sm text-slate-500">置信度：</span>
            <el-progress :percentage="Math.round(diagnosis.rootCause.confidence * 100)" :color="'#3b82f6'" />
          </div>
          <div>
            <span class="text-sm text-slate-500">证据来源：</span>
            <div class="flex flex-wrap gap-2 mt-2">
              <el-tag v-for="ev in diagnosis.rootCause.evidence" :key="ev" size="small" type="info">
                {{ ev }}
              </el-tag>
            </div>
          </div>
        </div>
      </div>

      <!-- 第三层：模式匹配 -->
      <div class="diagnosis-card layer-3">
        <div class="card-header">
          <div class="layer-badge">第三层</div>
          <span class="font-medium text-slate-800">误解模式匹配</span>
        </div>
        <div class="card-body">
          <el-tag type="warning" size="large" effect="dark">
            {{ diagnosis.misconceptionPattern }}
          </el-tag>
          <p class="text-sm text-slate-600 mt-3">
            该学生倾向于跳过中间层直接思考，属于典型的"层次穿越型"误解模式。
          </p>
          <div class="mt-4">
            <span class="text-sm text-slate-500">推荐资源类型：</span>
            <div class="flex flex-wrap gap-2 mt-2">
              <el-tag v-for="res in diagnosis.suggestedResourceTypes" :key="res" size="small" type="success">
                {{ res }}
              </el-tag>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 协议分层可视化 -->
    <div class="protocol-stack-visual">
      <h3 class="font-semibold text-slate-800 mb-4">TCP/IP 分层结构示意</h3>
      <div class="stack-container">
        <div
          v-for="layer in layers"
          :key="layer.name"
          class="stack-layer"
          :style="{ borderLeftColor: layer.color }"
        >
          <div class="layer-name" :style="{ color: layer.color }">{{ layer.name }}</div>
          <div class="layer-desc">{{ layer.desc }}</div>
        </div>
      </div>
      <div class="stack-arrow">
        <el-icon size="24" color="#64748b"><Bottom /></el-icon>
        <span class="text-sm text-slate-500">数据封装方向（自上而下）</span>
      </div>
    </div>
  </div>
  <app-empty v-else description="等待对话后生成认知诊断结果" />
</template>

<style scoped>
.diagnosis-section {
  background-color: #fff;
  border-radius: 12px;
  padding: 16px;
  border: 1px solid #e2e8f0;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.section-body {
  padding: 12px 16px;
  border-radius: 8px;
  border: 1px solid;
}

.diagnosis-card {
  background-color: #fff;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  overflow: hidden;
}

.card-header {
  padding: 12px 16px;
  background-color: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.layer-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 4px;
  background-color: #e2e8f0;
  color: #475569;
}

.card-body {
  padding: 16px;
}

.protocol-stack-visual {
  background-color: #fff;
  border-radius: 12px;
  padding: 24px;
  border: 1px solid #e2e8f0;
}

.stack-container {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.stack-layer {
  display: flex;
  align-items: center;
  padding: 14px 20px;
  background-color: #f8fafc;
  border-radius: 8px;
  border-left: 4px solid;
}

.layer-name {
  font-weight: 600;
  font-size: 15px;
  min-width: 100px;
}

.layer-desc {
  color: #64748b;
  font-size: 13px;
}

@media (max-width: 768px) {
  .grid-cols-3 {
    grid-template-columns: 1fr;
  }
  
  .stack-layer {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
  
  .layer-name {
    min-width: auto;
  }
}

.stack-arrow {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed #e2e8f0;
}
</style>
