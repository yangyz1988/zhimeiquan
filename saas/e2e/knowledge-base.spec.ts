import { test, expect } from "@playwright/test";

test.describe("/knowledge 知识库页面", () => {
  test("访问 /knowledge（未登录可能重定向到登录页）", async ({ page }) => {
    const response = await page.goto("/knowledge", {
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

  test("已登录状态下显示九层知识体系标题", async ({ page }) => {
    await page.goto("/knowledge", { waitUntil: "domcontentloaded" });

    if (page.url().includes("/sign-in")) {
      test.skip();
      return;
    }

    // 验证知识库标题
    await expect(page.getByText("知识库").first()).toBeVisible();
  });

  test("已登录状态下显示视图切换按钮", async ({ page }) => {
    await page.goto("/knowledge", { waitUntil: "domcontentloaded" });

    if (page.url().includes("/sign-in")) {
      test.skip();
      return;
    }

    // 验证九层体系按钮
    const timelineButton = page.getByText("九层体系");
    await expect(timelineButton).toBeVisible();

    // 验证文件管理按钮
    const filesButton = page.getByText("文件管理");
    await expect(filesButton).toBeVisible();
  });

  test("九层体系视图显示全部 9 个层次", async ({ page }) => {
    await page.goto("/knowledge", { waitUntil: "domcontentloaded" });

    if (page.url().includes("/sign-in")) {
      test.skip();
      return;
    }

    // 验证九层体系的层级标签
    const layers = ["L1", "L2", "L3", "L4", "L5", "L6", "L7", "L8", "L9"];
    for (const layer of layers) {
      await expect(page.getByText(layer).first()).toBeVisible();
    }
  });

  test("九层体系中显示各层级标题", async ({ page }) => {
    await page.goto("/knowledge", { waitUntil: "domcontentloaded" });

    if (page.url().includes("/sign-in")) {
      test.skip();
      return;
    }

    // 验证部分层级标题
    await expect(page.getByText("爆款底层逻辑").first()).toBeVisible();
    await expect(page.getByText("四步创作法").first()).toBeVisible();
    await expect(page.getByText("六大方法论").first()).toBeVisible();
    await expect(page.getByText("平台算法适配").first()).toBeVisible();
    await expect(page.getByText("标题类型库").first()).toBeVisible();
    await expect(page.getByText("爆款概率保障").first()).toBeVisible();
    await expect(page.getByText("运营SOP体系").first()).toBeVisible();
    await expect(page.getByText("视觉音频优化").first()).toBeVisible();
    await expect(page.getByText("专家智能体").first()).toBeVisible();
  });

  test("九层体系下方显示快捷链接区域", async ({ page }) => {
    await page.goto("/knowledge", { waitUntil: "domcontentloaded" });

    if (page.url().includes("/sign-in")) {
      test.skip();
      return;
    }

    // 验证快捷链接
    await expect(page.getByText("内容生成").first()).toBeVisible();
    await expect(page.getByText("专家引擎").first()).toBeVisible();
    await expect(page.getByText("运营中心").first()).toBeVisible();
  });

  test("切换到文件管理视图", async ({ page }) => {
    await page.goto("/knowledge", { waitUntil: "domcontentloaded" });

    if (page.url().includes("/sign-in")) {
      test.skip();
      return;
    }

    // 点击文件管理按钮
    await page.getByText("文件管理").click();

    // 验证文件管理器元素出现
    await expect(page.getByText("文件浏览器").first()).toBeVisible({ timeout: 5000 });
  });
});
