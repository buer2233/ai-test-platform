/**
 * Vite 构建配置
 *
 * 主要职责：
 * 1. 注册 Vue 插件，启用 .vue 单文件组件支持
 * 2. 配置路径别名，简化模块间的导入路径
 * 3. 配置开发服务器端口及 API 代理，将前端请求转发至 Django 后端
 */
import { resolve } from 'path'

import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

export default defineConfig({
  /* ========== Vue 插件 ========== */
  plugins: [
    vue()
  ],

  /* ========== 路径别名 ========== */
  resolve: {
    alias: {
      // 通用别名
      '@': resolve(__dirname, 'src'),
      '@shared': resolve(__dirname, 'src/shared'),
      '@core': resolve(__dirname, 'src/core'),

      // 业务模块别名
      '@api-automation': resolve(__dirname, 'src/modules/api-automation'),
      '@ui-automation': resolve(__dirname, 'src/modules/ui-automation'),

      // 将 element-plus 导入重定向到本项目自定义的兼容层实现
      'element-plus': resolve(__dirname, 'src/shared/ui/element-plus/index.ts')
    }
  },

  /* ========== 开发服务器 ========== */
  server: {
    port: 3000,
    proxy: {
      // 将 /api 前缀的请求代理到 Django 后端（127.0.0.1:8000）
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      }
    }
  }
})
