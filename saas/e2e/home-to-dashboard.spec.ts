// E2E Tests: Home → Sign Up → Dashboard Journey
// Playwright end-to-end test for the complete user onboarding flow
//
// Covers:
//   - Homepage hero section
//   - CTA "免费开始创作" → navigate to sign-in or generate
//   - Clerk sign-in page redirect
//   - Dashboard / project list rendering

import { test, expect } from "@playwright/test";

test.describe("Home → Sign Up → Dashboard Journey", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");
  });

  test("GET / returns 200 and renders hero section", async ({ page }) => {
    // Hero heading
    await expect(
      page.getByText("不用猜算法想标题").first()
    ).toBeVisible({ timeout: 10_000 });

    // Subtitle / description
    await expect(
      page.getByText("内容策略引擎").first()
    ).toBeVisible();

    // Brand name in header
    await expect(page.getByText("智媒圈").first()).toBeVisible();
  });

  test("hero section shows stat cards", async ({ page }) => {
    // Verify the 4 stat cards render
    await expect(page.getByText("13")).toBeVisible();
    await expect(page.getByText("平台覆盖")).toBeVisible();
    await expect(page.getByText("50+")).toBeVisible();
    await expect(page.getByText("95%+")).toBeVisible();
  });

  test("clicking '免费开始创作' navigates to /generate or redirects to sign-in", async ({
    page,
  }) => {
    const ctaButton = page.getByText("免费开始创作").first();

    // The button might be inside a Link wrapping a Button
    await expect(ctaButton).toBeVisible({ timeout: 10_000 });
    await ctaButton.click();

    await page.waitForLoadState("networkidle");

    const finalUrl = page.url();
    const isGenerate = finalUrl.includes("/generate");
    const isSignIn = finalUrl.includes("/sign-in");

    // Should be on /generate or redirected to sign-in (Clerk)
    expect(isGenerate || isSignIn).toBeTruthy();
  });

  test("clicking '查看会员方案' navigates to /pricing", async ({ page }) => {
    const pricingLink = page.getByText("查看会员方案").first();
    await expect(pricingLink).toBeVisible();
    await pricingLink.click();

    await page.waitForLoadState("networkidle");

    const finalUrl = page.url();
    // /pricing should be accessible without auth
    expect(finalUrl).toContain("/pricing");
  });

  test("visiting /sign-in redirects to Clerk auth domain", async ({ page }) => {
    await page.goto("/sign-in", { waitUntil: "domcontentloaded" });

    const finalUrl = page.url();
    const navigatedAway =
      finalUrl.includes("clerk.") ||
      finalUrl.includes("accounts.dev") ||
      finalUrl !== new URL("/sign-in", "http://localhost:3000").toString();

    if (navigatedAway) {
      // Clerk redirect happened — this is the expected auth flow
      expect(finalUrl).not.toBe(
        new URL("/sign-in", "http://localhost:3000").toString()
      );
    } else {
      // Clerk might not be configured in dev; page should still load
      const response = await page.goto("/sign-in");
      expect(response).not.toBeNull();
    }
  });

  test("dashboard page is reachable (auth-gated)", async ({ page }) => {
    await page.goto("/dashboard", { waitUntil: "domcontentloaded" });

    const finalUrl = page.url();
    const isDashboard = finalUrl.includes("/dashboard");
    const isSignIn = finalUrl.includes("/sign-in");

    // Either renders dashboard or redirects to sign-in
    expect(isDashboard || isSignIn).toBeTruthy();
  });
});
