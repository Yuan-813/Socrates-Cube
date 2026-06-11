<script setup lang="ts">
import { computed } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { RadarChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import { useUserStore } from '../stores/userStore'
import { PROFILE_DIMENSION_LABELS } from '../types'

use([CanvasRenderer, RadarChart, TitleComponent, TooltipComponent, LegendComponent])

const userStore = useUserStore()

const PROFILE_DIMS = [
  'layered_model_cognition',
  'protocol_flow_memory',
  'packet_format_understanding',
  'inter_protocol_relation',
  'fault_diagnosis_logic',
  'practical_operation',
  'cognitive_style',
  'misconception_pattern',
]

const dimensions = PROFILE_DIMS.map(k => ({
  name: PROFILE_DIMENSION_LABELS[k] ?? k,
  max: 100,
}))

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
    axisName: { color: '#475569', fontSize: 12 },
    splitArea: {
      areaStyle: {
        color: ['#f8fafc', '#f1f5f9', '#e2e8f0', '#cbd5e1', '#94a3b8'],
        shadowColor: 'rgba(0,0,0,0.1)',
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
          value: userStore.radarScores,
          name: '当前能力',
          areaStyle: { color: 'rgba(37,99,235,0.3)' },
          lineStyle: { color: '#2563eb', width: 2 },
          itemStyle: { color: '#2563eb' },
        },
        {
          value: [80, 85, 80, 85, 75, 80, 90, 90],
          name: '目标水平',
          lineStyle: { color: '#10b981', width: 2, type: 'dashed' },
          itemStyle: { color: '#10b981' },
        },
      ],
    },
  ],
}))

const dimensionDetails = computed(() =>
  PROFILE_DIMS.map((k, i) => ({
    name: PROFILE_DIMENSION_LABELS[k] ?? k,
    score: userStore.radarScores[i],
  }))
)

function getLevelColor(score: number): string {
  if (score >= 80) return '#22c55e'
  if (score >= 60) return '#84cc16'
  if (score >= 40) return '#eab308'
  if (score >= 20) return '#f97316'
  return '#ef4444'
}

function getLevelLabel(score: number): string {
  if (score >= 80) return '优秀'
  if (score >= 60) return '良好'
  if (score >= 40) return '中等'
  if (score >= 20) return '较差'
  return '薄弱'
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
            <el-tag :color="getLevelColor(dim.score)" effect="dark" size="small">
              {{ getLevelLabel(dim.score) }}
            </el-tag>
          </div>
          <el-progress
            :percentage="dim.score"
            :color="getLevelColor(dim.score)"
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
