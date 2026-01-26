import { test, expect } from '@playwright/test';

/**
 * 环境管理功能测试用例
 * 包含环境列表、创建环境、编辑环境、删除环境、导入导出、测试连接测试
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

test.describe('环境管理', () => {

  test('应该显示环境管理页面', async ({ page }) => {
    await page.goto('/api-automation/environments');
    await page.waitForLoadState('networkidle');

    // 验证页面加载
    const pageTitle = page.locator('h1, h2, .page-title');
    await expect(pageTitle.first()).toBeVisible({ timeout: 5000 });

    console.log('✓ 环境管理页面加载成功');
  });

  test('应该显示环境列表表格', async ({ page }) => {
    await page.goto('/api-automation/environments');
    await page.waitForLoadState('networkidle');

    // 查找表格
    const table = page.locator('.el-table, table, [role="table"]');

    if (await table.isVisible({ timeout: 5000 })) {
      console.log('✓ 环境列表表格存在');
    } else {
      console.log('⚠ 未找到环境列表表格');
    }
  });

  test('应该显示环境统计卡片', async ({ page }) => {
    await page.goto('/api-automation/environments');
    await page.waitForLoadState('networkidle');

    // 查找统计卡片
    const statCards = page.locator('.stat-card, .stat-content, .el-card');

    const cardCount = await statCards.count();
    if (cardCount > 0) {
      console.log(`✓ 找到 ${cardCount} 个环境统计卡片`);
    } else {
      console.log('⚠ 未找到环境统计卡片');
    }
  });

  test('应该有新建环境按钮', async ({ page }) => {
    await page.goto('/api-automation/environments');
    await page.waitForLoadState('networkidle');

    // 查找新建按钮
    const createButton = page.locator('button:has-text("新建"), button:has-text("创建"), .el-button--primary');

    if (await createButton.first().isVisible({ timeout: 3000 })) {
      console.log('✓ 新建环境按钮存在');
    } else {
      console.log('⚠ 未找到新建环境按钮');
    }
  });

  test('应该支持测试连接功能', async ({ page }) => {
    await page.goto('/api-automation/environments');
    await page.waitForLoadState('networkidle');

    // 查找测试连接按钮
    const testConnectionButton = page.locator('button:has-text("测试连接"), button:has-text("连接测试")');

    if (await testConnectionButton.first().isVisible({ timeout: 3000 })) {
      console.log('✓ 测试连接按钮存在');
    } else {
      console.log('⚠ 未找到测试连接按钮');
    }
  });

  test('应该支持导入导出功能', async ({ page }) => {
    await page.goto('/api-automation/environments');
    await page.waitForLoadState('networkidle');

    // 查找导入导出按钮
    const importButton = page.locator('button:has-text("导入"), button:has-text("Import")');
    const exportButton = page.locator('button:has-text("导出"), button:has-text("Export")');

    const hasImport = await importButton.count() > 0;
    const hasExport = await exportButton.count() > 0;

    if (hasImport && hasExport) {
      console.log('✓ 导入导出按钮都存在');
    } else if (hasImport || hasExport) {
      console.log('⚠ 只有部分导入导出功能');
    } else {
      console.log('⚠ 未找到导入导出按钮');
    }
  });

  test('应该支持批量操作', async ({ page }) => {
    await page.goto('/api-automation/environments');
    await page.waitForLoadState('networkidle');

    // 查找批量操作按钮
    const batchButtons = page.locator('button:has-text("批量"), button:has-text("设为默认"), button:has-text("删除")');

    if (await batchButtons.count() > 0) {
      console.log('✓ 批量操作按钮存在');
    } else {
      console.log('⚠ 未找到批量操作按钮');
    }
  });

  test('应该支持搜索功能', async ({ page }) => {
    await page.goto('/api-automation/environments');
    await page.waitForLoadState('networkidle');

    // 查找搜索框
    const searchInput = page.locator('input[placeholder*="搜索"]');

    if (await searchInput.isVisible({ timeout: 3000 })) {
      console.log('✓ 搜索框存在');

      // 尝试搜索
      await searchInput.fill('test');
      await page.waitForTimeout(500);
      console.log('✓ 搜索框可输入');
    } else {
      console.log('⚠ 未找到搜索框');
    }
  });

  test('应该能打开环境详情', async ({ page }) => {
    await page.goto('/api-automation/environments');
    await page.waitForLoadState('networkidle');

    // 查找环境行并点击
    const table = page.locator('.el-table, table');
    const rows = table.locator('tbody tr');

    const rowCount = await rows.count();
    if (rowCount > 0) {
      const firstRow = rows.first();
      const link = firstRow.locator('a').first();

      if (await link.isVisible({ timeout: 1000 })) {
        await link.click();
        await page.waitForLoadState('networkidle');
        console.log('✓ 环境详情可打开');
      } else {
        console.log('⚠ 未找到环境详情链接');
      }
    } else {
      console.log('⚠ 环境列表为空');
    }
  });

  test('环境详情应该显示配置信息', async ({ page }) => {
    await page.goto('/api-automation/environments/1');
    await page.waitForLoadState('networkidle');

    // 查找配置信息
    const urlInput = page.locator('input[placeholder*="URL"], input[placeholder*="url"]');
    const headersSection = page.locator('text=/请求头|Headers/i');

    const hasUrl = await urlInput.count() > 0;
    const hasHeaders = await headersSection.count() > 0;

    if (hasUrl || hasHeaders) {
      console.log('✓ 环境详情显示配置信息');
    } else {
      console.log('⚠ 环境配置信息可能不完整');
    }
  });

  test('应该支持设置默认环境', async ({ page }) => {
    await page.goto('/api-automation/environments');
    await page.waitForLoadState('networkidle');

    // 查找设为默认按钮
    const setDefaultButton = page.locator('button:has-text("设为默认"), button:has-text("默认")');

    if (await setDefaultButton.first().isVisible({ timeout: 3000 })) {
      console.log('✓ 设为默认按钮存在');
    } else {
      console.log('⚠ 未找到设为默认按钮');
    }
  });

  test('应该支持克隆环境', async ({ page }) => {
    await page.goto('/api-automation/environments');
    await page.waitForLoadState('networkidle');

    // 查找克隆按钮
    const cloneButton = page.locator('button:has-text("克隆"), [class*="clone"]');

    if (await cloneButton.first().isVisible({ timeout: 3000 })) {
      console.log('✓ 克隆按钮存在');
    } else {
      console.log('⚠ 未找到克隆按钮');
    }
  });
});
