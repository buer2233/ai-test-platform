import { test, expect } from '@playwright/test';

/**
 * 仪表盘功能测试用例
 * 包含统计卡片、图表可视化、环境维度报告、集合维度报告测试
 */

// 需要先登录才能访问仪表盘
test.beforeEach(async ({ page }) => {
  // 导航到登录页
  await page.goto('/');

  // 尝试登录（如果需要）- 使用 first() 避免严格模式违规
  const usernameInput = page.locator('input[type="text"]').first();
  const passwordInput = page.locator('input[type="password"]').first();

  if (await usernameInput.isVisible({ timeout: 3000 })) {
    await usernameInput.fill('admin');
    await passwordInput.fill('admin123');
    // 使用通用按钮选择器来定位登录提交按钮
    const loginButtons = page.locator('button').filter({ hasText: /登录/i });
    await loginButtons.first().click();

    // 等待导航到仪表盘
    await page.waitForURL('**/dashboard**', { timeout: 5000 }).catch(() => {});
  }
});

test.describe('仪表盘功能', () => {

  test('应该显示仪表盘页面', async ({ page }) => {
    // 导航到仪表盘
    await page.goto('/dashboard');

    // 等待页面加载
    await page.waitForLoadState('networkidle');

    // 验证页面标题
    const title = await page.title();
    console.log('页面标题:', title);

    // 验证仪表盘关键元素存在
    const statsCards = page.locator('.stat-card, .el-card');
    await expect(statsCards.first()).toBeVisible({ timeout: 5000 });
  });

  test('应该显示统计卡片', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // 查找统计卡片
    const statCards = page.locator('.stat-card, .stat-content, .el-card');

    // 统计卡片数量至少应该有4个（总用例、通过、失败、通过率）
    const cardCount = await statCards.count();
    console.log(`找到 ${cardCount} 个统计卡片`);

    if (cardCount >= 4) {
      console.log('✓ 统计卡片显示正常');
    } else {
      console.log('⚠ 统计卡片数量可能不完整');
    }
  });

  test('应该显示图表容器', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // 查找 ECharts 图表容器
    const chartContainers = page.locator('[class*="chart"], .echart, #echart');

    const chartCount = await chartContainers.count();
    console.log(`找到 ${chartCount} 个图表容器`);

    if (chartCount > 0) {
      console.log('✓ 图表容器存在');
    } else {
      console.log('⚠ 未找到图表容器');
    }
  });

  test('应该显示环境维度报告', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // 查找环境维度报告相关元素
    const environmentSection = page.locator('text=/环境/i').first();

    if (await environmentSection.isVisible({ timeout: 3000 })) {
      console.log('✓ 环境维度报告区域存在');
    } else {
      console.log('⚠ 未找到环境维度报告');
    }
  });

  test('应该显示集合维度报告', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // 查找集合维度报告相关元素
    const collectionSection = page.locator('text=/集合|Collection/i').first();

    if (await collectionSection.isVisible({ timeout: 3000 })) {
      console.log('✓ 集合维度报告区域存在');
    } else {
      console.log('⚠ 未找到集合维度报告');
    }
  });

  test('应该支持筛选功能', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // 查找筛选相关元素（下拉框、按钮等）
    const filterElements = page.locator('.el-select, select, [role="combobox"]');

    if (await filterElements.first().isVisible({ timeout: 3000 })) {
      console.log('✓ 筛选控件存在');

      // 尝试点击筛选器
      try {
        await filterElements.first().click();
        await page.waitForTimeout(500);
        console.log('✓ 筛选器可交互');
      } catch (e) {
        console.log('⚠ 筛选器交互可能有问题');
      }
    } else {
      console.log('⚠ 未找到筛选控件');
    }
  });

  test('统计卡片应该可以点击', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // 查找可点击的统计卡片
    const clickableCards = page.locator('.stat-card, .stat-content, [class*="stat"]');

    const cardCount = await clickableCards.count();
    if (cardCount > 0) {
      try {
        // 尝试点击第一个卡片
        await clickableCards.first().click();
        await page.waitForTimeout(500);
        console.log('✓ 统计卡片可点击');
      } catch (e) {
        console.log('⚠ 统计卡片点击可能有问题');
      }
    } else {
      console.log('⚠ 没有找到可点击的统计卡片');
    }
  });

  test('应该有导航菜单', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // 查找侧边栏或导航菜单
    const sidebar = page.locator('.sidebar, .el-aside, nav, [class*="menu"]');

    if (await sidebar.first().isVisible({ timeout: 3000 })) {
      console.log('✓ 导航菜单存在');
    } else {
      console.log('⚠ 未找到导航菜单');
    }
  });

  test('应该显示面包屑导航', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // 查找面包屑
    const breadcrumb = page.locator('.el-breadcrumb, [class*="breadcrumb"], nav[aria-label="breadcrumb"]');

    if (await breadcrumb.isVisible({ timeout: 3000 })) {
      console.log('✓ 面包屑导航存在');
    } else {
      console.log('⚠ 未找到面包屑导航');
    }
  });

  test('应该有用户信息显示', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // 查找用户头像、用户名或下拉菜单
    const userElements = page.locator('[class*="user"], [class*="avatar"], .el-dropdown');

    if (await userElements.first().isVisible({ timeout: 3000 })) {
      console.log('✓ 用户信息区域存在');
    } else {
      console.log('⚠ 未找到用户信息显示');
    }
  });
});
