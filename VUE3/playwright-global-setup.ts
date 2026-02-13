import { FullConfig } from '@playwright/test';

/**
 * Playwright 全局设置
 * 在所有测试运行前执行
 */
async function globalSetup(config: FullConfig) {
  console.log('========================================');
  console.log('开始执行 Playwright UI 自动化测试');
  console.log('测试平台: AI 自动化测试平台');
  console.log('测试地址: http://localhost:3000');
  console.log('========================================');
}

export default globalSetup;

