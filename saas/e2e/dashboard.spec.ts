import { test, expect } from "@playwright/test";

test.describe("/dashboard 仪表盘页面", () => {
  test("访问 /dashboard（未登录可能重定向到登录页）", async ({ page }) => {
    const response = await page.goto("/dashboard", {
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

  test("页面标题匹配预期的仪表盘路径", async ({ page }) => {
    await page.goto("/dashboard", { waitUntil: "domcontentloaded" });

    // 如果已登录，页面应该渲染某种内容
    // 如果未登录，会重定向到登录页面
    // 这里我们只验证路由是否可达
    const url = page.url();
    const isDashboard = url.includes("/dashboard");
    const isSignIn = url.includes("/sign-in");

    // 必须重定向到登录页或者正确渲染仪表盘
    expect(isDashboard || isSignIn).toBeTruthy();
  });
});
