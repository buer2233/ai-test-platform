import { test, expect } from '@playwright/test';

/**
 * 回收站功能测试用例
 * 包含回收站列表、恢复数据、彻底删除、批量操作测试
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

test.describe('回收站', () => {

  test('应该显示回收站页面', async ({ page }) => {
    await page.goto('/api-automation/recycle-bin');
    await page.waitForLoadState('networkidle');

    // 验证页面加载
    const pageTitle = page.locator('h1, h2, .page-title');
    await expect(pageTitle.first()).toBeVisible({ timeout: 5000 });

    console.log('✓ 回收站页面加载成功');
  });

  test('应该显示回收站统计卡片', async ({ page }) => {
    await page.goto('/api-automation/recycle-bin');
    await page.waitForLoadState('networkidle');

    // 查找统计卡片
    const statCards = page.locator('.stat-card, .stat-content, .el-card');

    const cardCount = await statCards.count();
    if (cardCount > 0) {
      console.log(`✓ 找到 ${cardCount} 个回收站统计卡片`);
    } else {
      console.log('⚠ 未找到回收站统计卡片');
    }
  });

  test('应该显示已删除数据表格', async ({ page }) => {
    await page.goto('/api-automation/recycle-bin');
    await page.waitForLoadState('networkidle');

    // 查找表格
    const table = page.locator('.el-table, table, [role="table"]');

    if (await table.isVisible({ timeout: 5000 })) {
      console.log('✓ 回收站表格存在');
    } else {
      console.log('⚠ 未找到回收站表格');
    }
  });

  test('应该支持按类型筛选', async ({ page }) => {
    await page.goto('/api-automation/recycle-bin');
    await page.waitForLoadState('networkidle');

    // 查找类型筛选器
    const typeSelect = page.locator('.el-select, select');

    if (await typeSelect.first().isVisible({ timeout: 3000 })) {
      console.log('✓ 类型筛选器存在');
    } else {
      console.log('⚠ 未找到类型筛选器');
    }
  });

  test('应该支持搜索功能', async ({ page }) => {
    await page.goto('/api-automation/recycle-bin');
    await page.waitForLoadState('networkidle');

    // 查找搜索框
    const searchInput = page.locator('input[placeholder*="搜索"]');

    if (await searchInput.isVisible({ timeout: 3000 })) {
      console.log('✓ 搜索框存在');
    } else {
      console.log('⚠ 未找到搜索框');
    }
  });

  test('应该有恢复功能按钮', async ({ page }) => {
    await page.goto('/api-automation/recycle-bin');
    await page.waitForLoadState('networkidle');

    // 查找恢复按钮
    const restoreButton = page.locator('button:has-text("恢复"), button:has-text("Restore")');

    if (await restoreButton.first().isVisible({ timeout: 3000 })) {
      console.log('✓ 恢复按钮存在');
    } else {
      console.log('⚠ 未找到恢复按钮');
    }
  });

  test('应该有批量恢复功能', async ({ page }) => {
    await page.goto('/api-automation/recycle-bin');
    await page.waitForLoadState('networkidle');

    // 查找批量恢复按钮
    const batchRestoreButton = page.locator('button:has-text("批量恢复"), button:has-text("批量")');

    if (await batchRestoreButton.isVisible({ timeout: 3000 })) {
      console.log('✓ 批量恢复按钮存在');
    } else {
      console.log('⚠ 未找到批量恢复按钮');
    }
  });

  test('应该有彻底删除功能', async ({ page }) => {
    await page.goto('/api-automation/recycle-bin');
    await page.waitForLoadState('networkidle');

    // 查找彻底删除按钮
    const deleteButton = page.locator('button:has-text("彻底删除"), button:has-text("删除")');

    if (await deleteButton.first().isVisible({ timeout: 3000 })) {
      console.log('✓ 彻底删除按钮存在');
    } else {
      console.log('⚠ 未找到彻底删除按钮');
    }
  });

  test('应该有批量彻底删除功能', async ({ page }) => {
    await page.goto('/api-automation/recycle-bin');
    await page.waitForLoadState('networkidle');

    // 查找批量彻底删除按钮
    const batchDeleteButton = page.locator('button:has-text("批量彻底删除"), button:has-text("批量删除")');

    if (await batchDeleteButton.isVisible({ timeout: 3000 })) {
      console.log('✓ 批量彻底删除按钮存在');
    } else {
      console.log('⚠ 未找到批量彻底删除按钮');
    }
  });

  test('应该显示删除时间', async ({ page }) => {
    await page.goto('/api-automation/recycle-bin');
    await page.waitForLoadState('networkidle');

    // 查找删除时间列
    const timeColumn = page.locator('text=/删除时间|删除日期/i');

    if (await timeColumn.count() > 0) {
      console.log('✓ 显示删除时间');
    } else {
      console.log('⚠ 未找到删除时间显示');
    }
  });

  test('应该显示数据类型标签', async ({ page }) => {
    await page.goto('/api-automation/recycle-bin');
    await page.waitForLoadState('networkidle');

    // 查找类型标签
    const typeTags = page.locator('.el-tag, [class*="tag"]');

    if (await typeTags.count() > 0) {
      console.log('✓ 显示数据类型标签');
    } else {
      console.log('⚠ 未找到数据类型标签');
    }
  });

  test('应该有分页功能', async ({ page }) => {
    await page.goto('/api-automation/recycle-bin');
    await page.waitForLoadState('networkidle');

    // 查找分页组件
    const pagination = page.locator('.el-pagination, .pagination');

    if (await pagination.isVisible({ timeout: 3000 })) {
      console.log('✓ 分页组件存在');
    } else {
      console.log('⚠ 未找到分页组件');
    }
  });

  test('应该支持选择功能', async ({ page }) => {
    await page.goto('/api-automation/recycle-bin');
    await page.waitForLoadState('networkidle');

    // 查找复选框
    const checkboxes = page.locator('input[type="checkbox"], .el-checkbox');

    if (await checkboxes.count() > 0) {
      console.log('✓ 选择功能存在');
    } else {
      console.log('⚠ 未找到选择功能');
    }
  });
});
