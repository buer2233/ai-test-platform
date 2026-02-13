import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    vue()
  ],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
      '@shared': resolve(__dirname, 'src/shared'),
      '@core': resolve(__dirname, 'src/core'),
      '@api-automation': resolve(__dirname, 'src/modules/api-automation'),
      '@ui-automation': resolve(__dirname, 'src/modules/ui-automation'),
      'element-plus': resolve(__dirname, 'src/shared/ui/element-plus/index.ts')
    }
  },
  server: {
    port: 3000,
    proxy: {
      // 代理 /api 开头的请求到后端
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      }
    }
  }
})
