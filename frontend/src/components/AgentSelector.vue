<script setup lang="ts">

interface AgentPersona {
  key: string
  name: string
  title: string
  avatar: string
  color: string
  lightBg: string
  glowColor: string
  desc: string
  traits: string[]
  model: string
}

defineProps<{ modelValue: string }>()
const emit = defineEmits<{
  (e: 'update:modelValue', val: string): void
  (e: 'change', persona: AgentPersona): void
}>()

const personas: AgentPersona[] = [
  {
    key: 'professor',
    name: '严教授',
    title: '网络领域权威',
    avatar: '👨‍🏫',
    color: '#6366f1',
    lightBg: '#eef2ff',
    glowColor: 'rgba(99,102,241,0.3)',
    desc: '严谨专业，从理论框架出发，引导你建立系统性知识体系',
    traits: ['理论深度', '框架清晰', '学术严谨'],
    model: 'Spark X',
  },
  {
    key: 'peer',
    name: '学长 Alex',
    title: '同龄学习伙伴',
    avatar: '🧑‍💻',
    color: '#0891b2',
    lightBg: '#ecfeff',
    glowColor: 'rgba(8,145,178,0.3)',
    desc: '口语化、类比丰富，把复杂概念变简单易懂',
    traits: ['轻松亲切', '类比生动', '互动讨论'],
    model: 'SkyClaw Lite',
  },
  {
    key: 'expert',
    name: '行业导师',
    title: '5年+ 工程师',
    avatar: '👩‍💼',
    color: '#059669',
    lightBg: '#ecfdf5',
    glowColor: 'rgba(5,150,105,0.3)',
    desc: '结合生产场景，给出可操作的工程实践建议',
    traits: ['实战导向', '直接高效', '场景丰富'],
    model: 'SkyClaw Pro',
  },
]

function select(p: AgentPersona) {
  emit('update:modelValue', p.key)
  emit('change', p)
}

function tooltipFor(p: AgentPersona) {
  return `${p.name} · ${p.desc}\n特质：${p.traits.join(' / ')}`
}
</script>

<template>
  <!--
    纯横排 chip 行：
    - 选中 chip → 展开，显示头像 + 名称 + 模型
    - 未选中 chip → 仅显示头像（悬停显示 tooltip）
    全程单行，不会撑高 persona-bar
  -->
  <div class="agent-chips" role="group" aria-label="选择 AI 助手人格">
    <button
      v-for="p in personas"
      :key="p.key"
      class="chip"
      :class="{ 'chip--on': modelValue === p.key }"
      :style="`--c: ${p.color}; --lbg: ${p.lightBg}; --glow: ${p.glowColor}`"
      :title="tooltipFor(p)"
      :aria-pressed="modelValue === p.key"
      @click="select(p)"
    >
      <!-- 头像 emoji -->
      <span class="chip-ava">{{ p.avatar }}</span>

      <!-- 仅选中时展开显示名称 + 模型 -->
      <Transition name="expand">
        <span v-if="modelValue === p.key" class="chip-meta">
          <span class="chip-name">{{ p.name }}</span>
          <span class="chip-model">{{ p.model }}</span>
        </span>
      </Transition>

      <!-- 选中脉冲点 -->
      <span v-if="modelValue === p.key" class="chip-dot"></span>
    </button>
  </div>
</template>

<style scoped>
/* ===========================
   Chip 行容器
=========================== */
.agent-chips {
  display: flex;
  align-items: center;
  gap: 4px;
}

/* ===========================
   单个 Chip
=========================== */
.chip {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 4px 8px;
  height: 32px;
  border-radius: 99px;
  border: 1.5px solid #e4e9f2;
  background: white;
  cursor: pointer;
  transition:
    background 0.22s,
    border-color 0.22s,
    box-shadow 0.22s,
    transform 0.18s;
  user-select: none;
  position: relative;
  white-space: nowrap;
  overflow: hidden;
}

/* 未选中 hover */
.chip:hover:not(.chip--on) {
  border-color: var(--c);
  background: var(--lbg);
  transform: translateY(-1px);
}

/* 选中态 */
.chip--on {
  background: var(--lbg);
  border-color: var(--c);
  box-shadow:
    0 0 0 3px var(--glow),
    0 2px 10px var(--glow);
  transform: none;
}

/* ===========================
   头像
=========================== */
.chip-ava {
  font-size: 16px;
  line-height: 1;
  flex-shrink: 0;
  transition: transform 0.2s;
}
.chip--on .chip-ava {
  transform: scale(1.1);
}

/* ===========================
   名称 + 模型（选中才显示）
=========================== */
.chip-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0;
  overflow: hidden;
}
.chip-name {
  font-size: 12px;
  font-weight: 700;
  color: var(--c);
  line-height: 1.3;
  white-space: nowrap;
}
.chip-model {
  font-size: 9px;
  font-weight: 600;
  color: var(--c);
  opacity: 0.7;
  line-height: 1.2;
  white-space: nowrap;
}

/* ===========================
   选中脉冲小圆点
=========================== */
.chip-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--c);
  flex-shrink: 0;
  animation: dotBreath 2.2s ease-in-out infinite;
}
@keyframes dotBreath {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(0.7); }
}

/* ===========================
   展开动画
=========================== */
.expand-enter-active {
  transition: all 0.28s cubic-bezier(0.34, 1.3, 0.64, 1);
  overflow: hidden;
}
.expand-leave-active {
  transition: all 0.16s ease;
  overflow: hidden;
}
.expand-enter-from {
  opacity: 0;
  max-width: 0;
  transform: translateX(-6px);
}
.expand-leave-to {
  opacity: 0;
  max-width: 0;
  transform: translateX(-4px);
}
.expand-enter-to,
.expand-leave-from {
  max-width: 120px;
  opacity: 1;
}
</style>
