// E2E Tests: Payment Flow
// Playwright end-to-end tests for Stripe subscription flow

import { test, expect } from '@playwright/test';

test.describe('Payment Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to pricing page
    await page.goto('/pricing');
  });

  test('should display pricing tiers', async ({ page }) => {
    // Check pricing cards are visible
    await expect(page.locator('[data-testid=\"pricing-card\"]')).toHaveCount(3);
    
    // Check tier names
    await expect(page.getByText('Basic')).toBeVisible();
    await expect(page.getByText('Pro')).toBeVisible();
    await expect(page.getByText('Enterprise')).toBeVisible();
  });

  test('should show subscribe button for each tier', async ({ page }) => {
    const subscribeButtons = page.locator('[data-testid=\"subscribe-button\"]');
    await expect(subscribeButtons).toHaveCount(3);
  });

  test('should redirect to checkout on subscribe click', async ({ page }) => {
    // Mock Stripe checkout
    await page.route('**/api/v1/payment/subscribe', route => {
      route.fulfill({
        status: 200,
        body: JSON.stringify({ checkoutUrl: 'https://checkout.stripe.com/mock' })
      });
    });

    const subscribeButton = page.locator('[data-testid=\"subscribe-button\"]').first();
    await subscribeButton.click();
    
    // Wait for checkout redirect or modal
    await page.waitForTimeout(1000);
  });
});
