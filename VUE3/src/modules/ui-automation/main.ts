/**
 * UI自动化测试模块入口
 */

import { createApp } from 'vue'
import UiAutomationApp from './App.vue'

// 创建模块应用实例
export function createUiAutomationModule() {
  const app = createApp(UiAutomationApp)

  return app
}

export default createUiAutomationModule
