<template>
  <!-- 方案一：明亮 AI 知识星图 · Bright AI Glass -->
  <div class="min-h-screen bg-[#EEF2FF] p-4 space-y-4">

    <!-- Toast 通知 -->
    <Teleport to="body">
      <Transition name="toast">
        <div v-if="toastMsg"
          class="fixed top-6 left-1/2 -translate-x-1/2 z-[100] bg-gray-900 text-white text-sm font-medium px-5 py-2.5 rounded-full shadow-2xl flex items-center gap-2">
          <span>{{ toastMsg }}</span>
        </div>
      </Transition>
    </Teleport>

    <!-- ① 顶部 Hero Banner -->
    <div class="bg-white rounded-2xl p-5 shadow-sm border border-blue-50">
      <div class="flex flex-wrap items-start gap-5">

        <!-- 左侧：标题 + 统计栏 -->
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2 mb-1">
            <span class="text-xs font-semibold text-blue-500 bg-blue-50 px-2 py-0.5 rounded-full">AI Path Planner</span>
            <span class="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
            <span class="text-[10px] text-gray-400">实时规划中</span>
          </div>
          <h1 class="text-2xl font-bold text-gray-900">你的个性化学习路径</h1>
          <p class="text-sm text-gray-400 mt-0.5">基于知识图谱与能力模型，AI 为你规划的最优学习路线</p>
          <!-- 可点击 4 stat chips -->
          <div class="flex flex-wrap gap-4 mt-4">
            <button v-for="stat in statsChips" :key="stat.label"
              class="flex items-center gap-2 hover:opacity-80 transition-opacity group"
              :title="stat.tip"
              @click="stat.action()">
              <span class="w-7 h-7 rounded-full flex items-center justify-center text-sm group-hover:scale-110 transition-transform"
                :class="stat.bg">{{ stat.icon }}</span>
              <div class="text-left">
                <div class="text-[10px] text-gray-400 leading-3">{{ stat.label }}</div>
                <div class="text-xs font-semibold text-gray-700 leading-4">{{ stat.value }}</div>
              </div>
            </button>
          </div>
        </div>

        <!-- 中：装饰插图 -->
        <div class="hidden lg:flex items-center justify-center w-28 h-24 rounded-2xl bg-gradient-to-br from-blue-100 via-indigo-50 to-purple-100 text-4xl select-none">
          🗺️
        </div>

        <!-- 右：环形进度 + 动态提示卡 -->
        <div class="flex items-start gap-4 shrink-0">
          <!-- 环形进度 -->
          <div class="flex flex-col items-center">
            <svg width="100" height="100" viewBox="0 0 100 100" class="cursor-pointer hover:opacity-90 transition-opacity" @click="goToProfile">
              <circle cx="50" cy="50" r="42" fill="none" stroke="#E0E7FF" stroke-width="9"/>
              <circle cx="50" cy="50" r="42" fill="none"
                stroke="url(#s1grad1)" stroke-width="9"
                stroke-linecap="round"
                :stroke-dasharray="`${2 * Math.PI * 42}`"
                :stroke-dashoffset="`${2 * Math.PI * 42 * (1 - pathStore.progressPercent / 100)}`"
                transform="rotate(-90 50 50)"
                class="transition-all duration-1000"
              />
              <defs>
                <linearGradient id="s1grad1" x1="0" y1="0" x2="1" y2="1">
                  <stop offset="0" stop-color="#6366F1"/>
                  <stop offset="1" stop-color="#2563EB"/>
                </linearGradient>
              </defs>
              <text x="50" y="46" text-anchor="middle" font-size="18" font-weight="700" fill="#2563EB">{{ pathStore.progressPercent }}%</text>
              <text x="50" y="60" text-anchor="middle" font-size="9" fill="#9CA3AF">点击查看画像</text>
            </svg>
          </div>
          <!-- 动态提示卡 -->
          <div class="w-44 bg-blue-50 border border-blue-100 rounded-xl p-3">
            <div class="flex items-center gap-1.5 mb-1.5">
              <span class="w-1.5 h-1.5 bg-blue-400 rounded-full animate-pulse"></span>
              <span class="text-xs font-semibold text-blue-600">路径动态调整中</span>
            </div>
            <p class="text-[11px] text-gray-600 leading-[1.6]">AI 正在根据你的学习表现和理解情况，实时优化后续学习内容。</p>
            <div class="mt-2 pt-2 border-t border-blue-100 text-[10px] text-gray-400 space-y-0.5">
              <div>最近更新：2 分钟前</div>
              <button class="flex items-center gap-1 hover:text-blue-500 transition-colors group" @click="goToDiagnosis">
                <span class="w-1.5 h-1.5 bg-green-400 rounded-full"></span>
                <span class="group-hover:underline">规划引擎：Path Planner Agent →</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ② 主区：知识图谱 + Alice AI 卡 -->
    <div class="grid grid-cols-1 lg:grid-cols-5 gap-4">

      <!-- 知识图谱 (3/5) -->
      <div class="lg:col-span-3 bg-white rounded-2xl shadow-sm border border-slate-100 p-4">
        <div class="flex items-center justify-between mb-3">
          <div class="flex items-center gap-2">
            <h2 class="font-semibold text-gray-800">知识图谱学习地图</h2>
            <span class="text-[11px] text-gray-400 cursor-default select-none">❓</span>
          </div>
          <div class="flex items-center gap-3 text-[10px] text-gray-500">
            <span class="flex items-center gap-1"><span class="w-2.5 h-2.5 bg-emerald-400 rounded-full inline-block"></span>已掌握</span>
            <span class="flex items-center gap-1"><span class="w-2.5 h-2.5 bg-blue-500 rounded-full inline-block ring-2 ring-blue-200"></span>学习中</span>
            <span class="flex items-center gap-1"><span class="w-2.5 h-2.5 bg-gray-200 rounded-full inline-block border border-gray-300"></span>未解锁</span>
          </div>
        </div>

        <!-- SVG 图谱 -->
        <div class="overflow-auto rounded-xl bg-gradient-to-br from-slate-50 to-blue-50 p-2">
          <svg :width="SVG_W" :height="SVG_H" class="mx-auto block">
            <defs>
              <marker id="s1arrow" markerWidth="6" markerHeight="4" refX="5" refY="2" orient="auto">
                <polygon points="0 0, 6 2, 0 4" fill="#CBD5E1"/>
              </marker>
              <marker id="s1arrowGreen" markerWidth="6" markerHeight="4" refX="5" refY="2" orient="auto">
                <polygon points="0 0, 6 2, 0 4" fill="#6EE7B7"/>
              </marker>
              <filter id="s1glow">
                <feGaussianBlur stdDeviation="3" result="blur"/>
                <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
              </filter>
              <filter id="s1selectedGlow">
                <feGaussianBlur stdDeviation="5" result="blur"/>
                <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
              </filter>
            </defs>

            <!-- 连接线 -->
            <path v-for="(conn, i) in connections" :key="`conn${i}`"
              :d="conn.d" fill="none"
              :stroke="conn.done ? '#6EE7B7' : '#E2E8F0'"
              stroke-width="2"
              :marker-end="conn.done ? 'url(#s1arrowGreen)' : 'url(#s1arrow)'"
            />

            <!-- 节点 -->
            <g v-for="pos in nodePositions" :key="pos.node.node_id"
              :transform="`translate(${pos.x},${pos.y})`"
              class="cursor-pointer"
              @click="selectNode(pos.node)"
            >
              <!-- 选中节点外框高亮 -->
              <circle v-if="selectedNode?.node_id === pos.node.node_id"
                :r="NODE_R + 12" fill="none" stroke="#2563EB" stroke-width="2.5"
                stroke-dasharray="5 3" opacity="0.7" filter="url(#s1selectedGlow)"
                class="s1-selected-ring"
              />

              <!-- 刚完成节点绿色闪光 -->
              <circle v-if="justCompleted === pos.node.node_id"
                :r="NODE_R + 16" fill="none" stroke="#10B981" stroke-width="4"
                opacity="0.5" class="s1-complete-flash"
              />

              <!-- 进行中节点呼吸光晕 -->
              <circle v-if="pos.node.status === 'in_progress'"
                :r="NODE_R + 14" fill="none" stroke="#93C5FD" stroke-width="6" opacity="0.25"
                class="s1-pulse"
              />
              <circle v-if="pos.node.status === 'in_progress'"
                :r="NODE_R + 6" fill="none" stroke="#60A5FA" stroke-width="3" opacity="0.35"
                class="s1-pulse" style="animation-delay:0.3s"
              />

              <!-- 主圆 -->
              <circle :r="NODE_R"
                :fill="ns(pos.node.status).bg"
                :stroke="ns(pos.node.status).border"
                :stroke-width="pos.node.status === 'in_progress' ? 3 : selectedNode?.node_id === pos.node.node_id ? 2.5 : 2"
                :filter="pos.node.status !== 'locked' ? 'url(#s1glow)' : 'none'"
              />

              <!-- 掌握度弧 -->
              <circle v-if="pos.node.status !== 'locked'"
                :r="NODE_R - 6" fill="none"
                :stroke="pos.node.status === 'completed' ? '#34D399' : '#60A5FA'"
                stroke-width="3" stroke-linecap="round"
                :stroke-dasharray="`${2*Math.PI*(NODE_R-6)}`"
                :stroke-dashoffset="`${2*Math.PI*(NODE_R-6)*(1-pos.node.current_mastery)}`"
                transform="rotate(-90)"
                opacity="0.7"
              />

              <!-- 图标 / 百分比 -->
              <text text-anchor="middle" :y="pos.node.status === 'locked' ? '6' : '-5'"
                font-size="15" :fill="pos.node.status === 'locked' ? '#9CA3AF' : ns(pos.node.status).text">
                {{ pos.node.status === 'locked' ? '🔒' : pos.node.status === 'completed' ? '✓' : '▶' }}
              </text>
              <text v-if="pos.node.status !== 'locked'"
                text-anchor="middle" y="11" font-size="11" font-weight="700"
                :fill="ns(pos.node.status).text">
                {{ pct(pos.node.current_mastery) }}%
              </text>

              <!-- 节点名标签 -->
              <text text-anchor="middle" y="52" font-size="11" fill="#374151" font-weight="500">
                {{ trunc(pos.node.node_name, 7) }}
              </text>

              <!-- 当前学习 Badge -->
              <g v-if="pos.node.status === 'in_progress'">
                <rect x="-22" y="59" width="44" height="15" rx="7" fill="#2563EB"/>
                <text text-anchor="middle" y="70" font-size="9" fill="white">当前学习</text>
              </g>
              <!-- 目标 Badge -->
              <g v-else-if="pos.node.is_target">
                <rect x="-16" y="59" width="32" height="13" rx="6" fill="#E0E7FF"/>
                <text text-anchor="middle" y="69" font-size="8" fill="#4338CA">目标</text>
              </g>
            </g>
          </svg>
        </div>

        <!-- 空/加载态 -->
        <div v-if="!pathStore.path" class="flex flex-col items-center justify-center py-8 text-gray-300 text-sm gap-2">
          <div v-if="pathStore.loading" class="text-3xl animate-spin">⌁</div>
          <div v-else class="text-3xl">⌁</div>
          <p>{{ pathStore.loading ? '学习路径加载中…' : '暂无路径数据' }}</p>
          <button v-if="!pathStore.loading" class="mt-1 text-xs text-blue-500 hover:underline" @click="goToDiagnosis">
            完成智能诊断后自动规划 →
          </button>
        </div>
      </div>

      <!-- Alice AI 解释卡 (2/5) -->
      <div class="lg:col-span-2 bg-white rounded-2xl shadow-sm border border-purple-50 p-4 flex flex-col gap-3">
        <div class="flex items-center gap-2">
          <span class="text-lg">🤖</span>
          <span class="font-semibold text-gray-800">Alice AI 解释</span>
          <span class="text-[10px] bg-purple-50 text-purple-500 px-2 py-0.5 rounded-full ml-auto">实时分析</span>
        </div>

        <template v-if="currentNode">
          <div class="bg-blue-50 rounded-xl p-3">
            <p class="text-xs font-semibold text-blue-600 mb-1">为什么先学 {{ currentNode.node_name }}？</p>
            <p class="text-xs text-gray-700 leading-[1.7]">{{ currentNode.recommendation_reason }}</p>
          </div>

          <div class="text-xs text-gray-600 space-y-1.5">
            <p class="font-medium text-gray-700">通过分析你的能力画像，AI 发现：</p>
            <div v-if="currentNode.reason_sources?.graph_dependency" class="flex items-start gap-1.5">
              <span class="mt-1 w-1.5 h-1.5 bg-blue-400 rounded-full shrink-0"></span>
              <span>{{ currentNode.reason_sources.graph_dependency }}</span>
            </div>
            <div v-if="currentNode.reason_sources?.diagnosis_result" class="flex items-start gap-1.5">
              <span class="mt-1 w-1.5 h-1.5 bg-purple-400 rounded-full shrink-0"></span>
              <span>{{ currentNode.reason_sources.diagnosis_result }}</span>
            </div>
          </div>

          <div class="border-t border-gray-100 pt-3">
            <p class="text-xs font-semibold text-gray-700 mb-2">AI 推荐学习路径：</p>
            <div class="space-y-1.5">
              <button v-for="(node, i) in upcomingNodes.slice(0, 3)" :key="node.node_id"
                class="w-full flex items-center gap-2 text-xs text-left rounded-lg px-2 py-1.5 transition-colors hover:bg-gray-50"
                :class="i === 0 ? 'text-blue-600 font-semibold bg-blue-50/50' : 'text-gray-500'"
                @click="selectNode(node)"
              >
                <span class="w-5 h-5 rounded-full flex items-center justify-center text-[10px] shrink-0"
                  :class="i === 0 ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-400'">
                  {{ i + 1 }}
                </span>
                <span class="flex-1 truncate">{{ node.node_name }}</span>
                <span v-if="i === 0" class="text-[10px] bg-blue-100 text-blue-500 px-1.5 py-0.5 rounded-full shrink-0">当前</span>
              </button>
            </div>
          </div>

          <!-- 底部操作区 -->
          <div class="mt-auto flex flex-col gap-2">
            <button
              class="w-full py-2 bg-gradient-to-r from-blue-500 to-indigo-500 text-white text-sm font-semibold rounded-xl hover:opacity-90 transition-opacity flex items-center justify-center gap-2"
              @click="chatWithAlice()"
            >
              <span>💬</span> 与 Alice 对话
            </button>
            <button
              class="w-full py-2 border border-gray-200 text-gray-600 text-sm rounded-xl hover:bg-gray-50 transition-colors"
              @click="goToDiagnosis"
            >
              查看完整诊断分析 →
            </button>
          </div>
        </template>

        <div v-else class="flex-1 flex flex-col items-center justify-center text-gray-300 text-sm gap-2">
          <div class="text-3xl">🤖</div>
          <p>暂无路径数据</p>
          <button class="text-xs text-blue-500 hover:underline" @click="goToDiagnosis">
            去完成诊断 →
          </button>
        </div>
      </div>
    </div>

    <!-- ③ 当前节点详情 + 学习资源推荐 -->
    <div v-if="currentNode" class="grid grid-cols-1 lg:grid-cols-5 gap-4">

      <!-- 节点详情 (3/5) -->
      <div class="lg:col-span-3 bg-white rounded-2xl shadow-sm border border-blue-50 p-4">
        <div class="mb-3">
          <span class="text-[11px] bg-blue-500 text-white px-2.5 py-0.5 rounded-full">当前学习</span>
          <h3 class="text-lg font-bold text-gray-900 mt-2">{{ currentNode.node_name }}</h3>
          <p class="text-sm text-gray-400 mt-0.5 line-clamp-2">{{ currentNode.recommendation_reason }}</p>
        </div>
        <div class="grid grid-cols-3 gap-4">
          <!-- 学习目标 -->
          <div>
            <p class="text-[11px] font-semibold text-gray-600 mb-2 uppercase tracking-wide">学习目标</p>
            <ul class="space-y-2 text-xs text-gray-600">
              <li class="flex items-start gap-1.5">
                <span class="text-blue-400 font-bold shrink-0">1.</span>了解 {{ trunc(currentNode.node_name, 6) }} 核心概念
              </li>
              <li class="flex items-start gap-1.5">
                <span class="text-blue-400 font-bold shrink-0">2.</span>掌握工作原理与协议流程
              </li>
              <li class="flex items-start gap-1.5">
                <span class="text-blue-400 font-bold shrink-0">3.</span>能分析和解决实际问题
              </li>
            </ul>
          </div>
          <!-- 推荐方式 -->
          <div>
            <p class="text-[11px] font-semibold text-gray-600 mb-2 uppercase tracking-wide">推荐学习方式</p>
            <div class="space-y-2 text-xs text-gray-600">
              <button v-for="r in recommendedMethods" :key="r.label"
                class="w-full flex items-center gap-1.5 hover:text-blue-600 transition-colors group text-left"
                @click="r.action()">
                <span class="w-5 h-5 bg-blue-50 group-hover:bg-blue-100 text-blue-400 rounded flex items-center justify-center text-[10px] shrink-0 transition-colors">{{ r.icon }}</span>
                <span>{{ r.label }}</span>
              </button>
            </div>
          </div>
          <!-- 掌握度 + 开始 -->
          <div>
            <p class="text-[11px] font-semibold text-gray-600 mb-2 uppercase tracking-wide">掌握度</p>
            <div class="flex items-center gap-2 mb-2">
              <div class="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                <div class="h-full bg-blue-500 rounded-full transition-all duration-700"
                  :style="{width: pct(currentNode.current_mastery) + '%'}"/>
              </div>
              <span class="text-xs font-bold text-blue-600 shrink-0">{{ pct(currentNode.current_mastery) }}%</span>
            </div>
            <p class="text-[10px] text-gray-400 mb-3">
              前置 {{ currentNode.prerequisites?.length ?? 0 }} 个 · 难度 {{ currentNode.difficulty }}/5 · {{ currentNode.estimated_time }} 分钟
            </p>
            <button
              class="w-full py-2 bg-blue-500 hover:bg-blue-600 text-white text-sm font-semibold rounded-xl transition-colors"
              @click="startLearning(currentNode)"
            >
              开始学习 →
            </button>
          </div>
        </div>
      </div>

      <!-- 学习资源推荐 (2/5) -->
      <div class="lg:col-span-2 bg-white rounded-2xl shadow-sm border border-gray-50 p-4">
        <div class="flex items-center justify-between mb-3">
          <h3 class="font-semibold text-gray-800">学习资源推荐</h3>
          <button class="text-[11px] text-blue-500 hover:text-blue-600 transition-colors" @click="goToResources">
            更多资源 ›
          </button>
        </div>
        <div class="space-y-2">
          <button v-for="item in resourceItems" :key="item.title"
            class="group w-full flex items-center gap-3 p-2.5 rounded-xl hover:bg-slate-50 cursor-pointer transition-colors text-left"
            @click="openResource(item)"
          >
            <div class="w-10 h-10 rounded-xl flex items-center justify-center text-xl shrink-0"
              :class="item.bg">{{ item.icon }}</div>
            <div class="flex-1 min-w-0">
              <p class="text-xs font-medium text-gray-800 truncate">{{ item.title }}</p>
              <p class="text-[10px] text-gray-400">{{ item.type }} · {{ item.dur }}</p>
            </div>
            <div class="w-7 h-7 bg-blue-50 rounded-full flex items-center justify-center text-blue-400 text-xs opacity-0 group-hover:opacity-100 transition-opacity">▶</div>
          </button>
        </div>
      </div>
    </div>

    <!-- ④ 底部推荐路线横向时间线 -->
    <div class="bg-white rounded-2xl shadow-sm border border-blue-50 p-4">
      <div class="flex items-center justify-between mb-4">
        <h3 class="font-semibold text-gray-800">
          推荐学习路线
          <span class="text-xs text-gray-400 font-normal ml-1">（AI 为你规划）</span>
        </h3>
        <div class="flex items-center gap-3">
          <button class="text-[11px] text-gray-400 hover:text-blue-500 transition-colors" @click="reloadPath">
            🔄 重新加载
          </button>
          <button class="text-[11px] text-blue-500 hover:underline" @click="goToDiagnosis">
            重新诊断规划 →
          </button>
        </div>
      </div>
      <div class="flex items-start gap-2 overflow-x-auto pb-2">
        <template v-for="(node, i) in (pathStore.path?.nodes ?? [])" :key="node.node_id">
          <div class="flex flex-col items-center gap-1 shrink-0 w-24 cursor-pointer group"
            :class="{ 'opacity-50': node.status === 'locked' }"
            @click="selectNode(node)"
          >
            <!-- 序号圈 -->
            <div class="w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold border-2 transition-all"
              :class="{
                'bg-emerald-400 border-emerald-400 text-white': node.status === 'completed',
                'bg-blue-500 border-blue-500 text-white ring-2 ring-blue-200': node.status === 'in_progress',
                'bg-gray-100 border-gray-200 text-gray-400': node.status === 'locked',
                'bg-white border-gray-300 text-gray-500': node.status === 'pending',
                'ring-2 ring-indigo-400 ring-offset-1': selectedNode?.node_id === node.node_id,
              }">
              <span v-if="node.status === 'completed'">✓</span>
              <span v-else>{{ i + 1 }}</span>
            </div>
            <!-- 名称 -->
            <p class="text-[10px] text-gray-700 text-center leading-3 font-medium group-hover:text-blue-600 transition-colors">
              {{ trunc(node.node_name, 6) }}
            </p>
            <!-- 状态 -->
            <p class="text-[10px] text-center"
              :class="{
                'text-emerald-500': node.status === 'completed',
                'text-blue-500 font-semibold': node.status === 'in_progress',
                'text-gray-400': node.status === 'locked' || node.status === 'pending',
              }">
              {{ statusLabel(node.status) }}
            </p>
            <!-- 掌握度 -->
            <p v-if="node.status !== 'locked'" class="text-[10px] text-blue-400">
              {{ pct(node.current_mastery) }}%
            </p>
          </div>
          <!-- 分割线 -->
          <div v-if="i < (pathStore.path?.nodes.length ?? 0) - 1" class="flex items-center shrink-0 pt-4">
            <div class="w-6 h-px"
              :class="node.status === 'completed' ? 'bg-emerald-300' : 'bg-gray-200'"></div>
            <span class="text-[10px]" :class="node.status === 'completed' ? 'text-emerald-300' : 'text-gray-200'">›</span>
          </div>
        </template>
      </div>
    </div>

    <!-- 节点详情弹窗 -->
    <Teleport to="body">
      <Transition name="s1-modal">
        <div v-if="selectedNode" class="fixed inset-0 z-50 flex items-center justify-center px-4"
          @click.self="selectedNode = null">
          <div class="absolute inset-0 bg-black/20 backdrop-blur-sm"/>
          <div class="relative w-full max-w-md bg-white rounded-2xl shadow-2xl p-5 space-y-3 max-h-[85vh] overflow-y-auto">

            <!-- 头部 -->
            <div class="flex items-start justify-between">
              <div class="flex items-center gap-2">
                <span class="text-xs px-2 py-0.5 rounded-full font-medium"
                  :class="{
                    'bg-emerald-100 text-emerald-700': selectedNode.status === 'completed',
                    'bg-blue-100 text-blue-700': selectedNode.status === 'in_progress',
                    'bg-gray-100 text-gray-500': selectedNode.status === 'locked',
                    'bg-slate-100 text-slate-600': selectedNode.status === 'pending',
                  }">
                  {{ statusLabel(selectedNode.status) }}
                </span>
                <span v-if="selectedNode.is_target" class="text-xs bg-indigo-50 text-indigo-600 px-2 py-0.5 rounded-full">🎯 目标节点</span>
              </div>
              <button class="text-gray-300 hover:text-gray-600 text-xl leading-none transition-colors" @click="selectedNode = null">×</button>
            </div>

            <div>
              <h3 class="font-bold text-gray-900 text-lg">{{ selectedNode.node_name }}</h3>
              <p class="text-xs text-gray-400 mt-0.5">{{ selectedNode.chapter }} · 难度 {{ selectedNode.difficulty }}/5 · 预计 {{ selectedNode.estimated_time }} 分钟</p>
            </div>

            <!-- 掌握度 -->
            <div class="bg-slate-50 rounded-xl p-3">
              <div class="flex items-center justify-between mb-2">
                <span class="text-xs font-semibold text-gray-700">当前掌握度</span>
                <span class="text-sm font-bold text-blue-600">{{ pct(selectedNode.current_mastery) }}%</span>
              </div>
              <div class="h-2 bg-gray-200 rounded-full overflow-hidden">
                <div class="h-full bg-blue-500 rounded-full transition-all duration-700"
                  :style="{width: pct(selectedNode.current_mastery)+'%'}"/>
              </div>
            </div>

            <!-- 推荐理由 -->
            <div class="bg-blue-50 rounded-xl p-3">
              <p class="text-xs font-semibold text-blue-700 mb-1.5">💡 AI 推荐理由</p>
              <p class="text-xs text-gray-700 leading-6">{{ selectedNode.recommendation_reason }}</p>
            </div>

            <!-- 三维推荐理由 -->
            <div v-if="selectedNode.reason_sources" class="space-y-2">
              <div v-if="selectedNode.reason_sources.graph_dependency" class="rounded-xl bg-blue-50/50 border border-blue-100 p-3">
                <p class="text-[10px] font-semibold text-blue-700 mb-1">📊 知识图谱依赖</p>
                <p class="text-xs text-gray-600 leading-5">{{ selectedNode.reason_sources.graph_dependency }}</p>
              </div>
              <div v-if="selectedNode.reason_sources.diagnosis_result" class="rounded-xl bg-purple-50/50 border border-purple-100 p-3">
                <p class="text-[10px] font-semibold text-purple-700 mb-1">🔍 诊断结果驱动</p>
                <p class="text-xs text-gray-600 leading-5">{{ selectedNode.reason_sources.diagnosis_result }}</p>
              </div>
              <div v-if="selectedNode.reason_sources.cognitive_style" class="rounded-xl bg-emerald-50/50 border border-emerald-100 p-3">
                <p class="text-[10px] font-semibold text-emerald-700 mb-1">🧠 认知风格适配</p>
                <p class="text-xs text-gray-600 leading-5">{{ selectedNode.reason_sources.cognitive_style }}</p>
              </div>
            </div>

            <!-- 前置知识 -->
            <div v-if="selectedNode.prerequisites?.length" class="space-y-1.5">
              <p class="text-xs font-semibold text-gray-600">前置知识</p>
              <div class="flex flex-wrap gap-1.5">
                <span v-for="p in selectedNode.prerequisites" :key="p"
                  class="text-[10px] px-2 py-1 rounded-lg"
                  :class="selectedNode.prerequisites_met ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-600'">
                  {{ selectedNode.prerequisites_met ? '✓' : '⚠' }} {{ p }}
                </span>
              </div>
            </div>

            <!-- 操作按钮组 -->
            <div class="space-y-2 pt-1">
              <!-- 开始学习（未锁定） -->
              <button v-if="selectedNode.status !== 'locked'"
                class="w-full py-2.5 bg-blue-500 hover:bg-blue-600 text-white text-sm font-semibold rounded-xl transition-colors flex items-center justify-center gap-2"
                @click="startLearning(selectedNode)"
              >
                <span>🚀</span> 开始学习
              </button>

              <!-- 标记完成（进行中或待学习） -->
              <button
                v-if="selectedNode.status === 'in_progress' || selectedNode.status === 'pending'"
                class="w-full py-2.5 border-2 border-emerald-400 text-emerald-600 hover:bg-emerald-50 text-sm font-semibold rounded-xl transition-colors flex items-center justify-center gap-2"
                @click="markDone(selectedNode)"
              >
                <span>✓</span> 标记为已完成
              </button>

              <!-- 与 Alice 对话 -->
              <button
                v-if="selectedNode.status !== 'locked'"
                class="w-full py-2.5 border border-gray-200 text-gray-600 hover:bg-gray-50 text-sm rounded-xl transition-colors flex items-center justify-center gap-2"
                @click="chatWithAlice(selectedNode)"
              >
                <span>💬</span> 向 Alice 提问此节点
              </button>

              <!-- 锁定时提示 -->
              <div v-if="selectedNode.status === 'locked'"
                class="text-center text-xs text-gray-400 bg-gray-50 rounded-xl py-3">
                🔒 请先完成前置知识节点后解锁
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { usePathStore } from '@/stores/pathStore'
import { useUserStore } from '@/stores/userStore'
import type { PathNode, PathNodeStatus } from '@/types/path'

const router = useRouter()
const pathStore = usePathStore()
const userStore = useUserStore()

const selectedNode = ref<PathNode | null>(null)
const justCompleted = ref<string | null>(null)
const toastMsg = ref<string | null>(null)

onMounted(() => {
  userStore.fetchProfile()
  pathStore.fetchPath(userStore.userId)
})

// ── 导航函数 ───────────────────────────────────────────────────
function goToProfile() {
  router.push('/profile')
}
function goToDiagnosis() {
  selectedNode.value = null
  router.push('/diagnosis')
}
function goToResources() {
  router.push('/resources')
}
function goToSimulator() {
  router.push('/simulator')
}
function goToBookshelf() {
  router.push('/bookshelf')
}

/** 开始学习指定节点 → 跳转至智能对话并预填话题 */
function startLearning(node?: PathNode | null) {
  const n = node ?? currentNode.value
  selectedNode.value = null
  if (!n) {
    router.push('/chat')
    return
  }
  router.push({ path: '/chat', query: { topic: n.node_name, from: 'path' } })
}

/** 与 Alice 对话，聚焦该节点 */
function chatWithAlice(node?: PathNode | null) {
  const n = node ?? currentNode.value
  selectedNode.value = null
  const query: Record<string, string> = { from: 'path' }
  if (n) query.topic = n.node_name
  router.push({ path: '/chat', query })
}

/** 打开资源 item → 根据类型跳转 */
function openResource(item: { type: string }) {
  selectedNode.value = null
  if (item.type === '视频' || item.type === '实验') {
    router.push('/simulator')
  } else if (item.type === '文档') {
    router.push('/bookshelf')
  } else {
    router.push('/resources')
  }
}

/** 重新加载路径 */
function reloadPath() {
  pathStore.fetchPath(userStore.userId)
  showToast('🔄 正在重新加载学习路径…')
}

// ── 节点交互 ───────────────────────────────────────────────────
function selectNode(node: PathNode) {
  selectedNode.value = selectedNode.value?.node_id === node.node_id ? null : node
}

/** 标记节点完成 */
async function markDone(node: PathNode) {
  await pathStore.markNodeCompleted(userStore.userId, node.node_id, 0.9)
  selectedNode.value = null
  justCompleted.value = node.node_id
  showToast(`🎉 「${node.node_name}」已标记为完成！`)
  setTimeout(() => { justCompleted.value = null }, 2000)
}

// ── Toast ──────────────────────────────────────────────────────
function showToast(msg: string) {
  toastMsg.value = msg
  setTimeout(() => { toastMsg.value = null }, 2500)
}

// ── 计算属性 ──────────────────────────────────────────────────
const currentNode = computed(() =>
  pathStore.path?.nodes.find(n => n.status === 'in_progress')
  ?? pathStore.path?.nodes.find(n => n.status === 'pending')
  ?? null,
)

const upcomingNodes = computed(() =>
  pathStore.path?.nodes.filter(n => n.status !== 'completed') ?? [],
)

const totalHours = computed(() =>
  Math.max(1, Math.round((pathStore.path?.total_estimated_time ?? 240) / 60)),
)

// 顶部统计 chips（可点击）
const statsChips = computed(() => [
  {
    icon: '📍', label: '当前阶段', value: currentNode.value?.node_name ?? 'TCP/IP 基础',
    bg: 'bg-blue-100', tip: '点击进入智能对话',
    action: () => chatWithAlice(),
  },
  {
    icon: '🎯', label: '预计节点数', value: `${pathStore.totalCount} 个知识节点`,
    bg: 'bg-purple-100', tip: '查看所有节点',
    action: () => showToast(`📊 共 ${pathStore.totalCount} 个知识节点，已完成 ${pathStore.completedCount} 个`),
  },
  {
    icon: '⏱', label: '预计学习时长', value: `${totalHours.value} 小时`,
    bg: 'bg-green-100', tip: '预计总学习时间',
    action: () => showToast(`⏱ 预计还需 ${totalHours.value} 小时完成全部路径`),
  },
  {
    icon: '📊', label: '路径完成度', value: `${pathStore.progressPercent}%`,
    bg: 'bg-orange-100', tip: '点击查看能力画像',
    action: () => goToProfile(),
  },
])

// ── SVG 图谱布局 ───────────────────────────────────────────────
const SVG_W = 680
const SVG_H = 360
const NODE_R = 34
const COLS = 4

const nodePositions = computed(() => {
  const nodes = pathStore.path?.nodes ?? []
  if (!nodes.length) return []
  const colCount = Math.min(COLS, nodes.length)
  return nodes.map((node, i) => {
    const row = Math.floor(i / colCount)
    const col = row % 2 === 0 ? i % colCount : (colCount - 1 - i % colCount)
    const gapX = colCount > 1 ? (SVG_W - 120) / (colCount - 1) : 0
    return { node, x: 60 + col * gapX, y: 75 + row * 140 }
  })
})

const connections = computed(() => {
  const nodes = pathStore.path?.nodes ?? []
  const pm = new Map(nodePositions.value.map(p => [p.node.node_id, p]))
  return nodes.slice(0, -1).map((n, i) => {
    const a = pm.get(n.node_id)!
    const b = pm.get(nodes[i + 1].node_id)!
    const mx = (a.x + b.x) / 2
    const my = (a.y + b.y) / 2
    return {
      d: `M ${a.x} ${a.y} Q ${mx} ${my - 18} ${b.x} ${b.y}`,
      done: n.status === 'completed',
    }
  }).filter(Boolean)
})

// ── 节点样式 ───────────────────────────────────────────────────
function ns(status: PathNodeStatus | string) {
  const m: Record<string, { bg: string; border: string; text: string }> = {
    completed: { bg: '#D1FAE5', border: '#10B981', text: '#065F46' },
    in_progress: { bg: '#EFF6FF', border: '#2563EB', text: '#1D4ED8' },
    locked: { bg: '#F3F4F6', border: '#D1D5DB', text: '#9CA3AF' },
    pending: { bg: '#F0FDF4', border: '#86EFAC', text: '#16A34A' },
  }
  return m[status] ?? m.pending
}

const pct = (m: number) => Math.round(m * 100)
const trunc = (s: string, n: number) => s.length > n ? s.slice(0, n) + '…' : s

function statusLabel(status: PathNodeStatus | string) {
  const m: Record<string, string> = { completed: '已掌握', in_progress: '学习中', locked: '锁定中', pending: '未开始' }
  return m[status] ?? '未开始'
}

// ── 推荐学习方式（可点击跳转） ──────────────────────────────────
const recommendedMethods = computed(() => [
  { icon: '🎬', label: '协议仿真模拟', action: () => goToSimulator() },
  { icon: '💬', label: '与 Alice 对话', action: () => chatWithAlice() },
  { icon: '📄', label: '查阅知识文档', action: () => goToBookshelf() },
])

// ── 资源推荐（根据当前节点动态生成） ─────────────────────────────
const resourceItems = computed(() => {
  const name = currentNode.value?.node_name ?? '当前节点'
  return [
    { icon: '🎬', title: `${name}动画演示`, type: '视频', dur: '12 分钟', bg: 'bg-red-50' },
    { icon: '🔬', title: 'Wireshark 实验抓包分析', type: '实验', dur: '15 分钟', bg: 'bg-green-50' },
    { icon: '📄', title: `${name}详解文档`, type: '文档', dur: '8 分钟', bg: 'bg-blue-50' },
  ]
})
</script>

<style scoped>
@keyframes s1Pulse {
  0%, 100% { opacity: 0.25; transform: scale(1); }
  50% { opacity: 0.08; transform: scale(1.1); }
}
.s1-pulse {
  transform-origin: center;
  animation: s1Pulse 2s ease-in-out infinite;
}

@keyframes s1SelectedRing {
  0%, 100% { stroke-dashoffset: 0; opacity: 0.7; }
  50% { stroke-dashoffset: -16; opacity: 0.4; }
}
.s1-selected-ring {
  transform-origin: center;
  animation: s1SelectedRing 1.5s ease-in-out infinite;
}

@keyframes s1CompleteFlash {
  0% { opacity: 0.6; transform: scale(0.8); }
  50% { opacity: 0.3; transform: scale(1.2); }
  100% { opacity: 0; transform: scale(1.5); }
}
.s1-complete-flash {
  transform-origin: center;
  animation: s1CompleteFlash 1.5s ease-out forwards;
}

.s1-modal-enter-active,
.s1-modal-leave-active {
  transition: opacity 0.2s ease;
}
.s1-modal-enter-from,
.s1-modal-leave-to {
  opacity: 0;
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.toast-enter-from {
  opacity: 0;
  transform: translateX(-50%) translateY(-12px);
}
.toast-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(-8px);
}
</style>
