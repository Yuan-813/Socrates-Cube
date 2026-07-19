<template>
  <div class="flipbook-container">
    <div ref="bookRef" class="flipbook-inner">
      <div
        v-for="page in pages"
        :key="page.id"
        class="flip-page"
        :class="page.bgClass"
      >
        <ManualPageComp :page="page" />
      </div>
    </div>

    <!-- 导航按钮 -->
    <button
      class="nav-btn nav-btn-prev"
      :disabled="currentPage <= 0"
      @click="flipPrev"
      aria-label="上一页"
    >
      ‹
    </button>
    <button
      class="nav-btn nav-btn-next"
      :disabled="currentPage >= totalPages - 1"
      @click="flipNext"
      aria-label="下一页"
    >
      ›
    </button>

    <!-- 页码指示器 -->
    <div class="page-indicator">
      第 {{ currentPage + 1 }} / {{ totalPages }} 页
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { PageFlip } from 'page-flip'
import type { ManualPage } from '@/data/userManualContent'
import ManualPageComp from './ManualPage.vue'

const props = defineProps<{
  pages: ManualPage[]
}>()

const emit = defineEmits<{
  'page-change': [page: number]
  'last-page-reached': []
}>()

const bookRef = ref<HTMLElement | null>(null)
const currentPage = ref(0)
const totalPages = computed(() => props.pages.length)
let pageFlip: PageFlip | null = null

onMounted(() => {
  nextTick(() => {
    initFlipBook()
  })
  window.addEventListener('keydown', handleKeydown)
})

function initFlipBook() {
  if (!bookRef.value) return
  try {
    pageFlip = new PageFlip(bookRef.value, {
      width: 550,
      height: 733,
      size: 'stretch',
      minWidth: 315,
      maxWidth: 1000,
      minHeight: 420,
      maxHeight: 1350,
      showCover: true,
      maxShadowOpacity: 0.5,
      mobileScrollSupport: false,
      flippingTime: 800,
      useMouseEvents: true,
    })

    const pageElements = bookRef.value.querySelectorAll('.flip-page') as NodeListOf<HTMLElement>
    pageFlip.loadFromHTML(pageElements)

    pageFlip.on('flip', (e: any) => {
      currentPage.value = e.data
      emit('page-change', e.data)
      if (e.data >= props.pages.length - 1) {
        emit('last-page-reached')
      }
    })
  } catch (err) {
    console.warn('PageFlip初始化失败，使用降级模式', err)
  }
}

function flipNext() {
  pageFlip?.flipNext()
}

function flipPrev() {
  pageFlip?.flipPrev()
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'ArrowRight') flipNext()
  if (e.key === 'ArrowLeft') flipPrev()
}

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
  pageFlip?.destroy()
})
</script>

<style scoped>
.flipbook-container {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  box-sizing: border-box;
}

.flipbook-inner {
  width: 100%;
  max-width: 1100px;
  height: 100%;
  max-height: 733px;
}

.nav-btn {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 44px;
  height: 44px;
  border-radius: 50%;
  border: none;
  background: rgba(15, 23, 42, 0.6);
  color: #fff;
  font-size: 24px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s, opacity 0.2s;
  z-index: 10;
}

.nav-btn:hover:not(:disabled) {
  background: rgba(15, 23, 42, 0.9);
}

.nav-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.nav-btn-prev {
  left: 12px;
}

.nav-btn-next {
  right: 12px;
}

.page-indicator {
  position: absolute;
  bottom: 12px;
  left: 50%;
  transform: translateX(-50%);
  color: rgba(255, 255, 255, 0.8);
  font-size: 13px;
  letter-spacing: 1px;
  user-select: none;
}
</style>
