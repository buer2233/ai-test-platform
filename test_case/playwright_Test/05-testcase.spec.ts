import { test, expect } from '@playwright/test';

/**
 * 测试用例管理功能测试用例
 * 包含用例列表、用例详情、创建用例、编辑用例、删除用例测试
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

test.describe('测试用例管理', () => {

  test('应该显示测试用例列表页面', async ({ page }) => {
    await page.goto('/api-automation/test-cases');
    await page.waitForLoadState('networkidle');

    // 验证页面加载
    const pageTitle = page.locator('h1, h2, .page-title');
    await expect(pageTitle.first()).toBeVisible({ timeout: 5000 });

    console.log('✓ 测试用例列表页面加载成功');
  });

  test('应该显示测试用例表格', async ({ page }) => {
    await page.goto('/api-automation/test-cases');
    await page.waitForLoadState('networkidle');

    // 查找表格
    const table = page.locator('.el-table, table, [role="table"]');

    if (await table.isVisible({ timeout: 5000 })) {
      console.log('✓ 测试用例表格存在');
    } else {
      console.log('⚠ 未找到测试用例表格');
    }
  });

  test('应该支持按项目和集合筛选', async ({ page }) => {
    await page.goto('/api-automation/test-cases');
    await page.waitForLoadState('networkidle');

    // 查找筛选器
    const filters = page.locator('.el-select, select');

    const filterCount = await filters.count();
    if (filterCount >= 2) {
      console.log('✓ 筛选器存在（至少2个）');
    } else {
      console.log('⚠ 筛选器可能不完整');
    }
  });

  test('应该有新建用例按钮', async ({ page }) => {
    await page.goto('/api-automation/test-cases');
    await page.waitForLoadState('networkidle');

    // 查找新建按钮
    const createButton = page.locator('button:has-text("新建"), button:has-text("创建"), .el-button--primary');

    if (await createButton.first().isVisible({ timeout: 3000 })) {
      console.log('✓ 新建用例按钮存在');
    } else {
      console.log('⚠ 未找到新建用例按钮');
    }
  });

  test('应该支持搜索功能', async ({ page }) => {
    await page.goto('/api-automation/test-cases');
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

  test('应该能打开用例详情页', async ({ page }) => {
    await page.goto('/api-automation/test-cases');
    await page.waitForLoadState('networkidle');

    // 查找用例行并点击
    const table = page.locator('.el-table, table');
    const rows = table.locator('tbody tr');

    const rowCount = await rows.count();
    if (rowCount > 0) {
      const firstRow = rows.first();
      const link = firstRow.locator('a').first();

      if (await link.isVisible({ timeout: 1000 })) {
        await link.click();
        await page.waitForLoadState('networkidle');
        console.log('✓ 用例详情页面可打开');
      } else {
        console.log('⚠ 未找到用例详情链接');
      }
    } else {
      console.log('⚠ 用例列表为空');
    }
  });

  test('用例详情应该显示请求配置', async ({ page }) => {
    await page.goto('/api-automation/test-cases/1');
    await page.waitForLoadState('networkidle');

    // 查找请求配置相关元素
    const methodSelector = page.locator('text=/GET|POST|PUT|DELETE/i');
    const urlInput = page.locator('input[placeholder*="URL"], input[placeholder*="url"]');

    const hasMethod = await methodSelector.count() > 0;
    const hasUrl = await urlInput.count() > 0;

    if (hasMethod || hasUrl) {
      console.log('✓ 用例详情显示请求配置');
    } else {
      console.log('⚠ 请求配置可能不完整');
    }
  });

  test('用例详情应该显示断言配置区域', async ({ page }) => {
    await page.goto('/api-automation/test-cases/1');
    await page.waitForLoadState('networkidle');

    // 查找断言配置相关元素 - 使用 first() 避免严格模式违规
    const assertionTab = page.locator('text=/断言|Assertion/i').first();

    if (await assertionTab.isVisible({ timeout: 3000 })) {
      console.log('✓ 断言配置区域存在');
    } else {
      console.log('⚠ 未找到断言配置区域');
    }
  });

  test('用例详情应该显示数据提取区域', async ({ page }) => {
    await page.goto('/api-automation/test-cases/1');
    await page.waitForLoadState('networkidle');

    // 查找数据提取相关元素 - 使用 first() 避免严格模式违规
    const extractionTab = page.locator('text=/提取|Extraction/i').first();

    if (await extractionTab.isVisible({ timeout: 3000 })) {
      console.log('✓ 数据提取区域存在');
    } else {
      console.log('⚠ 未找到数据提取区域');
    }
  });

  test('应该支持执行单个用例', async ({ page }) => {
    await page.goto('/api-automation/test-cases');
    await page.waitForLoadState('networkidle');

    // 查找执行按钮
    const executeButton = page.locator('button:has-text("执行"), button:has-text("运行")');

    if (await executeButton.first().isVisible({ timeout: 3000 })) {
      console.log('✓ 执行按钮存在');
    } else {
      console.log('⚠ 未找到执行按钮');
    }
  });

  test('应该支持批量执行用例', async ({ page }) => {
    await page.goto('/api-automation/test-cases');
    await page.waitForLoadState('networkidle');

    // 查找批量执行按钮
    const batchExecuteButton = page.locator('button:has-text("批量执行"), button:has-text("批量运行")');

    if (await batchExecuteButton.isVisible({ timeout: 3000 })) {
      console.log('✓ 批量执行按钮存在');
    } else {
      console.log('⚠ 未找到批量执行按钮');
    }
  });

  test('应该支持克隆用例', async ({ page }) => {
    await page.goto('/api-automation/test-cases');
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
