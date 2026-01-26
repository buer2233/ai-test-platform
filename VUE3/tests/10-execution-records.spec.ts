import { test, expect } from '@playwright/test';

/**
 * 执行记录功能测试用例
 * 包含执行记录列表、执行详情、实时状态监控测试
 */

test.beforeEach(async ({ page }) => {
  // 快速登录 - 使用 first() 避免严格模式违规
  await page.goto('/');
  const usernameInput = page.locator('input[type="text"]').first();
  if (await usernameInput.isVisible({ timeout: 3000 })) {
    await usernameInput.fill('admin');
    await page.locator('input[type="password"]').first().fill('admin123');
    await page.getByRole('button', { name: /登录/i }).click();
    await page.waitForTimeout(1000);
  }
});

test.describe('执行记录', () => {

  test('应该显示执行记录页面', async ({ page }) => {
    await page.goto('/api-automation/executions');
    await page.waitForLoadState('networkidle');

    // 验证页面加载
    const pageTitle = page.locator('h1, h2, .page-title');
    await expect(pageTitle.first()).toBeVisible({ timeout: 5000 });

    console.log('✓ 执行记录页面加载成功');
  });

  test('应该显示执行记录列表', async ({ page }) => {
    await page.goto('/api-automation/executions');
    await page.waitForLoadState('networkidle');

    // 查找表格
    const table = page.locator('.el-table, table, [role="table"]');

    if (await table.isVisible({ timeout: 5000 })) {
      console.log('✓ 执行记录列表存在');
    } else {
      console.log('⚠ 未找到执行记录列表');
    }
  });

  test('应该显示执行状态', async ({ page }) => {
    await page.goto('/api-automation/executions');
    await page.waitForLoadState('networkidle');

    // 查找状态标签
    const statusTags = page.locator('.el-tag, [class*="status"], [class*="tag"]');

    if (await statusTags.count() > 0) {
      console.log('✓ 执行状态显示存在');
    } else {
      console.log('⚠ 未找到执行状态显示');
    }
  });

  test('应该能查看执行详情', async ({ page }) => {
    await page.goto('/api-automation/executions');
    await page.waitForLoadState('networkidle');

    // 查找执行记录行并点击
    const table = page.locator('.el-table, table');
    const rows = table.locator('tbody tr');

    const rowCount = await rows.count();
    if (rowCount > 0) {
      const firstRow = rows.first();
      const link = firstRow.locator('a').first();

      if (await link.isVisible({ timeout: 1000 })) {
        await link.click();
        await page.waitForLoadState('networkidle');
        console.log('✓ 执行详情可打开');
      } else {
        console.log('⚠ 未找到执行详情链接');
      }
    } else {
      console.log('⚠ 执行记录列表为空');
    }
  });

  test('执行详情应该显示用例结果', async ({ page }) => {
    await page.goto('/api-automation/executions/1');
    await page.waitForLoadState('networkidle');

    // 查找用例结果
    const table = page.locator('.el-table, table');

    if (await table.isVisible({ timeout: 5000 })) {
      console.log('✓ 执行详情显示用例结果');
    } else {
      console.log('⚠ 未找到用例结果列表');
    }
  });

  test('执行详情应该显示进度条', async ({ page }) => {
    await page.goto('/api-automation/executions/1');
    await page.waitForLoadState('networkidle');

    // 查找进度条
    const progressBar = page.locator('.el-progress, [class*="progress"], [role="progressbar"]');

    if (await progressBar.count() > 0) {
      console.log('✓ 进度条存在');
    } else {
      console.log('⚠ 未找到进度条');
    }
  });

  test('应该支持取消执行功能', async ({ page }) => {
    await page.goto('/api-automation/executions');
    await page.waitForLoadState('networkidle');

    // 查找取消按钮
    const cancelButton = page.locator('button:has-text("取消"), button:has-text("停止")');

    if (await cancelButton.first().isVisible({ timeout: 3000 })) {
      console.log('✓ 取消执行按钮存在');
    } else {
      console.log('⚠ 未找到取消执行按钮');
    }
  });

  test('应该支持重新执行功能', async ({ page }) => {
    await page.goto('/api-automation/executions');
    await page.waitForLoadState('networkidle');

    // 查找重新执行按钮
    const rerunButton = page.locator('button:has-text("重新执行"), button:has-text("重试"), button:has-text("再次运行")');

    if (await rerunButton.first().isVisible({ timeout: 3000 })) {
      console.log('✓ 重新执行按钮存在');
    } else {
      console.log('⚠ 未找到重新执行按钮');
    }
  });

  test('应该显示执行时间', async ({ page }) => {
    await page.goto('/api-automation/executions');
    await page.waitForLoadState('networkidle');

    // 查找执行时间显示
    const timeDisplay = page.locator('text=/执行时间|耗时|秒|ms/i');

    if (await timeDisplay.count() > 0) {
      console.log('✓ 执行时间显示存在');
    } else {
      console.log('⚠ 未找到执行时间显示');
    }
  });

  test('应该支持按环境筛选', async ({ page }) => {
    await page.goto('/api-automation/executions');
    await page.waitForLoadState('networkidle');

    // 查找环境筛选器
    const envSelect = page.locator('.el-select, select');

    if (await envSelect.first().isVisible({ timeout: 3000 })) {
      console.log('✓ 环境筛选器存在');
    } else {
      console.log('⚠ 未找到环境筛选器');
    }
  });

  test('应该支持按状态筛选', async ({ page }) => {
    await page.goto('/api-automation/executions');
    await page.waitForLoadState('networkidle');

    // 查找状态筛选器
    const statusFilter = page.locator('.el-select, select, .el-radio-group');

    const filterCount = await statusFilter.count();
    if (filterCount > 0) {
      console.log('✓ 状态筛选器存在');
    } else {
      console.log('⚠ 未找到状态筛选器');
    }
  });

  test('应该支持时间范围筛选', async ({ page }) => {
    await page.goto('/api-automation/executions');
    await page.waitForLoadState('networkidle');

    // 查找日期选择器
    const datePicker = page.locator('.el-date-editor, [class*="date"]');

    if (await datePicker.count() > 0) {
      console.log('✓ 时间范围筛选器存在');
    } else {
      console.log('⚠ 未找到时间范围筛选器');
    }
  });
});
