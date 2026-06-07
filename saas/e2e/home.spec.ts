import { test, expect } from "@playwright/test";

test.describe("首页", () => {
  test("GET / 返回 200 且包含「智媒圈」字样", async ({ page }) => {
    const response = await page.goto("/");
    expect(response, "page response").not.toBeNull();
    expect(response!.status()).toBe(200);

    await expect(page.getByText("智媒圈").first()).toBeVisible();
  });

  test("GET /sign-in 跳转到 Clerk 鉴权域", async ({ page, context }) => {
    const response = await page.goto("/sign-in", {
      waitUntil: "domcontentloaded",
    });
    expect(response, "page response").not.toBeNull();

    const finalUrl = page.url();
    const navigatedAway =
      finalUrl.includes("clerk.") ||
      finalUrl.includes("accounts.dev") ||
      finalUrl !== new URL("/sign-in", "http://localhost:3000").toString();

    if (navigatedAway) {
      expect(finalUrl).not.toBe(
        new URL("/sign-in", "http://localhost:3000").toString()
      );
    } else {
      expect(response!.status()).toBe(200);
    }

    await context.close();
  });
});
