import { test, expect } from '@playwright/test';

/**
 * Example E2E Test
 *
 * This is a placeholder test to verify the Playwright setup is working.
 * Real tests will be added in subsequent tasks.
 */

test.describe('Playwright Setup Verification', () => {
  test('@smoke example test validates Playwright is configured', async ({ page }) => {
    // Navigate to a test page
    await page.goto('https://example.com');

    // Verify page title
    await expect(page).toHaveTitle(/Example Domain/);

    // Verify heading
    const heading = page.locator('h1');
    await expect(heading).toContainText('Example Domain');
  });

  test('@smoke API request example', async ({ request }) => {
    // Make an API request
    const response = await request.get('https://jsonplaceholder.typicode.com/todos/1');

    // Verify response
    expect(response.status()).toBe(200);
    const data = await response.json();
    expect(data).toHaveProperty('title');
  });
});
