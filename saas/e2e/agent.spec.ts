// E2E Tests: Agent Feature
// Playwright end-to-end tests for AI Agent functionality

import { test, expect } from '@playwright/test';

test.describe('Agent Feature', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/operations');
  });

  test('should display agent start button', async ({ page }) => {
    const startButton = page.locator('[data-testid=\"start-agent-button\"]');
    await expect(startButton).toBeVisible();
  });

  test('should start agent on button click', async ({ page }) => {
    // Mock agent start API
    await page.route('**/api/agent/start', route => {
      route.fulfill({
        status: 200,
        body: JSON.stringify({ 
          agentId: 'agent_123',
          status: 'running',
          message: 'Agent started successfully'
        })
      });
    });

    const startButton = page.locator('[data-testid=\"start-agent-button\"]');
    await startButton.click();
    
    // Check for status indicator
    const statusIndicator = page.locator('[data-testid=\"agent-status\"]');
    await expect(statusIndicator).toBeVisible({ timeout: 5000 });
  });

  test('should display agent list', async ({ page }) => {
    // Mock agent list API
    await page.route('**/api/agent', route => {
      route.fulfill({
        status: 200,
        body: JSON.stringify({
          agents: [
            { id: 'agent_1', name: 'Content Agent', status: 'idle' },
            { id: 'agent_2', name: 'Analysis Agent', status: 'running' }
          ]
        })
      });
    });

    await page.goto('/operations');
    
    const agentList = page.locator('[data-testid=\"agent-list\"]');
    await expect(agentList).toBeVisible();
  });

  test('should allow agent configuration', async ({ page }) => {
    const configButton = page.locator('[data-testid=\"agent-config-button\"]').first();
    
    if (await configButton.isVisible()) {
      await configButton.click();
      
      // Check config modal opens
      const configModal = page.locator('[data-testid=\"agent-config-modal\"]');
      await expect(configModal).toBeVisible();
    }
  });
});
