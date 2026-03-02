/**
 * UI自动化测试模块入口
 *
 * 提供模块级应用实例的创建函数，用于独立部署或集成到主应用中。
 * 该模块基于 browser_use 框架，实现 AI 驱动的 UI 自动化测试。
 */

import { createApp } from 'vue'

import UiAutomationApp from './App.vue'

/**
 * 创建 UI 自动化测试模块的 Vue 应用实例
 * @returns Vue 应用实例，可挂载到指定 DOM 节点
 */
export function createUiAutomationModule() {
  const app = createApp(UiAutomationApp)
  return app
}

export default createUiAutomationModule
