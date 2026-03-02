/**
 * 环境类型声明文件
 *
 * - 引入 Vite 客户端类型（import.meta.env 等全局类型支持）
 * - 声明 .vue 单文件组件模块，使 TypeScript 能正确识别 Vue 组件的默认导出
 */
/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}