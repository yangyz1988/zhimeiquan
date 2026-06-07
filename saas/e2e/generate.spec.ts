import { test, expect } from "@playwright/test";

test.describe("/generate 页面", () => {
  test("访问 /generate（未登录可能重定向到登录页）", async ({ page }) => {
    const response = await page.goto("/generate", {
      waitUntil: "domcontentloaded",
    });
    expect(response, "page response").not.toBeNull();

    const finalUrl = page.url();
    const signInUrl = new URL("/sign-in", "http://localhost:3000").toString();
    const isRedirectedToSignIn = finalUrl.startsWith(signInUrl);

    if (isRedirectedToSignIn) {
      expect(finalUrl).toContain("/sign-in");
    } else {
      expect(response!.ok()).toBeTruthy();
    }
  });
});
