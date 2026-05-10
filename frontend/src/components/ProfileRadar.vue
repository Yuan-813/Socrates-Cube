<script setup lang="ts">
import { computed } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { RadarChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import { useAssistantStore } from '@/stores/assistantStore'

use([CanvasRenderer, RadarChart, TitleComponent, TooltipComponent, LegendComponent])

const assistantStore = useAssistantStore()

const dimensions = [
  { name: '网络分层认知', max: 100 },
  { name: '协议流程记忆', max: 100 },
  { name: '报文格式理解', max: 100 },
  { name: '协议间关系', max: 100 },
  { name: '故障排查逻辑', max: 100 },
  { name: '实践操作能力', max: 100 },
  { name: '认知风格偏好', max: 100 },
  { name: '常见误解模式', max: 100 },
]

const fallbackDimensionDetails = [
  { name: '网络分层认知', level: 2, desc: '对OSI七层/TCP/IP四层结构掌握度偏低，建议从分层封装动画入手' },
  { name: '协议流程记忆', level: 3, desc: '三次握手、四次挥手能背诵但理解不深入' },
  { name: '报文格式理解', level: 1, desc: '头部字段含义混淆，是连接管理薄弱的前置原因' },
  { name: '协议间关系', level: 3, desc: 'HTTP-TCP-IP依赖关系基本理解，但封装过程不清晰' },
  { name: '故障排查逻辑', level: 1, desc: '从现象定位根因的推理能力较弱，建议多做故障案例' },
  { name: '实践操作能力', level: 1, desc: 'Wireshark抓包和Socket编程经验不足' },
  { name: '认知风格偏好', level: 4, desc: '偏视觉型学习者，适合动画、图解类资源' },
  { name: '常见误解模式', level: 2, desc: '当前聚类为"层次穿越型"，需重点纠正分层概念' },
]

const dimensionDetails = computed(() => {
  const dimensionsFromStore = assistantStore.profile?.dimensions
  if (!dimensionsFromStore?.length) {
    return fallbackDimensionDetails
  }

  return dimensionsFromStore.map((item) => ({
    name: item.label,
    level: item.level,
    desc: item.description,
  }))
})

const radarOption = computed(() => ({
  tooltip: {},
  legend: {
    data: ['当前能力', '目标水平'],
    bottom: 0,
  },
  radar: {
    indicator: dimensions,
    radius: '65%',
    splitNumber: 5,
    axisName: {
      color: '#475569',
      fontSize: 12,
    },
    splitArea: {
      areaStyle: {
        color: ['#f8fafc', '#f1f5f9', '#e2e8f0', '#cbd5e1', '#94a3b8'],
        shadowColor: 'rgba(0, 0, 0, 0.1)',
        shadowBlur: 10,
      },
    },
  },
  series: [
    {
      name: '能力评估',
      type: 'radar',
      data: [
        {
          value: dimensionDetails.value.map((item) => item.level * 20),
          name: '当前能力',
          areaStyle: {
            color: 'rgba(37, 99, 235, 0.3)',
          },
          lineStyle: {
            color: '#2563eb',
            width: 2,
          },
          itemStyle: {
            color: '#2563eb',
          },
        },
        {
          value: [80, 85, 80, 85, 75, 80, 90, 90],
          name: '目标水平',
          lineStyle: {
            color: '#10b981',
            width: 2,
            type: 'dashed',
          },
          itemStyle: {
            color: '#10b981',
          },
        },
      ],
    },
  ],
}))

function getLevelColor(level: number): string {
  const colors = ['#ef4444', '#f97316', '#eab308', '#84cc16', '#22c55e']
  return colors[level - 1] || '#94a3b8'
}

function getLevelLabel(level: number): string {
  const labels = ['薄弱', '较差', '中等', '良好', '优秀']
  return labels[level - 1] || '未知'
}
</script>

<template>
  <div class="profile-radar">
    <div class="radar-chart">
      <v-chart class="chart" :option="radarOption" autoresize />
    </div>

    <div class="dimension-list">
      <h3 class="text-lg font-semibold text-slate-800 mb-4">维度详情</h3>
      <div class="space-y-3">
        <div
          v-for="dim in dimensionDetails"
          :key="dim.name"
          class="dimension-card"
        >
          <div class="flex items-center justify-between">
            <span class="font-medium text-slate-700">{{ dim.name }}</span>
            <el-tag :color="getLevelColor(dim.level)" effect="dark" size="small">
              {{ getLevelLabel(dim.level) }}
            </el-tag>
          </div>
          <p class="text-xs text-slate-500 mt-1">{{ dim.desc }}</p>
          <el-progress
            :percentage="dim.level * 20"
            :color="getLevelColor(dim.level)"
            :show-text="false"
            :stroke-width="4"
            class="mt-2"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.profile-radar {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 32px;
  align-items: start;
}

.radar-chart {
  background-color: #f8fafc;
  border-radius: 12px;
  padding: 16px;
}

.chart {
  width: 100%;
  height: 450px;
}

.dimension-list {
  max-height: 500px;
  overflow-y: auto;
  padding-right: 8px;
}

.dimension-card {
  background-color: #f8fafc;
  border-radius: 8px;
  padding: 12px;
  border: 1px solid #e2e8f0;
}

@media (max-width: 1024px) {
  .profile-radar {
    grid-template-columns: 1fr;
  }
  
  .chart {
    height: 350px;
  }
  
  .dimension-list {
    max-height: none;
  }
}

@media (max-width: 640px) {
  .chart {
    height: 300px;
    padding: 8px;
  }
  
  .radar-chart {
    padding: 8px;
  }
}
</style>
