import { createApp } from 'vue'
import { createPinia } from 'pinia'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

import App from './App.vue'
import router from './router'
import './assets/styles/main.css'

// 全局通用组件
import AppLoading from '@/components/AppLoading.vue'
import AppEmpty from '@/components/AppEmpty.vue'
import AppError from '@/components/AppError.vue'

const app = createApp(App)
const pinia = createPinia()
pinia.use(piniaPluginPersistedstate)

app.use(pinia)
app.use(router)
app.use(ElementPlus)

// Element Plus 图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 全局通用组件
app.component('AppLoading', AppLoading)
app.component('AppEmpty', AppEmpty)
app.component('AppError', AppError)

/**
 * 全局 Vue 错误边界
 * 捕获所有未被组件内部 try-catch 处理的渲染异常，展示友好提示而非白屏
 */
app.config.errorHandler = (err, instance, info) => {
  // 将完整应计录写入控制台（便于生产排查）
  console.error('[Vue Global Error]', { err, info, component: instance?.$options?.name })

  // 展示友好的错误提示，不让用户面对空白屏
  ElMessage.error({
    message: '页面发生意外错误，已自动恢复。若持续异常请刷新页面。',
    duration: 5000,
    showClose: true,
  })
}

/**
 * 全局 Promise未捕获异常处理（如 async 函数未加 await/catch）
 */
window.addEventListener('unhandledrejection', (event) => {
  console.error('[Unhandled Promise Rejection]', event.reason)
  // 不展示弹窗，避免频繁打扰用户；仅记录到控制台
  event.preventDefault()
})

app.mount('#app')
