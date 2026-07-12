import { test, expect } from "@playwright/test";

test.describe("/ab-test A/B 测试页面", () => {
  test("访问 /ab-test（未登录可能重定向到登录页）", async ({ page }) => {
    const response = await page.goto("/ab-test", {
      waitUntil: "domcontentloaded",
    });
    expect(response, "页面响应").not.toBeNull();

    const finalUrl = page.url();
    const signInUrl = new URL("/sign-in", "http://localhost:3000").toString();
    const isRedirectedToSignIn = finalUrl.startsWith(signInUrl);

    if (isRedirectedToSignIn) {
      expect(finalUrl).toContain("/sign-in");
    } else {
      expect(response!.ok()).toBeTruthy();
    }
  });

  test("已登录状态下页面包含 A/B 测试核心元素", async ({ page }) => {
    await page.goto("/ab-test", { waitUntil: "domcontentloaded" });

    // 如果重定向到登录页则跳过后续检查
    if (page.url().includes("/sign-in")) {
      test.skip();
      return;
    }

    // 验证页面标题
    await expect(page.getByText("A/B 测试").first()).toBeVisible();

    // 验证「新建测试」按钮存在
    const createButton = page.getByText("新建测试");
    await expect(createButton).toBeVisible();

    // 验证「刷新」按钮存在
    const refreshButton = page.getByText("刷新");
    await expect(refreshButton).toBeVisible();
  });

  test("「新建测试」按钮可点击", async ({ page }) => {
    await page.goto("/ab-test", { waitUntil: "domcontentloaded" });

    if (page.url().includes("/sign-in")) {
      test.skip();
      return;
    }

    const createButton = page.getByText("新建测试");
    await createButton.click();

    // 点击后应显示创建模态框
    await expect(page.getByText("创建 A/B 测试").first()).toBeVisible({ timeout: 5000 });
  });
});
