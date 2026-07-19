import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    // 单个 chunk 超过 800KB 时弹出警告（对标优化候选）
    chunkSizeWarningLimit: 800,
    rollupOptions: {
      output: {
        /**
         * 代码分割策略：
         *   vendor       — Vue 核心生态（最常用，长期缓存）
         *   element-plus — UI 组件库（大但可预加载）
         *   echarts      — 图表库（仅在图表页加载）
         *   three        — 3D 渲染库（仅在 Hardware3D 页加载）
         *   markdown     — Markdown 渲染相关（marked + highlight.js）
         */
        manualChunks: {
          'vendor': ['vue', 'vue-router', 'pinia'],
          'element-plus': ['element-plus'],
          'echarts': ['echarts', 'vue-echarts'],
          'three': ['three'],
          'markdown': ['marked', 'highlight.js'],
        },
      },
    },
  },
})
