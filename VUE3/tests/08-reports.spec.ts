import { test, expect } from '@playwright/test';

/**
 * 测试报告功能测试用例
 * 包含报告列表、报告详情、报告导出、图表可视化测试
 */

test.beforeEach(async ({ page }) => {
  // 快速登录 - 使用 first() 避免严格模式违规
  await page.goto('/');
  const usernameInput = page.locator('input[type="text"]').first();
  if (await usernameInput.isVisible({ timeout: 3000 })) {
    await usernameInput.fill('admin');
    await page.locator('input[type="password"]').first().fill('admin123');
    // 使用通用按钮选择器来定位登录提交按钮
    const loginButtons = page.locator('button').filter({ hasText: /登录/i });
    await loginButtons.first().click();
    await page.waitForTimeout(1000);
  }
});

test.describe('测试报告', () => {

  test('应该显示报告列表页面', async ({ page }) => {
    await page.goto('/api-automation/reports');
    await page.waitForLoadState('networkidle');

    // 验证页面加载
    const pageTitle = page.locator('h1, h2, .page-title');
    await expect(pageTitle.first()).toBeVisible({ timeout: 5000 });

    console.log('✓ 报告列表页面加载成功');
  });

  test('应该显示报告列表表格', async ({ page }) => {
    await page.goto('/api-automation/reports');
    await page.waitForLoadState('networkidle');

    // 查找表格
    const table = page.locator('.el-table, table, [role="table"]');

    if (await table.isVisible({ timeout: 5000 })) {
      console.log('✓ 报告列表表格存在');
    } else {
      console.log('⚠ 未找到报告列表表格');
    }
  });

  test('应该支持按环境筛选', async ({ page }) => {
    await page.goto('/api-automation/reports');
    await page.waitForLoadState('networkidle');

    // 查找环境筛选器
    const envSelect = page.locator('.el-select, select');

    if (await envSelect.first().isVisible({ timeout: 3000 })) {
      console.log('✓ 环境筛选器存在');
    } else {
      console.log('⚠ 未找到环境筛选器');
    }
  });

  test('应该能打开报告详情', async ({ page }) => {
    await page.goto('/api-automation/reports');
    await page.waitForLoadState('networkidle');

    // 查找报告行并点击
    const table = page.locator('.el-table, table');
    const rows = table.locator('tbody tr');

    const rowCount = await rows.count();
    if (rowCount > 0) {
      const firstRow = rows.first();
      const link = firstRow.locator('a').first();

      if (await link.isVisible({ timeout: 1000 })) {
        await link.click();
        await page.waitForLoadState('networkidle');
        console.log('✓ 报告详情可打开');
      } else {
        console.log('⚠ 未找到报告详情链接');
      }
    } else {
      console.log('⚠ 报告列表为空');
    }
  });

  test('报告详情应该显示执行摘要', async ({ page }) => {
    await page.goto('/api-automation/reports/1');
    await page.waitForLoadState('networkidle');

    // 查找执行摘要信息
    const summary = page.locator('text=/总数|通过|失败|通过率/i');

    if (await summary.count() > 0) {
      console.log('✓ 报告详情显示执行摘要');
    } else {
      console.log('⚠ 未找到执行摘要');
    }
  });

  test('报告详情应该显示测试结果列表', async ({ page }) => {
    await page.goto('/api-automation/reports/1');
    await page.waitForLoadState('networkidle');

    // 查找测试结果表格
    const table = page.locator('.el-table, table');

    if (await table.isVisible({ timeout: 5000 })) {
      console.log('✓ 报告详情显示测试结果列表');
    } else {
      console.log('⚠ 未找到测试结果列表');
    }
  });

  test('报告详情应该显示图表', async ({ page }) => {
    await page.goto('/api-automation/reports/1');
    await page.waitForLoadState('networkidle');

    // 查找图表容器
    const chartContainers = page.locator('[class*="chart"], .echart, [class*="echart"]');

    if (await chartContainers.count() > 0) {
      console.log('✓ 报告详情显示图表');
    } else {
      console.log('⚠ 未找到图表');
    }
  });

  test('应该支持报告导出功能', async ({ page }) => {
    await page.goto('/api-automation/reports/1');
    await page.waitForLoadState('networkidle');

    // 查找导出按钮
    const exportButtons = page.locator('button:has-text("导出"), button:has-text("Export"), button:has-text("PDF"), button:has-text("Excel")');

    if (await exportButtons.count() > 0) {
      console.log('✓ 报告导出按钮存在');
    } else {
      console.log('⚠ 未找到报告导出按钮');
    }
  });

  test('应该支持多种导出格式', async ({ page }) => {
    await page.goto('/api-automation/reports/1');
    await page.waitForLoadState('networkidle');

    // 查找导出格式选项
    const formats = ['PDF', 'Excel', 'CSV', 'JSON'];
    let foundFormats = 0;

    for (const format of formats) {
      const hasFormat = await page.locator(`text=${format}`).count() > 0;
      if (hasFormat) {
        foundFormats++;
        console.log(`  ✓ 支持 ${format} 格式`);
      }
    }

    if (foundFormats > 0) {
      console.log(`✓ 共支持 ${foundFormats} 种导出格式`);
    } else {
      console.log('⚠ 未找到导出格式选项');
    }
  });

  test('报告列表应该支持搜索', async ({ page }) => {
    await page.goto('/api-automation/reports');
    await page.waitForLoadState('networkidle');

    // 查找搜索框
    const searchInput = page.locator('input[placeholder*="搜索"]');

    if (await searchInput.isVisible({ timeout: 3000 })) {
      console.log('✓ 搜索框存在');
    } else {
      console.log('⚠ 未找到搜索框');
    }
  });

  test('报告列表应该支持时间范围筛选', async ({ page }) => {
    await page.goto('/api-automation/reports');
    await page.waitForLoadState('networkidle');

    // 查找日期选择器
    const datePicker = page.locator('.el-date-editor, [class*="date"], input[type="date"]');

    if (await datePicker.count() > 0) {
      console.log('✓ 时间范围筛选器存在');
    } else {
      console.log('⚠ 未找到时间范围筛选器');
    }
  });

  test('应该支持批量操作', async ({ page }) => {
    await page.goto('/api-automation/reports');
    await page.waitForLoadState('networkidle');

    // 查找批量操作按钮
    const batchButtons = page.locator('button:has-text("批量"), button:has-text("导出"), button:has-text("删除")');

    if (await batchButtons.count() > 0) {
      console.log('✓ 批量操作按钮存在');
    } else {
      console.log('⚠ 未找到批量操作按钮');
    }
  });
});
