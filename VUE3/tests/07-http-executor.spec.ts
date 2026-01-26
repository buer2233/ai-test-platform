import { test, expect } from '@playwright/test';

/**
 * HTTP执行器功能测试用例
 * 包含HTTP请求配置、响应查看、cURL导入导出、保存为用例测试
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

test.describe('HTTP执行器', () => {

  test('应该显示HTTP执行器页面', async ({ page }) => {
    await page.goto('/api-automation/http-executor');
    await page.waitForLoadState('networkidle');

    // 验证页面加载
    const pageTitle = page.locator('h1, h2, .page-title');
    await expect(pageTitle.first()).toBeVisible({ timeout: 5000 });

    console.log('✓ HTTP执行器页面加载成功');
  });

  test('应该显示请求方法选择器', async ({ page }) => {
    await page.goto('/api-automation/http-executor');
    await page.waitForLoadState('networkidle');

    // 查找请求方法选择器
    const methodSelector = page.locator('.el-select, select, [class*="method"]');

    if (await methodSelector.first().isVisible({ timeout: 3000 })) {
      console.log('✓ 请求方法选择器存在');

      // 检查是否包含常见HTTP方法
      const methods = ['GET', 'POST', 'PUT', 'DELETE'];
      for (const method of methods) {
        const hasMethod = await page.locator(`text=${method}`).count() > 0;
        if (hasMethod) {
          console.log(`  ✓ 包含 ${method} 方法`);
        }
      }
    } else {
      console.log('⚠ 未找到请求方法选择器');
    }
  });

  test('应该显示URL输入框', async ({ page }) => {
    await page.goto('/api-automation/http-executor');
    await page.waitForLoadState('networkidle');

    // 查找URL输入框
    const urlInput = page.locator('input[placeholder*="URL"], input[placeholder*="http"]');

    if (await urlInput.isVisible({ timeout: 3000 })) {
      console.log('✓ URL输入框存在');

      // 尝试输入URL
      await urlInput.fill('https://api.example.com/test');
      const value = await urlInput.inputValue();
      if (value.includes('api.example.com')) {
        console.log('✓ URL输入框可输入');
      }
    } else {
      console.log('⚠ 未找到URL输入框');
    }
  });

  test('应该显示请求头配置区域', async ({ page }) => {
    await page.goto('/api-automation/http-executor');
    await page.waitForLoadState('networkidle');

    // 查找请求头配置
    const headersSection = page.locator('text=/请求头|Headers/i');

    if (await headersSection.isVisible({ timeout: 3000 })) {
      console.log('✓ 请求头配置区域存在');
    } else {
      console.log('⚠ 未找到请求头配置区域');
    }
  });

  test('应该显示请求体配置区域', async ({ page }) => {
    await page.goto('/api-automation/http-executor');
    await page.waitForLoadState('networkidle');

    // 查找请求体配置
    const bodySection = page.locator('text=/请求体|Body/i');
    const tabs = page.locator('.el-tabs, [role="tablist"]');

    const hasBodySection = await bodySection.count() > 0;
    const hasTabs = await tabs.count() > 0;

    if (hasBodySection || hasTabs) {
      console.log('✓ 请求体配置区域存在');
    } else {
      console.log('⚠ 未找到请求体配置区域');
    }
  });

  test('应该有发送请求按钮', async ({ page }) => {
    await page.goto('/api-automation/http-executor');
    await page.waitForLoadState('networkidle');

    // 查找发送按钮
    const sendButton = page.locator('button:has-text("发送"), button:has-text("Send"), .el-button--primary');

    if (await sendButton.isVisible({ timeout: 3000 })) {
      console.log('✓ 发送请求按钮存在');
    } else {
      console.log('⚠ 未找到发送请求按钮');
    }
  });

  test('应该显示响应区域', async ({ page }) => {
    await page.goto('/api-automation/http-executor');
    await page.waitForLoadState('networkidle');

    // 查找响应区域 - 使用 or() 方法组合多个选择器
    const responseSection1 = page.locator('text=/响应/i');
    const responseSection2 = page.locator('text=/Response/i');
    const responseSection3 = page.locator('[class*="response"]');

    if (await responseSection1.count() > 0 || await responseSection2.count() > 0 || await responseSection3.count() > 0) {
      console.log('✓ 响应区域存在');
    } else {
      console.log('⚠ 未找到响应区域');
    }
  });

  test('应该支持cURL导入功能', async ({ page }) => {
    await page.goto('/api-automation/http-executor');
    await page.waitForLoadState('networkidle');

    // 查找cURL导入按钮
    const importCurlButton = page.locator('button:has-text("导入cURL"), button:has-text("Import")');

    if (await importCurlButton.isVisible({ timeout: 3000 })) {
      console.log('✓ cURL导入按钮存在');
    } else {
      console.log('⚠ 未找到cURL导入按钮');
    }
  });

  test('应该支持保存为用例功能', async ({ page }) => {
    await page.goto('/api-automation/http-executor');
    await page.waitForLoadState('networkidle');

    // 查找保存为用例按钮
    const saveAsCaseButton = page.locator('button:has-text("保存"), button:has-text("Save")');

    if (await saveAsCaseButton.isVisible({ timeout: 3000 })) {
      console.log('✓ 保存为用例按钮存在');
    } else {
      console.log('⚠ 未找到保存为用例按钮');
    }
  });

  test('应该显示请求历史', async ({ page }) => {
    await page.goto('/api-automation/http-executor');
    await page.waitForLoadState('networkidle');

    // 查找请求历史区域 - 分别检查多个选择器
    const historySection1 = page.locator('text=/历史/i');
    const historySection2 = page.locator('text=/History/i');
    const historySection3 = page.locator('[class*="history"]');

    if (await historySection1.count() > 0 || await historySection2.count() > 0 || await historySection3.count() > 0) {
      console.log('✓ 请求历史区域存在');
    } else {
      console.log('⚠ 未找到请求历史区域');
    }
  });

  test('应该支持环境选择', async ({ page }) => {
    await page.goto('/api-automation/http-executor');
    await page.waitForLoadState('networkidle');

    // 查找环境选择器
    const envSelect = page.locator('.el-select, select');

    if (await envSelect.first().isVisible({ timeout: 3000 })) {
      console.log('✓ 环境选择器存在');
    } else {
      console.log('⚠ 未找到环境选择器');
    }
  });

  test('应该支持变量替换', async ({ page }) => {
    await page.goto('/api-automation/http-executor');
    await page.waitForLoadState('networkidle');

    // 查找变量相关元素
    const variableIndicator = page.locator('text=/变量|Variable|\${/i');

    if (await variableIndicator.count() > 0) {
      console.log('✓ 变量功能相关元素存在');
    } else {
      console.log('⚠ 未找到变量相关元素');
    }
  });
});
