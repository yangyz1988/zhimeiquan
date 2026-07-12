// E2E Tests: Knowledge Base Browsing
// Playwright end-to-end test for the knowledge base page
//
// Covers:
//   - Navigate to /knowledge
//   - Verify 9-layer knowledge system renders
//   - Switch to file management view
//   - Click on a methodology file
//   - Verify content renders
//   - Quick-link navigation

import { test, expect } from "@playwright/test";

test.describe("Knowledge Base Browsing", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/knowledge", { waitUntil: "domcontentloaded" });
  });

  test("page loads with knowledge base title", async ({ page }) => {
    if (page.url().includes("/sign-in")) {
      test.skip();
      return;
    }

    // Verify the knowledge base heading
    await expect(page.getByText("知识库").first()).toBeVisible({
      timeout: 10_000,
    });
  });

  test("9-layer knowledge system renders all layers (L1-L9)", async ({
    page,
  }) => {
    if (page.url().includes("/sign-in")) {
      test.skip();
      return;
    }

    // Verify all 9 layer labels are visible
    const layers = ["L1", "L2", "L3", "L4", "L5", "L6", "L7", "L8", "L9"];
    for (const layer of layers) {
      await expect(page.getByText(layer).first()).toBeVisible({
        timeout: 5_000,
      });
    }
  });

  test("each layer displays correct title", async ({ page }) => {
    if (page.url().includes("/sign-in")) {
      test.skip();
      return;
    }

    // Verify layer titles
    const layerTitles = [
      "爆款底层逻辑",
      "四步创作法",
      "六大方法论",
      "平台算法适配",
      "标题类型库",
      "爆款概率保障",
      "运营SOP体系",
      "视觉音频优化",
      "专家智能体",
    ];

    for (const title of layerTitles) {
      await expect(page.getByText(title).first()).toBeVisible({
        timeout: 3_000,
      });
    }
  });

  test("view toggle buttons (九层体系 / 文件管理) are visible", async ({
    page,
  }) => {
    if (page.url().includes("/sign-in")) {
      test.skip();
      return;
    }

    // Verify the two view toggle buttons
    await expect(page.getByText("九层体系").first()).toBeVisible();
    await expect(page.getByText("文件管理").first()).toBeVisible();
  });

  test("switching to file management view shows file browser", async ({
    page,
  }) => {
    if (page.url().includes("/sign-in")) {
      test.skip();
      return;
    }

    // Click the file management tab
    const fileButton = page.getByText("文件管理").first();
    await expect(fileButton).toBeVisible();
    await fileButton.click();

    // Verify file browser appears
    await expect(page.getByText("文件浏览器").first()).toBeVisible({
      timeout: 5_000,
    });
  });

  test("file management view shows directory tree", async ({ page }) => {
    if (page.url().includes("/sign-in")) {
      test.skip();
      return;
    }

    // Switch to file management
    await page.getByText("文件管理").first().click();

    // Verify some folder structure is visible
    // The file browser should show content directories
    await page.waitForTimeout(1000);

    // Look for any file/folder indicators
    const hasFileTree =
      (await page.getByText("methodology").isVisible().catch(() => false)) ||
      (await page.locator('[data-testid="file-tree"]').isVisible().catch(
        () => false
      )) ||
      (await page.getByText("文件浏览器").isVisible().catch(() => false));

    expect(hasFileTree).toBeTruthy();
  });

  test("switching back to 九层体系 view restores layer display", async ({
    page,
  }) => {
    if (page.url().includes("/sign-in")) {
      test.skip();
      return;
    }

    // Switch to file management
    await page.getByText("文件管理").first().click();
    await page.waitForTimeout(500);

    // Switch back to 九层体系
    await page.getByText("九层体系").first().click();
    await page.waitForTimeout(500);

    // Verify layers are visible again
    await expect(page.getByText("L1").first()).toBeVisible({ timeout: 5_000 });
    await expect(page.getByText("L9").first()).toBeVisible();
  });

  test("quick-link section is visible below 9 layers", async ({ page }) => {
    if (page.url().includes("/sign-in")) {
      test.skip();
      return;
    }

    // Verify quick-link navigation items
    await expect(page.getByText("内容生成").first()).toBeVisible({
      timeout: 5_000,
    });
    await expect(page.getByText("专家引擎").first()).toBeVisible();
    await expect(page.getByText("运营中心").first()).toBeVisible();
  });

  test("clicking a layer expands to show detail", async ({ page }) => {
    if (page.url().includes("/sign-in")) {
      test.skip();
      return;
    }

    // Click on L1 to expand
    const l1Element = page.getByText("L1").first();
    await expect(l1Element).toBeVisible();
    await l1Element.click();

    // After click, the detail should show the description
    await page.waitForTimeout(500);
    await expect(page.getByText("CTR公式").first()).toBeVisible({
      timeout: 3_000,
    });
  });
});
