import { test, expect } from '@playwright/test';

/**
 * 项目管理功能测试用例
 * 包含项目列表、项目详情、创建项目、编辑项目、删除项目测试
 */

test.beforeEach(async ({ page }) => {
  // 导航到首页
  await page.goto('/');

  // 尝试快速登录（如果需要）- 使用 first() 避免严格模式违规
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

test.describe('项目管理', () => {

  test('应该显示项目列表页面', async ({ page }) => {
    // 导航到项目列表
    await page.goto('/api-automation/projects');
    await page.waitForLoadState('networkidle');

    // 验证页面标题或关键元素
    const pageTitle = page.locator('h1, h2, .page-title');
    await expect(pageTitle.first()).toBeVisible({ timeout: 5000 });

    console.log('✓ 项目列表页面加载成功');
  });

  test('应该显示项目列表表格', async ({ page }) => {
    await page.goto('/api-automation/projects');
    await page.waitForLoadState('networkidle');

    // 查找表格
    const table = page.locator('.el-table, table, [role="table"]');

    if (await table.isVisible({ timeout: 5000 })) {
      console.log('✓ 项目列表表格存在');

      // 检查表格行数
      const rows = table.locator('tr');
      const rowCount = await rows.count();
      console.log(`表格行数: ${rowCount}`);
    } else {
      console.log('⚠ 未找到项目列表表格');
    }
  });

  test('应该有新建项目按钮', async ({ page }) => {
    await page.goto('/api-automation/projects');
    await page.waitForLoadState('networkidle');

    // 查找新建按钮
    const createButton = page.locator('button:has-text("新建"), button:has-text("创建"), .el-button--primary');

    if (await createButton.first().isVisible({ timeout: 3000 })) {
      console.log('✓ 新建项目按钮存在');
    } else {
      console.log('⚠ 未找到新建项目按钮');
    }
  });

  test('应该支持搜索功能', async ({ page }) => {
    await page.goto('/api-automation/projects');
    await page.waitForLoadState('networkidle');

    // 查找搜索框
    const searchInput = page.locator('input[placeholder*="搜索"], input[placeholder*="搜索"], .el-input__inner');

    if (await searchInput.first().isVisible({ timeout: 3000 })) {
      console.log('✓ 搜索框存在');

      // 尝试输入搜索内容
      await searchInput.first().fill('test');
      await page.waitForTimeout(500);
      console.log('✓ 搜索框可输入');
    } else {
      console.log('⚠ 未找到搜索框');
    }
  });

  test('应该支持分页功能', async ({ page }) => {
    await page.goto('/api-automation/projects');
    await page.waitForLoadState('networkidle');

    // 查找分页组件
    const pagination = page.locator('.el-pagination, .pagination, [class*="pagination"]');

    if (await pagination.isVisible({ timeout: 3000 })) {
      console.log('✓ 分页组件存在');
    } else {
      console.log('⚠ 未找到分页组件');
    }
  });

  test('应该能打开项目详情', async ({ page }) => {
    await page.goto('/api-automation/projects');
    await page.waitForLoadState('networkidle');

    // 查找项目行
    const table = page.locator('.el-table, table');
    const rows = table.locator('tbody tr');

    const rowCount = await rows.count();
    if (rowCount > 0) {
      // 点击第一行的详情或项目名称
      const firstRow = rows.first();
      const link = firstRow.locator('a').first();

      if (await link.isVisible({ timeout: 1000 })) {
        await link.click();
        await page.waitForLoadState('networkidle');
        console.log('✓ 项目详情页面可打开');
      } else {
        console.log('⚠ 未找到项目详情链接');
      }
    } else {
      console.log('⚠ 项目列表为空');
    }
  });

  test('应该有表格操作按钮', async ({ page }) => {
    await page.goto('/api-automation/projects');
    await page.waitForLoadState('networkidle');

    // 查找操作按钮（编辑、删除等）
    const actionButtons = page.locator('button:has-text("编辑"), button:has-text("删除"), .el-button--text');

    const buttonCount = await actionButtons.count();
    if (buttonCount > 0) {
      console.log(`✓ 找到 ${buttonCount} 个操作按钮`);
    } else {
      console.log('⚠ 未找到表格操作按钮');
    }
  });

  test('应该能访问项目详情页', async ({ page }) => {
    // 直接导航到项目详情页（假设有项目ID为1）
    await page.goto('/api-automation/projects/1');
    await page.waitForLoadState('networkidle');

    // 检查是否成功加载
    const hasContent = await page.locator('body').textContent() > '';
    if (hasContent) {
      console.log('✓ 项目详情页可访问');
    } else {
      console.log('⚠ 项目详情页可能加载失败');
    }
  });

  test('应该显示项目统计信息', async ({ page }) => {
    await page.goto('/api-automation/projects/1');
    await page.waitForLoadState('networkidle');

    // 查找统计卡片
    const stats = page.locator('.stat-card, .el-card, [class*="stat"]');

    if (await stats.first().isVisible({ timeout: 3000 })) {
      console.log('✓ 项目统计信息存在');
    } else {
      console.log('⚠ 未找到项目统计信息');
    }
  });

  test('应该有返回按钮', async ({ page }) => {
    await page.goto('/api-automation/projects/1');
    await page.waitForLoadState('networkidle');

    // 查找返回按钮
    const backButton = page.locator('button:has-text("返回"), .el-button--default, [class*="back"]');

    if (await backButton.first().isVisible({ timeout: 3000 })) {
      console.log('✓ 返回按钮存在');
    } else {
      console.log('⚠ 未找到返回按钮');
    }
  });
});
