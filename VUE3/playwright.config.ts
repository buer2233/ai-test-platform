import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright 配置文件
 * 用于 AI 自动化测试平台的 UI 自动化测试
 */
export default defineConfig({
  // 测试目录位置
  testDir: './tests',

  // 测试文件匹配模式
  testMatch: '**/*.spec.ts',

  // 完全并行运行测试
  fullyParallel: false,

  // 在 CI 环境失败时禁止重试
  forbidOnly: !!process.env.CI,

  // 失败重试次数
  retries: process.env.CI ? 2 : 1,

  // 并行工作进程数
  workers: 1,

  // 测试报告配置
  reporter: [
    ['html', { outputFolder: './tests/report/html-report' }],
    ['json', { outputFile: './tests/report/test-results.json' }],
    ['list']
  ],

  // 全局设置
  use: {
    // 基础 URL
    baseURL: 'http://localhost:3000',

    // 收集测试失败时的追踪信息
    trace: 'on-first-retry',

    // 截图配置
    screenshot: 'only-on-failure',

    // 视频录制
    video: 'retain-on-failure',

    // 操作超时时间
    actionTimeout: 10000,

    // 导航超时时间
    navigationTimeout: 30000,
  },

  // 项目配置
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  // 测试运行前的全局设置
  globalSetup: './playwright-global-setup.ts',
});
